# R40-T023 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T023.

---

## 1. Normal Scenario (AllenAI OLMo Exemplar)

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario normal
```

Expected Decision: `OPEN_SOURCE`

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 1,
  "passed_scenarios": 1,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "model_id": "allenai-olmo-7b-fixture",
      "expected_decision": "OPEN_SOURCE",
      "direct_decision": "OPEN_SOURCE",
      "independent_decision": "OPEN_SOURCE",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Model 'allenai-olmo-7b-fixture' fully aligns with the traditional definition of open source defined in Lesson 16 (exemplified by AllenAI OLMo). All six critical artifacts\u2014training datasets, model weights, evaluation code, fine-tuning code, training metrics, and an OSI-approved license\u2014are fully public and accessible without proprietary restrictions."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Meets all 5 lesson criteria plus OSI license. Direct rule engine and independent calculation agree.

---

## 2. Boundary Scenario (Llama 2 / Mistral Exemplar)

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario boundary
```

Expected Decision: `OPEN_WEIGHTS`

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 1,
  "passed_scenarios": 1,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "model_id": "llama-2-chat-fixture",
      "expected_decision": "OPEN_WEIGHTS",
      "direct_decision": "OPEN_WEIGHTS",
      "independent_decision": "OPEN_WEIGHTS",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Model 'llama-2-chat-fixture' provides public model weights for inference and local adaptation, but key pre-training artifacts remain withheld: ['osi_approved_license', 'training_datasets_public', 'training_metrics_public']. Under the Lesson 16 framework, this falls on the boundary: it is classified as an 'open model' or 'open weights' model (similar to Llama 2 or Mistral), rather than traditional open source."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Weights and fine-tuning are public, but training data and metrics are withheld. Correctly categorized as an open model / open weights boundary.

---

## 3. Missing Information Scenario (Unverified Disclosures)

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario missing_info
```

Expected Decision: `UNDETERMINED`

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 1,
  "passed_scenarios": 1,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_MISSING_INFO",
      "scenario_type": "missing_information",
      "model_id": "unverified-candidate-v1",
      "expected_decision": "UNDETERMINED",
      "direct_decision": "UNDETERMINED",
      "independent_decision": "UNDETERMINED",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Cannot determine classification for model 'unverified-candidate-v1' because 4 essential transparency criteria are missing or unverified: ['fine_tuning_code_public', 'osi_approved_license', 'training_datasets_public', 'training_metrics_public'], leaving the status undetermined. As stated in Lesson 16, a rigorous openness assessment requires verified public disclosure of training datasets, weights, code, and metrics before classifying a model."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Required transparency criteria are `None`, appropriately yielding `UNDETERMINED` across both approaches.

---

## 4. Full Decision Table Comparison Checker

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --check
```

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 3,
  "passed_scenarios": 3,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "model_id": "allenai-olmo-7b-fixture",
      "expected_decision": "OPEN_SOURCE",
      "direct_decision": "OPEN_SOURCE",
      "independent_decision": "OPEN_SOURCE",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Model 'allenai-olmo-7b-fixture' fully aligns with the traditional definition of open source defined in Lesson 16 (exemplified by AllenAI OLMo). All six critical artifacts\u2014training datasets, model weights, evaluation code, fine-tuning code, training metrics, and an OSI-approved license\u2014are fully public and accessible without proprietary restrictions."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "model_id": "llama-2-chat-fixture",
      "expected_decision": "OPEN_WEIGHTS",
      "direct_decision": "OPEN_WEIGHTS",
      "independent_decision": "OPEN_WEIGHTS",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Model 'llama-2-chat-fixture' provides public model weights for inference and local adaptation, but key pre-training artifacts remain withheld: ['osi_approved_license', 'training_datasets_public', 'training_metrics_public']. Under the Lesson 16 framework, this falls on the boundary: it is classified as an 'open model' or 'open weights' model (similar to Llama 2 or Mistral), rather than traditional open source."
    },
    {
      "scenario_id": "SCENARIO_MISSING_INFO",
      "scenario_type": "missing_information",
      "model_id": "unverified-candidate-v1",
      "expected_decision": "UNDETERMINED",
      "direct_decision": "UNDETERMINED",
      "independent_decision": "UNDETERMINED",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "status": "PASS",
      "rationale": "Cannot determine classification for model 'unverified-candidate-v1' because 4 essential transparency criteria are missing or unverified: ['fine_tuning_code_public', 'osi_approved_license', 'training_datasets_public', 'training_metrics_public'], leaving the status undetermined. As stated in Lesson 16, a rigorous openness assessment requires verified public disclosure of training datasets, weights, code, and metrics before classifying a model."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 3 scenarios verified; Approach 1 (direct engine) and Approach 2 (independent baseline) agree across every scenario.

---

## 5. Custom JSON Payload Evaluation

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --call '{"model_id": "custom-eval-model", "facts": {"model_weights_public": true, "training_datasets_public": true, "evaluation_code_public": true, "fine_tuning_code_public": true, "training_metrics_public": true, "osi_approved_license": true}}'
```

Actual Output:
```json
{
  "direct_evaluation": {
    "status": "success",
    "approach": "direct_rule_engine",
    "model_id": "custom-eval-model",
    "decision": "OPEN_SOURCE",
    "decision_code": "DECISION_OPEN_SOURCE",
    "rationale": "Model 'custom-eval-model' fully aligns with the traditional definition of open source defined in Lesson 16 (exemplified by AllenAI OLMo). All six critical artifacts\u2014training datasets, model weights, evaluation code, fine-tuning code, training metrics, and an OSI-approved license\u2014are fully public and accessible without proprietary restrictions.",
    "criteria_summary": {
      "total_required": 6,
      "satisfied_count": 6,
      "withheld_count": 0,
      "missing_count": 0,
      "satisfied": [
        "model_weights_public",
        "training_datasets_public",
        "evaluation_code_public",
        "fine_tuning_code_public",
        "training_metrics_public",
        "osi_approved_license"
      ],
      "withheld": [],
      "missing": []
    },
    "raw_facts": {
      "model_weights_public": true,
      "training_datasets_public": true,
      "evaluation_code_public": true,
      "fine_tuning_code_public": true,
      "training_metrics_public": true,
      "osi_approved_license": true
    }
  },
  "independent_decision": "OPEN_SOURCE",
  "approaches_agree": true
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Custom JSON payload processed cleanly by both approaches.

---

## 6. Deliberate Tamper Test Verification

Command:
```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --tamper-test
```

Actual Stderr:
```text
Executing deliberate failure verification: Tampering SCENARIO_NORMAL expected_decision to 'OPEN_WEIGHTS'...
DecisionMismatchError: Decision check failed for 'SCENARIO_NORMAL'. Expected='OPEN_WEIGHTS', Direct='OPEN_SOURCE', Independent='OPEN_SOURCE'. Keyword mismatches: []
```

Exit code: `1` (Expected non-zero: `1`)

**Result:** PASS — Deliberately changing a decision in the table triggers `DecisionMismatchError` and exits with code 1.

---

## 7. Automated Unit Test Discovery

Command:
```bash
python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t023 -p "test_*.py" -v
```

Test Output:
```text
test_deliberate_wrong_result_fails (test_example.TestDeliberateFailureVerification.test_deliberate_wrong_result_fails) ... ok
test_boundary_only_license_non_osi_yields_open_weights (test_example.TestDirectEvaluationEngine.test_boundary_only_license_non_osi_yields_open_weights)
If all artifacts are public but license is non-OSI (e.g. custom commercial cap), it's OPEN_WEIGHTS. ... ok
test_boundary_proprietary_closed_model (test_example.TestDirectEvaluationEngine.test_boundary_proprietary_closed_model)
If model weights are private (API-only), model is PROPRIETARY. ... ok
test_boundary_scenario_open_weights (test_example.TestDirectEvaluationEngine.test_boundary_scenario_open_weights)
Model with public weights but withheld pre-training data and metrics must be OPEN_WEIGHTS. ... ok
test_boundary_single_missing_field_triggers_undetermined (test_example.TestDirectEvaluationEngine.test_boundary_single_missing_field_triggers_undetermined)
Even if 5 criteria are True, a single None field must trigger UNDETERMINED. ... ok
test_invalid_facts_type_raises_type_error (test_example.TestDirectEvaluationEngine.test_invalid_facts_type_raises_type_error)
Non-dictionary input must raise TypeError. ... ok
test_missing_information_scenario_undetermined (test_example.TestDirectEvaluationEngine.test_missing_information_scenario_undetermined)
Model with null/unverified fields must result in UNDETERMINED. ... ok
test_normal_scenario_open_source (test_example.TestDirectEvaluationEngine.test_normal_scenario_open_source)
Fully disclosed model with all 5 lesson criteria + OSI license must be OPEN_SOURCE. ... ok
test_approaches_perfectly_agree_across_fixtures (test_example.TestIndependentCalculationBaseline.test_approaches_perfectly_agree_across_fixtures)
Verifies that Approach 1 and Approach 2 produce identical decisions on identical inputs. ... ok
test_independent_boundary_scenario (test_example.TestIndependentCalculationBaseline.test_independent_boundary_scenario) ... ok
test_independent_missing_info_scenario (test_example.TestIndependentCalculationBaseline.test_independent_missing_info_scenario) ... ok
test_independent_normal_scenario (test_example.TestIndependentCalculationBaseline.test_independent_normal_scenario) ... ok
test_checker_fails_when_boundary_decision_deliberately_changed (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_boundary_decision_deliberately_changed)
Tampering with boundary scenario decision must raise DecisionMismatchError. ... ok
test_checker_fails_when_decision_deliberately_changed (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_decision_deliberately_changed)
Tampering with a decision in the table must raise DecisionMismatchError. ... ok
test_checker_fails_when_missing_info_decision_deliberately_changed (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_missing_info_decision_deliberately_changed)
Tampering with missing_info scenario decision must raise DecisionMismatchError. ... ok
test_checker_passes_on_canonical_table (test_example.TestPublishedDecisionTableAndChecker.test_checker_passes_on_canonical_table)
The untouched published decision table must pass all checks. ... ok
test_checker_soft_failure_reporting (test_example.TestPublishedDecisionTableAndChecker.test_checker_soft_failure_reporting)
When fail_on_tamper=False, checker returns a report with all_passed=False instead of raising. ... ok
test_cli_custom_call_payload (test_example.TestSubprocessCLIExecution.test_cli_custom_call_payload) ... ok
test_cli_default_check_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_default_check_exit_0) ... ok
test_cli_scenario_boundary_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_boundary_exit_0) ... ok
test_cli_scenario_missing_info_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_missing_info_exit_0) ... ok
test_cli_scenario_normal_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_normal_exit_0) ... ok
test_cli_tamper_test_exit_1 (test_example.TestSubprocessCLIExecution.test_cli_tamper_test_exit_1)
The CLI --tamper-test flag must exit nonzero with DecisionMismatchError. ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.126s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 23 unit and CLI tests passed.

---

## 8. Deliberate Wrong Assertion Verification

Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.

Command:
```bash
python3 -c "import subprocess, sys, json; res = subprocess.run([sys.executable, '16-open-source-models/applied-labs/r40-t023/example.py', '--scenario', 'normal'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['scenarios'][0]['direct_decision'] == 'FORCED_WRONG_DECISION'"
```

Actual Output:
```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import subprocess, sys, json; res = subprocess.run([sys.executable, '16-open-source-models/applied-labs/r40-t023/example.py', '--scenario', 'normal'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['scenarios'][0]['direct_decision'] == 'FORCED_WRONG_DECISION', 'Deliberate test failure: expected FORCED_WRONG_DECISION'
                                                                                                                                                                                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Deliberate test failure: expected FORCED_WRONG_DECISION
```

Exit code: `1` (Expected non-zero: `1`)

**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.

---

## Summary

| Check ID | Description | Status | Exit Code |
|---|---|---|---|
| 1 | Normal Scenario (`AllenAI OLMo -> OPEN_SOURCE`) | PASS | 0 |
| 2 | Boundary Scenario (`Llama 2 / Mistral -> OPEN_WEIGHTS`) | PASS | 0 |
| 3 | Missing Information Scenario (`Unverified -> UNDETERMINED`) | PASS | 0 |
| 4 | Full Decision Table Comparison Checker | PASS | 0 |
| 5 | Custom JSON Payload Evaluation | PASS | 0 |
| 6 | Deliberate Tamper Test Detection | PASS | 1 (Expected Nonzero) |
| 7 | Automated Unit Test Suite (23 tests) | PASS | 0 |
| 8 | Deliberate Wrong Assertion Verification | PASS | 1 (Expected Nonzero) |

All checks passed successfully.
