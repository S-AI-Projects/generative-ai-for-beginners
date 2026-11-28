#!/usr/bin/env python3
"""Tests for the r40-t055 lexical-retriever example.

These tests exercise the stated contract:
  - normal scenario: query "red apple" ranks document A before B
  - boundary scenarios: a tie broken by document ID, case/word-order
    normalization, an empty-string query
  - failure scenarios: a non-match query returns no results; a non-string
    query is rejected; a corpus with duplicate document IDs is rejected
  - the task's focus: the external dependency is used only through the
    callable Retriever interface (run_retrieval), with
    LocalLexicalRetriever as its deterministic local adapter
  - a deliberately wrong result is rejected by assertion

Run from the repository root:
    python3 -m unittest discover -s 20-mistral/applied-labs/r40-t055 -p "test_*.py"
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from example import (  # noqa: E402
    DOCUMENTS,
    Document,
    LocalLexicalRetriever,
    RetrievalResult,
    UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
    run_retrieval,
)


class NormalScenario(unittest.TestCase):
    """Query 'red apple' ranks document A before B; C is excluded."""

    def setUp(self):
        self.retriever = LocalLexicalRetriever(list(DOCUMENTS))

    def test_red_apple_ranks_a_before_b(self):
        results = run_retrieval(self.retriever, "red apple")
        self.assertEqual([r.doc_id for r in results], ["A", "B"])

    def test_scores_reflect_word_overlap(self):
        results = run_retrieval(self.retriever, "red apple")
        by_id = {r.doc_id: r.score for r in results}
        self.assertEqual(by_id["A"], 2)  # "red" and "apple" both match
        self.assertEqual(by_id["B"], 1)  # only "apple" matches

    def test_document_c_excluded_from_red_apple_query(self):
        results = run_retrieval(self.retriever, "red apple")
        self.assertNotIn("C", [r.doc_id for r in results])

    def test_results_name_their_source_document(self):
        # The "citations" lesson concept: every result is traceable to a doc_id.
        results = run_retrieval(self.retriever, "red apple")
        for result in results:
            self.assertIn(result.doc_id, {"A", "B", "C"})

    def test_wrong_ranking_is_not_silently_accepted(self):
        # A deliberately wrong expectation (B before A) must fail.
        results = run_retrieval(self.retriever, "red apple")
        wrong_order = ["B", "A"]
        self.assertNotEqual([r.doc_id for r in results], wrong_order)
        self.assertEqual([r.doc_id for r in results], ["A", "B"])


class BoundaryScenario(unittest.TestCase):
    """Tie-break by document ID, normalization, and empty-string query."""

    def setUp(self):
        self.retriever = LocalLexicalRetriever(list(DOCUMENTS))

    def test_tie_is_broken_by_ascending_document_id(self):
        # "apple" overlaps A and B with an identical score of 1; the tie
        # must be broken by doc_id, i.e. A before B.
        results = run_retrieval(self.retriever, "apple")
        self.assertEqual([r.doc_id for r in results], ["A", "B"])
        self.assertEqual(results[0].score, results[1].score)

    def test_query_is_normalized_for_case_and_word_order(self):
        results = run_retrieval(self.retriever, "APPLE RED")
        self.assertEqual([r.doc_id for r in results], ["A", "B"])
        self.assertEqual({r.doc_id: r.score for r in results}["A"], 2)

    def test_empty_string_query_returns_no_match(self):
        results = run_retrieval(self.retriever, "")
        self.assertEqual(results, [])

    def test_single_matching_document(self):
        results = run_retrieval(self.retriever, "sky")
        self.assertEqual([r.doc_id for r in results], ["C"])


class FailureScenario(unittest.TestCase):
    """A non-match returns no results; invalid inputs are rejected."""

    def setUp(self):
        self.retriever = LocalLexicalRetriever(list(DOCUMENTS))

    def test_ocean_query_returns_no_match(self):
        results = run_retrieval(self.retriever, "ocean")
        self.assertEqual(results, [])

    def test_non_string_query_raises_type_error(self):
        with self.assertRaises(TypeError):
            run_retrieval(self.retriever, None)

    def test_duplicate_document_ids_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            LocalLexicalRetriever(
                [Document(doc_id="A", text="red apple"), Document(doc_id="A", text="green apple")]
            )


class CallableInterfaceScenario(unittest.TestCase):
    """The task's focus: the external dependency sits behind a callable
    interface, with a deterministic local adapter supplied for it."""

    def test_run_retrieval_only_needs_a_callable(self):
        # Any callable matching the Retriever interface works -- run_retrieval
        # never references LocalLexicalRetriever by name.
        def fake_retriever(query: str) -> list[RetrievalResult]:
            return [RetrievalResult(doc_id="Z", score=99)]

        results = run_retrieval(fake_retriever, "anything")
        self.assertEqual(results, [RetrievalResult(doc_id="Z", score=99)])

    def test_local_adapter_is_deterministic_across_repeated_calls(self):
        retriever = LocalLexicalRetriever(list(DOCUMENTS))
        first = run_retrieval(retriever, "red apple")
        second = run_retrieval(retriever, "red apple")
        self.assertEqual(first, second)

    def test_unestablished_behaviors_are_documented(self):
        # The mock must explicitly name what it does not establish about a
        # real retrieval service.
        self.assertGreater(len(UNESTABLISHED_REAL_SERVICE_BEHAVIORS), 0)
        for behavior in UNESTABLISHED_REAL_SERVICE_BEHAVIORS:
            self.assertIsInstance(behavior, str)
            self.assertTrue(behavior)


if __name__ == "__main__":
    unittest.main()
