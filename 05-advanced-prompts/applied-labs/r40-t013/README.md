
# R40-T013: Prompt-template escaping

## Goal

This local Python example demonstrates how template variables can be validated and replaced while keeping supplied data separate from fixed template instructions.

It compares two approaches:

1. Regular-expression replacement using `re.sub`.
2. A simple left-to-right scanner.

Both approaches use the same template, input values, and expected results.

## Prerequisites

- Python 3
- Python standard library only
- A local checkout of this repository

No model, API key, paid service, GPU, or physical device is required.

## Example template

    Hello {{name}}. Explain {{topic}} clearly.

Normal input:

    {"name": "Asha", "topic": "Photosynthesis"}

Expected output:

    Hello Asha. Explain Photosynthesis clearly.

Boundary input:

    {"name": "Asha {{admin}}", "topic": "Maths {advanced}"}

Expected output:

    Hello Asha {{admin}}. Explain Maths {advanced} clearly.

Braces inside supplied values remain literal. Inserted values are not processed again as template instructions.

## Run the example

From the repository root:

    python3 05-advanced-prompts/applied-labs/r40-t013/example.py

Run individual scenarios:

    python3 05-advanced-prompts/applied-labs/r40-t013/example.py --scenario normal

    python3 05-advanced-prompts/applied-labs/r40-t013/example.py --scenario boundary

The example prints JSON containing the inputs, both results, and expected output.

## Failure scenarios

A missing topic is rejected:

    python3 05-advanced-prompts/applied-labs/r40-t013/example.py --scenario missing

An unknown input key is rejected:

    python3 05-advanced-prompts/applied-labs/r40-t013/example.py --scenario unknown

Both commands should exit with a nonzero status.

## Run tests

From the repository root:

    python3 -m unittest discover -s 05-advanced-prompts/applied-labs/r40-t013 -p "test_example.py" -v

The tests compare both approaches, check expected outputs, verify invalid inputs are rejected, and confirm that a deliberately incorrect expected result fails.

## Scope and limitations

This is a local template-rendering simulation using fixed fixtures. It does not call an API or an AI model.

Separating template instructions from supplied values and treating inserted braces literally helps avoid accidental reprocessing during rendering. However, template rendering alone does not prevent prompt injection or guarantee that an AI model will follow instructions safely.

