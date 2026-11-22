# R40-T011: Worked Decision Example — Open Models

## Purpose

This local example demonstrates the five information categories listed
in the lesson's "What are Open Source Models?" section:

1. Training datasets.
2. Full model weights.
3. Evaluation code.
4. Fine-tuning code.
5. Training metrics.

The lesson explains that these categories should be publicly available
for a model to align with the traditional open-source definition.
It also uses the broader term "open models" because some models do not
meet every criterion.

## Run

Prerequisite: Python 3 standard library and a local repository checkout.

Run all three scenarios:

```bash
python3 16-open-source-models/applied-labs/r40-t011/example.py
```

Run the decision checker:

```bash
python3 16-open-source-models/applied-labs/r40-t011/example.py --check
```

Run individual scenarios:

```bash
python3 16-open-source-models/applied-labs/r40-t011/example.py --scenario normal
python3 16-open-source-models/applied-labs/r40-t011/example.py --scenario boundary
python3 16-open-source-models/applied-labs/r40-t011/example.py --scenario missing
```

Run automated tests from the repository root:

```bash
python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t011 -p "test_*.py"
```

## Local fixtures and expected decisions

| Scenario | Input facts | Expected decision |
|---|---|---|
| Normal | All five categories available | `meets_checklist` |
| Boundary | Training metrics unavailable; other four available | `does_not_meet_checklist` |
| Missing information | Training metrics unknown; other four available | `cannot_determine` |

In the fixture, `True` means available, `False` means confirmed
unavailable, and `None` means unknown.

## Expected checker output

With `--check`, the program prints JSON containing all three scenarios
and `"checks_passed": true`. The process exits with status zero.

A deliberately incorrect published decision raises an assertion.
The automated tests verify this failure behavior.

## Simulation and limitations

This is a mock educational checklist using local Python dictionaries.
It does not download, inspect, train, or run an AI model. It does not
verify actual licences, dataset contents, hardware, cloud services,
model quality, or legal open-source status.

The checklist is a simplified representation of the lesson's
information categories, not a legal certification or complete
interpretation of the Open Source Initiative definition.
