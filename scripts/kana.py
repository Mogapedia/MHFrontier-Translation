#!/usr/bin/env python3
"""
Katakana -> Latin transliteration with etymology restoration.

Japanese borrows foreign names through a syllabary that cannot write bare
consonants, so it pads them with vowels: Gloria -> グロリア (gu-ro-ri-a),
Sthenno -> ステノ (su-te-no). A plain Hepburn romanisation gives back the
padded form ("guroria"), which is not a name in any language.

`restore()` undoes the padding with the standard heuristics:

  - u/o inserted after a consonant before another consonant is epenthetic
    (グロリア -> g[u]roria -> Gloria)
  - r-row kana render as l as often as r; the caller resolves genuine
    ambiguity through the override table
  - long vowels (ー) collapse rather than double

The result is a *proposal*, not an answer. Anything this module produces is
tagged `romaji` in docs/armor_series.fr.csv so a human can confirm it, and
the generator will not ship those rows without review.
"""

import re

# Hepburn base table, longest keys first so digraphs win.
KANA = {
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo", "シャ": "sha", "シュ": "shu",
    "ショ": "sho", "チャ": "cha", "チュ": "chu", "チョ": "cho", "ニャ": "nya",
    "ニュ": "nyu", "ニョ": "nyo", "ヒャ": "hya", "ヒュ": "hyu", "ヒョ": "hyo",
    "ミャ": "mya", "ミュ": "myu", "ミョ": "myo", "リャ": "rya", "リュ": "ryu",
    "リョ": "ryo", "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo", "ジャ": "ja",
    "ジュ": "ju", "ジョ": "jo", "ビャ": "bya", "ビュ": "byu", "ビョ": "byo",
    "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo",
    "ファ": "fa", "フィ": "fi", "フェ": "fe", "フォ": "fo", "フュ": "fyu",
    "ティ": "ti", "ディ": "di", "トゥ": "tu", "ドゥ": "du",
    "ウィ": "wi", "ウェ": "we", "ウォ": "wo", "ヴァ": "va", "ヴィ": "vi",
    "ヴェ": "ve", "ヴォ": "vo", "ヴュ": "vyu",
    "シェ": "she", "ジェ": "je", "チェ": "che", "ツァ": "tsa", "ツィ": "tsi",
    "ツェ": "tse", "ツォ": "tso", "クァ": "kwa", "クィ": "kwi", "クォ": "kwo",
    "グァ": "gwa",
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "wo", "ン": "n",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "ヴ": "vu",
    "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o",
    "ャ": "ya", "ュ": "yu", "ョ": "yo",
}
_KEYS = sorted(KANA, key=len, reverse=True)
_KANA_RE = re.compile("|".join(_KEYS))

VOWELS = "aeiou"


def romaji(s):
    """Plain Hepburn romanisation, keeping ー as ':' for later collapsing."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == "ッ":                      # gemination: double next consonant
            m = _KANA_RE.match(s, i + 1)
            if m:
                nxt = KANA[m.group(0)]
                out.append(nxt[0])
            i += 1
            continue
        if s[i] == "ー":
            out.append(":")
            i += 1
            continue
        if s[i] in "・･":
            out.append("-")
            i += 1
            continue
        m = _KANA_RE.match(s, i)
        if m:
            out.append(KANA[m.group(0)])
            i = m.end()
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


# Kana whose vowel is routinely epenthetic: the u-column, plus ト/ド whose
# 'o' is inserted to carry a bare t/d (テクスト -> text, ゴルト -> Golt).
_EPEN_U = set("クグスズツフブプムルヴ")
_EPEN_O = set("トド")


def syllables(s):
    """Split katakana into (kana, romaji) pairs, folding ー and ッ inward."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == "ッ":
            out.append(("ッ", "*"))          # resolved against the next syllable
            i += 1
            continue
        if s[i] == "ー":
            if out:
                out[-1] = (out[-1][0], out[-1][1] + ":")
            i += 1
            continue
        if s[i] in "・･":
            out.append(("・", "-"))
            i += 1
            continue
        m = _KANA_RE.match(s, i)
        if m:
            out.append((m.group(0), KANA[m.group(0)]))
            i = m.end()
        else:
            out.append((s[i], s[i]))
            i += 1
    return out


def restore(s, l_bias=True):
    """Katakana -> a plausible original Latin spelling.

    Works syllable by syllable so that only genuinely inserted vowels are
    dropped: グロリア -> Gloria (the u of グ is epenthetic, the o of ロ is not),
    ゴルゴン -> Gorgon, ステノ -> Steno, テクスト -> Text.

    l_bias renders the r-row as 'l' inside a consonant cluster and word-
    finally, which matches most Western names borrowed into MHF. Genuine
    'r' names are handled by the override table, not by this heuristic.
    """
    syl = syllables(s)
    parts = []
    for idx, (kana, rom) in enumerate(syl):
        rom = re.sub(r"([aeiou]):", r"\1", rom).replace(":", "")
        if rom == "*":
            nxt = syl[idx + 1][1] if idx + 1 < len(syl) else ""
            parts.append(nxt[0] if nxt else "")
            continue
        nxt_kana = syl[idx + 1][0] if idx + 1 < len(syl) else None
        last = idx == len(syl) - 1
        # A following syllable that itself starts with a consonant means this
        # syllable's vowel was only there to make the cluster pronounceable.
        nxt_is_cons = bool(nxt_kana) and syl[idx + 1][1][:1] not in VOWELS + "-*"
        drop = False
        if kana in _EPEN_U and rom.endswith("u") and (last or nxt_is_cons):
            drop = True
        elif kana in _EPEN_O and rom.endswith("o") and (last or nxt_is_cons):
            drop = True
        parts.append(rom[:-1] if drop else rom)

    r = "".join(parts)

    if l_bias:
        # r immediately after another consonant, or word-final, is usually l.
        r = re.sub(r"(?<=[bcdfgkpstv])r", "l", r)
        r = re.sub(r"r$", "l", r)

    return r.capitalize()


if __name__ == "__main__":
    import sys
    for w in sys.argv[1:]:
        print(f"{w}\t{romaji(w)}\t{restore(w)}")
