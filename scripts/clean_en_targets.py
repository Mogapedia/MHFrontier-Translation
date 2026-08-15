#!/usr/bin/env python3
"""
Blank English targets that are not translations of their own source row.

`translations/en/` was bootstrapped from a binary that had been patched by an
older fan translation (commit 7379bfb). That binary was not the same build as
the Japanese dump the `source` column comes from, so a large part of the
`target` column holds text belonging to *other* rows: untranslated Japanese
from a different pointer table, and in a few hundred cases Traditional Chinese
from the Taiwanese release.

`dat/equipment/description` is the worst case — 47095 of its 54165 non-empty
targets contain CJK, and none of that is English.

This never inflated the coverage figures: `stats.py` already refuses to count
a target containing CJK. What it does corrupt is everything that reads the
column directly — translation-memory lookups, `export_json.py`, and any build
that trusts `target` to be English. A row showing a full Japanese description
in the English column is also simply wrong to ship.

What is *kept* is decided per row, never by position:

  - a target with no CJK at all is English, and English is only ever produced
    by a translator looking at that row: keep it;
  - a target that mixes Japanese and English is a half-finished row. Keep it
    only if it also shares a `{j}` segment with its own source, which is what
    proves it belongs to this row and not to a neighbour;
  - anything else that contains CJK is displaced text: blank it;
  - a row whose source is a placeholder ('0', 'ダミー', empty) has nothing to
    translate, so any target it carries came from somewhere else: blank it.

Alignment of the surviving English was checked before writing this: on
`dat/equipment/description`, JP slot words (頭用/胴用/腕用/腰用/脚用) agree with
English slot words (headgear/mail/vambraces/coil/greaves) in 95.6% of the
1220 rows where both are unambiguous, evenly across all six regions of the
file. The English column is correctly keyed; only the CJK is displaced.

This does not delete any translation. Everything it removes is Japanese or
Chinese sitting in a column reserved for English.

Usage:
    python scripts/clean_en_targets.py --survey            # all en/ sections
    python scripts/clean_en_targets.py --report <section>  # one section
    python scripts/clean_en_targets.py --apply  <section>
"""

import argparse
import csv
import glob
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KANA = re.compile(r"[ぁ-ゖァ-ヺー]")
HAN = re.compile(r"[一-鿿]")
COLOUR = re.compile(r"\{/?c\d*\}")
PLACEHOLDER = {"", "0", "ダミー"}


def has_cjk(s):
    return bool(KANA.search(s) or HAN.search(s))


def segments(s):
    """`{j}` join markers and newlines both start a new rendered line."""
    return [x.strip() for x in re.split(r"\{j\}|\n", COLOUR.sub("", s)) if x.strip()]


def classify(source, target):
    """Return (keep, reason). Only called for non-empty targets."""
    src = source.strip()
    tgt = target.strip()

    if src in PLACEHOLDER:
        return False, "source is a placeholder"
    if tgt == src:
        return False, "target copies source"
    if not has_cjk(tgt):
        return True, "english"

    seg_s, seg_t = set(segments(src)), segments(target)
    shared = [x for x in seg_t if x in seg_s]
    english = [x for x in seg_t if not has_cjk(x)]
    if shared and english:
        return True, "partial translation"
    if shared:
        return False, "japanese, overlaps source but adds nothing"
    return False, "displaced text"


def process(path):
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    rows = list(csv.DictReader(raw.splitlines(True)))

    stats = {}
    for r in rows:
        t = (r["target"] or "").strip()
        if not t:
            stats["empty"] = stats.get("empty", 0) + 1
            continue
        keep, reason = classify(r["source"] or "", r["target"] or "")
        key = ("keep: " if keep else "blank: ") + reason
        stats[key] = stats.get(key, 0) + 1
        if not keep:
            r["_blank"] = True
    return rows, stats, crlf


LATIN_WORD = re.compile(r"[A-Za-z]{3,}")


def salvage(section, rows):
    """Blanked rows still holding an English fragment, keyed to nothing.

    The fragment is real English from the patch, but it sits against a source
    it does not translate, so it cannot stay in the column. Its own Japanese
    neighbours usually identify the row it *does* belong to, which makes
    re-keying possible later; this file is that queue.
    """
    out = []
    for r in rows:
        if not r.get("_blank"):
            continue
        t = r["target"] or ""
        if LATIN_WORD.search(COLOUR.sub("", t).replace("{j}", "")):
            out.append({"section": section, "index": r["index"],
                        "source": r["source"], "orphan_target": t})
    if not out:
        return 0
    path = os.path.join(HERE, "docs", "en_orphan_fragments.csv")
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = [r for r in csv.DictReader(f) if r["section"] != section]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n",
                           fieldnames=["section", "index", "source", "orphan_target"])
        w.writeheader()
        w.writerows(existing + out)
    return len(out)


def write(path, rows, crlf):
    for r in rows:
        if r.pop("_blank", False):
            r["target"] = ""
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\r\n" if crlf else "\n",
                           fieldnames=["index", "source", "target"])
        w.writeheader()
        w.writerows(rows)


def section_path(section):
    return os.path.join(HERE, "translations", "en", section + ".csv")


def cmd_survey():
    print(f"{'section':44s} {'rows':>7s} {'filled':>7s} {'blank':>7s} {'%lost':>6s}")
    total_b = total_f = 0
    for path in sorted(glob.glob(os.path.join(HERE, "translations", "en", "**", "*.csv"),
                                 recursive=True)):
        rows, stats, _ = process(path)
        filled = sum(n for k, n in stats.items() if k != "empty")
        blanked = sum(n for k, n in stats.items() if k.startswith("blank"))
        if not blanked:
            continue
        rel = os.path.relpath(path, os.path.join(HERE, "translations", "en"))[:-4]
        pct = blanked / filled * 100 if filled else 0
        print(f"{rel:44s} {len(rows):7d} {filled:7d} {blanked:7d} {pct:5.1f}%")
        total_b += blanked
        total_f += filled
    print(f"{'TOTAL':44s} {'':7s} {total_f:7d} {total_b:7d} "
          f"{total_b / total_f * 100 if total_f else 0:5.1f}%")


def cmd_one(section, apply_):
    path = section_path(section)
    rows, stats, crlf = process(path)
    print(f"{section}  ({len(rows)} rows, {'CRLF' if crlf else 'LF'})")
    for k in sorted(stats):
        print(f"   {stats[k]:7d}  {k}")
    if apply_:
        n = salvage(section, rows)
        write(path, rows, crlf)
        print(f"written. {n} English fragments queued in docs/en_orphan_fragments.csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("section", nargs="?", help="e.g. dat/equipment/description")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--survey", action="store_true")
    g.add_argument("--report", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.survey:
        cmd_survey()
    else:
        if not args.section:
            ap.error("a section is required with --report/--apply")
        cmd_one(args.section, args.apply)


if __name__ == "__main__":
    main()
