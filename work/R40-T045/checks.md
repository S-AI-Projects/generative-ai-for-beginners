# R40-T045 Check Evidence

## Tool versions

- Python: 3.15.2 (checked via `python3 --version`)
- unittest: stdlib (no third-party dependencies)

## Inputs, expected vs actual results

### Scenario 1 — Normal

| Field | Value |
|---|---|
| **Input** | `user_message` contains `__normal__` |
| **Fixture events** | `("chunk","Hello, ")`, `("chunk","world!")`, `("complete","")` |
| **Expected state** | `COMPLETE` |
| **Actual state** | `COMPLETE` ✓ |
| **Expected text** | `"Hello, world!"` |
| **Actual text** | `"Hello, world!"` ✓ |
| **Chunks in order?** | Yes — first "Hello, " then "world!" |

### Scenario 2 — Boundary

| Field | Value |
|---|---|
| **Input** | `user_message` contains `__boundary__` |
| **Fixture events** | `("chunk","")`, `("complete","")` |
| **Expected state** | `COMPLETE` |
| **Actual state** | `COMPLETE` ✓ |
| **Expected text** | `""` (empty string) |
| **Actual text** | `""` ✓ |

### Scenario 3 — Error (mid-stream)

| Field | Value |
|---|---|
| **Input** | `user_message` contains `__error__` |
| **Fixture events** | `("chunk","Partial ")`, `("error","Simulated network timeout…")` |
| **Expected state** | `ERROR` |
| **Actual state** | `ERROR` ✓ |
| **Expected text** | `"Partial "` (preserved, not discarded) |
| **Actual text** | `"Partial "` ✓ |
| **error_detail contains "timeout"?** | Yes ✓ |

### Post-completion / post-error chunk rejection

| Check | Expected | Actual |
|---|---|---|
| `apply_chunk` on COMPLETE message | `ValueError` raised | `ValueError` raised ✓ |
| `apply_chunk` on ERROR message | `ValueError` raised | `ValueError` raised ✓ |
| Stray chunk text in final message | Absent ("STRAY" not in text) | Absent ✓ |

### Error recovery

| Check | Expected | Actual |
|---|---|---|
| Turn 1 (error) state | `ERROR` | `ERROR` ✓ |
| Turn 2 (normal) state | `COMPLETE` | `COMPLETE` ✓ |
| Turn 2 text | `"Hello, world!"` | `"Hello, world!"` ✓ |
| msg1.message_id ≠ msg2.message_id | True | True ✓ |

### Deliberate-failure checks

Each scenario has at least one `test_deliberate_wrong_*_fails` test that:
1. Gets the actual result.
2. Asserts the **wrong** expected value inside `assertRaises(AssertionError)`.
3. Proves the checker would exit non-zero if a result were silently changed.

All deliberate-failure tests pass → checker is verified.

## Test run summary

```
Ran 22 tests in 0.000s
OK
Exit code: 0
```

## Mock adapter — real-service behaviour NOT established

| Behaviour | Established by mock? |
|---|---|
| Non-deterministic token output | ✗ — mock is fully deterministic |
| Network back-pressure / HTTP 429 | ✗ — mock never raises APIError |
| Token-budget truncation | ✗ — mock never truncates |
| Safety-filter refusals | ✗ — mock always yields fixture |
| Server-assigned message IDs | ✗ — mock uses local uuid4() |
| True concurrent streaming | ✗ — mock is synchronous |
