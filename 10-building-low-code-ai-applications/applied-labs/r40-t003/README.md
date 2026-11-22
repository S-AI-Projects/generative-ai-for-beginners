# Applied Lab R40-T003: Low-Code AI Decision Evaluator (Dual-Approach Comparison)

## Overview

This lab extends [Lesson 10: Building Low Code AI Applications](../../README.md) by implementing a worked decision framework to evaluate enterprise AI architecture decisions: choosing between Low-Code AI platforms (Microsoft Power Platform, AI Builder, Copilot Studio) and Custom Pro-Code Development.

## Scenarios & Decision Table

| Scenario | Architectural Facts | Decision | Lesson Rationale |
|---|---|---|---|
| **Normal** | Standard invoice document processing, prebuilt AI Builder model, Dataverse storage, 5 RPS, 2-week delivery | `LOW_CODE_POWER_PLATFORM` | Prebuilt models and low-code connectors deliver solution rapidly without dedicated AI infrastructure. |
| **Boundary** | 15,000 RPS, custom model weights, air-gapped on-premises compliance | `CUSTOM_CODE_PRO_DEV` | Exceeds multi-tenant low-code platform boundaries; requires custom containerized service. |
| **Missing Info** | Customer feedback analysis with unknown throughput, unspecified data source, unassigned compliance tier | `DEFER_INSUFFICIENT_INFORMATION` | Incomplete architectural specifications require additional discovery before committing to platform. |

## Focus: Dual-Approach Comparison

The module implements and evaluates two independent approaches on identical inputs:
1. **Direct Procedural Rule Engine (`evaluate_decision_direct`)**: Evaluates input facts step-by-step through procedural logic.
2. **Reference Matrix Calculation (`evaluate_decision_reference`)**: Implements an independent constraint satisfaction calculation.

Both approaches are verified to produce 100% equivalent decisions and rationale strings across all scenarios.

## Scope Note (Simulation / Test Double)

This component is an offline decision engine using only Python's standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Individual scenarios
python3 10-building-low-code-ai-applications/applied-labs/r40-t003/example.py --scenario normal
python3 10-building-low-code-ai-applications/applied-labs/r40-t003/example.py --scenario boundary
python3 10-building-low-code-ai-applications/applied-labs/r40-t003/example.py --scenario missing

# Compare dual approaches & run canonical check
python3 10-building-low-code-ai-applications/applied-labs/r40-t003/example.py --compare

# Automated unit tests
python3 -m unittest discover -s 10-building-low-code-ai-applications/applied-labs/r40-t003 -p "test_*.py" -v
```
