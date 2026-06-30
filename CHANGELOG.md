# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-30

First tagged release. Bundles the full feature set published on AnkiWeb.

### Added
- **Copy Note IDs as a search string** — right-click selected notes in the
  Browser to copy a compact `nid:1,2,3` query to the clipboard. Configurable
  keyboard shortcut (default `Ctrl+Alt+C`) and output format.
- **Copy Note IDs (excluding suspended)** — a second context-menu entry that
  omits fully-suspended notes (a note is kept as long as it still has at least
  one active card). Optional separate shortcut.
- **Compare with a friend** — a colour-coded scorecard of Missing / Extra /
  Shared note IDs. Suspension-aware, with per-deck and per-tag coverage
  breakdown, each region openable in the Browser.
- **Find due siblings** — a Tools-menu dialog that surfaces new (blue) cards
  whose sibling cards are already stably learned, with a live match count, a
  Browser view, and a one-click rescheduling filtered study deck.
- German and English localization (follows Anki's language); theme-aware UI for
  both light and dark mode.

[1.0.0]: https://github.com/tamenmd/Anki_ID_Copy/releases/tag/v1.0.0
