# R40-T022 — Test and Check Results

This document records all inputs, expected vs. actual outputs, exit codes, and verification assertions for Task R40-T022.

---

## 1. Normal Scenario: Addition (`add(2, 3) -> 5`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
```

Expected output:
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

Actual output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — Addition executed successfully with strict numeric typing.

---

## 2. Normal Scenario: Multiplication (`multiply(2, 3) -> 6`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'
```

Expected output:
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

Actual output:
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

Exit code: `0` (Expected: `0`)

**Result:** PASS — Multiplication executed successfully with strict numeric typing.

---

## 3. Failure Scenario: Unknown Tool (`divide`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'
```

Expected output:
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

Actual output:
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

Exit code: `1` (Expected: `1`)

**Result:** PASS — Unknown tool was rejected via the explicit allowlist with a structured error envelope.

---

## 4. Failure Scenario: String Argument `a` (`a = "2"`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": "2", "b": 3}}'
```

Expected output:
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

Actual output:
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

Exit code: `1` (Expected: `1`)

**Result:** PASS — Numeric string argument was rejected without implicit coercion.

---

## 5. Failure Scenario: Pipeline Halting & Tool Isolation

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --pipeline '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
```

Expected output:
```json
{
  "status": "error",
  "pipeline_halted": true,
  "failed_step_index": 0,
  "completed_steps": 0,
  "total_steps": 2,
  "executed_results": [],
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

Actual output:
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

Exit code: `1` (Expected: `1`)

**Result:** PASS — Pipeline halted immediately on the first failed call; `multiply` was aborted without execution.

---

## 6. Boundary Scenario: Smallest Valid Integers (`add(0, 0) -> 0`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": 0, "b": 0}}'
```

Actual output:
```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 0,
    "b": 0
  },
  "result": 0
}
```

Exit code: `0`

**Result:** PASS — Zero boundary handled cleanly.

---

## 7. Boundary Decision: Strict Boolean Rejection (`a = true`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": true, "b": 3}}'
```

Actual output:
```json
{
  "status": "error",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_ARGUMENT_TYPE",
    "message": "Argument 'a' must be a finite number (int or float), got bool: True",
    "details": {
      "parameter": "a",
      "expected": "number (int or float)",
      "received_type": "bool",
      "received_value": true
    }
  },
  "tool": "add",
  "arguments": {
    "a": true,
    "b": 3
  }
}
```

Exit code: `1`

**Result:** PASS — Boolean primitive rejected despite Python int subclassing.

---

## 8. Automated Unit Test Discovery

Command:
```bash
python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t022 -p "test_*.py" -v
```

Test output:
```text
test_boundary_boolean_rejection (test_example.TestArgumentValidation.test_boundary_boolean_rejection)
Boundary decision: Python booleans subclass int, but in JSON / agent payloads, ... ok
test_non_finite_float_rejection (test_example.TestArgumentValidation.test_non_finite_float_rejection)
Boundary decision: NaN, Infinity, -Infinity are not permissible in standard JSON ... ok
test_non_numeric_types_rejection (test_example.TestArgumentValidation.test_non_numeric_types_rejection)
None, lists, dicts must be rejected. ... ok
test_schema_missing_and_unexpected_arguments (test_example.TestArgumentValidation.test_schema_missing_and_unexpected_arguments) ... ok
test_string_rejection (test_example.TestArgumentValidation.test_string_rejection)
Boundary decision: Strings representing numbers (e.g. '2') must not be coerced. ... ok
test_valid_float_arguments (test_example.TestArgumentValidation.test_valid_float_arguments) ... ok
test_valid_integer_arguments (test_example.TestArgumentValidation.test_valid_integer_arguments) ... ok
test_add_boundaries (test_example.TestBasicToolFunctions.test_add_boundaries) ... ok
test_add_normal (test_example.TestBasicToolFunctions.test_add_normal) ... ok
test_multiply_boundaries (test_example.TestBasicToolFunctions.test_multiply_boundaries) ... ok
test_multiply_normal (test_example.TestBasicToolFunctions.test_multiply_normal) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateFailureVerification.test_deliberate_wrong_result_fails) ... ok
test_pipeline_halts_on_failure_blocking_subsequent_tools (test_example.TestExecutionIsolationAndHalting.test_pipeline_halts_on_failure_blocking_subsequent_tools)
Contract rule: 'a failed call cannot execute another tool.' ... ok
test_pipeline_mid_sequence_halting (test_example.TestExecutionIsolationAndHalting.test_pipeline_mid_sequence_halting)
If step 1 succeeds, step 2 fails, step 3 must be aborted. ... ok
test_single_failed_call_does_not_execute_tool (test_example.TestExecutionIsolationAndHalting.test_single_failed_call_does_not_execute_tool)
Spy on functions to ensure neither is called when validation fails. ... ok
test_add_success_envelope (test_example.TestSingleDispatchAndStructuredEnvelopes.test_add_success_envelope) ... ok
test_invalid_payload_envelope (test_example.TestSingleDispatchAndStructuredEnvelopes.test_invalid_payload_envelope) ... ok
test_multiply_success_envelope (test_example.TestSingleDispatchAndStructuredEnvelopes.test_multiply_success_envelope) ... ok
test_string_argument_a_structured_error (test_example.TestSingleDispatchAndStructuredEnvelopes.test_string_argument_a_structured_error) ... ok
test_unknown_tool_structured_error (test_example.TestSingleDispatchAndStructuredEnvelopes.test_unknown_tool_structured_error) ... ok
test_cli_add_normal (test_example.TestSubprocessCLIExecution.test_cli_add_normal) ... ok
test_cli_flag_convenience (test_example.TestSubprocessCLIExecution.test_cli_flag_convenience) ... ok
test_cli_multiply_normal (test_example.TestSubprocessCLIExecution.test_cli_multiply_normal) ... ok
test_cli_pipeline_halting_exit_code_1 (test_example.TestSubprocessCLIExecution.test_cli_pipeline_halting_exit_code_1) ... ok
test_cli_stdin_support (test_example.TestSubprocessCLIExecution.test_cli_stdin_support) ... ok
test_cli_string_argument_exit_code_1 (test_example.TestSubprocessCLIExecution.test_cli_string_argument_exit_code_1) ... ok
test_cli_unknown_tool_exit_code_1 (test_example.TestSubprocessCLIExecution.test_cli_unknown_tool_exit_code_1) ... ok
test_allowed_tools_pass (test_example.TestToolAllowlist.test_allowed_tools_pass) ... ok
test_unknown_tools_raise_unknown_tool_error (test_example.TestToolAllowlist.test_unknown_tools_raise_unknown_tool_error) ... ok

----------------------------------------------------------------------
Ran 29 tests in 0.184s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 29 unit and integration tests passed.

---

## 9. Deliberate Failure Verification

Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.

Command:
```bash
python3 -c "import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t022/example.py', '--call', '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure for assertion verification'"
```

Output:
```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t022/example.py', '--call', '{"tool": "add", "arguments": {"a": 2, "b": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure: expected 999 got ' + str(data['result'])
                                                                                                                                                                                                                                                             ^^^^^^^^^^^^^^^^^^^^^
AssertionError: Deliberate test failure: expected 999 got 5
```

Exit code: `1` (Expected non-zero: `1`)

**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.

---

## Summary

| Check ID | Description | Status | Exit Code |
|---|---|---|---|
| 1 | Normal Addition (`add(2, 3) -> 5`) | PASS | 0 |
| 2 | Normal Multiplication (`multiply(2, 3) -> 6`) | PASS | 0 |
| 3 | Unknown Tool Error (`divide`) | PASS | 1 |
| 4 | String Argument Error (`a = "2"`) | PASS | 1 |
| 5 | Pipeline Halting & Tool Isolation | PASS | 1 |
| 6 | Boundary Integers (`0, 0`) | PASS | 0 |
| 7 | Boundary Decision on Booleans | PASS | 1 |
| 8 | Automated Test Suite (29 tests) | PASS | 0 |
| 9 | Deliberate Failure Verification | PASS | 1 (Expected Nonzero) |

All checks passed successfully.
