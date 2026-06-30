# -*- coding: utf-8 -*-
"""Tests for the pure due-siblings query/logic helpers (no Anki/Qt required)."""
import os
import sys
import unittest

# Make the repo root importable so `due_siblings_logic` resolves when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from due_siblings_logic import (
    build_qualifier_query,
    build_struggling_query,
    build_target_cards_query,
    build_cid_query,
    merge_config,
)


class TestQueryBuilders(unittest.TestCase):
    def test_qualifier_query_with_deck(self):
        self.assertEqual(
            build_qualifier_query("8. Semester", 21, 1),
            'deck:"8. Semester" is:review prop:ivl>=21 prop:lapses<=1 -tag:leech',
        )

    def test_qualifier_query_without_deck(self):
        self.assertEqual(
            build_qualifier_query("", 21, 1),
            "is:review prop:ivl>=21 prop:lapses<=1 -tag:leech",
        )

    def test_struggling_query(self):
        self.assertEqual(
            build_struggling_query("8. Semester", 1),
            'deck:"8. Semester" (is:learn OR tag:leech OR prop:lapses>1)',
        )

    def test_target_cards_query(self):
        self.assertEqual(
            build_target_cards_query("8. Semester", [3, 1, 2]),
            'deck:"8. Semester" is:new (nid:3,1,2)',
        )

    def test_target_cards_query_empty_notes(self):
        self.assertEqual(build_target_cards_query("8. Semester", []), "")

    def test_cid_query(self):
        self.assertEqual(build_cid_query([10, 20, 30]), "cid:10,20,30")

    def test_cid_query_empty(self):
        self.assertEqual(build_cid_query([]), "")


class TestMergeConfig(unittest.TestCase):
    def test_defaults_when_user_empty(self):
        defaults = {"a": 1, "b": True}
        self.assertEqual(merge_config(defaults, {}), {"a": 1, "b": True})

    def test_user_overrides(self):
        defaults = {"a": 1, "b": True}
        self.assertEqual(merge_config(defaults, {"a": 5}), {"a": 5, "b": True})

    def test_ignores_none_and_unknown_keys(self):
        defaults = {"a": 1, "b": True}
        self.assertEqual(merge_config(defaults, {"a": None, "c": 9}), {"a": 1, "b": True})


from due_siblings_logic import compute_due_sibling_cids  # noqa: E402


class FakeCol:
    """Minimal stand-in: returns canned ids per exact query string."""

    def __init__(self, notes_by_query, cards_by_query):
        self.notes_by_query = notes_by_query
        self.cards_by_query = cards_by_query
        self.seen = []

    def find_notes(self, query):
        self.seen.append(query)
        return list(self.notes_by_query.get(query, []))

    def find_cards(self, query):
        self.seen.append(query)
        return list(self.cards_by_query.get(query, []))


class TestComputeDueSiblingCids(unittest.TestCase):
    def setUp(self):
        self.deck = "8. Semester"
        self.qual_q = build_qualifier_query(self.deck, 21, 1)
        self.prob_q = build_struggling_query(self.deck, 1)

    def test_exclude_struggling_subtracts_problem_notes(self):
        # qualifier notes {1,2,3}; struggling notes {2}; target -> notes {1,3}
        target_q = build_target_cards_query(self.deck, [1, 3])
        col = FakeCol(
            notes_by_query={self.qual_q: [1, 2, 3], self.prob_q: [2]},
            cards_by_query={target_q: [10, 30]},
        )
        self.assertEqual(
            compute_due_sibling_cids(col, self.deck, 21, 1, True), [10, 30]
        )

    def test_without_exclude_uses_all_qualifier_notes(self):
        target_q = build_target_cards_query(self.deck, [1, 2, 3])
        col = FakeCol(
            notes_by_query={self.qual_q: [1, 2, 3], self.prob_q: [2]},
            cards_by_query={target_q: [10, 20, 30]},
        )
        self.assertEqual(
            compute_due_sibling_cids(col, self.deck, 21, 1, False), [10, 20, 30]
        )
        self.assertNotIn(self.prob_q, col.seen)  # struggling query must NOT run

    def test_no_qualifier_notes_returns_empty(self):
        col = FakeCol(notes_by_query={self.qual_q: []}, cards_by_query={})
        self.assertEqual(compute_due_sibling_cids(col, self.deck, 21, 1, True), [])
        self.assertNotIn(self.prob_q, col.seen)  # short-circuit before struggling


if __name__ == "__main__":
    unittest.main()
