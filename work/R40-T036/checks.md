# R40-T036 Check Evidence

## Tool Versions

- Python: 3.14.6 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: `encoder:100, head:20` with `encoder` Frozen

| Field | Input Parameter | Expected Output | Actual Output |
|---|---|---|---|
| **Parameter Manifest** | `{"encoder": 100, "head": 20}` | N/A | Evaluated ✓ |
| **Freeze Prefixes** | `["encoder"]` | N/A | Evaluated ✓ |
| **Total Parameters** | N/A | `120` | `120` ✓ |
| **Trainable Parameters** | N/A | `20` | `20` ✓ |
| **Frozen Parameters** | N/A | `100` | `100` ✓ |
| **Trainable Percentage** | N/A | `16.6667%` | `16.6667%` ✓ |
| **Unmatched Prefixes** | N/A | `()` | `()` ✓ |
| **Frozen Layers** | N/A | `("encoder",)` | `("encoder",)` ✓ |
| **Trainable Layers** | N/A | `("head",)` | `("head",)` ✓ |

### Scenario 2 — Unmatched Freeze Prefix Detection (Configuration Safety)

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Parameter Manifest** | `{"encoder": 100, "head": 20}` | N/A | Evaluated ✓ |
| **Freeze Prefixes** | `["encoder", "decoder", "backbone"]` | Flags unmatched prefixes | Reported ✓ |
| **Total Parameters** | N/A | `120` | `120` ✓ |
| **Trainable Parameters** | N/A | `20` | `20` ✓ |
| **Frozen Parameters** | N/A | `100` | `100` ✓ |
| **Unmatched Prefixes** | N/A | `("decoder", "backbone")` | `("decoder", "backbone")` ✓ |

### Scenario 3 — Multiple Prefixes & Hierarchical Model Structure

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | 5 layers: `transformer.encoder.*`, `transformer.decoder.*`, `lm_head.*` | Total: 350 | Total: 350 ✓ |
| **Freeze Prefixes** | `["transformer.encoder", "transformer.embedding"]` | Frozen: 240, Trainable: 110 | Frozen: 240, Trainable: 110 ✓ |
| **Unmatched Prefixes** | N/A | `()` | `()` ✓ |

### Scenario 4 — Boundary Scenario: No Freeze Rules (Full Fine-Tuning)

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Freeze Prefixes** | `()` | 100% trainable | 100.0% trainable (120/120) ✓ |
| **Frozen Params** | N/A | `0` | `0` ✓ |

### Scenario 5 — Boundary Scenario: All Layers Frozen

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Freeze Prefixes** | `["encoder", "head"]` | 0 trainable | 0.0% trainable (0/120) ✓ |
| **Frozen Params** | N/A | `120` | `120` ✓ |

### Scenario 6 — Failure Scenario A: Negative Parameter Count

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | `{"encoder": -10, "head": 20}` | `ValueError` raised | `ValueError` raised ✓ |
| **Error Message** | N/A | Contains `Invalid parameter count` | Verified ✓ |

### Scenario 7 — Failure Scenario B: Empty Layer Name

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | `{"": 100}` | `ValueError` raised | `ValueError` raised ✓ |
| **Error Message** | N/A | Contains `Invalid layer name` | Verified ✓ |

### Scenario 8 — Failure Scenario C: Invalid Manifest Type

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | `[("encoder", 100)]` (list instead of dict) | `TypeError` raised | `TypeError` raised ✓ |

---

## Focus: Refactoring by Extracting a Named Responsibility

The goal of this focus is to implement a correct monolithic baseline, extract one named responsibility, maintain the identical contract, and prove before/after equivalence.

1. **Monolithic Baseline (`baseline_freeze_budget`)**:
   Combines input validation, string prefix checking, parameter summation, and reporting in a single procedure.
2. **Extracted Named Responsibility (`PrefixFreezeMatcher`)**:
   Dedicated class encapsulating:
   - Configured freeze prefix normalization and storage (`_prefixes`).
   - Single-layer prefix matching (`match_layer`).
   - Full manifest classification and unmatched rule identification (`classify_manifest`).
3. **Refactored Coordinator (`count_fine_tuning_parameters`)**:
   Validates manifest structure, delegates layer classification to `PrefixFreezeMatcher`, and builds the immutable `FineTuningBudgetSummary`.

### Before / After Equivalence Proof

Tested across diverse fixtures via `prove_before_after_equivalence`:

| Fixture Description | Manifest Size | Freeze Rules | Baseline Result | Refactored Result | Equivalent? |
|---|---|---|---|---|---|
| **Contract Fixture** | 2 layers | `["encoder"]` | `total=120, train=20` | `total=120, train=20` | **Identical** (`True`) ✓ |
| **Unmatched Prefix Fixture** | 2 layers | `["encoder", "missing"]` | `unmatched=("missing",)` | `unmatched=("missing",)` | **Identical** (`True`) ✓ |
| **Multi-Prefix Hierarchy** | 4 layers | `["a.", "b."]` | `frozen=60, train=40` | `frozen=60, train=40` | **Identical** (`True`) ✓ |
| **Empty Rules Boundary** | 2 layers | `[]` | `train=100, frozen=0` | `train=100, frozen=0` | **Identical** (`True`) ✓ |
| **Full Freeze Boundary** | 1 layer | `["full_freeze"]` | `train=0, frozen=500` | `train=0, frozen=500` | **Identical** (`True`) ✓ |

---

## Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_trainable_count_fails` and `test_deliberate_wrong_unmatched_prefix_fails` verifying that:
- Any divergence in calculated trainable parameter counts immediately raises `AssertionError`.
- Any mismatch in reported unmatched prefixes immediately raises `AssertionError`.

## Test Run Summary

```
test_deliberate_wrong_trainable_count_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_trainable_count_fails) ... ok
test_deliberate_wrong_unmatched_prefix_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_unmatched_prefix_fails) ... ok
test_matcher_unit_functionality (test_example.TestExtractedResponsibility.test_matcher_unit_functionality) ... ok
test_contract_fixture_before_after_equivalence (test_example.TestFocusBeforeAfterEquivalence.test_contract_fixture_before_after_equivalence) ... ok
test_diverse_fixtures_before_after_equivalence (test_example.TestFocusBeforeAfterEquivalence.test_diverse_fixtures_before_after_equivalence) ... ok
test_all_layers_frozen (test_example.TestParameterBudgetContract.test_all_layers_frozen) ... ok
test_empty_freeze_prefixes_leaves_all_trainable (test_example.TestParameterBudgetContract.test_empty_freeze_prefixes_leaves_all_trainable) ... ok
test_empty_manifest_returns_zero_budget (test_example.TestParameterBudgetContract.test_empty_manifest_returns_zero_budget) ... ok
test_multiple_freeze_prefixes_and_nested_modules (test_example.TestParameterBudgetContract.test_multiple_freeze_prefixes_and_nested_modules) ... ok
test_required_contract_encoder_head (test_example.TestParameterBudgetContract.test_required_contract_encoder_head) ... ok
test_unmatched_freeze_prefix_is_reported (test_example.TestParameterBudgetContract.test_unmatched_freeze_prefix_is_reported) ... ok
test_empty_layer_name_raises_value_error (test_example.TestValidationFailures.test_empty_layer_name_raises_value_error) ... ok
test_invalid_freeze_prefixes_type_raises_type_error (test_example.TestValidationFailures.test_invalid_freeze_prefixes_type_raises_type_error) ... ok
test_invalid_manifest_type_raises_type_error (test_example.TestValidationFailures.test_invalid_manifest_type_raises_type_error) ... ok
test_negative_parameter_count_raises_value_error (test_example.TestValidationFailures.test_negative_parameter_count_raises_value_error) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
```

## Simulation Disclaimers

| Aspect | Local Budget Calculator (This Lab) | Production LLM Training Pipeline |
|---|---|---|
| Parameter Representation | In-memory named-parameter dictionary | Live PyTorch / HuggingFace `nn.Module` weights & gradient buffers |
| Execution Hardware | Local CPU stdlib only | Distributed GPU / TPU clusters (e.g., A100, H100) |
| Freezing Mechanism | Prefix matching on layer name strings | Toggling `parameter.requires_grad = False` in autograd graph |
| Model Performance | Evaluates counting and configuration validity | Requires forward/backward passes, loss convergence, and evaluation benchmarks |
