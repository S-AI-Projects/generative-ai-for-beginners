# R40-T008 — Verification Results

This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T008.

## 1. Normal Scenario (Shape Preserved, 0->0, 255->1)
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "NORMALIZATION_SUCCESS_SHAPE_PRESERVED",
  "input_batch": [
    [
      [
        0,
        255
      ],
      [
        128,
        64
      ]
    ]
  ],
  "normalized_batch": [
    [
      [
        0.0,
        1.0
      ],
      [
        0.501961,
        0.25098
      ]
    ]
  ],
  "input_shape": [
    1,
    2,
    2
  ],
  "output_shape": [
    1,
    2,
    2
  ],
  "zero_mapped_to_zero": true,
  "max_mapped_to_one": true,
  "contract_satisfied": true
}
```

## 2. Negative Pixel Failure Scenario
```json
{
  "scenario_id": "SCENARIO_NEGATIVE_PIXEL",
  "decision": "NEGATIVE_PIXEL_REJECTED",
  "input_batch": [
    [
      [
        -10,
        255
      ],
      [
        128,
        64
      ]
    ]
  ],
  "error_message": "Pixel value -10 at (0,0,0) out of bounds [0, 255].",
  "failed_as_expected": true,
  "contract_satisfied": true
}
```

## 3. Overflow Pixel Failure Scenario
```json
{
  "scenario_id": "SCENARIO_OVERFLOW_PIXEL",
  "decision": "OVERFLOW_PIXEL_REJECTED",
  "input_batch": [
    [
      [
        0,
        300
      ],
      [
        128,
        64
      ]
    ]
  ],
  "error_message": "Pixel value 300 at (0,0,1) out of bounds [0, 255].",
  "failed_as_expected": true,
  "contract_satisfied": true
}
```

## 4. Pipeline Failure and Recovery Demonstration
```json
{
  "scenario_id": "SCENARIO_RECOVERY",
  "decision": "FAILURE_DOCUMENTED_AND_RECOVERED",
  "step_1_invalid_result": {
    "status": "FAILED",
    "shape": null,
    "normalized_batch": null,
    "error": "Pixel value -50 at (0,1,0) out of bounds [0, 255]."
  },
  "step_2_recovery_result": {
    "status": "SUCCESS",
    "shape": [
      1,
      2,
      2
    ],
    "normalized_batch": [
      [
        [
          0.0,
          1.0
        ],
        [
          0.501961,
          0.25098
        ]
      ]
    ],
    "error": null
  },
  "pipeline_state": {
    "processed_count": 1,
    "error_count": 1
  },
  "recovery_verified": true,
  "contract_satisfied": true
}
```

## 5. Tamper Test Output (Deliberate Non-Zero Exit)
```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "details": "Decision mismatch detected: [{'scenario_id': 'SCENARIO_NORMAL', 'expected_decision': 'TAMPERED_WRONG_DECISION', 'actual_decision': 'NORMALIZATION_SUCCESS_SHAPE_PRESERVED', 'passed': False}]",
  "exit_code": 1
}
```

## 6. Unittest Output
```
test_cli_check (test_example.TestCLIExecution.test_cli_check) ... ok
test_cli_scenario_negative (test_example.TestCLIExecution.test_cli_scenario_negative) ... ok
test_cli_scenario_normal (test_example.TestCLIExecution.test_cli_scenario_normal) ... ok
test_cli_scenario_overflow (test_example.TestCLIExecution.test_cli_scenario_overflow) ... ok
test_cli_scenario_recovery (test_example.TestCLIExecution.test_cli_scenario_recovery) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestCLIExecution.test_cli_tamper_fails_with_nonzero_exit) ... ok
test_canonical_check_fails_on_tamper (test_example.TestCanonicalCheckAndTamper.test_canonical_check_fails_on_tamper) ... ok
test_canonical_check_passes (test_example.TestCanonicalCheckAndTamper.test_canonical_check_passes) ... ok
test_deliberate_wrong_result_fails (test_example.TestDeliberateWrongResult.test_deliberate_wrong_result_fails) ... ok
test_failure_and_subsequent_recovery (test_example.TestPipelineFailureAndRecovery.test_failure_and_subsequent_recovery) ... ok
test_canonical_batch_shape_preserved (test_example.TestTensorShapeAndNormalizationContract.test_canonical_batch_shape_preserved)
Batch [[[0, 255], [128, 64]]] stays shape (1, 2, 2); 0->0 and 255->1. ... ok
test_negative_pixel_rejected (test_example.TestTensorShapeAndNormalizationContract.test_negative_pixel_rejected)
Negative pixel raises TensorContractError. ... ok
test_non_numeric_elements_rejected (test_example.TestTensorShapeAndNormalizationContract.test_non_numeric_elements_rejected)
Non-numeric elements raise TensorContractError. ... ok
test_overflow_pixel_rejected (test_example.TestTensorShapeAndNormalizationContract.test_overflow_pixel_rejected)
Pixel > 255 raises TensorContractError. ... ok
test_ragged_dimensions_rejected (test_example.TestTensorShapeAndNormalizationContract.test_ragged_dimensions_rejected)
Ragged/inconsistent dimensions raise TensorContractError. ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.175s

OK

```
