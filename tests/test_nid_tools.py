# -*- coding: utf-8 -*-
"""Tests for the pure NID parsing/formatting helpers (no Anki/Qt required)."""
import os
import sys
import unittest

# Make the repo root importable so `nid_tools` resolves when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nid_tools import parse_nids_from_text, build_search_string, compute_diff


class TestParseNids(unittest.TestCase):
    def test_or_form(self):
        self.assertEqual(parse_nids_from_text("nid:123 OR nid:456"), {123, 456})

    def test_compact_comma_form(self):
        self.assertEqual(parse_nids_from_text("nid:1,2,3"), {1, 2, 3})

    def test_compact_comma_form_with_spaces(self):
        self.assertEqual(parse_nids_from_text("nid: 10 , 20 ,30"), {10, 20, 30})

    def test_nid_with_trailing_letters_keeps_digits(self):
        # Regression: old regex dropped the whole token because of a trailing \b.
        self.assertEqual(parse_nids_from_text("nid:123abc"), {123})

    def test_bare_numbers_one_per_line(self):
        self.assertEqual(parse_nids_from_text("123\n456\n789"), {123, 456, 789})

    def test_prose_numbers_ignored_without_nid_prefix(self):
        # Regression: "3.14" / inline numbers must NOT become phantom NIDs.
        self.assertEqual(parse_nids_from_text("Seite 3.14 von 2023 gelesen"), set())

    def test_nid_prefix_suppresses_stray_numbers(self):
        self.assertEqual(parse_nids_from_text("nid:111 (siehe Seite 42)"), {111})

    def test_case_insensitive_prefix(self):
        self.assertEqual(parse_nids_from_text("NID:5 or Nid:6"), {5, 6})

    def test_real_world_large_ids(self):
        self.assertEqual(
            parse_nids_from_text("nid:1568383637297,1568384125335"),
            {1568383637297, 1568384125335},
        )

    def test_empty_and_blank(self):
        self.assertEqual(parse_nids_from_text(""), set())
        self.assertEqual(parse_nids_from_text("   \n  \t "), set())

    def test_duplicates_collapse(self):
        self.assertEqual(parse_nids_from_text("nid:7 OR nid:7 OR nid:7"), {7})


class TestBuildSearchString(unittest.TestCase):
    def test_or_form_default(self):
        self.assertEqual(build_search_string([123, 456]), "nid:123 OR nid:456")

    def test_compact_form(self):
        self.assertEqual(build_search_string([1, 2, 3], compact=True), "nid:1,2,3")

    def test_empty_is_empty_string(self):
        self.assertEqual(build_search_string([]), "")


class TestComputeDiff(unittest.TestCase):
    def test_basic_regions(self):
        d = compute_diff({1, 2, 3}, {2, 3, 4})
        self.assertEqual(d["missing"], {4})   # friend has, you don't
        self.assertEqual(d["extra"], {1})     # you have, friend doesn't
        self.assertEqual(d["shared"], {2, 3})

    def test_disjoint(self):
        d = compute_diff({1}, {2})
        self.assertEqual(d["missing"], {2})
        self.assertEqual(d["extra"], {1})
        self.assertEqual(d["shared"], set())

    def test_identical(self):
        d = compute_diff({1, 2}, {1, 2})
        self.assertEqual(d["missing"], set())
        self.assertEqual(d["extra"], set())
        self.assertEqual(d["shared"], {1, 2})

    def test_empty_your_side(self):
        d = compute_diff(set(), {1, 2})
        self.assertEqual(d["missing"], {1, 2})
        self.assertEqual(d["extra"], set())
        self.assertEqual(d["shared"], set())

    def test_accepts_lists(self):
        d = compute_diff([1, 1, 2], [2, 2, 3])
        self.assertEqual(d["missing"], {3})
        self.assertEqual(d["extra"], {1})
        self.assertEqual(d["shared"], {2})


if __name__ == "__main__":
    unittest.main(verbosity=2)
