#!/usr/bin/env python3
"""Regression and invariant test suite for R40-T002.

Lesson 20: Building with Mistral Models
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
    LexicalRetriever,
    run_boundary_tie_scenario,
    run_boundary_zero_match_scenario,
    run_canonical_check,
    run_invalid_case_scenario,
    run_normal_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestLexicalRetrieverCoreContract(unittest.TestCase):
    """Core retrieval contract: ranking, tie-breaking, and zero match."""

    def setUp(self) -> None:
        self.retriever = LexicalRetriever()

    def test_query_red_apple_ranks_a_before_b(self) -> None:
        """Query 'red apple' ranks A (score 2) before B (score 1)."""
        results = self.retriever.search("red apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[0].text, "red apple")

        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)
        self.assertEqual(results[1].text, "green apple")

    def test_query_ocean_returns_no_match(self) -> None:
        """Query 'ocean' returns an empty result list."""
        results = self.retriever.search("ocean")
        self.assertEqual(len(results), 0)

    def test_tie_breaking_by_doc_id(self) -> None:
        """Query 'apple' matches A and B with score 1; tie broken alphabetically by doc_id."""
        results = self.retriever.search("apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)

    def test_case_and_whitespace_insensitivity(self) -> None:
        """Mixed case and padded whitespace produce identical ranking."""
        results = self.retriever.search("   RED   APPLE  ")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)


class TestBoundaryAndInvalidCases(unittest.TestCase):
    """Boundary-case lesson extension: smallest valid, boundary, and invalid inputs."""

    def setUp(self) -> None:
        self.retriever = LexicalRetriever()

    def test_smallest_valid_query(self) -> None:
        """Single matching token is the smallest valid query."""
        results = self.retriever.search("sky")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].doc_id, "C")
        self.assertEqual(results[0].score, 1)

    def test_empty_and_whitespace_queries_fail(self) -> None:
        """Empty query or whitespace-only query raises ValueError."""
        with self.assertRaises(ValueError):
            self.retriever.search("")
        with self.assertRaises(ValueError):
            self.retriever.search("     ")

    def test_invalid_query_type_fails(self) -> None:
        """Non-string query raises TypeError."""
        with self.assertRaises(TypeError):
            self.retriever.search(12345)  # type: ignore
        with self.assertRaises(TypeError):
            self.retriever.search(None)  # type: ignore

    def test_empty_corpus_fails(self) -> None:
        """Empty corpus dictionary raises ValueError."""
        with self.assertRaises(ValueError):
            LexicalRetriever({})


class TestScenarioHelpersAndDecisionTable(unittest.TestCase):
    """Verifies scenario helper functions and canonical check behavior."""

    def test_run_normal_scenario(self) -> None:
        res = run_normal_scenario()
        self.assertEqual(res["decision"], "RANK_A_BEFORE_B")
        self.assertEqual(res["doc_ids"], ["A", "B"])
        self.assertTrue(res["contract_satisfied"])

    def test_run_boundary_zero_match_scenario(self) -> None:
        res = run_boundary_zero_match_scenario()
        self.assertEqual(res["decision"], "NO_MATCH_EMPTY_RESULT")
        self.assertEqual(len(res["results"]), 0)
        self.assertTrue(res["contract_satisfied"])

    def test_run_boundary_tie_scenario(self) -> None:
        res = run_boundary_tie_scenario()
        self.assertEqual(res["decision"], "TIE_BROKEN_A_BEFORE_B")
        self.assertEqual(res["doc_ids"], ["A", "B"])
        self.assertTrue(res["contract_satisfied"])

    def test_run_invalid_case_scenario(self) -> None:
        res = run_invalid_case_scenario()
        self.assertEqual(res["decision"], "INVALID_INPUTS_REJECTED")
        self.assertTrue(res["contract_satisfied"])

    def test_canonical_check_passes(self) -> None:
        summary = run_canonical_check(tamper=False)
        self.assertEqual(summary["status"], "success")
        self.assertTrue(summary["all_passed"])
        self.assertEqual(summary["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateFailure(unittest.TestCase):
    """Verifies that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI subprocess execution."""

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
