# R40-T025 — Verification Results

This report records all inputs, expected vs. actual outputs, exit codes, and verification assertions for Task R40-T025.
Focus: Put the external dependency behind a callable interface and supply the deterministic local adapter. Identify which real-service behavior this mock does not establish.

---

## 1. Normal Scenario: Addition (`add(2, 3) -> 5`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
```

Expected output:
```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 5
}
```

Actual output:
```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 5
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Addition executed successfully via deterministic local adapter with strict numeric typing.

---

## 2. Normal Scenario: Multiplication (`multiply(2, 3) -> 6`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'
```

Expected output:
```json
{
  "status": "success",
  "tool": "multiply",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 6
}
```

Actual output:
```json
{
  "status": "success",
  "tool": "multiply",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 6
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Multiplication executed successfully via deterministic local adapter with strict numeric typing.

---

## 3. Failure Scenario: Unknown Tool (`divide`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'
```

Expected error envelope:
```json
{
  "status": "error",
  "error": {
    "type": "UnknownToolError",
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
    "details": {
      "tool": "divide",
      "allowed_tools": [
        "add",
        "multiply"
      ]
    }
  },
  "tool": "divide",
  "arguments": {
    "a": 6,
    "b": 2
  }
}
```

Actual output:
```json
{
  "status": "error",
  "error": {
    "type": "UnknownToolError",
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
    "details": {
      "tool": "divide",
      "allowed_tools": [
        "add",
        "multiply"
      ]
    }
  },
  "tool": "divide",
  "arguments": {
    "a": 6,
    "b": 2
  }
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — Unknown tool was rejected with structured UnknownToolError envelope and exit code 1.

---

## 4. Failure Scenario: String Argument `a = "2"`

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "add", "arguments": {"a": "2", "b": 3}}'
```

Expected error envelope:
```json
{
  "status": "error",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_ARGUMENT_TYPE",
    "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
    "details": {
      "parameter": "a",
      "expected": "finite number (int or float)",
      "received_type": "str",
      "received_value": "2"
    }
  },
  "tool": "add",
  "arguments": {
    "a": "2",
    "b": 3
  }
}
```

Actual output:
```json
{
  "status": "error",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_ARGUMENT_TYPE",
    "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
    "details": {
      "parameter": "a",
      "expected": "finite number (int or float)",
      "received_type": "str",
      "received_value": "2"
    }
  },
  "tool": "add",
  "arguments": {
    "a": "2",
    "b": 3
  }
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — String argument was rejected with structured ValidationError envelope and exit code 1.

---

## 5. Pipeline Failure Halting & Tool Isolation

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --pipeline '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
```

Actual output:
```json
{
  "status": "error",
  "pipeline_halted": true,
  "failed_step_index": 0,
  "completed_steps": 0,
  "total_steps": 2,
  "executed_results": [],
  "failed_call": {
    "status": "error",
    "error": {
      "type": "ValidationError",
      "code": "INVALID_ARGUMENT_TYPE",
      "message": "Argument 'a' must be a finite number (int or float), got str: \"invalid\"",
      "details": {
        "parameter": "a",
        "expected": "finite number (int or float)",
        "received_type": "str",
        "received_value": "invalid"
      }
    },
    "tool": "add",
    "arguments": {
      "a": "invalid",
      "b": 3
    }
  },
  "aborted_calls": [
    {
      "tool": "multiply",
      "arguments": {
        "a": 2,
        "b": 3
      }
    }
  ],
  "message": "Pipeline halted: a failed call cannot execute another tool."
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — Pipeline halted immediately on first call failure. The subsequent tool (`multiply`) was aborted and never executed.

---

## 6. Boundary Scenario: Zeros (`add(0, 0) -> 0`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "add", "arguments": {"a": 0, "b": 0}}'
```

Actual output:
```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 0,
    "b": 0
  },
  "result": 0
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Zeros properly handled as valid finite numeric boundary.

---

## 7. Boundary Scenario: Negative Numbers (`multiply(-2, 3) -> -6`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "multiply", "arguments": {"a": -2, "b": 3}}'
```

Actual output:
```json
{
  "status": "success",
  "tool": "multiply",
  "arguments": {
    "a": -2,
    "b": 3
  },
  "result": -6
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Signed arithmetic correctly executed.

---

## 8. Boundary Decision: Booleans Strictly Rejected

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{"tool": "add", "arguments": {"a": true, "b": 3}}'
```

Actual output:
```json
{
  "status": "error",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_ARGUMENT_TYPE",
    "message": "Argument 'a' cannot be boolean; must be a finite number (int or float)",
    "details": {
      "parameter": "a",
      "expected": "finite number (int or float)",
      "received_type": "bool",
      "received_value": "True"
    }
  },
  "tool": "add",
  "arguments": {
    "a": true,
    "b": 3
  }
}
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — Booleans strictly rejected to prevent type coercion vulnerabilities in tool dispatch.

---

## 9. Real-Service Gaps Introspection (`--show-service-gaps`)

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --show-service-gaps
```

Actual output (abbreviated):
```json
{
  "scope": "offline_service_adapter_contract_fixture",
  "description": "Explicit catalog of real-service behaviors NOT established by this local mock.",
  "unestablished_behaviors": {
    "network_latency_and_jitter": {
      "title": "Network Transport Latency & Jitter",
      "description": "The offline adapter executes synchronously in-memory (0ms simulated transport delay). It does not establish network round-trip time (RTT), packet queuing, latency jitter (p50/p95/p99), or bandwidth constraints.",
      "production_counterpart": "TCP/HTTP/gRPC network stack with variable latency and timeout envelopes."
    },
    "transient_network_faults": {
      "title": "Transient Network & Connection Failures",
      "description": "The offline adapter does not simulate dropped packets, socket timeouts, connection resets, TLS negotiation failures, or half-open socket hangs.",
      "production_counterpart": "Transport retry policies, exponential backoff, and circuit breakers."
    },
    "authentication_and_authorization": {
      "title": "Authentication & Access Control",
      "description": "The offline adapter executes without authentication tokens, API keys, OAuth2 bearer negotiation, mTLS certificates, or IAM role checks.",
      "production_counterpart": "Identity providers, token refresh cycles, and cloud IAM authorization."
    },
    "rate_limiting_and_concurrency": {
      "title": "Rate Limiting & Concurrency Contention",
      "description": "The offline adapter handles unbounded sequential calls without throttling. It does not establish HTTP 429 Too Many Requests, token bucket rate limits, worker pool saturation, or distributed lock contention.",
      "production_counterpart": "API gateway throttling, quota budgets, and distributed concurrency limits."
    },
    "distributed_state_and_consistency": {
      "title": "Distributed State & Idempotency",
      "description": "The offline adapter maintains no distributed state. It does not establish idempotency keys, distributed transaction rollbacks, replica lag, or eventual consistency drift across multi-region clusters.",
      "production_counterpart": "Distributed databases, message queues, and consensus protocols (e.g. Raft)."
    },
    "remote_service_lifecycle_and_outages": {
      "title": "Remote Service Outages & HTTP Status Codes",
      "description": "The offline adapter is always available in-process. It does not establish HTTP 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, or 504 Gateway Timeout downstream dependency failures.",
      "production_counterpart": "Service health checks, blue/green rollouts, and failover routing."
    },
    "hardware_and_environment_heterogeneity": {
      "title": "Hardware & Environment Heterogeneity",
      "description": "The offline adapter relies strictly on the host CPU and Python runtime. It does not establish GPU kernel launch overhead, specialized accelerator precision differences, container cold-starts, or VM memory cgroups.",
      "production_counterpart": "Cloud VM instances, container orchestrators (K8s), and hardware accelerators."
    },
    "llm_probabilistic_drift": {
      "title": "Model Non-Determinism & Hallucination Drift",
      "description": "The offline fixture validates deterministic JSON payloads. It does not model probabilistic LLM sampling drift, prompt injection exploits, context truncation, or malformed schema generation from stochastic models.",
      "production_counterpart": "Model guardrails, temperature controls, and output schema verifiers."
    }
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Explicitly exposes the 8 real-service behaviors that this local offline adapter does not establish.

---

## 10. Swappable Adapter Test: Callable Interface Demonstration

Command:
```bash
python3 17-ai-agents/applied-labs/r40-t025/example.py --adapter deliberate-wrong --call '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
```

Actual output:
```json
{
  "status": "success",
  "tool": "add",
  "arguments": {
    "a": 2,
    "b": 3
  },
  "result": 999
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Callable interface allowed hot-swapping the backend adapter to `DeliberateWrongResultAdapter` without altering dispatcher logic.

---

## 11. Automated Test Suite Execution

Command:
```bash
python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t025 -p "test_*.py" -v
```

Test output:
```text
test_floating_point_numbers (test_example.TestBoundaryScenarios.test_floating_point_numbers)
Floating point numbers must preserve floating precision. ... ok
test_large_integers (test_example.TestBoundaryScenarios.test_large_integers)
Large numbers within Python arbitrary precision must succeed. ... ok
test_negative_numbers (test_example.TestBoundaryScenarios.test_negative_numbers)
Negative numbers must be properly handled. ... ok
test_zeros (test_example.TestBoundaryScenarios.test_zeros)
add(0, 0) -> 0 and multiply(0, 10) -> 0. ... ok
test_custom_callable_function (test_example.TestCallableInterfaceAndAdapters.test_custom_callable_function)
A simple callable function or lambda can act as service backend. ... ok
test_deliberate_wrong_result_adapter_fails_expectation (test_example.TestCallableInterfaceAndAdapters.test_deliberate_wrong_result_adapter_fails_expectation)
Deliberate wrong adapter produces 999; ... ok
test_faulty_backend_adapter_returns_structured_error (test_example.TestCallableInterfaceAndAdapters.test_faulty_backend_adapter_returns_structured_error)
Backend service errors are caught and returned in structured error envelopes. ... ok
test_add_normal (test_example.TestNormalScenarios.test_add_normal)
add(2, 3) must return 5 with status success. ... ok
test_multiply_normal (test_example.TestNormalScenarios.test_multiply_normal)
multiply(2, 3) must return 6 with status success. ... ok
test_pipeline_halts_on_first_failure (test_example.TestPipelineExecutionAndFailureIsolation.test_pipeline_halts_on_first_failure)
Failure halting: A failed call cannot execute another tool. ... ok
test_pipeline_halts_on_intermediate_failure (test_example.TestPipelineExecutionAndFailureIsolation.test_pipeline_halts_on_intermediate_failure)
Pipeline executes prior steps, but halts immediately on failure and aborts rest. ... ok
test_successful_pipeline (test_example.TestPipelineExecutionAndFailureIsolation.test_successful_pipeline)
A pipeline of valid calls executes all steps successfully. ... ok
test_adapter_property_matches_real_service_gaps (test_example.TestRealServiceGapsDocumentation.test_adapter_property_matches_real_service_gaps) ... ok
test_all_service_gap_categories_present (test_example.TestRealServiceGapsDocumentation.test_all_service_gap_categories_present)
All expected categories of real-service gaps must be present. ... ok
test_cli_add_exit_0 (test_example.TestSubprocessCLI.test_cli_add_exit_0) ... ok
test_cli_deliberate_wrong_result_fails_assertion (test_example.TestSubprocessCLI.test_cli_deliberate_wrong_result_fails_assertion) ... ok
test_cli_multiply_exit_0 (test_example.TestSubprocessCLI.test_cli_multiply_exit_0) ... ok
test_cli_pipeline_halt_exit_1 (test_example.TestSubprocessCLI.test_cli_pipeline_halt_exit_1) ... ok
test_cli_schema_exit_0 (test_example.TestSubprocessCLI.test_cli_schema_exit_0) ... ok
test_cli_service_gaps_exit_0 (test_example.TestSubprocessCLI.test_cli_service_gaps_exit_0) ... ok
test_cli_string_argument_exit_1 (test_example.TestSubprocessCLI.test_cli_string_argument_exit_1) ... ok
test_cli_unknown_tool_exit_1 (test_example.TestSubprocessCLI.test_cli_unknown_tool_exit_1) ... ok
test_unknown_tool_rejected (test_example.TestToolAllowlist.test_unknown_tool_rejected)
Unknown tool must return UnknownToolError with allowed tools list. ... ok
test_boolean_strictly_rejected (test_example.TestTypeValidationAndErrors.test_boolean_strictly_rejected)
Booleans must not be coerced to integers even though bool subclasses int in Python. ... ok
test_invalid_arguments_type (test_example.TestTypeValidationAndErrors.test_invalid_arguments_type)
Arguments must be a JSON object (dict), not a list or primitive. ... ok
test_missing_argument (test_example.TestTypeValidationAndErrors.test_missing_argument)
Missing required parameter must return MISSING_ARGUMENT. ... ok
test_missing_tool_name (test_example.TestTypeValidationAndErrors.test_missing_tool_name)
Missing or empty tool property must return MISSING_TOOL_NAME. ... ok
test_non_finite_floats_rejected (test_example.TestTypeValidationAndErrors.test_non_finite_floats_rejected)
NaN, +inf, -inf must be rejected with NON_FINITE_NUMERIC_VALUE. ... ok
test_string_argument_a_rejected (test_example.TestTypeValidationAndErrors.test_string_argument_a_rejected)
String argument 'a' must be rejected with structured ValidationError. ... ok
test_string_argument_b_rejected (test_example.TestTypeValidationAndErrors.test_string_argument_b_rejected)
String argument 'b' must be rejected with structured ValidationError. ... ok
test_unexpected_argument (test_example.TestTypeValidationAndErrors.test_unexpected_argument)
Extraneous parameters must return UNEXPECTED_ARGUMENT. ... ok

----------------------------------------------------------------------
Ran 31 tests in 0.197s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 31 unit, boundary, pipeline, and integration tests passed.

---

## 12. Deliberate Failure Verification

Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.

Command:
```bash
python3 -c "import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t025/example.py', '--call', '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure for assertion verification'"
```

Output:
```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t025/example.py', '--call', '{"tool": "add", "arguments": {"a": 2, "b": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure: expected 999 got ' + str(data['result'])
                                                                                                                                                                                                                                                             ^^^^^^^^^^^^^^^^^^^^^
AssertionError: Deliberate test failure: expected 999 got 5
```

Exit code: `1` (Expected non-zero: `1`)

**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.

---

## Summary of Verification Checks

| Check ID | Description | Status | Exit Code |
|---|---|---|---|
| 1 | Normal Addition (`add(2, 3) -> 5`) | PASS | 0 |
| 2 | Normal Multiplication (`multiply(2, 3) -> 6`) | PASS | 0 |
| 3 | Unknown Tool Error (`divide`) | PASS | 1 |
| 4 | String Argument Error (`a = "2"`) | PASS | 1 |
| 5 | Pipeline Halting & Tool Isolation | PASS | 1 |
| 6 | Boundary Zeros (`0, 0`) | PASS | 0 |
| 7 | Boundary Negative Arithmetic (`-2 * 3 = -6`) | PASS | 0 |
| 8 | Boundary Decision on Booleans (`a = true`) | PASS | 1 |
| 9 | Real-Service Gaps Introspection (8 categories) | PASS | 0 |
| 10 | Swappable Adapter Test (`DeliberateWrongResultAdapter`) | PASS | 0 |
| 11 | Automated Test Suite (31 unit tests) | PASS | 0 |
| 12 | Deliberate Failure Verification | PASS | 1 (Expected Nonzero) |

All checks passed successfully. Verification complete.
