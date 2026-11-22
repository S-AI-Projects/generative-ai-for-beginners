#!/usr/bin/env python3
"""Lexical Retriever with Source Attribution and Boundary-Case Evaluation (R40-T002).

Lesson 20: Building with Mistral Models
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a deterministic, lexical retrieval engine over a local document
corpus to model source attribution, score tie-breaking, and boundary handling.
In retrieval-augmented systems (such as those using Mistral or other foundation models),
before passing retrieved context into generation prompts, the retriever must provide
transparent source citations (document IDs), deterministic rank ordering, and clear
filtering for zero-relevance boundary queries.

Contract Rules:
1. Local Fixture:
   - Document A: "red apple"
   - Document B: "green apple"
   - Document C: "blue sky"
2. Scoring:
   - Lowercase word sets are constructed for both query and candidate documents.
   - Relevance score is the size of the set intersection: |words(query) ∩ words(doc)|.
3. Tie-breaking:
   - Ranked primarily by score descending.
   - Ties in score are broken alphabetically by document ID ascending (e.g. 'A' before 'B').
4. Source Attribution:
   - Every result includes document ID, relevance score, text content, and matching tokens.
5. Invariants & Boundary Cases:
   - Query "red apple": ranks Document A (score 2) before Document B (score 1).
   - Query "ocean": produces no match (empty result list), preventing zero-relevance noise.
   - Smallest valid case: single matching token (e.g. "apple" matches A and B with score 1,
     breaking ties by ID to place A before B).
   - Invalid inputs: empty or whitespace-only queries raise ValueError; non-string queries
     raise TypeError.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local lexical test double using Python's standard library.
It is NOT a dense vector search or neural embedding model. It requires no network
access, external APIs, cloud credentials, or GPU hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
import sys
from typing import Any, Dict, List, Optional, Set

DEFAULT_DOCUMENTS: Dict[str, str] = {
    "A": "red apple",
    "B": "green apple",
    "C": "blue sky",
}


class RetrievalError(Exception):
    """Base exception for retrieval errors."""


class DecisionMismatchError(RetrievalError):
    """Raised when verification assertions fail."""


@dataclass(frozen=True)
class SearchResult:
    """Represents a retrieved document with source attribution and score."""

    doc_id: str
    score: int
    text: str
    matched_tokens: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "score": self.score,
            "text": self.text,
            "matched_tokens": self.matched_tokens,
        }


def tokenize(text: str) -> Set[str]:
    """Extracts a set of lowercase word tokens from a string."""
    if not isinstance(text, str):
        raise TypeError(f"Expected text of type str, got {type(text).__name__}")
    tokens = re.findall(r"\b\w+\b", text.lower())
    return set(tokens)


class LexicalRetriever:
    """Deterministic lexical retriever scoring query-document word overlap."""

    def __init__(self, documents: Optional[Dict[str, str]] = None) -> None:
        if documents is None:
            documents = dict(DEFAULT_DOCUMENTS)
        if not documents:
            raise ValueError("Corpus cannot be empty.")
        self.documents = dict(documents)
        self.doc_token_sets = {doc_id: tokenize(text) for doc_id, text in self.documents.items()}

    def search(self, query: str, min_score: int = 1) -> List[SearchResult]:
        """Searches the corpus for documents with overlap >= min_score."""
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query).__name__}")
        if not query.strip():
            raise ValueError("Query must not be empty or whitespace-only.")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        results: List[SearchResult] = []
        for doc_id, doc_tokens in self.doc_token_sets.items():
            intersection = query_tokens.intersection(doc_tokens)
            score = len(intersection)
            if score >= min_score:
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        score=score,
                        text=self.documents[doc_id],
                        matched_tokens=sorted(list(intersection)),
                    )
                )

        # Primary sort: score descending; Secondary sort: doc_id ascending
        results.sort(key=lambda r: (-r.score, r.doc_id))
        return results


def run_normal_scenario() -> Dict[str, Any]:
    """Normal query 'red apple' ranks A (score 2) before B (score 1)."""
    retriever = LexicalRetriever()
    results = retriever.search("red apple")
    doc_ids = [r.doc_id for r in results]
    scores = [r.score for r in results]

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "query": "red apple",
        "decision": "RANK_A_BEFORE_B",
        "doc_ids": doc_ids,
        "scores": scores,
        "results": [r.to_dict() for r in results],
        "contract_satisfied": (doc_ids == ["A", "B"] and scores == [2, 1]),
    }


def run_boundary_zero_match_scenario() -> Dict[str, Any]:
    """Boundary query 'ocean' returns no match (empty list)."""
    retriever = LexicalRetriever()
    results = retriever.search("ocean")

    return {
        "scenario_id": "SCENARIO_BOUNDARY_ZERO_MATCH",
        "query": "ocean",
        "decision": "NO_MATCH_EMPTY_RESULT",
        "doc_ids": [r.doc_id for r in results],
        "scores": [r.score for r in results],
        "results": [r.to_dict() for r in results],
        "contract_satisfied": (len(results) == 0),
    }


def run_boundary_tie_scenario() -> Dict[str, Any]:
    """Boundary tie-breaking scenario: query 'apple' matches A and B equally; A breaks tie before B."""
    retriever = LexicalRetriever()
    results = retriever.search("apple")
    doc_ids = [r.doc_id for r in results]
    scores = [r.score for r in results]

    return {
        "scenario_id": "SCENARIO_BOUNDARY_TIE",
        "query": "apple",
        "decision": "TIE_BROKEN_A_BEFORE_B",
        "doc_ids": doc_ids,
        "scores": scores,
        "results": [r.to_dict() for r in results],
        "contract_satisfied": (doc_ids == ["A", "B"] and scores == [1, 1]),
    }


def run_invalid_case_scenario() -> Dict[str, Any]:
    """Invalid case scenario: empty string and non-string inputs rejected with structured errors."""
    retriever = LexicalRetriever()
    empty_caught = False
    type_caught = False

    try:
        retriever.search("   ")
    except ValueError:
        empty_caught = True

    try:
        retriever.search(12345)  # type: ignore
    except TypeError:
        type_caught = True

    return {
        "scenario_id": "SCENARIO_INVALID_CASES",
        "decision": "INVALID_INPUTS_REJECTED",
        "empty_query_rejected": empty_caught,
        "invalid_type_rejected": type_caught,
        "contract_satisfied": (empty_caught and type_caught),
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the complete decision table and raises DecisionMismatchError on failure."""
    normal = run_normal_scenario()
    zero_match = run_boundary_zero_match_scenario()
    tie_match = run_boundary_tie_scenario()
    invalid_cases = run_invalid_case_scenario()

    scenarios = [normal, zero_match, tie_match, invalid_cases]
    expected_decisions = {
        "SCENARIO_NORMAL": "RANK_A_BEFORE_B",
        "SCENARIO_BOUNDARY_ZERO_MATCH": "NO_MATCH_EMPTY_RESULT",
        "SCENARIO_BOUNDARY_TIE": "TIE_BROKEN_A_BEFORE_B",
        "SCENARIO_INVALID_CASES": "INVALID_INPUTS_REJECTED",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected and sc.get("contract_satisfied", False))
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T002: Lexical Retriever with Source Attribution Example."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "zero_match", "tie", "invalid"],
        help="Run a specific evaluation scenario.",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Execute an ad-hoc retrieval query against the default corpus.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    if args.query:
        retriever = LexicalRetriever()
        results = retriever.search(args.query)
        print(json.dumps([r.to_dict() for r in results], indent=2))
        sys.exit(0)
    elif args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "zero_match":
        print(json.dumps(run_boundary_zero_match_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "tie":
        print(json.dumps(run_boundary_tie_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "invalid":
        print(json.dumps(run_invalid_case_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
