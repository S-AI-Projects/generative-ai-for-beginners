# Applied Lab R40-T006: Chat-View State Lifecycle (Refactored Teaching Example)

## Overview

This lab extends [Lesson 07: Building Generative AI-Powered Chat Applications](../../README.md) by modeling the chat response lifecycle and refactoring a monolithic baseline by extracting a dedicated buffer responsibility.

## Contract & Response Lifecycle

```
       [PENDING]
           │
           │ (first chunk arrives)
           ▼
      [STREAMING] ◄─── (subsequent chunks append in order)
       │       │
       │       └───► [ERROR] (connection failure, preserves text + [ERROR: ...])
       │
       ▼ (stream completes)
   [COMPLETE]
       │
       └───► (late chunk arriving after complete is rejected -> ChunkRejectedError)
```

1. **Stable Message Identity**: `message_id` persists unchanged throughout all lifecycle transitions.
2. **Ordered Streaming Chunks**: Two chunks (`"Hello, "` then `"how can I assist you today?"`) append sequentially.
3. **Error Recovery**: Stream failure preserves previously accumulated text and attaches `[ERROR: <reason>]`.
4. **Terminal State Boundary**: Late packets arriving after `COMPLETE` or `ERROR` are rejected by raising `ChunkRejectedError`.

## Focus: Extraction of `StreamingContentBuffer`

The baseline design concentrated both state coordination and buffer concatenation into `BaselineChatResponseManager`.
In the refactored architecture:
- `StreamingContentBuffer` encapsulates buffer concatenation, partial text preservation, and error marker injection.
- `RefactoredChatResponseManager` coordinates lifecycle states and terminal invariants.
- 100% behavioral equivalence is proven across all normal, error, and boundary fixtures.

## Scope Note (Simulation / Test Double)

This component is an offline state machine test double using only Python's standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Normal complete stream
python3 07-building-chat-applications/applied-labs/r40-t006/example.py --scenario normal

# Stream error with partial text preservation
python3 07-building-chat-applications/applied-labs/r40-t006/example.py --scenario error

# Post-completion chunk rejection
python3 07-building-chat-applications/applied-labs/r40-t006/example.py --scenario boundary

# Verify refactored before/after equivalence
python3 07-building-chat-applications/applied-labs/r40-t006/example.py --refactor-check

# Canonical check
python3 07-building-chat-applications/applied-labs/r40-t006/example.py --check

# Automated unit tests
python3 -m unittest discover -s 07-building-chat-applications/applied-labs/r40-t006 -p "test_*.py" -v
```
