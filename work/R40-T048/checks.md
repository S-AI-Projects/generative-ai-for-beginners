# R40-T048 Check Evidence

## Tool Versions

- Python: 3.15.2 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario (Truncation)

| Field | Input / Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Prompt** | `"one two three four"` | N/A | `"one two three four"` |
| **Budget** | `3` | `3` | `3` |
| **Retained Tokens** | `["one", "two", "three"]` | `("one", "two", "three")` | `("one", "two", "three")` ✓ |
| **Removed Count** | N/A | `1` | `1` ✓ |
| **Tokenizer Label** | N/A | Contains `TEACHING APPROXIMATION` | Present ✓ |

### Scenario 2 — Boundary Scenario (Empty Input)

| Field | Input / Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Prompt** | `""` | N/A | `""` |
| **Budget** | `3` | `3` | `3` |
| **Retained Tokens** | `[]` | `()` | `()` ✓ |
| **Removed Count** | N/A | `0` | `0` ✓ |

### Scenario 3 — Boundary Scenario (Zero Budget)

| Field | Input / Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Prompt** | `"one two three"` | N/A | `"one two three"` |
| **Budget** | `0` | `0` | `0` |
| **Retained Tokens** | `[]` | `()` | `()` ✓ |
| **Removed Count** | N/A | `3` | `3` ✓ |

### Scenario 4 — Failure Scenario (Negative Budget)

| Field | Input / Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Budget** | `-1` | Rejection with `ValueError` | `ValueError` raised ✓ |
| **Error Message** | N/A | Contains `Budget must be >= 0` | Verified ✓ |

### Focus: Intermediate States & Invariant Verification

The intermediate pipeline trace records 4 distinct states before report assembly:
1. `VALIDATE_INPUT`: `{budget: 3, prompt_length: ...}`
2. `TOKENIZATION`: `{tokens: ('alpha', 'beta', ...), token_count: 5}`
3. `EVALUATE_BUDGET`: `{initial_count: 5, budget: 3, planned_retained_count: 3, planned_removed_count: 2}`
4. `TRUNCATION`: `{retained_tokens: ('alpha', 'beta', 'gamma'), removed_tokens: ('delta', 'epsilon')}`

Invariants formally tested and confirmed:
- **Token Conservation**: `token_count == len(retained_tokens) + removed_count` ✓
- **Sequence Reconstitution**: `tokens == retained_tokens + removed_tokens` ✓
- **Bounded Capacity**: `len(retained_tokens) <= budget` ✓
- **Prefix Preservation**: `tokens[:len(retained_tokens)] == retained_tokens` ✓
- **Planning Accuracy**: `planned_retained_count == len(retained_tokens)` and `planned_removed_count == removed_count` ✓

### Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_*_fails` and `test_deliberate_invariant_violation_fails` tests verifying that:
- Incorrect expected retained tokens cause `AssertionError`.
- Incorrect expected removed counts cause `AssertionError`.
- Invariant violations (e.g., token count corruption) cause `AssertionError`.

## Test Run Summary

```
Ran 18 tests in 0.001s
OK
Exit code: 0
```

## Approximation and Real-Service Distinctions

| Feature / Behavior | WhitespaceTokenizer (Teaching Approximation) | Production Model Tokenizer (e.g. Phi-3/4) |
|---|---|---|
| Sub-word Tokenization | No (splits purely on whitespace) | Yes (BPE / SentencePiece) |
| Special Tokens (BOS/EOS) | None | Embedded control tokens |
| Unicode / Multi-lingual | Naive whitespace split | Byte-level fallbacks & normalization |
| Hardware Dependencies | None (pure Python stdlib) | NPU/GPU/ONNX Runtime execution |
