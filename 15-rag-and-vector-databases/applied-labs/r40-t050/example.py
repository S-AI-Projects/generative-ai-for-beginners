"""
R40-T045 · Applied Lab: Tiny Lexical Retriever (RAG Test Double)
================================================================

This module illustrates Lesson 15 ("Retrieval Augmented Generation and Vector Databases")
by providing a **tiny lexical test double** that demonstrates query normalization,
word-set overlap scoring, tie-breaking, and empty-result handling.

Lesson connection
-----------------
Lesson 15 explains that RAG systems connect an LLM to a knowledge base by:
  1. Receiving a user query.
  2. Normalizing and matching query terms against stored documents.
  3. Ranking retrieved documents by relevance.
  4. Passing retrieved context to the generator (or safely handling empty matches).

Test double disclaimer
----------------------
This is a **lexical test double**, NOT a production vector search.
  - It scores simple set overlap on lowercase words.
  - It does NOT use dense neural embeddings (e.g. OpenAI ada-002, text-embedding-3).
  - It does NOT compute cosine similarity or approximate nearest neighbors (HNSW/ScANN).
  - It does NOT perform semantic matching (e.g., "automobile" will not match "car").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence


RETRIEVER_LABEL = (
    "LEXICAL TEST DOUBLE — lowercase word-set overlap only. "
    "This is NOT a production vector search (no embeddings, no cosine similarity, "
    "no semantic vector index)."
)


@dataclass(frozen=True)
class SearchResult:
    """A scored document result returned by the retriever."""
    doc_id: str
    score: int
    text: str


def _tokenize_to_set(text: str) -> set[str]:
    """Extract lowercase alphanumeric words into a set."""
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


class TinyLexicalRetriever:
    """
    A tiny deterministic lexical retriever for RAG unit tests.

    Parameters
    ----------
    documents : Mapping[str, str]
        Mapping of document ID to document text.
    """

    def __init__(self, documents: Mapping[str, str]) -> None:
        self.documents = dict(documents)
        self.doc_word_sets: dict[str, set[str]] = {
            doc_id: _tokenize_to_set(text)
            for doc_id, text in self.documents.items()
        }

    def search(self, query: str, min_score: int = 1) -> list[SearchResult]:
        """
        Search documents by lowercase word overlap, breaking ties by document ID.

        Parameters
        ----------
        query : str
            User search prompt.
        min_score : int, default=1
            Minimum overlap score required for inclusion in results.

        Returns
        -------
        list[SearchResult]
            Ranked results sorted by: (-score, doc_id).
            Empty list if no documents meet min_score.
        """
        query_words = _tokenize_to_set(query)
        scored: list[SearchResult] = []

        for doc_id, doc_words in self.doc_word_sets.items():
            overlap = len(query_words & doc_words)
            if overlap >= min_score:
                scored.append(SearchResult(
                    doc_id=doc_id,
                    score=overlap,
                    text=self.documents[doc_id],
                ))

        # Primary sort: score descending (-score)
        # Secondary sort: doc_id ascending (alphabetical tie-breaking)
        scored.sort(key=lambda res: (-res.score, res.doc_id))
        return scored


# Standard fixture corpus required by task specification
FIXTURE_DOCUMENTS: dict[str, str] = {
    "A": "red apple",
    "B": "green apple",
    "C": "blue sky",
}


# ---------------------------------------------------------------------------
# Applied Questions (Focus Requirement)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppliedQuestion:
    question_id: str
    question_type: str  # "predict_output", "diagnose_failure", "boundary_policy"
    prompt: str
    factual_answer: str
    rationale: str


APPLIED_QUESTIONS: dict[str, AppliedQuestion] = {
    "Q1": AppliedQuestion(
        question_id="Q1",
        question_type="predict_output",
        prompt="Given documents A='red apple', B='green apple', C='blue sky' and query 'apple', what are the ranked document IDs?",
        factual_answer="['A', 'B']",
        rationale=(
            "Both documents A and B share exactly 1 word ('apple') with the query, "
            "giving each an overlap score of 1. Document C has 0 overlap and is excluded. "
            "Ties between A and B are broken alphabetically by document ID, placing 'A' before 'B'."
        ),
    ),
    "Q2": AppliedQuestion(
        question_id="Q2",
        question_type="diagnose_failure",
        prompt="Why would a naive split() without punctuation stripping fail to match query 'apple!' against Document A ('red apple')?",
        factual_answer="Tokenization mismatch: 'apple!' retains punctuation and does not equal 'apple'.",
        rationale=(
            "Naive whitespace splitting produces token 'apple!' with trailing punctuation. "
            "Because set membership checks exact string equality, {'apple!'} & {'red', 'apple'} "
            "is empty, resulting in a false-negative retrieval failure."
        ),
    ),
    "Q3": AppliedQuestion(
        question_id="Q3",
        question_type="boundary_policy",
        prompt="When a query like 'ocean' returns 0 matching documents, which boundary policy should the RAG pipeline choose?",
        factual_answer="Short-circuit and refuse generation (return 'No relevant documents found') rather than hallucinating without context.",
        rationale=(
            "Lesson 15 explains that RAG exists to ground answers in verifiable source documents. "
            "Forwarding an empty context to the LLM risks hallucinations or ungrounded claims. "
            "Short-circuiting preserves grounding integrity and saves inference tokens."
        ),
    ),
}
