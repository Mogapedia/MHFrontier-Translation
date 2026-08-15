#!/usr/bin/env python3
"""
One-shot: re-decode text extracted with the wrong Shift-JIS variant.

FrontierTextHandler read game text as `shift_jisx0213` until 1.7.0. MHF is a
Japanese Windows title, so its bytes are CP932. The two agree on ordinary kana
and kanji but diverge in the NEC-selected IBM-extended area, which is where the
game keeps its Roman numerals:

    bytes 0xFA4A-0xFA53   CP932: Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ
                 shift_jisx0213: 貤 賖 賕 賙 𧶠 賰 賱 𧸐 贉 贎

So a weapon named ダガダイアⅡ is stored here as ダガダイア賖. This must be fixed
in the CSVs and not only in FTH: those characters have no CP932 encoding at
all, so once FTH is on the right codec they fail on import.

The mapping is not hand-written. Every character in the corpus is round-tripped
`encode(shift_jisx0213)` then `decode(cp932)`; anything that changes is a
character the old codec got wrong, and the pair is recorded. A hand-list would
be as complete as whatever happened to be noticed.

Only characters that came out of the binary are touched. French and English
targets are left alone: the transform is applied per-character from that
derived table, never by re-encoding whole strings, so translator-written text
(é, œ, « ») cannot be caught up in it.

Usage:
    python scripts/migrate_cp932.py --report
    python scripts/migrate_cp932.py --apply
"""

import argparse
import csv
import glob
import os
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_mapping(texts):
    """char -> corrected char, derived by re-decoding under the right codec."""
    mapping, seen = {}, set()
    for t in texts:
        for ch in t:
            if ch in seen:
                continue
            seen.add(ch)
            try:
                fixed = ch.encode("shift_jisx0213").decode("cp932")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue          # not from the binary, or not representable
            if fixed != ch and len(fixed) == 1:
                mapping[ch] = fixed
    return mapping


def csv_paths():
    return sorted(glob.glob(os.path.join(HERE, "translations", "**", "*.csv"),
                            recursive=True))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--report", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    paths = csv_paths()

    # Derive the mapping from the source columns only. They are the text that
    # actually came out of the binary; targets are written by translators.
    sources = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            sources.extend((r["source"] or "") for r in csv.DictReader(f))
    mapping = build_mapping(sources)

    print(f"derived mapping ({len(mapping)} characters):")
    for a, b in sorted(mapping.items(), key=lambda kv: kv[1]):
        print(f"    {a!r} U+{ord(a):04X}  ->  {b!r} U+{ord(b):04X}")

    changed = Counter()
    files_touched = 0
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        dirty = False
        for r in rows:
            for col in ("source", "target"):
                v = r.get(col) or ""
                if not v:
                    continue
                new = "".join(mapping.get(c, c) for c in v)
                if new != v:
                    for c in v:
                        if c in mapping:
                            changed[(c, mapping[c], col)] += 1
                    r[col] = new
                    dirty = True
        if dirty:
            files_touched += 1
            if args.apply:
                with open(p, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, lineterminator="\n",
                                       fieldnames=["index", "source", "target"])
                    w.writeheader()
                    w.writerows(rows)

    verb = "fixed" if args.apply else "would fix"
    print(f"\n{verb} {sum(changed.values())} characters in {files_touched} file(s)")
    per_col = Counter()
    for (a, b, col), n in changed.items():
        per_col[(a, b)] += n
    for (a, b), n in per_col.most_common():
        print(f"    {a} -> {b}   {n}")


if __name__ == "__main__":
    main()
