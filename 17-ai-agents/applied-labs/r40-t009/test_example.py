#!/usr/bin/env python3
"""Regression, boundary, and evaluation experiment test suite for R40-T009.

Lesson 17: AI Agents
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    ALLOWED_TOOLS,
    DecisionMismatchError,
    DispatchMode,
    TypedToolDispatcher,
    run_canonical_check,
    run_cascade_prevention_scenario,
    run_evaluation_experiment,
    run_normal_scenario,
    run_string_type_scenario,
    run_unknown_tool_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestTypedToolDispatchContract(unittest.TestCase):
    """Core tool dispatch contracts: arithmetic, typing, and allowlist."""

    def setUp(self) -> None:
        self.dispatcher = TypedToolDispatcher()

    def test_add_two_and_three_equals_five(self) -> None:
        """add(2, 3) -> 5."""
        res = self.dispatcher.dispatch_single({"tool": "add", "a": 2, "b": 3})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 5)

    def test_multiply_two_and_three_equals_six(self) -> None:
        """multiply(2, 3) -> 6."""
        res = self.dispatcher.dispatch_single({"tool": "multiply", "a": 2, "b": 3})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 6)

    def test_unknown_tool_returns_structured_error(self) -> None:
        """Unknown tool returns structured error."""
        res = self.dispatcher.dispatch_single({"tool": "delete_all", "a": 1, "b": 2})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "UnknownToolError")
        self.assertIn("not in allowlist", res["message"])

    def test_string_argument_returns_structured_error(self) -> None:
        """String argument 'a' returns structured error."""
        res = self.dispatcher.dispatch_single({"tool": "add", "a": "two", "b": 3})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "TypeValidationError")
        self.assertEqual(res["field"], "a")

    def test_failed_call_cannot_execute_another_tool(self) -> None:
        """A failed call halts sequence execution and blocks subsequent calls."""
        calls = [
            {"tool": "add", "a": "invalid", "b": 3},  # Fails
            {"tool": "multiply", "a": 2, "b": 3},      # Must be blocked
        ]
        batch = self.dispatcher.dispatch_sequence(calls)
        self.assertTrue(batch["halted"])
        self.assertEqual(batch["executed_count"], 0)
        self.assertEqual(batch["results"][0]["status"], "error")
        self.assertEqual(batch["results"][1]["status"], "blocked")


class TestFocusControlledConfigurations(unittest.TestCase):
    """Focus: Compare three controlled configurations and report correctness & trade-offs."""

    def test_evaluation_experiment_all_modes_safe(self) -> None:
        """Verifies zero unauthorized executions across all 3 controlled modes."""
        exp = run_evaluation_experiment()
        self.assertTrue(exp["contract_satisfied"])
        configs = exp["configurations"]
        self.assertEqual(len(configs), 3)
        for mode, data in configs.items():
            self.assertEqual(data["unauthorized_executed"], 0)
            self.assertEqual(data["boundary_safety"], "100%")


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Canonical verification checks and deliberate tamper detection."""

    def test_canonical_check_passes(self) -> None:
        res = run_canonical_check(tamper=False)
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateWrongResult(unittest.TestCase):
    """Demonstrates that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI execution in fresh subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal(self) -> None:
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "TOOLS_DISPATCHED_SUCCESSFULLY")

    def test_cli_scenario_unknown(self) -> None:
        res = self._run_cli(["--scenario", "unknown"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "UNKNOWN_TOOL_REJECTED")

    def test_cli_scenario_string_type(self) -> None:
        res = self._run_cli(["--scenario", "string_type"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STRING_ARG_REJECTED")

    def test_cli_scenario_cascade(self) -> None:
        res = self._run_cli(["--scenario", "cascade"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "CASCADE_EXECUTION_BLOCKED")

    def test_cli_experiment(self) -> None:
        res = self._run_cli(["--experiment"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["contract_satisfied"])

    def test_cli_check(self) -> None:
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")


if __name__ == "__main__":
    unittest.main()
