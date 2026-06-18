# -*- coding: utf-8 -*-
# Anki Add-on: Notiz-IDs kopieren & Vergleichs-Dialog (mit vorausgefüllten eigenen IDs)

import re

from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.utils import showInfo, tooltip
# Import all Qt symbols through aqt.qt so the add-on works on both Qt5 and Qt6
# Anki builds (importing PyQt6 directly crashes on Qt5 builds).
from aqt.qt import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QAction,
    Qt,
)

from .nid_tools import parse_nids_from_text, build_search_string

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
        "copied_success": "Notiz-IDs kopiert ({num_ids} Stück). Beispiel: {example_string}",

        # Dialogtexte
        "compare_dialog_title": "Notiz-IDs vergleichen",
        "your_nids_label": "Deine Notiz-IDs (die du hast):",
        "friend_nids_label": "Notiz-IDs deines Freundes (die er hat):",
        "friend_paste_button": "Aus Zwischenablage einfügen",
        "compare_button": "Vergleichen",
        "cancel_button": "Abbrechen",
        "invalid_nids_format": "Es wurden keine gültigen Notiz-IDs erkannt. Bitte gib gültige IDs ein (z. B. 'nid:123 OR nid:456', 'nid:123,456' oder eine ID pro Zeile).",
        "your_field_empty": "Bitte gib zuerst deine eigenen Notiz-IDs ein (oder wähle Karten im Browser aus), bevor du vergleichst.",
        "friend_field_empty": "Bitte füge die Notiz-IDs deines Freundes ein.",
        "clipboard_empty": "Die Zwischenablage ist leer oder enthält keinen Text.",
        "no_missing_cards": "Du hast bereits alle Notizen deines Freundes!",
        "missing_cards_found": "{num_missing} fehlende Notizen im Browser angezeigt. Suchstring in Zwischenablage kopiert."
    },
    "en": {
        "menu_item_copy": "Copy Note IDs as Search String",
        "menu_item_compare": "Compare Note IDs with Friend",
        "copied_success": "Note IDs copied ({num_ids} total). Example: {example_string}",

        # Dialog texts
        "compare_dialog_title": "Compare Note IDs",
        "your_nids_label": "Your Note IDs (that you have):",
        "friend_nids_label": "Friend's Note IDs (that they have):",
        "friend_paste_button": "Paste from clipboard",
        "compare_button": "Compare",
        "cancel_button": "Cancel",
        "invalid_nids_format": "No valid Note IDs were recognized. Please enter valid IDs (e.g., 'nid:123 OR nid:456', 'nid:123,456' or one ID per line).",
        "your_field_empty": "Please enter your own Note IDs first (or select cards in the browser) before comparing.",
        "friend_field_empty": "Please paste your friend's Note IDs.",
        "clipboard_empty": "The clipboard is empty or does not contain any text.",
        "no_missing_cards": "You already have all of your friend's notes!",
        "missing_cards_found": "{num_missing} missing notes displayed in browser. Search string copied to clipboard."
    }
}

# Funktion, um den passenden Text für die aktuelle Anki-Sprache zu erhalten
def get_localized_text(key, **kwargs):
    lang_code = ""
    try:
        # Anki speichert die UI-Sprache als 'defaultLang' (z. B. 'de_DE', 'en_US').
        raw_lang = mw.pm.meta.get("defaultLang") or ""
        lang_code = re.split(r"[-_]", raw_lang)[0].lower()
    except (AttributeError, KeyError, TypeError):
        pass

    if lang_code not in LANGUAGES:
        lang_code = "en"

    text = LANGUAGES[lang_code].get(key, LANGUAGES["en"].get(key, key))
    return text.format(**kwargs)

# -----------------------------------------------------------------------------
# Zwischenablage setzen
# -----------------------------------------------------------------------------
def set_clipboard_text(text: str) -> None:
    # Bewusst nur die Standard-Zwischenablage beschreiben. Das frühere Schreiben
    # in den X11/Wayland-Selection-Buffer überschrieb still die Maus-Auswahl.
    QApplication.clipboard().setText(text)


def copy_note_ids_as_search_string(browser: Browser):
    selected_nids = browser.selectedNotes()

    if not selected_nids:
        # Keine Meldung anzeigen, um Pop-up zu vermeiden
        return

    final_search_string = build_search_string(selected_nids)
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
        button_layout.addStretch(1)  # Schiebt Buttons nach rechts
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
        else:
            tooltip(self.get_localized_text("clipboard_empty"))


# -----------------------------------------------------------------------------
# Dialog öffnen und Vergleich durchführen
# -----------------------------------------------------------------------------
def show_nid_compare_dialog_and_compare(browser: Browser):
    selected_nids = browser.selectedNotes()
    initial_your_nids_text = build_search_string(selected_nids) if selected_nids else ""

    dialog = NIDCompareDialog(mw, get_localized_text, initial_your_nids_text)
    if dialog.exec():
        your_text = dialog.get_your_nids_text()
        friend_text = dialog.get_friend_nids_text()

        your_nids = parse_nids_from_text(your_text)
        friend_nids = parse_nids_from_text(friend_text)

        # Erst das Freundes-Feld prüfen: leer vs. unlesbar getrennt melden.
        if not friend_nids:
            if friend_text.strip():
                showInfo(get_localized_text("invalid_nids_format"))
            else:
                showInfo(get_localized_text("friend_field_empty"))
            return

        # Ohne eigene IDs würde der Vergleich sonst alles als "fehlend" melden.
        if not your_nids:
            if your_text.strip():
                showInfo(get_localized_text("invalid_nids_format"))
            else:
                showInfo(get_localized_text("your_field_empty"))
            return

        missing_nids = friend_nids - your_nids

        if not missing_nids:
            tooltip(get_localized_text("no_missing_cards"))
        else:
            final_missing_search_string = build_search_string(sorted(missing_nids))
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
    # kleine Trennung zu den vorherigen Einträgen
    menu.addSeparator()

    # Überschrift "Anki ID Copy" (nicht klickbar)
    header = QAction("Anki ID Copy", browser)
    header.setEnabled(False)  # deaktiviert, nur Label

    font = header.font()
    font.setBold(True)
    header.setFont(font)

    menu.addAction(header)

    # Eintrag: menu_item_copy
    action_copy = QAction(get_localized_text("menu_item_copy"), browser)
    action_copy.triggered.connect(lambda: copy_note_ids_as_search_string(browser))
    action_copy.setEnabled(bool(browser.selectedNotes()))
    menu.addAction(action_copy)

    # Eintrag: menu_item_compare
    action_compare = QAction(get_localized_text("menu_item_compare"), browser)
    action_compare.triggered.connect(
        lambda: show_nid_compare_dialog_and_compare(browser)
    )
    menu.addAction(action_compare)

    # optional: Trennung nach dem Block
    menu.addSeparator()

gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
