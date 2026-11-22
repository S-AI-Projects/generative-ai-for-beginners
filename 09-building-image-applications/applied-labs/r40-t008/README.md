# Applied Lab R40-T008: Tensor-Shape Contract, Validation & Pipeline Recovery

## Overview

This lab extends [Lesson 09: Building Image Generation Applications](../../README.md) by implementing multidimensional tensor contract validation, numeric pixel range normalization, and pipeline error recovery for image generation workflows.

## Contract & Normalization Rules

1. **Tensor Shape Invariant**: Validates regular $N \times H \times W$ batches. The canonical batch `[[[0, 255], [128, 64]]]` strictly preserves shape `(1, 2, 2)`.
2. **Numeric Normalization**: Maps integer pixel values in $[0, 255]$ to floats in $[0.0, 1.0]$ via $x / 255.0$. Specifically, $0 \to 0.0$ and $255 \to 1.0$.
3. **Out-of-Bounds Rejection**: Pixels $< 0$ or $> 255$, ragged dimensions, or non-numeric types raise `TensorContractError`.
4. **Scope Note**: This lab verifies input data preprocessing and tensor shape contracts; it does **not** evaluate neural model generation quality.

## Focus: Documented Failure & Pipeline Recovery

A stateful pipeline (`BatchPreprocessingPipeline`) demonstrates resilient failure handling:
- **Step 1 (Failure)**: An invalid batch containing an out-of-bounds pixel (`-50`) is rejected with a documented `TensorContractError`.
- **Step 2 (Recovery)**: The pipeline immediately accepts and normalizes the subsequent valid batch without lingering state corruption or memory leaks.

## Scope Note (Simulation / Test Double)

This component is an offline tensor preprocessing test double using only Python's standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Canonical batch normalization
python3 09-building-image-applications/applied-labs/r40-t008/example.py --scenario normal

# Negative pixel failure
python3 09-building-image-applications/applied-labs/r40-t008/example.py --scenario negative

# Overflow pixel failure
python3 09-building-image-applications/applied-labs/r40-t008/example.py --scenario overflow

# Pipeline error and clean recovery demonstration
python3 09-building-image-applications/applied-labs/r40-t008/example.py --scenario recovery

# Canonical check
python3 09-building-image-applications/applied-labs/r40-t008/example.py --check

# Automated unit tests
python3 -m unittest discover -s 09-building-image-applications/applied-labs/r40-t008 -p "test_*.py" -v
```
