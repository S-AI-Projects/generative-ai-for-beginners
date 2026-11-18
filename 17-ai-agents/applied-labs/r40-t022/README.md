# R40-T022: Typed Tool Dispatch and Boundary Validation

## Overview

In AI Agent architectures, Large Language Models (LLMs) plan actions by producing structured tool calls (e.g., function calling schemas or Model Context Protocol [MCP] tool requests). Because LLM outputs are probabilistic and untrusted, the agent runtime must enforce defensive dispatch:
1. **Explicit Allowlist:** Restrict tool execution to verified, declared functions.
2. **Strict Schema & Type Validation:** Check parameter presence and types before invoking tool handlers.
3. **Structured Error Envelopes:** Return uniform machine-readable JSON status envelopes for both successes and validation errors.
4. **Failure Isolation:** Ensure that a failed call immediately halts execution and cannot trigger subsequent tools.

This lab demonstrates these concepts using a lightweight, local contract fixture implemented in Python's standard library.

## Requirements & Scope

- **Runtime:** Python 3.9+
- **Dependencies:** Python standard library only (`argparse`, `json`, `math`, `sys`, `unittest`)
- **Infrastructure:** No model downloads, GPU, cloud subscriptions, or external API keys required.
- **Contract Fixture vs. Full Transport:** This lab is a local contract fixture demonstrating validation and dispatch semantics. It is **not** a full MCP transport implementation (it does not implement JSON-RPC 2.0 message framing, stdio/SSE socket transports, or agent session negotiation).

## Local Contract & Behavior

### 1. Declared Tools in Allowlist

| Tool | Parameters | Description | Example Input | Expected Output |
|---|---|---|---|---|
| `add` | `a` (number), `b` (number) | Calculates arithmetic sum | `{"a": 2, "b": 3}` | `5` |
| `multiply` | `a` (number), `b` (number) | Calculates arithmetic product | `{"a": 2, "b": 3}` | `6` |

Any tool not in `["add", "multiply"]` is rejected with `UnknownToolError` (`TOOL_NOT_ALLOWED`).

### 2. Boundary Decisions & Rationale

| Case Category | Example Input | Behavior | Rationale & Boundary Decision |
|---|---|---|---|
| **Smallest Valid Integers** | `add(0, 0)`, `multiply(0, 10)` | Returns `0` | `0` is a valid identity element and boundary integer. |
| **Negative Numbers** | `add(-1, 1)`, `multiply(-2, 3)` | Returns `0`, `-6` | Signed values are valid finite arithmetic operands. |
| **Floating Point Values** | `add(0.25, 0.75)`, `multiply(2.5, 4.0)` | Returns `1.0`, `10.0` | Fractional numbers are supported and preserved. |
| **Booleans (`bool`)** | `add(True, 3)`, `add(2, False)` | Rejected (`INVALID_ARGUMENT_TYPE`) | In Python, `isinstance(True, int)` is `True`. However, in JSON and tool schemas, boolean is a distinct primitive (`true`/`false`). Coercing boolean to numeric `1`/`0` is unsafe in agent tool dispatch. |
| **Numeric Strings** | `add("2", 3)` | Rejected (`INVALID_ARGUMENT_TYPE`) | LLMs occasionally emit stringified numbers (`"2"`). Automatic coercion masks model schema drift. Strict typing requires numbers to be JSON numeric types. |
| **Non-Finite Floats** | `add(float('nan'), 3)`, `multiply(float('inf'), 2)` | Rejected (`NON_FINITE_NUMERIC_VALUE`) | Standard JSON (RFC 8259) prohibits `NaN` and `Infinity`. Non-finite numbers violate discrete arithmetic contracts. |
| **Missing Parameters** | `{"tool": "add", "arguments": {"a": 2}}` | Rejected (`MISSING_ARGUMENT`) | Missing `b` cannot be defaulted unless explicitly configured. |
| **Unexpected Parameters** | `{"tool": "add", "arguments": {"a": 2, "b": 3, "c": 4}}` | Rejected (`UNEXPECTED_ARGUMENT`) | Extraneous keys indicate malformed tool proposals. |
| **Pipeline Failure Halting** | `[{"tool": "add", "arguments": {"a": "bad", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]` | Halted immediately; `multiply` aborted | A failed call cannot execute another tool. If a tool fails validation or execution, all subsequent calls are aborted. |

## Running the Lab

### 1. Normal Scenarios

#### Addition: `add(2, 3) -> 5`

```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
```

Output:

```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 5
}
```

Exit code: `0`

#### Multiplication: `multiply(2, 3) -> 6`

```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'
```

Output:

```json
{
  "status": "success",
  "tool": "multiply",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 6
}
```

Exit code: `0`

---

### 2. Failure Scenarios

#### Unknown Tool

```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'
```

Output:

```json
{
  "status": "error",
  "error": {
    "type": "UnknownToolError",
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
    "details": {
      "tool": "divide",
      "allowed_tools": [
        "add",
        "multiply"
      ]
    }
  },
  "tool": "divide",
  "arguments": {
    "a": 6,
    "b": 2
  }
}
```

Exit code: `1`

#### String Argument `a`

```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": "2", "b": 3}}'
```

Output:

```json
{
  "status": "error",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_ARGUMENT_TYPE",
    "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
    "details": {
      "parameter": "a",
      "expected": "number (int or float)",
      "received_type": "str",
      "received_value": "2"
    }
  },
  "tool": "add",
  "arguments": {
    "a": "2",
    "b": 3
  }
}
```

Exit code: `1`

---

### 3. Execution Halting / Failure Isolation

To verify that a failed call cannot execute another tool in a sequence:

```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --pipeline '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
```

Output:

```json
{
  "status": "error",
  "pipeline_halted": true,
  "failed_step_index": 0,
  "completed_steps": 0,
  "total_steps": 2,
  "executed_results": [],
  "failed_call": {
    "status": "error",
    "error": {
      "type": "ValidationError",
      "code": "INVALID_ARGUMENT_TYPE",
      "message": "Argument 'a' must be a finite number (int or float), got str: \"invalid\"",
      "details": {
        "parameter": "a",
        "expected": "number (int or float)",
        "received_type": "str",
        "received_value": "invalid"
      }
    },
    "tool": "add",
    "arguments": {
      "a": "invalid",
      "b": 3
    }
  },
  "aborted_calls": [
    {
      "tool": "multiply",
      "arguments": {
        "a": 2,
        "b": 3
      }
    }
  ],
  "message": "Pipeline halted: a failed call cannot execute another tool."
}
```

Exit code: `1`

---

## Running Unit Tests

Run the automated test suite from the repository root:

```bash
python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t022 -p "test_*.py" -v
```

All 29 tests execute in memory with zero external dependencies and report `OK`.
