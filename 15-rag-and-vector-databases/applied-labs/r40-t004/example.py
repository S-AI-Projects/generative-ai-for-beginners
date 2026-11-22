#!/usr/bin/env python3
"""Lexical Retriever with Source Attribution, Intermediate Trace & Invariants (R40-T004).

Lesson 15: Retrieval Augmented Generation (RAG) and Vector Databases
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a deterministic, lexical retrieval engine over a local document
corpus to model source attribution, score tie-breaking, and multi-stage state tracing.
In RAG pipelines, grounding requires complete observability into how documents are
tokenized, scored, filtered, and sorted so that citations can be traced back to the
original source text without ambiguity.

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
   - Ties in score are broken alphabetically by document ID ascending ('A' before 'B').
4. Invariants & Retrieval Expectations:
   - Query "red apple": ranks Document A (score 2) before Document B (score 1).
   - Query "ocean": produces no match (empty list).
5. Focus (Intermediate State & Invariant Trace):
   - The engine logs each execution step:
     * STEP 1: Query tokenization
     * STEP 2: Candidate scoring
     * STEP 3: Threshold filtering
     * STEP 4: Rank ordering and deterministic tie-breaking
     * STEP 5: Attribution projection
   - Explicit invariants connect each intermediate state to the final output:
     * Invariant I1 (Scoring Fidelity): Every returned item's score equals the intersection size.
     * Invariant I2 (Monotonic Order): Results are strictly sorted by (-score, doc_id).
     * Invariant I3 (Zero Pruning): Zero-score documents never appear in final output.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local lexical test double using Python's standard library.
It is NOT a production vector search or dense embedding model. It requires no network
access, external APIs, cloud credentials, or GPU hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

DEFAULT_DOCUMENTS: Dict[str, str] = {
    "A": "red apple",
    "B": "green apple",
    "C": "blue sky",
}


class RetrievalError(Exception):
    """Base exception for retrieval errors."""


class DecisionMismatchError(RetrievalError):
    """Raised when verification assertions fail."""


class InvariantViolationError(RetrievalError):
    """Raised when an intermediate state invariant is violated."""


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


class TracingLexicalRetriever:
    """Lexical retriever that logs intermediate execution states and validates invariants."""

    def __init__(self, documents: Optional[Dict[str, str]] = None) -> None:
        if documents is None:
            documents = dict(DEFAULT_DOCUMENTS)
        if not documents:
            raise ValueError("Corpus cannot be empty.")
        self.documents = dict(documents)
        self.doc_token_sets = {doc_id: tokenize(text) for doc_id, text in self.documents.items()}

    def search_with_trace(
        self, query: str, min_score: int = 1
    ) -> Tuple[List[SearchResult], List[Dict[str, Any]]]:
        """Searches the corpus while recording intermediate step states."""
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query).__name__}")
        if not query.strip():
            raise ValueError("Query must not be empty or whitespace-only.")

        trace: List[Dict[str, Any]] = []

        # STEP 1: Query tokenization
        query_tokens = tokenize(query)
        trace.append({
            "step": 1,
            "name": "query_tokenization",
            "state": {"query": query, "query_tokens": sorted(list(query_tokens))},
        })

        if not query_tokens:
            return [], trace

        # STEP 2: Candidate scoring
        raw_scores: Dict[str, Dict[str, Any]] = {}
        for doc_id, doc_tokens in self.doc_token_sets.items():
            intersection = query_tokens.intersection(doc_tokens)
            raw_scores[doc_id] = {
                "score": len(intersection),
                "matched_tokens": sorted(list(intersection)),
            }
        trace.append({
            "step": 2,
            "name": "candidate_scoring",
            "state": {"raw_scores": raw_scores},
        })

        # STEP 3: Threshold filtering
        filtered_candidates: List[Tuple[str, int, List[str]]] = []
        for doc_id, info in raw_scores.items():
            if info["score"] >= min_score:
                filtered_candidates.append((doc_id, info["score"], info["matched_tokens"]))
        trace.append({
            "step": 3,
            "name": "threshold_filtering",
            "state": {
                "min_score": min_score,
                "passed_count": len(filtered_candidates),
                "candidates": [
                    {"doc_id": c[0], "score": c[1], "matched": c[2]}
                    for c in filtered_candidates
                ],
            },
        })

        # STEP 4: Rank ordering and deterministic tie-breaking
        # Primary: score desc, Secondary: doc_id asc
        sorted_candidates = sorted(filtered_candidates, key=lambda c: (-c[1], c[0]))
        trace.append({
            "step": 4,
            "name": "rank_ordering",
            "state": {
                "ranked_doc_ids": [c[0] for c in sorted_candidates],
                "ranked_scores": [c[1] for c in sorted_candidates],
            },
        })

        # STEP 5: Attribution projection
        results = [
            SearchResult(
                doc_id=doc_id,
                score=score,
                text=self.documents[doc_id],
                matched_tokens=matched,
            )
            for doc_id, score, matched in sorted_candidates
        ]
        trace.append({
            "step": 5,
            "name": "attribution_projection",
            "state": {"final_result_count": len(results)},
        })

        # Validate Invariants linking trace state to final output
        self._verify_invariants(trace, results)

        return results, trace

    def _verify_invariants(
        self, trace: List[Dict[str, Any]], results: List[SearchResult]
    ) -> None:
        """Verifies mathematical invariants linking intermediate states to final output."""
        raw_scores = trace[1]["state"]["raw_scores"]

        # Invariant 1: Fidelity of scores in output vs raw scoring
        for res in results:
            expected_score = raw_scores[res.doc_id]["score"]
            if res.score != expected_score:
                raise InvariantViolationError(
                    f"Invariant I1 violated: result {res.doc_id} score {res.score} != raw {expected_score}"
                )

        # Invariant 2: Strictly sorted order (-score, doc_id)
        for i in range(len(results) - 1):
            curr = results[i]
            nxt = results[i + 1]
            if curr.score < nxt.score:
                raise InvariantViolationError("Invariant I2 violated: scores not monotonically descending")
            if curr.score == nxt.score and curr.doc_id >= nxt.doc_id:
                raise InvariantViolationError("Invariant I2 violated: tie-break alphabetical order violated")

        # Invariant 3: Zero-score documents are pruned
        for res in results:
            if res.score <= 0:
                raise InvariantViolationError("Invariant I3 violated: non-positive score present in results")

    def search(self, query: str, min_score: int = 1) -> List[SearchResult]:
        """Convenience method returning search results without exposing trace."""
        results, _ = self.search_with_trace(query, min_score=min_score)
        return results


def run_normal_scenario() -> Dict[str, Any]:
    """Query 'red apple' ranks A before B; trace records 5 intermediate states."""
    retriever = TracingLexicalRetriever()
    results, trace = retriever.search_with_trace("red apple")
    doc_ids = [r.doc_id for r in results]
    scores = [r.score for r in results]

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "query": "red apple",
        "decision": "RANK_A_BEFORE_B",
        "doc_ids": doc_ids,
        "scores": scores,
        "trace_step_count": len(trace),
        "results": [r.to_dict() for r in results],
        "invariants_verified": True,
        "contract_satisfied": (doc_ids == ["A", "B"] and scores == [2, 1]),
    }


def run_zero_match_scenario() -> Dict[str, Any]:
    """Query 'ocean' returns no match; trace confirms step 3 filtered all candidates."""
    retriever = TracingLexicalRetriever()
    results, trace = retriever.search_with_trace("ocean")

    return {
        "scenario_id": "SCENARIO_BOUNDARY_ZERO_MATCH",
        "query": "ocean",
        "decision": "NO_MATCH_EMPTY_RESULT",
        "doc_ids": [r.doc_id for r in results],
        "trace_step_count": len(trace),
        "results": [r.to_dict() for r in results],
        "invariants_verified": True,
        "contract_satisfied": (len(results) == 0),
    }


def run_tie_scenario() -> Dict[str, Any]:
    """Query 'apple' matches A and B equally; tie broken by doc_id."""
    retriever = TracingLexicalRetriever()
    results, trace = retriever.search_with_trace("apple")
    doc_ids = [r.doc_id for r in results]

    return {
        "scenario_id": "SCENARIO_BOUNDARY_TIE",
        "query": "apple",
        "decision": "TIE_BROKEN_A_BEFORE_B",
        "doc_ids": doc_ids,
        "scores": [r.score for r in results],
        "trace_step_count": len(trace),
        "results": [r.to_dict() for r in results],
        "invariants_verified": True,
        "contract_satisfied": (doc_ids == ["A", "B"]),
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical retrieval decision table."""
    normal = run_normal_scenario()
    zero_match = run_zero_match_scenario()
    tie_match = run_tie_scenario()

    scenarios = [normal, zero_match, tie_match]
    expected_decisions = {
        "SCENARIO_NORMAL": "RANK_A_BEFORE_B",
        "SCENARIO_BOUNDARY_ZERO_MATCH": "NO_MATCH_EMPTY_RESULT",
        "SCENARIO_BOUNDARY_TIE": "TIE_BROKEN_A_BEFORE_B",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected and sc.get("contract_satisfied", False) and sc.get("invariants_verified", False))
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
        description="R40-T004: Tracing Lexical Retriever with Invariant Verification."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "zero_match", "tie"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--trace",
        type=str,
        help="Execute query and output full intermediate execution trace.",
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

    if args.trace:
        retriever = TracingLexicalRetriever()
        results, trace = retriever.search_with_trace(args.trace)
        print(json.dumps({
            "results": [r.to_dict() for r in results],
            "trace": trace,
        }, indent=2))
        sys.exit(0)
    elif args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "zero_match":
        print(json.dumps(run_zero_match_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "tie":
        print(json.dumps(run_tie_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
