#!/usr/bin/env python3
"""
Deterministic generator for French armour names.

Armour names in MHF are compositional. This script parses the Japanese
source into its grammar:

    SERIES [TIER] SLOT [・COLOUR]            e.g. シャランＦヘッド・青
    SERIES・SLOT_KANJI：CLASS [TIER] COLOUR   e.g. 赤原礼装・頭：剣HS赤

and re-renders it in French with correct adjective agreement, using the
closed vocabularies in `docs/armor_vocab.fr.json` and the series-stem
table in `docs/armor_series.fr.csv`.

Because the grammar is closed, this needs no machine translation and
produces no review queue for the parts it covers: the only judgement
calls live in the two data files, which are small enough to review by
hand.

Usage:
    python scripts/armor_names.py --report        # parse rate + width check
    python scripts/armor_names.py --emit-series   # (re)generate the stem table
    python scripts/armor_names.py --apply         # fill target= in translations/fr
"""

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB = os.path.join(HERE, "docs", "armor_vocab.fr.json")
SERIES_TABLE = os.path.join(HERE, "docs", "armor_series.fr.csv")
SECTIONS = ["head", "body", "arms", "waist", "legs"]

# Slot nouns written in kanji, used by the ：class variant.
KANJI_SLOTS = "頭胴腕腰脚"
# Weapon-class markers that follow the colon.
CLASS_MARKS = "剣弓銃打"


def load_vocab():
    with open(VOCAB, encoding="utf-8") as f:
        return json.load(f)


# Stem origins trusted enough to ship without human review. `romaji` is
# excluded: kana transliteration loses vowel quality, so those stems are
# proposals for a reviewer, not output.
TRUSTED_ORIGINS = {"hand", "monster", "etymology", "francised", "en-patch"}


def load_series(include_romaji=False):
    """series stem (JP) -> French rendering. Missing/empty = unresolved."""
    out = {}
    if not os.path.exists(SERIES_TABLE):
        return out
    allowed = set(TRUSTED_ORIGINS)
    if include_romaji:
        allowed.add("romaji")
    with open(SERIES_TABLE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fr = (row.get("fr") or "").strip()
            origin = (row.get("origin") or "hand").strip() or "hand"
            if fr and origin in allowed:
                out[row["jp"]] = fr
    return out


class Parser:
    def __init__(self, vocab):
        self.vocab = vocab
        slots = sorted(vocab["slots"], key=len, reverse=True)
        tiers = sorted(vocab["tiers"], key=len, reverse=True)
        self.slot_re = re.compile("|".join(map(re.escape, slots)))
        self.tier_re = re.compile("|".join(map(re.escape, tiers)))
        self.colours = vocab["colours"]
        self.colour_re = re.compile("[" + "".join(self.colours) + "]")

    def parse(self, jp):
        """Return a component dict, or None if the name is not compositional."""
        s = jp.strip()
        if not s or s == "ダミー":
            return None

        out = {"bracket": None, "cls": None, "tier": None,
               "colour": None, "slot": None, "series": None, "shape": None}

        # 【...】 suffixes are proper names (【鉢金】, 【天頭】) — preserved verbatim.
        m = re.search(r"【(.+?)】", s)
        if m:
            out["bracket"] = m.group(1)
            s = s[: m.start()] + s[m.end():]

        # --- colon variant: ...・頭：剣HS赤 -----------------------------------
        if "：" in s or ":" in s:
            head, _, tail = re.split(r"[：:]", s, maxsplit=1)[0], ":", \
                re.split(r"[：:]", s, maxsplit=1)[1]
            if tail and tail[0] in CLASS_MARKS:
                out["cls"] = tail[0]
                tail = tail[1:]
            t = self.tier_re.match(tail)
            if t:
                out["tier"] = t.group(0)
                tail = tail[t.end():]
            tail = tail.strip("・･")
            if tail and self.colour_re.fullmatch(tail):
                out["colour"] = tail
            elif tail:
                return None  # unrecognised residue — do not guess
            head = head.rstrip("・･")
            if head and head[-1] in KANJI_SLOTS:
                out["slot"] = head[-1]
                head = head[:-1].rstrip("・･")
            else:
                return None
            out["series"] = head
            out["shape"] = "colon"
            return out if out["series"] else None

        # --- dominant variant: SERIES [TIER] SLOT [・COLOUR] ------------------
        s = s.rstrip()
        m = re.search(r"[・･]?(" + self.colour_re.pattern + r")$", s)
        if m:
            out["colour"] = m.group(1)
            s = s[: m.start()]
        s = s.rstrip("・･")

        matches = list(self.slot_re.finditer(s))
        if not matches:
            return None
        m = matches[-1]           # slot noun is the rightmost token
        out["slot"] = m.group(0)
        head, rest = s[: m.start()], s[m.end():]
        if rest.strip("・･ "):
            return None           # trailing junk after the slot — skip

        t = self.tier_re.search(head)
        if t and t.end() == len(head):     # tier sits immediately before slot
            out["tier"] = t.group(0)
            head = head[: t.start()]
        out["series"] = head.rstrip("・･")
        out["shape"] = "dot"
        return out if out["series"] else None


def agree(adj, gender, number):
    """Apply French adjective agreement from the vocab's 4 stored forms."""
    key = ("m" if gender == "m" else "f") + ("p" if number == "p" else "s")
    return adj[key]


def render(parts, vocab, series_map):
    """Build the French name, or None if the series stem is unresolved."""
    slot = vocab["slots"].get(parts["slot"]) or vocab["kanji_slots"].get(parts["slot"])
    if not slot:
        return None
    stem = series_map.get(parts["series"])
    if not stem:
        return None

    words = [slot["fr"], stem]

    if parts["tier"]:
        words.append(vocab["tiers"][parts["tier"]])
    if parts["cls"]:
        words.append(vocab["classes"][parts["cls"]])
    if parts["bracket"]:
        words.append("[" + parts["bracket"] + "]")
    if parts["colour"]:
        adj = vocab["colours"][parts["colour"]]
        words.append(agree(adj, slot["g"], slot["n"]))

    return " ".join(w for w in words if w)


def width(s):
    """Rendered width in half-width units: JP glyphs count double."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def iter_rows():
    for sec in SECTIONS:
        path = os.path.join(HERE, "translations", "fr", "dat", "armors", sec + ".csv")
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                yield sec, row


def cmd_emit_series(args):
    """Dump every distinct series stem with its frequency for hand-resolution."""
    vocab = load_vocab()
    p = Parser(vocab)
    stems = Counter()
    examples = defaultdict(list)
    for sec, row in iter_rows():
        jp = (row["source"] or "").strip()
        parts = p.parse(jp)
        if parts:
            stems[parts["series"]] += 1
            if len(examples[parts["series"]]) < 2:
                examples[parts["series"]].append(jp)

    existing = {}
    if os.path.exists(SERIES_TABLE):
        with open(SERIES_TABLE, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row["jp"]] = row

    with open(SERIES_TABLE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=["jp", "fr", "occurrences", "origin", "example"])
        w.writeheader()
        for stem, n in stems.most_common():
            old = existing.get(stem, {})
            w.writerow({
                "jp": stem,
                "fr": old.get("fr", ""),
                "occurrences": n,
                "origin": old.get("origin", ""),
                "example": " / ".join(examples[stem]),
            })
    print(f"wrote {SERIES_TABLE}: {len(stems)} distinct series stems")
    resolved = sum(n for s, n in stems.items() if existing.get(s, {}).get("fr"))
    print(f"  resolved stems cover {resolved}/{sum(stems.values())} parsed rows")


def cmd_report(args):
    vocab = load_vocab()
    series_map = load_series(args.include_romaji)
    p = Parser(vocab)
    total = parsed = rendered = 0
    unparsed = []
    unresolved = Counter()
    over = []
    for sec, row in iter_rows():
        jp = (row["source"] or "").strip()
        if not jp or jp == "ダミー":
            continue
        total += 1
        parts = p.parse(jp)
        if not parts:
            unparsed.append(jp)
            continue
        parsed += 1
        fr = render(parts, vocab, series_map)
        if not fr:
            unresolved[parts["series"]] += 1
            continue
        rendered += 1
        if width(fr) > 2 * width(jp):
            over.append((jp, fr, width(jp), width(fr)))

    pct = lambda a, b: 100.0 * a / b if b else 0.0
    print(f"armour name rows      : {total}")
    print(f"  parsed by grammar   : {parsed} ({pct(parsed,total):.1f}%)")
    print(f"  fully rendered FR   : {rendered} ({pct(rendered,total):.1f}%)")
    print(f"  blocked on stems    : {sum(unresolved.values())} "
          f"({len(unresolved)} distinct stems unresolved)")
    print(f"  not compositional   : {len(unparsed)} ({pct(len(unparsed),total):.1f}%)")
    print(f"\nwidth: {len(over)} rendered names exceed 2x the JP width")
    for jp, fr, wj, wf in over[:10]:
        print(f"    {jp}  ({wj}) -> {fr}  ({wf})")
    if unresolved:
        print("\ntop unresolved stems:")
        for s, n in unresolved.most_common(15):
            print(f"    {s:14s} {n}")
    if unparsed:
        print("\nsample of non-compositional names (left for human translation):")
        for s in unparsed[:12]:
            print(f"    {s}")


def cmd_apply(args):
    vocab = load_vocab()
    series_map = load_series(args.include_romaji)
    p = Parser(vocab)
    written = 0
    for sec in SECTIONS:
        path = os.path.join(HERE, "translations", "fr", "dat", "armors", sec + ".csv")
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            jp = (row["source"] or "").strip()
            if not jp or (row["target"] or "").strip():
                continue          # never overwrite existing human work
            parts = p.parse(jp)
            if not parts:
                continue
            fr = render(parts, vocab, series_map)
            if not fr:
                continue
            if args.max_width and width(fr) > args.max_width * width(jp):
                continue
            row["target"] = fr
            written += 1
        if not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, lineterminator="\n", fieldnames=["index", "source", "target"])
                w.writeheader()
                w.writerows(rows)
    verb = "would fill" if args.dry_run else "filled"
    print(f"{verb} {written} armour name rows")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--report", action="store_true", help="coverage and width report")
    g.add_argument("--emit-series", action="store_true", help="regenerate the stem table")
    g.add_argument("--apply", action="store_true", help="write targets into the FR CSVs")
    ap.add_argument("--dry-run", action="store_true", help="with --apply, do not write")
    ap.add_argument("--include-romaji", action="store_true",
                    help="also use romaji-proposal stems (needs review)")
    ap.add_argument("--max-width", type=float, default=2.0,
                    help="skip names wider than N x the JP width (default 2.0)")
    args = ap.parse_args()

    if args.report:
        cmd_report(args)
    elif args.emit_series:
        cmd_emit_series(args)
    elif args.apply:
        cmd_apply(args)


if __name__ == "__main__":
    main()
