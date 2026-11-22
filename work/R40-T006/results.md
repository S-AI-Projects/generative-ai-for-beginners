# R40-T006 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T006.

## 1. Normal Scenario
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "STATE_COMPLETE_SUCCESS",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "chunks_received": 2,
  "contract_satisfied": true
}
```

## 2. Error Recovery Scenario
```json
{
  "scenario_id": "SCENARIO_ERROR",
  "decision": "STATE_ERROR_RECOVERED",
  "state": "error",
  "content": "Hello, [ERROR: Stream connection dropped]",
  "chunks_received": 1,
  "contract_satisfied": true
}
```

## 3. Boundary Rejection Scenario
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "rejection_verified": true,
  "rejection_exception": "ChunkRejectedError",
  "contract_satisfied": true
}
```

## 4. Refactoring Equivalence Proof
```json
{
  "status": "success",
  "normal_path_equivalent": true,
  "error_path_equivalent": true,
  "boundary_path_equivalent": true,
  "all_equivalent": true
}
```

## 5. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'STATE_COMPLETE_SUCCESS', 'passed': False}]",
  "exit_code": 1
}
```

## 6. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_refactor_check (test_example.TestCLIExecution.test_cli_refactor_check) ... ok
test_cli_scenario_boundary (test_example.TestCLIExecution.test_cli_scenario_boundary) ... ok
test_cli_scenario_error (test_example.TestCLIExecution.test_cli_scenario_error) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_chunks_after_completion_rejected (test_example.TestCoreStateContract.test_chunks_after_completion_rejected) ... ok
test_chunks_after_error_rejected (test_example.TestCoreStateContract.test_chunks_after_error_rejected) ... ok
test_error_preserves_received_text_with_marker (test_example.TestCoreStateContract.test_error_preserves_received_text_with_marker) ... ok
test_two_chunks_append_in_order (test_example.TestCoreStateContract.test_two_chunks_append_in_order) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_baseline_and_refactored_equivalence (test_example.TestRefactoringResponsibilityExtraction.test_baseline_and_refactored_equivalence) ... ok
test_extracted_streaming_buffer_unit (test_example.TestRefactoringResponsibilityExtraction.test_extracted_streaming_buffer_unit) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.162s

OK

```
