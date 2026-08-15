#!/usr/bin/env python3
"""
Restore French accents and the oe ligature in translated targets.

Part of the French corpus was seeded from a binary that had been ASCII-folded,
so it carries "Ecaille", "Oeuf", "tenacite" where style.fr.md requires
"Écaille", "Œuf", "ténacité". The CSVs are the source of truth and must hold
correct French; folding for the game engine is a build-time concern.

Only unambiguous cases are touched:

  - the unaccented form must NOT itself be a valid French word, so "cote"
    is never turned into "côte" and "sur" is never turned into "sûr";
  - exactly ONE accented word may fold to it. "medaille" folds to both
    "médaille" and "médaillé", and "peche" to both "pêche" and "péché", so
    both are skipped rather than guessed;
  - proper nouns are excluded wholesale, taken from the armour series table
    and the monster list, so series stems keep their spelling.

Everything skipped is reported by --report so it can be fixed by hand.

Usage:
    python scripts/fix_accents.py --report   # what would change, and what is ambiguous
    python scripts/fix_accents.py --apply
"""

import argparse
import csv
import glob
import os
import re
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR_DIC = "/usr/share/hunspell/fr_FR.dic"

WORD = re.compile(r"[A-Za-zÀ-ÿŒœ'-]+")

# Short function words and homographs where the bare form is legitimate French.
SAFE = {
    "du", "le", "de", "ou", "la", "a", "ete", "des", "les", "ce", "ca", "sur",
    "ma", "mur", "tache", "pate", "sale", "cote", "foret", "age", "mat",
    "entree", "marche", "pere", "mere", "frere", "notre", "votre", "es",
    "medulla",           # Latin anatomical term Capcom keeps unaccented
}

LIGATURE = {
    "oeuf": "œuf", "oeufs": "œufs", "coeur": "cœur", "coeurs": "cœurs",
    "voeu": "vœu", "voeux": "vœux", "soeur": "sœur", "soeurs": "sœurs",
    "oeuvre": "œuvre", "oeuvres": "œuvres", "boeuf": "bœuf",
}


def fold(s):
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn")


def build_map():
    """folded form -> accented form, only where the mapping is unambiguous."""
    words = set()
    with open(FR_DIC, encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.split("/")[0].strip().lower()
            if w and w.replace("-", "").isalpha():
                words.add(w)
    cand = defaultdict(set)
    for w in words:
        f_ = fold(w)
        if f_ != w and f_ not in words:
            cand[f_].add(w)
    unambiguous = {k: next(iter(v)) for k, v in cand.items() if len(v) == 1}
    ambiguous = {k: sorted(v) for k, v in cand.items() if len(v) > 1}
    return unambiguous, ambiguous


def load_proper_nouns():
    names = set()
    for path in ("docs/armor_series.fr.csv", "docs/monster_names.fr.csv"):
        p = os.path.join(HERE, path)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                for w in WORD.findall(row.get("fr") or ""):
                    names.add(w.lower())
    return names


def match_case(src, repl):
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def fix_text(text, mapping, names):
    changed = Counter()

    def sub(m):
        w = m.group(0)
        lw = w.lower()
        if lw in LIGATURE:
            changed[(lw, LIGATURE[lw])] += 1
            return match_case(w, LIGATURE[lw])
        if lw in SAFE or lw in names:
            return w
        if lw in mapping:
            changed[(lw, mapping[lw])] += 1
            return match_case(w, mapping[lw])
        return w

    return WORD.sub(sub, text), changed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--report", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    mapping, ambiguous = build_map()
    names = load_proper_nouns()

    total = Counter()
    skipped = Counter()
    files_changed = 0

    for path in sorted(glob.glob(os.path.join(HERE, "translations", "fr", "**", "*.csv"),
                                 recursive=True)):
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        dirty = False
        for r in rows:
            t = r.get("target") or ""
            if not t:
                continue
            new, changed = fix_text(t, mapping, names)
            for w in WORD.findall(t):
                lw = w.lower()
                if lw in ambiguous and lw not in names and lw not in SAFE:
                    skipped[(lw, " | ".join(ambiguous[lw]))] += 1
            if new != t:
                r["target"] = new
                total.update(changed)
                dirty = True
        if dirty:
            files_changed += 1
            if args.apply:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, lineterminator="\n",
                                       fieldnames=["index", "source", "target"])
                    w.writeheader()
                    w.writerows(rows)

    verb = "fixed" if args.apply else "would fix"
    print(f"{verb} {sum(total.values())} occurrences "
          f"({len(total)} distinct words) across {files_changed} file(s)")
    for (a, b), c in total.most_common(25):
        print(f"    {a:16s} -> {b:16s} {c}")
    if skipped:
        print(f"\nskipped as ambiguous ({sum(skipped.values())} occurrences) "
              f"- fix these by hand:")
        for (a, opts), c in skipped.most_common(15):
            print(f"    {a:16s} could be {opts:28s} {c}")


if __name__ == "__main__":
    main()
