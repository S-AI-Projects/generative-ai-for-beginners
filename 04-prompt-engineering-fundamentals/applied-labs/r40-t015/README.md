
# R40-T015: Prompt Template Escaping

## Objective

Learn how to render reusable prompt templates using declared variables, validate supplied values, and keep user data separate from fixed instructions.

## Prerequisites

- Python 3
- Python standard library only
- No API key, model download, GPU, or internet connection required

## Files

- `example.py` — template renderer and deterministic local service adapter.
- `test_example.py` — automated tests.

## Input Fixture

The normal scenario uses:

```python
{"name": "Asha", "topic": "fractions"}
```

The template contains two declared variables: `name` and `topic`.

## Run the Example

From the repository root, run:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t015/example.py
```

Expected output includes:

```text
Fixed instruction: Explain the topic 'fractions' clearly to Asha.
LOCAL MOCK RESPONSE: Fixed instruction: Explain the topic 'fractions' clearly to Asha.
```

## Boundary Scenario

Run:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t015/example.py --scenario boundary
```

The input contains braces inside user data:

```python
{"name": "Asha {admin}", "topic": "fractions {level}"}
```

Those braces remain literal text in the rendered prompt.

## Failure Scenario

Run:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t015/example.py --scenario failure
```

The missing `topic` variable is rejected with an error and a nonzero exit status.

Unknown variables are also rejected.

## Run Automated Tests

From the repository root:

```bash
python3 -m unittest discover -s 04-prompt-engineering-fundamentals/applied-labs/r40-t015 -p "test_*.py"
```

The test suite covers normal rendering, missing and unknown keys, literal braces, invalid value types, the local adapter, callable service injection, and fresh-process scenarios.

## Local Adapter and Limitations

The local adapter is deterministic. It returns a predictable mock response and does not contact an external AI service.

This lab does not establish real provider behavior, authentication, network reliability, rate limits, model responses, or provider-specific formatting.

Separating fixed instructions from user data and rendering templates correctly does not, by itself, prevent prompt injection. User-provided content can still contain instructions that influence a real model. Additional application-level safeguards and evaluation are necessary.

