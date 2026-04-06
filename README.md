# Monster Hunter Frontier Translation

A community-maintained translation of Monster Hunter Frontier — a Japanese MMORPG shut down by Capcom in 2019.

Translation data lives directly in this repository as CSV files, one per game section. No server required.

**[View translation progress →](https://mogapedia.github.io/MHFrontier-Translation/)**

## Repository layout

```
translations/
  fr/                        ← French translations
    dat/armors/head.csv
    dat/items/name.csv
    pac/skills/name.csv
    ...                      (48 sections total, mirroring FrontierTextHandler xpaths)
  en/                        ← English translations (contribute via PR)
    ...
scripts/
  migrate.py                 ← split a monolithic Weblate CSV into per-section files
  validate.py                ← check CSV format (run locally or in CI)
  export_json.py             ← generate translations.json for downstream tools
  stats.py                   ← generate stats.json (coverage per file/language)
docs/
  index.html                 ← GitHub Pages translation dashboard (fetches stats.json)
```

Each CSV has three columns:

```
location,source,target
3328544,革兜,Casque en cuir
3328560,軽い素材で作られた頭用装備。,Équipement de tête en matériaux légers.
```

- **location** — integer byte offset in the game binary (from FrontierTextHandler)
- **source** — original Japanese text (do not edit)
- **target** — your translation (fill this in)

## Contributing

### I want to translate strings

1. Fork this repository
2. Open the CSV for the section you want to translate (e.g. `translations/fr/dat/items/name.csv`)
3. Fill in the `target` column — leave it empty for strings you haven't translated yet
4. Submit a pull request

GitHub renders CSVs as a table, so reviewers can read your changes without any tooling.

If your language directory doesn't exist yet, copy `translations/fr/` and rename it.

#### A note on the Japanese source column

The `source` column contains the original Japanese strings extracted from the
game binary. **Do not edit it** — translators rely on it as the canonical
reference, and the import tooling matches rows by `location`, not by source.

These strings are Capcom's, but hosting them here is consistent with
established community practice for Monster Hunter fan translations on GitHub:

- [NSACloud/MHR-EFX-Translator](https://github.com/NSACloud/MHR-EFX-Translator)
  ships a JP→EN TSV (`translationCache.tsv`) with thousands of Monster Hunter
  Rise EFX source strings.
- [xl3lackout/MHFZ-Ferias-English-Project](https://github.com/xl3lackout/MHFZ-Ferias-English-Project)
  translates the Japanese Ferias MHF-Z info site; the per-page HTML files
  contain the original Japanese descriptions alongside the English.

Capcom's MH-related enforcement has historically targeted ROMs, asset rips,
and server emulators — never translation source strings — and MHF was
officially shut down in 2019, so the preservation use case is well-grounded.
Item names, skill names, and UI labels are essentially zero risk.

The only category where some discretion is warranted is **bulk scenario
scripts, NPC monologues, and quest dialogue**, where the creative-content
argument has more weight. Even there it is fine to commit translations; just
avoid pasting huge raw blocks into public issues or PR descriptions where
they would be indexed without context.

### I want to apply translations to my game files

You need [FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler) and your own copy of the game files.

```bash
# 1. Clone this repo
git clone https://github.com/Houmgaor/MHFrontier-Translation
cd MHFrontier-Translation

# 2. Apply one section
python path/to/FrontierTextHandler/main.py \
    --csv-to-bin translations/fr/dat/items/name.csv \
    path/to/mhfdat.bin \
    --compress --encrypt

# Or apply all sections using the pre-built release JSON
#   → download translations-translated.json from Releases
#   → FrontierTextHandler --merge-json translations-translated.json data/mhfdat.bin
```

### I want to migrate existing Weblate translations

If you have a monolithic CSV from a previous Weblate export, run:

```bash
# 1. Extract all sections from your game files
cd path/to/FrontierTextHandler
python main.py --extract-all          # writes to output/

# 2. Run the migration script
cd path/to/MHFrontier-Translation
python scripts/migrate.py \
    --extracted-dir path/to/FrontierTextHandler/output \
    --translated    path/to/mhfdat-all-fr.csv \
    --lang fr
```

### Validate locally

```bash
python scripts/validate.py                     # validate all CSVs
python scripts/validate.py translations/fr/    # one language
python scripts/validate.py --changed-only      # only git-changed files (fast, good pre-commit)
```

### Export JSON for downstream tools

```bash
python scripts/export_json.py                  # → translations.json (all strings)
python scripts/export_json.py --only-translated  # → translations.json (non-empty targets only)
```

### Check coverage locally

```bash
python scripts/stats.py                        # → stats.json (all languages)
python scripts/stats.py translations/fr/       # → stats.json (one language)
```

Open `docs/index.html` in a browser after placing `stats.json` next to it to preview the dashboard.

The release workflow runs this automatically on every push to `main` and publishes the JSON to GitHub Releases.

## Translatable content

All game text uses Shift-JIS encoding internally. FrontierTextHandler handles encoding automatically.

### mhfdat.bin — Main game data

| Section | XPath | Content |
|---------|-------|---------|
| Head armor | `dat/armors/head` | Helmet names & descriptions |
| Body armor | `dat/armors/body` | Chest armor |
| Arm armor | `dat/armors/arms` | Gauntlets |
| Waist armor | `dat/armors/waist` | Belts |
| Leg armor | `dat/armors/legs` | Greaves |
| Equipment descriptions | `dat/equipment/description` | Flavor text |
| Item names | `dat/items/name` | Consumables, materials, key items |
| Item descriptions | `dat/items/description` | Effect and lore |
| Item sources | `dat/items/source` | Acquisition info |
| Monster descriptions | `dat/monsters/description` | Monster lore |
| Rank labels | `dat/ranks/label` | HR labels |
| Rank requirements | `dat/ranks/requirement` | Requirement text |
| Hunting Horn guide | `dat/hunting_horn/guide` | Song effect guide |
| Hunting Horn tutorial | `dat/hunting_horn/tutorial` | Tutorial text |
| Melee weapon names | `dat/weapons/melee/name` | GS, Hammer, LS, etc. |
| Melee weapon descriptions | `dat/weapons/melee/description` | Flavor text |
| Ranged weapon names | `dat/weapons/ranged/name` | Bow, Bowgun |
| Ranged weapon descriptions | `dat/weapons/ranged/description` | Flavor text |

### mhfpac.bin — Skills

| Section | XPath | Content |
|---------|-------|---------|
| Skill names | `pac/skills/name` | Skill activation names |
| Skill effects | `pac/skills/effect` | Effect descriptions |
| Zenith skill effects | `pac/skills/effect_z` | Zenith-era descriptions |
| Skill descriptions | `pac/skills/description` | Skill point text |
| UI text tables | `pac/text_14` … `pac/text_d4` | Menus, interface strings |

### mhfinf.bin — Quests

| Section | XPath | Content |
|---------|-------|---------|
| Quest data | `inf/quests` | Names, descriptions, objectives |

### mhfjmp.bin — Fast travel

| Section | XPath | Content |
|---------|-------|---------|
| Location titles | `jmp/menu/title` | Teleport point names |
| Location descriptions | `jmp/menu/description` | Area descriptions |
| Menu strings | `jmp/strings` | Navigation UI |

## CI

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| Validate | Every PR touching `translations/` | Checks CSV format and reports coverage |
| Release | Every push to `main` | Validates all CSVs, exports JSON, publishes to Releases |
| Pages | Every push to `main` | Generates `stats.json`, deploys dashboard to GitHub Pages |

## Community efforts

| Language | Project | Notes |
|----------|---------|-------|
| French | [Mogapédia](https://mogapedia.fandom.com/fr/) + [@ezemania2](https://github.com/ezemania2) | Primary contributors to this repo |
| English | MHF English Patch | Distributed via [Rain server](https://discord.com/invite/rainserver) |
| English | [@ezemania2](https://github.com/ezemania2) | Near-complete EN translation work |

*Know of another project? Open an issue.*

## Related tools

| Tool | Purpose |
|------|---------|
| [FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler) | Extract, edit, and reimport game text (Python) |
| [ReFrontier](https://github.com/Houmgaor/ReFrontier) | Archive unpacking and batch processing (C#) |
| [mhf-outpost](https://github.com/Mogapedia/mhf-outpost) | Download and apply translated game files (companion project) |

## Disclaimer

Monster Hunter Frontier and all associated game text are the property of Capcom Co., Ltd.
This is a non-commercial fan project for preservation purposes. No original game binaries are included.
