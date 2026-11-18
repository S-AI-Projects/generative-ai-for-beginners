#!/usr/bin/env python3
"""Automated unit and integration test suite for R40-T023.

Validates the three-scenario decision framework, comparing the direct rule engine
with the independent calculation baseline, testing boundary conditions, missing
disclosures, decision tampering detection, and CLI invocations.
"""

import copy
import json
import os
import subprocess
import sys
import unittest
from typing import Any, Dict

# Support direct execution and test discovery
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from example import (
    PUBLISHED_DECISION_TABLE,
    REQUIRED_CRITERIA_KEYS,
    Decision,
    DecisionMismatchError,
    check_decision_table,
    evaluate_model_direct,
    evaluate_model_independent,
)


class TestDirectEvaluationEngine(unittest.TestCase):
    """Tests the direct rule engine (Approach 1) across diverse model transparency profiles."""

    def test_normal_scenario_open_source(self) -> None:
        """Fully disclosed model with all 5 lesson criteria + OSI license must be OPEN_SOURCE."""
        facts = {
            "model_weights_public": True,
            "training_datasets_public": True,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": True,
            "osi_approved_license": True,
        }
        res = evaluate_model_direct(facts, model_id="olmo-test")
        self.assertEqual(res["decision"], Decision.OPEN_SOURCE.value)
        self.assertEqual(res["decision_code"], "DECISION_OPEN_SOURCE")
        self.assertEqual(res["criteria_summary"]["satisfied_count"], 6)
        self.assertEqual(res["criteria_summary"]["withheld_count"], 0)
        self.assertEqual(res["criteria_summary"]["missing_count"], 0)
        self.assertIn("OLMo", res["rationale"])
        self.assertIn("traditional definition of open source", res["rationale"])

    def test_boundary_scenario_open_weights(self) -> None:
        """Model with public weights but withheld pre-training data and metrics must be OPEN_WEIGHTS."""
        facts = {
            "model_weights_public": True,
            "training_datasets_public": False,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": False,
            "osi_approved_license": False,
        }
        res = evaluate_model_direct(facts, model_id="llama2-test")
        self.assertEqual(res["decision"], Decision.OPEN_WEIGHTS.value)
        self.assertEqual(res["decision_code"], "DECISION_OPEN_WEIGHTS")
        self.assertEqual(res["criteria_summary"]["satisfied_count"], 3)
        self.assertEqual(res["criteria_summary"]["withheld_count"], 3)
        self.assertIn("open model", res["rationale"].lower())
        self.assertIn("boundary", res["rationale"].lower())
        self.assertIn("training_datasets_public", res["rationale"])

    def test_missing_information_scenario_undetermined(self) -> None:
        """Model with null/unverified fields must result in UNDETERMINED."""
        facts = {
            "model_weights_public": True,
            "training_datasets_public": None,
            "evaluation_code_public": True,
            "fine_tuning_code_public": None,
            "training_metrics_public": None,
            "osi_approved_license": None,
        }
        res = evaluate_model_direct(facts, model_id="unverified-model")
        self.assertEqual(res["decision"], Decision.UNDETERMINED.value)
        self.assertEqual(res["decision_code"], "DECISION_UNDETERMINED_MISSING_DISCLOSURES")
        self.assertEqual(res["criteria_summary"]["missing_count"], 4)
        self.assertIn("fine_tuning_code_public", res["criteria_summary"]["missing"])
        self.assertIn("training_datasets_public", res["criteria_summary"]["missing"])
        self.assertIn("undetermined", res["rationale"].lower())

    def test_boundary_single_missing_field_triggers_undetermined(self) -> None:
        """Even if 5 criteria are True, a single None field must trigger UNDETERMINED."""
        facts = {
            "model_weights_public": True,
            "training_datasets_public": True,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": True,
            "osi_approved_license": None,  # Single missing field
        }
        res = evaluate_model_direct(facts, model_id="single-missing")
        self.assertEqual(res["decision"], Decision.UNDETERMINED.value)
        self.assertEqual(res["criteria_summary"]["missing"], ["osi_approved_license"])

    def test_boundary_only_license_non_osi_yields_open_weights(self) -> None:
        """If all artifacts are public but license is non-OSI (e.g. custom commercial cap), it's OPEN_WEIGHTS."""
        facts = {
            "model_weights_public": True,
            "training_datasets_public": True,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": True,
            "osi_approved_license": False,  # Non-OSI license
        }
        res = evaluate_model_direct(facts, model_id="non-osi-model")
        self.assertEqual(res["decision"], Decision.OPEN_WEIGHTS.value)

    def test_boundary_proprietary_closed_model(self) -> None:
        """If model weights are private (API-only), model is PROPRIETARY."""
        facts = {
            "model_weights_public": False,
            "training_datasets_public": False,
            "evaluation_code_public": False,
            "fine_tuning_code_public": False,
            "training_metrics_public": False,
            "osi_approved_license": False,
        }
        res = evaluate_model_direct(facts, model_id="closed-api-model")
        self.assertEqual(res["decision"], Decision.PROPRIETARY.value)
        self.assertIn("proprietary/closed", res["rationale"])

    def test_invalid_facts_type_raises_type_error(self) -> None:
        """Non-dictionary input must raise TypeError."""
        with self.assertRaises(TypeError):
            evaluate_model_direct("not-a-dict")  # type: ignore


class TestIndependentCalculationBaseline(unittest.TestCase):
    """Tests the simpler independent calculation (Approach 2) and cross-checks with Approach 1."""

    def test_independent_normal_scenario(self) -> None:
        facts = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]["facts"]
        self.assertEqual(evaluate_model_independent(facts), Decision.OPEN_SOURCE.value)

    def test_independent_boundary_scenario(self) -> None:
        facts = PUBLISHED_DECISION_TABLE["SCENARIO_BOUNDARY"]["facts"]
        self.assertEqual(evaluate_model_independent(facts), Decision.OPEN_WEIGHTS.value)

    def test_independent_missing_info_scenario(self) -> None:
        facts = PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]["facts"]
        self.assertEqual(evaluate_model_independent(facts), Decision.UNDETERMINED.value)

    def test_approaches_perfectly_agree_across_fixtures(self) -> None:
        """Verifies that Approach 1 and Approach 2 produce identical decisions on identical inputs."""
        test_cases = [
            PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]["facts"],
            PUBLISHED_DECISION_TABLE["SCENARIO_BOUNDARY"]["facts"],
            PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]["facts"],
            {k: False for k in REQUIRED_CRITERIA_KEYS},  # Closed
            {k: True for k in REQUIRED_CRITERIA_KEYS},   # Open source
            {**{k: True for k in REQUIRED_CRITERIA_KEYS}, "training_datasets_public": False},  # Open weights
        ]
        for facts in test_cases:
            direct = evaluate_model_direct(facts)["decision"]
            independent = evaluate_model_independent(facts)
            self.assertEqual(
                direct,
                independent,
                f"Mismatch between direct ({direct}) and independent ({independent}) for facts: {facts}",
            )


class TestPublishedDecisionTableAndChecker(unittest.TestCase):
    """Tests the published decision table validation and tamper detection."""

    def test_checker_passes_on_canonical_table(self) -> None:
        """The untouched published decision table must pass all checks."""
        report = check_decision_table(PUBLISHED_DECISION_TABLE, fail_on_tamper=True)
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["total_scenarios"], 3)
        self.assertEqual(report["passed_scenarios"], 3)
        self.assertEqual(report["failed_scenarios"], 0)

        for scenario in report["scenarios"]:
            self.assertEqual(scenario["status"], "PASS")
            self.assertTrue(scenario["approaches_agree"])
            self.assertTrue(scenario["matches_table"])
            self.assertTrue(scenario["rationale_valid"])

    def test_checker_fails_when_decision_deliberately_changed(self) -> None:
        """Tampering with a decision in the table must raise DecisionMismatchError."""
        tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        # Change normal scenario expected decision to OPEN_WEIGHTS
        tampered_table["SCENARIO_NORMAL"]["expected_decision"] = Decision.OPEN_WEIGHTS.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered_table, fail_on_tamper=True)

        self.assertIn("SCENARIO_NORMAL", str(ctx.exception))
        self.assertEqual(ctx.exception.expected, Decision.OPEN_WEIGHTS.value)
        self.assertEqual(ctx.exception.actual, Decision.OPEN_SOURCE.value)

    def test_checker_fails_when_boundary_decision_deliberately_changed(self) -> None:
        """Tampering with boundary scenario decision must raise DecisionMismatchError."""
        tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered_table["SCENARIO_BOUNDARY"]["expected_decision"] = Decision.OPEN_SOURCE.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered_table, fail_on_tamper=True)

        self.assertIn("SCENARIO_BOUNDARY", str(ctx.exception))

    def test_checker_fails_when_missing_info_decision_deliberately_changed(self) -> None:
        """Tampering with missing_info scenario decision must raise DecisionMismatchError."""
        tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered_table["SCENARIO_MISSING_INFO"]["expected_decision"] = Decision.OPEN_SOURCE.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered_table, fail_on_tamper=True)

        self.assertIn("SCENARIO_MISSING_INFO", str(ctx.exception))

    def test_checker_soft_failure_reporting(self) -> None:
        """When fail_on_tamper=False, checker returns a report with all_passed=False instead of raising."""
        tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered_table["SCENARIO_NORMAL"]["expected_decision"] = "WRONG_DECISION"

        report = check_decision_table(tampered_table, fail_on_tamper=False)
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["status"], "failure")
        self.assertEqual(report["failed_scenarios"], 1)


class TestSubprocessCLIExecution(unittest.TestCase):
    """Tests CLI entrypoint and fresh-process execution."""

    def setUp(self) -> None:
        self.example_script = os.path.join(CURRENT_DIR, "example.py")

    def _run_cmd(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, self.example_script] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_default_check_exit_0(self) -> None:
        res = self._run_cmd(["--check"])
        self.assertEqual(res.returncode, 0, f"Stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_scenarios"], 3)

    def test_cli_scenario_normal_exit_0(self) -> None:
        res = self._run_cmd(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["scenarios"][0]["direct_decision"], "OPEN_SOURCE")

    def test_cli_scenario_boundary_exit_0(self) -> None:
        res = self._run_cmd(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["scenarios"][0]["direct_decision"], "OPEN_WEIGHTS")

    def test_cli_scenario_missing_info_exit_0(self) -> None:
        res = self._run_cmd(["--scenario", "missing_info"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["scenarios"][0]["direct_decision"], "UNDETERMINED")

    def test_cli_tamper_test_exit_1(self) -> None:
        """The CLI --tamper-test flag must exit nonzero with DecisionMismatchError."""
        res = self._run_cmd(["--tamper-test"])
        self.assertEqual(res.returncode, 1)
        self.assertIn("DecisionMismatchError", res.stderr)

    def test_cli_custom_call_payload(self) -> None:
        payload = json.dumps({
            "model_id": "cli-test",
            "facts": {
                "model_weights_public": True,
                "training_datasets_public": True,
                "evaluation_code_public": True,
                "fine_tuning_code_public": True,
                "training_metrics_public": True,
                "osi_approved_license": True,
            },
        })
        res = self._run_cmd(["--call", payload])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["direct_evaluation"]["decision"], "OPEN_SOURCE")
        self.assertEqual(data["independent_decision"], "OPEN_SOURCE")
        self.assertTrue(data["approaches_agree"])


class TestDeliberateFailureVerification(unittest.TestCase):
    """Guarantees that a deliberate wrong test expectation strictly fails."""

    def test_deliberate_wrong_result_fails(self) -> None:
        facts = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]["facts"]
        actual_decision = evaluate_model_direct(facts)["decision"]

        # Deliberate wrong expectation
        with self.assertRaises(AssertionError):
            self.assertEqual(actual_decision, "WRONG_FORCED_DECISION")


if __name__ == "__main__":
    unittest.main()
