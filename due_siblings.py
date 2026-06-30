# -*- coding: utf-8 -*-
"""Anki/Qt glue for the "due siblings" feature.

Pure query logic lives in ``due_siblings_logic``; this module wires it to a
running collection: the dialog, config persistence, opening the browser and
building a filtered study deck. Qt symbols are imported through ``aqt.qt`` so
the add-on keeps working on both Qt5 and Qt6 builds.
"""

from aqt import mw, dialogs
from aqt.utils import showInfo
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QWidget,
    QAction,
)

from .due_siblings_logic import (
    compute_due_sibling_cids,
    build_cid_query,
    merge_config,
)
# Reuse the existing localization + styling helpers from the package __init__.
from . import (
    get_localized_text,
    base_stylesheet,
    make_action_button,
    make_primary_button,
    WINDOW_STAYS_ON_TOP,
)

# Addon package name (config is keyed by the top-level package, not the submodule).
ADDON_PACKAGE = __name__.split(".")[0]

DEFAULT_DUE_SIBLINGS = {
    "deck": "",
    "min_ivl": 21,
    "max_lapses": 1,
    "exclude_struggling": True,
}


def get_due_siblings_config():
    """Return the persisted due-siblings settings merged over the defaults."""
    try:
        cfg = mw.addonManager.getConfig(ADDON_PACKAGE) or {}
    except Exception:
        cfg = {}
    return merge_config(DEFAULT_DUE_SIBLINGS, cfg.get("due_siblings") or {})


def save_due_siblings_config(values):
    """Write the given due-siblings settings back into config.json (nested)."""
    try:
        cfg = mw.addonManager.getConfig(ADDON_PACKAGE) or {}
    except Exception:
        cfg = {}
    cfg["due_siblings"] = {
        "deck": str(values.get("deck", "")),
        "min_ivl": int(values.get("min_ivl", 21)),
        "max_lapses": int(values.get("max_lapses", 1)),
        "exclude_struggling": bool(values.get("exclude_struggling", True)),
    }
    try:
        mw.addonManager.writeConfig(ADDON_PACKAGE, cfg)
    except Exception:
        pass


def open_in_browser(cids):
    """Open the Anki browser filtered to exactly these card ids."""
    query = build_cid_query(cids)
    if not query:
        return
    browser = dialogs.open("Browser", mw)
    try:
        browser.search_for(query)
    except AttributeError:
        browser.setFilter(query)
    browser.activateWindow()
    browser.raise_()


def _build_filtered_legacy(col, deck_name, search, limit):
    """Fallback for builds without the modern proto filtered-deck API."""
    try:
        did = col.decks.new_filtered(deck_name)
        deck = col.decks.get(did)
        deck["terms"] = [[search, limit, 0]]
        deck["resched"] = True
        col.decks.save(deck)
        try:
            col.sched.rebuild_filtered_deck(did)
        except Exception:
            col.sched.rebuildDyn(did)
        return did
    except Exception:
        return None


def build_and_select_filtered_deck(cids, deck_name):
    """Build/refresh a rescheduling filtered deck for the cards; return its id.

    Reuses an existing filtered deck of the same name instead of creating
    duplicates. Returns ``None`` on failure.
    """
    col = mw.col
    search = build_cid_query(cids)
    if not search:
        return None
    limit = max(len(cids), 1)
    try:
        existing_id = None
        try:
            existing_id = col.decks.id_for_name(deck_name)
        except Exception:
            existing_id = None
        deck = col.sched.get_or_create_filtered_deck(existing_id or 0)
        try:
            deck.name = deck_name
        except Exception:
            pass
        deck.config.reschedule = True
        deck.config.ClearField("search_terms")
        term = deck.config.search_terms.add()
        term.search = search
        term.limit = limit
        out = col.sched.add_or_update_filtered_deck(deck)
        new_id = getattr(out, "id", 0)
        if not new_id:
            try:
                new_id = col.decks.id_for_name(deck_name)
            except Exception:
                new_id = None
        return new_id
    except Exception:
        return _build_filtered_legacy(col, deck_name, search, limit)


class DueSiblingsDialog(QDialog):
    """Pick a deck + thresholds, see the live hit count, then browse or study."""

    def __init__(self, parent, get_localized_text_func):
        super().__init__(parent)
        self.t = get_localized_text_func
        self.current_cids = []
        cfg = get_due_siblings_config()

        self.setWindowTitle(self.t("ds_title"))
        self.setWindowFlags(self.windowFlags() | WINDOW_STAYS_ON_TOP)
        self.setStyleSheet(base_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel(self.t("ds_title"))
        title.setObjectName("aic_title")
        layout.addWidget(title)

        intro = QLabel(self.t("ds_intro"))
        intro.setObjectName("aic_subtitle")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Deck picker (editable + type-to-filter via the combo's own completer).
        deck_row = QHBoxLayout()
        deck_row.addWidget(QLabel(self.t("ds_deck_label")))
        self.deck_combo = QComboBox()
        self.deck_combo.setEditable(True)
        names = sorted(
            (d.name for d in mw.col.decks.all_names_and_ids()),
            key=lambda s: s.lower(),
        )
        self.deck_combo.addItems(names)
        self.deck_combo.setCurrentText(cfg["deck"])
        deck_row.addWidget(self.deck_combo, 1)
        layout.addLayout(deck_row)

        # The one visible switch = exclude_struggling (the heart of the request).
        self.exclude_check = QCheckBox(self.t("ds_exclude_struggling"))
        self.exclude_check.setChecked(bool(cfg["exclude_struggling"]))
        layout.addWidget(self.exclude_check)

        self.count_label = QLabel("")
        self.count_label.setObjectName("aic_region")
        layout.addWidget(self.count_label)

        # Collapsible "Advanced" with the numeric thresholds.
        self.advanced_button = make_action_button("▸ " + self.t("ds_advanced"))
        self.advanced_button.setCheckable(True)
        adv_row = QHBoxLayout()
        adv_row.addWidget(self.advanced_button)
        adv_row.addStretch(1)
        layout.addLayout(adv_row)

        self.advanced = QWidget()
        adv_layout = QVBoxLayout(self.advanced)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(6)

        ivl_row = QHBoxLayout()
        ivl_row.addWidget(QLabel(self.t("ds_min_ivl_label")))
        ivl_row.addStretch(1)
        self.min_ivl_spin = QSpinBox()
        self.min_ivl_spin.setRange(0, 100000)
        self.min_ivl_spin.setValue(int(cfg["min_ivl"]))
        ivl_row.addWidget(self.min_ivl_spin)
        adv_layout.addLayout(ivl_row)

        lap_row = QHBoxLayout()
        lap_row.addWidget(QLabel(self.t("ds_max_lapses_label")))
        lap_row.addStretch(1)
        self.max_lapses_spin = QSpinBox()
        self.max_lapses_spin.setRange(0, 100000)
        self.max_lapses_spin.setValue(int(cfg["max_lapses"]))
        lap_row.addWidget(self.max_lapses_spin)
        adv_layout.addLayout(lap_row)

        self.advanced.setVisible(False)
        layout.addWidget(self.advanced)

        # Actions.
        self.show_button = make_action_button(self.t("ds_show_browser"))
        self.start_button = make_primary_button(self.t("ds_start_filtered"))
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.show_button)
        btn_row.addWidget(self.start_button)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.resize(560, 360)

        self.advanced_button.toggled.connect(self._toggle_advanced)
        self.deck_combo.currentTextChanged.connect(lambda _=None: self._recompute())
        self.exclude_check.toggled.connect(lambda _=None: self._recompute())
        self.min_ivl_spin.valueChanged.connect(lambda _=None: self._recompute())
        self.max_lapses_spin.valueChanged.connect(lambda _=None: self._recompute())
        self.show_button.clicked.connect(self._on_show_browser)
        self.start_button.clicked.connect(self._on_start_filtered)
        # Persist the last-used values whenever the dialog closes (accept/reject/X).
        self.finished.connect(lambda _=None: save_due_siblings_config(self._params()))

        self._recompute()

    def _params(self):
        return {
            "deck": self.deck_combo.currentText().strip(),
            "min_ivl": self.min_ivl_spin.value(),
            "max_lapses": self.max_lapses_spin.value(),
            "exclude_struggling": self.exclude_check.isChecked(),
        }

    def _toggle_advanced(self, checked):
        self.advanced.setVisible(checked)
        arrow = "▾ " if checked else "▸ "
        self.advanced_button.setText(arrow + self.t("ds_advanced"))

    def _recompute(self):
        p = self._params()
        try:
            self.current_cids = compute_due_sibling_cids(
                mw.col, p["deck"], p["min_ivl"], p["max_lapses"],
                p["exclude_struggling"],
            )
        except Exception:
            self.current_cids = []
        count = len(self.current_cids)
        self.count_label.setText(self.t("ds_count", count=count))
        has = count > 0
        self.show_button.setEnabled(has)
        self.start_button.setEnabled(has)

    def _on_show_browser(self):
        if not self.current_cids:
            showInfo(self.t("ds_empty_info"))
            return
        open_in_browser(self.current_cids)
        self.accept()

    def _on_start_filtered(self):
        if not self.current_cids:
            showInfo(self.t("ds_empty_info"))
            return
        did = build_and_select_filtered_deck(
            self.current_cids, self.t("ds_filtered_deck_name")
        )
        if not did:
            showInfo(self.t("ds_filtered_failed"))
            return
        mw.col.decks.select(did)
        self.accept()
        mw.moveToState("overview")


def open_due_siblings_dialog():
    """Tools-menu entry point: open the due-siblings dialog."""
    DueSiblingsDialog(mw, get_localized_text).exec()
