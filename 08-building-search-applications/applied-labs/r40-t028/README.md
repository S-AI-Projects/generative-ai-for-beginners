# Applied Lab: Ranked Search with Stable Ties — Failure and Recovery (R40-T028)

## Overview & Lesson 08 Context

In [Lesson 08 — Building a Search Applications](../../README.md?WT.mc_id=academic-105485-koreyst), we explore how search applications retrieve and rank relevant documents from a corpus against user queries. Real-world search and Retrieval-Augmented Generation (RAG) pipelines rely on four fundamental pillars:
1. **Retrieval Scoring**: Quantifying the relevance between user queries and candidate documents.
2. **Provenance Attribution**: Returning source identifiers (`id`) and text alongside similarity scores for citation and auditability.
3. **Stable Tie-Breaking**: Ensuring that when multiple documents achieve identical scores, ranking remains 100% deterministic, predictable, and reproducible.
4. **Relevance Threshold Filtering**: Omitting non-relevant documents whose scores fail to satisfy a minimum threshold.

This applied lab provides a self-contained reference implementation and regression test suite modeling these core mechanics using token overlap, stable tie-breaking, input validation, and state recovery.

---

## Contract & Invariants

The ranked search engine enforces six foundational invariants:

1. **Token Overlap Retrieval Scoring**:
   - Queries and documents are tokenized into case-insensitive alphanumeric tokens.
   - Retrieval score is calculated as the token overlap between query tokens and document tokens ($|Q \cap D|$).
   - Candidates with higher scores rank ahead of candidates with lower scores.

2. **Source ID Provenance**:
   - Every returned search result item contains the document's unique identifier (`id`), retrieval score (`score`), matched tokens (`matched_tokens`), and document text (`text`).
   - Callers and UI layers can trace every match directly back to its source record.

3. **Deterministic Stable Tie-Breaking**:
   - When multiple documents match equally (e.g., query `"red"` matches `"red apple"` and `"red berry"` with identical score `1.0`), ties are broken deterministically by sorting ascending by document ID (`doc-01` < `doc-02`).
   - Ranking order is invariant to the insertion order of documents in the corpus (e.g., indexing `doc-02` before `doc-01` still produces `doc-01` as Rank 1 and `doc-02` as Rank 2).

4. **Minimum-Score Threshold Filtering**:
   - A configurable `min_score` threshold (default `0.1`) is applied to all candidates.
   - Candidates scoring strictly below `min_score` are omitted from the returned result set.
   - For example, candidate `"blue sky"` (score `0.0`) is omitted when searching for `"red"`.

5. **Input Validation & Documented Error Taxonomy**:
   - Empty, whitespace-only, `None`, or non-string query inputs raise `InvalidQueryError` with structured diagnostic reasons (`empty_query_string`, `missing_or_null_query`, `invalid_query_type`) and suggested recovery actions.
   - Queries containing no alphanumeric tokens raise `InvalidQueryError` (`no_alphanumeric_tokens`).
   - Malformed corpus documents (missing `id` or missing/non-string `text`) raise `MissingDataError`.
   - Malformed corpus containers or duplicate document IDs raise `CorpusValidationError`.
   - Negative threshold values raise `InvalidThresholdError`.

6. **State Resiliency & Clean Recovery**:
   - Rejecting an invalid input or encountering an error leaves the search engine's internal corpus and state completely uncorrupted.
   - The engine cleanly and successfully executes the subsequent valid input without process restart, memory leaks, or state degradation.

---

## Classification & Scope Note (Simulation / Test Double)

> [!NOTE]
> **Simulation / Test Double Classification:**
> This component is strictly a **local ranked retrieval test double** using Python's standard library. It requires zero external dependencies, no cloud credentials, no paid API keys, no local weights download, and no GPU or physical hardware.
>
> **Where Simplifications Stop:**
> - Retrieval scoring uses exact discrete token overlap rather than 1536-dimensional dense embedding vectors (such as OpenAI `text-embedding-ada-002`) or cosine distance.
> - Semantic synonymy (e.g. recognizing "crimson" as matching "red") requires continuous embeddings and is outside token overlap scope.
> - The component operates over an in-memory document fixture rather than distributed vector databases (Azure AI Search, Pinecone, Weaviate, Redis).

---

## Canonical Test Fixtures & Scenarios

### Fixture Definitions

- **Corpus**:
  ```json
  [
    {"id": "doc-01", "text": "red apple"},
    {"id": "doc-02", "text": "red berry"},
    {"id": "doc-03", "text": "blue sky"}
  ]
  ```
- **Query**: `"red"`
- **Threshold (`min_score`)**: `0.1`

---

## Scenarios & Invocations

### 1. Normal Scenario (`--scenario normal`)

Executes the standard search query `"red"` against the corpus with `min_score = 0.1`:
1. Tokenizes query `"red"` -> `{"red"}`.
2. Scores documents:
   - `doc-01` (`"red apple"`): Overlap = `{"red"}` -> Score = `1.0`.
   - `doc-02` (`"red berry"`): Overlap = `{"red"}` -> Score = `1.0`.
   - `doc-03` (`"blue sky"`): Overlap = `set()` -> Score = `0.0`.
3. Filter: `doc-03` has score `0.0 < 0.1` and is omitted.
4. Stable Tie-Breaking: `doc-01` and `doc-02` tie at score `1.0`; ascending ID breaks tie -> `doc-01` (Rank 1), `doc-02` (Rank 2).

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario normal
```

**Expected JSON Output (`exit 0`):**
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "scenario_type": "normal",
  "decision": "RANKED_SEARCH_SUCCESS",
  "query": "red",
  "min_score": 0.1,
  "total_candidates": 3,
  "results_count": 2,
  "omitted_count": 1,
  "results": [
    {
      "rank": 1,
      "id": "doc-01",
      "score": 1.0,
      "text": "red apple",
      "matched_tokens": [
        "red"
      ]
    },
    {
      "rank": 2,
      "id": "doc-02",
      "score": 1.0,
      "text": "red berry",
      "matched_tokens": [
        "red"
      ]
    }
  ],
  "omitted_ids": [
    "doc-03"
  ],
  "tie_broken_by_stable_id": true,
  "zero_score_omitted": true,
  "rationale": "Query 'red' matched 'red apple' (doc-01) and 'red berry' (doc-02) equally with score 1.0. Stable ID order ('doc-01' < 'doc-02') broke the tie deterministically. 'blue sky' (doc-03) scored 0.0 and was omitted below min_score 0.1.",
  "classification": "ranked_search_simulation"
}
```

---

### 2. Failure Scenario (`--scenario failure`)

Exercises a documented invalid/missing-data case by submitting an empty query `""`:
1. Engine catches the empty input before scoring.
2. Raises structured `InvalidQueryError` with reason `empty_query_string` and recovery suggestion.
3. Internal search index remains completely unmutated.

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario failure
```

**Expected JSON Output (`exit 0`):**
```json
{
  "scenario_id": "SCENARIO_FAILURE",
  "scenario_type": "invalid_data_rejection",
  "decision": "INVALID_DATA_REJECTED",
  "query": "",
  "error_type": "InvalidQueryError",
  "error_message": "Search query is missing or empty. Query must be a non-empty string containing at least one alphanumeric token.",
  "reason": "empty_query_string",
  "suggested_recovery": "Provide a non-empty query string such as 'red'.",
  "rejection_verified": true,
  "engine_state_preserved": true,
  "rationale": "Missing search query '' was safely rejected with InvalidQueryError. A structured diagnostic reason and recovery suggestion were provided, and the internal search index remained intact without state corruption.",
  "classification": "ranked_search_simulation"
}
```

---

### 3. Recovery Scenario (`--scenario recovery`)

Demonstrates failure handling and recovery on the next valid input in sequence on the same engine instance:
1. Submits invalid missing query `""` -> intercepted with `InvalidQueryError`.
2. Caller recovers by submitting valid query `"red"`.
3. Engine recovers immediately and returns accurate ranked results with stable tie-breaking and zero-score omission.

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario recovery
```

**Expected JSON Output (`exit 0`):**
```json
{
  "scenario_id": "SCENARIO_RECOVERY",
  "scenario_type": "failure_and_recovery",
  "decision": "ERROR_RECOVERY_SUCCESS",
  "invalid_step": {
    "query": "",
    "caught_error": "InvalidQueryError",
    "error_explanation": "Search query is missing or empty. Query must be a non-empty string containing at least one alphanumeric token.",
    "rejected": true
  },
  "recovery_step": {
    "query": "red",
    "status": "success",
    "results_count": 2,
    "top_id": "doc-01",
    "top_score": 1.0,
    "second_id": "doc-02",
    "second_score": 1.0,
    "omitted_id": "doc-03"
  },
  "recovery_verified": true,
  "state_consistency_maintained": true,
  "rationale": "Engine intercepted invalid empty query with documented InvalidQueryError, maintained internal state consistency, and cleanly recovered on next valid query 'red', returning accurate ranked results with stable tie-breaking.",
  "classification": "ranked_search_simulation"
}
```

---

### 4. Boundary Scenario (`--scenario boundary`)

Validates boundary conditions:
- **Exact Score Tie**: Verifies `doc-01` and `doc-02` tie at score `1.0`.
- **Insertion Order Invariance**: Verifies that even when `doc-02` is indexed before `doc-01` in the corpus, stable ID tie-breaking ranks `doc-01` first.
- **Threshold Cutoff Boundary**: Verifies `doc-03` (`0.0`) is strictly excluded when `min_score = 0.1`.
- **Zero-Match Query Handling**: Verifies query `"yellow"` returns empty list `[]` rather than raising an error.

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario boundary
```

**Expected JSON Output (`exit 0`):**
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "scenario_type": "boundary_invariants",
  "decision": "BOUNDARY_INVARIANTS_VERIFIED",
  "tie_score_equality_verified": true,
  "order_invariance_verified": true,
  "zero_score_exclusion_verified": true,
  "zero_match_query_handled": true,
  "min_score_applied": 0.1,
  "rationale": "All boundary invariants verified: exact score tie (1.0 == 1.0), insertion order invariance ('doc-01' precedes 'doc-02' even when indexed second), strict zero-score omission below threshold, and graceful empty list for zero matches.",
  "classification": "ranked_search_simulation"
}
```

---

### 5. Canonical Decision Table Check (`--check`)

Validates all 4 canonical scenarios in a single run against the formal decision table specification:

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --check
```

**Expected JSON Output (`exit 0`):**
```json
{
  "status": "success",
  "total_scenarios": 4,
  "passed_scenarios": 4,
  "failed_scenarios": 0,
  "all_passed": true,
  "classification": "ranked_search_simulation",
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_decision": "RANKED_SEARCH_SUCCESS",
      "actual_decision": "RANKED_SEARCH_SUCCESS",
      "matches_table": true,
      "status": "PASS",
      "rationale": "Query 'red' matched 'red apple' (doc-01) and 'red berry' (doc-02) equally with score 1.0. Stable ID order ('doc-01' < 'doc-02') broke the tie deterministically. 'blue sky' (doc-03) scored 0.0 and was omitted below min_score 0.1."
    },
    {
      "scenario_id": "SCENARIO_FAILURE",
      "scenario_type": "invalid_data_rejection",
      "expected_decision": "INVALID_DATA_REJECTED",
      "actual_decision": "INVALID_DATA_REJECTED",
      "matches_table": true,
      "status": "PASS",
      "rationale": "Missing search query '' was safely rejected with InvalidQueryError. A structured diagnostic reason and recovery suggestion were provided, and the internal search index remained intact without state corruption."
    },
    {
      "scenario_id": "SCENARIO_RECOVERY",
      "scenario_type": "failure_and_recovery",
      "expected_decision": "ERROR_RECOVERY_SUCCESS",
      "actual_decision": "ERROR_RECOVERY_SUCCESS",
      "matches_table": true,
      "status": "PASS",
      "rationale": "Engine intercepted invalid empty query with documented InvalidQueryError, maintained internal state consistency, and cleanly recovered on next valid query 'red', returning accurate ranked results with stable tie-breaking."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary_invariants",
      "expected_decision": "BOUNDARY_INVARIANTS_VERIFIED",
      "actual_decision": "BOUNDARY_INVARIANTS_VERIFIED",
      "matches_table": true,
      "status": "PASS",
      "rationale": "All boundary invariants verified: exact score tie (1.0 == 1.0), insertion order invariance ('doc-01' precedes 'doc-02' even when indexed second), strict zero-score omission below threshold, and graceful empty list for zero matches."
    }
  ]
}
```

---

### 6. Deliberate Tamper Test (`--tamper`)

Simulates a deliberate regression/tamper to prove that any specification violation or assertion mismatch strictly causes verification failure:

**Invocation:**
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --tamper
```

**Expected Stderr Output (`exit 1`):**
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "error_message": "Verification failed: 1 scenario(s) did not match the canonical decision table.",
  "exit_code": 1,
  "classification": "ranked_search_simulation",
  "rationale": "Deliberately mutated expectation failed assertion as expected."
}
```

---

## Running the Automated Test Suite

Run the full unit test discovery suite across all invariants, edge cases, error conditions, and subprocess executions:

```bash
python3 -m unittest discover -s 08-building-search-applications/applied-labs/r40-t028 -p "test_*.py" -v
```

Expected result: 39 tests passing cleanly (`OK`).
