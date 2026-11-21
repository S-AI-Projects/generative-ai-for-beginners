"""
Unit tests for Low-Code AI Workflow Step Trace and Invariants (R40-T034).
"""

import unittest
import sys
from pathlib import Path

# Add directory to sys.path for direct or discover execution
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from example import (
    DECISION_TABLE,
    LowCodeWorkflowEngine,
    verify_pipeline_invariant,
    check_decision_table,
)


class TestLowCodeWorkflow(unittest.TestCase):
    def setUp(self):
        self.engine = LowCodeWorkflowEngine()

    def test_normal_scenario(self):
        """Test normal scenario: critical outage routed to emergency oncall."""
        scenario = DECISION_TABLE[0]
        out = self.engine.execute_pipeline(scenario["input"])
        self.assertEqual(out["decision"], scenario["expected_decision"])
        self.assertEqual(out["routing"], scenario["expected_routing"])
        valid, violations = verify_pipeline_invariant(out["intermediate_states"], out)
        self.assertTrue(valid, f"Violations: {violations}")

    def test_boundary_scenario(self):
        """Test boundary scenario: low urgency monitored service routed to standard queue."""
        scenario = DECISION_TABLE[1]
        out = self.engine.execute_pipeline(scenario["input"])
        self.assertEqual(out["decision"], scenario["expected_decision"])
        self.assertEqual(out["routing"], scenario["expected_routing"])
        valid, violations = verify_pipeline_invariant(out["intermediate_states"], out)
        self.assertTrue(valid, f"Violations: {violations}")

    def test_missing_info_scenario(self):
        """Test missing-info scenario: missing department triggers clarification prompt."""
        scenario = DECISION_TABLE[2]
        out = self.engine.execute_pipeline(scenario["input"])
        self.assertEqual(out["decision"], scenario["expected_decision"])
        self.assertEqual(out["routing"], scenario["expected_routing"])
        valid, violations = verify_pipeline_invariant(out["intermediate_states"], out)
        self.assertTrue(valid, f"Violations: {violations}")

    def test_decision_table_validation(self):
        """Published decision table must validate with zero errors."""
        passed, errors = check_decision_table(DECISION_TABLE)
        self.assertTrue(passed, f"Check failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_deliberate_wrong_decision_fails(self):
        """Checker must fail when a decision is deliberately tampered."""
        tampered_table = [dict(item) for item in DECISION_TABLE]
        tampered_table[0]["expected_decision"] = "DELIBERATELY_TAMPERED"
        passed, errors = check_decision_table(tampered_table)
        self.assertFalse(passed)
        self.assertTrue(any("DELIBERATELY_TAMPERED" in err for err in errors))

    def test_broken_intermediate_state_invariant_fails(self):
        """Tampering with an intermediate state must be caught by invariant verification."""
        out = self.engine.execute_pipeline(DECISION_TABLE[0]["input"])
        corrupted_states = [dict(s) for s in out["intermediate_states"]]
        # Corrupt step 3 decision to mismatch final output
        corrupted_states[2]["decision"] = "MISMATCHED_STEP_DECISION"
        valid, violations = verify_pipeline_invariant(corrupted_states, out)
        self.assertFalse(valid)
        self.assertTrue(any("does not match step 3 gate decision" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
