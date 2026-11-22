#!/usr/bin/env python3
"""Regression, invariant, and state trace test suite for R40-T004.

Lesson 15: Retrieval Augmented Generation (RAG) and Vector Databases
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    DEFAULT_DOCUMENTS,
    DecisionMismatchError,
    InvariantViolationError,
    SearchResult,
    TracingLexicalRetriever,
    run_canonical_check,
    run_normal_scenario,
    run_tie_scenario,
    run_zero_match_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestCoreRetrievalContract(unittest.TestCase):
    """Core retrieval assertions: rankings, tie-breaking, and empty results."""

    def setUp(self) -> None:
        self.retriever = TracingLexicalRetriever()

    def test_query_red_apple_ranks_a_before_b(self) -> None:
        results = self.retriever.search("red apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)

    def test_query_ocean_returns_no_match(self) -> None:
        results = self.retriever.search("ocean")
        self.assertEqual(len(results), 0)

    def test_tie_breaking_by_doc_id(self) -> None:
        results = self.retriever.search("apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].score, 1)


class TestIntermediateStateTraceAndInvariants(unittest.TestCase):
    """Focus: Inspects intermediate step state and validates linking invariants."""

    def setUp(self) -> None:
        self.retriever = TracingLexicalRetriever()

    def test_intermediate_trace_steps_recorded(self) -> None:
        results, trace = self.retriever.search_with_trace("red apple")
        self.assertEqual(len(trace), 5)
        step_names = [s["name"] for s in trace]
        expected_steps = [
            "query_tokenization",
            "candidate_scoring",
            "threshold_filtering",
            "rank_ordering",
            "attribution_projection",
        ]
        self.assertEqual(step_names, expected_steps)

    def test_invariant_scoring_fidelity(self) -> None:
        """Every returned document score must match the candidate_scoring raw score."""
        results, trace = self.retriever.search_with_trace("red apple")
        raw_scores = trace[1]["state"]["raw_scores"]
        for r in results:
            self.assertEqual(r.score, raw_scores[r.doc_id]["score"])

    def test_invariant_zero_pruned_from_output(self) -> None:
        """Zero score documents (e.g. Doc C with query 'red apple') must not be in results."""
        results, trace = self.retriever.search_with_trace("red apple")
        raw_scores = trace[1]["state"]["raw_scores"]
        self.assertEqual(raw_scores["C"]["score"], 0)
        result_ids = [r.doc_id for r in results]
        self.assertNotIn("C", result_ids)

    def test_tampered_trace_raises_invariant_violation(self) -> None:
        """Artificially corrupted scores trigger InvariantViolationError."""
        results, trace = self.retriever.search_with_trace("red apple")
        corrupted_results = [
            SearchResult(doc_id="A", score=99, text="red apple", matched_tokens=["red"])
        ]
        with self.assertRaises(InvariantViolationError):
            self.retriever._verify_invariants(trace, corrupted_results)


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Validates decision table verification and deliberate tamper detection."""

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
        self.assertEqual(data["decision"], "RANK_A_BEFORE_B")

    def test_cli_scenario_zero_match(self) -> None:
        res = self._run_cli(["--scenario", "zero_match"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "NO_MATCH_EMPTY_RESULT")

    def test_cli_scenario_tie(self) -> None:
        res = self._run_cli(["--scenario", "tie"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "TIE_BROKEN_A_BEFORE_B")

    def test_cli_trace(self) -> None:
        res = self._run_cli(["--trace", "red apple"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(len(data["trace"]), 5)

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
