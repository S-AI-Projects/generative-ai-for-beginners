# R40-T030 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T030.
**Focus:** Model local pending, streaming, complete and error states for one response with a stable message ID. Two chunks append in order; an error preserves received text with an error marker; chunks after completion are rejected.
**Applied Questions Assessment:** Predict an output, diagnose a failure, and choose a boundary policy, each with architectural rationale and executable verification check.

---

## 1. Normal Scenario (`--scenario normal`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario normal
```

Expected Decision: `STATE_COMPLETE_SUCCESS`  
Expected State: `complete`  
Expected Content: `"Hello, how can I assist you today?"`  
Expected Chunks Received: `2`

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
  "state_transitions": [
    "pending",
    "streaming",
    "streaming",
    "complete"
  ],
  "rationale": "Response 'msg-resp-001' initialized in PENDING state, sequentially appended 2 chunks in arrival order, and completed successfully with stable ID.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Stable message ID preserved, two chunks appended strictly in order, and transitioned cleanly PENDING -> STREAMING -> COMPLETE.

---

## 2. Error Recovery Scenario (`--scenario error`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario error
```

Expected Decision: `STATE_ERROR_RECOVERED`  
Expected State: `error`  
Expected Content: `"Hello, [ERROR: Stream connection dropped]"`  
Expected Partial Text Preservation: `true`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_ERROR",
  "scenario_type": "error_recovery",
  "decision": "STATE_ERROR_RECOVERED",
  "message_id": "msg-resp-001",
  "state": "error",
  "content": "Hello, [ERROR: Stream connection dropped]",
  "chunks_received": 1,
  "error_message": "Stream connection dropped",
  "stable_id_preserved": true,
  "partial_text_preserved": true,
  "error_marker_present": true,
  "rationale": "Response 'msg-resp-001' received chunk 1 ('Hello, ') before stream failed. The error preserved previously received text intact and appended error marker.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Previously received text intact ('Hello, ') with error marker appended in-place upon mid-stream failure.

---

## 3. Boundary Scenario — Late Chunk Rejection (`--scenario boundary`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario boundary
```

Expected Decision: `CHUNK_AFTER_COMPLETION_REJECTED`  
Expected Rejection Exception: `ChunkRejectedError`  
Expected Buffer Unmodified: `true`

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
  "buffer_unmodified": true,
  "state_unmodified": true,
  "rejection_message": "Cannot append chunk ' [Late chunk arriving after stream close]' to message 'msg-resp-001': response is already in terminal state 'complete'.",
  "rationale": "Response 'msg-resp-001' reached COMPLETE state. Incoming late chunk ' [Late chunk arriving after stream close]' was rejected with ChunkRejectedError, preserving the finalized response buffer without corruption.",
  "classification": "chat_view_state_simulation"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Delayed chunk rejected by raising ChunkRejectedError, preserving sealed buffer without corruption.

---

## 4. Applied Question 1: Predict an Output (`--question 1`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 1
```

**Question Focus:** `predict_an_output`  
**Question Prompt:** A response is initiated with message ID 'msg-resp-001' in PENDING state. Chunk 1 ('Hello, ') arrives successfully. Before Chunk 2 can be received, the stream aborts with error 'Stream connection dropped'. What is the exact final state and content buffer of 'msg-resp-001'?  
**Selected Option:** `B` (`state='error', content='Hello, [ERROR: Stream connection dropped]'`)  
**Status:** `PASS`

Actual Output:
```json
{
  "question": {
    "question_id": "Q1_PREDICT_OUTPUT",
    "focus_area": "predict_an_output",
    "title": "Predict Output Under Mid-Stream Network Interruption",
    "prompt": "A response is initiated with message ID 'msg-resp-001' in PENDING state. Chunk 1 ('Hello, ') arrives successfully. Before Chunk 2 can be received, the stream aborts with error 'Stream connection dropped'. What is the exact final state and content buffer of 'msg-resp-001'?",
    "options": {
      "A": "state='error', content='' (Buffer cleared to avoid showing incomplete text)",
      "B": "state='error', content='Hello, [ERROR: Stream connection dropped]' (Text preserved + marker appended)",
      "C": "state='complete', content='Hello, ' (Truncated stream coerced to complete)",
      "D": "state='pending', content='Hello, ' (State remains pending awaiting reconnect)"
    },
    "correct_option": "B",
    "factual_answer": {
      "message_id": "msg-resp-001",
      "state": "error",
      "content": "Hello, [ERROR: Stream connection dropped]",
      "chunks_received": 1
    },
    "rationale": "In AI user experience design (Lesson 12: Reliability & Transparency), partial stream failures must never discard already-rendered tokens. Preserving previously received text retains immediate utility for the user, while an explicit in-place error marker explains the failure without silent data loss or disruptive layout collapse."
  },
  "assessment": {
    "question_id": "Q1_PREDICT_OUTPUT",
    "focus_area": "predict_an_output",
    "status": "PASS",
    "passed": true,
    "selected_option": "B",
    "predicted_output": {
      "message_id": "msg-resp-001",
      "state": "error",
      "content": "Hello, [ERROR: Stream connection dropped]",
      "chunks_received": 1
    },
    "actual_output": {
      "message_id": "msg-resp-001",
      "state": "error",
      "content": "Hello, [ERROR: Stream connection dropped]",
      "chunks_received": 1
    },
    "rationale": "In AI user experience design (Lesson 12: Reliability & Transparency), partial stream failures must never discard already-rendered tokens. Preserving previously received text retains immediate utility for the user, while an explicit in-place error marker explains the failure without silent data loss or disruptive layout collapse.",
    "classification": "chat_view_state_simulation"
  }
}
```

Exit code: `0` (Expected: `0`)

**Rationale:** In AI user experience design (Lesson 12: Reliability & Transparency), partial stream failures must never discard already-rendered tokens. Preserving previously received text retains immediate utility for the user, while an explicit in-place error marker explains the failure without silent data loss or disruptive layout collapse.

---

## 5. Applied Question 2: Diagnose a Failure (`--question 2`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 2
```

**Question Focus:** `diagnose_a_failure`  
**Question Prompt:** A client chat-view component successfully finalizes 'msg-resp-001' after receiving Chunk 1 ('Hello, ') and Chunk 2 ('how can I assist you today?'), entering COMPLETE state. A delayed network packet subsequently attempts to deliver ' [Late chunk arriving after stream close]'. The application raises ChunkRejectedError. What is the root cause of this failure and what UX invariant does it enforce?  
**Selected Option:** `B` (Attempted mutation of sealed message in terminal COMPLETE state)  
**Status:** `PASS`

Actual Output:
```json
{
  "question": {
    "question_id": "Q2_DIAGNOSE_FAILURE",
    "focus_area": "diagnose_a_failure",
    "title": "Diagnose Late Chunk Arrival on Finalized Message",
    "prompt": "A client chat-view component successfully finalizes 'msg-resp-001' after receiving Chunk 1 ('Hello, ') and Chunk 2 ('how can I assist you today?'), entering COMPLETE state. A delayed network packet subsequently attempts to deliver ' [Late chunk arriving after stream close]'. The application raises ChunkRejectedError. What is the root cause of this failure and what UX invariant does it enforce?",
    "options": {
      "A": "Root Cause: Network packet payload size exceeded max buffer limit.",
      "B": "Root Cause: Attempted mutation of a sealed message in terminal COMPLETE state; enforces transcript immutability.",
      "C": "Root Cause: HTTP 404 stream endpoint not found on server.",
      "D": "Root Cause: Message ID mismatch between client session and server socket."
    },
    "correct_option": "B",
    "factual_answer": {
      "exception_type": "ChunkRejectedError",
      "root_cause": "Attempted buffer append on message already in terminal COMPLETE state",
      "invariant_enforced": "Terminal state immutability protects finalized conversation history from out-of-order race conditions.",
      "final_buffer_preserved": "Hello, how can I assist you today?"
    },
    "rationale": "In asynchronous streaming architectures, network retries or lagged transport packets can arrive after a completion event. Permitting post-completion appends causes text flickering, transcript corruption, and broken user trust. The state machine must enforce terminal sealing: once COMPLETE or ERROR is reached, the buffer is immutable."
  },
  "assessment": {
    "question_id": "Q2_DIAGNOSE_FAILURE",
    "focus_area": "diagnose_a_failure",
    "status": "PASS",
    "passed": true,
    "selected_option": "B",
    "diagnosis": {
      "exception_type": "ChunkRejectedError",
      "root_cause": "Attempted buffer append on message already in terminal COMPLETE state",
      "invariant_enforced": "Terminal state immutability protects finalized conversation history from out-of-order race conditions.",
      "final_buffer_preserved": "Hello, how can I assist you today?"
    },
    "actual_diagnostic_evidence": {
      "rejection_verified": true,
      "rejection_exception": "ChunkRejectedError",
      "rejection_message": "Cannot append chunk ' [Late chunk arriving after stream close]' to message 'msg-resp-001': response is already in terminal state 'complete'.",
      "content_retained": "Hello, how can I assist you today?"
    },
    "rationale": "In asynchronous streaming architectures, network retries or lagged transport packets can arrive after a completion event. Permitting post-completion appends causes text flickering, transcript corruption, and broken user trust. The state machine must enforce terminal sealing: once COMPLETE or ERROR is reached, the buffer is immutable.",
    "classification": "chat_view_state_simulation"
  }
}
```

Exit code: `0` (Expected: `0`)

**Rationale:** In asynchronous streaming architectures, network retries or lagged transport packets can arrive after a completion event. Permitting post-completion appends causes text flickering, transcript corruption, and broken user trust. The state machine must enforce terminal sealing: once COMPLETE or ERROR is reached, the buffer is immutable.

---

## 6. Applied Question 3: Choose a Boundary Policy (`--question 3`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 3
```

**Question Focus:** `choose_boundary_policy`  
**Question Prompt:** When designing the client chat-view state manager, how should incoming chunks arriving after a terminal state (COMPLETE or ERROR) be handled at the system boundary? Choose the most robust boundary policy.  
**Selected Option:** `C` (`POLICY_EXPLICIT_REJECTION`: Fail-Fast with ChunkRejectedError)  
**Status:** `PASS`

Actual Output:
```json
{
  "question": {
    "question_id": "Q3_CHOOSE_BOUNDARY_POLICY",
    "focus_area": "choose_boundary_policy",
    "title": "Choose Boundary Policy for Terminal State Chunk Interceptions",
    "prompt": "When designing the client chat-view state manager, how should incoming chunks arriving after a terminal state (COMPLETE or ERROR) be handled at the system boundary? Choose the most robust boundary policy.",
    "options": {
      "A": "POLICY_SILENT_DISCARD: Discard late chunks silently without raising exceptions or logging.",
      "B": "POLICY_UNCONDITIONAL_APPEND: Append all arriving chunks unconditionally whenever they arrive.",
      "C": "POLICY_EXPLICIT_REJECTION: Raise ChunkRejectedError immediately (fail-fast) while preserving finalized buffer.",
      "D": "POLICY_RESET_PENDING: Reset message state back to PENDING and resume streaming from scratch."
    },
    "correct_option": "C",
    "factual_answer": {
      "chosen_policy": "POLICY_EXPLICIT_REJECTION",
      "exception": "ChunkRejectedError",
      "buffer_action": "NO_MUTATION",
      "system_behavior": "Fail-fast notification to monitoring/telemetry while preserving user-visible transcript integrity."
    },
    "rationale": "Silent discard (Policy A) masks transport protocol bugs and duplicate delivery defects from telemetry. Unconditional append (Policy B) causes race condition corruptions. Resetting (Policy D) destroys existing conversational context. Explicit rejection (Policy C) enforces fail-fast boundaries, guarantees buffer immutability, and provides observable diagnostic signals."
  },
  "assessment": {
    "question_id": "Q3_CHOOSE_BOUNDARY_POLICY",
    "focus_area": "choose_boundary_policy",
    "status": "PASS",
    "passed": true,
    "selected_option": "C",
    "chosen_policy": "POLICY_EXPLICIT_REJECTION",
    "policy_specification": {
      "chosen_policy": "POLICY_EXPLICIT_REJECTION",
      "exception": "ChunkRejectedError",
      "buffer_action": "NO_MUTATION",
      "system_behavior": "Fail-fast notification to monitoring/telemetry while preserving user-visible transcript integrity."
    },
    "verification_evidence": {
      "error_terminal_rejection": true,
      "complete_terminal_rejection": true,
      "error_buffer_preserved": true,
      "complete_buffer_preserved": true
    },
    "rationale": "Silent discard (Policy A) masks transport protocol bugs and duplicate delivery defects from telemetry. Unconditional append (Policy B) causes race condition corruptions. Resetting (Policy D) destroys existing conversational context. Explicit rejection (Policy C) enforces fail-fast boundaries, guarantees buffer immutability, and provides observable diagnostic signals.",
    "classification": "chat_view_state_simulation"
  }
}
```

Exit code: `0` (Expected: `0`)

**Rationale:** Silent discard (Policy A) masks transport protocol bugs and duplicate delivery defects from telemetry. Unconditional append (Policy B) causes race condition corruptions. Resetting (Policy D) destroys existing conversational context. Explicit rejection (Policy C) enforces fail-fast boundaries, guarantees buffer immutability, and provides observable diagnostic signals.

---

## 7. Full Questions Assessment Suite (`--questions`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --questions
```

Expected Status: `success`  
Expected Passed Questions: `3 / 3`  
Expected All Passed: `true`

Actual Summary:
```json
{
  "status": "success",
  "total_questions": 3,
  "passed_questions": 3,
  "failed_questions": 0,
  "all_passed": true
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 3 applied scenario assessment questions verified with factual answers and rationales.

---

## 8. Canonical Decision Table Check (`--check`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --check
```

Expected Status: `success`  
Expected Passed Scenarios: `3 / 3`  
Expected All Passed: `true`

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

**Result:** PASS — All canonical scenarios matched expected decisions, states, contents, and invariants.

---

## 9. Deliberate Tamper Regression Test (`--tamper`)

Command:
```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --tamper
```

Expected Exit Code: `1`  
Expected Error Type: `DecisionMismatchError`  
Expected Status: `expected_tamper_failure`

Actual Stderr Output:
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "error_message": "Verification failed: 1 scenario(s) did not match canonical decision table.",
  "exit_code": 1,
  "classification": "chat_view_state_simulation",
  "rationale": "Deliberately mutated expectation failed assertion as expected.",
  "details": {
    "status": "failure",
    "total_scenarios": 3,
    "passed_scenarios": 2,
    "failed_scenarios": 1,
    "all_passed": false,
    "classification": "chat_view_state_simulation",
    "scenarios": [
      {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "expected_decision": "TAMPERED_WRONG_DECISION",
        "actual_decision": "STATE_COMPLETE_SUCCESS",
        "expected_state": "complete",
        "actual_state": "complete",
        "matches_table": false,
        "status": "FAIL",
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
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — Deliberate wrong expectation strictly failed assertion with exit code 1, proving regression sensitivity.

---

## 10. Automated Unit Test Discovery Suite

Command:
```bash
python3 -m unittest discover -s 12-designing-ux-for-ai-applications/applied-labs/r40-t030 -p "test_*.py" -v
```

Expected Status: `OK` with non-zero test count (41 tests)  
Expected Exit Code: `0`

Actual Test Runner Output:
```
test_question_1_predict_output_factual_answer (test_example.TestAppliedQuestions.test_question_1_predict_output_factual_answer) ... ok
test_question_1_verification_check_passes (test_example.TestAppliedQuestions.test_question_1_verification_check_passes) ... ok
test_question_2_diagnose_failure_factual_answer (test_example.TestAppliedQuestions.test_question_2_diagnose_failure_factual_answer) ... ok
test_question_2_verification_check_passes (test_example.TestAppliedQuestions.test_question_2_verification_check_passes) ... ok
test_question_3_choose_boundary_policy_factual_answer (test_example.TestAppliedQuestions.test_question_3_choose_boundary_policy_factual_answer) ... ok
test_question_3_verification_check_passes (test_example.TestAppliedQuestions.test_question_3_verification_check_passes) ... ok
test_run_all_questions_assessment (test_example.TestAppliedQuestions.test_run_all_questions_assessment) ... ok
test_append_after_complete_preserves_content_unmodified (test_example.TestBoundaryAndTerminalStateRejection.test_append_after_complete_preserves_content_unmodified) ... ok
test_append_after_complete_raises_chunk_rejected_error (test_example.TestBoundaryAndTerminalStateRejection.test_append_after_complete_raises_chunk_rejected_error) ... ok
test_append_after_error_preserves_content_unmodified (test_example.TestBoundaryAndTerminalStateRejection.test_append_after_error_preserves_content_unmodified) ... ok
test_append_after_error_raises_chunk_rejected_error (test_example.TestBoundaryAndTerminalStateRejection.test_append_after_error_raises_chunk_rejected_error) ... ok
test_complete_after_complete_raises_invalid_state_transition (test_example.TestBoundaryAndTerminalStateRejection.test_complete_after_complete_raises_invalid_state_transition) ... ok
test_complete_after_error_raises_invalid_state_transition (test_example.TestBoundaryAndTerminalStateRejection.test_complete_after_error_raises_invalid_state_transition) ... ok
test_fail_after_complete_raises_invalid_state_transition (test_example.TestBoundaryAndTerminalStateRejection.test_fail_after_complete_raises_invalid_state_transition) ... ok
test_fail_after_error_raises_invalid_state_transition (test_example.TestBoundaryAndTerminalStateRejection.test_fail_after_error_raises_invalid_state_transition) ... ok
test_boundary_scenario_contract (test_example.TestCanonicalScenarios.test_boundary_scenario_contract) ... ok
test_decision_table_check_success (test_example.TestCanonicalScenarios.test_decision_table_check_success) ... ok
test_decision_table_check_tamper_detects_failure (test_example.TestCanonicalScenarios.test_decision_table_check_tamper_detects_failure) ... ok
test_error_scenario_contract (test_example.TestCanonicalScenarios.test_error_scenario_contract) ... ok
test_normal_scenario_contract (test_example.TestCanonicalScenarios.test_normal_scenario_contract) ... ok
test_complete_transitions_to_complete (test_example.TestChatViewStateManagerLifecycle.test_complete_transitions_to_complete) ... ok
test_first_chunk_transitions_to_streaming (test_example.TestChatViewStateManagerLifecycle.test_first_chunk_transitions_to_streaming) ... ok
test_init_pending_state (test_example.TestChatViewStateManagerLifecycle.test_init_pending_state) ... ok
test_invalid_chunk_type_raises_type_error (test_example.TestChatViewStateManagerLifecycle.test_invalid_chunk_type_raises_type_error) ... ok
test_invalid_message_id_raises_value_error (test_example.TestChatViewStateManagerLifecycle.test_invalid_message_id_raises_value_error) ... ok
test_second_chunk_appends_in_order (test_example.TestChatViewStateManagerLifecycle.test_second_chunk_appends_in_order) ... ok
test_stable_message_id_across_all_transitions (test_example.TestChatViewStateManagerLifecycle.test_stable_message_id_across_all_transitions) ... ok
test_cli_check_subprocess (test_example.TestCommandLineInterface.test_cli_check_subprocess) ... ok
test_cli_no_args_exits_nonzero (test_example.TestCommandLineInterface.test_cli_no_args_exits_nonzero) ... ok
test_cli_questions_flag_subprocess (test_example.TestCommandLineInterface.test_cli_questions_flag_subprocess) ... ok
test_cli_scenario_boundary_subprocess (test_example.TestCommandLineInterface.test_cli_scenario_boundary_subprocess) ... ok
test_cli_scenario_error_subprocess (test_example.TestCommandLineInterface.test_cli_scenario_error_subprocess) ... ok
test_cli_scenario_normal_subprocess (test_example.TestCommandLineInterface.test_cli_scenario_normal_subprocess) ... ok
test_cli_scenario_questions_subprocess (test_example.TestCommandLineInterface.test_cli_scenario_questions_subprocess) ... ok
test_cli_single_question_flags_subprocess (test_example.TestCommandLineInterface.test_cli_single_question_flags_subprocess) ... ok
test_cli_tamper_subprocess_exits_nonzero (test_example.TestCommandLineInterface.test_cli_tamper_subprocess_exits_nonzero) ... ok
test_error_empty_reason_fallback (test_example.TestErrorRecoveryAndTextPreservation.test_error_empty_reason_fallback) ... ok
test_error_in_pending_state (test_example.TestErrorRecoveryAndTextPreservation.test_error_in_pending_state) ... ok
test_error_in_streaming_state_preserves_partial_text (test_example.TestErrorRecoveryAndTextPreservation.test_error_in_streaming_state_preserves_partial_text) ... ok
test_error_with_multiple_chunks_preserves_all_chunks (test_example.TestErrorRecoveryAndTextPreservation.test_error_with_multiple_chunks_preserves_all_chunks) ... ok
test_snapshot_representation (test_example.TestErrorRecoveryAndTextPreservation.test_snapshot_representation) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.295s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 41 unit tests passed in fresh process without failures or errors.

---

## 11. Summary of Verification Checks

| # | Check / Scenario | Invocation / Action | Expected Result | Actual Result | Exit Code | Status |
|---|---|---|---|---|---|---|
| 1 | `SCENARIO_NORMAL` | `--scenario normal` | `STATE_COMPLETE_SUCCESS` | `STATE_COMPLETE_SUCCESS` | `0` | **PASS** |
| 2 | `SCENARIO_ERROR` | `--scenario error` | `STATE_ERROR_RECOVERED` | `STATE_ERROR_RECOVERED` | `0` | **PASS** |
| 3 | `SCENARIO_BOUNDARY` | `--scenario boundary` | `CHUNK_AFTER_COMPLETION_REJECTED` | `CHUNK_AFTER_COMPLETION_REJECTED` | `0` | **PASS** |
| 4 | `QUESTION_1` | `--question 1` | `Q1_PREDICT_OUTPUT` (Opt B) | `Q1_PREDICT_OUTPUT` (Opt B) | `0` | **PASS** |
| 5 | `QUESTION_2` | `--question 2` | `Q2_DIAGNOSE_FAILURE` (Opt B) | `Q2_DIAGNOSE_FAILURE` (Opt B) | `0` | **PASS** |
| 6 | `QUESTION_3` | `--question 3` | `Q3_CHOOSE_BOUNDARY_POLICY` (Opt C) | `Q3_CHOOSE_BOUNDARY_POLICY` (Opt C) | `0` | **PASS** |
| 7 | `QUESTIONS_ALL` | `--questions` | `3/3 passed` | `3/3 passed` | `0` | **PASS** |
| 8 | `CANONICAL_CHECK` | `--check` | `all_passed: true` | `all_passed: true` | `0` | **PASS** |
| 9 | `DELIBERATE_TAMPER` | `--tamper` | Exit `1` (`DecisionMismatchError`) | Exit `1` (`DecisionMismatchError`) | `1` | **PASS** |
| 10 | `UNIT_TEST_SUITE` | `unittest discover` | `41/41 tests OK` | `41/41 tests OK` | `0` | **PASS** |

All 10 checks passed successfully. Verification complete.
