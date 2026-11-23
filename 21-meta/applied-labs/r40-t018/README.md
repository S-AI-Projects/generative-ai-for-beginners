# R40-T018: Model Manifest Selection

## Goal

Learn how to select eligible model entries from a local manifest using
explicit RAM and context requirements.

This lab also demonstrates how to handle missing metadata and continue
processing valid entries.

## Requirements

- Python 3
- Python standard library only
- No model downloads, external services, or GPU required

## Synthetic manifest

The lab uses invented teaching fixtures, not specifications for real models.

| Model | RAM | Context |
|---|---:|---:|
| Model A | 4 | 2048 |
| Model B | 8 | 4096 |
| Model C | Missing | 1024 |

## Selection rules

An entry is eligible when:

- RAM data is present and valid.
- Context data is present and valid.
- RAM does not exceed the available budget.
- Context meets or exceeds the requested context.

Invalid or unsuitable entries are excluded with an explanation.

## Run the examples

From the repository root:

```bash
python3 21-meta/applied-labs/r40-t018/example.py normal
python3 21-meta/applied-labs/r40-t018/example.py boundary
python3 21-meta/applied-labs/r40-t018/example.py failure
