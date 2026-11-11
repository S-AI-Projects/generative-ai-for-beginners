"""Local lexical retriever test double behind a callable interface (Lesson 20).

This module is a deterministic lexical test double—NOT a production vector
search, semantic embedding model, or FAISS index. It makes no claims about real
hardware, cloud service behavior, or trained-model performance.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, Mapping, Sequence

LEXICAL_TEST_DOUBLE_NOTE = (
    "lexical test double (lowercase word-set overlap), not a production vector search"
)

# Callable interface abstracting the external retrieval dependency.
RetrieverFn = Callable[[str], list[dict[str, Any]]]

SYNTHETIC_DOCUMENTS: tuple[dict[str, str], ...] = (
    {"doc_id": "A", "text": "red apple"},
    {"doc_id": "B", "text": "green apple"},
    {"doc_id": "C", "text": "blue sky"},
)


def _normalize_terms(text: str) -> set[str]:
    if not isinstance(text, str):
        raise ValueError(f"text must be a str, got {type(text).__name__}")
    return set(text.lower().split())


def make_lexical_retriever(
    documents: Sequence[Mapping[str, str]] = SYNTHETIC_DOCUMENTS,
) -> RetrieverFn:
    """Return a deterministic local adapter implementing RetrieverFn.

    Scores query/document overlap on lowercase word sets, excludes zero-overlap
    documents, and breaks ties ascending by doc_id.

    Real-service behaviors NOT established by this mock:
    - Dense semantic or cross-lingual embeddings (e.g., cohere-embed-v3-multilingual)
    - FAISS vector indexing/L2 similarity and document chunking strategies
    - Network calls, authentication, rate limits, or Mistral answer synthesis
    """
    validated_docs: list[dict[str, Any]] = []
    for index, doc in enumerate(documents):
        if not isinstance(doc, Mapping):
            raise ValueError(f"documents[{index}] must be a mapping")
        doc_id = doc.get("doc_id")
        text = doc.get("text")
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError(f"documents[{index}]['doc_id'] must be a non-empty string")
        if not isinstance(text, str):
            raise ValueError(f"documents[{index}]['text'] must be a str")
        validated_docs.append(
            {
                "doc_id": doc_id,
                "text": text,
                "terms": _normalize_terms(text),
            }
        )

    def retrieve(query: str) -> list[dict[str, Any]]:
        query_terms = _normalize_terms(query)
        if not query_terms:
            return []

        scored: list[dict[str, Any]] = []
        for doc in validated_docs:
            matched_terms = sorted(query_terms & doc["terms"])
            score = len(matched_terms)
            if score > 0:
                scored.append(
                    {
                        "doc_id": doc["doc_id"],
                        "text": doc["text"],
                        "score": score,
                        "matched_terms": matched_terms,
                    }
                )

        scored.sort(key=lambda item: (-item["score"], item["doc_id"]))
        return scored

    return retrieve


def run_retrieval(
    query: str,
    retriever: RetrieverFn,
) -> dict[str, Any]:
    """Execute retrieval against any RetrieverFn adapter."""
    query_terms = _normalize_terms(query)
    results = retriever(query)
    return {
        "simulation": True,
        "test_double_note": LEXICAL_TEST_DOUBLE_NOTE,
        "query": query,
        "normalized_terms": sorted(query_terms),
        "results": results,
        "doc_ids": [item["doc_id"] for item in results],
        "matched_count": len(results),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local lexical retriever test double over synthetic "
            "documents A, B, and C."
        )
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query text to score (omit to run the default fixture queries).",
    )
    args = parser.parse_args(argv)

    adapter = make_lexical_retriever(SYNTHETIC_DOCUMENTS)
    if args.query is not None:
        payload = run_retrieval(args.query, adapter)
        print(json.dumps(payload, indent=2))
        return 0

    default_payload = {
        "simulation": True,
        "test_double_note": LEXICAL_TEST_DOUBLE_NOTE,
        "documents": list(SYNTHETIC_DOCUMENTS),
        "runs": [
            run_retrieval("red apple", adapter),
            run_retrieval("ocean", adapter),
        ],
    }
    print(json.dumps(default_payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
