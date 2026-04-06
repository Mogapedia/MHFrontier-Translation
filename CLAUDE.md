# CLAUDE.md

Project-specific guidance for the MHFrontier-Translation repository.

## Project role

Per-section CSV translations of Monster Hunter Frontier text, organized as
`translations/<lang>/<xpath>.csv`. Source data is extracted via
[FrontierTextHandler](../../tools/FrontierTextHandler) (see sibling
`mhfrontier/tools/FrontierTextHandler/CLAUDE.md`).

## Copyright posture on Japanese source text

The original Japanese strings in the `source` column belong to Capcom, but
hosting them here is consistent with established community practice and the
practical risk is very low:

- Sibling projects already host JP source publicly: `Frontier-Translation-Weblate`,
  `FrontierTextHandler` (per-section CSV outputs), `Erupe` (Go enums and packet
  strings), `mhf-patterns` (ImHex patterns).
- Weblate-based fan translations of other JP games (FFXI, Trails, Yakuza, …)
  have hosted source strings on GitHub for years without incident.
- Capcom's MH-related enforcement has targeted ROMs, asset rips, and server
  emulators — never translation source strings. MHF was shut down in 2019
  with no successor, so the preservation defense is strong.
- Short UI strings (item names, skill names, menu labels) have weak-to-no
  copyright protection individually.

**Practical guidance**: commit JP source freely for item names, skill names,
armor/weapon names, and UI strings. Be more deliberate about bulk-importing
**scenario scripts, NPC monologues, and quest dialogue** — these are the only
category where the creative-content argument has any weight. Even there, the
risk is low; just avoid pasting huge blocks into public issue trackers or
commit messages where they'd be indexed without context.

## Layout

```
translations/
  fr/                 ← French (primary)
  en/                 ← English (bootstrapped from polluted source rows)
scripts/
  validate.py         ← CSV format check
  stats.py            ← coverage report → stats.json
  export_json.py      ← bundle for FrontierTextHandler --merge-json
  migrate.py          ← import a monolithic Weblate CSV
  cleanup.py          ← classify rows, bootstrap translations/en/
```

## Known data quality issues

1. **English-as-source pollution**: the PC binary used for extraction had
   been partially patched by an older English fan-translation, leaving English
   in the `source` column for ~799 rows in `pac/text_*` and `jmp/menu/*`.
   FTH's `data/mhf*-jp.bin` reference files are themselves contaminated
   (3,188 English-source rows). **Partially fixed** by cracking the v2064 Wii U
   dump (`mhfrontier/client/wiiu/Monster Hunter Frontier G [0005000E1014DA00]
   (v2064)/`) with `cdecrypt`, extracting via FTH, and row-index matching
   sections with identical row counts — see `scripts/fix_pollution.py`. This
   recovered 130 rows across 17 sections. The remaining ~669 polluted rows
   live in 8 sections whose row counts differ between PC and Wii U
   (`pac/text_34`, `pac/text_40`, `dat/items/name`, etc.) and would need
   sequence alignment or a fresh unpatched PC JP dump.
2. **Dummy rows** (1,348 in fr/, 1,211 confirmed in `dat/items/source.csv`):
   literal `dummy` strings embedded in the binary at fixed offsets. Confirmed
   as **real unimplemented item-source slots**: they appear identically in
   every PC binary extracted (contaminated and "JP" reference), so they are
   not an extraction artifact. The game keeps a fixed-size offset table for
   item-source descriptions and pads unused entries with `dummy`. Safe to
   leave with empty target — they don't render in-game.
3. **Control-code rows** (~6,643): `<join at=...>` glue and color codes — not
   translatable on their own.

Run `python scripts/cleanup.py --audit` for the current breakdown.

## Workflows

```bash
python scripts/validate.py                       # validate all CSVs
python scripts/stats.py                          # regenerate stats.json
python scripts/cleanup.py --audit                # classify rows
python scripts/cleanup.py --bootstrap-en         # mirror fr/ → en/
python scripts/migrate.py --extracted-dir <FTH-output> \
    --translated <weblate.csv> --lang fr         # import Weblate dump
```
