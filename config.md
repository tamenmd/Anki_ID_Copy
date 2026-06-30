# Anki ID Copy — Einstellungen / Settings

**`copy_shortcut`** — Tastenkürzel im Browser für „Notiz-IDs als Suchstring kopieren".
Keyboard shortcut in the browser for "Copy Note IDs as Search String".
- Beispiele / examples: `Ctrl+Alt+C`, `Ctrl+Shift+Y`, `Ctrl+Shift+I`
- Leerer Wert (`""`) deaktiviert das Kürzel / an empty value disables the shortcut.
- Hinweis: `Ctrl+Shift+C` ist von Anki für „Lückentext einfügen" (Cloze) belegt — nicht verwenden.
  Note: `Ctrl+Shift+C` is Anki's built-in "Insert Cloze" shortcut — avoid it.
- Eine Änderung wirkt, sobald ein Browser-Fenster neu geöffnet wird /
  a change takes effect the next time a browser window is opened.

**`search_format`** — Format des kopierten Suchstrings / format of the copied search string.
- `"compact"` → `nid:1,2,3` (kürzer / shorter, empfohlen / recommended)
- `"or"` → `nid:1 OR nid:2`

**`due_siblings`** — Einstellungen für „Fällige Geschwister finden" /
settings for "Find due siblings". Die zuletzt im Dialog genutzten Werte werden
hier gespeichert / the values last used in the dialog are stored here.
- `deck` — zuletzt gewähltes Deck (leer = beim Öffnen nichts vorausgewählt) /
  last selected deck (empty = nothing preselected on open).
- `min_ivl` — Intervall (Tage), ab dem eine Geschwisterkarte als „sicher gelernt"
  gilt / interval (days) from which a sibling counts as "learned". Default `21`.
- `max_lapses` — höchstzulässige Patzer (Lapses) der Geschwisterkarte /
  max. allowed lapses of the sibling. Default `1`.
- `exclude_struggling` — `true` blendet Notizen aus, deren Geschwister gerade
  lernend/Leech/häufig-lapsend sind / hides notes whose siblings are currently
  learning/leech/lapsing. Default `true`.

**`copy_unsuspended_shortcut`** — optionales Tastenkürzel für „Notiz-IDs kopieren
(ohne suspendierte)" / optional keyboard shortcut for "Copy Note IDs (excluding
suspended)".
- Leerer Wert (`""`, Standard) = kein Kürzel / empty value (default) = no shortcut.
- Beispiel / example: `Ctrl+Alt+Shift+C`. Nicht denselben Wert wie
  `copy_shortcut` verwenden / do not use the same value as `copy_shortcut`.
- Wirkt beim nächsten Öffnen eines Browser-Fensters / takes effect the next time
  a browser window is opened.
