#!/usr/bin/env python3
"""
Re-extract the `source` column from unpatched Japanese game files.

The repository was bootstrapped from binaries partly patched by an older
English fan translation. In pac, gao, jmp, rcc and inf, `source` held that
patch's English ("Do you want to jump?" where the game says ジャンプしますか？),
and quest text overwritten in place was left truncated. Translators then worked
from the wrong reference, and stats.py dropped those rows from coverage because
they had no Japanese.

This script extracts every section again with FrontierTextHandler from a
folder of unpatched files and sets each row's `source` to it, by index.
Targets are kept: a translation made from the English text still means the
same thing. A section whose row count differs from the game file is skipped
and reported, as its indexes cannot be trusted.

With --carry-en, a row whose old source was English also gets that English
as its `en` target when the `en` target is empty: it is the fan patch's
translation of that very row.

Needs FrontierTextHandler >= 1.9.0 (grouped pac tables).

Usage:
    python scripts/resync_sources.py --fth-dir ../FrontierTextHandler \\
        --game-dir path/to/unpatched/dat --report
    python scripts/resync_sources.py --fth-dir ../FrontierTextHandler \\
        --game-dir path/to/unpatched/dat --apply --carry-en
"""

import argparse
import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path

CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")


def is_english(text: str) -> bool:
    return bool(LATIN_WORD.search(text)) and not CJK.search(text)


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=["index", "source", "target"])
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--fth-dir", required=True, type=Path)
    parser.add_argument("--game-dir", required=True, type=Path,
                        help="Folder with unpatched Japanese mhf*.bin files")
    parser.add_argument("--translations-dir", type=Path, default=Path("translations"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--report", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--carry-en", action="store_true",
                        help="Keep a replaced English source as the en target when empty")
    args = parser.parse_args()

    sys.path.insert(0, str(args.fth_dir.resolve()))
    logging.disable(logging.WARNING)
    from src import common  # type: ignore[import]
    from src.export import translation_document  # type: ignore[import]

    decoded: dict[str, bytes | None] = {}
    extracted: dict[str, list[str] | None] = {}

    def game_sources(xpath: str) -> list[str] | None:
        if xpath not in extracted:
            file_type = xpath.split("/")[0]
            if file_type not in decoded:
                path = args.game_dir / f"mhf{file_type}.bin"
                decoded[file_type] = common.load_file_data(str(path)) if path.exists() else None
            data = decoded[file_type]
            extracted[xpath] = None if data is None else [
                row["source"] for row in translation_document(
                    common.extract_text_data_from_bytes(data, common.read_extraction_config(xpath)),
                    f"mhf{file_type}.bin", xpath=xpath,
                )["strings"]
            ]
        return extracted[xpath]

    totals = Counter()
    for lang_dir in sorted(p for p in args.translations_dir.iterdir() if p.is_dir()):
        lang = lang_dir.name
        for path in sorted(lang_dir.rglob("*.csv")):
            xpath = path.relative_to(lang_dir).with_suffix("").as_posix()
            rows = read_csv(path)
            game = game_sources(xpath)
            if game is None:
                print(f"{lang} {xpath}: skipped, no game file")
                continue
            if len(game) != len(rows):
                print(f"{lang} {xpath}: skipped, {len(rows)} rows but the game file has {len(game)}")
                continue
            changed = english = carried = 0
            for r in rows:
                new = game[int(r["index"])]
                if r["source"] == new:
                    continue
                changed += 1
                english += is_english(r["source"])
                if args.carry_en and lang == "en" and not r["target"] and is_english(r["source"]):
                    r["target"] = r["source"]
                    carried += 1
                r["source"] = new
            if not changed:
                continue
            note = f", {carried} kept as en targets" if carried else ""
            print(f"{lang} {xpath}: {changed} source(s) updated ({english} were English){note}")
            totals["changed"] += changed
            totals["english"] += english
            totals["carried"] += carried
            if args.apply:
                write_csv(path, rows)

    verb = "updated" if args.apply else "would update"
    print(f"\n{verb} {totals['changed']} source(s) across languages "
          f"({totals['english']} were English)"
          + (f"; {totals['carried']} English text(s) kept as en targets" if args.carry_en else ""))


if __name__ == "__main__":
    main()
