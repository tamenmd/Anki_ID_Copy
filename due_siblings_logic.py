# -*- coding: utf-8 -*-
"""Pure, Anki-independent helpers for the "due siblings" feature.

Builds the Anki browser search strings from plain parameters so the query
logic can be unit-tested without a running Anki instance. No aqt/anki imports.
"""


def _deck_clause(deck):
    """Return a quoted ``deck:`` clause (so names with spaces work), or ""."""
    deck = (deck or "").strip()
    if not deck:
        return ""
    return 'deck:"%s"' % deck.replace('"', "")


def _join(parts):
    return " ".join(p for p in parts if p)


def build_qualifier_query(deck, min_ivl, max_lapses):
    """Notes that have a stable, mature 'green' sibling in the deck."""
    return _join([
        _deck_clause(deck),
        "is:review",
        "prop:ivl>=%d" % int(min_ivl),
        "prop:lapses<=%d" % int(max_lapses),
        "-tag:leech",
    ])


def build_struggling_query(deck, max_lapses):
    """Notes that currently have a 'struggling' sibling in the deck."""
    return _join([
        _deck_clause(deck),
        "(is:learn OR tag:leech OR prop:lapses>%d)" % int(max_lapses),
    ])


def build_target_cards_query(deck, note_ids):
    """The NEW (blue) cards of the given notes within the deck.

    Returns "" when ``note_ids`` is empty (no cards can match)."""
    ids = [int(n) for n in note_ids]
    if not ids:
        return ""
    return _join([
        _deck_clause(deck),
        "is:new",
        "(nid:%s)" % ",".join(str(n) for n in ids),
    ])


def build_cid_query(card_ids):
    """Compact ``cid:1,2,3`` query; "" when empty."""
    ids = [int(c) for c in card_ids]
    if not ids:
        return ""
    return "cid:" + ",".join(str(c) for c in ids)


def merge_config(defaults, user):
    """Shallow-merge ``user`` over ``defaults``, ignoring None/unknown keys."""
    merged = dict(defaults)
    if user:
        for key, value in user.items():
            if key in defaults and value is not None:
                merged[key] = value
    return merged
