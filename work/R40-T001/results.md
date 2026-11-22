# R40-T001 — Verification Results

This report records the inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T001.

## 1. Normal Scenario
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "scenario_type": "normal",
  "decision": "STATE_COMPLETE_SUCCESS",
  "message_id": "msg-resp-001",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "chunks_received": 2,
  "stable_id_preserved": true,
  "ordered_chunks_verified": true,
  "history_events": 4
}
```

## 2. Error Recovery Scenario
```json
{
  "scenario_id": "SCENARIO_ERROR",
  "scenario_type": "error_recovery",
  "decision": "STATE_ERROR_RECOVERED",
  "message_id": "msg-resp-001",
  "state": "error",
  "content": "Hello, [ERROR: Stream connection dropped unexpectedly]",
  "chunks_received": 1,
  "error_message": "Stream connection dropped unexpectedly",
  "stable_id_preserved": true,
  "text_preserved": true,
  "content_matches_expected": true,
  "history_events": 3
}
```

## 3. Boundary Rejection Scenario
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "scenario_type": "boundary_rejection",
  "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
  "message_id": "msg-resp-001",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "chunks_received": 2,
  "rejection_verified": true,
  "rejection_exception": "ChunkRejectedError",
  "content_unmodified_by_late_chunk": true,
  "history_events": 4
}
```

## 4. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'STATE_COMPLETE_SUCCESS', 'passed': False}]",
  "exit_code": 1
}
```

## 5. Unittest Output
```
test_cli_boundary_exit_0 (test_example.TestCLIExecution.test_cli_boundary_exit_0) ... ok
test_cli_check_exit_0 (test_example.TestCLIExecution.test_cli_check_exit_0) ... ok
test_cli_error_exit_0 (test_example.TestCLIExecution.test_cli_error_exit_0) ... ok
test_cli_normal_exit_0 (test_example.TestCLIExecution.test_cli_normal_exit_0) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateFailure.test_deliberate_wrong_result_fails) ... ok
test_error_preserves_received_text_with_marker (test_example.TestErrorRecoveryAndPreservation.test_error_preserves_received_text_with_marker)
Error transition preserves prior chunks and attaches error marker. ... ok
test_empty_message_id_rejected (test_example.TestMessageIdentityAndPending.test_empty_message_id_rejected)
Empty or whitespace-only message ID must be rejected. ... ok
test_init_pending_state (test_example.TestMessageIdentityAndPending.test_init_pending_state)
Initial state must be PENDING with empty content and 0 chunks. ... ok
test_cannot_complete_from_error (test_example.TestPostTerminalRejection.test_cannot_complete_from_error)
Attempting to complete a failed response raises IllegalStateTransitionError. ... ok
test_cannot_fail_from_complete (test_example.TestPostTerminalRejection.test_cannot_fail_from_complete)
Attempting to fail a completed response raises IllegalStateTransitionError. ... ok
test_chunks_after_completion_rejected (test_example.TestPostTerminalRejection.test_chunks_after_completion_rejected)
Appending chunk after COMPLETE state raises ChunkRejectedError. ... ok
test_chunks_after_error_rejected (test_example.TestPostTerminalRejection.test_chunks_after_error_rejected)
Appending chunk after ERROR state raises ChunkRejectedError. ... ok
test_canonical_check_fails_on_tamper (test_example.TestScenarioHelpersAndDecisionTable.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestScenarioHelpersAndDecisionTable.test_canonical_check_passes) ... ok
test_run_boundary_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_boundary_scenario) ... ok
test_run_error_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_error_scenario) ... ok
test_run_normal_scenario (test_example.TestScenarioHelpersAndDecisionTable.test_run_normal_scenario) ... ok
test_invalid_chunk_type_rejected (test_example.TestStreamingOrderingAndCompletion.test_invalid_chunk_type_rejected)
Non-string chunk must raise TypeError. ... ok
test_two_chunks_append_in_order (test_example.TestStreamingOrderingAndCompletion.test_two_chunks_append_in_order)
Two chunks append strictly in arrival order. ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.135s

OK

```
