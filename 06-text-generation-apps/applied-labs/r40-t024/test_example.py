#!/usr/bin/env python3
"""Automated unit and integration test suite for R40-T024.

Validates the three-scenario decision framework, intermediate state tracing across
all 5 pipeline steps, formal invariant verification linking intermediate states
to final outputs, decision table tamper detection, and subprocess CLI executions.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from typing import Any, Dict, List

# Ensure lab directory is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from example import (
    PUBLISHED_DECISION_TABLE,
    Decision,
    DecisionMismatchError,
    IntermediateState,
    InvariantViolationError,
    PipelineStep,
    StepStatus,
    check_decision_table,
    run_text_generation_pipeline,
    verify_allergen_exclusion_invariant,
    verify_context_chaining_lineage_invariant,
    verify_terminal_state_monotonicity_invariant,
    verify_token_conservation_invariant,
)


class TestIntermediateStateTracing(unittest.TestCase):
    """Tests the state machine recording intermediate state after each discrete step."""

    def test_normal_scenario_records_all_five_steps(self) -> None:
        """Verifies that the normal scenario traces exactly 5 sequential steps."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            scenario_type="normal",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )

        self.assertEqual(len(output.state_trace), 5)
        for idx, expected_step in enumerate([
            PipelineStep.STEP_1_VALIDATION_AND_CONFIG,
            PipelineStep.STEP_2_PROMPT_CONSTRUCTION,
            PipelineStep.STEP_3_PRIMARY_GENERATION,
            PipelineStep.STEP_4_CONTEXT_CHAINING,
            PipelineStep.STEP_5_FINAL_ASSEMBLY,
        ], start=1):
            state = output.state_trace[idx - 1]
            self.assertEqual(state.step_index, idx)
            self.assertEqual(state.step_name, expected_step)
            self.assertEqual(state.status, StepStatus.SUCCESS)

    def test_step_payload_contents(self) -> None:
        """Verifies specific payloads captured across intermediate states in normal scenario."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )

        trace = output.state_trace
        # Step 1
        self.assertTrue(trace[0].payload["api_secrets_verified"])
        self.assertEqual(trace[0].payload["model_id"], "gpt-5-mini")
        self.assertEqual(trace[0].payload["model_family"], "reasoning")
        self.assertIsNone(trace[0].payload["temperature"])

        # Step 2
        self.assertIn("garlic", trace[1].payload["prompt_text"])
        self.assertIn("Show me 3 recipes", trace[1].payload["prompt_text"])

        # Step 3
        self.assertIn("recipe_text", trace[2].payload)
        self.assertEqual(trace[2].step_tokens_generated, 240)
        self.assertEqual(trace[2].cumulative_tokens, 240)

        # Step 4
        self.assertIn("shopping_list_text", trace[3].payload)
        self.assertEqual(trace[3].step_tokens_generated, 110)
        self.assertEqual(trace[3].cumulative_tokens, 350)
        self.assertIn("olive oil", trace[3].payload["shopping_list_text"].lower())

        # Step 5
        self.assertEqual(trace[4].payload["decision"], Decision.EXECUTE_REASONING_PIPELINE.value)
        self.assertEqual(trace[4].payload["total_tokens_consumed"], 350)

    def test_boundary_scenario_records_boundary_saturation_in_step_4(self) -> None:
        """Verifies boundary scenario traces step 4 with BOUNDARY_SATURATED status."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_BOUNDARY"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_BOUNDARY",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )

        self.assertEqual(len(output.state_trace), 5)
        step4 = output.state_trace[3]
        self.assertEqual(step4.step_name, PipelineStep.STEP_4_CONTEXT_CHAINING)
        self.assertEqual(step4.status, StepStatus.BOUNDARY_SATURATED)
        self.assertEqual(step4.payload["reason"], "INSUFFICIENT_TOKEN_HEADROOM_AT_BOUNDARY")
        self.assertEqual(step4.payload["tokens_remaining"], 0)
        self.assertEqual(output.total_tokens_consumed, 150)
        self.assertEqual(output.token_budget, 150)

    def test_missing_info_records_halt_and_skips_downstream(self) -> None:
        """Verifies missing-information scenario records HALTED in step 1 and SKIPPED for 2-5."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_MISSING",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )

        self.assertEqual(len(output.state_trace), 5)
        self.assertEqual(output.state_trace[0].status, StepStatus.HALTED)
        for s in output.state_trace[1:]:
            self.assertEqual(s.status, StepStatus.SKIPPED)
            self.assertEqual(s.payload.get("reason"), "PREVIOUS_STEP_HALTED")
        self.assertEqual(output.total_tokens_consumed, 0)
        self.assertIsNone(output.final_text)


class TestStateInvariants(unittest.TestCase):
    """Tests each formal invariant linking intermediate states to final outputs."""

    def test_token_conservation_invariant_valid(self) -> None:
        """Token conservation holds when step sums equal total tokens and within budget."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        ok, msg = verify_token_conservation_invariant(
            output.state_trace, output.total_tokens_consumed, output.token_budget
        )
        self.assertTrue(ok)
        self.assertIn("Token conservation holds", msg)

    def test_token_conservation_invariant_fails_on_tampered_step_tokens(self) -> None:
        """Token conservation fails if an intermediate step's tokens are tampered with."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        # Mutate intermediate step tokens
        output.state_trace[2].step_tokens_generated = 999
        ok, msg = verify_token_conservation_invariant(
            output.state_trace, output.total_tokens_consumed, output.token_budget
        )
        self.assertFalse(ok)
        self.assertIn("Token mismatch", msg)

    def test_token_budget_exceeded_fails_invariant(self) -> None:
        """Token conservation fails if total tokens exceeds the configured budget."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        # Check against an artificially tiny budget
        ok, msg = verify_token_conservation_invariant(
            output.state_trace, output.total_tokens_consumed, token_budget=100
        )
        self.assertFalse(ok)
        self.assertIn("Token budget exceeded", msg)

    def test_allergen_exclusion_invariant_valid(self) -> None:
        """Allergen exclusion holds when excluded allergen is strictly absent."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        ok, msg = verify_allergen_exclusion_invariant(
            "garlic", output.state_trace, output.final_text
        )
        self.assertTrue(ok)
        self.assertIn("strictly absent", msg)

    def test_allergen_exclusion_invariant_fails_on_leak(self) -> None:
        """Allergen exclusion fails if an allergen leaks into intermediate recipe text."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        # Deliberately inject leaked allergen into Step 3
        output.state_trace[2].payload["recipe_text"] += "\n- 2 cloves minced garlic"
        ok, msg = verify_allergen_exclusion_invariant(
            "garlic", output.state_trace, output.final_text
        )
        self.assertFalse(ok)
        self.assertIn("leaked into Step 3", msg)

    def test_context_chaining_lineage_invariant_valid(self) -> None:
        """Context chaining lineage holds when Step 4 embeds Step 3 text and pantry is disjoint."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        pantry = entry["facts"]["prompt_inputs"]["ingredients"]
        ok, msg = verify_context_chaining_lineage_invariant(
            True, pantry, output.state_trace, output.final_text
        )
        self.assertTrue(ok)
        self.assertIn("Chaining lineage intact", msg)

    def test_context_chaining_lineage_fails_when_lineage_broken(self) -> None:
        """Context chaining fails if Step 4 input prompt loses Step 3 recipe context."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        pantry = entry["facts"]["prompt_inputs"]["ingredients"]
        # Wipe chained input context in step 4
        output.state_trace[3].payload["chained_input_context"] = "Completely different text"
        ok, msg = verify_context_chaining_lineage_invariant(
            True, pantry, output.state_trace, output.final_text
        )
        self.assertFalse(ok)
        self.assertIn("Lineage broken", msg)

    def test_context_chaining_lineage_fails_when_pantry_item_in_shopping_list(self) -> None:
        """Context chaining fails if an ingredient in the pantry is included in shopping list."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        pantry = entry["facts"]["prompt_inputs"]["ingredients"]
        # Inject pantry item 'chicken' into shopping list
        output.state_trace[3].payload["shopping_list_items"].append("chicken")
        ok, msg = verify_context_chaining_lineage_invariant(
            True, pantry, output.state_trace, output.final_text
        )
        self.assertFalse(ok)
        self.assertIn("Shopping list includes already-owned pantry ingredients", msg)

    def test_terminal_state_monotonicity_invariant_valid(self) -> None:
        """Terminal state monotonicity holds on missing information scenario."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_MISSING",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        ok, msg = verify_terminal_state_monotonicity_invariant(
            output.state_trace, output.final_text, output.total_tokens_consumed
        )
        self.assertTrue(ok)
        self.assertIn("Terminal state monotonicity holds", msg)

    def test_terminal_state_monotonicity_fails_if_tokens_emitted_after_halt(self) -> None:
        """Terminal monotonicity fails if non-zero tokens are emitted despite halt."""
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="TEST_MISSING",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        ok, msg = verify_terminal_state_monotonicity_invariant(
            output.state_trace, output.final_text, total_tokens_consumed=50
        )
        self.assertFalse(ok)
        self.assertIn("Tokens consumed is non-zero after Step 1 HALT", msg)


class TestThreeScenarios(unittest.TestCase):
    """Tests the three canonical decision scenarios."""

    def test_normal_scenario_decision_and_rationale(self) -> None:
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_NORMAL"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="SCENARIO_NORMAL",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        self.assertEqual(output.decision, Decision.EXECUTE_REASONING_PIPELINE)
        self.assertIn("reasoning model", output.rationale.lower())
        self.assertIn("gpt-5-mini", output.rationale.lower())
        self.assertIn("chaining", output.rationale.lower())
        self.assertTrue(output.invariants_summary["all_invariants_hold"])

    def test_boundary_scenario_decision_and_rationale(self) -> None:
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_BOUNDARY"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="SCENARIO_BOUNDARY",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        self.assertEqual(output.decision, Decision.EXECUTE_SAMPLING_BOUNDARY_PIPELINE)
        self.assertIn("sampling", output.rationale.lower())
        self.assertIn("boundary", output.rationale.lower())
        self.assertIn("1.0", output.rationale.lower())
        self.assertTrue(output.invariants_summary["all_invariants_hold"])

    def test_missing_info_scenario_decision_and_rationale(self) -> None:
        entry = PUBLISHED_DECISION_TABLE["SCENARIO_MISSING_INFO"]
        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id="SCENARIO_MISSING_INFO",
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )
        self.assertEqual(output.decision, Decision.HALT_MISSING_PREREQUISITES)
        self.assertIn("missing", output.rationale.lower())
        self.assertIn("secrets", output.rationale.lower())
        self.assertIn("halt", output.rationale.lower())
        self.assertTrue(output.invariants_summary["all_invariants_hold"])


class TestPublishedDecisionTableAndChecker(unittest.TestCase):
    """Tests the published decision table checker and tamper detection."""

    def test_checker_passes_on_canonical_table(self) -> None:
        """Untouched published decision table must pass all checks."""
        report = check_decision_table(PUBLISHED_DECISION_TABLE, fail_on_tamper=True)
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["total_scenarios"], 3)
        self.assertEqual(report["passed_scenarios"], 3)
        self.assertEqual(report["failed_scenarios"], 0)

        for s in report["scenarios"]:
            self.assertEqual(s["status"], "PASS")
            self.assertTrue(s["matches_table"])
            self.assertTrue(s["rationale_valid"])
            self.assertTrue(s["invariants_hold"])

    def test_checker_fails_when_normal_decision_tampered(self) -> None:
        """Tampering with normal scenario expected decision raises DecisionMismatchError."""
        tampered = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered["SCENARIO_NORMAL"]["expected_decision"] = Decision.EXECUTE_SAMPLING_BOUNDARY_PIPELINE.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered, fail_on_tamper=True)

        self.assertIn("SCENARIO_NORMAL", str(ctx.exception))
        self.assertEqual(ctx.exception.expected, Decision.EXECUTE_SAMPLING_BOUNDARY_PIPELINE.value)
        self.assertEqual(ctx.exception.actual, Decision.EXECUTE_REASONING_PIPELINE.value)

    def test_checker_fails_when_boundary_decision_tampered(self) -> None:
        """Tampering with boundary scenario expected decision raises DecisionMismatchError."""
        tampered = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered["SCENARIO_BOUNDARY"]["expected_decision"] = Decision.EXECUTE_REASONING_PIPELINE.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered, fail_on_tamper=True)

        self.assertIn("SCENARIO_BOUNDARY", str(ctx.exception))

    def test_checker_fails_when_missing_info_decision_tampered(self) -> None:
        """Tampering with missing_info scenario expected decision raises DecisionMismatchError."""
        tampered = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered["SCENARIO_MISSING_INFO"]["expected_decision"] = Decision.EXECUTE_REASONING_PIPELINE.value

        with self.assertRaises(DecisionMismatchError) as ctx:
            check_decision_table(tampered, fail_on_tamper=True)

        self.assertIn("SCENARIO_MISSING_INFO", str(ctx.exception))

    def test_checker_soft_failure_reporting(self) -> None:
        """When fail_on_tamper=False, checker returns failure dict instead of raising."""
        tampered = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        tampered["SCENARIO_NORMAL"]["expected_decision"] = "MUTATED_DECISION"

        report = check_decision_table(tampered, fail_on_tamper=False)
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["status"], "failure")
        self.assertEqual(report["failed_scenarios"], 1)


class TestSubprocessCLIExecution(unittest.TestCase):
    """Tests CLI entrypoint and fresh-process execution."""

    def setUp(self) -> None:
        self.example_script = os.path.join(CURRENT_DIR, "example.py")

    def _run_cmd(self, args: List[str]) -> subprocess.CompletedProcess[str]:
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
        self.assertEqual(res.returncode, 0, f"Stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "EXECUTE_REASONING_PIPELINE")
        self.assertTrue(data["invariants_summary"]["all_invariants_hold"])

    def test_cli_scenario_boundary_exit_0(self) -> None:
        res = self._run_cmd(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0, f"Stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "EXECUTE_SAMPLING_BOUNDARY_PIPELINE")
        self.assertEqual(data["total_tokens_consumed"], 150)

    def test_cli_scenario_missing_exit_0(self) -> None:
        res = self._run_cmd(["--scenario", "missing"])
        self.assertEqual(res.returncode, 0, f"Stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "HALT_MISSING_PREREQUISITES")
        self.assertIsNone(data["final_text"])

    def test_cli_deliberate_tamper_fails_with_nonzero_exit(self) -> None:
        res = self._run_cmd(["--deliberate-tamper", "SCENARIO_NORMAL"])
        self.assertEqual(res.returncode, 1)
        self.assertIn("DecisionMismatchError caught", res.stderr)

    def test_cli_trace_flag(self) -> None:
        res = self._run_cmd(["--scenario", "normal", "--trace"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("state_trace", data)
        self.assertEqual(len(data["state_trace"]), 5)


if __name__ == "__main__":
    unittest.main()
