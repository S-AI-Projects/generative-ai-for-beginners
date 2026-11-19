# Applied Lab (R40-T023): Worked Decision Example for "What are Open Source Models?"

This hands-on applied lab extends Lesson 16 (**What are Open Source Models?**) with a local contract fixture that models and verifies AI model openness classifications.

---

## 1. Context & Lesson Connection

In Lesson 16 ([What are Open Source Models?](../../README.md#what-are-open-source-models)), the lesson explains that while open source software has a well-established definition governed by the Open Source Initiative (OSI), Large Language Models (LLMs) present unique transparency challenges.

For an LLM to align with the traditional definition of open source, five core criteria must be publicly available:
1. **Training Datasets:** Full datasets used to train the model.
2. **Model Weights:** Full model weights as part of the training.
3. **Evaluation Code:** The reproducible evaluation code.
4. **Fine-Tuning Code:** The fine-tuning code and recipes.
5. **Training Metrics:** Full model weights and training metrics/logs.

Additionally, traditional open source requires an **OSI-approved open license**.

Currently, only a few foundation models (such as **AllenAI OLMo**) meet all these criteria. Many popular models (such as **Llama 2**, **Mistral**, and **Falcon**) release their weights and fine-tuning tooling for customization, but withhold their pre-training datasets or training metrics, or use licenses with commercial caps. The lesson terms these **"open models"** or **"open weights"** rather than traditional open source.

---

## 2. Contribution Focus: Comparing Two Approaches

This lab addresses the task focus **"Compare two approaches"** by implementing and cross-checking two independent evaluation methods on identical input facts:

1. **Approach 1 — Direct Rule Engine (`evaluate_model_direct`):**
   - Ingests structured model transparency facts.
   - Audits criteria completeness, identifying any missing or unverified fields (`None`).
   - Evaluates criteria subsets (satisfied vs. withheld).
   - Emits a rich structured evaluation dictionary containing the final decision, machine-readable `decision_code`, criteria breakdown, and an educational `rationale` grounded in Lesson 16.

2. **Approach 2 — Simpler Independent Calculation (`evaluate_model_independent`):**
   - A minimalist, independent reference calculation implementing pure boolean arithmetic over the criteria set without string generation or formatting logic.
   - Returns the baseline decision string directly.

3. **Comparison Checker (`check_decision_table`):**
   - Evaluates both approaches against a published decision table of canonical scenarios.
   - Enforces that `Approach 1 Decision == Approach 2 Decision == Table Expected Decision`.
   - Validates that the rationale contains required lesson-aligned concepts.
   - Detects deliberate tampering or configuration changes and fails with a nonzero exit code (`DecisionMismatchError`).

---

## 3. The Three Core Scenarios

| Scenario ID | Type | Exemplar | Facts Summary | Expected Decision | Rationale Highlight |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | **Normal** | AllenAI OLMo 7B | All 5 training artifacts public + OSI license | `OPEN_SOURCE` | Meets traditional open-source criteria; all datasets, weights, code, and metrics are public without restriction. |
| `SCENARIO_BOUNDARY` | **Boundary** | Llama 2 / Mistral | Weights & fine-tuning public; datasets & metrics withheld; custom license | `OPEN_WEIGHTS` | Falls on the openness boundary: weights are accessible for local use, but withheld pre-training assets classify it as an "open model" / "open weights". |
| `SCENARIO_MISSING_INFO` | **Missing Information** | Candidate Model v1 | Datasets, metrics, fine-tuning, and license fields are `None` (unverified) | `UNDETERMINED` | Essential disclosures are missing. An openness determination cannot be made without verified factual disclosures. |

---

## 4. Scope and Limitations (Simulation / Mock Scope)

- **Pure Local Fixture:** Built entirely with Python's standard library (`argparse`, `copy`, `enum`, `json`, `subprocess`, `sys`, `typing`, `unittest`).
- **Zero External Dependencies:** No `pip install`, external packages, or virtual environments required.
- **No Heavy Hardware or Cloud Costs:** Requires zero GPU memory, local model weight downloads, paid provider credentials, or network daemons.
- **Contract Boundary:** This fixture models the governance and transparency evaluation layer. It does not perform cryptographic artifact verification or inspect weight tensors on disk.

---

## 5. Usage & CLI Invocations

Run all commands from the repository root:

### 1. Run the Full Decision Table Checker (Default)

```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --check
```

**Expected Output (`exit 0`):**
```json
{
  "status": "success",
  "total_scenarios": 3,
  "passed_scenarios": 3,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "model_id": "allenai-olmo-7b-fixture",
      "expected_decision": "OPEN_SOURCE",
      "direct_decision": "OPEN_SOURCE",
      "independent_decision": "OPEN_SOURCE",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "status": "PASS"
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "model_id": "llama-2-chat-fixture",
      "expected_decision": "OPEN_WEIGHTS",
      "direct_decision": "OPEN_WEIGHTS",
      "independent_decision": "OPEN_WEIGHTS",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "status": "PASS"
    },
    {
      "scenario_id": "SCENARIO_MISSING_INFO",
      "scenario_type": "missing_information",
      "model_id": "unverified-candidate-v1",
      "expected_decision": "UNDETERMINED",
      "direct_decision": "UNDETERMINED",
      "independent_decision": "UNDETERMINED",
      "approaches_agree": true,
      "matches_table": true,
      "rationale_valid": true,
      "status": "PASS"
    }
  ]
}
```

### 2. Inspect an Individual Scenario

```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario boundary
```

### 3. Evaluate Custom Model Facts via JSON

```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --call '{
  "model_id": "my-custom-model",
  "facts": {
    "model_weights_public": true,
    "training_datasets_public": false,
    "evaluation_code_public": true,
    "fine_tuning_code_public": true,
    "training_metrics_public": false,
    "osi_approved_license": false
  }
}'
```

### 4. Verify Deliberate Failure Handling

Demonstrates that changing an expected decision immediately causes the checker to fail with exit code `1`:

```bash
python3 16-open-source-models/applied-labs/r40-t023/example.py --tamper-test
```

**Output (`exit 1`):**
```text
Executing deliberate failure verification: Tampering SCENARIO_NORMAL expected_decision to 'OPEN_WEIGHTS'...
DecisionMismatchError: Decision check failed for 'SCENARIO_NORMAL'. Expected='OPEN_WEIGHTS', Direct='OPEN_SOURCE', Independent='OPEN_SOURCE'. Keyword mismatches: []
```

---

## 6. Automated Unit Tests

Run the complete test suite via Python's standard `unittest` discovery runner:

```bash
python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t023 -p "test_*.py" -v
```
