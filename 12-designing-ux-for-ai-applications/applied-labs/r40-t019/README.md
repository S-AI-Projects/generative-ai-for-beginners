
# R40-T019: Chat-View State — Evaluation Experiment

## Objective

Model the local state of one chat response and evaluate how a chat interface handles streaming, completion, and errors.

This experiment demonstrates four response states:

- `pending`: The response has been created but no text has arrived.
- `streaming`: Response chunks are being received.
- `complete`: The response has finished successfully.
- `error`: The response failed, while preserving any text already received.

## Requirements

- Python 3
- Python standard library only
- No model download, API key, paid provider, GPU, or external service

## Files

- `example.py`: Implements the chat message state and demonstration scenarios.
- `test_example.py`: Tests the state transitions and message contract.

## Run the experiment

Run each scenario separately from the repository root:

```bash
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t019/example.py normal
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t019/example.py boundary
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t019/example.py failure
python3 12-designing-ux-for-ai-applications/applied-labs/r40-t019/example.py evaluation
```

The experiment demonstrates:

1. **Normal:** Two chunks are appended in order and the response completes.
2. **Boundary:** A short response completes after one chunk.
3. **Failure:** An error occurs after partial text arrives. The received text remains available with an error marker.
4. **Evaluation:** Three controlled input configurations are compared.

## Run the tests

From the repository root:

```bash
python3 -m unittest discover -s 12-designing-ux-for-ai-applications/applied-labs/r40-t019 -p "test_*.py"
```

The tests check stable message IDs, ordered chunk appending, completion, error preservation, and rejection of chunks after completion or failure.

## Evaluation

The experiment compares three local configurations:

| Configuration | Chunks | Measurement |
|---|---:|---|
| Small | 1 | Append operations and final characters |
| Medium | 2 | Append operations and final characters |
| Large | 5 | Append operations and final characters |

The measurements describe the local state-management workload. More chunks require more append operations. This does not establish real-world model accuracy, response latency, or production performance.

## Expected behavior

- A message keeps the same ID throughout its lifecycle.
- Chunks are appended in their received order.
- A completed response cannot receive additional chunks.
- An error preserves previously received text.
- The error state exposes an error marker.

## Scope and limitations

This is a deterministic, local simulation using synthetic text chunks. It does not connect to a language model, network stream, or real chat interface. It evaluates the correctness of a small response-state contract, not the quality or accuracy of generated answers.

The example focuses on one response at a time and does not implement multiple concurrent messages, cancellation, retries, or a graphical interface.

