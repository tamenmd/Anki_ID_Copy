## Summary

<!-- What does this change, and why? -->

## Checklist

- [ ] Tests pass: `python -m unittest discover -s tests -v`
- [ ] Clean compile: `python -m py_compile __init__.py nid_tools.py due_siblings_logic.py due_siblings.py`
- [ ] Pure logic stays in `nid_tools.py` / `due_siblings_logic.py` (with tests); Anki/Qt glue stays in `__init__.py` / `due_siblings.py`
- [ ] Qt imported only via `aqt.qt`
- [ ] New user-facing strings added in both German and English
- [ ] Change is additive — existing behavior is preserved
