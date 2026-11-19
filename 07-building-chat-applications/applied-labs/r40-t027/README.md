# Applied Lab: Chat-View State Lifecycle and Streaming Recovery (R40-T027)

## Overview & Lesson 07 Context

In [Lesson 07 — Building Generative AI-Powered Chat Applications](../../README.md?WT.mc_id=academic-105485-koreyst), we explore the UX and architectural considerations for deploying chat applications powered by Large Language Models (LLMs). Real-world production chat applications (such as ChatGPT, Microsoft Copilot, and enterprise customer service bots) rarely wait for the model to generate its entire response before displaying text. Instead, they stream tokens incrementally to minimize perceived response time and provide immediate feedback.

This architectural pattern requires a client-side chat-view layer capable of managing the lifecycle of each response. This applied lab provides a self-contained, deterministic reference implementation and regression test suite modeling this lifecycle.

## Contract & Invariants

The chat-view state manager enforces five foundational invariants:

1. **Stable Message Identity**: A unique `message_id` (e.g., `'msg-resp-001'`) is assigned at the moment the request is initiated and persists unchanged through every lifecycle state. This allows client UI frameworks to maintain stable DOM nodes, scroll anchors, and avoid visual re-rendering artifacts.
2. **Four Local States**:
   - `PENDING`: The user prompt is in flight; the client renders a typing indicator while awaiting the first token (buffer is empty `""`).
   - `STREAMING`: The first chunk arrives; the view transitions to active streaming and appends subsequent tokens sequentially.
   - `COMPLETE`: The stream signals completion; the response buffer is finalized.
   - `ERROR`: An interruption or failure occurs; previously received text is preserved, and an error marker is appended.
3. **Strict Sequential Chunk Concatenation**: Arriving chunks are appended in strict arrival order (e.g., Chunk 1: `"Hello, "` followed by Chunk 2: `"how can I assist you today?"`).
4. **Error Recovery with Text Preservation**: If a network drop, timeout, or server error occurs after partial text has arrived, the system **never** wipes out or drops the received text. It preserves the exact received content and appends a visible error marker (`[ERROR: <reason>]`), enabling the user to read partial content and trigger retry actions.
5. **Terminal State Rejection**: Once a response transitions into a terminal state (`COMPLETE` or `ERROR`), any late or out-of-order chunks are strictly rejected by raising a `ChunkRejectedError`. The finalized response buffer remains completely protected against corruption.

## Classification & Scope Note (Simulation / Test Double)

> [!NOTE]
> **Simulation / Test Double Classification:**
> This lab is implemented strictly as a **local state machine and test double** using Python's standard library. It requires zero external dependencies, no cloud credentials, no paid API keys, no local weights download, and no GPU or physical hardware.
>
> **Where Simplifications Stop:**
> - The component models the client-side state machine and buffer management.
> - It does not implement low-level HTTP/SSE network sockets, TLS handshakes, WebSocket heartbeats, markdown typography rendering, or multi-user database persistence.

---

## Canonical Test Fixtures & Scenarios

### Fixture Definitions

- **Stable Message ID**: `'msg-resp-001'`
- **Ordered Chunks**:
  - Chunk 1: `"Hello, "`
  - Chunk 2: `"how can I assist you today?"`
- **Error Condition**: `"Stream connection dropped"`
- **Late Chunk**: `" [Late chunk arriving after stream close]"`

---

## Scenarios & Invocations

### 1. Normal Scenario (`--scenario normal`)

Simulates a successful end-to-end response:
1. `init_pending("msg-resp-001")` -> State: `PENDING`, Content: `""`
2. `append_chunk("Hello, ")` -> State: `STREAMING`, Content: `"Hello, "`
3. `append_chunk("how can I assist you today?")` -> State: `STREAMING`, Content: `"Hello, how can I assist you today?"`
4. `complete_response()` -> State: `COMPLETE`, Content: `"Hello, how can I assist you today?"`

**Invocation:**
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario normal
```

**Expected JSON Output (`exit 0`):**
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

---

### 2. Error Recovery Scenario (`--scenario error`)

Simulates a network failure after receiving Chunk 1:
1. `init_pending("msg-resp-001")` -> State: `PENDING`
2. `append_chunk("Hello, ")` -> State: `STREAMING`, Content: `"Hello, "`
3. Network connection drops -> `fail_response("Stream connection dropped")`
4. State: `ERROR`, Content: `"Hello, [ERROR: Stream connection dropped]"`

**Invocation:**
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario error
```

**Expected JSON Output (`exit 0`):**
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

---

### 3. Boundary Scenario — Late Chunk Rejection (`--scenario boundary`)

Simulates a stream that has reached `COMPLETE` state receiving a delayed chunk:
1. Response completed with `"Hello, how can I assist you today?"`
2. Late chunk arrives: `" [Late chunk arriving after stream close]"`
3. `append_chunk()` raises `ChunkRejectedError`
4. State remains `COMPLETE`, content remains `"Hello, how can I assist you today?"` without modification.

**Invocation:**
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --scenario boundary
```

**Expected JSON Output (`exit 0`):**
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

---

### 4. Canonical Decision Table Check (`--check`)

Runs all three canonical scenarios and validates them against the decision table:

**Invocation:**
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --check
```

**Expected JSON Output (`exit 0`):**
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

---

### 5. Deliberate Tamper Regression Test (`--tamper`)

Simulates a deliberate expectation violation or regression to verify that the check strictly fails with a non-zero exit code:

**Invocation:**
```bash
python3 07-building-chat-applications/applied-labs/r40-t027/example.py --tamper
```

**Expected JSON Output on Stderr (`exit 1`):**
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

---

## Automated Unit Test Discovery Suite

Execute the full suite of unit and regression tests across state transitions, boundary rejections, and CLI processes:

```bash
python3 -m unittest discover -s 07-building-chat-applications/applied-labs/r40-t027 -p "test_*.py" -v
```

All 30 unit tests execute in a fresh isolated process and verify that the chat-view state manager strictly enforces all invariants.
