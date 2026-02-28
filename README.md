# Monster Hunter Frontier Translation

A curated guide to translating Monster Hunter Frontier, a Japanese MMORPG shut down by Capcom in 2019.
This project documents the tools, translatable content, and community efforts around MHF localization.

## Tools

### Text Extraction & Reimport

| Tool | Language | Description |
|------|----------|-------------|
| [FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler) | Python | Full pipeline: decrypt, decompress, extract, edit, reimport, compress, encrypt. Handles all main game text files. |
| [ReFrontier](https://github.com/Houmgaor/ReFrontier) | C# | Archive unpacking, batch decryption/decompression. Useful for non-text data and bulk processing. |
| [MHFTextEditor](https://github.com/matthe815s-projects/MHFTextEditor) | C# | UI-based text editor for MHF game files. |

### Dialogue & Quests

| Tool | Language | Description |
|------|----------|-------------|
| [readDialogue.py](https://gist.github.com/stratic-dev/162f4e5ad1766aeb59eb5edf1c1fb288) | Python | Extract NPC dialogue from stage files. |
| [writeDialogue.py](https://gist.github.com/stratic-dev/51e7927afc67612782e54ae87b4612b2) | Python | Reimport NPC dialogue into stage files. |
| [MHFZ Quest Editor](https://github.com/Paxlord/PaxMHFZQuestEditor) | — | Server-side quest data editor. Designed for closed-loop use. |

### Chat & Real-Time Translation

| Tool | Language | Description |
|------|----------|-------------|
| [MHFTranslate](https://github.com/wroleader/MHFTranslate) | C# | Parses in-game chat logs and translates via Google Cloud Translation API. Abandoned, no API key provided. |

### Launchers with Localization Support

| Tool | Language | Description |
|------|----------|-------------|
| [mhf-launcher](https://github.com/rockisch/mhf-launcher) | Rust | Custom launcher with built-in locale system (Fluent `.ftl` files). Supports adding new languages. |
| [mhf-patch-server](https://github.com/rockisch/mhf-patch-server) | Rust | Patch distribution server for mhf-launcher. Can deliver translation file updates to players. |

### Translation Platforms

| Tool | Description |
|------|-------------|
| [Weblate](https://weblate.org/) | Open-source web translation platform. Can be self-hosted to manage translations collaboratively. |

## Translatable Content

All game text uses Shift-JIS encoding. FrontierTextHandler extracts it to CSV (UTF-8) with columns: `location`, `source`, `target`.

### mhfdat.bin — Main Game Data

| Category | XPath | Content |
|----------|-------|---------|
| Weapon names (melee) | `dat/weapons/melee/name` | Great Sword, Hammer, Long Sword, etc. |
| Weapon descriptions (melee) | `dat/weapons/melee/description` | Melee weapon flavor text |
| Weapon names (ranged) | `dat/weapons/ranged/name` | Bow, Bowgun, etc. |
| Weapon descriptions (ranged) | `dat/weapons/ranged/description` | Ranged weapon flavor text |
| Head armor | `dat/armors/head` | Helmet names |
| Body armor | `dat/armors/body` | Chest armor names |
| Arm armor | `dat/armors/arms` | Gauntlet names |
| Waist armor | `dat/armors/waist` | Belt/fauld names |
| Leg armor | `dat/armors/legs` | Greave names |
| Item names | `dat/items/name` | Consumables, materials, key items |
| Item descriptions | `dat/items/description` | Item effect and lore text |
| Item sources | `dat/items/source` | Acquisition info |
| Monster descriptions | `dat/monsters/description` | Monster lore |
| Equipment descriptions | `dat/equipment/description` | General equipment flavor text |
| Rank labels | `dat/ranks/label` | HR requirement labels |
| Rank requirements | `dat/ranks/requirement` | Rank requirement descriptions |
| Hunting Horn guide | `dat/hunting_horn/guide` | Song effect guide |
| Hunting Horn tutorial | `dat/hunting_horn/tutorial` | Tutorial text |

### mhfpac.bin — Skills

| Category | XPath | Content |
|----------|-------|---------|
| Skill names | `pac/skills/name` | Skill activation names |
| Skill effects | `pac/skills/effect` | Skill effect descriptions |
| Zenith skill effects | `pac/skills/effect_z` | Zenith-era skill descriptions |
| Skill descriptions | `pac/skills/description` | Skill point descriptions |
| UI text tables | `pac/text_14` to `pac/text_d0` | Menu labels, interface strings (20+ tables) |

### mhfinf.bin — Quests

| Category | XPath | Content |
|----------|-------|---------|
| Quest info | `inf/quests` | Quest names, descriptions, objectives (8 fields per quest) |

### mhfjmp.bin — Fast Travel

| Category | XPath | Content |
|----------|-------|---------|
| Location titles | `jmp/menu/title` | Teleport point names |
| Location descriptions | `jmp/menu/description` | Area descriptions |
| Menu strings | `jmp/strings` | Navigation UI text |

### Other Formats

| Format | Flag | Content |
|--------|------|---------|
| FTXT files | `--ftxt` | Standalone text containers (magic `0x000B0000`) |
| Quest binaries | `--quest` / `--quest-dir` | Individual quest `.bin` files |
| NPC dialogue | `--npc` / `--npc-dir` | Stage dialogue files |

## Quick Start

### Extract text

```bash
# Extract everything at once (auto-decrypts)
cd FrontierTextHandler
python main.py --extract-all

# Or extract a specific category
python main.py --xpath=dat/items/name
```

### Edit translations

Edit the generated CSV in `output/`. Fill in the `target` column with your translation.

### Reimport into game files

```bash
# Produce a game-ready file
python main.py --csv-to-bin output/dat-items-name.csv data/mhfdat.bin --compress --encrypt
```

Replace the original `mhfdat.bin` with the output.

## Community Efforts

*Know of a translation project? Open an issue or PR to add it here.*

### Game Text Translation

| Language | Project | Coverage | Notes |
|----------|---------|----------|-------|
| English | MHF English Patch | Menus, equipment names, item names | Distributed via [Rain server](https://discord.com/invite/rainserver) (~70K members). Does not cover NPC dialogue or tutorial. |
| English | [MezeLounge](https://mholdschool.com/viewtopic.php?t=71) | Menus, equipment, quests | Private server with near-complete English translation. Also runs a Classic server (S1–Forward 5). |
| English | [Leaps' MHFZ Guide](https://leaps29.github.io/MHFZ-Guide/) | Guides | Comprehensive gameplay guide for Rain server players. |
| English | [MHFZ Ferias English](https://github.com/xl3lackout/MHFZ-Ferias-English-Project) | Game database/wiki | English translation of the [Ferias](http://ferias.life.coocan.jp/) Japanese info site. |
| English | [MHFZ Info](https://github.com/stratic-dev/MHFZ-Info) | Game database/wiki | Fork of the Ferias English project. |
| English | [Fist's English Guide](https://fist-mirror.github.io/guide/) | Guides | English info site and gameplay guides. |
| English | [MHF Frontier Wiki](https://mhfo.fandom.com/) | Wiki | English Fandom wiki with translation notes. |
| French | [Mogapédia](https://mogapedia.fandom.com/fr/) + [MezeLounge](https://mholdschool.com/viewtopic.php?t=71) | Game text | French translation effort in partnership between Mogapédia and MezeLounge. |
| Korean | [MHF Korean Wiki](https://mhfkr.fandom.com/) | Wiki | Korean Fandom wiki with menu translations and guides. |

### Official Localizations (Discontinued)

| Language | Region | Notes |
|----------|--------|-------|
| Japanese | Japan (PC, PS3, PS Vita, Wii U, Xbox 360) | Original language. Service ended December 2019. |
| Korean | South Korea | Service ended August 2011 (Season 7.0). |
| Traditional Chinese | Taiwan, Macau | Service ended alongside JP servers. |

## How to Contribute

1. **Translate text**: Extract a category with FrontierTextHandler, translate the CSV, and submit a PR.
2. **Document a project**: If you know of an active translation effort, open an issue to get it listed.
3. **Improve tooling**: Contributions to FrontierTextHandler and ReFrontier are welcome.

## Disclaimer

Monster Hunter Frontier and all associated game text are the property of Capcom Co., Ltd. This project is a non-commercial fan translation effort for game preservation purposes. No original game code is included. If Capcom requests removal, we will comply immediately.
