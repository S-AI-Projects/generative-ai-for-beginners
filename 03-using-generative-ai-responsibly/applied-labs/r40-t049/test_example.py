"""
R40-T049 · Test suite for example.py
======================================

Covers:
  1. Normal scenario:
     Allowed 'read' with a valid path passes and executes via StubExecutor.
  2. Failure scenario A:
     Unknown 'delete' tool is rejected and NEVER reaches StubExecutor.
  3. Failure scenario B:
     Missing required argument is rejected and NEVER reaches StubExecutor.
  4. Boundary scenarios:
     Empty path, invalid argument type, empty allowed-tools set.
  5. Security invariant:
     Rejected actions NEVER reach the stub executor (zero leakage).
  6. Focus comparison:
     Compare 3 controlled configurations (Strict, Standard, Extended)
     reporting interception rate and observed functional trade-offs.
  7. Deliberate wrong result verification:
     Assert deliberate wrong outcomes fail with AssertionError.
"""

import unittest

from example import (
    CONFIG_EXTENDED_ASSISTANT,
    CONFIG_STANDARD_INSPECTION,
    CONFIG_STRICT_READ,
    REASON_EMPTY_ARGUMENT,
    REASON_INVALID_ARGUMENT_TYPE,
    REASON_MISSING_ARGUMENT,
    REASON_UNKNOWN_TOOL,
    Action,
    ActionPolicyValidator,
    StubExecutor,
    ToolSchema,
    compare_policy_configurations,
)


class TestResponsiblePolicyContract(unittest.TestCase):
    """
    Contract requirements:
      - Allowed read with a valid path passes.
      - Unknown delete tool is rejected.
      - Missing required argument is rejected.
      - Rejected actions NEVER reach the stub executor.
    """

    def setUp(self):
        self.validator = ActionPolicyValidator(CONFIG_STRICT_READ)
        self.executor = StubExecutor()

    def test_allowed_read_with_valid_path_passes(self):
        action = Action(tool="read", args={"path": "/safe/data.txt"})
        result = self.validator.evaluate_and_execute(action, self.executor)

        self.assertTrue(result.executed)
        self.assertIsNone(result.refusal)
        self.assertIn("Mock content from /safe/data.txt", result.output)
        self.assertEqual(len(self.executor.executed_actions), 1)
        self.assertEqual(self.executor.executed_actions[0], action)

    def test_unknown_delete_tool_is_rejected(self):
        action = Action(tool="delete", args={"path": "/safe/data.txt"})
        result = self.validator.evaluate_and_execute(action, self.executor)

        self.assertFalse(result.executed)
        self.assertIsNotNone(result.refusal)
        self.assertEqual(result.refusal.reason, REASON_UNKNOWN_TOOL)
        self.assertIn("not in the allowed tool set", result.refusal.message)

        # CRITICAL SAFETY INVARIANT: never reached stub executor
        self.assertEqual(len(self.executor.executed_actions), 0)
        self.assertNotIn(action, self.executor.executed_actions)

    def test_missing_required_argument_is_rejected(self):
        action = Action(tool="read", args={})
        result = self.validator.evaluate_and_execute(action, self.executor)

        self.assertFalse(result.executed)
        self.assertIsNotNone(result.refusal)
        self.assertEqual(result.refusal.reason, REASON_MISSING_ARGUMENT)
        self.assertEqual(result.refusal.offending_arg, "path")

        # CRITICAL SAFETY INVARIANT: never reached stub executor
        self.assertEqual(len(self.executor.executed_actions), 0)
        self.assertNotIn(action, self.executor.executed_actions)

    def test_deliberate_wrong_execution_status_fails(self):
        """Deliberately assert that unknown tool was executed."""
        action = Action(tool="delete", args={"path": "/safe/data.txt"})
        result = self.validator.evaluate_and_execute(action, self.executor)
        with self.assertRaises(AssertionError):
            self.assertTrue(result.executed, "Intentional failure: delete must NOT be executed.")

    def test_deliberate_wrong_refusal_reason_fails(self):
        """Deliberately assert wrong refusal reason."""
        action = Action(tool="read", args={})
        result = self.validator.evaluate_and_execute(action, self.executor)
        with self.assertRaises(AssertionError):
            self.assertEqual(result.refusal.reason, REASON_UNKNOWN_TOOL,
                             "Intentional failure: missing arg is not unknown tool.")


class TestBoundaryScenarios(unittest.TestCase):
    """Boundary conditions: empty strings, incorrect types, empty toolset."""

    def setUp(self):
        self.validator = ActionPolicyValidator(CONFIG_STRICT_READ)
        self.executor = StubExecutor()

    def test_empty_string_path_rejected(self):
        action = Action(tool="read", args={"path": "   "})
        result = self.validator.evaluate_and_execute(action, self.executor)
        self.assertFalse(result.executed)
        self.assertEqual(result.refusal.reason, REASON_EMPTY_ARGUMENT)
        self.assertEqual(len(self.executor.executed_actions), 0)

    def test_invalid_argument_type_rejected(self):
        action = Action(tool="read", args={"path": 9999})
        result = self.validator.evaluate_and_execute(action, self.executor)
        self.assertFalse(result.executed)
        self.assertEqual(result.refusal.reason, REASON_INVALID_ARGUMENT_TYPE)
        self.assertEqual(len(self.executor.executed_actions), 0)

    def test_empty_allowed_toolset_rejects_all(self):
        empty_validator = ActionPolicyValidator({})
        action = Action(tool="read", args={"path": "/safe/data.txt"})
        result = empty_validator.evaluate_and_execute(action, self.executor)
        self.assertFalse(result.executed)
        self.assertEqual(result.refusal.reason, REASON_UNKNOWN_TOOL)
        self.assertEqual(len(self.executor.executed_actions), 0)


class TestControlledConfigurationsComparison(unittest.TestCase):
    """
    Focus requirement:
      Compare three small controlled configurations using a metric appropriate
      to this contract. Report correctness and the observed trade-off.
    """

    def setUp(self):
        self.workload = [
            Action(tool="read", args={"path": "/data/report.txt"}),       # Valid read
            Action(tool="delete", args={"path": "/data/report.txt"}),     # Blocked in all
            Action(tool="search", args={"query": "responsible AI"}),      # Allowed in B & C
            Action(tool="summarize", args={"text": "Long document..."}),   # Allowed in C
            Action(tool="read", args={}),                                 # Malformed in all
        ]

    def test_three_configurations_comparison(self):
        metrics = compare_policy_configurations(self.workload)

        config_a = metrics["Config_A_StrictRead"]
        config_b = metrics["Config_B_StandardInspection"]
        config_c = metrics["Config_C_ExtendedAssistant"]

        # Metric 1: Zero leakage across all configurations
        self.assertEqual(config_a.executor_leakage_count, 0)
        self.assertEqual(config_b.executor_leakage_count, 0)
        self.assertEqual(config_c.executor_leakage_count, 0)

        # Metric 2: Observed Trade-off in Interception Rate
        # Config A intercepts 4/5 (only read passes) -> 80%
        self.assertEqual(config_a.executed_count, 1)
        self.assertEqual(config_a.rejected_count, 4)
        self.assertAlmostEqual(config_a.interception_rate, 0.8)

        # Config B intercepts 3/5 (read and search pass) -> 60%
        self.assertEqual(config_b.executed_count, 2)
        self.assertEqual(config_b.rejected_count, 3)
        self.assertAlmostEqual(config_b.interception_rate, 0.6)

        # Config C intercepts 2/5 (read, search, summarize pass) -> 40%
        self.assertEqual(config_c.executed_count, 3)
        self.assertEqual(config_c.rejected_count, 2)
        self.assertAlmostEqual(config_c.interception_rate, 0.4)

    def test_deliberate_leakage_assertion_fails(self):
        """Deliberately assert non-zero leakage to verify checker."""
        metrics = compare_policy_configurations(self.workload)
        with self.assertRaises(AssertionError):
            self.assertEqual(metrics["Config_A_StrictRead"].executor_leakage_count, 1,
                             "Deliberate wrong assertion: leakage should strictly be 0.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
