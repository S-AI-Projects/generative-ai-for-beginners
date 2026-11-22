# R40-T012: Educational Startup Prompt-Readiness Example

## Purpose

This local example checks whether an educational prompt contains enough information.

## Required fields
- learner_level
- topic
- learning_goal

output_format is optional.

## Scenarios

| Scenario | Expected decision |
|---|---|
| Normal | ready |
| Boundary | minimum_ready |
| Missing | cannot_determine |
| Invalid | invalid |

The boundary case is the smallest valid prompt: all three required fields are present, but the optional output format is absent.

## Run all scenarios

    python3 01-introduction-to-genai/applied-labs/r40-t012/example.py

## Run checker

    python3 01-introduction-to-genai/applied-labs/r40-t012/example.py --check

## Run tests

    python3 -m unittest discover -s 01-introduction-to-genai/applied-labs/r40-t012 -p "test_*.py"

## Limitations

This is a local mock simulation. It does not call an LLM or guarantee the quality or accuracy of generated educational content.
