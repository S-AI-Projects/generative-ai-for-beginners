# R40-T029 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T029.
Focus: Select eligible entries from a local synthetic model manifest using explicit RAM and context requirements; report why excluded entries fail. Fixture A needs RAM4/context2048, B RAM8/context4096; budget RAM6 and requested context1024 admits only A. Values are invented teaching fixtures, not claims about the named real models. Focus: Compare three small controlled configurations or input sizes using a metric appropriate to this contract. Report correctness and the observed trade-off without claiming real-world model accuracy.

---

## 1. Normal Scenario (`--scenario normal`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario normal
```

Expected Decision: `SELECTIVE_ADMISSION_SUCCESS`
Expected Admitted Models: `["model-a"]`
Expected Excluded Models: `["model-b"]`
Expected Exclusion Reason: `RAM requirement (8.0 GB) exceeds host budget (6.0 GB) by 2.0 GB`

Actual Output:
```json
{
  "classification": "synthetic_model_manifest_selection_simulation",
  "decision": "SELECTIVE_ADMISSION_SUCCESS",
  "budget": {
    "budget_ram_gb": 6.0,
    "requested_context_tokens": 1024
  },
  "total_evaluated": 2,
  "admitted_count": 1,
  "excluded_count": 1,
  "admission_rate_pct": 50.0,
  "admitted_models": [
    "model-a"
  ],
  "excluded_models": [
    "model-b"
  ],
  "rationale": "Admitted 1 of 2 candidates (model-a). Excluded 1 candidates (model-b) due to resource deficits.",
  "evaluations": [
    {
      "model_id": "model-a",
      "name": "Synthetic Llama Edge 4B (Fixture A)",
      "eligible": true,
      "min_ram_gb": 4.0,
      "budget_ram_gb": 6.0,
      "ram_slack_gb": 2.0,
      "max_context_tokens": 2048,
      "requested_context_tokens": 1024,
      "context_headroom_tokens": 1024,
      "exclusion_reasons": [],
      "reason_codes": []
    },
    {
      "model_id": "model-b",
      "name": "Synthetic Llama Mid 8B (Fixture B)",
      "eligible": false,
      "min_ram_gb": 8.0,
      "budget_ram_gb": 6.0,
      "ram_slack_gb": -2.0,
      "max_context_tokens": 4096,
      "requested_context_tokens": 1024,
      "context_headroom_tokens": 3072,
      "exclusion_reasons": [
        "RAM requirement (8.0 GB) exceeds host budget (6.0 GB) by 2.0 GB"
      ],
      "reason_codes": [
        "RAM_EXCEEDS_BUDGET"
      ]
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Fixture A is admitted (+2.0 GB RAM slack, +1024 tokens headroom); Fixture B is excluded with exact RAM deficit diagnosis.

---

## 2. Boundary Scenario (`--scenario boundary`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario boundary
```

Expected Decision: `BOUNDARY_VERIFICATION_SUCCESS`
Case 1 (Exact Equality: RAM 4.0 GB / Context 2048): Admitted `["model-a"]` with `0.0 GB` RAM slack and `0` context headroom.
Case 2 (Step-Off Deficit: RAM 3.9 GB / Context 2048): Admitted `[]` (all excluded).

Actual Output:
```json
{
  "classification": "boundary_threshold_evaluation_simulation",
  "decision": "BOUNDARY_VERIFICATION_SUCCESS",
  "case_exact_equality": {
    "budget": {
      "budget_ram_gb": 4.0,
      "requested_context_tokens": 2048
    },
    "admitted_models": [
      "model-a"
    ],
    "fixture_a_ram_slack_gb": 0.0,
    "fixture_a_context_headroom_tokens": 0,
    "boundary_status": "EXACT_MATCH_ADMITTED"
  },
  "case_stepoff_deficit": {
    "budget": {
      "budget_ram_gb": 3.9,
      "requested_context_tokens": 2048
    },
    "admitted_models": [],
    "stepoff_status": "THRESHOLD_VIOLATION_EXCLUDED"
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Boundary threshold equality and step-off deficit conditions strictly verified.

---

## 3. Failure & Validation Scenario (`--scenario failure`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario failure
```

Expected Decision: `INPUT_VALIDATION_HANDLED_CLEANLY`
Expected Errors Validated: 3 (Negative RAM, Zero Context, Duplicate ID)

Actual Output:
```json
{
  "classification": "input_validation_failure_simulation",
  "decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
  "errors_validated_count": 3,
  "errors": [
    {
      "error_type": "InvalidResourceBudgetError",
      "message": "Host RAM budget must be strictly positive (> 0), got: -2.0 GB",
      "test_case": "negative_ram_budget"
    },
    {
      "error_type": "InvalidResourceBudgetError",
      "message": "Requested context length must be strictly positive (> 0 tokens), got: 0",
      "test_case": "zero_context_tokens"
    },
    {
      "error_type": "MalformedManifestError",
      "message": "Duplicate model_id detected in manifest: 'model-a'",
      "test_case": "duplicate_model_id"
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Documented failure conditions raised structured domain exceptions with clear diagnostics.

---

## 4. Evaluation Experiment (`--experiment`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --experiment
```

Expected Decision: `EXPERIMENT_EVALUATION_SUCCESS`
Expected Configurations Evaluated: 3 (Edge Constrained, Long-Context Cloud, Generous Workstation)

Actual Output:
```json
{
  "classification": "model_selection_evaluation_experiment",
  "decision": "EXPERIMENT_EVALUATION_SUCCESS",
  "total_configs_compared": 3,
  "all_configs_correct": true,
  "configurations": [
    {
      "config_id": "CONFIG_1_EDGE_CONSTRAINED",
      "name": "Edge / Resource-Constrained Host",
      "target_use_case": "Local desktop or edge device running single-tenant inference.",
      "budget": {
        "budget_ram_gb": 6.0,
        "requested_context_tokens": 1024
      },
      "total_candidates": 2,
      "admitted_models": [
        "model-a"
      ],
      "excluded_models": [
        "model-b"
      ],
      "admission_rate_pct": 50.0,
      "metrics": {
        "admitted_count": 1,
        "excluded_count": 1,
        "avg_ram_slack_gb": 2.0,
        "avg_context_headroom_tokens": 1024.0,
        "primary_bottleneck": "RAM_CAPACITY",
        "latency_us": 16.33,
        "per_candidate_latency_us": 8.17
      },
      "correctness_verified": true
    },
    {
      "config_id": "CONFIG_2_LONG_CONTEXT_CLOUD",
      "name": "Long-Context Cloud Host",
      "target_use_case": "Cloud instance optimized for long-document RAG and large context.",
      "budget": {
        "budget_ram_gb": 8.0,
        "requested_context_tokens": 4096
      },
      "total_candidates": 2,
      "admitted_models": [
        "model-b"
      ],
      "excluded_models": [
        "model-a"
      ],
      "admission_rate_pct": 50.0,
      "metrics": {
        "admitted_count": 1,
        "excluded_count": 1,
        "avg_ram_slack_gb": 0.0,
        "avg_context_headroom_tokens": 0.0,
        "primary_bottleneck": "CONTEXT_WINDOW_LIMIT",
        "latency_us": 8.46,
        "per_candidate_latency_us": 4.23
      },
      "correctness_verified": true
    },
    {
      "config_id": "CONFIG_3_WORKSTATION_EXPANSIVE",
      "name": "Generous Workstation Host",
      "target_use_case": "High-memory developer workstation supporting concurrent models.",
      "budget": {
        "budget_ram_gb": 16.0,
        "requested_context_tokens": 1024
      },
      "total_candidates": 2,
      "admitted_models": [
        "model-a",
        "model-b"
      ],
      "excluded_models": [],
      "admission_rate_pct": 100.0,
      "metrics": {
        "admitted_count": 2,
        "excluded_count": 0,
        "avg_ram_slack_gb": 10.0,
        "avg_context_headroom_tokens": 2048.0,
        "primary_bottleneck": "NONE_UNCONSTRAINED",
        "latency_us": 4.92,
        "per_candidate_latency_us": 2.46
      },
      "correctness_verified": true
    }
  ],
  "trade_off_analysis": {
    "finding": "Host selection involves an explicit architectural trade-off between deployment footprint and operational workload flexibility.",
    "edge_tradeoff": "Config 1 (Edge) minimizes hardware allocation to 6 GB, admitting only Fixture A. It yields +2.0 GB memory buffer safety margin, but rejects workloads requiring longer contexts (>2048).",
    "cloud_tradeoff": "Config 2 (Long-Context) unlocks 4096-token support via Fixture B, but consumes 100% of the 8 GB budget (0.0 GB RAM slack), eliminating safety buffers for memory spikes.",
    "workstation_tradeoff": "Config 3 (Workstation) achieves 100% admission rate and maximum model failover options (+10.0 GB avg slack), but requires high hardware over-provisioning (16 GB RAM) for small 1024-token requests.",
    "no_accuracy_claim_disclaimer": "Metrics reflect resource constraint satisfaction and filtering trade-offs on synthetic teaching fixtures; no claims are made regarding physical GPU throughput or real-world model accuracy."
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Three controlled configurations evaluated with domain metrics (admission rate, RAM slack, context headroom, bottleneck analysis) and documented trade-offs without unsupported real-model claims.

---

## 5. Canonical Decision Table Check (`--check`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --check
```

Expected Status: `success`
Expected Total Scenarios: 4
Expected Passed: 4, Failed: 0

Actual Output:
```json
{
  "classification": "model_manifest_selection_canonical_check",
  "status": "success",
  "total_scenarios": 4,
  "passed_scenarios": 4,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_admitted": [
        "model-a"
      ],
      "actual_admitted": [
        "model-a"
      ],
      "expected_decision": "SELECTIVE_ADMISSION_SUCCESS",
      "actual_decision": "SELECTIVE_ADMISSION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Admitted 1 of 2 candidates (model-a). Excluded 1 candidates (model-b) due to resource deficits."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "expected_decision": "BOUNDARY_VERIFICATION_SUCCESS",
      "actual_decision": "BOUNDARY_VERIFICATION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Exact equality at boundary admits Fixture A; step-off deficit (3.9 GB) excludes it."
    },
    {
      "scenario_id": "SCENARIO_FAILURE",
      "scenario_type": "failure_validation",
      "expected_decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
      "actual_decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Invalid negative RAM, zero context, and duplicate IDs were handled with explicit exceptions."
    },
    {
      "scenario_id": "SCENARIO_EXPERIMENT",
      "scenario_type": "evaluation_experiment",
      "expected_decision": "EXPERIMENT_EVALUATION_SUCCESS",
      "actual_decision": "EXPERIMENT_EVALUATION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Evaluated 3 controlled configurations reporting admission rates, resource slack, and trade-offs."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 4 canonical scenarios passed against the formal decision table.

---

## 6. Deliberate Tamper Test (`--tamper`)

Command:
```bash
python3 21-meta/applied-labs/r40-t029/example.py --tamper
```

Expected Exit Code: `1`
Expected Error Type: `DecisionMismatchError`

Actual Stderr Output:
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "error_message": "Deliberate tamper test triggered: Injected expectation that Fixture B is admitted under RAM 6 GB.",
  "exit_code": 1
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — A deliberate wrong result strictly makes the verification check fail with exit code 1, proving regression sensitivity.

---

## 7. Automated Unit Test Discovery Suite

Command:
```bash
python3 -m unittest discover -s 21-meta/applied-labs/r40-t029 -p "test_*.py" -v
```

Expected Status: `OK` with non-zero test count

Actual Test Runner Output:
```
test_context_window_exact_and_stepoff (test_example.TestBoundaryConditions.test_context_window_exact_and_stepoff)
Context window thresholding must exclude models when requested tokens exceed capacity. ... ok
test_dual_deficit_reporting (test_example.TestBoundaryConditions.test_dual_deficit_reporting)
Candidate failing both RAM and context must report DUAL_RESOURCE_DEFICIT. ... ok
test_exact_equality_admits_candidate (test_example.TestBoundaryConditions.test_exact_equality_admits_candidate)
Exact budget match (RAM 4.0 GB, Context 2048) must admit Fixture A with zero slack. ... ok
test_run_boundary_scenario_function (test_example.TestBoundaryConditions.test_run_boundary_scenario_function)
Direct call to run_boundary_scenario must succeed and verify boundary cases. ... ok
test_threshold_stepoff_excludes_candidate (test_example.TestBoundaryConditions.test_threshold_stepoff_excludes_candidate)
Host RAM of 3.9 GB (0.1 GB below Fixture A requirement) must exclude Fixture A. ... ok
test_canonical_check_clean_pass (test_example.TestCanonicalCheckAndTamper.test_canonical_check_clean_pass)
Untampered canonical check must report 100% pass across all scenarios. ... ok
test_canonical_check_tamper_fails (test_example.TestCanonicalCheckAndTamper.test_canonical_check_tamper_fails)
Tampered check must raise DecisionMismatchError. ... ok
test_canonical_fixture_properties (test_example.TestCanonicalSelectionContract.test_canonical_fixture_properties)
Verifies canonical fixture values match the contract specification. ... ok
test_canonical_selection_admits_only_a (test_example.TestCanonicalSelectionContract.test_canonical_selection_admits_only_a)
Budget RAM 6 and requested context 1024 must admit ONLY Fixture A. ... ok
test_run_normal_scenario_function (test_example.TestCanonicalSelectionContract.test_run_normal_scenario_function)
Direct call to run_normal_scenario must return valid report admitting only A. ... ok
test_evaluation_experiment_structure_and_correctness (test_example.TestEvaluationExperiment.test_evaluation_experiment_structure_and_correctness)
Experiment must evaluate 3 configurations and verify all correctness assertions. ... ok
test_trade_off_analysis_narrative_present (test_example.TestEvaluationExperiment.test_trade_off_analysis_narrative_present)
Experiment report must include explicit trade-off findings without real-model claims. ... ok
test_model_manifest_entry_initialization (test_example.TestManifestDataModelsAndValidation.test_model_manifest_entry_initialization)
Entry must preserve attributes and serialize accurately to dictionary. ... ok
test_resource_budget_rejects_negative_or_zero_context (test_example.TestManifestDataModelsAndValidation.test_resource_budget_rejects_negative_or_zero_context)
Non-positive requested context must raise InvalidResourceBudgetError. ... ok
test_resource_budget_rejects_negative_or_zero_ram (test_example.TestManifestDataModelsAndValidation.test_resource_budget_rejects_negative_or_zero_ram)
Non-positive host RAM budgets must raise InvalidResourceBudgetError. ... ok
test_resource_budget_validation_positive (test_example.TestManifestDataModelsAndValidation.test_resource_budget_validation_positive)
Valid positive budget must pass validation without error. ... ok
test_validate_manifest_duplicate_id_rejected (test_example.TestManifestDataModelsAndValidation.test_validate_manifest_duplicate_id_rejected)
Manifest with duplicate model IDs must raise MalformedManifestError. ... ok
test_validate_manifest_empty_id_rejected (test_example.TestManifestDataModelsAndValidation.test_validate_manifest_empty_id_rejected)
Entry with empty model_id string must raise MalformedManifestError. ... ok
test_validate_manifest_empty_rejected (test_example.TestManifestDataModelsAndValidation.test_validate_manifest_empty_rejected)
Empty manifest must raise MalformedManifestError. ... ok
test_validate_manifest_negative_ram_rejected (test_example.TestManifestDataModelsAndValidation.test_validate_manifest_negative_ram_rejected)
Entry with negative min_ram_gb must raise MalformedManifestError. ... ok
test_validate_manifest_non_positive_context_rejected (test_example.TestManifestDataModelsAndValidation.test_validate_manifest_non_positive_context_rejected)
Entry with non-positive context length must raise MalformedManifestError. ... ok
test_cli_check_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_check_exit_0)
CLI --check must exit 0 and report all passed. ... ok
test_cli_experiment_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_experiment_exit_0)
CLI --experiment must exit 0 and return 3-configuration comparison. ... ok
test_cli_scenario_boundary_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_boundary_exit_0)
CLI --scenario boundary must exit 0 and verify threshold equality. ... ok
test_cli_scenario_failure_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_failure_exit_0)
CLI --scenario failure must exit 0 and report caught validation errors. ... ok
test_cli_scenario_normal_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_normal_exit_0)
CLI --scenario normal must exit 0, emit JSON, and admit only model-a. ... ok
test_cli_tamper_fails_with_nonzero_exit_1 (test_example.TestSubprocessCLIExecution.test_cli_tamper_fails_with_nonzero_exit_1)
CLI --tamper must exit 1 and report DecisionMismatchError in stderr. ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.191s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 27 unit tests executed and passed in a fresh process.

---

## 8. Summary of Task Verification

| Scenario / Check | Invocations / Config | Expected Decision | Actual Decision | Status |
|---|---|---|---|---|
| `SCENARIO_NORMAL` | RAM 6 GB / Context 1024 | `SELECTIVE_ADMISSION_SUCCESS` (Admits A, Excludes B) | `SELECTIVE_ADMISSION_SUCCESS` (Admits A, Excludes B) | **PASS** |
| `SCENARIO_BOUNDARY` | Boundary Equality (RAM 4 / Ctx 2048) & Step-off (RAM 3.9) | `BOUNDARY_VERIFICATION_SUCCESS` | `BOUNDARY_VERIFICATION_SUCCESS` | **PASS** |
| `SCENARIO_FAILURE` | Negative RAM, Zero Context, Duplicate ID | `INPUT_VALIDATION_HANDLED_CLEANLY` (3 errors) | `INPUT_VALIDATION_HANDLED_CLEANLY` (3 errors) | **PASS** |
| `SCENARIO_EXPERIMENT` | 3 Controlled Configs (Edge, Cloud, Workstation) | `EXPERIMENT_EVALUATION_SUCCESS` | `EXPERIMENT_EVALUATION_SUCCESS` | **PASS** |
| `CANONICAL_CHECK` | All Scenarios Verified | `all_passed: true` | `all_passed: true` | **PASS** |
| `DELIBERATE_TAMPER` | Mutated Expectation | Exit Code `1` (`DecisionMismatchError`) | Exit Code `1` (`DecisionMismatchError`) | **PASS** |
| `UNIT_TESTS` | 27 Unit Tests via Discovery | `OK` (Exit 0) | `OK` (Exit 0) | **PASS** |

All checks passed successfully. Verification complete.
