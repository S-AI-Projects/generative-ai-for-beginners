# R40-T027 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T027.
Focus: Model local pending, streaming, complete and error states for one response with a stable message ID. Two chunks append in order; an error preserves received text with an error marker; chunks after completion are rejected.

---

## 1. Normal Scenario (`--scenario normal`)

Command:
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario normal
```

Expected Decision: `STATE_COMPLETE_SUCCESS`
Expected Final State: `complete`
Expected Content: `"Hello, how can I assist you today?"`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "scenario_type": "normal",
  "decision": "STATE_COMPLETE_SUCCESS",
  "message_id": "msg-resp-001",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "chunks_received": 2,
  "error_message": null,
  "stable_id_preserved": true,
  "ordered_chunks_verified": true,
  "rationale": "Response 'msg-resp-001' initialized in PENDING state, sequentially appended 2 chunks in arrival order, and completed successfully with stable ID.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Stable message ID preserved, two chunks appended strictly in arrival order, and state transitioned cleanly from PENDING -> STREAMING -> COMPLETE.

---

## 2. Error Recovery Scenario (`--scenario error`)

Command:
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario error
```

Expected Decision: `STATE_ERROR_RECOVERED`
Expected Final State: `error`
Expected Content: `"Hello, [ERROR: Stream connection dropped]"`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_ERROR",
  "scenario_type": "error_recovery",
  "decision": "STATE_ERROR_RECOVERED",
  "message_id": "msg-resp-001",
  "state": "error",
  "content": "Hello, [ERROR: Stream connection dropped]",
  "preserved_prefix": "Hello, ",
  "error_marker": "[ERROR: Stream connection dropped]",
  "error_message": "Stream connection dropped",
  "chunks_received": 1,
  "text_preserved": true,
  "rationale": "Response 'msg-resp-001' received chunk 1 ('Hello, ') before stream failed. The error preserved previously received text intact and appended error marker.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Network failure during streaming preserved already-received text ('Hello, ') and appended explicit error marker without dropping content.

---

## 3. Boundary Rejection Scenario (`--scenario boundary`)

Command:
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario boundary
```

Expected Decision: `CHUNK_AFTER_COMPLETION_REJECTED`
Expected Final State: `complete`
Expected Content: `"Hello, how can I assist you today?"`
Expected Rejection Exception: `ChunkRejectedError`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "scenario_type": "boundary_rejection",
  "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
  "message_id": "msg-resp-001",
  "state": "complete",
  "content": "Hello, how can I assist you today?",
  "chunks_received": 2,
  "attempted_late_chunk": " [Late chunk arriving after stream close]",
  "rejection_verified": true,
  "rejection_exception": "ChunkRejectedError",
  "rationale": "Response 'msg-resp-001' reached COMPLETE state. Incoming late chunk ' [Late chunk arriving after stream close]' was rejected with ChunkRejectedError, preserving the finalized response buffer without corruption.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Chunk received after stream completion was strictly rejected with ChunkRejectedError, preserving the finalized response buffer without corruption.

---

## 4. Canonical Decision Table Check (`--check`)

Command:
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --check
```

Expected Status: `success`
Expected Passed Scenarios: `3`
Expected Failed Scenarios: `0`

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 3,
  "passed_scenarios": 3,
  "failed_scenarios": 0,
  "all_passed": true,
  "classification": "chat_view_state_simulation",
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_decision": "STATE_COMPLETE_SUCCESS",
      "actual_decision": "STATE_COMPLETE_SUCCESS",
      "expected_state": "complete",
      "actual_state": "complete",
      "matches_table": true,
      "status": "PASS",
      "message_id": "msg-resp-001",
      "content": "Hello, how can I assist you today?",
      "rationale": "Response 'msg-resp-001' initialized in PENDING state, sequentially appended 2 chunks in arrival order, and completed successfully with stable ID."
    },
    {
      "scenario_id": "SCENARIO_ERROR",
      "scenario_type": "error_recovery",
      "expected_decision": "STATE_ERROR_RECOVERED",
      "actual_decision": "STATE_ERROR_RECOVERED",
      "expected_state": "error",
      "actual_state": "error",
      "matches_table": true,
      "status": "PASS",
      "message_id": "msg-resp-001",
      "content": "Hello, [ERROR: Stream connection dropped]",
      "rationale": "Response 'msg-resp-001' received chunk 1 ('Hello, ') before stream failed. The error preserved previously received text intact and appended error marker."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary_rejection",
      "expected_decision": "CHUNK_AFTER_COMPLETION_REJECTED",
      "actual_decision": "CHUNK_AFTER_COMPLETION_REJECTED",
      "expected_state": "complete",
      "actual_state": "complete",
      "matches_table": true,
      "status": "PASS",
      "message_id": "msg-resp-001",
      "content": "Hello, how can I assist you today?",
      "rationale": "Response 'msg-resp-001' reached COMPLETE state. Incoming late chunk ' [Late chunk arriving after stream close]' was rejected with ChunkRejectedError, preserving the finalized response buffer without corruption."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 3 canonical scenarios (Normal, Error Recovery, Boundary Rejection) passed 100% against the formal decision table.

---

## 5. Deliberate Tamper Test (`--tamper`)

Command:
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --tamper
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
  "classification": "chat_view_state_simulation",
  "rationale": "Deliberately mutated expectation failed assertion as expected."
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — A deliberate wrong result strictly makes the verification check fail with exit code 1, proving regression sensitivity.

---

## 6. Automated Unit Test Discovery Suite

Command:
```bash
python3 -m unittest discover -s 07-building-chat-applications/applied-labs/r40-t027 -p "test_*.py" -v
```

Expected Status: `OK` with non-zero test count

Actual Test Runner Output:
```
test_canonical_check_fails_on_tamper (test_example.TestCanonicalScenariosAndChecker.test_canonical_check_fails_on_tamper)
Tampered check must raise DecisionMismatchError. ... ok
test_canonical_check_passes_on_unmodified_table (test_example.TestCanonicalScenariosAndChecker.test_canonical_check_passes_on_unmodified_table)
Canonical check passes with all_passed=True and 0 failures. ... ok
test_run_boundary_scenario (test_example.TestCanonicalScenariosAndChecker.test_run_boundary_scenario)
Boundary scenario helper produces CHUNK_AFTER_COMPLETION_REJECTED. ... ok
test_run_error_scenario (test_example.TestCanonicalScenariosAndChecker.test_run_error_scenario)
Error scenario helper produces STATE_ERROR_RECOVERED with preserved text. ... ok
test_run_normal_scenario (test_example.TestCanonicalScenariosAndChecker.test_run_normal_scenario)
Normal scenario helper produces STATE_COMPLETE_SUCCESS with ordered chunks. ... ok
test_chunk_rejected_after_completion (test_example.TestChunkRejectionInTerminalStates.test_chunk_rejected_after_completion)
Attempting to append a chunk after stream completion raises ChunkRejectedError. ... ok
test_chunk_rejected_after_error (test_example.TestChunkRejectionInTerminalStates.test_chunk_rejected_after_error)
Attempting to append a chunk after stream error raises ChunkRejectedError. ... ok
test_rejection_event_logged_in_history (test_example.TestChunkRejectionInTerminalStates.test_rejection_event_logged_in_history)
Rejection must append an audit event into response.history. ... ok
test_state_and_content_unmodified_after_rejection_post_complete (test_example.TestChunkRejectionInTerminalStates.test_state_and_content_unmodified_after_rejection_post_complete)
Rejected chunk must not corrupt content or modify COMPLETE state. ... ok
test_state_and_content_unmodified_after_rejection_post_error (test_example.TestChunkRejectionInTerminalStates.test_state_and_content_unmodified_after_rejection_post_error)
Rejected chunk must not corrupt error content or modify ERROR state. ... ok
test_cannot_complete_from_error_state (test_example.TestErrorRecoveryAndTextPreservation.test_cannot_complete_from_error_state)
Attempting to complete an errored response raises IllegalStateTransitionError. ... ok
test_cannot_fail_already_completed_response (test_example.TestErrorRecoveryAndTextPreservation.test_cannot_fail_already_completed_response)
Attempting to fail a completed response raises IllegalStateTransitionError. ... ok
test_error_after_first_chunk_preserves_text_and_appends_marker (test_example.TestErrorRecoveryAndTextPreservation.test_error_after_first_chunk_preserves_text_and_appends_marker)
Previously received text must NOT be cleared; error marker is appended. ... ok
test_error_after_multiple_chunks_preserves_full_prefix (test_example.TestErrorRecoveryAndTextPreservation.test_error_after_multiple_chunks_preserves_full_prefix)
All chunks received prior to error must be preserved intact. ... ok
test_error_during_pending_sets_error_marker (test_example.TestErrorRecoveryAndTextPreservation.test_error_during_pending_sets_error_marker)
Error when 0 chunks have arrived sets content to just the marker. ... ok
test_empty_or_whitespace_message_id_rejected (test_example.TestMessageIdentityAndPending.test_empty_or_whitespace_message_id_rejected)
Creating a response with empty or blank ID must raise ValueError. ... ok
test_init_pending_state (test_example.TestMessageIdentityAndPending.test_init_pending_state)
Initial state must be PENDING with empty content and 0 chunks. ... ok
test_stable_message_id_persists_across_all_lifecycle_steps (test_example.TestMessageIdentityAndPending.test_stable_message_id_persists_across_all_lifecycle_steps)
Message ID must remain unchanged across PENDING, STREAMING, and COMPLETE. ... ok
test_to_dict_serialization (test_example.TestMessageIdentityAndPending.test_to_dict_serialization)
Snapshot serialization must produce JSON-serializable dictionary. ... ok
test_complete_response_is_idempotent (test_example.TestSequentialStreamingAndCompletion.test_complete_response_is_idempotent)
Subsequent completion calls on an already completed response are no-ops. ... ok
test_complete_response_transitions_to_complete (test_example.TestSequentialStreamingAndCompletion.test_complete_response_transitions_to_complete)
Calling complete_response must finalize state to COMPLETE. ... ok
test_complete_without_chunks_transitions_from_pending (test_example.TestSequentialStreamingAndCompletion.test_complete_without_chunks_transitions_from_pending)
A stream may complete with empty content (0 chunks received). ... ok
test_first_chunk_transitions_pending_to_streaming (test_example.TestSequentialStreamingAndCompletion.test_first_chunk_transitions_pending_to_streaming)
First incoming chunk transitions state from PENDING to STREAMING. ... ok
test_multiple_chunks_order_preservation (test_example.TestSequentialStreamingAndCompletion.test_multiple_chunks_order_preservation)
Multiple small chunks must maintain exact FIFO ordering. ... ok
test_subsequent_chunks_append_in_order (test_example.TestSequentialStreamingAndCompletion.test_subsequent_chunks_append_in_order)
Sequential chunks must concatenate in strict arrival order. ... ok
test_cli_check_all_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_check_all_exit_0)
CLI --check must exit 0 and report all passed. ... ok
test_cli_scenario_boundary_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_boundary_exit_0)
CLI --scenario boundary must exit 0 and output valid JSON. ... ok
test_cli_scenario_error_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_error_exit_0)
CLI --scenario error must exit 0 and output valid JSON. ... ok
test_cli_scenario_normal_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_normal_exit_0)
CLI --scenario normal must exit 0 and output valid JSON. ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestSubprocessCLIExecution.test_cli_tamper_fails_with_nonzero_exit)
CLI --tamper must exit with non-zero exit code (1) and output error details. ... ok

----------------------------------------------------------------------
Ran 30 tests in 0.114s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 30 unit tests executed and passed in a fresh process.

---

## 7. Summary of Task Verification

| Scenario | Message ID | Expected Decision | Actual Decision | Final State | Status |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | `'msg-resp-001'` | `STATE_COMPLETE_SUCCESS` | `STATE_COMPLETE_SUCCESS` | `complete` | **PASS** |
| `SCENARIO_ERROR` | `'msg-resp-001'` | `STATE_ERROR_RECOVERED` | `STATE_ERROR_RECOVERED` | `error` | **PASS** |
| `SCENARIO_BOUNDARY` | `'msg-resp-001'` | `CHUNK_AFTER_COMPLETION_REJECTED` | `CHUNK_AFTER_COMPLETION_REJECTED` | `complete` | **PASS** |
| `CANONICAL_CHECK` | Multiple | `all_passed: true` | `all_passed: true` | Verified | **PASS** |
| `DELIBERATE_TAMPER` | Mutated Spec | Exit Code `1` | Exit Code `1` | Failure Caught | **PASS** |

All checks passed successfully. Verification complete.
