# CLAUDE.md

Project-specific guidance for the MHFrontier-Translation repository.

## Project role

Per-section CSV translations of Monster Hunter Frontier text, organized as
`translations/<lang>/<xpath>.csv`. Source data is extracted via
[FrontierTextHandler](../../tools/FrontierTextHandler) (see sibling
`mhfrontier/tools/FrontierTextHandler/CLAUDE.md`).

## CSV format

`index,source,target` where `index` is the slot number in the section's
pointer table (FTH `--with-index` output). Indexes are stable across
upstream string-length changes that used to shift raw byte offsets.

**Required FTH version: ≥ 1.6.0** (index-keyed format is now the default;
join markers use `{j}` instead of `<join at="NNN">`; color codes use
`{cNN}/{/c}` instead of `‾CNN`; untranslated rows have empty `target`
instead of copying `source`). Earlier releases will not understand the
`{j}` and `{cNN}` placeholders.

The legacy `location,source,target` format (with `0xHEX@file.bin` keys) was
retired in April 2026. Importing an index-keyed CSV with FTH **requires
`--xpath`** so the importer can resolve indexes against the live pointer
table; in this repo the xpath is implicit from the file path
(`translations/fr/dat/armors/head.csv` → `dat/armors/head`). `build_bins.py`
derives it automatically.

## Copyright posture on Japanese source text

The original Japanese strings in the `source` column belong to Capcom, but
hosting them here is consistent with established community practice and the
practical risk is very low:

- Other Monster Hunter fan-translation repos host JP source publicly:
  [NSACloud/MHR-EFX-Translator](https://github.com/NSACloud/MHR-EFX-Translator)
  (TSV of Rise EFX JP→EN strings) and
  [xl3lackout/MHFZ-Ferias-English-Project](https://github.com/xl3lackout/MHFZ-Ferias-English-Project)
  (HTML pages translating the JP Ferias MHF-Z info site, original JP text
  preserved alongside the English).
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
  fr/                 ← French (primary; currently empty post-migration)
  en/                 ← English (~74% coverage, carried from legacy bootstrap)
scripts/
  validate.py         ← CSV format check (header + index + uniqueness)
  stats.py            ← coverage report → stats.json
  export_json.py      ← bundle as translations.json
  migrate_to_index.py      ← one-shot: rewrite legacy location-keyed CSVs as index-keyed
  migrate_join_markers.py  ← one-shot: rewrite <join at="…"> → {j} for FTH 1.6.0
  build_bins.py            ← apply translations and produce game-ready binaries
  armor_names.py           ← deterministic FR armour-name generator
  resolve_series.py        ← fill the armour series-stem table
  kana.py                  ← katakana → Latin transliteration (etymology restoration)
  fix_accents.py           ← restore French accents / œ ligature in targets
  item_descriptions.py     ← fill repeated item descriptions from a phrase table
docs/
  item_descriptions.fr.csv ← distinct item-description strings → FR
  armor_vocab.fr.json      ← closed vocabularies: slots (+gender), colours, tiers
  armor_series.fr.csv      ← series stem → FR, with `origin` trust level
  capcom_items.fr.csv      ← 1472 official Capcom JP→FR item names
  capcom_conflicts.fr.csv  ← where this repo disagrees with Capcom (unresolved)
```

## Capcom's official French as a reference

`docs/capcom_items.fr.csv` pairs Japanese item names with Capcom's own
French localisation, taken from the shipped Rise/Sunbreak string tables.
This is the authority `glossary.fr.md` rule #1 already points at
("si Capcom a traduit le terme en FR dans un jeu officiel récent, utiliser
ce terme tel quel"), in a form that can actually be checked against.

It fills almost none of the backlog — MHF's untranslated items are the
MHF-exclusive long tail. Its use is **auditing what is already translated**.
`docs/capcom_conflicts.fr.csv` records 202 rows where this repo differs:

- **158 `terminology`** — genuine disagreements (強走薬 is *Boisson tonique*
  here, *Potion vitalité* for Capcom). Note `glossary.fr.md` §5 currently
  enshrines several of these against its own rule #1. Left unresolved on
  purpose: MHF predates Rise and some choices may be deliberate.
- **44 `abbreviation`** — Capcom's UI truncations (*Potion ancest.*); the
  fuller repo form is usually preferable.

## Repeated item descriptions

`dat/items/description` is written from a small stock of boilerplate: its
16696 untranslated rows collapse to 7443 distinct strings, and one string
("Ｇ級防具を精錬することで作られた装飾品。") accounts for 1952 of them.
`docs/item_descriptions.fr.csv` holds one row per distinct string; fill `fr`
and `--apply` writes it everywhere that string occurs.

5838 rows are constant strings and can be translated directly. The other
10858 contain a katakana run — usually an item or series name that has to be
resolved before the sentence can be written — and are marked `has_var` and
left for later.

**Control codes are verified, not trusted.** An entry whose `{j}`, `{cNN}`
and `{/c}` markers do not match the source exactly is refused and `--apply`
aborts. A dropped colour span corrupts the rendered text with no
compile-time warning, so this is the one rule that cannot be left to care.

```bash
python scripts/item_descriptions.py --emit
python scripts/item_descriptions.py --report
python scripts/item_descriptions.py --apply
```

## French accents

Part of the corpus was seeded from an ASCII-folded binary, so it carried
`Ecaille`, `Oeuf`, `tenacite`. `scripts/fix_accents.py` restores them, but
only where the fix is unambiguous: the bare form must not itself be a French
word, exactly one accented word may fold to it, and proper nouns (armour
stems, monster names) are excluded. Words with more than one candidate —
`medaille` (médaille/médaillé), `peche` (pêche/péché) — are reported, never
guessed.

```bash
python scripts/fix_accents.py --report
python scripts/fix_accents.py --apply
```

## Armour names are generated, not translated

Armour names are compositional:

```
SERIES [TIER] SLOT [・COLOUR]              シャランＦヘッド・青
SERIES・SLOT_KANJI：CLASS [TIER] COLOUR     赤原礼装・頭：剣HS赤
```

77% of the 67,724 armour name rows parse against that grammar. Everything
except the series stem is a **closed vocabulary** — 24 slot nouns, 16
colours, 29 tier markers — so those rows need no translation and no review
queue: `scripts/armor_names.py` renders them, applying French adjective
agreement from the gender/number recorded per slot in
`docs/armor_vocab.fr.json` (`Heaume … cramoisi` vs `Casquette … cramoisie`).

Series stems are proper nouns and are **restored, not translated**.
`resolve_series.py` fills them from four sources and records which one won
in the `origin` column:

| origin | trust | meaning |
|---|---|---|
| `hand` | shipped | a human wrote it |
| `monster` | shipped | matched `docs/monster_names.fr.csv` |
| `francised` | shipped | an English loanword rendered in French (フレイム → Flamme) |
| `etymology` | shipped | hand-confirmed original spelling (ステノ → Stheno) |
| `en-patch` | shipped | reused the English patch's romanisation |
| `romaji` | **not shipped** | `kana.py` proposal; kana loses vowel quality (スリート is *Sleet*, not *Slit*) |
| `unresolved` | **not shipped** | needs a human |

`--apply` only writes stems in the shipped set; pass `--include-romaji` to
override. Hand edits to `fr` are never overwritten, and `--apply` never
touches a row that already has a target.

`francised` is checked **before** `etymology`, so that whether a stem comes
out French does not depend on which table happened to contain it. Etymology
restoration tells us what a stem *is* (スリート is *sleet*); francisation
decides what the French build *shows* (Grésil). Stems whose English is a
name rather than a common noun — Noel, Fine, Bonito — are deliberately left
alone.

A CJK stem whose en-patch value is an ordinary English dictionary word is a
partial romanisation, not a name (蒼ノ剣雄 → "Sword"), so it is forced to
`unresolved` rather than shipped.

```bash
python scripts/armor_names.py --report        # coverage + width check
python scripts/armor_names.py --emit-series   # refresh the stem table
python scripts/resolve_series.py              # fill stems, print trust breakdown
python scripts/armor_names.py --apply         # write targets
```

**Remaining English**: seven name-like stems still render in English —
Real, Gold, Barney, Pyx, Wither, Truss, Core. They are left as names rather
than guessed at; add them to `FRANCISATION` in `resolve_series.py` if they
turn out to be common nouns.

## Known data quality issues

1. **English-as-source pollution**: the PC `mhfdat-jp.bin` shipped with FTH
   was partially patched by an older English fan-translation, so some
   `pac/text_*`, `jmp/menu/*`, and `dat/items/*` rows still have English
   text in `source` instead of Japanese. The legacy fix used row-index
   matching against the v2064 Wii U dump (cracked with `cdecrypt`) and
   recovered ~130 rows. The remaining ~669 rows in 8 sections with
   mismatched row counts would need sequence alignment or a fresh
   unpatched PC JP dump. After the index-format migration, any future fix
   should re-extract with `--with-index` and run `migrate_to_index.py`.
2. **Dummy rows** (1,211 in `dat/items/source`): literal `dummy` strings in
   the binary. Confirmed as real unimplemented item-source slots — fixed-
   size pointer table padded with `dummy` for unused entries. Safe to leave
   with empty target; they don't render in-game.
3. **Control-code rows** (~6,643): `{j}` join glue and `{cNN}/{/c}`
   color codes — not translatable on their own.

## Translation guidelines

Before translating any French CSV, read:

- [`docs/glossary.fr.md`](docs/glossary.fr.md) — canonical FR terms
  (weapon classes, statuses, UI verbs, MHF-specific vocabulary).
  Extend it whenever a recurring term is missing.
- [`docs/style.fr.md`](docs/style.fr.md) — tone (tutoiement),
  typography (« » œ), length constraints, and the **critical rule**
  on preserving `{j}`, `{cNN}/{/c}`, and other control codes verbatim.

Recommended flow: pick **one** CSV section, pre-fill exact-match
`target` values from sibling CSVs (translation memory), translate
the rest with the glossary loaded, then run `scripts/validate.py`.
Translation itself stays in interactive agent sessions — scripts
only handle deterministic steps (validation, TM lookup, build).

## Workflows

```bash
python scripts/validate.py                       # validate all CSVs
python scripts/stats.py                          # regenerate stats.json
python scripts/export_json.py                    # bundle → translations.json

# One-shot legacy migration (from a fork keyed by location)
python scripts/migrate_to_index.py \
    --fth-output ../../tools/FrontierTextHandler/output
```
