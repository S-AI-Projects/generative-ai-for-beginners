"""
Unit tests for R40-T010: Building Low Code AI Applications Scenario Assessment
"""

import io
import json
import unittest
from contextlib import redirect_stdout

try:
    from .example import (
        BASELINE_SCENARIOS,
        DecisionType,
        ScenarioFacts,
        check_question_1_predict_output,
        check_question_2_diagnose_failure,
        check_question_3_choose_boundary_policy,
        evaluate_scenario,
        main,
        run_all_applied_questions,
        verify_decision_table,
    )
except ImportError:
    from example import (
        BASELINE_SCENARIOS,
        DecisionType,
        ScenarioFacts,
        check_question_1_predict_output,
        check_question_2_diagnose_failure,
        check_question_3_choose_boundary_policy,
        evaluate_scenario,
        main,
        run_all_applied_questions,
        verify_decision_table,
    )


class TestScenarioAssessment(unittest.TestCase):
    def test_normal_scenario_evaluation(self):
        facts = BASELINE_SCENARIOS["S1_NORMAL"]
        assessment = evaluate_scenario(facts)
        self.assertEqual(assessment.scenario_id, "S1_NORMAL")
        self.assertEqual(assessment.decision, DecisionType.LOW_CODE_POWER_PLATFORM.value)
        self.assertEqual(assessment.missing_fields, [])
        self.assertEqual(assessment.boundary_flags, [])
        self.assertIn("Power Platform", assessment.rationale)

    def test_boundary_scenario_evaluation(self):
        facts = BASELINE_SCENARIOS["S2_BOUNDARY"]
        assessment = evaluate_scenario(facts)
        self.assertEqual(assessment.scenario_id, "S2_BOUNDARY")
        self.assertEqual(assessment.decision, DecisionType.CUSTOM_CODE_PRO_DEV.value)
        self.assertTrue(len(assessment.boundary_flags) >= 3)
        self.assertTrue(any("CUSTOM_MODEL_REQUIRED" in flag for flag in assessment.boundary_flags))
        self.assertTrue(any("VOLUME_EXCEEDED" in flag for flag in assessment.boundary_flags))
        self.assertTrue(any("LATENCY_SLA_BREACH" in flag for flag in assessment.boundary_flags))
        self.assertIn("Exceeds low-code architectural boundaries", assessment.rationale)

    def test_missing_info_scenario_evaluation(self):
        facts = BASELINE_SCENARIOS["S3_MISSING_INFO"]
        assessment = evaluate_scenario(facts)
        self.assertEqual(assessment.scenario_id, "S3_MISSING_INFO")
        self.assertEqual(assessment.decision, DecisionType.DEFER_INSUFFICIENT_INFORMATION.value)
        self.assertIn("monthly_volume", assessment.missing_fields)
        self.assertIn("latency_sla_ms", assessment.missing_fields)
        self.assertIn("compliance_tier", assessment.missing_fields)
        self.assertIn("Decision deferred", assessment.rationale)

    def test_decision_table_verification_clean(self):
        result = verify_decision_table(tamper=False)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.passed_scenarios, 3)
        self.assertEqual(result.total_scenarios, 3)
        self.assertEqual(result.mismatches, [])
        self.assertFalse(result.tampered)

    def test_decision_table_verification_tampered(self):
        result = verify_decision_table(tamper=True)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.tampered)
        self.assertTrue(len(result.mismatches) > 0)
        self.assertIn("S1_NORMAL", result.mismatches[0])

    def test_volume_boundary_trigger(self):
        custom_facts = ScenarioFacts(
            scenario_id="TEST_HIGH_VOL",
            name="High Vol Test",
            description="Testing volume threshold",
            monthly_volume=250_000,  # Exceeds 100,000
            latency_sla_ms=5000,
            custom_model_required=False,
            prebuilt_model_available=True,
            compliance_tier="Standard Enterprise Cloud",
        )
        assessment = evaluate_scenario(custom_facts)
        self.assertEqual(assessment.decision, DecisionType.CUSTOM_CODE_PRO_DEV.value)
        self.assertTrue(any("VOLUME_EXCEEDED" in flag for flag in assessment.boundary_flags))

    def test_latency_boundary_trigger(self):
        custom_facts = ScenarioFacts(
            scenario_id="TEST_LOW_LATENCY",
            name="Low Latency Test",
            description="Testing latency threshold",
            monthly_volume=10_000,
            latency_sla_ms=50,  # Below 200ms
            custom_model_required=False,
            prebuilt_model_available=True,
            compliance_tier="Standard Enterprise Cloud",
        )
        assessment = evaluate_scenario(custom_facts)
        self.assertEqual(assessment.decision, DecisionType.CUSTOM_CODE_PRO_DEV.value)
        self.assertTrue(any("LATENCY_SLA_BREACH" in flag for flag in assessment.boundary_flags))

    def test_compliance_boundary_trigger(self):
        custom_facts = ScenarioFacts(
            scenario_id="TEST_COMPLIANCE",
            name="Airgapped Compliance Test",
            description="Testing compliance restriction",
            monthly_volume=10_000,
            latency_sla_ms=5000,
            custom_model_required=False,
            prebuilt_model_available=True,
            compliance_tier="Airgapped On-Prem",
        )
        assessment = evaluate_scenario(custom_facts)
        self.assertEqual(assessment.decision, DecisionType.CUSTOM_CODE_PRO_DEV.value)
        self.assertTrue(any("COMPLIANCE_RESTRICTION" in flag for flag in assessment.boundary_flags))


class TestAppliedQuestions(unittest.TestCase):
    def test_question_1_predict_output_correct(self):
        res = check_question_1_predict_output()
        self.assertTrue(res.passed)
        self.assertEqual(res.expected, DecisionType.LOW_CODE_POWER_PLATFORM.value)
        self.assertEqual(res.actual, DecisionType.LOW_CODE_POWER_PLATFORM.value)
        self.assertIn("Power Platform capabilities", res.rationale)

    def test_question_1_predict_output_wrong_fails(self):
        res = check_question_1_predict_output(predicted_decision=DecisionType.CUSTOM_CODE_PRO_DEV.value)
        self.assertFalse(res.passed)
        self.assertEqual(res.actual, DecisionType.CUSTOM_CODE_PRO_DEV.value)

    def test_question_2_diagnose_failure_correct(self):
        res = check_question_2_diagnose_failure()
        self.assertTrue(res.passed)
        self.assertEqual(res.expected, "MISSING_OPERATIONAL_METRICS")
        self.assertEqual(res.actual, "MISSING_OPERATIONAL_METRICS")
        self.assertIn("mandatory operational fields are absent", res.rationale)

    def test_question_2_diagnose_failure_wrong_code(self):
        res = check_question_2_diagnose_failure(diagnostic_code="WRONG_ERROR_CODE")
        self.assertFalse(res.passed)
        self.assertEqual(res.actual, "WRONG_ERROR_CODE")

    def test_question_3_choose_boundary_policy_correct(self):
        res = check_question_3_choose_boundary_policy()
        self.assertTrue(res.passed)
        self.assertEqual(res.expected, "POLICY_HYBRID_PRO_CODE_OFFLOAD")
        self.assertEqual(res.actual, "POLICY_HYBRID_PRO_CODE_OFFLOAD")
        self.assertIn("Hybrid Pro-Code Offload", res.rationale)

    def test_question_3_choose_boundary_policy_wrong_policy(self):
        res = check_question_3_choose_boundary_policy(chosen_policy="POLICY_RETRY_SPIKE")
        self.assertFalse(res.passed)
        self.assertEqual(res.actual, "POLICY_RETRY_SPIKE")

    def test_run_all_applied_questions(self):
        results = run_all_applied_questions()
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.passed for r in results.values()))


class TestCommandLineInterface(unittest.TestCase):
    def test_cli_all_scenarios(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["--scenario", "all"])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn("S1_NORMAL", output)
        self.assertIn("S2_BOUNDARY", output)
        self.assertIn("S3_MISSING_INFO", output)

    def test_cli_check_success(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["--check"])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn("[CHECK PASSED]", output)

    def test_cli_check_tamper_fails_with_code_1(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["--check", "--tamper"])
        self.assertEqual(exit_code, 1)
        output = f.getvalue()
        self.assertIn("[CHECK FAILED]", output)
        self.assertIn("tampered=True", output)

    def test_cli_questions_flag(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["--questions"])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn("[PASS] Q1_PREDICT_OUTPUT", output)
        self.assertIn("[PASS] Q2_DIAGNOSE_FAILURE", output)
        self.assertIn("[PASS] Q3_CHOOSE_BOUNDARY_POLICY", output)

    def test_cli_json_mode(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["--check", "--questions", "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(f.getvalue())
        self.assertTrue(data["decision_table_verification"]["is_valid"])
        self.assertTrue(data["applied_questions_all_passed"])


if __name__ == "__main__":
    unittest.main()
