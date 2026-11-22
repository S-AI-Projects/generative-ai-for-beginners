#!/usr/bin/env python3
"""Regression and invariant test suite for R40-T003.

Lesson 10: Building Low Code AI Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    DECISION_DEFER,
    DECISION_LOW_CODE,
    DECISION_PRO_CODE,
    SCENARIOS_DATA,
    DecisionMismatchError,
    evaluate_decision_direct,
    evaluate_decision_reference,
    run_canonical_check,
    run_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestLowCodeDecisionScenarios(unittest.TestCase):
    """Validates the three scenarios: normal, boundary, and missing information."""

    def test_normal_scenario_decision_and_rationale(self) -> None:
        """Normal scenario selects LOW_CODE_POWER_PLATFORM with valid rationale."""
        res = run_scenario("SCENARIO_NORMAL")
        self.assertEqual(res["decision"], DECISION_LOW_CODE)
        self.assertEqual(res["type"], "normal")
        self.assertIn("Power Automate", res["rationale"])
        self.assertIn("AI Builder", res["rationale"])
        self.assertTrue(res["contract_satisfied"])

    def test_boundary_scenario_decision_and_rationale(self) -> None:
        """Boundary scenario selects CUSTOM_CODE_PRO_DEV with valid rationale."""
        res = run_scenario("SCENARIO_BOUNDARY")
        self.assertEqual(res["decision"], DECISION_PRO_CODE)
        self.assertEqual(res["type"], "boundary")
        self.assertIn("15,000 RPS", res["rationale"])
        self.assertIn("air-gapped", res["rationale"])
        self.assertTrue(res["contract_satisfied"])

    def test_missing_info_scenario_decision_and_rationale(self) -> None:
        """Missing information scenario selects DEFER_INSUFFICIENT_INFORMATION with valid rationale."""
        res = run_scenario("SCENARIO_MISSING_INFO")
        self.assertEqual(res["decision"], DECISION_DEFER)
        self.assertEqual(res["type"], "missing_information")
        self.assertIn("missing", res["rationale"])
        self.assertTrue(res["contract_satisfied"])


class TestDualApproachEquivalence(unittest.TestCase):
    """Focus check: Compares direct procedural logic with reference matrix lookup."""

    def test_all_scenarios_dual_approach_parity(self) -> None:
        """Both direct and reference approaches yield 100% equivalent decisions and rationales."""
        for key, data in SCENARIOS_DATA.items():
            facts = data["facts"]
            direct = evaluate_decision_direct(facts)
            reference = evaluate_decision_reference(facts)

            self.assertEqual(
                direct["decision"],
                reference["decision"],
                f"Decision mismatch in {key}"
            )
            self.assertEqual(
                direct["rationale"],
                reference["rationale"],
                f"Rationale mismatch in {key}"
            )

    def test_arbitrary_custom_weights_boundary(self) -> None:
        """Custom weights requirement triggers CUSTOM_CODE_PRO_DEV across both approaches."""
        facts = {
            "target_throughput_rps": 10,
            "data_source": "Dataverse",
            "compliance_tier": "standard",
            "requires_custom_weights": True,
            "prebuilt_model_available": True,
        }
        self.assertEqual(evaluate_decision_direct(facts)["decision"], DECISION_PRO_CODE)
        self.assertEqual(evaluate_decision_reference(facts)["decision"], DECISION_PRO_CODE)


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Validates decision table verification and deliberate tamper detection."""

    def test_canonical_check_passes(self) -> None:
        res = run_canonical_check(tamper=False)
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["failed_scenarios"], 0)
        self.assertEqual(res["total_scenarios"], 3)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateWrongResult(unittest.TestCase):
    """Demonstrates that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_scenario("SCENARIO_NORMAL")
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
        self.assertEqual(data["decision"], DECISION_LOW_CODE)

    def test_cli_scenario_boundary(self) -> None:
        res = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], DECISION_PRO_CODE)

    def test_cli_scenario_missing(self) -> None:
        res = self._run_cli(["--scenario", "missing"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], DECISION_DEFER)

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
