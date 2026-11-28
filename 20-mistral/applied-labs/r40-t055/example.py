#!/usr/bin/env python3
"""Minimal local example: a tiny lexical retriever over three local
documents, put behind a callable interface with a deterministic local
adapter standing in for a real retrieval service.

Teaching fixture only. This file performs no model download, no remote API
call, no GPU and no network access.

> **Lexical test double disclaimer**: ``LocalLexicalRetriever`` below scores
> query/document overlap on lowercase word *sets*. It is a **lexical test
> double**, not a production vector search -- it does not embed text, does
> not call Cohere Embed or any other embedding model, and does not use
> faiss or any approximate nearest-neighbor index, unlike the RAG example
> in this lesson's README.

Public inputs and outputs, connected to lesson concepts
--------------------------------------------------------
- Query normalization (lesson: before a question can be matched against
    retrieved chunks, both sides need a comparable representation)
    _normalize(text) -- lowercase, whitespace-split word set.
- Retrieval ranking (lesson: `index.search(...)` returning the most
    similar chunks to a question, as in the RAG example)
    LocalLexicalRetriever.__call__, RetrievalResult.score
- Empty results (lesson: a query with no relevant chunks should not
    fabricate a match)
    an unmatched query returns an empty list, not a fabricated low-score
    result.
- Citations (lesson: the RAG example feeds `retrieved_chunks` back into the
    prompt so the model's answer can be traced to a source)
    RetrievalResult.doc_id -- every result names which document it came
    from.

Real-service behaviours this mock does NOT establish
------------------------------------------------------
Documented explicitly (and asserted non-empty by the tests) in
``UNESTABLISHED_REAL_SERVICE_BEHAVIORS`` below -- this mock says nothing
about semantic similarity, embedding quality, stemming/synonyms, ranking
beyond exact word overlap, or the latency/availability/cost of a real
embedding + vector-search service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# What this lexical test double does NOT establish about a real retrieval
# service (e.g. Cohere Embed v4 + faiss, as used in this lesson's RAG
# example). Listed explicitly so nobody mistakes this fixture for a claim
# about real embedding/vector-search behavior.
UNESTABLISHED_REAL_SERVICE_BEHAVIORS: tuple[str, ...] = (
    "semantic/embedding similarity beyond exact lowercase word overlap",
    "stemming, lemmatization, or synonym matching (e.g. 'ocean' vs 'sea')",
    "ranking quality, relevance feedback, or any learned re-ranking",
    "network latency, rate limits, or failure modes of a real embedding/search API",
    "scaling behavior over large corpora, or approximate nearest-neighbor search",
)


@dataclass(frozen=True)
class Document:
    """One local document: a stable ``doc_id`` and its text."""

    doc_id: str
    text: str


@dataclass(frozen=True)
class RetrievalResult:
    """One ranked hit: which document, and its lexical overlap score."""

    doc_id: str
    score: int


def _normalize(text: str) -> set[str]:
    """Lowercase, whitespace-split word set. The query-normalization step."""
    return set(text.lower().split())


class Retriever(Protocol):
    """The external dependency's callable interface.

    In production this would be implemented by a client that embeds the
    query, searches a vector index (as in this lesson's faiss example),
    and returns ranked chunks. Code that depends only on this interface
    (see :func:`run_retrieval`) never knows whether it is talking to that
    real service or to a local test double.
    """

    def __call__(self, query: str) -> list[RetrievalResult]: ...


class LocalLexicalRetriever:
    """Deterministic local adapter implementing :class:`Retriever`.

    Scores each document by the size of the intersection between the
    query's lowercase word set and the document's lowercase word set.
    Documents with zero overlap are dropped entirely -- an unmatched query
    returns an empty list rather than a fabricated low-score hit. Ties are
    broken by ascending ``doc_id``.
    """

    def __init__(self, documents: list[Document]):
        doc_ids = [doc.doc_id for doc in documents]
        if len(doc_ids) != len(set(doc_ids)):
            raise ValueError(f"duplicate document ids in corpus: {doc_ids}")
        self._documents = tuple(documents)

    def __call__(self, query: str) -> list[RetrievalResult]:
        if not isinstance(query, str):
            raise TypeError(f"query must be a string, got {type(query).__name__}")

        query_words = _normalize(query)
        results = []
        for doc in self._documents:
            score = len(query_words & _normalize(doc.text))
            if score > 0:
                results.append(RetrievalResult(doc_id=doc.doc_id, score=score))

        results.sort(key=lambda r: (-r.score, r.doc_id))
        return results


def run_retrieval(retriever: Retriever, query: str) -> list[RetrievalResult]:
    """Call the external dependency through its callable interface only.

    This function never references :class:`LocalLexicalRetriever`
    directly -- it only knows about the :class:`Retriever` callable
    contract, which is exactly what lets a real retrieval client be
    substituted later without changing this code.
    """
    return retriever(query)


# Fixture corpus from the task brief.
DOCUMENTS: tuple[Document, ...] = (
    Document(doc_id="A", text="red apple"),
    Document(doc_id="B", text="green apple"),
    Document(doc_id="C", text="blue sky"),
)


# ---------------------------------------------------------------------------
# Demo entry point (minimal complete example).
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Run the headline fixture and print the lesson-linked trace."""
    retriever = LocalLexicalRetriever(list(DOCUMENTS))

    print("[LESSON: query normalization] corpus=%s" % [(d.doc_id, d.text) for d in DOCUMENTS])
    print("  retriever=LocalLexicalRetriever (lexical test double, NOT a production vector search)")

    query = "red apple"
    results = run_retrieval(retriever, query)
    print("[LESSON: retrieval ranking] query=%r -> %s" % (query, [(r.doc_id, r.score) for r in results]))

    query2 = "ocean"
    results2 = run_retrieval(retriever, query2)
    print("[LESSON: empty results] query=%r -> %s (no match)" % (query2, results2))

    print("[LESSON: citations] every result names its source doc_id, e.g. %r" % (results[0].doc_id if results else None))

    print("[LESSON: unestablished real-service behavior] this mock does not establish:")
    for behavior in UNESTABLISHED_REAL_SERVICE_BEHAVIORS:
        print("  - %s" % behavior)


if __name__ == "__main__":
    run_demo()
