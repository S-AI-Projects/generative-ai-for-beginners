"""
Unit tests for Open Source Models Assessment (R40-T040).
"""

import unittest
import sys
from pathlib import Path

# Add directory to sys.path for direct or discover execution
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from example import (
    DECISION_TABLE,
    APPLIED_QUESTIONS,
    evaluate_model_selection,
    check_decision_table,
    check_applied_question,
)


class TestOpenSourceModelDecisions(unittest.TestCase):
    def test_normal_scenario(self):
        """Test normal scenario: strict open source requirements with full open assets."""
        scenario = DECISION_TABLE[0]
        res = evaluate_model_selection(scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["model_category"], scenario["model_category"])

    def test_boundary_scenario(self):
        """Test boundary scenario: open weights with private training dataset."""
        scenario = DECISION_TABLE[1]
        res = evaluate_model_selection(scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["model_category"], scenario["model_category"])

    def test_missing_info_scenario(self):
        """Test missing-information scenario: None weight availability."""
        scenario = DECISION_TABLE[2]
        res = evaluate_model_selection(scenario["input"])
        self.assertEqual(res["decision"], scenario["expected_decision"])
        self.assertEqual(res["model_category"], scenario["model_category"])

    def test_decision_table_passes(self):
        """Published decision table check passes without error."""
        passed, errors = check_decision_table(DECISION_TABLE)
        self.assertTrue(passed, f"Errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_deliberate_tampered_decision_fails(self):
        """Altering a decision in the published table fails the checker."""
        tampered_table = [dict(item) for item in DECISION_TABLE]
        tampered_table[0]["expected_decision"] = "WRONG_DECISION"
        passed, errors = check_decision_table(tampered_table)
        self.assertFalse(passed)
        self.assertTrue(any("WRONG_DECISION" in e for e in errors))

    def test_applied_question_1_predict_output(self):
        """Applied question 1: predict output for open weights scenario."""
        q = APPLIED_QUESTIONS[0]
        valid, rationale = check_applied_question("q1_predict_output", q["expected_answer"])
        self.assertTrue(valid)
        self.assertIn("Lesson 16", rationale)

    def test_applied_question_2_diagnose_failure(self):
        """Applied question 2: diagnose missing weights evaluation failure."""
        q = APPLIED_QUESTIONS[1]
        valid, rationale = check_applied_question("q2_diagnose_failure", q["expected_answer"])
        self.assertTrue(valid)
        self.assertIn("weight availability status", rationale)

    def test_applied_question_3_choose_boundary_policy(self):
        """Applied question 3: choose boundary policy for full OSI compliance."""
        q = APPLIED_QUESTIONS[2]
        valid, rationale = check_applied_question("q3_choose_boundary_policy", q["expected_answer"])
        self.assertTrue(valid)
        self.assertIn("OLMo", rationale)

    def test_applied_question_wrong_answer_fails(self):
        """Executable check must fail when candidate answer is incorrect."""
        valid, msg = check_applied_question("q1_predict_output", "INCORRECT_PREDICTION")
        self.assertFalse(valid)
        self.assertIn("Incorrect answer", msg)


if __name__ == "__main__":
    unittest.main()
