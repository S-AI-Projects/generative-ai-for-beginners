# Applied Lab R40-T009: Typed Tool Dispatch & Evaluation Experiment

## Overview

This lab extends [Lesson 17: AI Agents](../../README.md) by implementing a typed tool dispatcher for agentic function calling, enforcing strict tool allowlists, validating JSON argument types, returning structured error objects, and preventing unsafe tool execution cascades upon failure.

## Contract & Tool Allowlist

1. **Explicit Allowlist**: Only `add` and `multiply` are permissible tools.
2. **Deterministic Arithmetic**:
   - `add(2, 3)` -> `5`
   - `multiply(2, 3)` -> `6`
3. **Structured Errors**:
   - Unknown tools (e.g. `subtract`) return `{"status": "error", "error_type": "UnknownToolError", ...}`.
   - Non-numeric inputs (e.g. string `a` in `add("two", 3)`) return `{"status": "error", "error_type": "TypeValidationError", ...}`.
4. **Cascade Abort Invariant**: In a planned sequence of tool calls, a failed call immediately halts execution; subsequent tools are blocked from executing.

## Focus: Three Controlled Configurations Evaluation

The lab benchmarks three controlled dispatch modes on identical payloads:
1. **`FAIL_FAST`**: Terminates execution immediately upon encountering an invalid tool or type error, minimizing latency.
2. **`PRE_VALIDATE`**: Validates all tool payloads upfront before invoking any tool.
3. **`AUDIT_LOGGED`**: Traps all calls in an isolated runner with structured step-by-step diagnostic audit logging.

All three modes achieve 100% boundary safety (0 unallowlisted or ill-typed tool executions).

## Scope Note (Simulation / Test Double)

This component is an offline tool dispatch test double using only Python's standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Normal tool execution
python3 17-ai-agents/applied-labs/r40-t009/example.py --scenario normal

# Unknown tool rejection
python3 17-ai-agents/applied-labs/r40-t009/example.py --scenario unknown

# String argument rejection
python3 17-ai-agents/applied-labs/r40-t009/example.py --scenario string_type

# Cascade abort prevention
python3 17-ai-agents/applied-labs/r40-t009/example.py --scenario cascade

# Run 3-configuration evaluation experiment
python3 17-ai-agents/applied-labs/r40-t009/example.py --experiment

# Canonical check
python3 17-ai-agents/applied-labs/r40-t009/example.py --check

# Automated unit tests
python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t009 -p "test_*.py" -v
```
