# Changelog

All notable changes to MHFrontier-Translation are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

Versioning: **MAJOR** = breaking format change, **MINOR** = new translations
or sections, **PATCH** = fixes to existing translations.

## [0.3.0] - 2026-09-28

**Breaking**: requires **FrontierTextHandler >= 1.9.0**. Earlier versions
read the grouped `pac/text_14`…`text_54` tables one row per pointer and cannot
import these CSVs, fail on accented text in `--apply-translations`, and
(before 1.8.0) cannot encode the CP932-corrected characters.

Coverage: French 3,090 → 63,023 translated strings, English 97,672 → 97,957
(`stats.py`).

### Added

- **fr/**: armour names generated from their compositional grammar
  (`scripts/armor_names.py`), with series stems, slots and colours.
- **fr/**: repeated item descriptions from a phrase table, item sources
  (monster, training, system templates), ranks, `pac/text_40` system
  messages, control bindings, header labels and menu UI strings.
- **fr/**: Capcom's official French item names as a reference table
  (`docs/capcom_items.fr.csv`), with the differences recorded.
- **pac/**: menu UI sections (`pac/menu/*`) in French and English.
- `scripts/resync_sources.py`: re-extract `source` from unpatched game files.
- `validate.py` rejects a target that drops a `~ANN`/`~BNN` substitution
  code (a key name or slot number in game; #4).

### Changed

- **fr/**: current Capcom terminology over Freedom-era terms; 狩護 is
  « Chassegarde », 装飾品 is « joyau ».
- All line endings normalised to LF.

### Fixed

- **Sources are Japanese again.** pac, gao, jmp, rcc and inf had been
  extracted from a binary patched by an English fan translation: ~3,000
  `source` rows held English and quest text was truncated. Re-extracted from
  the unpatched client; the English moved to `en` targets where empty.
- **Encoding**: text extracted as `shift_jisx0213` migrated to CP932
  (Roman numerals Ⅰ–Ⅹ were mojibake).
- **en/**: blanked targets that belong to other rows (displaced Japanese and
  Chinese, `0` placeholders, wrong `{j}` segment counts). The English build
  now succeeds; before, it dropped every equipment description.
- **fr/**: accents restored.
- `build_bins.py` works with FTH 1.9.0 (`src/headers.json`, accent folding).
- README and release notes: correct application instructions.

## [0.2.0] - 2026-04-12

**Breaking**: requires **FrontierTextHandler >= 1.6.0**.

### Changed

- Migrated join markers from `<join at="NNN">` to `{j}` (477,105 markers
  across 42 files).
- Migrated color codes from `‾CNN` to `{cNN}/{/c}` (ASCII-safe brace form).
- Bumped FTH version requirement from 1.5.1 to 1.6.0 in release workflow.

### Added

- **fr/**: seeded French item names from Ezemania binary.
- **fr/**: imported Spartcon FR item descriptions.
- **fr/**: translated items/name rows 0-150 (consumables, ammo, tools).
- `docs/glossary.fr.md`: canonical French terminology reference.
- `docs/style.fr.md`: French style guide (tone, typography, control codes).
- `scripts/migrate_join_markers.py`: one-shot `<join>` to `{j}` migration.
- Per-language gzipped launcher payloads in release artifacts.

### Fixed

- Realigned 15 misplaced "Monster List book" entries in en/dat/items.
- Repaired 36 truncated `‾C0` terminal color markers.
- Excluded untranslatable rows (control-code-only, dummy, partial
  pass-throughs) from coverage statistics.
- Tagged releases now marked as "latest" on GitHub.

## [0.1.0] - 2026-04-06

First tagged release. Requires **FrontierTextHandler >= 1.5.0**.

### Added

- **en/**: bootstrapped English translations from patched binary.
- **fr/**: populated source strings for all 48 translatable sections.
- `scripts/validate.py`: CSV format validation.
- `scripts/stats.py`: coverage statistics generator.
- `scripts/export_json.py`: JSON export for downstream consumers.
- `scripts/build_bins.py`: build game-ready binaries from CSVs.
- `scripts/migrate_to_index.py`: one-shot legacy location-to-index migration.
- GitHub Pages dashboard with per-section progress bars.
- CI: validation on PRs, immutable tagged releases.

### Changed

- Migrated CSV key format from `location` (byte offsets) to `index`
  (stable pointer-table slots).

### Fixed

- Recovered 130 JP source rows polluted by old English fan-translation
  (matched against v2064 Wii U dump).
