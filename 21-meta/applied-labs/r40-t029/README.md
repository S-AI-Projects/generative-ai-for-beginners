# Applied Lab: Model Manifest Selection & Resource Constraint Evaluation (R40-T029)

## Overview & Lesson 21 Context

In [Lesson 21 — Building With the Meta Family Models](../../README.md?WT.mc_id=academic-105485-koreyst), we explore the diverse architecture, sizes, and operational capabilities across Meta's Llama model family (including Llama 3.1, 3.2, 3.3, and 4). The Meta family spans a wide spectrum of parameter scales—ranging from edge/mobile-viable models (1B, 3B) designed for local latency-sensitive execution, to mid-range models (11B, 17B, 70B), up to massive datacenter-scale foundation models (405B) requiring distributed multi-GPU clusters. Furthermore, context window capacities vary from standard 8k tokens up to 128k tokens.

In production environments, selecting which model to load or route requests to requires balancing **host resource limits** against **workload requirements**:
1. **Host Memory Constraints**: A local edge device, developer workstation, or containerized cloud host has a finite RAM/VRAM budget. A model cannot run if its minimum memory requirement exceeds the available budget.
2. **Workload Context Requirements**: An application prompt (e.g. document summarization, retrieval-augmented generation (RAG), or chat history) requires a minimum context window length. A model cannot serve the workload if its maximum context window is shorter than the requested context.
3. **Exclusion Transparency**: When models are filtered out, the orchestration system must provide structured, explainable reasons rather than opaque failure states.

This applied lab provides a self-contained, deterministic reference implementation, regression test suite, and evaluation experiment modeling host-constrained model manifest selection.

---

## Contract & Invariants

The manifest selection engine enforces four core invariants:

1. **Explicit Manifest Metadata**: Each model entry in the local synthetic manifest specifies:
   - `model_id` (str): Unique canonical identifier (e.g. `'model-a'`, `'model-b'`).
   - `min_ram_gb` (float): Minimum host memory required for weights and runtime execution.
   - `max_context_tokens` (int): Maximum supported context window length in tokens.
2. **Deterministic Constraint Satisfaction**:
   - **RAM Constraint**: A model satisfies memory limits if and only if $\text{min\_ram\_gb} \le \text{budget\_ram\_gb}$.
   - **Context Constraint**: A model satisfies context requirements if and only if $\text{max\_context\_tokens} \ge \text{requested\_context\_tokens}$.
   - A model is **admitted** if both constraints hold; otherwise, it is **excluded**.
3. **Diagnostic Exclusion Explanations**:
   - Every excluded model reports why it was disqualified, including exact numeric deficits and structured reason codes:
     - `RAM_EXCEEDS_BUDGET`: $\text{min\_ram\_gb} > \text{budget\_ram\_gb}$.
     - `INSUFFICIENT_CONTEXT`: $\text{max\_context\_tokens} < \text{requested\_context\_tokens}$.
     - `DUAL_RESOURCE_DEFICIT`: Both constraints violated simultaneously.
4. **Canonical Teaching Fixtures**:
   - **Fixture A**: `min_ram_gb = 4.0` GB, `max_context_tokens = 2048` tokens.
   - **Fixture B**: `min_ram_gb = 8.0` GB, `max_context_tokens = 4096` tokens.
   - **Canonical Workload**: `budget_ram_gb = 6.0` GB, `requested_context_tokens = 1024` tokens.
   - **Outcome**: Admits **ONLY Fixture A**. Fixture B is excluded with the diagnostic message: `RAM requirement (8.0 GB) exceeds host budget (6.0 GB) by 2.0 GB`.

---

## Classification & Scope Note (Simulation / Test Double)

> [!NOTE]
> **Simulation / Test Double Classification:**
> This lab is implemented strictly as a **deterministic local constraint-satisfaction engine and test double** using Python's standard library. It requires zero cloud credentials, no paid API keys, no weights download, and no GPU or physical hardware.
>
> **Where Simplifications Stop:**
> - Values are invented teaching fixtures designed to demonstrate resource-gated model admission logic, not empirical measurements of physical hardware or production benchmarks of Meta's Llama models.
> - Static RAM thresholds model base memory requirements without dynamic KV-cache memory growth, multi-tenant memory fragmentation, or speculative decoding overhead.
> - The component makes no claims regarding physical GPU throughput, real-world inference latency, or trained-model benchmark accuracy.

---

## Canonical Test Fixtures & Configurations

### Manifest Fixtures
- **Fixture A (`model-a`)**:
  - Name: `Synthetic Llama Edge 4B (Fixture A)`
  - RAM Required: `4.0` GB
  - Context Supported: `2048` tokens
- **Fixture B (`model-b`)**:
  - Name: `Synthetic Llama Mid 8B (Fixture B)`
  - RAM Required: `8.0` GB
  - Context Supported: `4096` tokens

### Controlled Configurations Compared in Experiment
1. **Configuration 1 (Edge / Constrained Host)**:
   - Budget: RAM = `6.0` GB, Context = `1024` tokens.
   - Outcome: Admitted `['model-a']`, Excluded `['model-b']`.
2. **Configuration 2 (Long-Context Cloud Host)**:
   - Budget: RAM = `8.0` GB, Context = `4096` tokens.
   - Outcome: Admitted `['model-b']`, Excluded `['model-a']`.
3. **Configuration 3 (Generous Workstation Host)**:
   - Budget: RAM = `16.0` GB, Context = `1024` tokens.
   - Outcome: Admitted `['model-a', 'model-b']`, Excluded `[]`.

---

## Exact Invocations and Expected Output

### 1. Normal Scenario (`--scenario normal`)

Evaluates the canonical contract: Budget RAM 6 GB, Context 1024 tokens.

```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario normal
```

Expected JSON output (`exit 0`):

```json
{
  "classification": "synthetic_model_manifest_selection_simulation",
  "decision": "SELECTIVE_ADMISSION_SUCCESS",
  "budget": {
    "budget_ram_gb": 6.0,
    "requested_context_tokens": 1024
  },
  "total_evaluated": 2,
  "admitted_count": 1,
  "excluded_count": 1,
  "admission_rate_pct": 50.0,
  "admitted_models": [
    "model-a"
  ],
  "excluded_models": [
    "model-b"
  ],
  "rationale": "Admitted 1 of 2 candidates (model-a). Excluded 1 candidates (model-b) due to resource deficits.",
  "evaluations": [
    {
      "model_id": "model-a",
      "name": "Synthetic Llama Edge 4B (Fixture A)",
      "eligible": true,
      "min_ram_gb": 4.0,
      "budget_ram_gb": 6.0,
      "ram_slack_gb": 2.0,
      "max_context_tokens": 2048,
      "requested_context_tokens": 1024,
      "context_headroom_tokens": 1024,
      "exclusion_reasons": [],
      "reason_codes": []
    },
    {
      "model_id": "model-b",
      "name": "Synthetic Llama Mid 8B (Fixture B)",
      "eligible": false,
      "min_ram_gb": 8.0,
      "budget_ram_gb": 6.0,
      "ram_slack_gb": -2.0,
      "max_context_tokens": 4096,
      "requested_context_tokens": 1024,
      "context_headroom_tokens": 3072,
      "exclusion_reasons": [
        "RAM requirement (8.0 GB) exceeds host budget (6.0 GB) by 2.0 GB"
      ],
      "reason_codes": [
        "RAM_EXCEEDS_BUDGET"
      ]
    }
  ]
}
```

---

### 2. Boundary Scenario (`--scenario boundary`)

Evaluates exact threshold boundary equality (RAM = 4.0 GB, Context = 2048 tokens) and step-off deficit (RAM = 3.9 GB).

```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario boundary
```

Expected JSON output (`exit 0`):

```json
{
  "classification": "boundary_threshold_evaluation_simulation",
  "decision": "BOUNDARY_VERIFICATION_SUCCESS",
  "case_exact_equality": {
    "budget": {
      "budget_ram_gb": 4.0,
      "requested_context_tokens": 2048
    },
    "admitted_models": [
      "model-a"
    ],
    "fixture_a_ram_slack_gb": 0.0,
    "fixture_a_context_headroom_tokens": 0,
    "boundary_status": "EXACT_MATCH_ADMITTED"
  },
  "case_stepoff_deficit": {
    "budget": {
      "budget_ram_gb": 3.9,
      "requested_context_tokens": 2048
    },
    "admitted_models": [],
    "stepoff_status": "THRESHOLD_VIOLATION_EXCLUDED"
  }
}
```

---

### 3. Failure & Validation Scenario (`--scenario failure`)

Exercises documented invalid host resource budgets (negative RAM, zero context) and malformed manifest schemas.

```bash
python3 21-meta/applied-labs/r40-t029/example.py --scenario failure
```

Expected JSON output (`exit 0`):

```json
{
  "classification": "input_validation_failure_simulation",
  "decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
  "errors_validated_count": 3,
  "errors": [
    {
      "error_type": "InvalidResourceBudgetError",
      "message": "Host RAM budget must be strictly positive (> 0), got: -2.0 GB",
      "test_case": "negative_ram_budget"
    },
    {
      "error_type": "InvalidResourceBudgetError",
      "message": "Requested context length must be strictly positive (> 0 tokens), got: 0",
      "test_case": "zero_context_tokens"
    },
    {
      "error_type": "MalformedManifestError",
      "message": "Duplicate model_id detected in manifest: 'model-a'",
      "test_case": "duplicate_model_id"
    }
  ]
}
```

---

### 4. Evaluation Experiment (`--experiment`)

Compares three controlled host configurations across admission selectivity, resource slack, and primary bottleneck distributions.

```bash
python3 21-meta/applied-labs/r40-t029/example.py --experiment
```

Expected JSON output (`exit 0`):

```json
{
  "classification": "model_selection_evaluation_experiment",
  "decision": "EXPERIMENT_EVALUATION_SUCCESS",
  "total_configs_compared": 3,
  "all_configs_correct": true,
  "configurations": [
    {
      "config_id": "CONFIG_1_EDGE_CONSTRAINED",
      "name": "Edge / Resource-Constrained Host",
      "target_use_case": "Local desktop or edge device running single-tenant inference.",
      "budget": {
        "budget_ram_gb": 6.0,
        "requested_context_tokens": 1024
      },
      "total_candidates": 2,
      "admitted_models": ["model-a"],
      "excluded_models": ["model-b"],
      "admission_rate_pct": 50.0,
      "metrics": {
        "admitted_count": 1,
        "excluded_count": 1,
        "avg_ram_slack_gb": 2.0,
        "avg_context_headroom_tokens": 1024.0,
        "primary_bottleneck": "RAM_CAPACITY"
      },
      "correctness_verified": true
    },
    {
      "config_id": "CONFIG_2_LONG_CONTEXT_CLOUD",
      "name": "Long-Context Cloud Host",
      "target_use_case": "Cloud instance optimized for long-document RAG and large context.",
      "budget": {
        "budget_ram_gb": 8.0,
        "requested_context_tokens": 4096
      },
      "total_candidates": 2,
      "admitted_models": ["model-b"],
      "excluded_models": ["model-a"],
      "admission_rate_pct": 50.0,
      "metrics": {
        "admitted_count": 1,
        "excluded_count": 1,
        "avg_ram_slack_gb": 0.0,
        "avg_context_headroom_tokens": 0.0,
        "primary_bottleneck": "CONTEXT_WINDOW_LIMIT"
      },
      "correctness_verified": true
    },
    {
      "config_id": "CONFIG_3_WORKSTATION_EXPANSIVE",
      "name": "Generous Workstation Host",
      "target_use_case": "High-memory developer workstation supporting concurrent models.",
      "budget": {
        "budget_ram_gb": 16.0,
        "requested_context_tokens": 1024
      },
      "total_candidates": 2,
      "admitted_models": ["model-a", "model-b"],
      "excluded_models": [],
      "admission_rate_pct": 100.0,
      "metrics": {
        "admitted_count": 2,
        "excluded_count": 0,
        "avg_ram_slack_gb": 10.0,
        "avg_context_headroom_tokens": 2048.0,
        "primary_bottleneck": "NONE_UNCONSTRAINED"
      },
      "correctness_verified": true
    }
  ],
  "trade_off_analysis": {
    "finding": "Host selection involves an explicit architectural trade-off between deployment footprint and operational workload flexibility.",
    "edge_tradeoff": "Config 1 (Edge) minimizes hardware allocation to 6 GB, admitting only Fixture A. It yields +2.0 GB memory buffer safety margin, but rejects workloads requiring longer contexts (>2048).",
    "cloud_tradeoff": "Config 2 (Long-Context) unlocks 4096-token support via Fixture B, but consumes 100% of the 8 GB budget (0.0 GB RAM slack), eliminating safety buffers for memory spikes.",
    "workstation_tradeoff": "Config 3 (Workstation) achieves 100% admission rate and maximum model failover options (+10.0 GB avg slack), but requires high hardware over-provisioning (16 GB RAM) for small 1024-token requests.",
    "no_accuracy_claim_disclaimer": "Metrics reflect resource constraint satisfaction and filtering trade-offs on synthetic teaching fixtures; no claims are made regarding physical GPU throughput or real-world model accuracy."
  }
}
```

---

### 5. Canonical Check (`--check`)

Validates the full decision table across all scenarios.

```bash
python3 21-meta/applied-labs/r40-t029/example.py --check
```

---

### 6. Deliberate Tamper Test (`--tamper`)

Injects a deliberate defect into the expectation to verify regression sensitivity.

```bash
python3 21-meta/applied-labs/r40-t029/example.py --tamper
```

Expected output (`exit 1` on stderr):

```json
{
  "status": "expected_tamper_failure",
  "error_type": "DecisionMismatchError",
  "error_message": "Deliberate tamper test triggered: Injected expectation that Fixture B is admitted under RAM 6 GB.",
  "exit_code": 1
}
```

---

## Test Execution

Run the complete automated unit test suite:

```bash
python3 -m unittest discover -s 21-meta/applied-labs/r40-t029 -p "test_*.py" -v
```
