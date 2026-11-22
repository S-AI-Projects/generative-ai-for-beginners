# R40-T002 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T002.

## 1. Normal Scenario ('red apple' -> A before B)
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "query": "red apple",
  "decision": "RANK_A_BEFORE_B",
  "doc_ids": [
    "A",
    "B"
  ],
  "scores": [
    2,
    1
  ],
  "results": [
    {
      "doc_id": "A",
      "score": 2,
      "text": "red apple",
      "matched_tokens": [
        "apple",
        "red"
      ]
    },
    {
      "doc_id": "B",
      "score": 1,
      "text": "green apple",
      "matched_tokens": [
        "apple"
      ]
    }
  ],
  "contract_satisfied": true
}
```

## 2. Zero-Match Boundary Scenario ('ocean' -> [])
```json
{
  "scenario_id": "SCENARIO_BOUNDARY_ZERO_MATCH",
  "query": "ocean",
  "decision": "NO_MATCH_EMPTY_RESULT",
  "doc_ids": [],
  "scores": [],
  "results": [],
  "contract_satisfied": true
}
```

## 3. Tie-Breaking Boundary Scenario ('apple' -> A before B)
```json
{
  "scenario_id": "SCENARIO_BOUNDARY_TIE",
  "query": "apple",
  "decision": "TIE_BROKEN_A_BEFORE_B",
  "doc_ids": [
    "A",
    "B"
  ],
  "scores": [
    1,
    1
  ],
  "results": [
    {
      "doc_id": "A",
      "score": 1,
      "text": "red apple",
      "matched_tokens": [
        "apple"
      ]
    },
    {
      "doc_id": "B",
      "score": 1,
      "text": "green apple",
      "matched_tokens": [
        "apple"
      ]
    }
  ],
  "contract_satisfied": true
}
```

## 4. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'RANK_A_BEFORE_B', 'passed': False}]",
  "exit_code": 1
}
```

## 5. Unittest Output
```
test_empty_and_whitespace_queries_fail (test_example.TestBoundaryAndInvalidCases.test_empty_and_whitespace_queries_fail)
Empty query or whitespace-only query raises ValueError. ... ok
test_empty_corpus_fails (test_example.TestBoundaryAndInvalidCases.test_empty_corpus_fails)
Empty corpus dictionary raises ValueError. ... ok
test_invalid_query_type_fails (test_example.TestBoundaryAndInvalidCases.test_invalid_query_type_fails)
Non-string query raises TypeError. ... ok
test_smallest_valid_query (test_example.TestBoundaryAndInvalidCases.test_smallest_valid_query)
Single matching token is the smallest valid query. ... ok
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_tie (test_example.TestCLIExecution.test_cli_scenario_tie) ... ok
test_cli_scenario_zero_match (test_example.TestCLIExecution.test_cli_scenario_zero_match) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateFailure.test_deliberate_wrong_result_fails) ... ok
test_case_and_whitespace_insensitivity (test_example.TestLexicalRetrieverCoreContract.test_case_and_whitespace_insensitivity)
Mixed case and padded whitespace produce identical ranking. ... ok
test_query_ocean_returns_no_match (test_example.TestLexicalRetrieverCoreContract.test_query_ocean_returns_no_match)
Query 'ocean' returns an empty result list. ... ok
test_query_red_apple_ranks_a_before_b (test_example.TestLexicalRetrieverCoreContract.test_query_red_apple_ranks_a_before_b)
Query 'red apple' ranks A (score 2) before B (score 1). ... ok
test_tie_breaking_by_doc_id (test_example.TestLexicalRetrieverCoreContract.test_tie_breaking_by_doc_id)
Query 'apple' matches A and B with score 1; tie broken alphabetically by doc_id. ... ok
test_canonical_check_fails_on_tamper (test_example.TestScenarioHelpersAndDecisionTable.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestScenarioHelpersAndDecisionTable.test_canonical_check_passes) ... ok
test_run_boundary_tie_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_boundary_tie_scenario) ... ok
test_run_boundary_zero_match_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_boundary_zero_match_scenario) ... ok
test_run_invalid_case_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_invalid_case_scenario) ... ok
test_run_normal_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_normal_scenario) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.135s

OK

```
