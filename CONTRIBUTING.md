# Contributing

Thanks for your interest in improving **Anki ID Copy**! Bug reports, feature
ideas, and pull requests are all welcome.

## Project layout

- `nid_tools.py`, `due_siblings_logic.py` — **pure, Anki-independent logic**
  (ID parsing, search-string building, set diff). No `aqt`/`anki` imports, so it
  can be unit-tested without a running Anki.
- `__init__.py`, `due_siblings.py` — the **Anki/Qt glue** (Browser menus,
  dialogs, clipboard, filtered decks). Qt symbols are imported via `aqt.qt` so
  the add-on works on both Qt5 and Qt6 builds.
- `tests/` — `unittest` tests for the pure logic.

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile __init__.py nid_tools.py due_siblings_logic.py due_siblings.py
```

To try it inside Anki, symlink or copy this folder into your Anki add-ons
directory and restart Anki.

## Building the .ankiaddon

```bash
zip Anki_ID_Copy.ankiaddon __init__.py nid_tools.py due_siblings_logic.py \
    due_siblings.py manifest.json config.json config.md
```

Exactly these seven files, at the archive root, with **no** `meta.json` (Anki
manages that per-install). Pushing to `main` runs the same build in CI, and
tagged releases attach the artifact automatically.

## Guidelines

- Keep new pure logic in `nid_tools.py` / `due_siblings_logic.py` and cover it
  with tests; keep Anki/Qt glue in `__init__.py` / `due_siblings.py`.
- Import Qt only through `aqt.qt` (never `PyQt5`/`PyQt6` directly).
- Add user-facing strings to the `LANGUAGES` dict in **both** German and English.
- Run the tests before opening a pull request, and keep changes additive so
  existing behavior is preserved.
