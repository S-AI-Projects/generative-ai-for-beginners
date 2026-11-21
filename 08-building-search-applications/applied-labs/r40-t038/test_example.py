"""
Unit tests for R40-T038 Ranked Search with Stable Ties & Boundary Evaluation.
"""

from __future__ import annotations

import unittest

from example import (
    DEFAULT_CONTRACT_CORPUS,
    RankedTokenSearchEngine,
    SearchResult,
    get_boundary_case_matrix,
)


class TestRankedSearchContract(unittest.TestCase):
    """Core contract tests for RankedTokenSearchEngine."""

    def setUp(self) -> None:
        self.engine = RankedTokenSearchEngine(DEFAULT_CONTRACT_CORPUS)

    def test_query_red_matches_apple_and_berry_equally_with_stable_tie_break(self) -> None:
        """
        Contract requirement:
        Query 'red' matches 'red apple' and 'red berry' equally (score 1 each);
        stable ID order breaks the tie ('doc_1' before 'doc_2');
        'blue sky' scores zero and is omitted.
        """
        results = self.engine.search("red")

        self.assertEqual(len(results), 2)

        # Both match with score 1
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].score, 1)

        # Stable ID order: doc_1 ranked before doc_2
        self.assertEqual(results[0].doc_id, "doc_1")
        self.assertEqual(results[0].text, "red apple")

        self.assertEqual(results[1].doc_id, "doc_2")
        self.assertEqual(results[1].text, "red berry")

        # Confirm blue sky (doc_3) is omitted
        doc_ids = [r.doc_id for r in results]
        self.assertNotIn("doc_3", doc_ids)

    def test_score_ranking_differentiation(self) -> None:
        """Query 'red apple' scores 2 for doc_1 and 1 for doc_2."""
        results = self.engine.search("red apple")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "doc_1")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[1].doc_id, "doc_2")
        self.assertEqual(results[1].score, 1)


class TestBoundaryCasesAndSmallestValid(unittest.TestCase):
    """Focus requirements: Smallest valid case, threshold boundaries, and exact boundary decisions."""

    def test_smallest_valid_case(self) -> None:
        """Smallest valid case: Single character document ('a') and single token query ('a')."""
        engine = RankedTokenSearchEngine({"min_1": "a"})
        results = engine.search("a")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].doc_id, "min_1")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[0].text, "a")

    def test_threshold_boundary_exact_match(self) -> None:
        """
        Boundary decision: score >= min_score is inclusive.
        Documents scoring exactly min_score are included.
        """
        engine = RankedTokenSearchEngine({
            "one_match": "red",
            "two_match": "red apple",
            "zero_match": "blue",
        })

        # With min_score=2: only two_match is included
        results_min2 = engine.search("red apple", min_score=2)
        self.assertEqual(len(results_min2), 1)
        self.assertEqual(results_min2[0].doc_id, "two_match")
        self.assertEqual(results_min2[0].score, 2)

        # With min_score=1: both one_match and two_match are included
        results_min1 = engine.search("red apple", min_score=1)
        self.assertEqual(len(results_min1), 2)
        self.assertEqual([r.doc_id for r in results_min1], ["two_match", "one_match"])

    def test_boundary_zero_min_score_includes_zero_score_documents(self) -> None:
        """When min_score=0 is explicitly configured, even 0-score docs are included."""
        engine = RankedTokenSearchEngine({"a": "hello", "b": "world"}, default_min_score=0)
        results = engine.search("hello", min_score=0)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "a")
        self.assertEqual(results[0].score, 1)
        self.assertEqual(results[1].doc_id, "b")
        self.assertEqual(results[1].score, 0)

    def test_empty_and_whitespace_query_boundary(self) -> None:
        """Empty or whitespace-only queries produce empty results list."""
        engine = RankedTokenSearchEngine(DEFAULT_CONTRACT_CORPUS)
        self.assertEqual(engine.search(""), [])
        self.assertEqual(engine.search("     "), [])
        self.assertEqual(engine.search("!@#$%^"), [])

    def test_boundary_case_matrix_audit(self) -> None:
        """Verify the published boundary evaluation case matrix has all required categories."""
        matrix = get_boundary_case_matrix()
        categories = {case.category for case in matrix}

        self.assertIn("smallest_valid", categories)
        self.assertIn("threshold_boundary_exact", categories)
        self.assertIn("threshold_boundary_excluded", categories)
        self.assertIn("tie_breaking_boundary", categories)
        self.assertIn("empty_query_boundary", categories)
        self.assertIn("invalid_threshold", categories)


class TestInvalidCasesAndFailures(unittest.TestCase):
    """Failure scenario tests checking input validation and error handling."""

    def setUp(self) -> None:
        self.engine = RankedTokenSearchEngine(DEFAULT_CONTRACT_CORPUS)

    def test_invalid_query_type_raises_type_error(self) -> None:
        """Non-string query raises TypeError."""
        with self.assertRaises(TypeError):
            self.engine.search(12345)  # type: ignore

    def test_negative_threshold_raises_value_error(self) -> None:
        """Negative minimum score threshold raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.search("red", min_score=-1)
        self.assertIn("min_score must be a non-negative integer", str(ctx.exception))

    def test_invalid_doc_id_raises_value_error(self) -> None:
        """Empty or blank document ID raises ValueError."""
        with self.assertRaises(ValueError):
            self.engine.add_document("", "valid text")
        with self.assertRaises(ValueError):
            self.engine.add_document("   ", "valid text")

    def test_invalid_doc_text_raises_type_error(self) -> None:
        """Non-string document content raises TypeError."""
        with self.assertRaises(TypeError):
            self.engine.add_document("doc_new", 999)  # type: ignore


class TestDeliberateWrongAssertions(unittest.TestCase):
    """
    Deliberate wrong result checks to confirm that deviations immediately cause test failures.
    """

    def test_deliberate_wrong_tie_order_assertion_fails(self) -> None:
        """Asserting that doc_2 is ranked before doc_1 for query 'red' raises AssertionError."""
        engine = RankedTokenSearchEngine(DEFAULT_CONTRACT_CORPUS)
        results = engine.search("red")

        with self.assertRaises(AssertionError):
            self.assertEqual(results[0].doc_id, "doc_2")

    def test_deliberate_wrong_omission_assertion_fails(self) -> None:
        """Asserting that doc_3 ('blue sky') is included for query 'red' raises AssertionError."""
        engine = RankedTokenSearchEngine(DEFAULT_CONTRACT_CORPUS)
        results = engine.search("red")

        with self.assertRaises(AssertionError):
            self.assertIn("doc_3", [r.doc_id for r in results])


if __name__ == "__main__":
    unittest.main()
