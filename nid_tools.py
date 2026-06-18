# -*- coding: utf-8 -*-
"""Pure, Anki-independent helpers for parsing and formatting note IDs.

Kept free of any aqt/PyQt imports so the logic can be unit-tested without a
running Anki instance.
"""
import re

# Numbers attached to a `nid:` token, including the compact "nid:1,2,3" form.
_NID_PREFIX_RE = re.compile(r"(?i)nid:\s*(\d+(?:\s*,\s*\d+)*)")
# A line that consists solely of a number (used only when no `nid:` is present).
_BARE_LINE_RE = re.compile(r"^\s*(\d+)\s*$", re.MULTILINE)
_DIGITS_RE = re.compile(r"\d+")


def parse_nids_from_text(text):
    """Extract note IDs from free-form text, returning a ``set`` of ``int``.

    If the text contains any ``nid:`` token, only numbers attached to such
    tokens are used (supports both ``nid:1 OR nid:2`` and the compact
    ``nid:1,2,3`` form). Otherwise every line that is *only* a number is taken
    as a note ID. Bare numbers embedded in prose (dates, page numbers, decimals)
    are ignored, so pasted free text cannot inject phantom IDs.
    """
    nids = set()
    if not text:
        return nids

    if "nid:" in text.lower():
        for match in _NID_PREFIX_RE.finditer(text):
            for num in _DIGITS_RE.findall(match.group(1)):
                nids.add(int(num))
    else:
        for match in _BARE_LINE_RE.finditer(text):
            nids.add(int(match.group(1)))

    return nids


def build_search_string(nids, compact=False):
    """Build an Anki browser search string from an iterable of note IDs.

    ``compact=True`` yields the shorter ``nid:1,2,3`` form; the default yields
    the explicit ``nid:1 OR nid:2`` form. Returns ``""`` for an empty input.
    """
    parts = [str(n) for n in nids]
    if not parts:
        return ""
    if compact:
        return "nid:" + ",".join(parts)
    return " OR ".join("nid:" + p for p in parts)
