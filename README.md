# Anki ID Copy

[![Build](https://github.com/tamenmd/Anki_ID_Copy/actions/workflows/build.yml/badge.svg)](https://github.com/tamenmd/Anki_ID_Copy/actions/workflows/build.yml)
[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-download-2496ED)](https://ankiweb.net/shared/info/2110918647)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Copy selected note IDs as a search string, and compare your notes with a
friend's to instantly see what you're missing — built for medical students who
share large decks (AnKing / Zanki / AMBOSS / Ankizin / Ankiphil style).

> **Für deutsche Med-Studenten:** Schickt euch gegenseitig Karten-Auswahlen als
> `nid:`-Suchstring und vergleicht per Klick, welche Notizen euch fehlen, welche
> ihr zusätzlich habt und welche gemeinsam sind — inkl. Suspension-Status und
> Aufschlüsselung nach Fach. Funktioniert, wenn ihr dasselbe geteilte Deck
> (z. B. Ankizin über AnkiCollab) nutzt.

## Features

- **Copy Note IDs** — right-click selected notes in the Browser → copy them as a
  search string (`nid:1,2,3`) to the clipboard. Configurable keyboard shortcut
  (default `Ctrl+Alt+C`).
- **Copy Note IDs (excluding suspended)** — a second context-menu entry that
  leaves out fully-suspended notes (a note is kept while it still has at least
  one active card), so you share only what you're actively studying. Optional
  separate shortcut.
- **Compare with a friend** — paste your IDs and your friend's IDs; get a
  scorecard with all set regions:
  - **Missing** (friend has, you don't), split into *present in your collection
    (e.g. suspended)* vs *not in your collection at all*
  - **Extra** (you have, friend doesn't)
  - **Shared** (both have)
- **Suspension-aware** — for each locally-owned region, see how many notes you
  have suspended and jump straight to them (`is:suspended …`).
- **Coverage breakdown** — break any region down by **deck** or **tag**, sorted
  by count, with one click to show each group in the Browser.
- **Polished UI** — modern, theme-safe cards and badges that adapt to Anki's
  light and dark modes. German and English interface (follows Anki's language).

## Fällige Geschwister · Due Siblings

**DE:** Über **Werkzeuge → Fällige Geschwister finden …** öffnest du einen Dialog,
der neue (blaue) Karten findet, deren Geschwisterkarten (andere Karten derselben
Notiz, z. B. andere Clozes) du schon stabil gelernt hast — so gehen sie nicht im
Berg neuer Karten unter.

**EN:** Via **Tools → Find due siblings …** you open a dialog that finds new (blue)
cards whose sibling cards (other cards of the same note, e.g. other clozes) you
have already learned to a stable state — so they don't drown in your pile of new
cards.

**Actions:** *Show in browser* opens the matching cards straight in the Browser.
*Start as study deck* builds a rescheduling filtered deck so you can start
reviewing immediately.

**Settings (remembered between sessions):**
- **Deck** — restrict the search to a specific deck (or leave empty for all decks).
- **Hide cards whose siblings are struggling** — exclude notes whose siblings are
  still in the learning phase, are leeches, or have too many lapses (default: on).
- **Advanced → Interval threshold** — minimum interval (days) for a sibling to
  count as "learned" (default: 21 days).
- **Advanced → Max. lapses** — maximum allowed lapses for the sibling (default: 1).

## Installation

- **Manual (.ankiaddon):** download `Anki_ID_Copy.ankiaddon` from the
  [Releases](../../releases) page and double-click it (or drag it onto Anki).
- **From source:** the add-on *is* this repository folder. Pushing to `main`
  triggers a GitHub Actions build that produces `Anki_ID_Copy.ankiaddon` as an
  artifact; tagged releases attach it automatically.

## Usage

1. Open the **Browser** (`b`).
2. **Copy:** select notes → right-click → *Anki ID Copy → Copy Note IDs as
   Search String* (or press the shortcut). Send the copied text to your friend.
3. **Compare:** right-click → *Compare Note IDs with Friend* (or
   **Tools → Anki ID Copy: Compare Note IDs**). Your selection is pre-filled on
   the left; paste your friend's IDs on the right → **Compare**.
4. In the result scorecard, use **Show in browser**, **Copy**, **Show
   suspended**, or **Break down** on any region.

## Configuration

Open **Tools → Add-ons → Anki ID Copy → Config**. See
[config.md](config.md) for details.

| Key | Default | Meaning |
|-----|---------|---------|
| `copy_shortcut` | `Ctrl+Alt+C` | Browser shortcut for the copy action (empty disables it). `Ctrl+Shift+C` is reserved by Anki for Insert Cloze. |
| `copy_unsuspended_shortcut` | `""` | Optional shortcut for *Copy Note IDs (excluding suspended)* (empty = none). Don't reuse `copy_shortcut`'s value. |
| `search_format` | `compact` | `compact` → `nid:1,2,3`, `or` → `nid:1 OR nid:2`. |
| `due_siblings` | *(object)* | Last-used settings for the Due Siblings dialog (`deck`, `min_ivl`, `max_lapses`, `exclude_struggling`). See [config.md](config.md). |

## Compatibility

Anki **2.1.50+**, both Qt5 and Qt6 builds (Qt symbols are imported via `aqt.qt`).

## Development

```bash
python -m unittest discover -s tests   # run the unit tests for the pure logic
python -m py_compile __init__.py nid_tools.py due_siblings_logic.py due_siblings.py
```

The pure, Anki-independent logic (ID parsing, search-string building, set diff,
grouping, due-sibling queries) lives in [`nid_tools.py`](nid_tools.py) and
[`due_siblings_logic.py`](due_siblings_logic.py) and is unit-tested in
[`tests/`](tests). The Anki/Qt glue lives in [`__init__.py`](__init__.py) and
[`due_siblings.py`](due_siblings.py). See [CONTRIBUTING.md](CONTRIBUTING.md) for
the full layout and how to build the `.ankiaddon`.

## A note on note IDs

Comparison matches on Anki **note IDs (`nid`)**. These are preserved from the
source when a deck is distributed as one artifact (a shared AnkiCollab
subscription, an AnkiHub deck, or the same downloaded `.apkg`), so everyone who
got the deck the same way shares identical IDs and the comparison is exact. If
two people obtained "the same" deck through *different* channels, their IDs may
not line up.

## License

[MIT](LICENSE) © 2026 tamenmd
