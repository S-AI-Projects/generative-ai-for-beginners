#!/usr/bin/env python3
"""Applied Lab (R40-T026): Lexical Retriever with Source Attribution and Equivalence Refactoring.

This module extends Lesson 20 ("Building with Mistral Models") at 20-mistral/README.md.
It builds a tiny lexical retriever over local documents, scoring query/document
overlap on lowercase word sets and breaking ties by document ID.

CLASSIFICATION & SCOPE NOTE:
This component is strictly a LEXICAL TEST DOUBLE, not a production vector search.
It uses deterministic set intersection over lowercase word tokens and requires no
vector embeddings, no external vector database (FAISS/Chroma), no GPU hardware,
and no remote cloud provider or API credentials.

CONTRIBUTION FOCUS:
Implement a correct baseline retriever, then extract one named responsibility
(`WordSetOverlapScorer`). Maintain the identical retrieval contract and prove
before/after equivalence on the document fixture.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


# =============================================================================
# Domain Models & Contracts
# =============================================================================

@dataclass(frozen=True)
class Document:
    """A source document with an identifier and text content."""
    doc_id: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """A retrieved document match with score and source attribution."""
    doc_id: str
    score: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "score": self.score,
            "text": self.text,
        }


# Canonical Fixture as specified in Task R40-T026
DEFAULT_CORPUS: Tuple[Document, ...] = (
    Document(doc_id="A", text="red apple"),
    Document(doc_id="B", text="green apple"),
    Document(doc_id="C", text="blue sky"),
)


# =============================================================================
# 1. Baseline Implementation (Monolithic Retriever)
# =============================================================================

class BaselineLexicalRetriever:
    """Monolithic baseline lexical retriever.
    
    Couples tokenization, overlap scoring, score filtering, and tie-breaking
    directly inside a single class/method.
    
    Contract:
      retrieve(query: str) -> List[SearchResult]
    
    Tie-breaking rule:
      Primary: Overlap score descending.
      Secondary: Document ID ascending (alphabetical).
      Filters out documents with score == 0.
    """

    def __init__(self, corpus: Sequence[Document] = DEFAULT_CORPUS) -> None:
        self._corpus: Tuple[Document, ...] = tuple(corpus)

    @property
    def corpus(self) -> Tuple[Document, ...]:
        return self._corpus

    def retrieve(self, query: str) -> List[SearchResult]:
        """Executes lexical search over corpus using inline word-set overlap."""
        # Baseline monolithic tokenization of query
        query_words: Set[str] = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        if not query_words:
            return []

        scored_results: List[SearchResult] = []
        for doc in self._corpus:
            # Baseline monolithic tokenization of document text
            doc_words: Set[str] = set(re.findall(r"[a-zA-Z0-9]+", doc.text.lower()))
            overlap_count = len(query_words & doc_words)
            if overlap_count > 0:
                scored_results.append(
                    SearchResult(
                        doc_id=doc.doc_id,
                        score=overlap_count,
                        text=doc.text,
                    )
                )

        # Baseline inline sorting: score descending, doc_id ascending
        scored_results.sort(key=lambda r: (-r.score, r.doc_id))
        return scored_results


# =============================================================================
# 2. Extracted Named Responsibility: WordSetOverlapScorer
# =============================================================================

class WordSetOverlapScorer:
    """Extracted named responsibility: Token normalization and lexical overlap scoring.
    
    Separates the mathematical and lexical scoring policy from collection indexing
    and tie-breaking orchestration.
    """

    def tokenize(self, text: str) -> Set[str]:
        """Normalizes text into a set of lowercase alphanumeric word tokens."""
        if not text:
            return set()
        return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))

    def score_tokens(self, query_tokens: Set[str], doc_tokens: Set[str]) -> int:
        """Computes overlap score as the cardinality of word-set intersection."""
        if not query_tokens or not doc_tokens:
            return 0
        return len(query_tokens & doc_tokens)

    def score(self, query: str, doc_text: str) -> int:
        """Convenience method to tokenize and score raw text strings."""
        return self.score_tokens(self.tokenize(query), self.tokenize(doc_text))


# =============================================================================
# 3. Refactored Implementation (Composed Retriever)
# =============================================================================

class RefactoredLexicalRetriever:
    """Refactored lexical retriever with extracted WordSetOverlapScorer.
    
    Preserves the exact public retrieval contract and tie-breaking guarantees
    while delegating tokenization and scoring to WordSetOverlapScorer.
    
    Contract:
      retrieve(query: str) -> List[SearchResult]
    """

    def __init__(
        self,
        corpus: Sequence[Document] = DEFAULT_CORPUS,
        scorer: Optional[WordSetOverlapScorer] = None,
    ) -> None:
        self._corpus: Tuple[Document, ...] = tuple(corpus)
        self._scorer: WordSetOverlapScorer = scorer if scorer is not None else WordSetOverlapScorer()
        # Pre-tokenize documents for clean separated indexing
        self._tokenized_corpus: List[Tuple[Document, Set[str]]] = [
            (doc, self._scorer.tokenize(doc.text)) for doc in self._corpus
        ]

    @property
    def corpus(self) -> Tuple[Document, ...]:
        return self._corpus

    @property
    def scorer(self) -> WordSetOverlapScorer:
        return self._scorer

    def retrieve(self, query: str) -> List[SearchResult]:
        """Executes lexical search by delegating scoring to WordSetOverlapScorer."""
        query_tokens = self._scorer.tokenize(query)
        if not query_tokens:
            return []

        candidates: List[SearchResult] = []
        for doc, doc_tokens in self._tokenized_corpus:
            overlap = self._scorer.score_tokens(query_tokens, doc_tokens)
            if overlap > 0:
                candidates.append(
                    SearchResult(
                        doc_id=doc.doc_id,
                        score=overlap,
                        text=doc.text,
                    )
                )

        # Deterministic tie-breaking: score descending (-score), doc_id ascending (+doc_id)
        candidates.sort(key=lambda r: (-r.score, r.doc_id))
        return candidates


# =============================================================================
# 4. Equivalence Prover
# =============================================================================

class EquivalenceMismatchError(RuntimeError):
    """Raised when baseline and refactored retrievers diverge on identical queries."""
    pass


def prove_before_after_equivalence(
    baseline: BaselineLexicalRetriever,
    refactored: RefactoredLexicalRetriever,
    queries: Sequence[str],
) -> Dict[str, Any]:
    """Proves that baseline and refactored retrievers yield identical results.
    
    Asserts:
      1. Exactly the same number of results returned.
      2. Exactly the same document IDs in the exact same ranked order.
      3. Exactly the same overlap scores.
      4. Exactly the same document texts.
    """
    comparisons: List[Dict[str, Any]] = []

    for query in queries:
        base_res = baseline.retrieve(query)
        ref_res = refactored.retrieve(query)

        base_dicts = [r.to_dict() for r in base_res]
        ref_dicts = [r.to_dict() for r in ref_res]

        if base_dicts != ref_dicts:
            raise EquivalenceMismatchError(
                f"Equivalence failure for query '{query}':\n"
                f"Baseline:   {base_dicts}\n"
                f"Refactored: {ref_dicts}"
            )

        comparisons.append({
            "query": query,
            "baseline_count": len(base_res),
            "refactored_count": len(ref_res),
            "match": True,
            "ranked_doc_ids": [r.doc_id for r in ref_res],
            "scores": [r.score for r in ref_res],
        })

    return {
        "status": "EQUIVALENCE_PROVEN",
        "total_queries_tested": len(queries),
        "all_identical": True,
        "comparisons": comparisons,
    }


# =============================================================================
# 5. Citation & Prompt Attribution Helper
# =============================================================================

def format_prompt_citations(results: Sequence[SearchResult]) -> str:
    """Formats retrieved chunks with document IDs for source-attributed prompts.
    
    Enhances the Lesson 20 Mistral RAG pattern with clear source attribution.
    """
    if not results:
        return "No relevant context found."
    lines: List[str] = []
    for r in results:
        lines.append(f"[Source {r.doc_id}] (Score: {r.score}): {r.text}")
    return "\n".join(lines)


# =============================================================================
# 6. Canonical Decision Framework & Scenarios
# =============================================================================

class ScenarioDecision(str, Enum):
    RETRIEVAL_SUCCESS_RANKED = "RETRIEVAL_SUCCESS_RANKED"
    EMPTY_RESULT_NO_MATCH = "EMPTY_RESULT_NO_MATCH"
    RETRIEVAL_TIEBREAK_RESOLVED = "RETRIEVAL_TIEBREAK_RESOLVED"
    REFACTORING_EQUIVALENCE_PROVEN = "REFACTORING_EQUIVALENCE_PROVEN"


CANONICAL_DECISION_TABLE: Dict[str, Dict[str, Any]] = {
    "SCENARIO_NORMAL": {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "query": "red apple",
        "corpus_ids": ["A", "B", "C"],
        "expected_decision": ScenarioDecision.RETRIEVAL_SUCCESS_RANKED.value,
        "expected_doc_ids": ["A", "B"],
        "expected_scores": [2, 1],
        "rationale_keywords": ["ranks A before B", "overlap", "Doc C omitted", "source attribution"],
        "rationale": "Query 'red apple' overlaps Doc A on {'red', 'apple'} (score 2) and Doc B on {'apple'} (score 1). Ranks A before B with source attribution; Doc C ('blue sky') has 0 overlap and is omitted.",
    },
    "SCENARIO_BOUNDARY": {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary",
        "query": "ocean",
        "corpus_ids": ["A", "B", "C"],
        "expected_decision": ScenarioDecision.EMPTY_RESULT_NO_MATCH.value,
        "expected_doc_ids": [],
        "expected_scores": [],
        "rationale_keywords": ["ocean", "no match", "empty", "zero overlap"],
        "rationale": "Query 'ocean' has zero word overlap with any document in the corpus. The retriever cleanly returns an empty match set [], avoiding hallucination or irrelevant prompt context.",
    },
    "SCENARIO_TIEBREAK": {
        "scenario_id": "SCENARIO_TIEBREAK",
        "scenario_type": "boundary",
        "query": "apple",
        "corpus_ids": ["A", "B", "C"],
        "expected_decision": ScenarioDecision.RETRIEVAL_TIEBREAK_RESOLVED.value,
        "expected_doc_ids": ["A", "B"],
        "expected_scores": [1, 1],
        "rationale_keywords": ["tie", "document ID", "score 1", "A before B"],
        "rationale": "Query 'apple' matches Doc A and Doc B with identical score 1. The tie-breaking rule deterministically ranks Doc A before Doc B using document ID order ('A' < 'B').",
    },
    "SCENARIO_EQUIVALENCE": {
        "scenario_id": "SCENARIO_EQUIVALENCE",
        "scenario_type": "equivalence",
        "queries": ["red apple", "ocean", "apple", "green apple", "blue sky", "red", "green", "blue", "apple sky", ""],
        "corpus_ids": ["A", "B", "C"],
        "expected_decision": ScenarioDecision.REFACTORING_EQUIVALENCE_PROVEN.value,
        "expected_doc_ids": None,
        "expected_scores": None,
        "rationale_keywords": ["baseline", "refactored", "identical", "WordSetOverlapScorer"],
        "rationale": "BaselineLexicalRetriever and RefactoredLexicalRetriever (with extracted WordSetOverlapScorer) produce 100% identical ranked results, document IDs, and scores across all fixture queries.",
    },
}


class DecisionMismatchError(RuntimeError):
    """Raised when actual scenario output diverges from published decision table."""
    pass


def execute_scenario(
    scenario_id: str,
    retriever: Optional[RefactoredLexicalRetriever] = None,
    baseline: Optional[BaselineLexicalRetriever] = None,
) -> Dict[str, Any]:
    """Executes a canonical scenario and returns structured result."""
    if scenario_id not in CANONICAL_DECISION_TABLE:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")

    spec = CANONICAL_DECISION_TABLE[scenario_id]
    r = retriever if retriever is not None else RefactoredLexicalRetriever()
    b = baseline if baseline is not None else BaselineLexicalRetriever()

    if scenario_id == "SCENARIO_NORMAL":
        query = spec["query"]
        results = r.retrieve(query)
        doc_ids = [res.doc_id for res in results]
        scores = [res.score for res in results]
        decision = ScenarioDecision.RETRIEVAL_SUCCESS_RANKED.value
        citation_block = format_prompt_citations(results)

        return {
            "scenario_id": scenario_id,
            "scenario_type": spec["scenario_type"],
            "query": query,
            "decision": decision,
            "doc_ids": doc_ids,
            "scores": scores,
            "results": [res.to_dict() for res in results],
            "citation_block": citation_block,
            "rationale": spec["rationale"],
            "classification": "lexical_test_double",
        }

    elif scenario_id == "SCENARIO_BOUNDARY":
        query = spec["query"]
        results = r.retrieve(query)
        doc_ids = [res.doc_id for res in results]
        scores = [res.score for res in results]
        decision = ScenarioDecision.EMPTY_RESULT_NO_MATCH.value

        return {
            "scenario_id": scenario_id,
            "scenario_type": spec["scenario_type"],
            "query": query,
            "decision": decision,
            "doc_ids": doc_ids,
            "scores": scores,
            "results": [res.to_dict() for res in results],
            "citation_block": format_prompt_citations(results),
            "rationale": spec["rationale"],
            "classification": "lexical_test_double",
        }

    elif scenario_id == "SCENARIO_TIEBREAK":
        query = spec["query"]
        results = r.retrieve(query)
        doc_ids = [res.doc_id for res in results]
        scores = [res.score for res in results]
        decision = ScenarioDecision.RETRIEVAL_TIEBREAK_RESOLVED.value

        return {
            "scenario_id": scenario_id,
            "scenario_type": spec["scenario_type"],
            "query": query,
            "decision": decision,
            "doc_ids": doc_ids,
            "scores": scores,
            "results": [res.to_dict() for res in results],
            "citation_block": format_prompt_citations(results),
            "rationale": spec["rationale"],
            "classification": "lexical_test_double",
        }

    elif scenario_id == "SCENARIO_EQUIVALENCE":
        proof = prove_before_after_equivalence(b, r, spec["queries"])
        return {
            "scenario_id": scenario_id,
            "scenario_type": spec["scenario_type"],
            "decision": ScenarioDecision.REFACTORING_EQUIVALENCE_PROVEN.value,
            "proof": proof,
            "rationale": spec["rationale"],
            "classification": "lexical_test_double",
        }

    raise ValueError(f"Unhandled scenario: {scenario_id}")


def run_decision_table_check(
    tamper_scenario: Optional[str] = None,
    tamper_field: str = "expected_decision",
) -> Dict[str, Any]:
    """Runs the published decision table checker across all canonical scenarios.
    
    If tamper_scenario is provided, mutates that scenario's expected output
    to verify that the checker strictly raises DecisionMismatchError.
    """
    scenario_reports: List[Dict[str, Any]] = []
    retriever = RefactoredLexicalRetriever()
    baseline = BaselineLexicalRetriever()

    for sc_id, spec in CANONICAL_DECISION_TABLE.items():
        actual = execute_scenario(sc_id, retriever=retriever, baseline=baseline)
        expected_decision = spec["expected_decision"]

        # Apply deliberate tamper if requested
        if tamper_scenario == sc_id:
            if tamper_field == "expected_decision":
                expected_decision = "DELIBERATELY_MUTATED_WRONG_DECISION"
            elif tamper_field == "doc_ids":
                actual["doc_ids"] = ["WRONG_DOC_ORDER"]

        # Validate decision match
        if actual["decision"] != expected_decision:
            raise DecisionMismatchError(
                f"Scenario '{sc_id}' decision mismatch: "
                f"expected '{expected_decision}', got '{actual['decision']}'"
            )

        # Validate doc_ids match when expected
        if spec.get("expected_doc_ids") is not None:
            if actual["doc_ids"] != spec["expected_doc_ids"]:
                raise DecisionMismatchError(
                    f"Scenario '{sc_id}' doc_ids mismatch: "
                    f"expected {spec['expected_doc_ids']}, got {actual['doc_ids']}"
                )

        # Validate scores match when expected
        if spec.get("expected_scores") is not None:
            if actual["scores"] != spec["expected_scores"]:
                raise DecisionMismatchError(
                    f"Scenario '{sc_id}' scores mismatch: "
                    f"expected {spec['expected_scores']}, got {actual['scores']}"
                )

        scenario_reports.append({
            "scenario_id": sc_id,
            "scenario_type": spec["scenario_type"],
            "expected_decision": expected_decision,
            "actual_decision": actual["decision"],
            "matches_table": True,
            "status": "PASS",
            "doc_ids": actual.get("doc_ids"),
            "scores": actual.get("scores"),
            "rationale": spec["rationale"],
        })

    return {
        "status": "success",
        "total_scenarios": len(scenario_reports),
        "passed_scenarios": len(scenario_reports),
        "failed_scenarios": 0,
        "all_passed": True,
        "classification": "lexical_test_double",
        "scenarios": scenario_reports,
    }


# =============================================================================
# CLI Interface
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="R40-T026 Lexical Retriever with Source Attribution and Equivalence Refactoring"
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "tiebreak", "equivalence", "all"],
        default=None,
        help="Execute a specific canonical scenario",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run published decision table check across all canonical scenarios",
    )
    parser.add_argument(
        "--prove-equivalence",
        action="store_true",
        help="Prove baseline vs refactored equivalence across query suite",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Execute ad-hoc query over default corpus",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Demonstrate deliberate wrong result / mutation failure",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if args.tamper:
        print("[DEMO] Injecting deliberate tamper into SCENARIO_NORMAL expected decision...")
        try:
            run_decision_table_check(tamper_scenario="SCENARIO_NORMAL")
            print("[ERROR] Expected DecisionMismatchError was not raised!")
            return 0
        except DecisionMismatchError as err:
            print(f"[EXPECTED FAILURE CONFIRMED] Caught: {err}")
            return 1

    if args.check or args.scenario == "all":
        report = run_decision_table_check()
        print(json.dumps(report, indent=2))
        return 0

    if args.prove_equivalence:
        b = BaselineLexicalRetriever()
        r = RefactoredLexicalRetriever()
        queries = ["red apple", "ocean", "apple", "green apple", "blue sky", "red", "green", "blue", "apple sky", ""]
        proof = prove_before_after_equivalence(b, r, queries)
        print(json.dumps(proof, indent=2))
        return 0

    if args.scenario:
        scenario_map = {
            "normal": "SCENARIO_NORMAL",
            "boundary": "SCENARIO_BOUNDARY",
            "tiebreak": "SCENARIO_TIEBREAK",
            "equivalence": "SCENARIO_EQUIVALENCE",
        }
        report = execute_scenario(scenario_map[args.scenario])
        print(json.dumps(report, indent=2))
        return 0

    if args.query is not None:
        r = RefactoredLexicalRetriever()
        res = r.retrieve(args.query)
        output = {
            "query": args.query,
            "results": [item.to_dict() for item in res],
            "citations": format_prompt_citations(res),
            "classification": "lexical_test_double",
        }
        print(json.dumps(output, indent=2))
        return 0

    # Default action: run decision table check
    report = run_decision_table_check()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
