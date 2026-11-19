# Applied Lab: Chat-View State Lifecycle & Scenario Assessment (R40-T030)

## Overview & Lesson 12 Context

In [Lesson 12 — Designing UX for AI Applications](../../README.md?WT.mc_id=academic-105485-koreyst), we explore foundational user experience principles for artificial intelligence: **usability, reliability, accessibility, explainability, and user control**.

Unlike conventional deterministic web applications where UI views render predictable responses synchronously, Generative AI applications introduce high latency, non-deterministic token generation, and multi-second streaming responses. In an AI chat interface, how the frontend handles lifecycle state transitions directly dictates user trust, perceived latency, and overall reliability:

1. **Responsiveness vs. Uncertainty (Pending State):** When a user submits a prompt, LLM reasoning and first-token latency (TTFT) can take hundreds of milliseconds or several seconds. A responsive chat-view immediately registers the message in a `pending` state with a stable ID, rendering an accessible typing/loading indicator so the user knows their request was received.
2. **Perceived Speed & Explainability (Streaming State):** Displaying tokens incrementally as they arrive (`streaming`) drastically cuts perceived response time. Arriving chunks must append in strict arrival sequence to prevent scrambled prose.
3. **Resilience & Graceful Failure (Error Recovery):** Network drops, token rate-limits, or timeout aborts can strike mid-generation. In traditional software, unhandled errors often wipe the view or present a blank screen. In AI applications, erasing partially streamed tokens destroys value and fractures user trust. Reliable UX demands that partial generations remain visible, accompanied by a clear, in-place error marker (`[ERROR: <reason>]`) and actionable recovery controls.
4. **Data Integrity & Immutability (Terminal State Boundary):** Once a response signals completion (`complete`) or encounters an unrecoverable failure (`error`), the message buffer must be sealed. Out-of-order packets, delayed socket frames, or background retry loops attempting to deliver late chunks must be rejected (`ChunkRejectedError`) to protect the transcript against mutation.

This applied lab implements a deterministic, self-contained client-side state machine and scenario assessment suite modeling these exact UX invariants.

---

## Contract & Invariants

The chat-view state manager strictly enforces five core invariants:

| Invariant | Lifecycle Stage | Rule & Behavior |
|---|---|---|
| **Stable Message Identity** | Entire Lifecycle | `message_id` (e.g. `'msg-resp-001'`) is assigned at creation and remains immutable across all state transitions. Frontends rely on stable keys for DOM reconciliation, accessibility tree nodes, and scroll anchoring. |
| **Four Local States** | State Transitions | Exactly four mutually exclusive states: `pending` -> `streaming` -> `complete` or `error`. |
| **Strict Ordered Concatenation** | Streaming | Sequential chunks append strictly in arrival order (Chunk 1: `"Hello, "` + Chunk 2: `"how can I assist you today?"`). |
| **Partial Text Preservation on Error** | Error Recovery | If a stream aborts mid-flight, previously received text is preserved intact and an error marker (`[ERROR: <reason>]`) is appended directly to the buffer. |
| **Terminal State Immutability** | Boundary Enforcement | Once in `complete` or `error`, further chunk arrivals raise `ChunkRejectedError`. The finalized message buffer is protected against corruption. |

---

## Classification & Scope Note (Simulation / Test Double)

> [!NOTE]
> **Simulation / Test Double Classification:**
> This component is strictly a **local client-side chat-view state test double**, implemented using Python's standard library.
>
> - **Zero External Dependencies:** Requires no third-party libraries, no cloud credentials, no paid API keys, and no local LLM weight downloads.
> - **Zero Hardware Overhead:** Runs in memory on standard commodity CPU without GPU or specialized accelerator requirements.
>
> **Where Simplifications Stop:**
> - The component models the local frontend view state transitions, buffer concatenation, error recovery, and terminal boundary invariants.
> - It deliberately omits low-level transport mechanisms (SSE/WebSocket sockets, TCP keep-alives, TLS handshakes), markdown typography rendering, virtual DOM diffing, and distributed database persistence.

---

## The Three Applied Questions

This lab includes three applied scenario assessment questions evaluating real-world AI UX engineering decisions. Each question features a prompt, multiple-choice options, a factual answer, architectural rationale, and an executable verification check.

### Question 1: Predict an Output (Forecasting Partial Stream Interruption)

- **Focus:** `predict_an_output`
- **Question Prompt:**
  > A response is initiated with message ID `'msg-resp-001'` in `pending` state. Chunk 1 (`"Hello, "`) arrives successfully. Before Chunk 2 can be received, the stream aborts with error `'Stream connection dropped'`. What is the exact final state and content buffer of `'msg-resp-001'`?
- **Options:**
  - `A`: `state='error'`, `content=''` (Buffer cleared to avoid showing incomplete text)
  - `B`: `state='error'`, `content='Hello, [ERROR: Stream connection dropped]'` (Text preserved + marker appended)
  - `C`: `state='complete'`, `content='Hello, '` (Truncated stream coerced to complete)
  - `D`: `state='pending'`, `content='Hello, '` (State remains pending awaiting reconnect)
- **Factual Answer:** **Option B** (`state='error'`, `content='Hello, [ERROR: Stream connection dropped]'`)
- **Rationale:**
  Under Lesson 12 UX guidelines (Reliability and Transparency), clearing partial text destroys already-generated information and disorients the user. Preserving previously received tokens preserves immediate utility, while the in-place error marker transparently explains the interruption without silent data loss.
- **Executable Check:**
  ```bash
  python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 1
  ```

---

### Question 2: Diagnose a Failure (Root Cause Analysis of Late Packet Arrival)

- **Focus:** `diagnose_a_failure`
- **Question Prompt:**
  > A client chat-view component successfully finalizes `'msg-resp-001'` after receiving Chunk 1 (`"Hello, "`) and Chunk 2 (`"how can I assist you today?"`), entering `complete` state. A delayed network packet subsequently attempts to deliver `' [Late chunk arriving after stream close]'`. The application raises `ChunkRejectedError`. What is the root cause of this failure and what UX invariant does it enforce?
- **Options:**
  - `A`: Root Cause: Network packet payload size exceeded max buffer limit.
  - `B`: Root Cause: Attempted mutation of a sealed message in terminal `complete` state; enforces transcript immutability.
  - `C`: Root Cause: HTTP 404 stream endpoint not found on server.
  - `D`: Root Cause: Message ID mismatch between client session and server socket.
- **Factual Answer:** **Option B** (Attempted mutation of a sealed message in terminal `complete` state; enforces transcript immutability)
- **Rationale:**
  In asynchronous streaming architectures, transport retries or out-of-order socket packets can arrive after a stream closure signal. Allowing post-completion appends mutates finalized chat history, causes visual UI flickering, and breaks user trust. Raising `ChunkRejectedError` protects buffer immutability.
- **Executable Check:**
  ```bash
  python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 2
  ```

---

### Question 3: Choose a Boundary Policy (Terminal State Chunk Interception)

- **Focus:** `choose_boundary_policy`
- **Question Prompt:**
  > When designing the client chat-view state manager, how should incoming chunks arriving after a terminal state (`complete` or `error`) be handled at the system boundary? Choose the most robust boundary policy.
- **Options:**
  - `A`: `POLICY_SILENT_DISCARD`: Discard late chunks silently without raising exceptions or logging.
  - `B`: `POLICY_UNCONDITIONAL_APPEND`: Append all arriving chunks unconditionally whenever they arrive.
  - `C`: `POLICY_EXPLICIT_REJECTION`: Raise `ChunkRejectedError` immediately (fail-fast) while preserving finalized buffer.
  - `D`: `POLICY_RESET_PENDING`: Reset message state back to `pending` and resume streaming from scratch.
- **Factual Answer:** **Option C** (`POLICY_EXPLICIT_REJECTION`)
- **Rationale:**
  Silent discard (Policy A) hides network protocol bugs, duplicate delivery defects, and gateway race conditions from client monitoring/telemetry. Unconditional append (Policy B) corrupts transcripts and induces UI re-render races. Resetting (Policy D) discards existing context. Explicit rejection (Policy C) enforces fail-fast boundaries, guarantees transcript immutability, and provides observable diagnostic signals.
- **Executable Check:**
  ```bash
  python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 3
  ```

---

## Canonical Test Fixtures & Scenarios

### Canonical Fixtures

- **Stable Message ID:** `'msg-resp-001'`
- **Chunk 1:** `"Hello, "`
- **Chunk 2:** `"how can I assist you today?"`
- **Error Reason:** `"Stream connection dropped"`
- **Late Chunk:** `" [Late chunk arriving after stream close]"`

---

## CLI Invocations and Expected Output

### 1. Normal Scenario (`--scenario normal`)

Simulates a successful 2-chunk streaming lifecycle ending in `complete`:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario normal
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

---

### 2. Error Recovery Scenario (`--scenario error`)

Simulates a mid-stream network drop preserving partial text with an error marker:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario error
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
  "chunks_received": 1,
  "error_message": "Stream connection dropped",
  "stable_id_preserved": true,
  "partial_text_preserved": true,
  "error_marker_present": true,
  "rationale": "Response 'msg-resp-001' received chunk 1 ('Hello, ') before stream failed. The error preserved previously received text intact and appended error marker.",
  "classification": "chat_view_state_simulation"
}
```

---

### 3. Boundary Scenario — Late Chunk Rejection (`--scenario boundary`)

Simulates a completed message intercepting a delayed late chunk:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario boundary
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
  "buffer_unmodified": true,
  "state_unmodified": true,
  "rejection_message": "Cannot append chunk ' [Late chunk arriving after stream close]' to message 'msg-resp-001': response is already in terminal state 'complete'.",
  "rationale": "Response 'msg-resp-001' reached COMPLETE state. Incoming late chunk ' [Late chunk arriving after stream close]' was rejected with ChunkRejectedError, preserving the finalized response buffer without corruption.",
  "classification": "chat_view_state_simulation"
}
```

---

### 4. Applied Questions Assessment (`--questions`)

Evaluates all three applied questions, returning questions, options, factual answers, rationales, and executable verification results:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --questions
```

**Expected JSON Output (`exit 0`):**
```json
{
  "status": "success",
  "total_questions": 3,
  "passed_questions": 3,
  "failed_questions": 0,
  "all_passed": true,
  "classification": "chat_view_state_simulation"
}
```

---

### 5. Canonical Decision Table Check (`--check`)

Validates all canonical scenarios against the reference decision table:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --check
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

### 6. Deliberate Tamper Regression Test (`--tamper`)

Simulates a deliberate expectation violation to demonstrate that regressions produce a non-zero exit code (`exit 1`):

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --tamper
```

**Expected JSON Output on Stderr (`exit 1`):**
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "error_message": "Verification failed: 1 scenario(s) did not match canonical decision table.",
  "exit_code": 1,
  "classification": "chat_view_state_simulation",
  "rationale": "Deliberately mutated expectation failed assertion as expected."
}
```

---

## Automated Unit Test Discovery Suite

Run the full automated test suite containing 41 test cases in an isolated subprocess:

```bash
python3 -m unittest discover -s 12-designing-ux-for-ai-applications/applied-labs/r40-t030 -p "test_*.py" -v
```

All 41 tests execute in under 0.5s with zero external dependencies.
