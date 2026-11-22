# Applied Lab R40-T001: Chat-View State Lifecycle & Recovery

## Overview

This lab demonstrates the response lifecycle for chat-based AI interfaces as presented in [Lesson 12: Designing UX for AI Applications](../../README.md).

In generative AI user experiences, model generation is rarely instantaneous. Presenting streaming responses progressively requires careful state modeling to prevent user confusion, preserve partial responses on connection drops, maintain stable identity for message components, and reject unexpected packets.

## State Lifecycle Model

```
       [PENDING]
           │
           │ (first chunk arrives)
           ▼
      [STREAMING] ◄─── (subsequent chunks append)
       │       │
       │       └───► [ERROR] (connection failure, preserves text + [ERROR: ...])
       │
       ▼ (stream completes)
   [COMPLETE]
       │
       └───► (late arriving chunk rejected -> ChunkRejectedError)
```

## Contract Rules

1. **Message Identity**: Stable `message_id` (default `"msg-resp-001"`) is established at creation and persists unchanged across all transitions.
2. **Sequential Chunks**: Streaming chunks (`"Hello, "` then `"how can I assist you today?"`) append in strict order.
3. **Error Recovery**: An unexpected stream failure transitions the response to `ERROR`, retaining previously rendered text and appending `[ERROR: <reason>]`.
4. **Post-Completion Rejection**: Arriving chunks after `COMPLETE` or `ERROR` are rejected with `ChunkRejectedError`.

## Local Test Double Scope

This component is an offline, deterministic local state machine.
- No remote LLM services or API keys required.
- No local neural network weights or GPU required.
- Python standard library only (`dataclasses`, `enum`, `json`, `argparse`, `unittest`).

## Invocations & Scenarios

Run the scenarios from the repository root:

```bash
# Normal complete stream
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t001/example.py --scenario normal

# Stream error with partial text preservation
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t001/example.py --scenario error

# Late chunk post-completion rejection
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t001/example.py --scenario boundary

# Canonical check
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t001/example.py --check

# Automated unit tests
python3 -m unittest discover -s 12-designing-ux-for-ai-applications/applied-labs/r40-t001 -p "test_*.py" -v
```
