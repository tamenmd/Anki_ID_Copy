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
    QComboBox,
    QScrollArea,
    QWidget,
    QFrame,
    Qt,
)

from .nid_tools import parse_nids_from_text, build_search_string, compute_diff, group_counts

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
        "compare_help": "Füge links deine und rechts die Notiz-IDs deines Freundes ein. Du bekommst danach eine Auswertung: welche Notizen dir fehlen, welche du zusätzlich hast und welche gemeinsam sind.",
        "your_placeholder": "z. B. nid:123,456 — oder eine ID pro Zeile",
        "friend_placeholder": "IDs deines Freundes einfügen (Button oben rechts oder Strg+V)",
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
        "region_missing_present": "Fehlend – in deiner Sammlung vorhanden (z. B. suspendiert)",
        "region_missing_absent": "Fehlend – gar nicht in deiner Sammlung",
        "region_extra": "Zusätzlich – du hast, Freund nicht",
        "region_shared": "Gemeinsam",
        "btn_show": "Im Browser zeigen",
        "btn_copy": "Kopieren",
        "close_button": "Schließen",
        "region_copied": "{count} IDs kopiert.",
        "btn_suspended": "Suspendierte zeigen ({count})",
        "btn_breakdown": "Aufschlüsseln",
        "breakdown_title": "Aufschlüsselung: {region}",
        "group_by_label": "Gruppieren nach:",
        "group_by_deck": "Deck (Fach)",
        "group_by_tag": "Tag",
        "breakdown_other": "… {groups} weitere Gruppen ({notes} Notizen)"
    },
    "en": {
        "menu_item_copy": "Copy Note IDs as Search String",
        "menu_item_compare": "Compare Note IDs with Friend",
        "copied_success": "Note IDs copied ({num_ids} total). Example: {example_string}",

        # Dialog texts
        "compare_dialog_title": "Compare Note IDs",
        "compare_help": "Paste your Note IDs on the left and your friend's on the right. You'll then get a breakdown: which notes you're missing, which you have extra, and which you share.",
        "your_placeholder": "e.g. nid:123,456 — or one ID per line",
        "friend_placeholder": "Paste your friend's IDs (button top-right or Ctrl+V)",
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
        "region_missing_present": "Missing – present in your collection (e.g. suspended)",
        "region_missing_absent": "Missing – not in your collection at all",
        "region_extra": "Extra – you have, friend doesn't",
        "region_shared": "Shared",
        "btn_show": "Show in browser",
        "btn_copy": "Copy",
        "close_button": "Close",
        "region_copied": "{count} IDs copied.",
        "btn_suspended": "Show suspended ({count})",
        "btn_breakdown": "Break down",
        "breakdown_title": "Breakdown: {region}",
        "group_by_label": "Group by:",
        "group_by_deck": "Deck (subject)",
        "group_by_tag": "Tag",
        "breakdown_other": "… {groups} more groups ({notes} notes)"
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
        self.setStyleSheet(base_stylesheet())

        self.your_nids_text_edit = QTextEdit()
        self.your_nids_text_edit.setObjectName("aic_input")
        self.your_nids_text_edit.setPlaceholderText(self.get_localized_text("your_placeholder"))
        self.friend_nids_text_edit = QTextEdit()
        self.friend_nids_text_edit.setObjectName("aic_input")
        self.friend_nids_text_edit.setPlaceholderText(self.get_localized_text("friend_placeholder"))

        # Setze den initialen Text für deine NIDs
        self.your_nids_text_edit.setPlainText(initial_your_nids_text)

        self.friend_paste_button = make_action_button(self.get_localized_text("friend_paste_button"))
        self.compare_button = make_primary_button(self.get_localized_text("compare_button"))
        self.cancel_button = make_action_button(self.get_localized_text("cancel_button"))

        self.init_ui()

    def _make_input_card(self, label_text, text_edit, accent, extra_header_widget=None):
        card = QFrame()
        card.setObjectName("aic_card")
        card.setStyleSheet(
            "QFrame#aic_card { background-color: rgba(127,127,127,0.05);"
            " border: 1px solid rgba(127,127,127,0.18);"
            " border-left: 4px solid %s; border-radius: 8px; }" % _css_hex(accent)
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 9, 12, 9)
        card_layout.setSpacing(7)

        header = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("aic_region")
        header.addWidget(label)
        header.addStretch(1)
        if extra_header_widget is not None:
            header.addWidget(extra_header_widget)
        card_layout.addLayout(header)
        card_layout.addWidget(text_edit)
        return card

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        title = QLabel(self.get_localized_text("compare_dialog_title"))
        title.setObjectName("aic_title")
        main_layout.addWidget(title)

        help_label = QLabel(self.get_localized_text("compare_help"))
        help_label.setObjectName("aic_subtitle")
        help_label.setWordWrap(True)
        main_layout.addWidget(help_label)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        input_layout.addWidget(self._make_input_card(
            self.get_localized_text("your_nids_label"),
            self.your_nids_text_edit,
            accent_rgb("region_extra"),
        ))
        input_layout.addWidget(self._make_input_card(
            self.get_localized_text("friend_nids_label"),
            self.friend_nids_text_edit,
            accent_rgb("region_shared"),
            extra_header_widget=self.friend_paste_button,
        ))
        main_layout.addLayout(input_layout)

        # Buttons (rechtsbündig): Abbrechen sekundär, Vergleichen primär
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.compare_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.resize(680, 440)

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
def _find_notes(col, search):
    finder = getattr(col, "find_notes", None) or getattr(col, "findNotes", None)
    if finder is None:
        return set()
    try:
        return set(int(n) for n in finder(search))
    except Exception:
        return set()


def find_existing_nids(col, nids):
    """Return the subset of ``nids`` that actually exist in the collection."""
    if not nids:
        return set()
    return _find_notes(col, build_search_string(nids, compact=True))


def find_suspended_nids(col, nids):
    """Return the subset of ``nids`` that have at least one suspended card."""
    if not nids:
        return set()
    search = "is:suspended (" + build_search_string(nids, compact=True) + ")"
    return _find_notes(col, search) & set(nids)


def compute_coverage(col, nids, mode):
    """Group ``nids`` for the coverage breakdown.

    Returns a list of ``(label, count, search_clause)`` sorted by count desc.
    ``mode == "deck"`` assigns each note to the deck of its first card (so each
    note lands in exactly one group). ``mode == "tag"`` lets each note count
    once per tag it carries.
    """
    if not nids:
        return []
    id_list = ",".join(str(int(n)) for n in nids)
    pairs = []
    clause_for = {}
    try:
        if mode == "tag":
            for note_id, tag_str in col.db.all(
                "select id, tags from notes where id in (%s)" % id_list
            ):
                for tag in (tag_str or "").split():
                    pairs.append((tag, int(note_id)))
                    clause_for[tag] = 'tag:"%s"' % tag
        else:  # deck
            first_did = {}
            for note_id, did in col.db.all(
                "select nid, did from cards where nid in (%s)" % id_list
            ):
                first_did.setdefault(int(note_id), int(did))
            for note_id, did in first_did.items():
                name = col.decks.name(did)
                pairs.append((name, note_id))
                clause_for[name] = 'deck:"%s"' % name
    except Exception:
        return []
    return [
        (label, count, clause_for.get(label, ""))
        for label, count in group_counts(pairs)
    ]


# Wie viele Gruppen maximal im Aufschlüsselungs-Fenster gelistet werden.
COVERAGE_MAX_GROUPS = 40


# -----------------------------------------------------------------------------
# UI-Styling: theme-sichere Akzentfarben (hell & dunkel) + Stylesheet-Helfer
# -----------------------------------------------------------------------------
try:
    POINTING_CURSOR = Qt.CursorShape.PointingHandCursor
except AttributeError:
    POINTING_CURSOR = Qt.PointingHandCursor

# Akzent je Region als (hell, dunkel) — auf beiden Untergründen gut lesbar.
_REGION_ACCENTS = {
    "region_missing_present": {"light": (201, 122, 0), "dark": (229, 181, 103)},   # amber
    "region_missing_absent": {"light": (199, 70, 70), "dark": (224, 108, 117)},    # rot
    "region_extra": {"light": (45, 110, 200), "dark": (97, 175, 239)},             # blau
    "region_shared": {"light": (47, 145, 87), "dark": (152, 195, 121)},            # grün
}


def is_night_mode():
    try:
        from aqt.theme import theme_manager
        return bool(theme_manager.night_mode)
    except Exception:
        return False


def accent_rgb(region_key):
    entry = _REGION_ACCENTS.get(region_key, {"light": (120, 120, 120), "dark": (150, 150, 150)})
    return entry["dark" if is_night_mode() else "light"]


def _css_hex(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def _shift(rgb, delta):
    return tuple(max(0, min(255, c + delta)) for c in rgb)


def _readable_text_on(rgb):
    # Luminanz-basiert: dunkler Text auf hellem Akzent, sonst weiß.
    luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return "#1b1b1b" if luminance > 150 else "#ffffff"


def _elide(text, max_len=58):
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def base_stylesheet():
    # Nur halbtransparente Grautöne + Schrift: funktioniert auf hell UND dunkel,
    # ohne feste Hinter-/Vordergrundfarben zu erzwingen.
    return (
        "QLabel#aic_title { font-size: 15pt; font-weight: 600; }"
        "QLabel#aic_subtitle { color: rgba(127,127,127,0.95); }"
        "QLabel#aic_region { font-weight: 600; }"
        "QPushButton#aic_btn {"
        "  background-color: rgba(127,127,127,0.10);"
        "  border: 1px solid rgba(127,127,127,0.28);"
        "  border-radius: 6px; padding: 4px 12px; }"
        "QPushButton#aic_btn:hover { background-color: rgba(127,127,127,0.22); }"
        "QPushButton#aic_btn:pressed { background-color: rgba(127,127,127,0.32); }"
        "QPushButton#aic_btn:disabled {"
        "  color: rgba(127,127,127,0.55); border-color: rgba(127,127,127,0.12); }"
        "QTextEdit#aic_input { border: 1px solid rgba(127,127,127,0.28);"
        "  border-radius: 6px; padding: 4px; }"
    )


def make_badge(text, rgb):
    badge = QLabel(text)
    badge.setStyleSheet(
        "QLabel { background-color: %s; color: %s; border-radius: 9px;"
        " padding: 1px 10px; font-weight: 600; }"
        % (_css_hex(rgb), _readable_text_on(rgb))
    )
    return badge


def make_action_button(text):
    button = QPushButton(text)
    button.setObjectName("aic_btn")
    button.setAutoDefault(False)
    button.setDefault(False)
    button.setCursor(POINTING_CURSOR)
    return button


def make_primary_button(text):
    rgb = accent_rgb("region_extra")  # blauer Akzent für die Hauptaktion
    button = QPushButton(text)
    button.setObjectName("aic_primary")
    button.setStyleSheet(
        "QPushButton#aic_primary { background-color: %s; color: %s; border: none;"
        " border-radius: 6px; padding: 5px 18px; font-weight: 600; }"
        "QPushButton#aic_primary:hover { background-color: %s; }"
        "QPushButton#aic_primary:pressed { background-color: %s; }"
        % (
            _css_hex(rgb),
            _readable_text_on(rgb),
            _css_hex(_shift(rgb, 18)),
            _css_hex(_shift(rgb, -12)),
        )
    )
    button.setCursor(POINTING_CURSOR)
    button.setAutoDefault(True)
    button.setDefault(True)
    return button


# -----------------------------------------------------------------------------
# Aufschlüsselungs-Fenster: Coverage einer Region nach Deck oder Tag
# -----------------------------------------------------------------------------
class NICoverageBreakdownDialog(QDialog):
    def __init__(self, browser, region_key, region_label, region_nids, get_localized_text_func):
        super().__init__(browser)
        self.browser = browser
        self.t = get_localized_text_func
        self.accent = accent_rgb(region_key)
        self.region_nids = sorted(region_nids)
        self.region_search = build_search_string(self.region_nids, compact=use_compact_format())
        self.setWindowTitle(self.t("breakdown_title", region=region_label))
        self.setWindowFlags(self.windowFlags() | WINDOW_STAYS_ON_TOP)
        self.setStyleSheet(base_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel(self.t("group_by_label")))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.t("group_by_deck"), "deck")
        self.mode_combo.addItem(self.t("group_by_tag"), "tag")
        self.mode_combo.currentIndexChanged.connect(self._rebuild)
        top_row.addWidget(self.mode_combo)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setSpacing(4)
        self.scroll.setWidget(self.rows_container)
        layout.addWidget(self.scroll)

        close_button = make_action_button(self.t("close_button"))
        close_button.clicked.connect(self.close)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(close_button)
        layout.addLayout(close_row)

        self.setLayout(layout)
        self.resize(580, 480)
        self._rebuild()

    def _rebuild(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        mode = self.mode_combo.currentData()
        groups = compute_coverage(mw.col, self.region_nids, mode)

        for label, count, clause in groups[:COVERAGE_MAX_GROUPS]:
            self.rows_layout.addWidget(self._make_row(label, count, clause))

        rest = groups[COVERAGE_MAX_GROUPS:]
        if rest:
            rest_notes = sum(count for _, count, _ in rest)
            more = QLabel(self.t("breakdown_other", groups=len(rest), notes=rest_notes))
            more.setObjectName("aic_subtitle")
            self.rows_layout.addWidget(more)
        self.rows_layout.addStretch(1)

    def _make_row(self, label, count, clause):
        container = QFrame()
        container.setObjectName("aic_row")
        container.setStyleSheet(
            "QFrame#aic_row { background-color: rgba(127,127,127,0.06);"
            " border: 1px solid rgba(127,127,127,0.14); border-radius: 6px; }"
        )
        row = QHBoxLayout(container)
        row.setContentsMargins(10, 5, 8, 5)
        row.setSpacing(8)

        name = QLabel(_elide(label))
        name.setToolTip(label)
        row.addWidget(name)
        row.addStretch(1)
        row.addWidget(make_badge(str(count), self.accent))

        if self.region_search and clause:
            search = "(%s) (%s)" % (clause, self.region_search)
        else:
            search = clause or self.region_search

        show_button = make_action_button(self.t("btn_show"))
        show_button.setEnabled(bool(search))
        show_button.clicked.connect(lambda checked=False, s=search: self._show(s))
        row.addWidget(show_button)
        return container

    def _show(self, search):
        try:
            self.browser.search_for(search)
        except AttributeError:
            self.browser.setFilter(search)


# -----------------------------------------------------------------------------
# Ergebnis-Scorecard: zeigt alle Diff-Regionen mit klickbaren Aktionen
# -----------------------------------------------------------------------------
class NIDCompareResultDialog(QDialog):
    def __init__(self, browser, your_count, friend_count, regions, get_localized_text_func):
        super().__init__(browser)
        self.browser = browser
        self.t = get_localized_text_func
        self.setWindowTitle(self.t("result_dialog_title"))
        self.setWindowFlags(self.windowFlags() | WINDOW_STAYS_ON_TOP)
        self.setStyleSheet(base_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        title = QLabel(self.t("result_dialog_title"))
        title.setObjectName("aic_title")
        layout.addWidget(title)

        subtitle = QLabel(self.t("result_totals", your=your_count, friend=friend_count))
        subtitle.setObjectName("aic_subtitle")
        layout.addWidget(subtitle)

        for region in regions:
            self._add_region(layout, region)

        close_button = make_action_button(self.t("close_button"))
        close_button.clicked.connect(self.close)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(close_button)
        layout.addLayout(close_row)

        self.setLayout(layout)
        self.resize(640, 440)

    def _add_region(self, layout, region):
        nids = region["nids"]
        key = region["key"]
        allow_show = region["allow_show"]
        suspended = region.get("suspended")  # set, or None when not locally owned
        has_items = bool(nids)
        count = len(nids)
        search = build_search_string(sorted(nids), compact=use_compact_format())
        accent = accent_rgb(key)

        card = QFrame()
        card.setObjectName("aic_card")
        card.setStyleSheet(
            "QFrame#aic_card { background-color: rgba(127,127,127,0.07);"
            " border: 1px solid rgba(127,127,127,0.18);"
            " border-left: 4px solid %s; border-radius: 8px; }" % _css_hex(accent)
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 9, 12, 9)
        card_layout.setSpacing(7)

        # Kopfzeile: Regionsname + Anzahl-Badge
        head = QHBoxLayout()
        name = QLabel(self.t(key))
        name.setObjectName("aic_region")
        head.addWidget(name)
        head.addStretch(1)
        head.addWidget(make_badge(str(count), accent))
        card_layout.addLayout(head)

        # Aktionszeile (rechtsbündig)
        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addStretch(1)

        if suspended is not None:
            region_label = self.t(key)
            breakdown_button = make_action_button(self.t("btn_breakdown"))
            breakdown_button.setEnabled(has_items)
            breakdown_button.clicked.connect(
                lambda checked=False, k=key, lbl=region_label, ns=frozenset(nids): self._open_breakdown(k, lbl, ns)
            )
            actions.addWidget(breakdown_button)

            susp_button = make_action_button(self.t("btn_suspended", count=len(suspended)))
            susp_button.setEnabled(bool(suspended))
            susp_button.clicked.connect(
                lambda checked=False, s=search: self._show("is:suspended (" + s + ")")
            )
            actions.addWidget(susp_button)

        show_button = make_action_button(self.t("btn_show"))
        show_button.setEnabled(has_items and allow_show)
        show_button.clicked.connect(lambda checked=False, s=search: self._show(s))
        actions.addWidget(show_button)

        copy_button = make_action_button(self.t("btn_copy"))
        copy_button.setEnabled(has_items)
        copy_button.clicked.connect(lambda checked=False, s=search, n=count: self._copy(s, n))
        actions.addWidget(copy_button)

        card_layout.addLayout(actions)
        layout.addWidget(card)

    def _show(self, search):
        try:
            self.browser.search_for(search)
        except AttributeError:
            self.browser.setFilter(search)

    def _copy(self, search, count):
        set_clipboard_text(search)
        tooltip(self.t("region_copied", count=count))

    def _open_breakdown(self, region_key, region_label, region_nids):
        dialog = NICoverageBreakdownDialog(self.browser, region_key, region_label, region_nids, self.t)
        if not hasattr(self.browser, "_ankiidcopy_breakdowns"):
            self.browser._ankiidcopy_breakdowns = []
        self.browser._ankiidcopy_breakdowns.append(dialog)
        dialog.show()


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
        extra = diff["extra"]
        shared = diff["shared"]

        # "Fehlend" aufteilen: was liegt trotzdem in der Sammlung (z. B. suspendiert)?
        present_missing = missing & find_existing_nids(mw.col, missing) if missing else set()
        absent_missing = missing - present_missing

        # Pro lokal vorhandener Region: welche Notizen sind bei dir suspendiert?
        regions = [
            {"key": "region_missing_present", "nids": present_missing, "allow_show": True,
             "suspended": find_suspended_nids(mw.col, present_missing)},
            {"key": "region_missing_absent", "nids": absent_missing, "allow_show": False,
             "suspended": None},
            {"key": "region_extra", "nids": extra, "allow_show": True,
             "suspended": find_suspended_nids(mw.col, extra)},
            {"key": "region_shared", "nids": shared, "allow_show": True,
             "suspended": find_suspended_nids(mw.col, shared)},
        ]

        result_dialog = NIDCompareResultDialog(
            browser,
            your_count=len(your_nids),
            friend_count=len(friend_nids),
            regions=regions,
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
