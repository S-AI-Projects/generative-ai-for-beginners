"""Regression and failure tests for the Lesson 01 worked startup scenarios."""

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
    PUBLISHED_DECISION_TABLE,
    WORKED_SCENARIOS,
    assert_published_scenarios,
    build_tampered_scenarios,
    check_published_scenarios,
    evaluate_decision_table,
)


class TestStartupWorkedScenarios(unittest.TestCase):
    def test_published_three_scenario_regression_suite(self) -> None:
        """Execute the exact published three-scenario worked table as a regression test."""
        report = assert_published_scenarios(WORKED_SCENARIOS)
        self.assertTrue(report["simulation"])
        self.assertEqual(report["checked_count"], 3)
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["mismatches"], [])

        by_id = {item["scenario_id"]: item for item in report["results"]}
        self.assertEqual(by_id["normal"]["expected_decision"], "approve_llm_draft")
        self.assertEqual(by_id["normal"]["rule_id"], "R4")
        self.assertEqual(
            by_id["boundary"]["expected_decision"], "chunk_prompt_at_token_limit"
        )
        self.assertEqual(by_id["boundary"]["rule_id"], "R2")
        self.assertEqual(
            by_id["missing_info"]["expected_decision"], "request_missing_information"
        )
        self.assertEqual(by_id["missing_info"]["rule_id"], "R1")

    def test_decision_table_rules_cover_human_review_gate_and_boundaries(self) -> None:
        self.assertEqual([r["rule_id"] for r in PUBLISHED_DECISION_TABLE], ["R1", "R2", "R3", "R4"])

        no_review = evaluate_decision_table(
            {
                "role": "student",
                "task_type": "concept_explanation",
                "prompt_text": "Explain metaphors in poetry.",
                "estimated_tokens": 12,
                "max_input_tokens": 100,
                "human_review_enabled": False,
            }
        )
        self.assertEqual(no_review["rule_id"], "R3")
        self.assertEqual(no_review["decision"], "require_human_review_gate")

        just_under_limit = evaluate_decision_table(
            {
                "role": "teacher",
                "task_type": "article_summarization",
                "prompt_text": "Summarize this short passage.",
                "estimated_tokens": 99,
                "max_input_tokens": 100,
                "human_review_enabled": True,
            }
        )
        self.assertEqual(just_under_limit["rule_id"], "R4")
        self.assertEqual(just_under_limit["decision"], "approve_llm_draft")

    def test_checker_fails_when_decision_is_deliberately_changed(self) -> None:
        for scenario_id, wrong_decision in (
            ("normal", "chunk_prompt_at_token_limit"),
            ("boundary", "approve_llm_draft"),
            ("missing_info", "approve_llm_draft"),
        ):
            tampered = build_tampered_scenarios(scenario_id, wrong_decision)
            report = check_published_scenarios(tampered)
            self.assertFalse(report["all_passed"])
            self.assertEqual(len(report["mismatches"]), 1)
            self.assertEqual(report["mismatches"][0]["scenario_id"], scenario_id)

            with self.assertRaises(AssertionError) as ctx:
                assert_published_scenarios(tampered)
            self.assertIn(scenario_id, str(ctx.exception))

    def test_invalid_inputs_and_missing_rationale_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_decision_table(
                {
                    "role": "student",
                    "task_type": "concept_explanation",
                    "prompt_text": "Explain decimals.",
                    "estimated_tokens": -1,
                    "max_input_tokens": 100,
                    "human_review_enabled": True,
                }
            )

        bad_table = {
            "normal": {
                **WORKED_SCENARIOS["normal"],
                "rationale": "",
            }
        }
        with self.assertRaises(ValueError):
            check_published_scenarios(bad_table)

    def test_fresh_process_cli_normal_boundary_missing_and_tamper_failure(self) -> None:
        full_proc = subprocess.run(
            [sys.executable, str(EXAMPLE_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(full_proc.returncode, 0)
        full_payload = json.loads(full_proc.stdout)
        self.assertEqual(full_payload["checked_count"], 3)
        self.assertTrue(full_payload["all_passed"])

        for scenario_id, expected_decision in (
            ("normal", "approve_llm_draft"),
            ("boundary", "chunk_prompt_at_token_limit"),
            ("missing_info", "request_missing_information"),
        ):
            proc = subprocess.run(
                [sys.executable, str(EXAMPLE_PATH), "--scenario", scenario_id],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["results"][0]["actual_decision"], expected_decision)

        tamper_proc = subprocess.run(
            [
                sys.executable,
                str(EXAMPLE_PATH),
                "--scenario",
                "normal",
                "--tamper-decision",
                "request_missing_information",
            ],
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
