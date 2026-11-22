# R40-T005 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T005.

## 1. Normal Scenario (Valid Config with Redacted Output)
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "CONFIG_VALID_REDACTED_SUMMARY",
  "summary": {
    "status": "VALID_MOCK_LAUNCH_PREPARED",
    "process_launched": false,
    "command": "uvicorn",
    "argument_count": 5,
    "arguments": [
      "app.main:app",
      "--host",
      "0.0.0.0",
      "--port",
      "8000"
    ],
    "environment_keys": [
      "DATABASE_URL",
      "MODEL_NAME",
      "OPENAI_API_KEY"
    ],
    "redacted_environment": {
      "OPENAI_API_KEY": "[REDACTED]",
      "MODEL_NAME": "[REDACTED]",
      "DATABASE_URL": "[REDACTED]"
    },
    "unestablished_real_behaviors": [
      "TCP port availability and bind collisions (EADDRINUSE)",
      "Operating system binary presence in PATH and execution permissions",
      "Hardware GPU memory allocation (CUDA OOM / VRAM limits)",
      "Network latency, DNS resolution, and remote API endpoint health",
      "OS signal handling (SIGTERM/SIGKILL) and multi-process lifecycle management"
    ]
  },
  "all_redacted": true,
  "process_launched": false,
  "contract_satisfied": true
}
```

## 2. Missing Command Failure Scenario
```json
{
  "scenario_id": "SCENARIO_MISSING_COMMAND",
  "decision": "MISSING_COMMAND_REJECTED",
  "validation_failed": true,
  "error_message": "Missing or empty required 'command' field.",
  "contract_satisfied": true
}
```

## 3. String Arguments Failure Scenario
```json
{
  "scenario_id": "SCENARIO_STRING_ARGS",
  "decision": "STRING_ARGS_REJECTED",
  "validation_failed": true,
  "error_message": "A single string was provided where an argument array is required.",
  "contract_satisfied": true
}
```

## 4. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'CONFIG_VALID_REDACTED_SUMMARY', 'passed': False}]",
  "exit_code": 1
}
```

## 5. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_missing_cmd (test_example.TestCLIExecution.test_cli_scenario_missing_cmd) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_string_args (test_example.TestCLIExecution.test_cli_scenario_string_args) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_missing_command_fails (test_example.TestConfigValidationContract.test_missing_command_fails)
Missing or empty command raises ConfigurationValidationError. ... ok
test_non_list_arguments_fails (test_example.TestConfigValidationContract.test_non_list_arguments_fails)
Non-list arguments field raises ConfigurationValidationError. ... ok
test_single_string_arguments_fails (test_example.TestConfigValidationContract.test_single_string_arguments_fails)
Single string where argument array is required raises ConfigurationValidationError. ... ok
test_valid_config_produces_redacted_summary_without_process (test_example.TestConfigValidationContract.test_valid_config_produces_redacted_summary_without_process)
Valid configuration produces redacted summary and does not spawn process. ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_callable_adapter_interface (test_example.TestFocusCallableInterfaceAndLimitations.test_callable_adapter_interface)
OfflineServiceAdapter is callable and conforms to adapter protocol. ... ok
test_unestablished_real_behaviors_documented (test_example.TestFocusCallableInterfaceAndLimitations.test_unestablished_real_behaviors_documented)
Adapter explicitly documents unestablished real-service behaviors. ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.137s

OK

```
