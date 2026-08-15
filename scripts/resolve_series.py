#!/usr/bin/env python3
"""
Populate the `fr` column of docs/armor_series.fr.csv.

Series stems are proper nouns, so they are restored rather than translated.
Four sources are tried in order of trust, and the winning one is recorded in
the `origin` column so the generator knows what it can ship unreviewed:

  monster    the stem is a monster whose French name Mogapedia already fixes
             (docs/monster_names.fr.csv) -- highest trust
  etymology  hand-confirmed original spelling (ステノ -> Stheno, カーマイン ->
             Carmin). Curated below; extend it as stems are identified.
  en-patch   the English fan patch already romanised the stem, and the EN
             romanisation is reused as-is
  romaji     scripts/kana.py transliteration -- a *proposal only*. These are
             not shipped by armor_names.py --apply unless you pass
             --include-romaji, because kana loses vowel quality
             (スリート is Sleet, not Slit).

Existing non-empty `fr` values are never overwritten: hand edits win.

Usage:
    python scripts/resolve_series.py            # fill blanks, report
    python scripts/resolve_series.py --stats    # report only, write nothing
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kana import restore  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES_TABLE = os.path.join(HERE, "docs", "armor_series.fr.csv")
MONSTERS = os.path.join(HERE, "docs", "monster_names.fr.csv")

# Hand-confirmed original spellings. Several coherent naming families are
# visible and were used to disambiguate: a Greek myth set (Stheno / Gorgone /
# Asteri / Magos), a Latin set (Regnum / Aristo / Alma), and a French set
# (Carmin / Clair / Rage / Chaos / Marin / Bande / Demon).
ETYMOLOGY = {
    # Greek
    "ステノ": "Stheno", "ゴルゴン": "Gorgone", "アステリ": "Asteri",
    "マゴス": "Magos", "アリスト": "Aristo", "メレティ": "Meleti",
    "メトリー": "Metri", "ペリフ": "Perif", "ゲノム": "Genome",
    # Latin / romance
    "アルマ": "Alma", "レグヌム": "Regnum", "レアル": "Real",
    "リゲリア": "Ligeria", "セレナ": "Serena", "アミスタ": "Amista",
    "マギサ": "Magisa", "サジタリオ": "Sagittaire", "セクティ": "Secti",
    # French
    "カーマイン": "Carmin", "クレール": "Clair", "レイジ": "Rage",
    "カオス": "Chaos", "デモン": "Demon", "マリン": "Marin",
    "バンデ": "Bande", "シェリフ": "Sherif", "シエナ": "Sienne",
    "テクスト": "Texte",
    # Germanic / English
    "ゴルト": "Gold", "ダスク": "Dusk", "アッシュ": "Ash",
    "スリート": "Sleet", "クロース": "Cloth", "ブライト": "Bright",
    "ブレイズ": "Blaze", "ランページ": "Rampage", "レディ": "Lady",
    "ケブラー": "Kevlar", "レイヤー": "Layer", "ウィザー": "Wither",
    "ガウス": "Gauss", "ウェーバ": "Weber", "ギルバート": "Gilbert",
    "キャロル": "Carol", "バーニー": "Barney", "ダンテ": "Dante",
    "ニーナ": "Nina", "ザイラ": "Zaira", "ゲルト": "Gert",
    "オナブル": "Onable", "フェルム": "Ferm", "マイスト": "Maist",
    # Other
    "ナーガ": "Naga", "リュウ": "Ryu", "オユン": "Oyun", "ミク": "Miku",
    "イクス": "Ix", "ピクス": "Pyx", "ゾデック": "Zodec",
    "ガリトス": "Garitos", "エヴォル": "Evol", "ワンダレ": "Wandale",
    "エディオ": "Edio", "レイスト": "Reist", "ファラン": "Faran",
    "シャラン": "Sharan", "リアン": "Rian", "アミロ": "Amiro",
    "オメット": "Omet", "ガニア": "Gania", "グロリア": "Gloria",
    "カウチュ": "Kauchu", "ルフレ": "Rufre", "ジュアリ": "Juari",
    "カマレラ": "Camarera", "メテネラ": "Metenera", "アージェ": "Arge",
    "トラス": "Truss", "ブリス": "Bliss", "ディヴォル": "Divol",
    "カエシス": "Cayssis", "アクラ": "Akura",
}

KATAKANA = re.compile(r"^[ァ-ヶー・]+$")


def load_monsters():
    out = {}
    if not os.path.exists(MONSTERS):
        return out
    with open(MONSTERS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            jp = (row.get("jp") or "").strip()
            fr = (row.get("fr") or "").strip()
            if jp and fr:
                out[jp] = fr
                # armour stems often use only the first element of a
                # multi-part monster name: アクラ・ヴァシム -> アクラ
                head = jp.split("・")[0]
                if len(head) >= 3:
                    out.setdefault(head, fr.split()[0])
    return out


def load_en_hints():
    """Reuse the EN patch romanisation when it exists, from the example column."""
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stats", action="store_true", help="report only, write nothing")
    ap.add_argument("--en-hints", help="optional JSON of stem -> [EN tokens]")
    args = ap.parse_args()

    monsters = load_monsters()
    en_hints = {}
    if args.en_hints and os.path.exists(args.en_hints):
        import json
        en_hints = json.load(open(args.en_hints, encoding="utf-8"))

    with open(SERIES_TABLE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    origins = Counter()
    rows_by_origin = Counter()
    for r in rows:
        jp = r["jp"]
        n = int(r["occurrences"])
        if (r.get("fr") or "").strip():
            # Already filled. Keep whatever origin it carries: relabelling a
            # `romaji` proposal as `hand` would launder an unreviewed guess
            # into the trusted set that --apply ships.
            origin = (r.get("origin") or "hand").strip() or "hand"
            r["origin"] = origin
            origins[origin] += 1
            rows_by_origin[origin] += n
            continue

        fr, origin = None, None
        if jp in monsters:
            fr, origin = monsters[jp], "monster"
        elif jp in ETYMOLOGY:
            fr, origin = ETYMOLOGY[jp], "etymology"
        elif en_hints.get(jp):
            fr, origin = en_hints[jp][0], "en-patch"
        elif KATAKANA.match(jp):
            fr, origin = restore(jp), "romaji"
        else:
            origin = "unresolved"       # kanji stems need a human

        if fr:
            r["fr"] = fr
        r["origin"] = origin
        origins[origin] += 1
        rows_by_origin[origin] += n

    if not args.stats:
        with open(SERIES_TABLE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, lineterminator="\n", fieldnames=["jp", "fr", "occurrences", "origin", "example"])
            w.writeheader()
            w.writerows(rows)

    total_rows = sum(int(r["occurrences"]) for r in rows)
    print(f"{len(rows)} series stems, {total_rows} armour name rows\n")
    print(f"{'origin':12s} {'stems':>7s} {'rows':>8s}   {'% rows':>7s}")
    for o in ["hand", "monster", "etymology", "en-patch", "romaji", "unresolved"]:
        if origins[o]:
            print(f"{o:12s} {origins[o]:7d} {rows_by_origin[o]:8d}   "
                  f"{100.0*rows_by_origin[o]/total_rows:6.1f}%")
    shippable = sum(rows_by_origin[o] for o in ["hand", "monster", "etymology", "en-patch"])
    print(f"\nshippable without review: {shippable} rows "
          f"({100.0*shippable/total_rows:.1f}% of parsed armour names)")


if __name__ == "__main__":
    main()
