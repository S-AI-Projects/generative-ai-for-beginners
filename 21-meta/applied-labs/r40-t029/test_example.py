#!/usr/bin/env python3
"""Regression and Invariant Test Suite for Model Manifest Selection (R40-T029).

Lesson 21: Building With the Meta Family Models.
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Tests:
- Resource constraint satisfaction (RAM budget & requested context length)
- Explicit exclusion diagnosis and structured reason reporting
- Canonical teaching fixtures (admits only Fixture A under RAM 6 / Context 1024)
- Boundary equality and threshold step-off sensitivity
- Input validation and malformed manifest error handling
- 3-configuration evaluation experiment correctness and trade-off metrics
- Canonical decision table checks and deliberate tamper regression detection
- Subprocess CLI invocations and exit code contracts
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    CANONICAL_MANIFEST,
    EXTENDED_MANIFEST,
    FIXTURE_A,
    FIXTURE_B,
    FIXTURE_C,
    FIXTURE_D,
    CandidateEvaluation,
    DecisionMismatchError,
    ExclusionReasonCode,
    InvalidResourceBudgetError,
    MalformedManifestError,
    ManifestSelector,
    ModelManifestEntry,
    ResourceBudget,
    SelectionReport,
    run_boundary_scenario,
    run_canonical_check,
    run_evaluation_experiment,
    run_failure_scenario,
    run_normal_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestManifestDataModelsAndValidation(unittest.TestCase):
    """Validates schema definitions, serialization, and input validation guards."""

    def test_model_manifest_entry_initialization(self) -> None:
        """Entry must preserve attributes and serialize accurately to dictionary."""
        entry = ModelManifestEntry(
            model_id="test-mod",
            name="Test Model",
            min_ram_gb=4.5,
            max_context_tokens=4096,
        )
        self.assertEqual(entry.model_id, "test-mod")
        self.assertEqual(entry.name, "Test Model")
        self.assertEqual(entry.min_ram_gb, 4.5)
        self.assertEqual(entry.max_context_tokens, 4096)
        data = entry.to_dict()
        self.assertEqual(data["model_id"], "test-mod")
        self.assertEqual(data["min_ram_gb"], 4.5)

    def test_resource_budget_validation_positive(self) -> None:
        """Valid positive budget must pass validation without error."""
        budget = ResourceBudget(budget_ram_gb=8.0, requested_context_tokens=2048)
        budget.validate()
        self.assertEqual(budget.budget_ram_gb, 8.0)
        self.assertEqual(budget.requested_context_tokens, 2048)

    def test_resource_budget_rejects_negative_or_zero_ram(self) -> None:
        """Non-positive host RAM budgets must raise InvalidResourceBudgetError."""
        with self.assertRaises(InvalidResourceBudgetError):
            ResourceBudget(budget_ram_gb=0.0, requested_context_tokens=1024).validate()
        with self.assertRaises(InvalidResourceBudgetError):
            ResourceBudget(budget_ram_gb=-4.0, requested_context_tokens=1024).validate()

    def test_resource_budget_rejects_negative_or_zero_context(self) -> None:
        """Non-positive requested context must raise InvalidResourceBudgetError."""
        with self.assertRaises(InvalidResourceBudgetError):
            ResourceBudget(budget_ram_gb=8.0, requested_context_tokens=0).validate()
        with self.assertRaises(InvalidResourceBudgetError):
            ResourceBudget(budget_ram_gb=8.0, requested_context_tokens=-512).validate()

    def test_validate_manifest_empty_rejected(self) -> None:
        """Empty manifest must raise MalformedManifestError."""
        with self.assertRaises(MalformedManifestError):
            ManifestSelector.validate_manifest([])

    def test_validate_manifest_duplicate_id_rejected(self) -> None:
        """Manifest with duplicate model IDs must raise MalformedManifestError."""
        dup_manifest = [FIXTURE_A, FIXTURE_A]
        with self.assertRaises(MalformedManifestError):
            ManifestSelector.validate_manifest(dup_manifest)

    def test_validate_manifest_empty_id_rejected(self) -> None:
        """Entry with empty model_id string must raise MalformedManifestError."""
        invalid_entry = ModelManifestEntry(
            model_id="   ",
            name="Blank ID",
            min_ram_gb=4.0,
            max_context_tokens=1024,
        )
        with self.assertRaises(MalformedManifestError):
            ManifestSelector.validate_manifest([invalid_entry])

    def test_validate_manifest_negative_ram_rejected(self) -> None:
        """Entry with negative min_ram_gb must raise MalformedManifestError."""
        invalid_entry = ModelManifestEntry(
            model_id="neg-ram",
            name="Negative RAM",
            min_ram_gb=-2.0,
            max_context_tokens=1024,
        )
        with self.assertRaises(MalformedManifestError):
            ManifestSelector.validate_manifest([invalid_entry])

    def test_validate_manifest_non_positive_context_rejected(self) -> None:
        """Entry with non-positive context length must raise MalformedManifestError."""
        invalid_entry = ModelManifestEntry(
            model_id="zero-ctx",
            name="Zero Context",
            min_ram_gb=4.0,
            max_context_tokens=0,
        )
        with self.assertRaises(MalformedManifestError):
            ManifestSelector.validate_manifest([invalid_entry])


class TestCanonicalSelectionContract(unittest.TestCase):
    """Validates the core task contract: Fixture A vs Fixture B under RAM 6 / Context 1024."""

    def test_canonical_fixture_properties(self) -> None:
        """Verifies canonical fixture values match the contract specification."""
        self.assertEqual(FIXTURE_A.min_ram_gb, 4.0)
        self.assertEqual(FIXTURE_A.max_context_tokens, 2048)
        self.assertEqual(FIXTURE_B.min_ram_gb, 8.0)
        self.assertEqual(FIXTURE_B.max_context_tokens, 4096)

    def test_canonical_selection_admits_only_a(self) -> None:
        """Budget RAM 6 and requested context 1024 must admit ONLY Fixture A."""
        budget = ResourceBudget(budget_ram_gb=6.0, requested_context_tokens=1024)
        report = ManifestSelector.select(CANONICAL_MANIFEST, budget)

        # Admitted model assertions
        self.assertEqual(report.admitted_models, ["model-a"])
        self.assertEqual(report.excluded_models, ["model-b"])
        self.assertEqual(report.admitted_count if hasattr(report, "admitted_count") else len(report.admitted_models), 1)
        self.assertEqual(report.admission_rate_pct, 50.0)
        self.assertEqual(report.decision, "SELECTIVE_ADMISSION_SUCCESS")

        # Fixture A evaluation details
        a_eval = next(e for e in report.evaluations if e.model_id == "model-a")
        self.assertTrue(a_eval.eligible)
        self.assertEqual(a_eval.ram_slack_gb, 2.0)  # 6.0 - 4.0 = +2.0 GB
        self.assertEqual(a_eval.context_headroom_tokens, 1024)  # 2048 - 1024 = +1024 tokens
        self.assertEqual(a_eval.exclusion_reasons, [])
        self.assertEqual(a_eval.reason_codes, [])

        # Fixture B evaluation details & explicit exclusion explanation
        b_eval = next(e for e in report.evaluations if e.model_id == "model-b")
        self.assertFalse(b_eval.eligible)
        self.assertEqual(b_eval.ram_slack_gb, -2.0)  # 6.0 - 8.0 = -2.0 GB
        self.assertEqual(b_eval.context_headroom_tokens, 3072)  # 4096 - 1024 = +3072 tokens
        self.assertEqual(b_eval.reason_codes, [ExclusionReasonCode.RAM_EXCEEDS_BUDGET.value])
        self.assertEqual(len(b_eval.exclusion_reasons), 1)
        self.assertIn("RAM requirement (8.0 GB) exceeds host budget (6.0 GB)", b_eval.exclusion_reasons[0])
        self.assertIn("by 2.0 GB", b_eval.exclusion_reasons[0])

    def test_run_normal_scenario_function(self) -> None:
        """Direct call to run_normal_scenario must return valid report admitting only A."""
        report = run_normal_scenario()
        self.assertIsInstance(report, SelectionReport)
        self.assertEqual(report.admitted_models, ["model-a"])
        self.assertEqual(report.excluded_models, ["model-b"])


class TestBoundaryConditions(unittest.TestCase):
    """Validates exact threshold boundaries, slack calculations, and step-off deficits."""

    def test_exact_equality_admits_candidate(self) -> None:
        """Exact budget match (RAM 4.0 GB, Context 2048) must admit Fixture A with zero slack."""
        budget = ResourceBudget(budget_ram_gb=4.0, requested_context_tokens=2048)
        report = ManifestSelector.select(CANONICAL_MANIFEST, budget)

        self.assertEqual(report.admitted_models, ["model-a"])
        a_eval = next(e for e in report.evaluations if e.model_id == "model-a")
        self.assertTrue(a_eval.eligible)
        self.assertEqual(a_eval.ram_slack_gb, 0.0)
        self.assertEqual(a_eval.context_headroom_tokens, 0)

        # Fixture B fails both RAM and context (8 > 4 and 4096 >= 2048 context is ok)
        b_eval = next(e for e in report.evaluations if e.model_id == "model-b")
        self.assertFalse(b_eval.eligible)
        self.assertIn(ExclusionReasonCode.RAM_EXCEEDS_BUDGET.value, b_eval.reason_codes)

    def test_threshold_stepoff_excludes_candidate(self) -> None:
        """Host RAM of 3.9 GB (0.1 GB below Fixture A requirement) must exclude Fixture A."""
        budget = ResourceBudget(budget_ram_gb=3.9, requested_context_tokens=2048)
        report = ManifestSelector.select(CANONICAL_MANIFEST, budget)

        self.assertEqual(report.admitted_models, [])
        self.assertEqual(set(report.excluded_models), {"model-a", "model-b"})
        a_eval = next(e for e in report.evaluations if e.model_id == "model-a")
        self.assertFalse(a_eval.eligible)
        self.assertAlmostEqual(a_eval.ram_slack_gb, -0.1, places=2)

    def test_context_window_exact_and_stepoff(self) -> None:
        """Context window thresholding must exclude models when requested tokens exceed capacity."""
        # 2048 requested -> Fixture A meets it
        budget_exact = ResourceBudget(budget_ram_gb=10.0, requested_context_tokens=2048)
        report_exact = ManifestSelector.select([FIXTURE_A], budget_exact)
        self.assertTrue(report_exact.evaluations[0].eligible)

        # 2049 requested -> Fixture A fails context constraint
        budget_stepoff = ResourceBudget(budget_ram_gb=10.0, requested_context_tokens=2049)
        report_stepoff = ManifestSelector.select([FIXTURE_A], budget_stepoff)
        eval_stepoff = report_stepoff.evaluations[0]
        self.assertFalse(eval_stepoff.eligible)
        self.assertIn(ExclusionReasonCode.INSUFFICIENT_CONTEXT.value, eval_stepoff.reason_codes)
        self.assertEqual(eval_stepoff.context_headroom_tokens, -1)

    def test_dual_deficit_reporting(self) -> None:
        """Candidate failing both RAM and context must report DUAL_RESOURCE_DEFICIT."""
        # Fixture A needs RAM 4 / context 2048. Host offers RAM 2 / context 4096.
        budget = ResourceBudget(budget_ram_gb=2.0, requested_context_tokens=4096)
        report = ManifestSelector.select([FIXTURE_A], budget)
        a_eval = report.evaluations[0]
        self.assertFalse(a_eval.eligible)
        self.assertIn(ExclusionReasonCode.DUAL_RESOURCE_DEFICIT.value, a_eval.reason_codes)
        self.assertIn("Dual constraint deficit", a_eval.exclusion_reasons[0])

    def test_run_boundary_scenario_function(self) -> None:
        """Direct call to run_boundary_scenario must succeed and verify boundary cases."""
        res = run_boundary_scenario()
        self.assertEqual(res["decision"], "BOUNDARY_VERIFICATION_SUCCESS")
        self.assertEqual(res["case_exact_equality"]["admitted_models"], ["model-a"])
        self.assertEqual(res["case_stepoff_deficit"]["admitted_models"], [])


class TestEvaluationExperiment(unittest.TestCase):
    """Validates the 3-configuration evaluation experiment and trade-off metrics."""

    def test_evaluation_experiment_structure_and_correctness(self) -> None:
        """Experiment must evaluate 3 configurations and verify all correctness assertions."""
        res = run_evaluation_experiment()
        self.assertEqual(res["decision"], "EXPERIMENT_EVALUATION_SUCCESS")
        self.assertEqual(res["total_configs_compared"], 3)
        self.assertTrue(res["all_configs_correct"])

        configs = res["configurations"]
        self.assertEqual(len(configs), 3)

        # Config 1: Edge (RAM 6, Context 1024) -> Admits A, Excludes B
        cfg1 = configs[0]
        self.assertEqual(cfg1["config_id"], "CONFIG_1_EDGE_CONSTRAINED")
        self.assertEqual(cfg1["admitted_models"], ["model-a"])
        self.assertEqual(cfg1["excluded_models"], ["model-b"])
        self.assertEqual(cfg1["admission_rate_pct"], 50.0)
        self.assertEqual(cfg1["metrics"]["avg_ram_slack_gb"], 2.0)
        self.assertEqual(cfg1["metrics"]["avg_context_headroom_tokens"], 1024.0)
        self.assertEqual(cfg1["metrics"]["primary_bottleneck"], "RAM_CAPACITY")

        # Config 2: Long-Context Cloud (RAM 8, Context 4096) -> Admits B, Excludes A
        cfg2 = configs[1]
        self.assertEqual(cfg2["config_id"], "CONFIG_2_LONG_CONTEXT_CLOUD")
        self.assertEqual(cfg2["admitted_models"], ["model-b"])
        self.assertEqual(cfg2["excluded_models"], ["model-a"])
        self.assertEqual(cfg2["admission_rate_pct"], 50.0)
        self.assertEqual(cfg2["metrics"]["avg_ram_slack_gb"], 0.0)
        self.assertEqual(cfg2["metrics"]["avg_context_headroom_tokens"], 0.0)
        self.assertEqual(cfg2["metrics"]["primary_bottleneck"], "CONTEXT_WINDOW_LIMIT")

        # Config 3: Generous Workstation (RAM 16, Context 1024) -> Admits A and B
        cfg3 = configs[2]
        self.assertEqual(cfg3["config_id"], "CONFIG_3_WORKSTATION_EXPANSIVE")
        self.assertEqual(cfg3["admitted_models"], ["model-a", "model-b"])
        self.assertEqual(cfg3["excluded_models"], [])
        self.assertEqual(cfg3["admission_rate_pct"], 100.0)
        self.assertEqual(cfg3["metrics"]["avg_ram_slack_gb"], 10.0)
        self.assertEqual(cfg3["metrics"]["avg_context_headroom_tokens"], 2048.0)
        self.assertEqual(cfg3["metrics"]["primary_bottleneck"], "NONE_UNCONSTRAINED")

    def test_trade_off_analysis_narrative_present(self) -> None:
        """Experiment report must include explicit trade-off findings without real-model claims."""
        res = run_evaluation_experiment()
        trade_off = res["trade_off_analysis"]
        self.assertIn("finding", trade_off)
        self.assertIn("edge_tradeoff", trade_off)
        self.assertIn("cloud_tradeoff", trade_off)
        self.assertIn("workstation_tradeoff", trade_off)
        self.assertIn("no_accuracy_claim_disclaimer", trade_off)


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Validates canonical decision table check and regression sensitivity upon tampering."""

    def test_canonical_check_clean_pass(self) -> None:
        """Untampered canonical check must report 100% pass across all scenarios."""
        res = run_canonical_check(tamper=False)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["failed_scenarios"], 0)
        self.assertEqual(res["passed_scenarios"], 4)

    def test_canonical_check_tamper_fails(self) -> None:
        """Tampered check must raise DecisionMismatchError."""
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestSubprocessCLIExecution(unittest.TestCase):
    """Validates CLI command line invocations in fresh isolated subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal_exit_0(self) -> None:
        """CLI --scenario normal must exit 0, emit JSON, and admit only model-a."""
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "SELECTIVE_ADMISSION_SUCCESS")
        self.assertEqual(data["admitted_models"], ["model-a"])
        self.assertEqual(data["excluded_models"], ["model-b"])

    def test_cli_scenario_boundary_exit_0(self) -> None:
        """CLI --scenario boundary must exit 0 and verify threshold equality."""
        res = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "BOUNDARY_VERIFICATION_SUCCESS")
        self.assertEqual(data["case_exact_equality"]["boundary_status"], "EXACT_MATCH_ADMITTED")

    def test_cli_scenario_failure_exit_0(self) -> None:
        """CLI --scenario failure must exit 0 and report caught validation errors."""
        res = self._run_cli(["--scenario", "failure"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "INPUT_VALIDATION_HANDLED_CLEANLY")
        self.assertEqual(data["errors_validated_count"], 3)

    def test_cli_experiment_exit_0(self) -> None:
        """CLI --experiment must exit 0 and return 3-configuration comparison."""
        res = self._run_cli(["--experiment"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "EXPERIMENT_EVALUATION_SUCCESS")
        self.assertEqual(data["total_configs_compared"], 3)

    def test_cli_check_exit_0(self) -> None:
        """CLI --check must exit 0 and report all passed."""
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_fails_with_nonzero_exit_1(self) -> None:
        """CLI --tamper must exit 1 and report DecisionMismatchError in stderr."""
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1, f"Expected exit code 1, got {res.returncode}")
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")
        self.assertEqual(data["error_type"], "DecisionMismatchError")
        self.assertEqual(data["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
