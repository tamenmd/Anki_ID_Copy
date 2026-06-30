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
