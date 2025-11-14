 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/__init__.py b/__init__.py
index 01d4288d36ade6652cfaf261a28dab98210fd649..41543ab0407008710c2419cb1f4b3acbe0001bf9 100644
--- a/__init__.py
+++ b/__init__.py
@@ -1,74 +1,87 @@
 # -*- coding: utf-8 -*-
 # Anki Add-on: Notiz-IDs kopieren & Vergleichs-Dialog (mit vorausgefüllten eigenen IDs)
 
 from aqt import mw, QAction, gui_hooks
 from aqt.browser import Browser
 from aqt.utils import showInfo, tooltip
-from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
+from PyQt6.QtWidgets import (
+    QApplication,
+    QDialog,
+    QVBoxLayout,
+    QHBoxLayout,
+    QTextEdit,
+    QPushButton,
+    QLabel,
+)
 from PyQt6.QtCore import Qt
 import re
 
 # --- Kompatibilitätsschicht für PyQt5/PyQt6 ---
 try:
     # PyQt6
     WINDOW_STAYS_ON_TOP = Qt.WindowType.WindowStaysOnTopHint
 except AttributeError:
     # PyQt5
     WINDOW_STAYS_ON_TOP = Qt.WindowStaysOnTopHint
 
 # --- Übersetzungen ---
 LANGUAGES = {
     "de": {
         "menu_item_copy": "Notiz-IDs als Suchstring kopieren",
         "menu_item_compare": "Notiz-IDs mit Freund vergleichen",
         "copied_success": "Notiz-IDs kopiert ({num_ids} IDs). Beispiel: {example_string}...",
         
         # Dialogtexte
         "compare_dialog_title": "Notiz-IDs vergleichen",
         "your_nids_label": "Deine Notiz-IDs (die du hast):",
         "friend_nids_label": "Notiz-IDs deines Freundes (die er hat):",
         "friend_paste_button": "Aus Zwischenablage einfügen",
         "compare_button": "Vergleichen",
         "cancel_button": "Abbrechen",
-        "invalid_nids_format": "Ungültiges ID-Format. Bitte geben Sie gültige Notiz-IDs ein (z.B. 'nid:123 OR nid:456' oder nur '123' pro Zeile).",
+        "invalid_nids_format": (
+            "Ungültiges ID-Format. Bitte geben Sie gültige Notiz-IDs ein (z.B. 'nid:123 OR nid:456' oder nur "
+            "'123' pro Zeile)."
+        ),
         "no_missing_cards": "Du hast alle ausgewählten Karten deines Freundes!",
         "missing_cards_found": "{num_missing} fehlende Karten im Browser angezeigt. Suchstring in Zwischenablage kopiert."
     },
     "en": {
         "menu_item_copy": "Copy Note IDs as Search String",
         "menu_item_compare": "Compare Note IDs with Friend",
         "copied_success": "Note IDs copied ({num_ids} IDs). Example: {example_string}...",
 
         # Dialogtexts
         "compare_dialog_title": "Compare Note IDs",
         "your_nids_label": "Your Note IDs (that you have):",
         "friend_nids_label": "Friend's Note IDs (that they have):",
         "friend_paste_button": "Paste from clipboard",
         "compare_button": "Compare",
         "cancel_button": "Cancel",
-        "invalid_nids_format": "Invalid ID format. Please enter valid Note IDs (e.g., 'nid:123 OR nid:456' or just '123' per line).",
+        "invalid_nids_format": (
+            "Invalid ID format. Please enter valid Note IDs (e.g., 'nid:123 OR nid:456' or just '123' per line)."
+        ),
         "no_missing_cards": "You have all selected cards your friend has!",
         "missing_cards_found": "{num_missing} missing cards displayed in browser. Search string copied to clipboard."
     }
 }
 
 # Funktion, um den passenden Text für die aktuelle Anki-Sprache zu erhalten
 def get_localized_text(key, **kwargs):
     lang_code = ""
     try:
         lang_code = mw.pm.meta['interfaceLang'].split('-')[0]
     except (AttributeError, KeyError):
         pass
 
     if lang_code not in LANGUAGES:
         lang_code = 'en'
     
     text = LANGUAGES[lang_code].get(key, LANGUAGES['en'].get(key, key))
     return text.format(**kwargs)
 
 # -----------------------------------------------------------------------------
 # Bestehende Funktion: Notiz-IDs als Suchstring kopieren
 # -----------------------------------------------------------------------------
 def set_clipboard_text(text: str) -> None:
     clipboard = QApplication.clipboard()
     mode_enum = getattr(clipboard, "Mode", None)
@@ -226,37 +239,39 @@ def show_nid_compare_dialog_and_compare(browser: Browser):
             showInfo(get_localized_text("invalid_nids_format"))
             return
 
         if not friend_nids:
             showInfo(get_localized_text("invalid_nids_format"))
             return
 
         missing_nids = friend_nids - your_nids
 
         if not missing_nids:
             tooltip(get_localized_text("no_missing_cards"))
         else:
             missing_search_string_parts = [f"nid:{nid}" for nid in missing_nids]
             final_missing_search_string = " OR ".join(missing_search_string_parts)
             try:
                 browser.search_for(final_missing_search_string)
             except AttributeError:
                 browser.setFilter(final_missing_search_string)
             set_clipboard_text(final_missing_search_string)
             tooltip(get_localized_text("missing_cards_found", num_missing=len(missing_nids)))
 
 # -----------------------------------------------------------------------------
 # Kontextmenü-Integration
 # -----------------------------------------------------------------------------
 def on_browser_will_show_context_menu(browser, menu):
+    header_action = QAction("Anki ID Copy", browser)
+    header_action.setEnabled(False)
+    menu.addAction(header_action)
+
     action_copy = QAction(get_localized_text("menu_item_copy"), browser)
     action_copy.triggered.connect(lambda: copy_note_ids_as_search_string(browser))
     action_copy.setEnabled(bool(browser.selectedNotes()))
     menu.addAction(action_copy)
 
     action_compare = QAction(get_localized_text("menu_item_compare"), browser)
     action_compare.triggered.connect(lambda: show_nid_compare_dialog_and_compare(browser))
-
-    menu.addSeparator()
     menu.addAction(action_compare)
 
 gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
 
EOF
)
