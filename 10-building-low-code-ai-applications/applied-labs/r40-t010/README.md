# Applied Lab R40-T010: Building Low Code AI Applications — Scenario Assessment & Applied Questions

This lab extends [Lesson 10: Building Low Code AI Applications](../../README.md) with an executable scenario assessment evaluator, published decision table verification, and three applied architectural questions.

## Overview & Lesson Context

Lesson 10 introduces low-code AI development using Microsoft Power Platform (Power Apps, Power Automate, AI Builder, and Copilot Studio). A core challenge in modern enterprise AI engineering is determining **architectural fit**:
- When is a low-code approach appropriate?
- When do requirements breach platform boundaries and require custom pro-dev engineering?
- When must an architectural decision be deferred due to missing operational facts?

This lab models these trade-offs deterministically with:
1. **Three Worked Scenarios**:
   - **Normal Scenario (`S1_NORMAL`)**: Invoice Processing and Approval Flow using Power Automate, AI Builder prebuilt invoice extraction, and Dataverse.
   - **Boundary Scenario (`S2_BOUNDARY`)**: Real-time high-throughput handwritten fraud detection requiring bespoke PyTorch neural network weights, sub-50ms latency, and private isolated network hosting.
   - **Missing-Information Scenario (`S3_MISSING_INFO`)**: An underspecified student advisory chatbot proposal lacking volume projections, latency requirements, and compliance classification.
2. **Decision Table Verification**:
   - Automated checker validating evaluated decisions against the published lesson baseline.
   - Negative testing support (`--tamper`) to verify that invalid decision mutations exit non-zero.
3. **Three Applied Questions**:
   - **Question 1 (Predict Output)**: Evaluates a customer support ticket summarizer using AI Builder's "Create Text with GPT" prompt template.
   - **Question 2 (Diagnose Failure)**: Diagnoses why an incomplete proposal is rejected by governance checks.
   - **Question 3 (Choose Boundary Policy)**: Selects the appropriate governance pattern (`HYBRID_PRO_CODE_OFFLOAD`) when connector throttling occurs at scale.

---

## Published Decision Table

| Scenario ID | Name | Monthly Volume | Latency SLA | Model Type | Compliance Tier | Decision | Lesson Rationale Summary |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `S1_NORMAL` | Invoice Processing & Approval | 1,500 | 60,000 ms | Prebuilt AI Builder Invoice Model | Standard Cloud | `LOW_CODE_POWER_PLATFORM` | Prebuilt model fits requirements; throughput and SLA fall well within standard Power Automate quotas; native Dataverse integration. |
| `S2_BOUNDARY` | Exam Fraud Detection | 4,000,000 | 45 ms | Custom PyTorch Weights (Non-prebuilt) | Strict Isolated Private VPC | `CUSTOM_CODE_PRO_DEV` | Requires bespoke model weights unsupported by AI Builder; 4M monthly volume and 45ms SLA exceed connector throttling limits; mandates pro-code microservices. |
| `S3_MISSING_INFO` | Student Advisory Agent | Undefined | Undefined | Conversational Assistant | Undefined | `DEFER_INSUFFICIENT_INFORMATION` | Critical operational metrics (volume, SLA, compliance tier) are missing. Committing without sizing risks connector throttling or regulatory breach. |

---

## Applied Questions Summary

### 1. Predict an Output
- **Workload**: Customer Support Ticket Summarizer (5,000 tickets/month, 10s async SLA, prebuilt AI Builder "Create Text with GPT" model, Standard Enterprise Cloud).
- **Predicted Decision**: `LOW_CODE_POWER_PLATFORM`
- **Rationale**: The workload is well within Power Platform connector limits, fits prebuilt GPT prompt templates, and requires no custom ML infrastructure.

### 2. Diagnose a Failure
- **Workload**: Automated Course Syllabus Parser submitted without volume, latency SLA, or compliance tier.
- **Diagnostic Code**: `MISSING_OPERATIONAL_METRICS`
- **Rationale**: Low-code governance requires operational metrics to verify connector throughput limits and regulatory isolation before approving deployment.

### 3. Choose a Boundary Policy
- **Trigger**: Ingestion volume surges to 250,000 items/day, triggering HTTP 429 throttling on standard connectors.
- **Chosen Policy**: `POLICY_HYBRID_PRO_CODE_OFFLOAD`
- **Rationale**: The recommended pattern is hybrid extensibility: offload high-throughput ingestion and heavy AI processing to pro-code Azure microservices while maintaining low-code Power Apps for business user workflow management.

---

## Scope & Simulation Disclaimer

> [!NOTE]
> This lab is an offline, self-contained educational simulation and governance double.
> It uses Python 3 standard library data structures and rule-based evaluators.
> No real Power Platform tenant, Dataverse database, AI Builder credit consumption, GPU hardware, or cloud subscription is required or contacted.

---

## Execution Guide

### 1. Evaluate Scenarios
```bash
python3 example.py --scenario all
```

### 2. Verify Published Decision Table
```bash
python3 example.py --check
```

### 3. Test Negative / Tamper Failure Detection
```bash
python3 example.py --check --tamper
# Exits with status code 1 and logs decision mismatch
```

### 4. Run Applied Questions
```bash
python3 example.py --questions
```

### 5. Run All Checks with JSON Output
```bash
python3 example.py --check --questions --json
```

### 6. Run Unit Test Suite
```bash
python3 -m unittest discover -s . -p "test_*.py" -v
```
