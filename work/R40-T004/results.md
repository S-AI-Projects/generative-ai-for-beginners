# R40-T004 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T004.

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
  "trace_step_count": 5,
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
  "invariants_verified": true,
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
  "trace_step_count": 5,
  "results": [],
  "invariants_verified": true,
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
  "trace_step_count": 5,
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
  "invariants_verified": true,
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
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_tie (test_example.TestCLIExecution.test_cli_scenario_tie) ... ok
test_cli_scenario_zero_match (test_example.TestCLIExecution.test_cli_scenario_zero_match) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_cli_trace (test_example.TestCLIExecution.test_cli_trace) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_query_ocean_returns_no_match (test_example.TestCoreRetrievalContract.test_query_ocean_returns_no_match) ... ok
test_query_red_apple_ranks_a_before_b (test_example.TestCoreRetrievalContract.test_query_red_apple_ranks_a_before_b) ... ok
test_tie_breaking_by_doc_id (test_example.TestCoreRetrievalContract.test_tie_breaking_by_doc_id) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_intermediate_trace_steps_recorded (test_example.TestIntermediateStateTraceAndInvariants.test_intermediate_trace_steps_recorded) ... ok
test_invariant_scoring_fidelity (test_example.TestIntermediateStateTraceAndInvariants.test_invariant_scoring_fidelity)
Every returned document score must match the candidate_scoring raw score. ... ok
test_invariant_zero_pruned_from_output (test_example.TestIntermediateStateTraceAndInvariants.test_invariant_zero_pruned_from_output)
Zero score documents (e.g. Doc C with query 'red apple') must not be in results. ... ok
test_tampered_trace_raises_invariant_violation (test_example.TestIntermediateStateTraceAndInvariants.test_tampered_trace_raises_invariant_violation)
Artificially corrupted scores trigger InvariantViolationError. ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.162s

OK

```
