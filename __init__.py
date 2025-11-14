# -*- coding: utf-8 -*-
# Anki Add-on: Notiz-IDs kopieren & Vergleichs-Dialog (mit vorausgefüllten eigenen IDs)

from aqt import mw, QAction, gui_hooks
from aqt.browser import Browser
from aqt.utils import showInfo, tooltip
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
)
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
@@ -226,37 +234,39 @@ def show_nid_compare_dialog_and_compare(browser: Browser):
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
    header_action = QAction("Anki ID Copy", browser)
    header_action.setEnabled(False)
    menu.addAction(header_action)

    action_copy = QAction(get_localized_text("menu_item_copy"), browser)
    action_copy.triggered.connect(lambda: copy_note_ids_as_search_string(browser))
    action_copy.setEnabled(bool(browser.selectedNotes()))
    menu.addAction(action_copy)

    action_compare = QAction(get_localized_text("menu_item_compare"), browser)
    action_compare.triggered.connect(lambda: show_nid_compare_dialog_and_compare(browser))
    menu.addAction(action_compare)

gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)