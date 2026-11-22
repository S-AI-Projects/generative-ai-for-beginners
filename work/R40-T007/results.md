# R40-T007 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T007.

## 1. Normal Scenario
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "TEMPLATE_RENDERED_SUCCESS",
  "inputs": {
    "name": "Alice",
    "topic": "Quantum Computing"
  },
  "rendered_prompt": "<instruction>\nYou are an academic mentor. Provide a detailed, pedagogical explanation tailored to the student's inquiry.\n</instruction>\n<user_data>\nStudent Name: Alice\nTopic of Inquiry: Quantum Computing\n</user_data>",
  "contains_name": true,
  "contains_topic": true,
  "contract_satisfied": true
}
```

## 2. Missing Topic Scenario
```json
{
  "scenario_id": "SCENARIO_MISSING_TOPIC",
  "decision": "MISSING_TOPIC_REJECTED",
  "missing_variable_caught": true,
  "error_message": "Missing required variable(s): ['topic'].",
  "contract_satisfied": true
}
```

## 3. Literal Braces Boundary Scenario
```json
{
  "scenario_id": "SCENARIO_BRACES_PRESERVED",
  "decision": "LITERAL_BRACES_PRESERVED",
  "inputs": {
    "name": "Charlie {Eng}",
    "topic": "Configuration: {debug: true, flags: [1, 2]}"
  },
  "rendered_prompt": "<instruction>\nYou are an academic mentor. Provide a detailed, pedagogical explanation tailored to the student's inquiry.\n</instruction>\n<user_data>\nStudent Name: Charlie {Eng}\nTopic of Inquiry: Configuration: {debug: true, flags: [1, 2]}\n</user_data>",
  "braces_intact": true,
  "contract_satisfied": true
}
```

## 4. Unknown Key Scenario
```json
{
  "scenario_id": "SCENARIO_UNKNOWN_KEY",
  "decision": "UNKNOWN_KEY_REJECTED",
  "unknown_key_caught": true,
  "error_message": "Unknown variable(s) provided: ['extra_token']. Allowed variables: ['name', 'topic'].",
  "contract_satisfied": true
}
```

## 5. Worked Explanation Regression Output
```json
{
  "stage_1_inputs": {
    "name": "Alice {Researcher}",
    "topic": "Quantum Algorithms: {Hadamard, CNOT}"
  },
  "stage_2_schema_validation": {
    "declared_keys": [
      "name",
      "topic"
    ],
    "supplied_keys": [
      "name",
      "topic"
    ],
    "missing_keys": [],
    "unknown_keys": [],
    "status": "VALID"
  },
  "stage_3_brace_handling": {
    "user_data_contains_braces": true,
    "name_braces": "{Researcher}",
    "topic_braces": "{Hadamard, CNOT}",
    "strategy": "Direct substring replacement bypassing str.format / f-string parser",
    "literal_preserved": true
  },
  "stage_4_structural_separation": {
    "instruction_block": "<instruction>\nYou are an academic mentor. Provide a detailed, pedagogical explanation tailored to the student's inquiry.\n</instruction>",
    "user_data_block": "<user_data>\nStudent Name: Alice {Researcher}\nTopic of Inquiry: Quantum Algorithms: {Hadamard, CNOT}\n</user_data>"
  },
  "stage_5_final_output": "<instruction>\nYou are an academic mentor. Provide a detailed, pedagogical explanation tailored to the student's inquiry.\n</instruction>\n<user_data>\nStudent Name: Alice {Researcher}\nTopic of Inquiry: Quantum Algorithms: {Hadamard, CNOT}\n</user_data>",
  "prompt_injection_boundary_note": "Delimiting user data prevents template syntax corruption, but downstream semantic defense requires LLM moderation and guardrails."
}
```

## 6. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'TEMPLATE_RENDERED_SUCCESS', 'passed': False}]",
  "exit_code": 1
}
```

## 7. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_explain (test_example.TestCLIExecution.test_cli_explain) ... ok
test_cli_scenario_braces (test_example.TestCLIExecution.test_cli_scenario_braces) ... ok
test_cli_scenario_missing_topic (test_example.TestCLIExecution.test_cli_scenario_missing_topic) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_unknown (test_example.TestCLIExecution.test_cli_scenario_unknown) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_prompt_injection_boundary_acknowledged (test_example.TestFocusWorkedRegression.test_prompt_injection_boundary_acknowledged)
Adversarial prompt text is safely wrapped in data tags without preventing semantic injection. ... ok
test_worked_input_to_output_regression (test_example.TestFocusWorkedRegression.test_worked_input_to_output_regression)
Exact worked explanation inputs match expected outputs verbatim. ... ok
test_braces_inside_user_data_remain_literal (test_example.TestPromptTemplateContract.test_braces_inside_user_data_remain_literal)
Braces inside user data remain literal and do not trigger format errors. ... ok
test_missing_name_fails (test_example.TestPromptTemplateContract.test_missing_name_fails)
Missing required name variable raises MissingVariableError. ... ok
test_missing_topic_fails (test_example.TestPromptTemplateContract.test_missing_topic_fails)
Missing required topic variable raises MissingVariableError. ... ok
test_non_string_type_fails (test_example.TestPromptTemplateContract.test_non_string_type_fails)
Non-string value raises InvalidVariableTypeError. ... ok
test_none_value_fails (test_example.TestPromptTemplateContract.test_none_value_fails)
None value raises MissingVariableError. ... ok
test_render_supplied_values (test_example.TestPromptTemplateContract.test_render_supplied_values)
Template with name and topic renders supplied values. ... ok
test_unknown_variable_fails (test_example.TestPromptTemplateContract.test_unknown_variable_fails)
Unknown variable key raises UnknownVariableError. ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.196s

OK

```
