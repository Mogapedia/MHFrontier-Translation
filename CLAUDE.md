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
  clean_en_targets.py      ← blank en/ targets that don't translate their source
docs/
  en_orphan_fragments.csv  ← English fragments removed by clean_en_targets.py
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
MHF-exclusive long tail. Its use is **auditing what is already translated**,
and that audit has now been acted on.

### Which Capcom generation wins

Part of the repo's French came from the PSP games: « Pilule armure »,
« Drogue du démon », « Piège à choc » are genuine Capcom French, but from
the Freedom generation. MHF is contemporary with those games, which is an
argument for keeping them.

That is **not** the choice made here. Those localisations were done from
English under time pressure and are markedly weaker than the recent ones;
matching the era would freeze a worse translation in place. The current
vocabulary (Wilds, else Rise/Sunbreak) wins, even against an authentic
period term. An era-accurate set may return later as an optional
**nostalgia layer**, never as the reference.

157 item names were updated accordingly, and `glossary.fr.md` §5 was
corrected to match. Capcom's UI truncations were expanded where the
~24-character budget allows — MHF's limits are not Rise's — so the repo
carries « Sphère d'armure dense » where Capcom ships « Sph. arm. dense ».

`docs/capcom_conflicts.fr.csv` now holds 65 rows, none of them real
disagreements: 59 are Capcom truncations against the repo's fuller form,
and 6 are the same thing miscategorised by the comparison (an apostrophe
splits a word, so « Sphère d'armure dense » does not register as an
expansion of « Sph. arm. dense »).

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

   The mirror-image problem is much larger and lives in the **target**
   column. `translations/en/` was bootstrapped (7379bfb) from that same
   patched binary, which is not the build the `source` column came from, so
   a large part of `target` holds text belonging to other rows: Japanese
   from a different pointer table, and ~155 rows of Traditional Chinese from
   the Taiwanese release. `scripts/clean_en_targets.py --survey` measures it:

   | section | filled | not a translation |
   |---|---:|---:|
   | `dat/equipment/description` | 54165 | 47163 (87%) — **cleaned** |
   | `dat/armors/*` | ~67000 | ~10300 (16%) |
   | `dat/weapons/*/name` | 18985 | 2905 (15%) |
   | other sections | — | <1% |

   Only `dat/equipment/description` has been cleaned. The armour and weapon
   *name* sections are not prose and the heuristic was tuned on prose, so
   they need their own check before anything is blanked there.

   This never affected the coverage figures — `stats.py` already refuses to
   count a target containing CJK — but it corrupts translation-memory
   lookups, `export_json.py`, and any build reading `target` directly.
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
