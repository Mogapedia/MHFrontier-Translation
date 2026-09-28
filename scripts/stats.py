#!/usr/bin/env python3
"""Generate translation statistics as JSON.

Usage:
    python scripts/stats.py                        # writes stats.json
    python scripts/stats.py --output my-stats.json
    python scripts/stats.py translations/fr/       # single language
"""

import csv
import json
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

# A row is "translatable" only if its source contains at least one CJK
# character. This single rule excludes:
#   - control-code-only rows (e.g. `{j}{j}` padding slots in pointer
#     tables that share data with other slots),
#   - `dummy` placeholders in fixed-size pointer tables,
#   - numeric/empty placeholders like "0" for unused slots,
#   - English internal names left in the game file (`Z3P_item_089`).
# See CLAUDE.md "What not to trust".
_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _is_translatable(source: str) -> bool:
    return bool(_CJK_RE.search(source or ""))


def _is_translated(target: str) -> bool:
    # A target only counts as translated if it's non-empty AND contains no
    # leftover CJK characters. This filters out partial pass-throughs like
    # "忍の Kote・陽" where only one word was Romanized — common in the
    # legacy English bootstrap.
    t = (target or "").strip()
    if not t:
        return False
    return not _CJK_RE.search(t)


def stats_for_file(csv_path: Path) -> dict:
    total = translated = 0
    try:
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not _is_translatable(row.get("source", "")):
                    continue
                total += 1
                if _is_translated(row.get("target", "")):
                    translated += 1
    except Exception as e:
        print(f"Warning: could not read {csv_path}: {e}", flush=True)
    return {
        "total": total,
        "translated": translated,
        "untranslated": total - translated,
        "coverage": round(translated / total * 100, 1) if total else 0.0,
    }


def compute_lang_stats(lang_dir: Path) -> dict:
    lang_stats: dict = {"total": 0, "translated": 0, "untranslated": 0, "files": {}}
    for csv_file in sorted(lang_dir.rglob("*.csv")):
        xpath = csv_file.relative_to(lang_dir).with_suffix("").as_posix()
        fs = stats_for_file(csv_file)
        lang_stats["files"][xpath] = fs
        lang_stats["total"] += fs["total"]
        lang_stats["translated"] += fs["translated"]
        lang_stats["untranslated"] += fs["untranslated"]
    total = lang_stats["total"]
    lang_stats["coverage"] = (
        round(lang_stats["translated"] / total * 100, 1) if total else 0.0
    )
    return lang_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate translation statistics")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["translations"],
        help="translations/ root or individual language directories (default: translations/)",
    )
    parser.add_argument("--output", default="stats.json", help="Output JSON file")
    args = parser.parse_args()

    result: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "languages": {},
    }

    XPATH_NAMESPACES = {"dat", "pac", "inf", "jmp"}

    for path_str in args.paths:
        root = Path(path_str)
        if not root.exists():
            print(f"Warning: {root} does not exist, skipping")
            continue

        child_dirs = [d for d in root.iterdir() if d.is_dir()]
        # A language directory contains xpath-namespace subdirs (dat/, pac/, …)
        # The translations/ root contains language-code subdirs (fr/, en/, …)
        is_lang_dir = any(d.name in XPATH_NAMESPACES for d in child_dirs)

        if is_lang_dir:
            lang = root.name
            if lang not in result["languages"]:
                result["languages"][lang] = compute_lang_stats(root)
        else:
            for lang_dir in sorted(child_dirs):
                lang = lang_dir.name
                if lang not in result["languages"] and any(lang_dir.rglob("*.csv")):
                    result["languages"][lang] = compute_lang_stats(lang_dir)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print summary
    for lang, ls in result["languages"].items():
        print(
            f"  {lang}: {ls['translated']}/{ls['total']} strings translated "
            f"({ls['coverage']}%)"
        )
    print(f"Stats written to {args.output}")


if __name__ == "__main__":
    main()
