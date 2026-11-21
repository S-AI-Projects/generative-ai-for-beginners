"""
R40-T038 · Applied Lab: Ranked Search with Stable Ties & Boundary Evaluation
=============================================================================

This module extends Lesson 08 ("Building Search Applications") by implementing a
deterministic ranked search engine that computes token overlap scores, enforces
minimum-score thresholds, resolves score ties deterministically by document ID,
and provides boundary-case analysis.

Lesson connection
-----------------
Lesson 08 covers building search applications and contrasts keyword/token search with
semantic vector search. In search applications:
  1. Retrieval queries are tokenized and scored against candidate documents.
  2. Provenance (source document ID) and relevance score must accompany every result
     so downstream systems can cite sources and apply filtering.
  3. Minimum score thresholds (e.g. min_score=1) prune irrelevant documents scoring zero
     to prevent noise from reaching generation models.
  4. Stable tie-breaking is critical: when two documents (e.g., "red apple" and "red berry")
     share the identical score for query "red", tie-breaking by stable document ID ensures
     reproducible ranking order.

Simplification boundary
-----------------------
This local implementation operates on in-memory lowercase token sets. It does NOT:
  - Generate dense neural embeddings (e.g. text-embedding-ada-002).
  - Use vector databases (e.g. Azure AI Search, Pinecone, Cosmos DB).
  - Claim semantic understanding or real-world search precision.

Focus: Smallest Valid, Boundary, and Invalid Cases & Exact Boundary Decisions
------------------------------------------------------------------------------
The search engine's behavior is comprehensively characterized across:
  - Smallest valid case: Single-token document and single-token matching query.
  - Boundary cases: Exact score threshold match (score == min_score, included),
    sub-threshold match (score < min_score, excluded), score ties broken by doc_id,
    and empty string queries.
  - Invalid cases: Non-string queries, empty document IDs, negative score thresholds.
  - Exact boundary decision: `score >= min_score` (inclusive cutoff, where documents
    with score 0 are pruned by default) and sort key `(-score, doc_id)`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SearchResult:
    """
    Ranked search result with explicit source ID and score.

    Attributes
    ----------
    doc_id : str
        The unique document identifier (provenance).
    score : int
        The token overlap score.
    text : str
        The raw document content text.
    """
    doc_id: str
    score: int
    text: str


@dataclass(frozen=True)
class BoundaryEvaluationCase:
    """
    Structured representation of a boundary test scenario.
    """
    category: str
    description: str
    query: str
    min_score: int
    expected_status: str
    decision_rule: str


def tokenize(text: str) -> set[str]:
    """
    Normalize text into a lowercase set of word tokens.
    """
    if not isinstance(text, str):
        raise TypeError(f"Text must be a string, got {type(text).__name__}")
    return set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))


class RankedTokenSearchEngine:
    """
    Deterministic ranked search engine scoring token overlap, applying minimum-score
    thresholds, and resolving score ties using stable document ID order.
    """

    def __init__(
        self,
        corpus: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
        default_min_score: int = 1,
    ) -> None:
        if not isinstance(default_min_score, int) or default_min_score < 0:
            raise ValueError(f"default_min_score must be a non-negative integer, got {default_min_score!r}")

        self._default_min_score = default_min_score
        self._corpus: dict[str, str] = {}
        self._tokens: dict[str, set[str]] = {}

        if corpus is not None:
            if isinstance(corpus, Mapping):
                for doc_id, text in corpus.items():
                    self.add_document(doc_id, text)
            elif isinstance(corpus, Sequence):
                for item in corpus:
                    if not isinstance(item, (list, tuple)) or len(item) != 2:
                        raise ValueError("Corpus sequence items must be (doc_id, text) pairs.")
                    self.add_document(item[0], item[1])
            else:
                raise TypeError(f"Corpus must be a mapping or sequence of pairs, got {type(corpus).__name__}")

    @property
    def corpus(self) -> dict[str, str]:
        return dict(self._corpus)

    def add_document(self, doc_id: str, text: str) -> None:
        """
        Add a document to the index.
        """
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError(f"doc_id must be a non-empty string, got {doc_id!r}")
        if not isinstance(text, str):
            raise TypeError(f"Document text must be a string, got {type(text).__name__}")

        clean_id = doc_id.strip()
        self._corpus[clean_id] = text
        self._tokens[clean_id] = tokenize(text)

    def search(
        self,
        query: str,
        min_score: int | None = None,
    ) -> list[SearchResult]:
        """
        Rank indexed documents against the query.

        Parameters
        ----------
        query : str
            Search query string.
        min_score : int | None
            Minimum overlap score for inclusion. If None, uses default_min_score.

        Returns
        -------
        list[SearchResult]
            Ranked results sorted by score descending, breaking ties by doc_id ascending.
        """
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query).__name__}")

        threshold = self._default_min_score if min_score is None else min_score
        if not isinstance(threshold, int) or threshold < 0:
            raise ValueError(f"min_score must be a non-negative integer, got {threshold!r}")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored: list[SearchResult] = []
        for doc_id, doc_tokens in self._tokens.items():
            overlap = len(query_tokens & doc_tokens)
            # Boundary decision: score >= threshold
            if overlap >= threshold:
                scored.append(
                    SearchResult(
                        doc_id=doc_id,
                        score=overlap,
                        text=self._corpus[doc_id],
                    )
                )

        # Primary sort: score descending (-r.score)
        # Secondary sort: stable doc_id ascending (r.doc_id)
        scored.sort(key=lambda r: (-r.score, r.doc_id))
        return scored


# ---------------------------------------------------------------------------
# Focus: Boundary Evaluation Matrix & Decision Explanation
# ---------------------------------------------------------------------------

DEFAULT_CONTRACT_CORPUS: dict[str, str] = {
    "doc_1": "red apple",
    "doc_2": "red berry",
    "doc_3": "blue sky",
}


def get_boundary_case_matrix() -> list[BoundaryEvaluationCase]:
    """
    Returns an audited matrix of the smallest valid, boundary, and invalid cases.
    """
    return [
        BoundaryEvaluationCase(
            category="smallest_valid",
            description="Minimal valid document ('a') and single-token query ('a')",
            query="a",
            min_score=1,
            expected_status="Included with score=1",
            decision_rule="score >= 1 satisfied on single character word",
        ),
        BoundaryEvaluationCase(
            category="threshold_boundary_exact",
            description="Document score matches threshold exactly (score == 1, min_score == 1)",
            query="red",
            min_score=1,
            expected_status="Included (doc_1, doc_2)",
            decision_rule="score >= min_score is inclusive; boundary point is retained",
        ),
        BoundaryEvaluationCase(
            category="threshold_boundary_excluded",
            description="Document score is 0 with threshold 1 (blue sky for query 'red')",
            query="red",
            min_score=1,
            expected_status="Omitted (doc_3 omitted)",
            decision_rule="score < min_score causes document to be dropped from results",
        ),
        BoundaryEvaluationCase(
            category="tie_breaking_boundary",
            description="Equal score tie between doc_1 and doc_2 (both score 1)",
            query="red",
            min_score=1,
            expected_status="Stable order: doc_1 ranked before doc_2",
            decision_rule="Tie-breaker: alphabetical comparison on doc_id string",
        ),
        BoundaryEvaluationCase(
            category="empty_query_boundary",
            description="Empty or whitespace-only query string",
            query="   ",
            min_score=1,
            expected_status="Empty results list []",
            decision_rule="Empty token set matches zero documents",
        ),
        BoundaryEvaluationCase(
            category="invalid_threshold",
            description="Negative minimum-score threshold (e.g. -1)",
            query="red",
            min_score=-1,
            expected_status="Raises ValueError",
            decision_rule="Thresholds must be non-negative integers",
        ),
    ]


def explain_boundary_decisions() -> str:
    """
    Returns the comprehensive rationale for the exact boundary decisions.
    """
    return (
        "### Exact Boundary Decisions in Ranked Search\n\n"
        "1. **Inclusion Threshold (`score >= min_score`)**:\n"
        "   - We choose an **inclusive cutoff**. When `min_score=1`, any document with at least one\n"
        "     matching token is retained.\n"
        "   - Documents scoring 0 (e.g. `doc_3: 'blue sky'` for query `'red'`) have zero token overlap\n"
        "     and are omitted. This boundary prevents sending ungrounded documents to downstream LLM steps.\n\n"
        "2. **Deterministic Tie-Breaking (`(-score, doc_id)`)**:\n"
        "   - When multiple documents achieve identical overlap scores (e.g., `'doc_1: red apple'` and\n"
        "     `'doc_2: red berry'` both score 1 for query `'red'`), sort stability is preserved by sorting\n"
        "     ascending on the document ID string.\n"
        "   - This guarantees that search rankings remain completely deterministic and reproducible.\n\n"
        "3. **Zero-Token Queries**:\n"
        "   - Empty strings, punctuation-only strings, or whitespace produce an empty token set and return `[]`.\n"
    )
