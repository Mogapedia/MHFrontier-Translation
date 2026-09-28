#!/usr/bin/env python3
"""Build translated MHF binary game files from CSV translations.

Uses FrontierTextHandler (must be cloned or already present) to apply all
CSV translations for a given language and write compressed+encrypted binary
files ready to drop into the game directory.

Output names follow the mhf-outpost convention: <lang>-<original>.bin
  fr-mhfdat.bin, fr-mhfpac.bin, fr-mhfinf.bin, fr-mhfjmp.bin

Usage:
  python scripts/build_bins.py --fth-dir fth --lang fr --out release/

Local testing:
  python scripts/build_bins.py \\
    --fth-dir ../tools/FrontierTextHandler \\
    --lang fr --out /tmp/release
"""

import argparse
import shutil
import sys
from pathlib import Path

# (translations sub-directory, source binary in FTH data/, output filename)
SECTIONS = [
    ("dat", "mhfdat-jp.bin", "mhfdat.bin"),
    ("pac", "mhfpac.bin",    "mhfpac.bin"),
    ("inf", "mhfinf.bin",    "mhfinf.bin"),
    ("jmp", "mhfjmp.bin",    "mhfjmp.bin"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fth-dir", required=True, type=Path,
        help="Path to a FrontierTextHandler checkout",
    )
    parser.add_argument(
        "--lang", default="fr",
        help="Language code to build (default: fr)",
    )
    parser.add_argument(
        "--translations-dir", type=Path, default=Path("translations"),
        help="Root of the translations directory (default: translations/)",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("release"),
        help="Output directory (default: release/)",
    )
    args = parser.parse_args()

    fth_dir = args.fth_dir.resolve()
    trans_root = args.translations_dir.resolve() / args.lang
    out_dir = args.out.resolve()
    # FTH >= 1.9.0 ships headers.json inside its package.
    headers_json = fth_dir / "src" / "headers.json"

    if not fth_dir.exists():
        sys.exit(f"ERROR: FrontierTextHandler not found at {fth_dir}")
    if not headers_json.exists():
        sys.exit(f"ERROR: headers.json not found at {headers_json}")
    if not trans_root.exists():
        sys.exit(f"ERROR: no translations for '{args.lang}' at {trans_root}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Import FrontierTextHandler directly so we control headers_path and output
    # locations without depending on the current working directory.
    sys.path.insert(0, str(fth_dir))
    try:
        from src.import_data import import_from_csv  # type: ignore[import]
        from src.jkr_compress import compress_jkr_hfi  # type: ignore[import]
        from src.crypto import encrypt  # type: ignore[import]
    except ImportError as exc:
        sys.exit(f"ERROR: cannot import FrontierTextHandler from {fth_dir}: {exc}")

    failures = 0
    for section, src_name, out_name in SECTIONS:
        csv_dir = trans_root / section
        if not csv_dir.exists():
            print(f"[{section}] skip — {csv_dir} not found")
            continue

        csvs = sorted(csv_dir.rglob("*.csv"))
        if not csvs:
            print(f"[{section}] skip — no CSV files in {csv_dir}")
            continue

        src_bin = fth_dir / "data" / src_name
        if not src_bin.exists():
            print(f"[{section}] ERROR: base binary not found: {src_bin}", file=sys.stderr)
            failures += 1
            continue

        dest = out_dir / f"{args.lang}-{out_name}"
        # Working copy: raw (no compress/encrypt) so each step is fast.
        working = out_dir / f"_work_{src_name}"
        shutil.copy2(src_bin, working)
        print(f"\n[{section}] {dest.name}  ({len(csvs)} CSV(s))")

        applied = 0
        for csv in csvs:
            rel = csv.relative_to(trans_root.parent.parent)
            # xpath = path under translations/<lang>/, sans .csv
            xpath = str(csv.relative_to(trans_root).with_suffix("")).replace("\\", "/")
            print(f"  applying {rel}  (xpath={xpath})")
            result = import_from_csv(
                input_file=str(csv),
                output_file=str(working),
                output_path=str(working),  # write back to the same file
                compress=False,            # keep raw during intermediate steps
                encrypt=False,             # single compress+encrypt pass at the end
                xpath=xpath,
                headers_path=str(headers_json),
                # CP932 has no accented Latin: fold é → e and the like.
                fold_unsupported_chars=True,
            )
            if result is not None:
                applied += 1

        # Single compress+encrypt pass — much faster than per-CSV re-encryption.
        print(f"  compressing and encrypting…")
        raw = working.read_bytes()
        compressed = compress_jkr_hfi(raw)
        game_ready = encrypt(compressed)
        dest.write_bytes(game_ready)
        working.unlink()

        print(f"  ✓ {applied}/{len(csvs)} CSV(s) had translations  ({dest.stat().st_size:,} B)")

    if failures:
        sys.exit(f"\n{failures} section(s) failed.")
    print(f"\nDone. Translated binaries written to {out_dir}/")


if __name__ == "__main__":
    main()
