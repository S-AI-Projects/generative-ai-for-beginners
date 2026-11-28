#!/usr/bin/env python3
"""Tests for the r40-t053 whitespace-token budget example.

These tests exercise the stated contract:
  - normal scenario: budget 3 on "one two three four" retains
    [one, two, three] and reports one removed token
  - boundary scenarios: empty input, budget == token count, budget >
    token count, budget == 0
  - failure scenario: a negative budget is rejected
  - comparison focus: the direct implementation (tokenize_whitespace) is
    cross-checked against a simpler, independent calculation
    (count_tokens_naive) and against an explicit expected-result table, on
    identical inputs
  - a deliberately wrong result is rejected by assertion

Run from the repository root:
    python3 -m unittest discover -s 19-slm/applied-labs/r40-t053 -p "test_*.py"
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from example import (  # noqa: E402
    apply_token_budget,
    count_tokens_naive,
    tokenize_whitespace,
)

# Explicit expected-result table: (text, budget) -> (retained tokens,
# removed_count). Independent of the implementation -- these values are the
# fixture's stated contract, not a recomputation of it.
EXPECTED_RESULTS = {
    ("one two three four", 3): (("one", "two", "three"), 1),
    ("", 5): ((), 0),
    ("one two", 0): ((), 2),
    ("one two three", 3): (("one", "two", "three"), 0),
    ("one two", 10): (("one", "two"), 0),
}


class NormalScenario(unittest.TestCase):
    """Budget 3 on 'one two three four' retains [one, two, three], removed=1."""

    def test_headline_fixture_matches_expected_table(self):
        result = apply_token_budget("one two three four", 3)
        expected_retained, expected_removed = EXPECTED_RESULTS[("one two three four", 3)]
        self.assertEqual(result.retained, expected_retained)
        self.assertEqual(result.removed_count, expected_removed)
        self.assertTrue(result.truncated)

    def test_wrong_retained_order_is_not_silently_accepted(self):
        # A deliberately wrong expectation (reversed order) must fail.
        result = apply_token_budget("one two three four", 3)
        wrong_expected = ("three", "two", "one")
        self.assertNotEqual(result.retained, wrong_expected)
        self.assertEqual(result.retained, ("one", "two", "three"))


class ExpectedResultTableScenario(unittest.TestCase):
    """Every row of the explicit expected-result table, by identical input."""

    def test_table_rows_match_direct_implementation(self):
        for (text, budget), (expected_retained, expected_removed) in EXPECTED_RESULTS.items():
            with self.subTest(text=text, budget=budget):
                result = apply_token_budget(text, budget)
                self.assertEqual(result.retained, expected_retained)
                self.assertEqual(result.removed_count, expected_removed)


class IndependentCalculationScenario(unittest.TestCase):
    """Cross-check the direct implementation against a simpler, independent one."""

    SAMPLE_TEXTS = [
        "one two three four",
        "",
        "single",
        "  leading and trailing  ",
        "tabs\tand\nnewlines\tcount too",
        "one  two   three",
    ]

    def test_direct_and_naive_counts_agree_on_identical_inputs(self):
        for text in self.SAMPLE_TEXTS:
            with self.subTest(text=text):
                direct_count = len(tokenize_whitespace(text))
                naive_count = count_tokens_naive(text)
                self.assertEqual(
                    direct_count,
                    naive_count,
                    f"tokenize_whitespace and count_tokens_naive disagree on {text!r}",
                )

    def test_naive_count_catches_a_deliberately_wrong_tokenizer(self):
        # A deliberately wrong "tokenizer" that always reports zero tokens
        # must be caught by comparing against the independent calculation.
        text = "one two three four"
        wrong_token_count = 0
        self.assertNotEqual(wrong_token_count, count_tokens_naive(text))
        self.assertEqual(count_tokens_naive(text), len(tokenize_whitespace(text)))


class BoundaryScenario(unittest.TestCase):
    """Empty input, budget == token count, budget > token count, budget == 0."""

    def test_empty_input_retains_none(self):
        result = apply_token_budget("", 5)
        self.assertEqual(result.retained, ())
        self.assertEqual(result.removed_count, 0)
        self.assertFalse(result.truncated)

    def test_budget_equal_to_token_count_no_truncation(self):
        result = apply_token_budget("one two three", 3)
        self.assertEqual(result.retained, ("one", "two", "three"))
        self.assertEqual(result.removed_count, 0)
        self.assertFalse(result.truncated)

    def test_budget_greater_than_token_count_no_truncation(self):
        result = apply_token_budget("one two", 10)
        self.assertEqual(result.retained, ("one", "two"))
        self.assertEqual(result.removed_count, 0)
        self.assertFalse(result.truncated)

    def test_budget_zero_retains_nothing(self):
        result = apply_token_budget("one two", 0)
        self.assertEqual(result.retained, ())
        self.assertEqual(result.removed_count, 2)
        self.assertTrue(result.truncated)


class FailureScenario(unittest.TestCase):
    """A negative budget is rejected."""

    def test_negative_budget_raises(self):
        with self.assertRaises(ValueError):
            apply_token_budget("one two", -1)

    def test_negative_budget_on_empty_text_still_raises(self):
        with self.assertRaises(ValueError):
            apply_token_budget("", -1)


if __name__ == "__main__":
    unittest.main()
