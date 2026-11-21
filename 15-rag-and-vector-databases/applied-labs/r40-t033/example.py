"""
R40-T033 · Applied Lab: Tiny Lexical Retriever with Source Attribution
=======================================================================

This module extends Lesson 15 ("Retrieval Augmented Generation (RAG) and Vector
Databases") by implementing a deterministic lexical retriever test double with
source document attribution, tie-breaking, and an independent oracle calculation.

Lesson connection
-----------------
Lesson 15 explains how RAG grounds large language models with external knowledge
by retrieving relevant documents and attributing sources. In RAG pipelines:
  1. User queries are normalized (lowercased and tokenized) and compared against a
     document corpus to identify relevant context.
  2. Documents must be ranked by relevance score, with ties resolved deterministically
     (e.g., by document identifier) to guarantee repeatable application behavior.
  3. When no documents match a query (e.g. query "ocean" against fruit/sky texts),
     the retriever must return an empty result set so the generation phase can
     gracefully refuse or trigger fallbacks rather than hallucinating.
  4. Retrieved results must return clear source attribution (document IDs) so the
     model or user interface can cite the grounded source.

Simplification boundary (Lexical Test Double)
---------------------------------------------
This module is explicitly a **lexical test double**, NOT a production vector search:
  - It scores relevance using discrete lowercase word-set overlap (exact keyword matching).
  - It does NOT compute dense neural embeddings (e.g., OpenAI text-embedding-3 / ada-002).
  - It does NOT perform approximate nearest neighbor (ANN) vector indexing (e.g., HNSW, FAISS).
  - It does NOT understand semantic synonyms (e.g., "crimson" will not match "red").
  - No physical GPU, cloud vector database (Azure AI Search, Cosmos DB), or network API is needed.

Focus: Comparison with Independent Reference Oracle Table
---------------------------------------------------------
We provide both a direct object-oriented retriever (`TinyLexicalRetriever`) and an
independent reference oracle function (`reference_lexical_oracle`). The test suite
evaluates both against identical inputs to prove complete behavioral equivalence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SearchResult:
    """
    Ranked search result with explicit source document attribution.

    Attributes
    ----------
    doc_id : str
        The unique document identifier (source citation).
    score : int
        The lexical overlap score (number of common distinct words).
    text : str
        The raw document content text.
    """
    doc_id: str
    score: int
    text: str


def tokenize_to_word_set(text: str) -> set[str]:
    """
    Normalize text to a lowercase set of alphanumeric word tokens.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string for tokenization, got {type(text).__name__}")
    return set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))


class TinyLexicalRetriever:
    """
    Deterministic lexical retriever scoring query/document overlap on lowercase word sets
    and breaking score ties alphabetically by document ID.
    """

    def __init__(self, corpus: Mapping[str, str] | Sequence[tuple[str, str]] | None = None) -> None:
        self._corpus: dict[str, str] = {}
        self._index: dict[str, set[str]] = {}

        if corpus is not None:
            if isinstance(corpus, Mapping):
                for doc_id, text in corpus.items():
                    self.add_document(doc_id, text)
            elif isinstance(corpus, Sequence):
                for item in corpus:
                    if not isinstance(item, (list, tuple)) or len(item) != 2:
                        raise ValueError("Corpus sequence items must be (doc_id, text) tuples")
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
            raise ValueError("Document ID must be a non-empty string.")
        if not isinstance(text, str):
            raise TypeError("Document text must be a string.")

        clean_id = doc_id.strip()
        self._corpus[clean_id] = text
        self._index[clean_id] = tokenize_to_word_set(text)

    def retrieve(self, query: str) -> list[SearchResult]:
        """
        Retrieve documents matching the query, scored by word overlap and ranked
        by score descending, breaking ties by doc_id ascending.

        Documents with score == 0 are excluded (returns empty list if no matches).
        """
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query).__name__}")

        query_tokens = tokenize_to_word_set(query)
        if not query_tokens:
            return []

        results: list[SearchResult] = []
        for doc_id, doc_tokens in self._index.items():
            overlap_score = len(query_tokens & doc_tokens)
            if overlap_score > 0:
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        score=overlap_score,
                        text=self._corpus[doc_id],
                    )
                )

        # Primary sort: score descending (-score)
        # Secondary tie-breaker: doc_id ascending (doc_id)
        results.sort(key=lambda r: (-r.score, r.doc_id))
        return results


# ---------------------------------------------------------------------------
# Focus: Independent Reference Oracle & Equivalence Comparison
# ---------------------------------------------------------------------------

def reference_lexical_oracle(corpus: Mapping[str, str], query: str) -> list[SearchResult]:
    """
    Simpler independent calculation using a direct functional comprehension
    to compute expected retrieval results without the class state.
    """
    if not isinstance(query, str):
        raise TypeError("Query must be a string")

    q_words = set(re.findall(r"\b[a-zA-Z0-9_]+\b", query.lower()))
    if not q_words:
        return []

    scored_items: list[SearchResult] = []
    for doc_id, text in corpus.items():
        doc_words = set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))
        score = len(q_words & doc_words)
        if score > 0:
            scored_items.append(SearchResult(doc_id=doc_id, score=score, text=text))

    # Independent sort
    scored_items.sort(key=lambda x: (-x.score, x.doc_id))
    return scored_items


def compare_retriever_with_oracle(
    corpus: Mapping[str, str], query: str
) -> dict[str, Any]:
    """
    Compare direct TinyLexicalRetriever with independent oracle on identical inputs.
    """
    retriever = TinyLexicalRetriever(corpus)
    direct_results = retriever.retrieve(query)
    oracle_results = reference_lexical_oracle(corpus, query)

    is_equivalent = direct_results == oracle_results
    return {
        "query": query,
        "is_equivalent": is_equivalent,
        "direct_count": len(direct_results),
        "oracle_count": len(oracle_results),
        "direct_results": direct_results,
        "oracle_results": oracle_results,
    }
