"""
Unit tests for R40-T033 Tiny Lexical Retriever with Source Attribution.
"""

from __future__ import annotations

import unittest

from example import (
    SearchResult,
    TinyLexicalRetriever,
    compare_retriever_with_oracle,
    reference_lexical_oracle,
)


class TestLexicalRetrieverContract(unittest.TestCase):
    """Core contract tests for TinyLexicalRetriever."""

    def setUp(self) -> None:
        self.corpus = {
            "A": "red apple",
            "B": "green apple",
            "C": "blue sky",
        }
        self.retriever = TinyLexicalRetriever(self.corpus)

    def test_query_red_apple_ranks_a_before_b(self) -> None:
        """
        Contract requirement:
        Documents A="red apple", B="green apple", C="blue sky";
        query "red apple" ranks A before B.
        Document C (zero overlap) is excluded.
        """
        results = self.retriever.retrieve("red apple")

        self.assertEqual(len(results), 2)

        # Rank 1: Doc A with score 2 ("red", "apple")
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[0].text, "red apple")

        # Rank 2: Doc B with score 1 ("apple")
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[1].score, 1)
        self.assertEqual(results[1].text, "green apple")

    def test_query_ocean_returns_no_match(self) -> None:
        """
        Contract requirement:
        query "ocean" returns no match (empty result list).
        """
        results = self.retriever.retrieve("ocean")
        self.assertEqual(results, [])

    def test_tie_breaking_by_doc_id(self) -> None:
        """
        Contract requirement:
        Ties in overlap score must be broken deterministically by document ID (ascending).
        """
        tie_corpus = {
            "DOC_Z": "golden fruit harvest",
            "DOC_A": "golden fruit basket",
            "DOC_M": "golden fruit garden",
        }
        retriever = TinyLexicalRetriever(tie_corpus)
        results = retriever.retrieve("golden fruit")

        # All 3 have score 2; alphabetical doc_id order should be DOC_A, DOC_M, DOC_Z
        self.assertEqual(len(results), 3)
        self.assertEqual([r.doc_id for r in results], ["DOC_A", "DOC_M", "DOC_Z"])
        self.assertEqual([r.score for r in results], [2, 2, 2])

    def test_case_insensitivity_and_punctuation_handling(self) -> None:
        """Query matching is case-insensitive and ignores punctuation."""
        results = self.retriever.retrieve("RED, APPLE!!!")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[0].score, 2)

    def test_empty_query_returns_empty_results(self) -> None:
        """Empty or whitespace-only query returns empty list."""
        self.assertEqual(self.retriever.retrieve(""), [])
        self.assertEqual(self.retriever.retrieve("    "), [])

    def test_invalid_query_type_raises_type_error(self) -> None:
        """Non-string query raises TypeError."""
        with self.assertRaises(TypeError):
            self.retriever.retrieve(123)  # type: ignore

    def test_invalid_document_inputs_raise_errors(self) -> None:
        """Invalid document IDs or texts raise appropriate errors."""
        with self.assertRaises(ValueError):
            self.retriever.add_document("", "valid text")
        with self.assertRaises(TypeError):
            self.retriever.add_document("D", 123)  # type: ignore


class TestFocusIndependentOracleComparison(unittest.TestCase):
    """
    Focus requirements:
    Compare the direct implementation with a simpler independent calculation
    using identical inputs.
    """

    def setUp(self) -> None:
        self.corpus = {
            "A": "red apple",
            "B": "green apple",
            "C": "blue sky",
        }

    def test_oracle_comparison_query_red_apple(self) -> None:
        """Direct retriever and independent oracle produce identical ranked results for 'red apple'."""
        comp = compare_retriever_with_oracle(self.corpus, "red apple")

        self.assertTrue(comp["is_equivalent"])
        self.assertEqual(comp["direct_count"], 2)
        self.assertEqual(comp["direct_results"], comp["oracle_results"])
        self.assertEqual(comp["direct_results"][0].doc_id, "A")
        self.assertEqual(comp["direct_results"][1].doc_id, "B")

    def test_oracle_comparison_query_ocean(self) -> None:
        """Direct retriever and independent oracle both return empty list for 'ocean'."""
        comp = compare_retriever_with_oracle(self.corpus, "ocean")

        self.assertTrue(comp["is_equivalent"])
        self.assertEqual(comp["direct_count"], 0)
        self.assertEqual(comp["oracle_count"], 0)
        self.assertEqual(comp["direct_results"], [])

    def test_oracle_comparison_on_diverse_queries(self) -> None:
        """Compare direct retriever and oracle across multiple queries."""
        queries = ["apple", "blue", "sky red", "green sky", "nomatch"]
        for q in queries:
            with self.subTest(query=q):
                comp = compare_retriever_with_oracle(self.corpus, q)
                self.assertTrue(comp["is_equivalent"])
                self.assertEqual(comp["direct_results"], comp["oracle_results"])


class TestDeliberateWrongAssertions(unittest.TestCase):
    """
    Deliberate wrong result checks to confirm that deviations immediately cause test failures.
    """

    def test_deliberate_wrong_rank_order_fails(self) -> None:
        """Asserting that B ranks before A raises AssertionError."""
        retriever = TinyLexicalRetriever({"A": "red apple", "B": "green apple"})
        results = retriever.retrieve("red apple")

        with self.assertRaises(AssertionError):
            # Deliberately assert B is ranked first
            self.assertEqual(results[0].doc_id, "B")

    def test_deliberate_wrong_empty_result_fails(self) -> None:
        """Asserting that 'ocean' returns a match raises AssertionError."""
        retriever = TinyLexicalRetriever({"A": "red apple", "B": "green apple"})
        results = retriever.retrieve("ocean")

        with self.assertRaises(AssertionError):
            # Deliberately assert ocean returned 1 result
            self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
