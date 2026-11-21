# R40-T035 Check Evidence

## Tool Versions

- Python: 3.14.6 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: Contract Fixture `[[[0, 255], [128, 64]]]`

| Field | Input Parameter | Expected Output | Actual Output |
|---|---|---|---|
| **Batch Tensor** | `[[[0, 255], [128, 64]]]` | N/A | Processed ✓ |
| **Batch Shape** | N/A | `(1, 2, 2)` | `(1, 2, 2)` ✓ |
| **Pixel (0, 0, 0)** | `0` | `0.0` | `0.0` ✓ |
| **Pixel (0, 0, 1)** | `255` | `1.0` | `1.0` ✓ |
| **Pixel (0, 1, 0)** | `128` | `128 / 255 ≈ 0.501961` | `0.501961` ✓ |
| **Pixel (0, 1, 1)** | `64` | `64 / 255 ≈ 0.25098` | `0.25098` ✓ |
| **Minimum Pixel** | N/A | `0.0` | `0.0` ✓ |
| **Maximum Pixel** | N/A | `1.0` | `1.0` ✓ |

### Scenario 2 — Failure Scenario A: Negative Pixel (`< 0`)

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | `[[[0, -1], [128, 64]]]` | `InvalidPixelValueError` raised | `InvalidPixelValueError` raised ✓ |
| **Error Message** | N/A | Contains `Invalid pixel value -1` | Verified ✓ |

### Scenario 3 — Failure Scenario B: Pixel Exceeding 255 (`> 255`)

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | `[[[0, 256], [128, 64]]]` | `InvalidPixelValueError` raised | `InvalidPixelValueError` raised ✓ |
| **Error Message** | N/A | Contains `Invalid pixel value 256` | Verified ✓ |

### Scenario 4 — Failure Scenario C: Non-Numeric Pixel

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | `[[[0, "255"], [128, 64]]]` | `TypeError` raised | `TypeError` raised ✓ |

### Scenario 5 — Failure Scenario D: Ragged Batch Dimensions

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | `[[[0, 255], [128]]]` (inconsistent width) | `InvalidTensorShapeError` raised | `InvalidTensorShapeError` raised ✓ |

### Scenario 6 — Boundary Scenario: Multi-Image Batch

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | 2 images of size 3x2 | Shape `(2, 3, 2)` preserved | Shape `(2, 3, 2)` preserved ✓ |
| **Pixel Range** | `[0, 255]` | Scaled to `[0.0, 1.0]` | Scaled to `[0.0, 1.0]` ✓ |

### Scenario 7 — Boundary Scenario: Empty Batch

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Batch Tensor** | `[]` | Shape `(0, 0, 0)` | Shape `(0, 0, 0)` ✓ |

---

## Focus: Callable Interface & Offline Service Adapter

The external image service dependency is encapsulated behind the `ImageBatchService` callable protocol and satisfied by `DeterministicLocalImageAdapter`.

### Unestablished Real-Service Behaviors Declared

The local offline adapter explicitly identifies the production behaviors it does not establish:
1. **Network transport latency**: No HTTP socket handling, TLS handshakes, or connection timeouts.
2. **Cloud authentication**: No API key verification, Microsoft Foundry / Azure OpenAI RBAC, or subscription validation.
3. **Diffusion model execution**: No latent denoising steps, UNet forward passes, or text conditioning.
4. **Content safety moderation**: No cloud toxicity or NSFW filtering pipelines.
5. **Image encoding/decoding**: No base64 conversions or PNG compression.

---

## Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_shape_assertion_fails` and `test_deliberate_wrong_pixel_value_fails` verifying that:
- Any divergence in calculated tensor shapes immediately raises `AssertionError`.
- Any mismatch in normalized pixel values immediately raises `AssertionError`.

## Test Run Summary

```
test_deliberate_wrong_pixel_value_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_pixel_value_fails) ... ok
test_deliberate_wrong_shape_assertion_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_shape_assertion_fails) ... ok
test_adapter_identifies_unestablished_real_service_behaviors (test_example.TestFocusCallableInterfaceAndAdapter.test_adapter_identifies_unestablished_real_service_behaviors) ... ok
test_adapter_satisfies_callable_interface (test_example.TestFocusCallableInterfaceAndAdapter.test_adapter_satisfies_callable_interface) ... ok
test_dependency_injection_with_custom_adapter (test_example.TestFocusCallableInterfaceAndAdapter.test_dependency_injection_with_custom_adapter) ... ok
test_empty_batch_boundary (test_example.TestTensorShapeContract.test_empty_batch_boundary) ... ok
test_multi_image_batch_processing (test_example.TestTensorShapeContract.test_multi_image_batch_processing) ... ok
test_negative_pixel_is_rejected (test_example.TestTensorShapeContract.test_negative_pixel_is_rejected) ... ok
test_non_numeric_pixel_raises_type_error (test_example.TestTensorShapeContract.test_non_numeric_pixel_raises_type_error) ... ok
test_pixel_greater_than_255_is_rejected (test_example.TestTensorShapeContract.test_pixel_greater_than_255_is_rejected) ... ok
test_ragged_tensor_height_rejected (test_example.TestTensorShapeContract.test_ragged_tensor_height_rejected) ... ok
test_ragged_tensor_width_rejected (test_example.TestTensorShapeContract.test_ragged_tensor_width_rejected) ... ok
test_required_contract_fixture (test_example.TestTensorShapeContract.test_required_contract_fixture) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
```

## Simulation Disclaimers

| Aspect | Local Offline Adapter (This Lab) | Production Cloud Image Generation Service |
|---|---|---|
| Input Pipeline | In-memory 3D list validation | Multi-part form-data / JSON base64 payloads |
| Normalization | Pure Python float division (`pixel / 255.0`) | GPU tensor transforms (e.g. PyTorch / torchvision) |
| Hardware / Resources | CPU in-memory, Python 3 stdlib only | Dedicated GPU clusters running diffusion models |
| Output Verification | Structural preprocessing correctness only | Human visual fidelity and prompt alignment |
