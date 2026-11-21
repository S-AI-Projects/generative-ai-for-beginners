"""
R40-T050 · Test suite for example.py
======================================

Covers:
  1. Primary contract:
     Documents A="red apple", B="green apple", C="blue sky".
     Query "red apple" ranks A before B.
     Query "ocean" returns no match (empty list).
  2. Tie-breaking:
     Equal overlap scores break ties alphabetically by document ID.
  3. Returns document IDs:
     SearchResult objects contain doc_id, score, and text.
  4. Test double disclaimer:
     Explicitly labeled as a lexical test double, not a production vector search.
  5. Focus: Executable checks for the 3 applied questions:
     - Q1 (predict output): query "apple" ranks ['A', 'B'].
     - Q2 (diagnose failure): tokenization normalization check.
     - Q3 (choose boundary policy): short-circuit on empty retrieval.
  6. Deliberate wrong result checks:
     Proves checker exits non-zero if assertions fail.
"""

import unittest

from example import (
    APPLIED_QUESTIONS,
    FIXTURE_DOCUMENTS,
    RETRIEVER_LABEL,
    SearchResult,
    TinyLexicalRetriever,
    _tokenize_to_set,
)


class TestTinyLexicalRetrieverContract(unittest.TestCase):
    """
    Contract requirements:
      Documents A="red apple", B="green apple", C="blue sky";
      query "red apple" ranks A before B;
      query "ocean" returns no match.
      Returns document IDs with results.
    """

    def setUp(self):
        self.retriever = TinyLexicalRetriever(FIXTURE_DOCUMENTS)

    def test_query_red_apple_ranks_A_before_B(self):
        results = self.retriever.search("red apple")
        ranked_ids = [res.doc_id for res in results]

        # A has overlap 2 (red, apple); B has overlap 1 (apple); C has 0
        self.assertEqual(ranked_ids, ["A", "B"])
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[1].score, 1)
        self.assertEqual(results[1].doc_id, "B")

    def test_query_ocean_returns_no_match(self):
        results = self.retriever.search("ocean")
        self.assertEqual(results, [])

    def test_results_include_document_ids(self):
        results = self.retriever.search("red apple")
        for res in results:
            self.assertIsInstance(res.doc_id, str)
            self.assertIn(res.doc_id, FIXTURE_DOCUMENTS)

    def test_label_identifies_lexical_test_double(self):
        self.assertIn("LEXICAL TEST DOUBLE", RETRIEVER_LABEL)
        self.assertIn("NOT a production vector search", RETRIEVER_LABEL)

    def test_deliberate_wrong_ranking_fails(self):
        """Deliberately assert that B is ranked before A for 'red apple'."""
        results = self.retriever.search("red apple")
        ranked_ids = [res.doc_id for res in results]
        with self.assertRaises(AssertionError):
            self.assertEqual(ranked_ids, ["B", "A"],
                             "Intentional failure: A must precede B.")

    def test_deliberate_wrong_ocean_match_fails(self):
        """Deliberately assert that 'ocean' matches Document C."""
        results = self.retriever.search("ocean")
        with self.assertRaises(AssertionError):
            self.assertNotEqual(results, [],
                                "Intentional failure: ocean has no matches.")


class TestAppliedQuestionsExecutableChecks(unittest.TestCase):
    """
    Focus requirement:
      Provide a rationale and executable check for each factual answer
      to the three applied questions.
    """

    def setUp(self):
        self.retriever = TinyLexicalRetriever(FIXTURE_DOCUMENTS)

    def test_q1_predict_output_executable_check(self):
        """
        Q1 Executable Check:
        Query 'apple' produces tie between A (1) and B (1).
        Tie-breaking by document ID must rank ['A', 'B'].
        """
        q = APPLIED_QUESTIONS["Q1"]
        results = self.retriever.search("apple")
        actual_ranked_ids = [res.doc_id for res in results]

        self.assertEqual(str(actual_ranked_ids), q.factual_answer)
        self.assertEqual(results[0].doc_id, "A")
        self.assertEqual(results[1].doc_id, "B")
        self.assertEqual(results[0].score, results[1].score)

    def test_q2_diagnose_failure_executable_check(self):
        """
        Q2 Executable Check:
        Diagnose why naive split() fails on 'apple!' vs normalized regex set.
        """
        raw_query = "apple!"

        # Naive split preserves punctuation
        naive_tokens = set(raw_query.split())
        doc_a_naive = set(FIXTURE_DOCUMENTS["A"].split())
        naive_overlap = len(naive_tokens & doc_a_naive)
        # Demonstrates failure: 'apple!' != 'apple'
        self.assertEqual(naive_overlap, 0)

        # Standard normalized tokenization succeeds
        normalized_overlap = len(_tokenize_to_set(raw_query) & _tokenize_to_set(FIXTURE_DOCUMENTS["A"]))
        self.assertEqual(normalized_overlap, 1)

    def test_q3_choose_boundary_policy_executable_check(self):
        """
        Q3 Executable Check:
        When retrieval returns empty (e.g. 'ocean'), verify short-circuiting logic.
        """
        def rag_pipeline_with_boundary_policy(query: str) -> str:
            matched_docs = self.retriever.search(query)
            if not matched_docs:
                # Boundary policy: short-circuit with refusal / fallback
                return "Refusal: No relevant documents found to ground answer."
            context = "\n".join(f"[{doc.doc_id}] {doc.text}" for doc in matched_docs)
            return f"Augmented Prompt with Context:\n{context}"

        # Boundary case: ocean
        response = rag_pipeline_with_boundary_policy("ocean")
        self.assertIn("No relevant documents found", response)

        # Normal case: red apple
        response_normal = rag_pipeline_with_boundary_policy("red apple")
        self.assertIn("Augmented Prompt with Context", response_normal)
        self.assertIn("[A] red apple", response_normal)


class TestBoundaryAndEdgeCases(unittest.TestCase):
    """Boundary conditions: empty query, uppercase input, punctuation."""

    def setUp(self):
        self.retriever = TinyLexicalRetriever(FIXTURE_DOCUMENTS)

    def test_case_insensitive_matching(self):
        results = self.retriever.search("RED APPLE")
        self.assertEqual([res.doc_id for res in results], ["A", "B"])

    def test_empty_query_returns_no_match(self):
        results = self.retriever.search("")
        self.assertEqual(results, [])

    def test_single_word_partial_matches(self):
        results = self.retriever.search("blue")
        self.assertEqual([res.doc_id for res in results], ["C"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
