# Applied Lab R40-T031: Text Generation Decision Preflight

## Overview
This applied lab implements an original three-scenario worked example and decision preflight checker for Lesson 06 ("Building Text Generation Applications").

## Lesson Concept Illustrated
In text generation apps, configuring parameters (`temperature`, `max_tokens`) and pre-validating input prompts against budget limits are essential:
1. **Normal Scenario**: Factual/summarization requests require low temperature (e.g. 0.2) and bounded token caps to maintain consistency.
2. **Boundary Scenario**: When available token budget is close to minimum required tokens, the application must constrain generation limits to avoid budget overrun.
3. **Missing-Information Scenario**: Blank or whitespace-only prompts must be intercepted before triggering model completion calls.

## Scope & Limitations
- **Tokenization**: Uses a teaching approximation (whitespace word splitting), not real BPE / tiktoken tokenizers.
- **Environment**: Pure Python 3 standard library; no external dependencies, API keys, or GPU hardware required.

## Published Decision Table
| Scenario ID | Task Type | Budget | Expected Decision | Expected Status |
|-------------|-----------|--------|-------------------|-----------------|
| `scenario_normal` | summarization | 500 | `EXECUTE_DETERMINISTIC` | `READY` |
| `scenario_boundary` | creative | 35 | `CONSTRAIN_BUDGET_EXECUTE` | `BUDGET_CONSTRAINED` |
| `scenario_missing_info` | summarization | 200 | `REJECT_MISSING_PROMPT` | `ERROR_MISSING_PROMPT` |

## Execution
Run unit tests:
```bash
python3 -m unittest discover -s 06-text-generation-apps/applied-labs/r40-t031 -p "test_*.py" -v
```
