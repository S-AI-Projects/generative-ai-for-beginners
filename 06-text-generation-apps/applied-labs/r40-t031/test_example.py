"""
Unit tests for Text Generation Application Decision Preflight & Evaluator (R40-T031).
"""

import unittest
import sys
from pathlib import Path

# Support running directly or via discover
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from example import (
    DECISION_TABLE,
    evaluate_generation_request,
    check_decision_table,
    approximate_token_count,
)


class TestTextGenerationDecisions(unittest.TestCase):
    def test_normal_scenario(self):
        """Test normal scenario: valid prompt, factual summarization, ample budget."""
        scenario = DECISION_TABLE[0]
        res = evaluate_generation_request(**scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["status"], scenario["expected_status"])
        self.assertEqual(res["parameters"]["temperature"], 0.2)
        self.assertLessEqual(res["parameters"]["max_tokens"], 150)

    def test_boundary_scenario(self):
        """Test boundary scenario: creative prompt with tight budget near lower floor."""
        scenario = DECISION_TABLE[1]
        res = evaluate_generation_request(**scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["status"], scenario["expected_status"])
        self.assertEqual(res["parameters"]["temperature"], 0.8)
        self.assertLessEqual(res["parameters"]["max_tokens"], scenario["input"]["available_budget"])

    def test_missing_info_scenario(self):
        """Test missing-information scenario: empty/whitespace prompt."""
        scenario = DECISION_TABLE[2]
        res = evaluate_generation_request(**scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["status"], scenario["expected_status"])
        self.assertEqual(res["parameters"]["max_tokens"], 0)

    def test_check_decision_table_passes(self):
        """Published decision table must validate successfully."""
        passed, errors = check_decision_table(DECISION_TABLE)
        self.assertTrue(passed, f"Decision table check failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_deliberate_wrong_decision_fails_checker(self):
        """Checker must fail when an expected decision in the table is deliberately altered."""
        tampered_table = [dict(item) for item in DECISION_TABLE]
        tampered_table[0]["expected_decision"] = "DELIBERATE_WRONG_DECISION"
        passed, errors = check_decision_table(tampered_table)
        self.assertFalse(passed)
        self.assertTrue(any("DELIBERATE_WRONG_DECISION" in err for err in errors))

    def test_invalid_budget_negative(self):
        """Negative budget must be rejected with invalid budget status."""
        res = evaluate_generation_request("Some prompt", "creative", -10)
        self.assertEqual(res["decision"], "REJECT_INVALID_BUDGET")
        self.assertEqual(res["status"], "ERROR_INVALID_BUDGET")

    def test_prompt_exceeding_budget(self):
        """Prompt longer than total budget must be rejected."""
        res = evaluate_generation_request("A prompt with five words total", "factual", 3)
        self.assertEqual(res["decision"], "REJECT_BUDGET_EXCEEDED")
        self.assertEqual(res["status"], "ERROR_BUDGET_EXCEEDED")

    def test_approximate_token_count(self):
        """Token count helper test."""
        self.assertEqual(approximate_token_count(""), 0)
        self.assertEqual(approximate_token_count("   "), 0)
        self.assertEqual(approximate_token_count("one two three"), 3)


if __name__ == "__main__":
    unittest.main()
