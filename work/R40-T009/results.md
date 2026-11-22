# R40-T009 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T009.

## 1. Normal Scenario (add(2,3)->5, multiply(2,3)->6)
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "TOOLS_DISPATCHED_SUCCESSFULLY",
  "add_result": 5,
  "multiply_result": 6,
  "batch_status": "all_succeeded",
  "contract_satisfied": true
}
```

## 2. Unknown Tool Rejection Scenario
```json
{
  "scenario_id": "SCENARIO_UNKNOWN_TOOL",
  "decision": "UNKNOWN_TOOL_REJECTED",
  "response": {
    "status": "error",
    "error_type": "UnknownToolError",
    "tool": "subtract",
    "message": "Tool 'subtract' is not in allowlist: ['add', 'multiply']."
  },
  "contract_satisfied": true
}
```

## 3. String Type Rejection Scenario
```json
{
  "scenario_id": "SCENARIO_STRING_TYPE",
  "decision": "STRING_ARG_REJECTED",
  "response": {
    "status": "error",
    "error_type": "TypeValidationError",
    "tool": "add",
    "field": "a",
    "invalid_value": "two",
    "message": "Argument 'a' must be numeric, got str."
  },
  "contract_satisfied": true
}
```

## 4. Cascade Prevention Scenario
```json
{
  "scenario_id": "SCENARIO_CASCADE_PREVENTION",
  "decision": "CASCADE_EXECUTION_BLOCKED",
  "halted": true,
  "executed_count": 0,
  "contract_satisfied": true
}
```

## 5. Three Controlled Configurations Evaluation Output
```json
{
  "experiment_name": "three_controlled_configurations",
  "metric": "execution_isolation_and_overhead",
  "configurations": {
    "fail_fast": {
      "mode": "fail_fast",
      "elapsed_us": 6.21,
      "status": "completed_with_halts",
      "executed_count": 1,
      "unauthorized_executed": 0,
      "boundary_safety": "100%"
    },
    "pre_validate": {
      "mode": "pre_validate",
      "elapsed_us": 3.79,
      "status": "batch_aborted_prevalidation",
      "executed_count": 0,
      "unauthorized_executed": 0,
      "boundary_safety": "100%"
    },
    "audit_logged": {
      "mode": "audit_logged",
      "elapsed_us": 3.13,
      "status": "completed_with_halts",
      "executed_count": 1,
      "unauthorized_executed": 0,
      "boundary_safety": "100%"
    }
  },
  "trade_off_summary": "FAIL_FAST yields lowest latency with immediate abort; PRE_VALIDATE protects all downstream calls at the expense of pre-pass checking; AUDIT_LOGGED delivers full observability with complete step logs.",
  "contract_satisfied": true
}
```

## 6. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'TOOLS_DISPATCHED_SUCCESSFULLY', 'passed': False}]",
  "exit_code": 1
}
```

## 7. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_experiment (test_example.TestCLIExecution.test_cli_experiment) ... ok
test_cli_scenario_cascade (test_example.TestCLIExecution.test_cli_scenario_cascade) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_string_type (test_example.TestCLIExecution.test_cli_scenario_string_type) ... ok
test_cli_scenario_unknown (test_example.TestCLIExecution.test_cli_scenario_unknown) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_evaluation_experiment_all_modes_safe (test_example.TestFocusControlledConfigurations.test_evaluation_experiment_all_modes_safe)
Verifies zero unauthorized executions across all 3 controlled modes. ... ok
test_add_two_and_three_equals_five (test_example.TestTypedToolDispatchContract.test_add_two_and_three_equals_five)
add(2, 3) -> 5. ... ok
test_failed_call_cannot_execute_another_tool (test_example.TestTypedToolDispatchContract.test_failed_call_cannot_execute_another_tool)
A failed call halts sequence execution and blocks subsequent calls. ... ok
test_multiply_two_and_three_equals_six (test_example.TestTypedToolDispatchContract.test_multiply_two_and_three_equals_six)
multiply(2, 3) -> 6. ... ok
test_string_argument_returns_structured_error (test_example.TestTypedToolDispatchContract.test_string_argument_returns_structured_error)
String argument 'a' returns structured error. ... ok
test_unknown_tool_returns_structured_error (test_example.TestTypedToolDispatchContract.test_unknown_tool_returns_structured_error)
Unknown tool returns structured error. ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.189s

OK

```
