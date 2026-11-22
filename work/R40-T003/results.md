# R40-T003 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T003.

## 1. Normal Scenario
```json
{
  "scenario_key": "SCENARIO_NORMAL",
  "title": "Invoice Processing Automation for Education Startup",
  "type": "normal",
  "facts": {
    "use_case": "invoice_processing",
    "prebuilt_model_available": true,
    "requires_custom_weights": false,
    "target_throughput_rps": 5,
    "data_source": "Dataverse",
    "compliance_tier": "standard_commercial",
    "delivery_window_weeks": 2
  },
  "expected_decision": "LOW_CODE_POWER_PLATFORM",
  "direct_approach": {
    "decision": "LOW_CODE_POWER_PLATFORM",
    "rationale": "Standard document processing aligns with Power Automate and AI Builder prebuilt models. Dataverse integration and 2-week delivery timeline strongly favor low-code development.",
    "approach": "direct_rule_engine"
  },
  "reference_approach": {
    "decision": "LOW_CODE_POWER_PLATFORM",
    "rationale": "Standard document processing aligns with Power Automate and AI Builder prebuilt models. Dataverse integration and 2-week delivery timeline strongly favor low-code development.",
    "approach": "reference_matrix_lookup"
  },
  "dual_approach_match": true,
  "decision": "LOW_CODE_POWER_PLATFORM",
  "rationale": "Standard document processing aligns with Power Automate and AI Builder prebuilt models. Dataverse integration and 2-week delivery timeline strongly favor low-code development.",
  "contract_satisfied": true
}
```

## 2. Boundary Scenario
```json
{
  "scenario_key": "SCENARIO_BOUNDARY",
  "title": "Ultra-Low Latency Inference with Custom Deep Learning Model",
  "type": "boundary",
  "facts": {
    "use_case": "realtime_video_defect_detection",
    "prebuilt_model_available": false,
    "requires_custom_weights": true,
    "target_throughput_rps": 15000,
    "data_source": "edge_rtsp_stream",
    "compliance_tier": "air_gapped_defense",
    "delivery_window_weeks": 24
  },
  "expected_decision": "CUSTOM_CODE_PRO_DEV",
  "direct_approach": {
    "decision": "CUSTOM_CODE_PRO_DEV",
    "rationale": "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed multi-tenant low-code platform boundaries. Requires custom containerized pro-code service.",
    "approach": "direct_rule_engine"
  },
  "reference_approach": {
    "decision": "CUSTOM_CODE_PRO_DEV",
    "rationale": "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed multi-tenant low-code platform boundaries. Requires custom containerized pro-code service.",
    "approach": "reference_matrix_lookup"
  },
  "dual_approach_match": true,
  "decision": "CUSTOM_CODE_PRO_DEV",
  "rationale": "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed multi-tenant low-code platform boundaries. Requires custom containerized pro-code service.",
  "contract_satisfied": true
}
```

## 3. Missing Information Scenario
```json
{
  "scenario_key": "SCENARIO_MISSING_INFO",
  "title": "Underspecified Customer Feedback Sentiment Classifier",
  "type": "missing_information",
  "facts": {
    "use_case": "feedback_analysis",
    "prebuilt_model_available": true,
    "requires_custom_weights": false,
    "target_throughput_rps": null,
    "data_source": null,
    "compliance_tier": null,
    "delivery_window_weeks": 4
  },
  "expected_decision": "DEFER_INSUFFICIENT_INFORMATION",
  "direct_approach": {
    "decision": "DEFER_INSUFFICIENT_INFORMATION",
    "rationale": "Critical architectural specifications (target throughput, data source, compliance requirements) are missing. Decision must be deferred until additional discovery is conducted.",
    "approach": "direct_rule_engine"
  },
  "reference_approach": {
    "decision": "DEFER_INSUFFICIENT_INFORMATION",
    "rationale": "Critical architectural specifications (target throughput, data source, compliance requirements) are missing. Decision must be deferred until additional discovery is conducted.",
    "approach": "reference_matrix_lookup"
  },
  "dual_approach_match": true,
  "decision": "DEFER_INSUFFICIENT_INFORMATION",
  "rationale": "Critical architectural specifications (target throughput, data source, compliance requirements) are missing. Decision must be deferred until additional discovery is conducted.",
  "contract_satisfied": true
}
```

## 4. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_key': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'LOW_CODE_POWER_PLATFORM', 'dual_approach_match': True, 'passed': False}]",
  "exit_code": 1
}
```

## 5. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_boundary (test_example.TestCLIExecution.test_cli_scenario_boundary) ... ok
test_cli_scenario_missing (test_example.TestCLIExecution.test_cli_scenario_missing) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_all_scenarios_dual_approach_parity (test_example.TestDualApproachEquivalence.test_all_scenarios_dual_approach_parity)
Both direct and reference approaches yield 100% equivalent decisions and rationales. ... ok
test_arbitrary_custom_weights_boundary (test_example.TestDualApproachEquivalence.test_arbitrary_custom_weights_boundary)
Custom weights requirement triggers CUSTOM_CODE_PRO_DEV across both approaches. ... ok
test_boundary_scenario_decision_and_rationale (test_example.TestLowCodeDecisionScenarios.test_boundary_scenario_decision_and_rationale)
Boundary scenario selects CUSTOM_CODE_PRO_DEV with valid rationale. ... ok
test_missing_info_scenario_decision_and_rationale (test_example.TestLowCodeDecisionScenarios.test_missing_info_scenario_decision_and_rationale)
Missing information scenario selects DEFER_INSUFFICIENT_INFORMATION with valid rationale. ... ok
test_normal_scenario_decision_and_rationale (test_example.TestLowCodeDecisionScenarios.test_normal_scenario_decision_and_rationale)
Normal scenario selects LOW_CODE_POWER_PLATFORM with valid rationale. ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.131s

OK

```
