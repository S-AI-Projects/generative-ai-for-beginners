# R40-T047 Check Evidence

## Tool Versions

- Python: 3.15.2 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Exact Task Regression Case: `encoder:100, head:20` with `encoder` frozen

| Parameter / Field | Configured Input | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | `{"encoder": 100, "head": 20}` | N/A | `{"encoder": 100, "head": 20}` |
| **Freeze Prefixes** | `["encoder"]` | N/A | `["encoder"]` |
| **Total Parameters** | Calculated | `120` | `120` ✓ |
| **Trainable Parameters** | Calculated | `20` | `20` ✓ |
| **Frozen Parameters** | Calculated | `100` | `100` ✓ |
| **Unmatched Prefixes** | Calculated | `()` | `()` ✓ |

### Unmatched Freeze Prefix Reporting Case

| Parameter / Field | Configured Input | Expected Result | Actual Result |
|---|---|---|---|
| **Manifest** | `{"encoder": 100, "head": 20}` | N/A | `{"encoder": 100, "head": 20}` |
| **Freeze Prefixes** | `["encoder", "decoder"]` | N/A | `["encoder", "decoder"]` |
| **Total Parameters** | Calculated | `120` | `120` ✓ |
| **Trainable Parameters** | Calculated | `20` | `20` ✓ |
| **Frozen Parameters** | Calculated | `100` | `100` ✓ |
| **Unmatched Prefixes** | Reported | `("decoder",)` | `("decoder",)` ✓ |
| **Strict Mode Error** | `strict=True` | `ValueError` | `ValueError` raised ✓ |

### Boundary Cases

| Scenario | Input Manifest | Freeze Prefixes | Expected Total | Expected Trainable | Actual Result |
|---|---|---|---|---|---|
| **Empty Manifest** | `{}` | `["encoder"]` | `0` | `0` | `total=0, trainable=0, unmatched=('encoder',)` ✓ |
| **No Freeze Rules** | `{"encoder": 100, "head": 20}` | `[]` | `120` | `120` | `total=120, trainable=120` ✓ |
| **All Layers Frozen** | `{"encoder": 100, "head": 20}` | `["encoder", "head"]` | `120` | `0` | `total=120, trainable=0` ✓ |

### Validation & Failure Cases

| Case | Input | Expected Error | Actual Result |
|---|---|---|---|
| **Negative Parameter Count** | `{"encoder": -10}` | `ValueError` | `ValueError` raised ✓ |

### Worked Input-to-Output Explanation Verification

The `explanation` string was verified to contain:
- Input manifest breakdown (`{'encoder': 100, 'head': 20}`)
- Configured freeze rule list (`['encoder']`)
- Individual layer decision (`encoder` -> `FROZEN`, `head` -> `TRAINABLE`)
- Final counts (`total=120, trainable=20, frozen=100`)

### Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_*_fails` tests verifying that:
- Incorrect total parameter assertions fail with `AssertionError`.
- Incorrect trainable parameter assertions fail with `AssertionError`.
- Missing exception on negative parameter counts fails with `AssertionError`.

## Test Run Summary

```
Ran 20 tests in 0.001s
OK
Exit code: 0
```

## Simulation Disclaimers

| Real-Service Property | Local Manifest Mock | Real Fine-Tuning Service (e.g. Foundry / LoRA) |
|---|---|---|
| Weight storage | Pure integer dictionary | High-dimensional float16/bfloat16 tensors |
| Backward gradient pass | Not simulated | Backpropagation through trainable layers |
| GPU memory usage | Negligible (in-memory arithmetic) | Gigabytes of VRAM required |
| Hardware dependency | None | CUDA/ROCm/MPS GPU clusters |
