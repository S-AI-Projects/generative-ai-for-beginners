# Applied Lab R40-T034: Low-Code AI Flow State Trace & Invariants

## Overview
This applied lab demonstrates a three-step automated low-code flow pipeline (inspired by Power Automate and AI Builder) for Lesson 10 ("Building Low Code AI Applications"). It records the full intermediate state transition trace across each step and tests the invariant connecting intermediate states to the final routing decision.

## Lesson Concept Illustrated
Low-code workflow design relies on chaining discrete modular steps:
1. **Ingestion**: Normalizes incoming payload parameters (ID, text, department, urgency).
2. **AI Enrichment**: Analyzes content for severity and identifies missing context.
3. **Decision Gate**: Applies routing rules to assign tickets to appropriate queues.

## Recorded Intermediate States & Invariants
- Each execution records: `INGESTION` -> `AI_ENRICHMENT` -> `DECISION_GATE`.
- The formal invariant verifies that:
  - Exactly 3 sequential steps are executed.
  - Final output values strictly match the `DECISION_GATE` state.
  - Incomplete inputs with missing fields deterministically yield `REQUEST_MISSING_DETAILS`.

## Published Decision Table
| Scenario ID | Department | Urgency | Expected Decision | Routing Queue |
|-------------|------------|---------|-------------------|---------------|
| `scenario_normal` | IT Support | True | `ROUTE_HIGH_PRIORITY_INCIDENT` | `emergency_oncall` |
| `scenario_boundary` | Billing | False | `ROUTE_STANDARD_TRIAGE` | `standard_support` |
| `scenario_missing_info` | (empty) | False | `REQUEST_MISSING_DETAILS` | `clarification_prompt` |

## Execution
Run unit tests:
```bash
python3 -m unittest discover -s 10-building-low-code-ai-applications/applied-labs/r40-t034 -p "test_*.py" -v
```
