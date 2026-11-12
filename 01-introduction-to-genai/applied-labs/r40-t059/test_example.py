"""Unit tests for Lesson 01 startup decision table, error explanation & recovery."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = MODULE_DIR / "example.py"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from example import (  # noqa: E402
    DECISION_TABLE,
    WORKED_SCENARIOS,
    StartupSessionProcessor,
    assert_decision_table,
    build_tampered_table,
    check_decision_table,
    evaluate_startup_rules,
    run_error_and_recovery_sequence,
)


class TestStartupDecisionAndRecovery(unittest.TestCase):
    def test_three_worked_scenarios_match_decision_table(self) -> None:
        report = assert_decision_table(WORKED_SCENARIOS)
        self.assertTrue(report["simulation"])
        self.assertEqual(report["checked_count"], 3)
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["mismatches"], [])

        decisions = {r["scenario_id"]: r["actual_decision"] for r in report["results"]}
        self.assertEqual(decisions["normal"], "serve_tutor_first_draft")
        self.assertEqual(decisions["boundary"], "shorten_or_split_prompt")
        self.assertEqual(decisions["missing_info"], "halt_and_explain_missing_data")

        self.assertEqual([r["rule_id"] for r in DECISION_TABLE], ["M1", "B1", "R1", "N1"])
        gated = evaluate_startup_rules(
            {
                **WORKED_SCENARIOS["normal"]["input_facts"],
                "teacher_review_gate": False,
            }
        )
        self.assertEqual(gated["rule_id"], "R1")
        self.assertEqual(gated["decision"], "route_to_teacher_review")

    def test_checker_fails_when_any_decision_is_deliberately_changed(self) -> None:
        for scenario_id, bad_decision in (
            ("normal", "shorten_or_split_prompt"),
            ("boundary", "serve_tutor_first_draft"),
            ("missing_info", "serve_tutor_first_draft"),
        ):
            tampered = build_tampered_table(scenario_id, bad_decision)
            report = check_decision_table(tampered)
            self.assertFalse(report["all_passed"])
            self.assertEqual(len(report["mismatches"]), 1)
            self.assertEqual(report["mismatches"][0]["scenario_id"], scenario_id)

            with self.assertRaises(AssertionError) as ctx:
                assert_decision_table(tampered)
            self.assertIn(scenario_id, str(ctx.exception))

    def test_invalid_and_missing_data_error_explanation_and_next_input_recovery(self) -> None:
        recovery = run_error_and_recovery_sequence()
        self.assertTrue(recovery["simulation"])
        self.assertEqual(recovery["error_count"], 2)
        self.assertEqual(recovery["recovered_count"], 1)
        self.assertEqual(recovery["final_status"], "recovered_valid_ok")
        self.assertEqual(recovery["final_decision"], "serve_tutor_first_draft")

        step1, step2, step3 = recovery["steps"]
        self.assertEqual(step1["status"], "missing_data_error_explained")
        self.assertIn("learner_level", step1["error_explanation"])
        self.assertIn("prompt_tokens", step1["error_explanation"])
        self.assertEqual(step2["status"], "invalid_input_error_explained")
        self.assertIn("non-negative integer", step2["error_explanation"])
        self.assertEqual(step3["status"], "recovered_valid_ok")
        self.assertTrue(step3["recovered_after_prior_error"])

        processor = StartupSessionProcessor()
        bad = processor.process("bad_type", {"prompt": "hi"})
        self.assertEqual(bad["status"], "missing_data_error_explained")
        ok = processor.process("next_valid", WORKED_SCENARIOS["boundary"]["input_facts"])
        self.assertEqual(ok["status"], "recovered_valid_ok")
        self.assertEqual(ok["decision"], "shorten_or_split_prompt")

    def test_fresh_process_cli_scenarios_recovery_and_tamper_failure(self) -> None:
        for mode in ("normal", "boundary", "missing_info", "recovery", "all"):
            proc = subprocess.run(
                [sys.executable, str(EXAMPLE_PATH), "--mode", mode],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"mode={mode} stderr={proc.stderr}")
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["simulation"])

        tamper_proc = subprocess.run(
            [sys.executable, str(EXAMPLE_PATH), "--mode", "tamper"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(tamper_proc.returncode, 1)
        tamper_payload = json.loads(tamper_proc.stdout)
        self.assertFalse(tamper_payload["all_passed"])
        self.assertEqual(len(tamper_payload["mismatches"]), 1)


if __name__ == "__main__":
    unittest.main()
