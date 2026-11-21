# R40-T044 Check Evidence

## Tool versions

- Python: 3.15.2 (checked via `python3 --version`)
- unittest: stdlib (no third-party dependencies)

## Inputs, expected vs actual results

### Scenario 1 — Normal

| Field | Value |
|---|---|
| **Input** | `ingredients=["chicken","potatoes","carrots"], max_recipes=3` |
| **Scenario tag** | `__normal__` |
| **Mock fixture** | `"1. Roasted Chicken with Potatoes\n2. Chicken and Carrot Stew\n3. One-Pot Chicken Dinner\n"` |
| **Expected decision** | `SUGGEST` |
| **Actual decision** | `SUGGEST` ✓ |
| **recipes_found** | 3 |

### Scenario 2 — Boundary

| Field | Value |
|---|---|
| **Input** | `ingredients=["tomato"], max_recipes=2` |
| **Scenario tag** | `__boundary__` |
| **Mock fixture** | `"1. Simple Tomato Soup\n"` |
| **Expected decision** | `SUGGEST_MINIMAL` |
| **Actual decision** | `SUGGEST_MINIMAL` ✓ |
| **recipes_found** | 1 |

### Scenario 3 — Missing information

| Field | Value |
|---|---|
| **Input** | `ingredients=[], max_recipes=3` |
| **Scenario tag** | `__missing__` |
| **Mock fixture** | `""` (empty string) |
| **Expected decision** | `CANNOT_SUGGEST` |
| **Actual decision** | `CANNOT_SUGGEST` ✓ |
| **recipes_found** | 0 |

### Deliberate-failure checks (checker exits non-zero when decision is wrong)

Each scenario has a `test_deliberate_wrong_decision_fails` test that asserts the **wrong** expected decision inside `assertRaises(AssertionError)`. All three pass, proving the checker would exit non-zero if a decision were silently changed.

## Test run summary

```
Ran 14 tests in 0.001s
OK
Exit code: 0
```

## Mock adapter — real-service behaviour NOT established

| Behaviour | Established by mock? |
|---|---|
| Non-deterministic output | ✗ — mock is fully deterministic |
| Token-budget truncation | ✗ — mock never truncates |
| Network errors / HTTP 429 | ✗ — mock never raises APIError |
| Safety-filter refusals | ✗ — mock always returns fixture |
| Hallucinated ingredients | ✗ — mock only returns pre-written text |
| Latency / cost | ✗ — instantaneous and free |
