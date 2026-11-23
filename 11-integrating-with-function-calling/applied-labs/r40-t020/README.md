# R40-T020: Chat-View State — Scenario Assessment

## Objective

Assess how a local chat response behaves during pending, streaming, completion, and error states.

This is a local Python simulation using synthetic data. It does not call a real model or external API.

## Requirements

- Python 3
- Python standard library
- Local repository checkout

## Run the example

From the repository root:

    python3 11-integrating-with-function-calling/applied-labs/r40-t020/example.py

Expected output:

    Initial: pending
    After start: streaming
    Received text: Function call completed successfully.
    Final state: complete
    Rejected: Chunks are accepted only while streaming

## Applied Question 1 — Predict the output

**Question:** What text is stored after the chunks "Hello " and "world" are appended?

**Answer:** Hello world.

**Rationale:** Each chunk is appended to the existing text.

**Executable check:** `test_two_chunks_complete_in_order` verifies the exact text and final state.

## Applied Question 2 — Diagnose the failure

**Question:** A response receives "Partial result" and then encounters "Connection lost". Should the received text disappear?

**Answer:** No. The text remains available and the message enters the error state with an error marker.

**Rationale:** Preserving received text keeps useful partial output available when a response cannot finish.

**Executable check:** `test_error_preserves_received_text` checks the stored text, error state, and error message.

## Applied Question 3 — Choose the boundary policy

**Question:** Should another chunk be accepted after a message reaches the complete state?

**Answer:** No. Reject the late chunk and preserve the completed text.

**Rationale:** A completed response must not silently change. The same rule applies after an error.

**Executable check:** `test_chunk_after_completion_is_rejected` and `test_chunk_after_error_is_rejected` verify this policy.

## Test command

    python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t020 -p "test_*.py"

## Scope and limitations

This is a deterministic local simulation. It uses no API keys, network requests, external services, or model downloads. It demonstrates application-side response state handling, not actual model performance.
