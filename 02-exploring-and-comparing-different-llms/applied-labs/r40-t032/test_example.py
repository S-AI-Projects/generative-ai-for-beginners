"""
Unit tests for Token-Budget Preflight & Recovery (R40-T032).
"""

import unittest
import sys
from pathlib import Path

# Add directory to sys.path for direct or discover execution
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from example import TokenBudgetPreflight


class TestTokenBudgetPreflight(unittest.TestCase):
    def test_budget_three_truncation(self):
        """Budget 3 with 'one two three four' retains [one, two, three] and reports 1 removed."""
        preflight = TokenBudgetPreflight(budget=3)
        res = preflight.process("one two three four")
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["removed_count"], 1)
        self.assertTrue(res["is_truncated"])
        self.assertEqual(res["total_tokens"], 4)
        self.assertIn("Teaching approximation", res["tokenizer"])

    def test_empty_input_retains_none(self):
        """Empty input retains no tokens."""
        preflight = TokenBudgetPreflight(budget=5)
        res = preflight.process("")
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["is_truncated"])
        self.assertEqual(res["total_tokens"], 0)

    def test_reject_negative_budget(self):
        """Reject negative budget with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            TokenBudgetPreflight(budget=-1)
        self.assertIn("Negative or invalid budget rejected", str(ctx.exception))

    def test_exact_budget_boundary(self):
        """Exact budget boundary: total tokens == budget."""
        preflight = TokenBudgetPreflight(budget=3)
        res = preflight.process("alpha beta gamma")
        self.assertEqual(res["retained_tokens"], ["alpha", "beta", "gamma"])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["is_truncated"])

    def test_failure_and_recovery(self):
        """Exercise documented invalid/missing-data case, explain error, demonstrate recovery on valid input."""
        preflight = TokenBudgetPreflight(budget=4)

        # 1. Invalid input: None (missing data)
        with self.assertRaises(ValueError) as err_ctx:
            preflight.process(None)
        self.assertIn("Invalid/missing data: prompt cannot be None", str(err_ctx.exception))
        self.assertIsNotNone(preflight.last_error)

        # 2. Recovery on next valid input
        valid_res = preflight.process("recovery prompt input")
        self.assertEqual(valid_res["status"], "SUCCESS")
        self.assertEqual(valid_res["retained_tokens"], ["recovery", "prompt", "input"])
        self.assertTrue(valid_res["recovered_from_previous_error"])
        self.assertIsNone(preflight.last_error)

    def test_deliberate_wrong_assertion_fails(self):
        """Verifies that asserting incorrect retained tokens fails."""
        preflight = TokenBudgetPreflight(budget=2)
        res = preflight.process("word1 word2 word3")
        with self.assertRaises(AssertionError):
            self.assertEqual(res["retained_tokens"], ["word1", "word2", "word3"])


if __name__ == "__main__":
    unittest.main()
