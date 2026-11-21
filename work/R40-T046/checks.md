# R40-T046 Check Evidence

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
| **Error Message** | N/A | Explains budget must be >= 0 | Verified ✓ |

### Extracted Responsibility & Baseline Equivalence

The monolithic `_baseline_check` baseline was compared against `TokenBudgetChecker` (with extracted `TokenizerInterface`). All fixture cases yielded identical retained tokens, removed counts, and budget attributes:
- `"one two three four"`, budget `3` → Identical (`retained=('one', 'two', 'three'), removed=1`)
- `""`, budget `3` → Identical (`retained=(), removed=0`)
- `"one two three"`, budget `0` → Identical (`retained=(), removed=3`)
- `"hello world"`, budget `10` → Identical (`retained=('hello', 'world'), removed=0`)
- `"single"`, budget `1` → Identical (`retained=('single',), removed=0`)
- `"a b c d e"`, budget `5` → Identical (`retained=('a', 'b', 'c', 'd', 'e'), removed=0`)

### Deliberate Failure Verification

The test module contains dedicated `test_deliberate_wrong_*_fails` assertions ensuring that:
1. Incorrect expected retained tokens cause `AssertionError`.
2. Incorrect expected removed counts cause `AssertionError`.
3. Erroneous lack of exception on negative budgets causes `AssertionError`.

## Test Run Summary

```
Ran 31 tests in 0.001s
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
