# CLAUDE.md

Project-specific guidance for the MHFrontier-Translation repository.

## Project role

Per-section CSV translations of Monster Hunter Frontier text, organized as
`translations/<lang>/<xpath>.csv`. Source data is extracted via
[FrontierTextHandler](../../tools/FrontierTextHandler) (see sibling
`mhfrontier/tools/FrontierTextHandler/CLAUDE.md`). Current coverage lives in
`stats.json` (`python scripts/stats.py`), not in this file.

## CSV format

`index,source,target` where `index` is the slot number in the section's
pointer table (FTH `--with-index` output). Indexes are stable across upstream
string-length changes that used to shift raw byte offsets.

Rules when writing to these files:

- **Never edit the `source` column.** It is the Japanese original and the key
  everything else is checked against.
- **Preserve control codes verbatim**: `{j}` join markers, `{cNN}`/`{/c}`
  colour spans. Do *not* enforce marker-for-marker parity with the source —
  Japanese terminates colour spans implicitly, so French often needs an
  explicit `{/c}` the source does not have.
- **Line endings are LF everywhere**, enforced by `.gitattributes`. Python's
  `csv.writer` emits `\r\n` by default, which rewrites a whole file and buries
  the real change in a full-file diff, so always pass `lineterminator="\n"`.
- An empty `target` means untranslated. Never copy `source` into `target`.
- Run `python scripts/validate.py` before committing.

**Required FTH version: ≥ 1.6.0.** Earlier releases do not understand `{j}` or
`{cNN}`. Importing an index-keyed CSV requires `--xpath` so the importer can
resolve indexes against the live pointer table; here the xpath is implicit in
the file path (`translations/fr/dat/armors/head.csv` → `dat/armors/head`) and
`build_bins.py` derives it automatically.

## Japanese source text

Commit JP source freely for item names, skill names, armour/weapon names and
UI strings. Be more deliberate with **scenario scripts, NPC monologues and
quest dialogue** — that is the only category where the creative-content
argument has weight. Avoid pasting large blocks of it into public issue
trackers or commit messages.

## Layout

```
translations/
  fr/                 ← French (primary)
  en/                 ← English (legacy bootstrap; see "What not to trust")
scripts/
  validate.py         ← CSV format check (header + index + uniqueness)
  stats.py            ← coverage report → stats.json
  export_json.py      ← bundle as translations.json
  build_bins.py            ← apply translations and produce game-ready binaries
  armor_names.py           ← deterministic FR armour-name generator
  resolve_series.py        ← fill the armour series-stem table
  kana.py                  ← katakana → Latin transliteration
  fix_accents.py           ← restore French accents / œ ligature in targets
  item_descriptions.py     ← fill repeated item descriptions from a phrase table
  clean_en_targets.py      ← blank en/ targets that don't translate their source
  migrate_to_index.py      ← one-shot: legacy location-keyed → index-keyed
  migrate_join_markers.py  ← one-shot: <join at="…"> → {j}
docs/
  glossary.fr.md           ← canonical FR terms — read before translating
  style.fr.md              ← tone, typography, length, control-code rule
  armor_vocab.fr.json      ← closed vocabularies: slots (+gender), colours, tiers
  armor_series.fr.csv      ← series stem → FR, with `origin` trust level
  item_descriptions.fr.csv ← distinct item-description strings → FR
  capcom_items.fr.csv      ← official Capcom JP→FR item names
  capcom_conflicts.fr.csv  ← where this repo differs from Capcom
  glossary-todo.fr.csv     ← open terminology questions
  en_orphan_fragments.csv  ← English fragments removed by clean_en_targets.py
```

## Before translating

Read [`docs/glossary.fr.md`](docs/glossary.fr.md) and
[`docs/style.fr.md`](docs/style.fr.md). Extend the glossary whenever a
recurring term is missing, **before** filling the CSV.

Flow: pick **one** section, pre-fill exact matches from sibling CSVs
(translation memory), translate the rest with the glossary loaded, validate.
Translation itself stays in interactive sessions — scripts only do
deterministic steps.

## Terminology rules

1. If Capcom has translated a term into French in a recent official game, use
   that term. `docs/capcom_items.fr.csv` is that reference, in checkable form.
2. **Recent vocabulary beats period-accurate vocabulary.** Freedom-era French
   (« Drogue du démon », « Pilule armure ») is genuine Capcom and contemporary
   with MHF, but was translated from English under time pressure. Do not
   reintroduce it. An era-accurate set may return later as an optional
   nostalgia layer, never as the reference.
3. Capcom's UI truncations may be expanded — MHF's width budget is ~24
   half-width units, wider than Rise's. « Sphère d'armure dense », not
   « Sph. arm. dense ». JP glyphs count as 2 units
   (`unicodedata.east_asian_width` W/F).
4. Unresolved terms go in `docs/glossary-todo.fr.csv` rather than being
   guessed at inline.

## Generated content

Some sections are rendered, not translated. Do not queue these for human
translation.

### Armour names

Compositional, so everything but the series stem is a closed vocabulary
(slot nouns, colours, tier markers):

```
SERIES [TIER] SLOT [・COLOUR]              シャランＦヘッド・青
SERIES・SLOT_KANJI：CLASS [TIER] COLOUR     赤原礼装・頭：剣HS赤
```

`armor_names.py` renders them, applying adjective agreement from the
gender/number recorded per slot in `docs/armor_vocab.fr.json`
(`Heaume … cramoisi` vs `Casquette … cramoisie`).

Series stems are proper nouns: **restored, not translated**.
`resolve_series.py` records which source won in the `origin` column, and only
ships the trusted ones:

| origin | shipped | meaning |
|---|:---:|---|
| `hand` | yes | a human wrote it |
| `monster` | yes | matched `docs/monster_names.fr.csv` |
| `francised` | yes | English loanword rendered in French (フレイム → Flamme) |
| `etymology` | yes | hand-confirmed original spelling (ステノ → Stheno) |
| `en-patch` | yes | reused the English patch's romanisation |
| `romaji` | **no** | `kana.py` proposal; kana loses vowel quality (スリート is *Sleet*, not *Slit*) |
| `unresolved` | **no** | needs a human |

When extending: `francised` is checked **before** `etymology`, so a stem's
French form does not depend on which table happened to contain it. Etymology
says what a stem *is* (スリート = *sleet*); francisation decides what ships
(Grésil). Stems whose English is a name, not a common noun (Noel, Fine,
Bonito), are left alone. A CJK stem whose en-patch value is an ordinary
English word is a partial romanisation, not a name (蒼ノ剣雄 → "Sword"), so it
is forced to `unresolved`.

```bash
python scripts/armor_names.py --report        # coverage + width check
python scripts/armor_names.py --emit-series   # refresh the stem table
python scripts/resolve_series.py              # fill stems, print trust breakdown
python scripts/armor_names.py --apply         # write targets
```

Hand edits to `fr` are never overwritten and `--apply` never touches a row
that already has a target. Seven name-like stems still render in English
(Real, Gold, Barney, Pyx, Wither, Truss, Core) — add them to `FRANCISATION`
in `resolve_series.py` if they turn out to be common nouns.

### Item descriptions

`dat/items/description` is built from a small stock of boilerplate. Translate
each distinct string once in `docs/item_descriptions.fr.csv`, then apply:

```bash
python scripts/item_descriptions.py --report
python scripts/item_descriptions.py --apply
```

### French accents

Part of the corpus was seeded from an ASCII-folded binary (`Ecaille`, `Oeuf`,
`tenacite`). `fix_accents.py` repairs only unambiguous cases: the bare form
must not itself be a French word, exactly one accented word may fold to it,
and proper nouns are excluded. Ambiguous words (`medaille`, `peche`) are
reported, never guessed. Note hunspell stores base forms only, so inflected
accented spellings are not in its map and will not be caught.

```bash
python scripts/fix_accents.py --report
python scripts/fix_accents.py --apply
```

## What not to trust

1. **`translations/en/` targets are partly not translations.** The English
   corpus was bootstrapped from a binary patched by an older fan translation,
   built from a different pointer table, so many targets hold text belonging
   to other rows — including Traditional Chinese from the Taiwanese release.
   `dat/equipment/description` has been cleaned; `dat/armors/*` and
   `dat/weapons/*/name` are still ~15–19% polluted. **Check before using the
   English column as translation memory:**

   ```bash
   python scripts/clean_en_targets.py --survey
   python scripts/clean_en_targets.py --report <section>
   ```

   The heuristic was tuned on prose and is not validated for name sections.
2. **Some `source` rows hold English, not Japanese** (~669 rows across 8
   sections), from the same patched binary. Fixing needs sequence alignment or
   a fresh unpatched JP dump.
3. **Placeholder rows**: `0`, `ダミー`, `dummy` are unused pointer-table slots.
   Leave the target empty; they do not render in-game.
4. **Control-code-only rows** (`{j}`, `{cNN}`) are not translatable alone.

## Workflows

```bash
python scripts/validate.py     # validate all CSVs
python scripts/stats.py        # regenerate stats.json
python scripts/export_json.py  # bundle → translations.json
```
