#!/usr/bin/env python3
"""Ranked Search with Stable Ties — Failure and Recovery Worked Example (R40-T028).

Lesson 08: Building a Search Applications.
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a local ranked retrieval component modeling the core mechanisms
of search applications: token overlap scoring, source ID provenance attribution,
minimum-score threshold filtering, and deterministic stable tie-breaking.
It exercises documented invalid and missing-data edge cases, explains the diagnostic
errors, and demonstrates complete state recovery on the next valid input.

Contract Rules Implemented:
1. Retrieval Scoring: Ranks documents by token overlap between query and document text.
   Matches with higher overlap score appear first.
2. Source ID Provenance: Every search result preserves and returns the source document
   identifier ('id') alongside the retrieval score and source text for full auditability.
3. Stable Tie-Breaking: When multiple documents achieve equal overlap scores
   (e.g. query 'red' matching 'red apple' and 'red berry' equally with score 1.0),
   stable ascending document ID order ('doc-01' before 'doc-02') breaks the tie deterministically.
   This order is invariant to document insertion order in the underlying corpus.
4. Threshold Filtering: Applies a minimum-score threshold ('min_score', default 0.1).
   Candidates scoring strictly below the threshold (such as 'blue sky' with score 0.0)
   are omitted from the returned result set.
5. Error Resilience & Recovery:
   - Exercises documented invalid/missing-data cases (e.g. missing/empty query string,
     corpus documents missing required 'id' or 'text' fields, or negative thresholds).
   - Explains the exact failure mode with structured diagnostic exceptions.
   - Demonstrates immediate, clean recovery on the subsequent valid input without engine
     state corruption or memory leaks.

Classification & Scope Note (Simulation / Test Double):
This module is a deterministic local retrieval engine and test double implemented
exclusively using Python's standard library. It requires no vector embeddings download,
no OpenAI/Azure cloud credentials, no paid API keys, and no GPU hardware.

Where Simplifications Stop:
- Scoring uses exact token overlap rather than 1536-dimensional OpenAI embeddings
  (text-embedding-ada-002) or cosine distance; semantic synonyms (e.g. 'crimson' for 'red')
  are outside token overlap scope.
- In-memory data structures replace remote vector databases (e.g. Azure AI Search, Pinecone, Redis).
- Focus is on ranking invariants, deterministic tie-breaking, provenance, and input resilience.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================


class SearchError(Exception):
    """Base exception for all search engine operations."""


class SearchValidationError(SearchError):
    """Base exception for input and data validation errors."""


class InvalidQueryError(SearchValidationError):
    """Raised when a search query is missing, empty, or lacks valid search tokens."""

    def __init__(self, message: str, query: Any = None, reason: str = "", suggested_recovery: str = "") -> None:
        super().__init__(message)
        self.query = query
        self.reason = reason
        self.suggested_recovery = suggested_recovery


class MissingDataError(SearchValidationError):
    """Raised when required document fields (such as 'id' or 'text') are missing."""

    def __init__(self, message: str, field_name: str = "", doc_index: Optional[int] = None) -> None:
        super().__init__(message)
        self.field_name = field_name
        self.doc_index = doc_index


class CorpusValidationError(SearchValidationError):
    """Raised when the document corpus structure is malformed or contains duplicate IDs."""


class InvalidThresholdError(SearchValidationError):
    """Raised when the minimum score threshold parameter is invalid (e.g. negative)."""


class DecisionMismatchError(SearchError):
    """Raised when an assertion or verification check detects an unexpected outcome."""


# =============================================================================
# Data Structures
# =============================================================================


@dataclass(frozen=True)
class Document:
    """Represents an indexed document in the local search corpus."""

    id: str
    text: str
    tokens: Set[str] = field(default_factory=set, hash=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes document to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "tokens": sorted(list(self.tokens)),
        }


@dataclass(frozen=True)
class SearchResult:
    """Represents a ranked search match with provenance and score."""

    rank: int
    id: str
    score: float
    text: str
    matched_tokens: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes search result item to dictionary."""
        return {
            "rank": self.rank,
            "id": self.id,
            "score": round(self.score, 4),
            "text": self.text,
            "matched_tokens": self.matched_tokens,
        }


# =============================================================================
# Ranked Search Engine
# =============================================================================


class RankedSearchEngine:
    """Deterministic local search engine ranking documents by token overlap with stable tie-breaking."""

    def __init__(self, corpus: Optional[List[Dict[str, Any]]] = None) -> None:
        self._documents: List[Document] = []
        if corpus is not None:
            self.load_corpus(corpus)

    @property
    def documents(self) -> List[Document]:
        """Returns the indexed corpus documents."""
        return list(self._documents)

    @staticmethod
    def tokenize(text: str) -> Set[str]:
        """Extracts lowercase alphanumeric tokens from text."""
        if not text:
            return set()
        return set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))

    def load_corpus(self, raw_corpus: List[Dict[str, Any]]) -> None:
        """Validates and indexes a list of corpus documents.

        Raises:
            MissingDataError: If any document is missing 'id' or 'text'.
            CorpusValidationError: If corpus format is not a list or contains duplicate IDs.
        """
        if not isinstance(raw_corpus, list):
            raise CorpusValidationError(
                f"Corpus must be a list of document objects, got {type(raw_corpus).__name__}."
            )

        seen_ids: Set[str] = set()
        indexed_docs: List[Document] = []

        for idx, item in enumerate(raw_corpus):
            if not isinstance(item, dict):
                raise CorpusValidationError(
                    f"Document at index {idx} must be a dictionary, got {type(item).__name__}."
                )

            # Check required 'id'
            doc_id = item.get("id")
            if doc_id is None:
                raise MissingDataError(
                    f"Document at index {idx} is missing mandatory field 'id'.",
                    field_name="id",
                    doc_index=idx,
                )
            if not isinstance(doc_id, str) or not doc_id.strip():
                raise MissingDataError(
                    f"Document at index {idx} has invalid or empty 'id' field.",
                    field_name="id",
                    doc_index=idx,
                )
            doc_id = doc_id.strip()

            if doc_id in seen_ids:
                raise CorpusValidationError(
                    f"Duplicate document ID detected: '{doc_id}' at index {idx}."
                )
            seen_ids.add(doc_id)

            # Check required 'text'
            text = item.get("text")
            if text is None:
                raise MissingDataError(
                    f"Document '{doc_id}' (index {idx}) is missing mandatory field 'text'.",
                    field_name="text",
                    doc_index=idx,
                )
            if not isinstance(text, str):
                raise MissingDataError(
                    f"Document '{doc_id}' (index {idx}) 'text' field must be a string, got {type(text).__name__}.",
                    field_name="text",
                    doc_index=idx,
                )

            tokens = self.tokenize(text)
            indexed_docs.append(Document(id=doc_id, text=text, tokens=tokens))

        self._documents = indexed_docs

    def search(self, query: Any, min_score: float = 0.1) -> List[SearchResult]:
        """Ranks indexed corpus by token overlap against the query.

        Args:
            query: The search query string. Must be a non-empty string with alphanumeric tokens.
            min_score: Minimum overlap score threshold. Documents with score < min_score are omitted.

        Returns:
            List of SearchResult objects, sorted by (-score, doc_id).

        Raises:
            InvalidQueryError: If query is missing, empty, or has no valid search tokens.
            InvalidThresholdError: If min_score is negative or not a number.
        """
        # Validate query
        if query is None:
            raise InvalidQueryError(
                "Search query is missing or null. Query must be a non-empty string.",
                query=query,
                reason="missing_or_null_query",
                suggested_recovery="Provide a valid string query such as 'red'.",
            )

        if not isinstance(query, str):
            raise InvalidQueryError(
                f"Search query must be a string, got {type(query).__name__}.",
                query=query,
                reason="invalid_query_type",
                suggested_recovery="Pass a string value for query parameter.",
            )

        trimmed_query = query.strip()
        if not trimmed_query:
            raise InvalidQueryError(
                "Search query is missing or empty. Query must be a non-empty string containing at least one alphanumeric token.",
                query=query,
                reason="empty_query_string",
                suggested_recovery="Provide a non-empty query string such as 'red'.",
            )

        query_tokens = self.tokenize(trimmed_query)
        if not query_tokens:
            raise InvalidQueryError(
                f"Query '{query}' contains no valid alphanumeric search tokens.",
                query=query,
                reason="no_alphanumeric_tokens",
                suggested_recovery="Include at least one word character in your query.",
            )

        # Validate threshold
        if not isinstance(min_score, (int, float)):
            raise InvalidThresholdError(
                f"min_score threshold must be numeric, got {type(min_score).__name__}."
            )
        if min_score < 0.0:
            raise InvalidThresholdError(
                f"min_score threshold must be non-negative, got {min_score}."
            )

        # Score documents by token overlap
        candidates: List[Tuple[float, str, Document, List[str]]] = []
        for doc in self._documents:
            matched = query_tokens.intersection(doc.tokens)
            score = float(len(matched))

            # Apply minimum score threshold: strictly exclude candidates scoring below min_score
            if score >= min_score:
                candidates.append((score, doc.id, doc, sorted(list(matched))))

        # Stable tie-breaking:
        # Sort key: (-score, doc_id)
        # Primary: descending score (highest score first)
        # Secondary: ascending document ID (stable tie-breaker)
        candidates.sort(key=lambda item: (-item[0], item[1]))

        results: List[SearchResult] = []
        for rank_idx, (score, doc_id, doc, matched_tokens) in enumerate(candidates, start=1):
            results.append(
                SearchResult(
                    rank=rank_idx,
                    id=doc.id,
                    score=score,
                    text=doc.text,
                    matched_tokens=matched_tokens,
                )
            )

        return results


# =============================================================================
# Canonical Fixtures & Scenarios
# =============================================================================

DEFAULT_CORPUS: List[Dict[str, Any]] = [
    {"id": "doc-01", "text": "red apple"},
    {"id": "doc-02", "text": "red berry"},
    {"id": "doc-03", "text": "blue sky"},
]

DEFAULT_QUERY = "red"
DEFAULT_MIN_SCORE = 0.1


def run_normal_scenario() -> Dict[str, Any]:
    """Executes the canonical normal ranked search scenario.

    Corpus:
      - doc-01: 'red apple'
      - doc-02: 'red berry'
      - doc-03: 'blue sky'
    Query: 'red' (min_score=0.1)

    Expected Outcome:
      - 'red apple' and 'red berry' match equally with score 1.0.
      - Stable ID order ('doc-01' < 'doc-02') breaks the tie.
      - 'blue sky' scores 0.0 and is omitted.
    """
    engine = RankedSearchEngine(DEFAULT_CORPUS)
    results = engine.search(query=DEFAULT_QUERY, min_score=DEFAULT_MIN_SCORE)

    results_serialized = [r.to_dict() for r in results]
    returned_ids = [r.id for r in results]
    all_doc_ids = [d["id"] for d in DEFAULT_CORPUS]
    omitted_ids = [did for did in all_doc_ids if did not in returned_ids]

    # Invariants verification
    has_two_results = len(results) == 2
    equal_scores = results[0].score == 1.0 and results[1].score == 1.0
    stable_order = returned_ids == ["doc-01", "doc-02"]
    blue_sky_omitted = "doc-03" in omitted_ids

    decision = "RANKED_SEARCH_SUCCESS" if (has_two_results and equal_scores and stable_order and blue_sky_omitted) else "UNEXPECTED_SEARCH_OUTCOME"

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "decision": decision,
        "query": DEFAULT_QUERY,
        "min_score": DEFAULT_MIN_SCORE,
        "total_candidates": len(DEFAULT_CORPUS),
        "results_count": len(results),
        "omitted_count": len(omitted_ids),
        "results": results_serialized,
        "omitted_ids": omitted_ids,
        "tie_broken_by_stable_id": stable_order,
        "zero_score_omitted": blue_sky_omitted,
        "rationale": (
            "Query 'red' matched 'red apple' (doc-01) and 'red berry' (doc-02) equally with score 1.0. "
            "Stable ID order ('doc-01' < 'doc-02') broke the tie deterministically. "
            "'blue sky' (doc-03) scored 0.0 and was omitted below min_score 0.1."
        ),
        "classification": "ranked_search_simulation",
    }


def run_failure_scenario() -> Dict[str, Any]:
    """Executes the documented invalid/missing-data failure scenario.

    Exercises missing query input (empty string '').
    Verifies that the engine raises InvalidQueryError with an explanatory diagnostic
    and remediation suggestion, while preserving the engine's internal state.
    """
    engine = RankedSearchEngine(DEFAULT_CORPUS)
    invalid_query = ""

    caught_error_type: Optional[str] = None
    caught_error_message: Optional[str] = None
    caught_reason: Optional[str] = None
    suggested_recovery: Optional[str] = None

    try:
        engine.search(query=invalid_query, min_score=DEFAULT_MIN_SCORE)
    except InvalidQueryError as err:
        caught_error_type = err.__class__.__name__
        caught_error_message = str(err)
        caught_reason = err.reason
        suggested_recovery = err.suggested_recovery

    rejection_verified = caught_error_type == "InvalidQueryError"
    engine_state_preserved = len(engine.documents) == 3

    decision = "INVALID_DATA_REJECTED" if (rejection_verified and engine_state_preserved) else "FAILURE_NOT_HANDLED"

    return {
        "scenario_id": "SCENARIO_FAILURE",
        "scenario_type": "invalid_data_rejection",
        "decision": decision,
        "query": invalid_query,
        "error_type": caught_error_type,
        "error_message": caught_error_message,
        "reason": caught_reason,
        "suggested_recovery": suggested_recovery,
        "rejection_verified": rejection_verified,
        "engine_state_preserved": engine_state_preserved,
        "rationale": (
            "Missing search query '' was safely rejected with InvalidQueryError. "
            "A structured diagnostic reason and recovery suggestion were provided, "
            "and the internal search index remained intact without state corruption."
        ),
        "classification": "ranked_search_simulation",
    }


def run_recovery_scenario() -> Dict[str, Any]:
    """Executes failure and recovery in sequence on the same engine instance.

    Step 1: Submits invalid missing query '' -> caught and explained.
    Step 2: Submits subsequent valid query 'red' -> executes successfully and returns
            ranked results with stable tie-break and zero-score omission.
    """
    engine = RankedSearchEngine(DEFAULT_CORPUS)

    # Step 1: Invalid input failure
    invalid_query = ""
    error_caught = False
    error_msg = ""
    try:
        engine.search(query=invalid_query, min_score=DEFAULT_MIN_SCORE)
    except InvalidQueryError as err:
        error_caught = True
        error_msg = str(err)

    # Step 2: Next valid input recovery
    valid_query = "red"
    results = engine.search(query=valid_query, min_score=DEFAULT_MIN_SCORE)
    returned_ids = [r.id for r in results]

    recovered = (
        error_caught
        and len(results) == 2
        and returned_ids == ["doc-01", "doc-02"]
        and results[0].score == 1.0
        and results[1].score == 1.0
    )

    decision = "ERROR_RECOVERY_SUCCESS" if recovered else "RECOVERY_FAILED"

    return {
        "scenario_id": "SCENARIO_RECOVERY",
        "scenario_type": "failure_and_recovery",
        "decision": decision,
        "invalid_step": {
            "query": invalid_query,
            "caught_error": "InvalidQueryError" if error_caught else None,
            "error_explanation": error_msg,
            "rejected": error_caught,
        },
        "recovery_step": {
            "query": valid_query,
            "status": "success",
            "results_count": len(results),
            "top_id": results[0].id if results else None,
            "top_score": results[0].score if results else None,
            "second_id": results[1].id if len(results) > 1 else None,
            "second_score": results[1].score if len(results) > 1 else None,
            "omitted_id": "doc-03",
        },
        "recovery_verified": recovered,
        "state_consistency_maintained": len(engine.documents) == 3,
        "rationale": (
            "Engine intercepted invalid empty query with documented InvalidQueryError, "
            "maintained internal state consistency, and cleanly recovered on next valid "
            "query 'red', returning accurate ranked results with stable tie-breaking."
        ),
        "classification": "ranked_search_simulation",
    }


def run_boundary_scenario() -> Dict[str, Any]:
    """Verifies edge conditions and ranking invariants:
    1. Score equality verification: doc-01 and doc-02 tie exactly at 1.0.
    2. Insertion order invariance: indexing doc-02 before doc-01 still ranks doc-01 first.
    3. Threshold cutoff boundary: score 0.0 < min_score 0.1 strictly excluded.
    4. Zero-match query handling: query with valid token not matching any doc yields [].
    """
    # Invariant 1 & 3: Standard corpus
    engine1 = RankedSearchEngine(DEFAULT_CORPUS)
    results1 = engine1.search("red", min_score=0.1)
    tie_score_equality = len(results1) == 2 and results1[0].score == results1[1].score == 1.0
    zero_score_excluded = "doc-03" not in [r.id for r in results1]

    # Invariant 2: Inverted corpus insertion order [doc-02, doc-01, doc-03]
    inverted_corpus = [
        {"id": "doc-02", "text": "red berry"},
        {"id": "doc-01", "text": "red apple"},
        {"id": "doc-03", "text": "blue sky"},
    ]
    engine2 = RankedSearchEngine(inverted_corpus)
    results2 = engine2.search("red", min_score=0.1)
    # Despite doc-02 inserted first, stable ID tie-breaker must place doc-01 first
    order_invariance = [r.id for r in results2] == ["doc-01", "doc-02"]

    # Invariant 4: Zero-match valid query (e.g. 'yellow')
    results_zero = engine1.search("yellow", min_score=0.1)
    zero_match_handled = len(results_zero) == 0

    all_invariants_pass = (
        tie_score_equality
        and order_invariance
        and zero_score_excluded
        and zero_match_handled
    )

    decision = "BOUNDARY_INVARIANTS_VERIFIED" if all_invariants_pass else "BOUNDARY_CHECK_FAILED"

    return {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_invariants",
        "decision": decision,
        "tie_score_equality_verified": tie_score_equality,
        "order_invariance_verified": order_invariance,
        "zero_score_exclusion_verified": zero_score_excluded,
        "zero_match_query_handled": zero_match_handled,
        "min_score_applied": 0.1,
        "rationale": (
            "All boundary invariants verified: exact score tie (1.0 == 1.0), "
            "insertion order invariance ('doc-01' precedes 'doc-02' even when indexed second), "
            "strict zero-score omission below threshold, and graceful empty list for zero matches."
        ),
        "classification": "ranked_search_simulation",
    }


# =============================================================================
# Decision Table & Canonical Check
# =============================================================================

CANONICAL_DECISION_TABLE: List[Dict[str, Any]] = [
    {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "expected_decision": "RANKED_SEARCH_SUCCESS",
        "expected_results_count": 2,
        "expected_omitted_count": 1,
        "expected_top_id": "doc-01",
        "expected_second_id": "doc-02",
    },
    {
        "scenario_id": "SCENARIO_FAILURE",
        "scenario_type": "invalid_data_rejection",
        "expected_decision": "INVALID_DATA_REJECTED",
        "expected_error_type": "InvalidQueryError",
        "expected_rejection": True,
    },
    {
        "scenario_id": "SCENARIO_RECOVERY",
        "scenario_type": "failure_and_recovery",
        "expected_decision": "ERROR_RECOVERY_SUCCESS",
        "expected_recovered": True,
        "expected_top_id": "doc-01",
    },
    {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_invariants",
        "expected_decision": "BOUNDARY_INVARIANTS_VERIFIED",
        "expected_order_invariance": True,
        "expected_zero_score_exclusion": True,
    },
]


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Runs all canonical scenarios and validates them against the decision table.

    If tamper=True, deliberately introduces a specification mismatch to prove
    that regressions and unexpected results strictly fail verification.
    """
    results: List[Dict[str, Any]] = []
    actual_scenarios = [
        run_normal_scenario(),
        run_failure_scenario(),
        run_recovery_scenario(),
        run_boundary_scenario(),
    ]

    for spec, actual in zip(CANONICAL_DECISION_TABLE, actual_scenarios):
        expected_decision = spec["expected_decision"]
        if tamper and spec["scenario_id"] == "SCENARIO_NORMAL":
            # Deliberately mutate expectation to simulate wrong assertion
            expected_decision = "DELIBERATE_MUTATED_DECISION"

        matches = (actual["decision"] == expected_decision)

        item = {
            "scenario_id": spec["scenario_id"],
            "scenario_type": spec["scenario_type"],
            "expected_decision": expected_decision,
            "actual_decision": actual["decision"],
            "matches_table": matches,
            "status": "PASS" if matches else "FAIL",
            "rationale": actual["rationale"],
        }
        results.append(item)

    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    passed_count = len(results) - failed_count

    summary = {
        "status": "success" if failed_count == 0 else "failure",
        "total_scenarios": len(results),
        "passed_scenarios": passed_count,
        "failed_scenarios": failed_count,
        "all_passed": (failed_count == 0),
        "classification": "ranked_search_simulation",
        "scenarios": results,
    }

    if failed_count > 0:
        raise DecisionMismatchError(
            f"Verification failed: {failed_count} scenario(s) did not match the canonical decision table."
        )

    return summary


# =============================================================================
# CLI Entrypoint
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Configures command line arguments."""
    parser = argparse.ArgumentParser(
        description="R40-T028: Ranked Search with Stable Ties Worked Example"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scenario",
        choices=["normal", "failure", "recovery", "boundary"],
        help="Run an individual scenario and output structured JSON.",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Run all canonical scenarios against the decision table.",
    )
    group.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate a deliberate regression to prove failure detection.",
    )
    return parser


def main() -> int:
    """CLI main function."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.scenario == "normal":
            data = run_normal_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.scenario == "failure":
            data = run_failure_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.scenario == "recovery":
            data = run_recovery_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.scenario == "boundary":
            data = run_boundary_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.check:
            data = run_canonical_check(tamper=False)
            print(json.dumps(data, indent=2))
            return 0

        if args.tamper:
            try:
                run_canonical_check(tamper=True)
            except DecisionMismatchError as err:
                tamper_output = {
                    "status": "expected_tamper_failure",
                    "error_type": err.__class__.__name__,
                    "error_message": str(err),
                    "exit_code": 1,
                    "classification": "ranked_search_simulation",
                    "rationale": "Deliberately mutated expectation failed assertion as expected.",
                }
                print(json.dumps(tamper_output, indent=2), file=sys.stderr)
                return 1
            print("ERROR: Tampered execution did not fail!", file=sys.stderr)
            return 2

    except Exception as exc:
        print(f"Execution failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
