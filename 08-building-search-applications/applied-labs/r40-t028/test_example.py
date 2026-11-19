#!/usr/bin/env python3
"""Automated regression test suite for R40-T028.

Lesson 08: Building a Search Applications.
Focus: Ranked search with stable ties, source ID provenance, threshold filtering,
and failure/recovery on invalid/missing inputs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    DEFAULT_CORPUS,
    DEFAULT_MIN_SCORE,
    DEFAULT_QUERY,
    CorpusValidationError,
    DecisionMismatchError,
    Document,
    InvalidQueryError,
    InvalidThresholdError,
    MissingDataError,
    RankedSearchEngine,
    SearchResult,
    run_boundary_scenario,
    run_canonical_check,
    run_failure_scenario,
    run_normal_scenario,
    run_recovery_scenario,
)

EXAMPLE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.py")


class TestRankedSearchEngine(unittest.TestCase):
    """Unit tests for the core ranked search algorithm, invariants, and provenance."""

    def setUp(self) -> None:
        self.engine = RankedSearchEngine(DEFAULT_CORPUS)

    def test_normal_search_contract(self) -> None:
        """Query 'red' matches 'red apple' and 'red berry' equally with score 1.0;
        stable ID breaks tie ('doc-01' before 'doc-02'); 'blue sky' (0.0) is omitted."""
        results = self.engine.search("red", min_score=0.1)

        self.assertEqual(len(results), 2)
        # Top result: doc-01
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[0].id, "doc-01")
        self.assertEqual(results[0].score, 1.0)
        self.assertEqual(results[0].text, "red apple")
        self.assertEqual(results[0].matched_tokens, ["red"])

        # Second result: doc-02
        self.assertEqual(results[1].rank, 2)
        self.assertEqual(results[1].id, "doc-02")
        self.assertEqual(results[1].score, 1.0)
        self.assertEqual(results[1].text, "red berry")
        self.assertEqual(results[1].matched_tokens, ["red"])

        # Omission of zero score
        result_ids = [r.id for r in results]
        self.assertNotIn("doc-03", result_ids)

    def test_exact_tie_score(self) -> None:
        """Confirms that both tied documents receive identical overlap scores."""
        results = self.engine.search("red", min_score=0.1)
        self.assertEqual(results[0].score, results[1].score)
        self.assertEqual(results[0].score, 1.0)

    def test_tie_breaking_order_invariance(self) -> None:
        """Inverting corpus insertion order [doc-02, doc-01, doc-03] must still
        yield doc-01 before doc-02 due to stable ID tie-breaking."""
        inverted_corpus = [
            {"id": "doc-02", "text": "red berry"},
            {"id": "doc-01", "text": "red apple"},
            {"id": "doc-03", "text": "blue sky"},
        ]
        inverted_engine = RankedSearchEngine(inverted_corpus)
        results = inverted_engine.search("red", min_score=0.1)

        self.assertEqual([r.id for r in results], ["doc-01", "doc-02"])
        self.assertEqual(results[0].id, "doc-01")
        self.assertEqual(results[1].id, "doc-02")

    def test_blue_sky_zero_score_omission_by_threshold(self) -> None:
        """When min_score > 0 (e.g. 0.1), doc-03 ('blue sky') is excluded;
        when min_score == 0.0, doc-03 is included at the end."""
        results_thresholded = self.engine.search("red", min_score=0.1)
        self.assertNotIn("doc-03", [r.id for r in results_thresholded])

        results_zero_thresh = self.engine.search("red", min_score=0.0)
        self.assertEqual(len(results_zero_thresh), 3)
        self.assertEqual(results_zero_thresh[2].id, "doc-03")
        self.assertEqual(results_zero_thresh[2].score, 0.0)

    def test_source_id_provenance(self) -> None:
        """Every result preserves and returns source ID, score, and text."""
        results = self.engine.search("red", min_score=0.1)
        for r in results:
            self.assertIsInstance(r.id, str)
            self.assertTrue(r.id.startswith("doc-"))
            self.assertGreater(r.score, 0.0)
            self.assertIsInstance(r.text, str)
            self.assertIn("red", r.matched_tokens)

    def test_multi_token_query_scoring(self) -> None:
        """Query 'red apple' has 2 overlapping tokens with doc-01 and 1 with doc-02."""
        results = self.engine.search("red apple", min_score=0.1)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "doc-01")
        self.assertEqual(results[0].score, 2.0)
        self.assertEqual(results[1].id, "doc-02")
        self.assertEqual(results[1].score, 1.0)

    def test_case_insensitivity(self) -> None:
        """Uppercase query 'RED' behaves identically to lowercase 'red'."""
        results = self.engine.search("RED", min_score=0.1)
        self.assertEqual([r.id for r in results], ["doc-01", "doc-02"])

    def test_whitespace_and_punctuation_tokenization(self) -> None:
        """Punctuation in query and documents does not disrupt token matching."""
        results = self.engine.search("  red!  ", min_score=0.1)
        self.assertEqual([r.id for r in results], ["doc-01", "doc-02"])

    def test_zero_match_query(self) -> None:
        """Query matching zero documents returns an empty list without error."""
        results = self.engine.search("yellow", min_score=0.1)
        self.assertEqual(results, [])

    def test_high_threshold_filtering(self) -> None:
        """min_score higher than maximum overlap filters all documents."""
        results = self.engine.search("red", min_score=10.0)
        self.assertEqual(results, [])

    def test_empty_corpus(self) -> None:
        """Searching an empty corpus gracefully returns an empty list."""
        empty_engine = RankedSearchEngine([])
        results = empty_engine.search("red", min_score=0.1)
        self.assertEqual(results, [])


class TestInvalidAndMissingData(unittest.TestCase):
    """Unit tests for input validation, missing data detection, and error taxonomy."""

    def setUp(self) -> None:
        self.engine = RankedSearchEngine(DEFAULT_CORPUS)

    def test_empty_query_raises_invalid_query_error(self) -> None:
        """Empty query string '' raises InvalidQueryError."""
        with self.assertRaises(InvalidQueryError) as ctx:
            self.engine.search("", min_score=0.1)
        self.assertIn("missing or empty", str(ctx.exception))
        self.assertEqual(ctx.exception.reason, "empty_query_string")

    def test_whitespace_only_query_raises_invalid_query_error(self) -> None:
        """Whitespace query '   ' raises InvalidQueryError."""
        with self.assertRaises(InvalidQueryError) as ctx:
            self.engine.search("   ", min_score=0.1)
        self.assertEqual(ctx.exception.reason, "empty_query_string")

    def test_none_query_raises_invalid_query_error(self) -> None:
        """None query raises InvalidQueryError."""
        with self.assertRaises(InvalidQueryError) as ctx:
            self.engine.search(None, min_score=0.1)
        self.assertEqual(ctx.exception.reason, "missing_or_null_query")

    def test_non_string_query_raises_invalid_query_error(self) -> None:
        """Non-string query raises InvalidQueryError."""
        with self.assertRaises(InvalidQueryError) as ctx:
            self.engine.search(12345, min_score=0.1)
        self.assertEqual(ctx.exception.reason, "invalid_query_type")

    def test_punctuation_only_query_raises_invalid_query_error(self) -> None:
        """Query with no alphanumeric tokens raises InvalidQueryError."""
        with self.assertRaises(InvalidQueryError) as ctx:
            self.engine.search("!@#$%^&*()", min_score=0.1)
        self.assertEqual(ctx.exception.reason, "no_alphanumeric_tokens")

    def test_negative_threshold_raises_invalid_threshold_error(self) -> None:
        """Negative min_score raises InvalidThresholdError."""
        with self.assertRaises(InvalidThresholdError):
            self.engine.search("red", min_score=-0.5)

    def test_non_numeric_threshold_raises_invalid_threshold_error(self) -> None:
        """Non-numeric min_score raises InvalidThresholdError."""
        with self.assertRaises(InvalidThresholdError):
            self.engine.search("red", min_score="high")  # type: ignore

    def test_corpus_missing_id_field(self) -> None:
        """Corpus document missing 'id' raises MissingDataError."""
        bad_corpus = [{"text": "red apple"}]
        with self.assertRaises(MissingDataError) as ctx:
            RankedSearchEngine(bad_corpus)
        self.assertEqual(ctx.exception.field_name, "id")

    def test_corpus_empty_id_field(self) -> None:
        """Corpus document with blank string 'id' raises MissingDataError."""
        bad_corpus = [{"id": "   ", "text": "red apple"}]
        with self.assertRaises(MissingDataError) as ctx:
            RankedSearchEngine(bad_corpus)
        self.assertEqual(ctx.exception.field_name, "id")

    def test_corpus_missing_text_field(self) -> None:
        """Corpus document missing 'text' raises MissingDataError."""
        bad_corpus = [{"id": "doc-01"}]
        with self.assertRaises(MissingDataError) as ctx:
            RankedSearchEngine(bad_corpus)
        self.assertEqual(ctx.exception.field_name, "text")

    def test_corpus_non_string_text_field(self) -> None:
        """Corpus document with non-string 'text' raises MissingDataError."""
        bad_corpus = [{"id": "doc-01", "text": 42}]
        with self.assertRaises(MissingDataError) as ctx:
            RankedSearchEngine(bad_corpus)
        self.assertEqual(ctx.exception.field_name, "text")

    def test_corpus_duplicate_ids(self) -> None:
        """Corpus documents with duplicate IDs raise CorpusValidationError."""
        bad_corpus = [
            {"id": "doc-01", "text": "red apple"},
            {"id": "doc-01", "text": "duplicate red apple"},
        ]
        with self.assertRaises(CorpusValidationError) as ctx:
            RankedSearchEngine(bad_corpus)
        self.assertIn("Duplicate document ID", str(ctx.exception))

    def test_corpus_not_a_list(self) -> None:
        """Corpus passed as a dict raises CorpusValidationError."""
        with self.assertRaises(CorpusValidationError):
            RankedSearchEngine({"doc-01": "red apple"})  # type: ignore


class TestFailureAndRecoveryWorkflow(unittest.TestCase):
    """Unit tests verifying state preservation and recovery on subsequent valid inputs."""

    def setUp(self) -> None:
        self.engine = RankedSearchEngine(DEFAULT_CORPUS)

    def test_invalid_query_then_valid_recovery(self) -> None:
        """Interleaved invalid queries must not corrupt subsequent valid searches."""
        # 1. Invalid input fails
        with self.assertRaises(InvalidQueryError):
            self.engine.search("", min_score=0.1)

        # 2. Subsequent valid input succeeds cleanly
        results = self.engine.search("red", min_score=0.1)
        self.assertEqual(len(results), 2)
        self.assertEqual([r.id for r in results], ["doc-01", "doc-02"])

    def test_multiple_failures_then_recovery(self) -> None:
        """Multiple consecutive errors of different kinds must not leak state."""
        bad_inputs = ["", None, "   ", "???", "---"]
        for bad in bad_inputs:
            with self.assertRaises(InvalidQueryError):
                self.engine.search(bad, min_score=0.1)

        # Engine recovers completely
        results = self.engine.search("red", min_score=0.1)
        self.assertEqual([r.id for r in results], ["doc-01", "doc-02"])
        self.assertEqual(results[0].score, 1.0)
        self.assertEqual(results[1].score, 1.0)

    def test_engine_documents_unmodified_by_queries(self) -> None:
        """Query executions (whether valid or invalid) do not mutate the internal corpus."""
        initial_doc_count = len(self.engine.documents)
        try:
            self.engine.search("", min_score=0.1)
        except InvalidQueryError:
            pass
        self.engine.search("red", min_score=0.1)
        self.assertEqual(len(self.engine.documents), initial_doc_count)


class TestCanonicalScenariosAndTamper(unittest.TestCase):
    """Unit tests validating canonical scenario runner functions and deliberate tamper detection."""

    def test_run_normal_scenario_output(self) -> None:
        data = run_normal_scenario()
        self.assertEqual(data["decision"], "RANKED_SEARCH_SUCCESS")
        self.assertEqual(data["results_count"], 2)
        self.assertEqual(data["omitted_count"], 1)
        self.assertEqual(data["results"][0]["id"], "doc-01")
        self.assertEqual(data["results"][1]["id"], "doc-02")
        self.assertTrue(data["tie_broken_by_stable_id"])
        self.assertTrue(data["zero_score_omitted"])

    def test_run_failure_scenario_output(self) -> None:
        data = run_failure_scenario()
        self.assertEqual(data["decision"], "INVALID_DATA_REJECTED")
        self.assertEqual(data["error_type"], "InvalidQueryError")
        self.assertTrue(data["rejection_verified"])
        self.assertTrue(data["engine_state_preserved"])

    def test_run_recovery_scenario_output(self) -> None:
        data = run_recovery_scenario()
        self.assertEqual(data["decision"], "ERROR_RECOVERY_SUCCESS")
        self.assertTrue(data["recovery_verified"])
        self.assertTrue(data["state_consistency_maintained"])
        self.assertEqual(data["recovery_step"]["top_id"], "doc-01")
        self.assertEqual(data["recovery_step"]["second_id"], "doc-02")

    def test_run_boundary_scenario_output(self) -> None:
        data = run_boundary_scenario()
        self.assertEqual(data["decision"], "BOUNDARY_INVARIANTS_VERIFIED")
        self.assertTrue(data["tie_score_equality_verified"])
        self.assertTrue(data["order_invariance_verified"])
        self.assertTrue(data["zero_score_exclusion_verified"])
        self.assertTrue(data["zero_match_query_handled"])

    def test_canonical_check_clean(self) -> None:
        data = run_canonical_check(tamper=False)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_scenarios"], 4)
        self.assertEqual(data["passed_scenarios"], 4)
        self.assertEqual(data["failed_scenarios"], 0)
        self.assertTrue(data["all_passed"])

    def test_deliberate_tamper_fails_check(self) -> None:
        """Verifies that a deliberate mutation in the specification strictly raises DecisionMismatchError."""
        with self.assertRaises(DecisionMismatchError) as ctx:
            run_canonical_check(tamper=True)
        self.assertIn("Verification failed", str(ctx.exception))


class TestCLIExecution(unittest.TestCase):
    """Subprocess tests ensuring that fresh CLI invocations produce the expected exit codes and JSON."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal(self) -> None:
        proc = self._run_cli(["--scenario", "normal"])
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "RANKED_SEARCH_SUCCESS")
        self.assertEqual(data["results_count"], 2)

    def test_cli_scenario_failure(self) -> None:
        proc = self._run_cli(["--scenario", "failure"])
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "INVALID_DATA_REJECTED")
        self.assertEqual(data["error_type"], "InvalidQueryError")

    def test_cli_scenario_recovery(self) -> None:
        proc = self._run_cli(["--scenario", "recovery"])
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "ERROR_RECOVERY_SUCCESS")

    def test_cli_scenario_boundary(self) -> None:
        proc = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "BOUNDARY_INVARIANTS_VERIFIED")

    def test_cli_check(self) -> None:
        proc = self._run_cli(["--check"])
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_nonzero_exit(self) -> None:
        """Verifies that deliberate tamper flag triggers nonzero exit (exit 1) and JSON on stderr."""
        proc = self._run_cli(["--tamper"])
        self.assertEqual(proc.returncode, 1)
        err_data = json.loads(proc.stderr)
        self.assertEqual(err_data["status"], "expected_tamper_failure")
        self.assertEqual(err_data["error_type"], "DecisionMismatchError")
        self.assertEqual(err_data["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
