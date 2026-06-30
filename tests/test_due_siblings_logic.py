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


if __name__ == "__main__":
    unittest.main()
