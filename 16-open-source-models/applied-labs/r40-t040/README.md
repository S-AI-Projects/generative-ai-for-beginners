# Applied Lab R40-T040: Open Source Models Assessment & Applied Questions

## Overview
This applied lab implements an original three-scenario worked example and applied assessment questions for Lesson 16 ("What are Open Source Models?").

## Lesson Concept Illustrated
Understanding the taxonomy of open models vs strict open source models vs proprietary models:
1. **Strict Open Source**: Models (such as AllenAI OLMo) with public weights, training datasets, training code, and evaluation metrics under approved licenses.
2. **Open Weights**: Models (such as Llama 2, Mistral) where model weights are published for local hosting, but complete training datasets and methodologies remain proprietary.
3. **Proprietary**: Models hosted exclusively behind vendor APIs without weight distribution.

## Published Decision Table
| Scenario ID | Weights Public | Dataset Public | Expected Decision | Model Category |
|-------------|----------------|----------------|-------------------|----------------|
| `scenario_normal` | True | True | `SELECT_FULL_OPEN_SOURCE` | `open_source_strict` |
| `scenario_boundary` | True | False | `SELECT_OPEN_WEIGHTS_MODEL` | `open_weights` |
| `scenario_missing_info` | None | False | `REJECT_INSUFFICIENT_SPECIFICATION` | `unknown` |

## Applied Questions
1. **Predict an Output**: When weights are downloadable but dataset is private, the model is classified as `SELECT_OPEN_WEIGHTS_MODEL`.
2. **Diagnose a Failure**: When weight status is `None`, the evaluator rejects evaluation (`REJECT_INSUFFICIENT_SPECIFICATION`) due to missing deployment specification.
3. **Choose Boundary Policy**: When strict OSI compliance is mandated, `SELECT_FULL_OPEN_SOURCE` policy is selected.

## Execution
Run unit tests:
```bash
python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t040 -p "test_*.py" -v
```
