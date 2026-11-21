# R40-T049 Check Evidence

## Tool Versions

- Python: 3.15.2 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: Allowed `read` with Valid Path

| Field | Input / Action | Expected Result | Actual Result |
|---|---|---|---|
| **Proposed Action** | `{"tool": "read", "args": {"path": "/safe/data.txt"}}` | Executed via StubExecutor | Executed ✓ |
| **Execution Status** | N/A | `executed=True` | `executed=True` ✓ |
| **Refusal Record** | N/A | `None` | `None` ✓ |
| **Executor Call Count** | N/A | `1` | `1` ✓ |

### Scenario 2 — Failure Scenario A: Unknown `delete` Tool

| Field | Input / Action | Expected Result | Actual Result |
|---|---|---|---|
| **Proposed Action** | `{"tool": "delete", "args": {"path": "/safe/data.txt"}}` | Intercepted & Rejected | Rejected ✓ |
| **Execution Status** | N/A | `executed=False` | `executed=False` ✓ |
| **Refusal Reason** | N/A | `UNKNOWN_TOOL` | `UNKNOWN_TOOL` ✓ |
| **Executor Call Count** | N/A | `0` (Zero Leakage) | `0` ✓ |

### Scenario 3 — Failure Scenario B: Missing Required Argument

| Field | Input / Action | Expected Result | Actual Result |
|---|---|---|---|
| **Proposed Action** | `{"tool": "read", "args": {}}` | Intercepted & Rejected | Rejected ✓ |
| **Execution Status** | N/A | `executed=False` | `executed=False` ✓ |
| **Refusal Reason** | N/A | `MISSING_REQUIRED_ARGUMENT` | `MISSING_REQUIRED_ARGUMENT` ✓ |
| **Offending Argument** | N/A | `"path"` | `"path"` ✓ |
| **Executor Call Count** | N/A | `0` (Zero Leakage) | `0` ✓ |

### Focus: Comparison of Three Controlled Configurations

Workload: 5 test actions (`read`, `delete`, `search`, `summarize`, and malformed `read`).

| Metric | Config A (Strict Read) | Config B (Standard Inspection) | Config C (Extended Assistant) |
|---|---|---|---|
| **Allowed Tools** | `{"read"}` | `{"read", "search"}` | `{"read", "search", "summarize"}` |
| **Total Actions** | 5 | 5 | 5 |
| **Executed Count** | 1 | 2 | 3 |
| **Rejected Count** | 4 | 3 | 2 |
| **Interception Rate** | 80.0% | 60.0% | 40.0% |
| **Executor Leakage** | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

**Observed Trade-off**:
Expanding allowed tool definitions enables richer capabilities for agents (increasing pass-through from 20% to 60%) while maintaining strict safety boundary enforcement (100% of disallowed `delete` actions and malformed requests are intercepted without leaking to the executor).

### Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_*_fails` and `test_deliberate_leakage_assertion_fails` tests verifying that:
- Incorrect execution status assertions fail with `AssertionError`.
- Incorrect refusal reason assertions fail with `AssertionError`.
- Non-zero executor leakage assertions fail with `AssertionError`.

## Test Run Summary

```
Ran 10 tests in 0.001s
OK
Exit code: 0
```

## Simulation Disclaimers

| Simulation Property | Local Policy Validator | Real Production Content Safety / Guardrail |
|---|---|---|
| Validation mechanism | Exact schema & whitelist lookup | Multi-layered ML classifiers + regex + policies |
| Executor | In-memory python call tracker | Real system shell / API / DB connector |
| Network / Hardware | None | Azure Content Safety / OpenAI Moderation endpoints |
