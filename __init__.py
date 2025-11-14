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
    QMenu,
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
        "invalid_nids_format": "Ungültiges ID-Format. Bitte geben Sie gültige Notiz-IDs ein (z.B. 'nid:123 OR nid:456' oder nur '123' pro Zeile).",
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
        "invalid_nids_format": "Invalid ID format. Please enter valid Note IDs (e.g., 'nid:123 OR nid:456' or just '123' per line).",
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
    modes_to_try = []
    if mode_enum is not None:
        modes_to_try.append(getattr(mode_enum, "Clipboard", None))
        selection_mode = getattr(mode_enum, "Selection", None)
        if selection_mode is not None:
            modes_to_try.append(selection_mode)

    if not modes_to_try:
        clipboard.setText(text)
    else:
        for mode in modes_to_try:
            if mode is not None:
                clipboard.setText(text, mode)


def copy_note_ids_as_search_string(browser: Browser):
    selected_nids = browser.selectedNotes()

    if not selected_nids:
        # Keine Meldung anzeigen, um Pop-up zu vermeiden
        return

    search_string_parts = []
    for nid in selected_nids:
        search_string_parts.append(f"nid:{nid}")

    final_search_string = " OR ".join(search_string_parts)

    set_clipboard_text(final_search_string)

    preview = final_search_string[:50]
    if len(final_search_string) > 50:
        preview += "…"

    message = get_localized_text(
        "copied_success",
        num_ids=len(selected_nids),
        example_string=preview
    )
    tooltip(message)

# -----------------------------------------------------------------------------
# Helper-Funktion zum Parsen von NIDs aus Textfeldern
# -----------------------------------------------------------------------------
def parse_nids_from_text(text_content: str) -> set:
    nids = set()
    # Erlaubt flexible Trennzeichen (Leerzeichen, neue Zeilen, Kommas, "or", etc.)
    # und ignoriert ungültige Einträge ohne das restliche Parsing zu stoppen.
    for match in re.finditer(r"(?i)\bnid:\s*(\d+)\b|\b(\d+)\b", text_content):
        nid = match.group(1) or match.group(2)
        if nid is not None:
            try:
                nids.add(int(nid))
            except ValueError:
                # Sollte nicht vorkommen, bewahrt aber defensive Robustheit
                continue
    return nids

# -----------------------------------------------------------------------------
# Benutzerdefiniertes Dialogfenster für den NID-Vergleich
# -----------------------------------------------------------------------------
class NIDCompareDialog(QDialog):
    def __init__(self, parent=None, get_localized_text_func=None, initial_your_nids_text=""):
        super().__init__(parent)
        self.get_localized_text = get_localized_text_func if get_localized_text_func else (lambda key, **kwargs: key)
        self.setWindowTitle(self.get_localized_text("compare_dialog_title"))
        # Fenster bleibt oben (PyQt5 + PyQt6 kompatibel)
        self.setWindowFlags(self.windowFlags() | WINDOW_STAYS_ON_TOP)

        self.your_nids_text_edit = QTextEdit()
        self.friend_nids_text_edit = QTextEdit()

        # Setze den initialen Text für deine NIDs
        self.your_nids_text_edit.setPlainText(initial_your_nids_text)

        self.compare_button = QPushButton(self.get_localized_text("compare_button"))
        self.cancel_button = QPushButton(self.get_localized_text("cancel_button"))

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        # Linke Seite: Deine IDs
        your_nids_layout = QVBoxLayout()
        your_nids_layout.addWidget(QLabel(self.get_localized_text("your_nids_label")))
        your_nids_layout.addWidget(self.your_nids_text_edit)
        input_layout.addLayout(your_nids_layout)

        # Rechte Seite: Freunds IDs
        friend_nids_layout = QVBoxLayout()
        friend_label_row = QHBoxLayout()
        friend_label_row.addWidget(QLabel(self.get_localized_text("friend_nids_label")))
        friend_label_row.addStretch(1)
        self.friend_paste_button = QPushButton(self.get_localized_text("friend_paste_button"))
        self.friend_paste_button.setAutoDefault(False)
        self.friend_paste_button.setDefault(False)
        friend_label_row.addWidget(self.friend_paste_button)
        friend_nids_layout.addLayout(friend_label_row)
        friend_nids_layout.addWidget(self.friend_nids_text_edit)
        input_layout.addLayout(friend_nids_layout)

        main_layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1) # Schiebt Buttons nach rechts
        button_layout.addWidget(self.compare_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.compare_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.friend_paste_button.clicked.connect(self.fill_friend_from_clipboard)

    def get_your_nids_text(self):
        return self.your_nids_text_edit.toPlainText()

    def get_friend_nids_text(self):
        return self.friend_nids_text_edit.toPlainText()

    def fill_friend_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            self.friend_nids_text_edit.setPlainText(clipboard_text)
            self.friend_nids_text_edit.selectAll()
            self.friend_nids_text_edit.setFocus()


# -----------------------------------------------------------------------------
# Dialog öffnen und Vergleich durchführen
# -----------------------------------------------------------------------------
def show_nid_compare_dialog_and_compare(browser: Browser):
    selected_nids = browser.selectedNotes()
    initial_your_nids_text = ""
    if selected_nids:
        initial_your_nids_parts = [f"nid:{nid}" for nid in selected_nids]
        initial_your_nids_text = " OR ".join(initial_your_nids_parts)

    dialog = NIDCompareDialog(mw, get_localized_text, initial_your_nids_text)
    if dialog.exec():
        your_text = dialog.get_your_nids_text()
        friend_text = dialog.get_friend_nids_text()

        your_nids = parse_nids_from_text(your_text)
        friend_nids = parse_nids_from_text(friend_text)

        if not your_nids and not friend_nids:
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
    addon_menu = QMenu("Anki ID Copy", menu)
    menu.addMenu(addon_menu)

    action_copy = QAction(get_localized_text("menu_item_copy"), browser)
    action_copy.triggered.connect(lambda: copy_note_ids_as_search_string(browser))
    action_copy.setEnabled(bool(browser.selectedNotes()))
    addon_menu.addAction(action_copy)

    action_compare = QAction(get_localized_text("menu_item_compare"), browser)
    action_compare.triggered.connect(lambda: show_nid_compare_dialog_and_compare(browser))
    addon_menu.addAction(action_compare)

gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
