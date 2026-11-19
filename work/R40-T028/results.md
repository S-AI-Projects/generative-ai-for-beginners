# R40-T028 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T028.
Focus: Rank a small local corpus by token overlap, return score and source ID, and apply a minimum-score threshold. Query red matches red apple and red berry equally; stable ID order breaks the tie; blue sky scores zero and is omitted. Focus: Exercise a documented invalid/missing-data case, explain the error, and demonstrate recovery on the next valid input.

---

## 1. Normal Scenario (`--scenario normal`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario normal
```

Expected Decision: `RANKED_SEARCH_SUCCESS`
Expected Results Count: `2` (`doc-01` and `doc-02`)
Expected Omitted Count: `1` (`doc-03`)
Expected Tie-Breaking: Stable ID (`doc-01` before `doc-02`)

Actual Output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — Query 'red' matched 'red apple' and 'red berry' equally with score 1.0; stable ID order ('doc-01' < 'doc-02') broke the tie; 'blue sky' scored 0.0 and was omitted below min_score 0.1.

---

## 2. Failure Scenario (`--scenario failure`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario failure
```

Expected Decision: `INVALID_DATA_REJECTED`
Expected Error Type: `InvalidQueryError`
Expected Reason: `empty_query_string`

Actual Output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — Empty search query '' was caught and safely rejected with structured InvalidQueryError, providing remediation suggestion while preserving internal index state.

---

## 3. Recovery Scenario (`--scenario recovery`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario recovery
```

Expected Decision: `ERROR_RECOVERY_SUCCESS`
Expected Recovery Verification: `true`
Expected Top Result: `doc-01`
Expected Second Result: `doc-02`

Actual Output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — Engine intercepted invalid empty query with documented InvalidQueryError, maintained state consistency, and cleanly recovered on next valid query 'red', returning accurate rankings with stable tie-breaking.

---

## 4. Boundary Scenario (`--scenario boundary`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --scenario boundary
```

Expected Decision: `BOUNDARY_INVARIANTS_VERIFIED`
Expected Tie Equality: `true`
Expected Order Invariance: `true`
Expected Zero-Score Exclusion: `true`

Actual Output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — All boundary invariants verified: exact score tie (1.0 == 1.0), insertion order invariance ('doc-01' precedes 'doc-02' even when indexed second), strict zero-score omission below threshold, and graceful empty list for zero matches.

---

## 5. Canonical Decision Table Check (`--check`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --check
```

Expected Status: `success`
Expected Passed Scenarios: `4`
Expected Failed Scenarios: `0`

Actual Output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 4 canonical scenarios (Normal, Failure, Recovery, Boundary) passed 100% against the formal decision table specification.

---

## 6. Deliberate Tamper Test (`--tamper`)

Command:
```bash
python3 08-building-search-applications/applied-labs/r40-t028/example.py --tamper
```

Expected Exit Code: `1`
Expected Error Type: `DecisionMismatchError`

Actual Stderr Output:
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

Exit code: `1` (Expected: `1`)

**Result:** PASS — A deliberate wrong result strictly makes the verification check fail with exit code 1, proving regression sensitivity.

---

## 7. Automated Unit Test Discovery Suite

Command:
```bash
python3 -m unittest discover -s 08-building-search-applications/applied-labs/r40-t028 -p "test_*.py" -v
```

Expected Status: `OK` with non-zero test count

Actual Test Runner Output:
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_boundary (test_example.TestCLIExecution.test_cli_scenario_boundary) ... ok
test_cli_scenario_failure (test_example.TestCLIExecution.test_cli_scenario_failure) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_recovery (test_example.TestCLIExecution.test_cli_scenario_recovery) ... ok
test_cli_tamper_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_nonzero_exit)
Verifies that deliberate tamper flag triggers nonzero exit (exit 1) and JSON on stderr. ... ok
test_canonical_check_clean (test_example.TestCanonicalScenariosAndTamper.test_canonical_check_clean) ... ok
test_deliberate_tamper_fails_check (test_example.TestCanonicalScenariosAndTamper.test_deliberate_tamper_fails_check)
Verifies that a deliberate mutation in the specification strictly raises DecisionMismatchError. ... ok
test_run_boundary_scenario_output (test_example.TestCanonicalScenariosAndTamper.test_run_boundary_scenario_output) ... ok
test_run_failure_scenario_output (test_example.TestCanonicalScenariosAndTamper.test_run_failure_scenario_output) ... ok
test_run_normal_scenario_output (test_example.TestCanonicalScenariosAndTamper.test_run_normal_scenario_output) ... ok
test_run_recovery_scenario_output (test_example.TestCanonicalScenariosAndTamper.test_run_recovery_scenario_output) ... ok
test_engine_documents_unmodified_by_queries (test_example.TestFailureAndRecoveryWorkflow.test_engine_documents_unmodified_by_queries)
Query executions (whether valid or invalid) do not mutate the internal corpus. ... ok
test_invalid_query_then_valid_recovery (test_example.TestFailureAndRecoveryWorkflow.test_invalid_query_then_valid_recovery)
Interleaved invalid queries must not corrupt subsequent valid searches. ... ok
test_multiple_failures_then_recovery (test_example.TestFailureAndRecoveryWorkflow.test_multiple_failures_then_recovery)
Multiple consecutive errors of different kinds must not leak state. ... ok
test_corpus_duplicate_ids (test_example.TestInvalidAndMissingData.test_corpus_duplicate_ids)
Corpus documents with duplicate IDs raise CorpusValidationError. ... ok
test_corpus_empty_id_field (test_example.TestInvalidAndMissingData.test_corpus_empty_id_field)
Corpus document with blank string 'id' raises MissingDataError. ... ok
test_corpus_missing_id_field (test_example.TestInvalidAndMissingData.test_corpus_missing_id_field)
Corpus document missing 'id' raises MissingDataError. ... ok
test_corpus_missing_text_field (test_example.TestInvalidAndMissingData.test_corpus_missing_text_field)
Corpus document missing 'text' raises MissingDataError. ... ok
test_corpus_non_string_text_field (test_example.TestInvalidAndMissingData.test_corpus_non_string_text_field)
Corpus document with non-string 'text' raises MissingDataError. ... ok
test_corpus_not_a_list (test_example.TestInvalidAndMissingData.test_corpus_not_a_list)
Corpus passed as a dict raises CorpusValidationError. ... ok
test_empty_query_raises_invalid_query_error (test_example.TestInvalidAndMissingData.test_empty_query_raises_invalid_query_error)
Empty query string '' raises InvalidQueryError. ... ok
test_negative_threshold_raises_invalid_threshold_error (test_example.TestInvalidAndMissingData.test_negative_threshold_raises_invalid_threshold_error)
Negative min_score raises InvalidThresholdError. ... ok
test_non_numeric_threshold_raises_invalid_threshold_error (test_example.TestInvalidAndMissingData.test_non_numeric_threshold_raises_invalid_threshold_error)
Non-numeric min_score raises InvalidThresholdError. ... ok
test_non_string_query_raises_invalid_query_error (test_example.TestInvalidAndMissingData.test_non_string_query_raises_invalid_query_error)
Non-string query raises InvalidQueryError. ... ok
test_none_query_raises_invalid_query_error (test_example.TestInvalidAndMissingData.test_none_query_raises_invalid_query_error)
None query raises InvalidQueryError. ... ok
test_punctuation_only_query_raises_invalid_query_error (test_example.TestInvalidAndMissingData.test_punctuation_only_query_raises_invalid_query_error)
Query with no alphanumeric tokens raises InvalidQueryError. ... ok
test_whitespace_only_query_raises_invalid_query_error (test_example.TestInvalidAndMissingData.test_whitespace_only_query_raises_invalid_query_error)
Whitespace query '   ' raises InvalidQueryError. ... ok
test_blue_sky_zero_score_omission_by_threshold (test_example.TestRankedSearchEngine.test_blue_sky_zero_score_omission_by_threshold)
When min_score > 0 (e.g. 0.1), doc-03 ('blue sky') is excluded; ... ok
test_case_insensitivity (test_example.TestRankedSearchEngine.test_case_insensitivity)
Uppercase query 'RED' behaves identically to lowercase 'red'. ... ok
test_empty_corpus (test_example.TestRankedSearchEngine.test_empty_corpus)
Searching an empty corpus gracefully returns an empty list. ... ok
test_exact_tie_score (test_example.TestRankedSearchEngine.test_exact_tie_score)
Confirms that both tied documents receive identical overlap scores. ... ok
test_high_threshold_filtering (test_example.TestRankedSearchEngine.test_high_threshold_filtering)
min_score higher than maximum overlap filters all documents. ... ok
test_multi_token_query_scoring (test_example.TestRankedSearchEngine.test_multi_token_query_scoring)
Query 'red apple' has 2 overlapping tokens with doc-01 and 1 with doc-02. ... ok
test_normal_search_contract (test_example.TestRankedSearchEngine.test_normal_search_contract)
Query 'red' matches 'red apple' and 'red berry' equally with score 1.0; ... ok
test_source_id_provenance (test_example.TestRankedSearchEngine.test_source_id_provenance)
Every result preserves and returns source ID, score, and text. ... ok
test_tie_breaking_order_invariance (test_example.TestRankedSearchEngine.test_tie_breaking_order_invariance)
Inverting corpus insertion order [doc-02, doc-01, doc-03] must still ... ok
test_whitespace_and_punctuation_tokenization (test_example.TestRankedSearchEngine.test_whitespace_and_punctuation_tokenization)
Punctuation in query and documents does not disrupt token matching. ... ok
test_zero_match_query (test_example.TestRankedSearchEngine.test_zero_match_query)
Query matching zero documents returns an empty list without error. ... ok

----------------------------------------------------------------------
Ran 39 tests in 0.288s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 39 unit tests executed and passed in a fresh process.

---

## 8. Summary of Task Verification

| Scenario | Input Query / Action | Expected Decision | Actual Decision | Results / Invariants | Status |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | `'red'` | `RANKED_SEARCH_SUCCESS` | `RANKED_SEARCH_SUCCESS` | `doc-01` (1.0), `doc-02` (1.0), `doc-03` omitted | **PASS** |
| `SCENARIO_FAILURE` | `''` (empty query) | `INVALID_DATA_REJECTED` | `INVALID_DATA_REJECTED` | `InvalidQueryError` caught, state preserved | **PASS** |
| `SCENARIO_RECOVERY` | `''` then `'red'` | `ERROR_RECOVERY_SUCCESS` | `ERROR_RECOVERY_SUCCESS` | Intercepted error then clean recovery | **PASS** |
| `SCENARIO_BOUNDARY` | Ties, Order, Thresh | `BOUNDARY_INVARIANTS_VERIFIED` | `BOUNDARY_INVARIANTS_VERIFIED` | Tie equality, order invariance, cutoff verified | **PASS** |
| `CANONICAL_CHECK` | Decision Table | `all_passed: true` | `all_passed: true` | 4/4 scenarios pass table check | **PASS** |
| `DELIBERATE_TAMPER` | Mutated Spec | Exit Code `1` | Exit Code `1` | Failure caught with non-zero exit | **PASS** |
| `UNIT_TEST_SUITE` | 39 test methods | `OK` (Ran 39 tests) | `OK` (Ran 39 tests) | 39/39 passed in fresh process | **PASS** |

All checks passed successfully. Verification complete.
