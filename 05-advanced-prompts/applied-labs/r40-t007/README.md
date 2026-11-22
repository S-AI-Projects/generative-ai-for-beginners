# Applied Lab R40-T007: Prompt-Template Escaping & Worked Regression

## Overview

This lab extends [Lesson 05: Creating Advanced Prompts](../../README.md) by introducing a secure prompt template compiler with declared variable validation, literal brace preservation, and structural separation of system instructions from untrusted user inputs.

## Contract & Template Schema

1. **Declared Variables**: `name`, `topic`.
2. **Missing Variable Rejection**: Omitting `topic` (or `name`) raises `MissingVariableError`.
3. **Unknown Key Rejection**: Undeclared keys raise `UnknownVariableError`.
4. **Literal Brace Preservation**: Curly braces within user data (e.g. `{Hadamard, CNOT}`) are preserved literally without escaping or formatting exceptions.
5. **Structural Separation**: System instructions (`<instruction>`) are cleanly isolated from user inputs (`<user_data>`).
6. **Prompt Injection Boundary**: Templating alone guarantees structural syntax integrity, but **does not prevent semantic prompt injection**; semantic defense requires downstream model guardrails and system moderation.

## Focus: Worked Input-to-Output Regression

A fully worked example traces raw inputs through schema validation, token substitution, and tag encapsulation:
- **Input**: `{"name": "Alice {Researcher}", "topic": "Quantum Algorithms: {Hadamard, CNOT}"}`
- **Rendered Output**:
```xml
<instruction>
You are an academic mentor. Provide a detailed, pedagogical explanation tailored to the student's inquiry.
</instruction>
<user_data>
Student Name: Alice {Researcher}
Topic of Inquiry: Quantum Algorithms: {Hadamard, CNOT}
</user_data>
```
This worked example is executed as an automated regression test.

## Scope Note (Simulation / Test Double)

This component is an offline prompt template compiler implemented using only Python's standard library. It requires no LLM API calls, cloud subscriptions, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Valid template rendering
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --scenario normal

# Missing topic failure
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --scenario missing_topic

# User braces preservation
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --scenario braces

# Unknown key rejection
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --scenario unknown

# Display worked explanation
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --explain

# Canonical check
python3 05-advanced-prompts/applied-labs/r40-t007/example.py --check

# Automated unit tests
python3 -m unittest discover -s 05-advanced-prompts/applied-labs/r40-t007 -p "test_*.py" -v
```
