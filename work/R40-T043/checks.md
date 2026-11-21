# R40-T043 Check Evidence

## Tool Versions

- Python: 3.15.2 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: Valid Server Launch Configuration

| Field | Input Parameter | Expected Output | Actual Output |
|---|---|---|---|
| **Command** | `"uvicorn"` | `"uvicorn"` | `"uvicorn"` ✓ |
| **Arguments** | `["app:api", "--port", "8000"]` | `("app:api", "--port", "8000")` | `("app:api", "--port", "8000")` ✓ |
| **Configured Env** | `{"API_KEY": "sk-secret-12345"}` | Keys recorded, values redacted | Keys recorded, values redacted ✓ |
| **Redacted Value** | Secret string | `"[REDACTED]"` | `"[REDACTED]"` ✓ |
| **Process Launched** | N/A | `False` | `False` ✓ |

### Scenario 2 — Failure Scenario A: Missing Launch Command

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Config** | `{"args": ["--port", "8000"]}` | `ValueError` raised | `ValueError` raised ✓ |
| **Error Message** | N/A | Contains `Missing required 'command'` | Verified ✓ |

### Scenario 3 — Failure Scenario B: Single String where Argument Array Required

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Config** | `{"command": "python", "args": "-m http.server 8080"}` | `TypeError` raised | `TypeError` raised ✓ |
| **Error Message** | N/A | Explains array strictly required | Verified ✓ |

### Focus: Comparison with Independent Reference Oracle Table

Identical inputs were evaluated through `validate_launch_config` and `reference_oracle_table`:
- **Inference Server Fixture**:
  - `command`: `"uvicorn"` == `"uvicorn"` ✓
  - `args`: `("main:app", "--port", "8000")` == `("main:app", "--port", "8000")` ✓
  - `redacted_env`: `{"KEY": "[REDACTED]"}` == `{"KEY": "[REDACTED]"}` ✓
  - `process_launched`: `False` == `False` ✓
- **Multi-Flag Fixture**: Full parity across all attributes ✓
- **Empty Bounds Fixture**: Full parity across all attributes ✓

### Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_command_fails` and `test_deliberate_wrong_redaction_fails` verifying that:
- Incorrect command assertions fail with `AssertionError`.
- Unredacted secret assertions fail with `AssertionError`.

## Test Run Summary

```
Ran 9 tests in 0.001s
OK
Exit code: 0
```

## Simulation Disclaimers

| Property | Local Configuration Validator | Production Server Deployer |
|---|---|---|
| Process spawning | None (`process_launched=False`) | `subprocess.Popen` / systemd / container engine |
| Secret storage | Replaced in memory with `[REDACTED]` | HashiCorp Vault / Azure Key Vault integration |
| Hardware / Network | None | Socket binding on TCP/IP interfaces |
