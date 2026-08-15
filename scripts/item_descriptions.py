#!/usr/bin/env python3
"""
Fill repeated item descriptions from a reviewed phrase table.

`dat/items/description` is written from a small stock of boilerplate. Its
16696 untranslated rows collapse to 5882 distinct strings, and a single
string ("Ｇ級防具を精錬することで作られた装飾品。") accounts for 1952 of them.
Translating those once and applying them everywhere is deterministic work
that does not belong in a translator's queue.

`docs/item_descriptions.fr.csv` is the table: one row per distinct Japanese
string, with occurrence count and (where the English patch has one) an
English hint. Fill the `fr` column; --apply writes it to every matching row.

Only exact whole-string matches are used. Strings containing a katakana run
are marked `has_var` because the run is usually an item or series name that
must be resolved before the sentence can be written; they are listed but
left for later.

Control codes are checked, not trusted: a translation whose {j}, {cNN} and
{/c} markers do not match the source exactly is refused, because a dropped
colour span corrupts the rendered text with no compile-time warning.

Usage:
    python scripts/item_descriptions.py --emit     # (re)generate the table
    python scripts/item_descriptions.py --report
    python scripts/item_descriptions.py --apply
"""

import argparse
import csv
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(HERE, "docs", "item_descriptions.fr.csv")
SECTION = os.path.join("dat", "items", "description")

KATAKANA_RUN = re.compile(r"[ァ-ヶー・]{2,}")
CJK = re.compile(r"[぀-ヿ一-鿿]")
CONTROL = re.compile(r"\{/?c?\d*\}|\{j\}")
FIELDS = ["jp", "fr", "occurrences", "has_var", "en_hint"]


def path_for(lang):
    return os.path.join(HERE, "translations", lang, SECTION + ".csv")


def read(lang):
    with open(path_for(lang), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def control_codes(s):
    """Ordered list of control markers, which a translation must reproduce."""
    return CONTROL.findall(s)


def load_table():
    if not os.path.exists(TABLE):
        return {}
    with open(TABLE, encoding="utf-8") as f:
        return {r["jp"]: r for r in csv.DictReader(f)}


def cmd_emit(args):
    fr_rows = read("fr")
    en_by_index = {r["index"]: (r["target"] or "").strip() for r in read("en")}

    counts = Counter()
    hints = {}
    for r in fr_rows:
        s = (r["source"] or "").strip()
        if not s or (r["target"] or "").strip():
            continue
        counts[s] += 1
        if s not in hints:
            e = en_by_index.get(r["index"], "")
            e_clean = CONTROL.sub(" ", e).strip()
            hints[s] = e if e_clean and not CJK.search(e_clean) else ""

    existing = load_table()
    with open(TABLE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=FIELDS)
        w.writeheader()
        for s, n in counts.most_common():
            old = existing.get(s, {})
            w.writerow({
                "jp": s,
                "fr": old.get("fr", ""),
                "occurrences": n,
                "has_var": "yes" if KATAKANA_RUN.search(s) else "",
                "en_hint": hints.get(s, ""),
            })
    filled = sum(n for s, n in counts.items() if existing.get(s, {}).get("fr"))
    print(f"wrote {TABLE}: {len(counts)} distinct strings, {sum(counts.values())} rows")
    print(f"  already translated in table: {filled} rows")


def check(table):
    """Return (usable, problems) after verifying control-code parity."""
    usable, problems = {}, []
    for jp, row in table.items():
        fr = (row.get("fr") or "").strip()
        if not fr:
            continue
        if control_codes(jp) != control_codes(fr):
            problems.append((jp, fr))
            continue
        usable[jp] = fr
    return usable, problems


def cmd_report(args):
    table = load_table()
    usable, problems = check(table)
    rows = read("fr")
    fillable = sum(1 for r in rows
                   if (r["source"] or "").strip() in usable
                   and not (r["target"] or "").strip())
    untranslated = sum(1 for r in rows
                       if (r["source"] or "").strip() and not (r["target"] or "").strip())
    const = sum(int(r["occurrences"]) for r in table.values() if not r["has_var"])
    var = sum(int(r["occurrences"]) for r in table.values() if r["has_var"])
    print(f"untranslated rows in {SECTION}: {untranslated}")
    print(f"  distinct strings          : {len(table)}")
    print(f"  constant strings          : {const} rows")
    print(f"  strings with a katakana var: {var} rows (left for later)")
    print(f"  table entries filled      : {len(usable)}")
    print(f"  rows fillable now         : {fillable}")
    if problems:
        print(f"\nREFUSED - control codes do not match the source ({len(problems)}):")
        for jp, fr in problems[:10]:
            print(f"    src {control_codes(jp)} != tgt {control_codes(fr)}")
            print(f"      {jp[:60]!r}")


def cmd_apply(args):
    table = load_table()
    usable, problems = check(table)
    if problems:
        print(f"refusing to apply: {len(problems)} entries have mismatched "
              f"control codes (run --report)")
        return
    path = path_for("fr")
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    n = 0
    for r in rows:
        s = (r["source"] or "").strip()
        if s in usable and not (r["target"] or "").strip():
            r["target"] = usable[s]
            n += 1
    if not args.dry_run:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, lineterminator="\n",
                               fieldnames=["index", "source", "target"])
            w.writeheader()
            w.writerows(rows)
    print(f"{'would fill' if args.dry_run else 'filled'} {n} rows from "
          f"{len(usable)} table entries")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--report", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.emit:
        cmd_emit(args)
    elif args.report:
        cmd_report(args)
    else:
        cmd_apply(args)


if __name__ == "__main__":
    main()
