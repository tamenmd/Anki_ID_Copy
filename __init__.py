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
    QKeySequence,
    Qt,
)

from .nid_tools import parse_nids_from_text, build_search_string, compute_diff

# --- Kompatibilitätsschicht für PyQt5/PyQt6 ---
try:
    # PyQt6
    WINDOW_STAYS_ON_TOP = Qt.WindowType.WindowStaysOnTopHint
except AttributeError:
    # PyQt5
    WINDOW_STAYS_ON_TOP = Qt.WindowStaysOnTopHint

# --- Konfiguration ---
DEFAULT_CONFIG = {
    "copy_shortcut": "Ctrl+Alt+C",
    "search_format": "compact",
}


def get_config():
    """Return the merged add-on config, with defaults as a safety net."""
    user_cfg = {}
    try:
        user_cfg = mw.addonManager.getConfig(__name__) or {}
    except Exception:
        user_cfg = {}
    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in user_cfg.items() if v is not None})
    return merged


def use_compact_format():
    """True unless the user explicitly chose the verbose 'or' format."""
    return str(get_config().get("search_format", "compact")).lower() != "or"


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
        "result_dialog_title": "Vergleichsergebnis",
        "result_totals": "Deine IDs: {your}  ·  Freundes IDs: {friend}",
        "region_missing_present": "Fehlend – in deiner Sammlung vorhanden (z. B. suspendiert): {count}",
        "region_missing_absent": "Fehlend – gar nicht in deiner Sammlung: {count}",
        "region_extra": "Zusätzlich – du hast, Freund nicht: {count}",
        "region_shared": "Gemeinsam: {count}",
        "btn_show": "Im Browser zeigen",
        "btn_copy": "Kopieren",
        "close_button": "Schließen",
        "region_copied": "{count} IDs kopiert."
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
        "result_dialog_title": "Comparison Result",
        "result_totals": "Your IDs: {your}  ·  Friend's IDs: {friend}",
        "region_missing_present": "Missing – present in your collection (e.g. suspended): {count}",
        "region_missing_absent": "Missing – not in your collection at all: {count}",
        "region_extra": "Extra – you have, friend doesn't: {count}",
        "region_shared": "Shared: {count}",
        "btn_show": "Show in browser",
        "btn_copy": "Copy",
        "close_button": "Close",
        "region_copied": "{count} IDs copied."
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

    final_search_string = build_search_string(selected_nids, compact=use_compact_format())
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
# Hilfsfunktion: welche der NIDs existieren tatsächlich in der Sammlung?
# -----------------------------------------------------------------------------
def find_existing_nids(col, nids):
    """Return the subset of ``nids`` that actually exist in the collection."""
    if not nids:
        return set()
    search = build_search_string(nids, compact=True)
    finder = getattr(col, "find_notes", None) or getattr(col, "findNotes", None)
    if finder is None:
        return set()
    try:
        return set(int(n) for n in finder(search))
    except Exception:
        return set()


# -----------------------------------------------------------------------------
# Ergebnis-Scorecard: zeigt alle Diff-Regionen mit klickbaren Aktionen
# -----------------------------------------------------------------------------
class NIDCompareResultDialog(QDialog):
    def __init__(self, browser, your_count, friend_count,
                 present_missing, absent_missing, extra, shared,
                 get_localized_text_func):
        super().__init__(browser)
        self.browser = browser
        self.t = get_localized_text_func
        self.setWindowTitle(self.t("result_dialog_title"))
        self.setWindowFlags(self.windowFlags() | WINDOW_STAYS_ON_TOP)

        layout = QVBoxLayout()

        totals = QLabel(self.t("result_totals", your=your_count, friend=friend_count))
        totals_font = totals.font()
        totals_font.setBold(True)
        totals.setFont(totals_font)
        layout.addWidget(totals)

        self._add_region(layout, "region_missing_present", present_missing, allow_show=True)
        self._add_region(layout, "region_missing_absent", absent_missing, allow_show=False)
        self._add_region(layout, "region_extra", extra, allow_show=True)
        self._add_region(layout, "region_shared", shared, allow_show=True)

        close_button = QPushButton(self.t("close_button"))
        close_button.clicked.connect(self.close)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(close_button)
        layout.addLayout(close_row)

        self.setLayout(layout)
        self.resize(580, 240)

    def _add_region(self, layout, label_key, nids, allow_show):
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t(label_key, count=len(nids))))
        row.addStretch(1)

        search = build_search_string(sorted(nids), compact=use_compact_format())
        has_items = bool(nids)

        show_button = QPushButton(self.t("btn_show"))
        copy_button = QPushButton(self.t("btn_copy"))
        for button in (show_button, copy_button):
            button.setAutoDefault(False)
            button.setDefault(False)
        show_button.setEnabled(has_items and allow_show)
        copy_button.setEnabled(has_items)
        show_button.clicked.connect(lambda: self._show(search))
        copy_button.clicked.connect(lambda: self._copy(search, len(nids)))

        row.addWidget(show_button)
        row.addWidget(copy_button)
        layout.addLayout(row)

    def _show(self, search):
        try:
            self.browser.search_for(search)
        except AttributeError:
            self.browser.setFilter(search)

    def _copy(self, search, count):
        set_clipboard_text(search)
        tooltip(self.t("region_copied", count=count))


# -----------------------------------------------------------------------------
# Dialog öffnen und Vergleich durchführen
# -----------------------------------------------------------------------------
def show_nid_compare_dialog_and_compare(browser: Browser):
    selected_nids = browser.selectedNotes()
    initial_your_nids_text = build_search_string(selected_nids, compact=use_compact_format()) if selected_nids else ""

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

        diff = compute_diff(your_nids, friend_nids)
        missing = diff["missing"]

        # "Fehlend" aufteilen: was liegt trotzdem in der Sammlung (z. B. suspendiert)?
        present_missing = missing & find_existing_nids(mw.col, missing) if missing else set()
        absent_missing = missing - present_missing

        result_dialog = NIDCompareResultDialog(
            browser,
            your_count=len(your_nids),
            friend_count=len(friend_nids),
            present_missing=present_missing,
            absent_missing=absent_missing,
            extra=diff["extra"],
            shared=diff["shared"],
            get_localized_text_func=get_localized_text,
        )
        # Referenz halten, damit der nicht-modale Dialog nicht weggeräumt wird.
        browser._ankiidcopy_result_dialog = result_dialog
        result_dialog.show()

# -----------------------------------------------------------------------------
# Persistente Copy-Aktion (damit der Shortcut wirkt UND im Menü angezeigt wird)
# -----------------------------------------------------------------------------
def get_or_create_copy_action(browser):
    """Return a persistent copy QAction for this browser, creating it once.

    Registering it on the browser window makes the configured shortcut active
    window-wide; reusing the same action in the context menu shows the shortcut
    next to the entry and avoids a duplicate/ambiguous shortcut binding.
    """
    existing = getattr(browser, "_ankiidcopy_copy_action", None)
    if existing is not None:
        return existing

    action = QAction(get_localized_text("menu_item_copy"), browser)
    shortcut = (get_config().get("copy_shortcut") or "").strip()
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(lambda: copy_note_ids_as_search_string(browser))
    browser.addAction(action)
    browser._ankiidcopy_copy_action = action
    return action

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

    # Eintrag: menu_item_copy — persistente Aktion mit Shortcut-Anzeige
    menu.addAction(get_or_create_copy_action(browser))

    # Eintrag: menu_item_compare
    action_compare = QAction(get_localized_text("menu_item_compare"), browser)
    action_compare.triggered.connect(
        lambda: show_nid_compare_dialog_and_compare(browser)
    )
    menu.addAction(action_compare)

    # optional: Trennung nach dem Block
    menu.addSeparator()


# Shortcut früh registrieren, damit er auch ohne geöffnetes Kontextmenü wirkt.
gui_hooks.browser_will_show.append(get_or_create_copy_action)
gui_hooks.browser_will_show_context_menu.append(on_browser_will_show_context_menu)
