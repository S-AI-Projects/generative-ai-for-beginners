# R40-T016: Allowlisted Action Policy

## Objective

Evaluate a proposed action against an explicit tool allowlist and argument
schema before allowing it to reach an executor.

This local lab demonstrates a small policy check related to the Safety System
layer discussed in the lesson.

## Prerequisites

- Python 3
- A local checkout of this repository
- Python standard library only

No model download, API key, paid provider, GPU, or physical device is needed.

## Policy fixture

Only the read tool is allowed. It requires one string argument named path.

Input fixture: {"tool": "read", "arguments": {"path": "notes.txt"}}

The delete tool is not allowlisted.

## Run from the repository root

Normal scenario:

    python3 03-using-generative-ai-responsibly/applied-labs/r40-t016/example.py --scenario normal

Expected output: allowed is true and the mock result is MOCK READ: notes.txt.

Boundary scenario:

    python3 03-using-generative-ai-responsibly/applied-labs/r40-t016/example.py --scenario boundary

Expected decision: rejected with Unknown tool. The executor is not called.

Failure scenario:

    python3 03-using-generative-ai-responsibly/applied-labs/r40-t016/example.py --scenario failure

Expected decision: rejected because the required path argument is missing.
This scenario exits with status 1.

## Run automated tests

    python3 -m unittest discover -s 03-using-generative-ai-responsibly/applied-labs/r40-t016 -p "test_*.py"

The tests compare baseline and refactored behavior using the same fixtures.
They also verify that rejected actions never reach the executor and that a
deliberately incorrect assertion causes a nonzero test exit.

## Refactoring responsibility

The baseline combines validation and execution in one function.
The refactored implementation extracts validation into validate_action().
The equivalence test checks decisions, results, and executor calls.

## Scope and limitations

The executor is a deterministic local mock. It does not read or delete files,
contact a cloud service, or invoke an AI model.

The path check only verifies that path is a non-empty string. It does not
check whether a file exists or whether a real filesystem permits access.

This example illustrates narrow application-level allowlisting and argument
validation. It does not prove that a model is safe or replace operating-system
permissions, sandboxing, authentication, or authorization.
