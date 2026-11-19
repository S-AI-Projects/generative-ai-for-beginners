#!/usr/bin/env python3
"""Automated Test Suite for R40-T026: Lexical Retriever with Source Attribution.

Validates:
1. BaselineLexicalRetriever contract, scoring, ranking, tie-breaking, and empty match.
2. Extracted WordSetOverlapScorer tokenization and scoring responsibilities.
3. RefactoredLexicalRetriever contract preservation and dependency injection.
4. Before/after equivalence proof across canonical fixtures.
5. Equivalence tamper detection: deliberate wrong result makes the test fail.
6. Canonical decision table checker and tamper detection.
7. Fresh subprocess CLI execution and nonzero exit on failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from typing import List

from example import (
    DEFAULT_CORPUS,
    BaselineLexicalRetriever,
    DecisionMismatchError,
    Document,
    EquivalenceMismatchError,
    RefactoredLexicalRetriever,
    SearchResult,
    WordSetOverlapScorer,
    format_prompt_citations,
    prove_before_after_equivalence,
    run_decision_table_check,
)


class TestBaselineLexicalRetriever(unittest.TestCase):
    """Tests for the monolithic baseline retriever."""

    def setUp(self) -> None:
        self.retriever = BaselineLexicalRetriever(DEFAULT_CORPUS)

    def test_query_red_apple_ranks_a_before_b(self) -> None:
        """Query 'red apple' must score Doc A (2) before Doc B (1); Doc C omitted."""
        results = self.retriever.retrieve("red apple")
        self.assertEqual(len(results), 2)

        # Check rankings
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[0].text, "red apple")

        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)
        self.assertEqual(results[1].text, "green apple")

        # Ensure Doc C is omitted
        doc_ids = [r.doc_id for r in results]
        self.assertNotIn("C", doc_ids)

    def test_query_ocean_returns_no_match(self) -> None:
        """Query 'ocean' has zero overlap with all documents and must return empty list."""
        results = self.retriever.retrieve("ocean")
        self.assertEqual(results, [])

    def test_tie_breaking_by_doc_id(self) -> None:
        """Query 'apple' ties Doc A (1) and Doc B (1); breaks tie by doc_id ('A' < 'B')."""
        results = self.retriever.retrieve("apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)

    def test_case_insensitivity(self) -> None:
        """Uppercase query 'RED APPLE' must yield identical results to 'red apple'."""
        res_upper = self.retriever.retrieve("RED APPLE")
        res_lower = self.retriever.retrieve("red apple")
        self.assertEqual(res_upper, res_lower)

    def test_punctuation_handling(self) -> None:
        """Punctuation in query ('red, apple!') must be normalized away."""
        results = self.retriever.retrieve("red, apple!")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)

    def test_empty_and_whitespace_query(self) -> None:
        """Empty or whitespace queries must return empty list without error."""
        self.assertEqual(self.retriever.retrieve(""), [])
        self.assertEqual(self.retriever.retrieve("   "), [])
        self.assertEqual(self.retriever.retrieve("\t\n"), [])


class TestExtractedWordSetOverlapScorer(unittest.TestCase):
    """Tests for the extracted named responsibility: WordSetOverlapScorer."""

    def setUp(self) -> None:
        self.scorer = WordSetOverlapScorer()

    def test_tokenize_lowercase_word_sets(self) -> None:
        tokens = self.scorer.tokenize("Red Apple 123")
        self.assertEqual(tokens, {"red", "apple", "123"})

    def test_tokenize_punctuation_and_whitespace(self) -> None:
        tokens = self.scorer.tokenize("  green,  apple! ... ")
        self.assertEqual(tokens, {"green", "apple"})

    def test_tokenize_empty(self) -> None:
        self.assertEqual(self.scorer.tokenize(""), set())
        self.assertEqual(self.scorer.tokenize("   "), set())

    def test_score_tokens_cardinality(self) -> None:
        query_tokens = {"red", "apple"}
        doc_a_tokens = {"red", "apple"}
        doc_b_tokens = {"green", "apple"}
        doc_c_tokens = {"blue", "sky"}

        self.assertEqual(self.scorer.score_tokens(query_tokens, doc_a_tokens), 2)
        self.assertEqual(self.scorer.score_tokens(query_tokens, doc_b_tokens), 1)
        self.assertEqual(self.scorer.score_tokens(query_tokens, doc_c_tokens), 0)

    def test_score_tokens_empty(self) -> None:
        self.assertEqual(self.scorer.score_tokens(set(), {"apple"}), 0)
        self.assertEqual(self.scorer.score_tokens({"apple"}, set()), 0)

    def test_score_convenience_method(self) -> None:
        self.assertEqual(self.scorer.score("red apple", "red apple"), 2)
        self.assertEqual(self.scorer.score("red apple", "green apple"), 1)
        self.assertEqual(self.scorer.score("ocean", "blue sky"), 0)


class TestRefactoredLexicalRetriever(unittest.TestCase):
    """Tests for the refactored retriever composing WordSetOverlapScorer."""

    def setUp(self) -> None:
        self.retriever = RefactoredLexicalRetriever(DEFAULT_CORPUS)

    def test_query_red_apple_ranks_a_before_b(self) -> None:
        results = self.retriever.retrieve("red apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)

    def test_query_ocean_returns_no_match(self) -> None:
        results = self.retriever.retrieve("ocean")
        self.assertEqual(results, [])

    def test_tie_breaking_by_doc_id(self) -> None:
        results = self.retriever.retrieve("apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].score, 1)

    def test_custom_injected_scorer(self) -> None:
        custom_scorer = WordSetOverlapScorer()
        retriever = RefactoredLexicalRetriever(DEFAULT_CORPUS, scorer=custom_scorer)
        self.assertIs(retriever.scorer, custom_scorer)
        results = retriever.retrieve("red apple")
        self.assertEqual(len(results), 2)


class TestBeforeAfterEquivalenceAndTamper(unittest.TestCase):
    """Tests proving strict equivalence and verifying that deliberate wrong results fail."""

    def setUp(self) -> None:
        self.baseline = BaselineLexicalRetriever(DEFAULT_CORPUS)
        self.refactored = RefactoredLexicalRetriever(DEFAULT_CORPUS)
        self.queries = [
            "red apple",
            "ocean",
            "apple",
            "green apple",
            "blue sky",
            "red",
            "green",
            "blue",
            "apple sky",
            "",
            "   ",
            "RED, apple!",
        ]

    def test_before_after_equivalence_proven(self) -> None:
        """Baseline and refactored retrievers must yield 100% identical outputs."""
        report = prove_before_after_equivalence(self.baseline, self.refactored, self.queries)
        self.assertEqual(report["status"], "EQUIVALENCE_PROVEN")
        self.assertTrue(report["all_identical"])
        self.assertEqual(report["total_queries_tested"], len(self.queries))

    def test_deliberate_wrong_result_makes_equivalence_test_fail(self) -> None:
        """A deliberate alteration in ranking or scoring must trigger EquivalenceMismatchError."""
        # Create a mutated baseline that flips tie-breaking order
        class MutatedRetriever(BaselineLexicalRetriever):
            def retrieve(self, query: str) -> List[SearchResult]:
                res = super().retrieve(query)
                # Mutate tie-break order: sort doc_id descending instead of ascending
                res.sort(key=lambda r: (-r.score, -ord(r.doc_id[0])))
                return res

        mutated = MutatedRetriever(DEFAULT_CORPUS)
        # On query "apple", baseline returns [A, B] but mutated returns [B, A]
        with self.assertRaises(EquivalenceMismatchError):
            prove_before_after_equivalence(mutated, self.refactored, ["apple"])


class TestCanonicalDecisionTableAndChecker(unittest.TestCase):
    """Tests for the canonical decision table checker."""

    def test_checker_passes_on_canonical_table(self) -> None:
        report = run_decision_table_check()
        self.assertEqual(report["status"], "success")
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["total_scenarios"], 4)
        self.assertEqual(report["failed_scenarios"], 0)

    def test_checker_fails_when_decision_tampered(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_decision_table_check(tamper_scenario="SCENARIO_NORMAL")

    def test_checker_fails_when_boundary_tampered(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_decision_table_check(tamper_scenario="SCENARIO_BOUNDARY")

    def test_checker_fails_when_doc_ids_tampered(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_decision_table_check(
                tamper_scenario="SCENARIO_NORMAL",
                tamper_field="doc_ids",
            )


class TestCitationFormatting(unittest.TestCase):
    """Tests for prompt citation and source attribution formatting."""

    def test_format_citations_with_results(self) -> None:
        results = [
            SearchResult(doc_id="A", score=2, text="red apple"),
            SearchResult(doc_id="B", score=1, text="green apple"),
        ]
        citation = format_prompt_citations(results)
        self.assertIn("[Source A] (Score: 2): red apple", citation)
        self.assertIn("[Source B] (Score: 1): green apple", citation)

    def test_format_citations_empty(self) -> None:
        self.assertEqual(format_prompt_citations([]), "No relevant context found.")


class TestSubprocessCLIExecution(unittest.TestCase):
    """Tests running example.py in fresh subprocesses."""

    def setUp(self) -> None:
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.example_script = os.path.join(
            self.repo_root, "20-mistral", "applied-labs", "r40-t026", "example.py"
        )

    def _run(self, args: List[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, self.example_script] + args
        return subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)

    def test_cli_scenario_normal_exit_0(self) -> None:
        res = self._run(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "RETRIEVAL_SUCCESS_RANKED")
        self.assertEqual(data["doc_ids"], ["A", "B"])
        self.assertEqual(data["scores"], [2, 1])

    def test_cli_scenario_boundary_exit_0(self) -> None:
        res = self._run(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "EMPTY_RESULT_NO_MATCH")
        self.assertEqual(data["doc_ids"], [])

    def test_cli_scenario_tiebreak_exit_0(self) -> None:
        res = self._run(["--scenario", "tiebreak"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "RETRIEVAL_TIEBREAK_RESOLVED")
        self.assertEqual(data["doc_ids"], ["A", "B"])

    def test_cli_check_all_exit_0(self) -> None:
        res = self._run(["--check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_scenarios"], 4)

    def test_cli_prove_equivalence_exit_0(self) -> None:
        res = self._run(["--prove-equivalence"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_identical"])

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        """The --tamper flag must intentionally trigger an error and exit with code 1."""
        res = self._run(["--tamper"])
        self.assertEqual(res.returncode, 1)
        self.assertIn("[EXPECTED FAILURE CONFIRMED]", res.stdout)


if __name__ == "__main__":
    unittest.main()
