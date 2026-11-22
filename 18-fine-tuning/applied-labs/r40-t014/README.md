
# R40-T014: Trainable-Parameter Accounting

## Goal

Demonstrate how a prefix-based freeze rule separates frozen and trainable parameters using a small local parameter manifest.

This is a mock simulation. It does not load or train a real language model.

## Prerequisites

- Python 3
- Python standard library
- A local repository checkout

No model download, GPU, paid provider, or physical device is required.

## Input fixture

```python
{
    "encoder.weight": 100,
    "head.weight": 20
}
```

Freeze prefix: `encoder`

Expected result:

- Total parameters: 120
- Frozen parameters: 100
- Trainable parameters: 20
- Unmatched prefix: false

## Run the example

From the repository root:

```bash
python3 18-fine-tuning/applied-labs/r40-t014/example.py
```

## Other scenarios

Boundary scenario:

```bash
python3 18-fine-tuning/applied-labs/r40-t014/example.py --scenario boundary
```

Expected: total=2, frozen=1, trainable=1.

Unmatched prefix:

```bash
python3 18-fine-tuning/applied-labs/r40-t014/example.py --scenario unmatched
```

Expected: total=120, frozen=0, trainable=120, unmatched_prefix=true.

## State trace and invariant

The example records three intermediate states:

1. Read the parameter manifest and calculate the total.
2. Apply the freeze prefix and calculate frozen parameters.
3. Calculate trainable parameters.

The invariant is:

`total = frozen + trainable`

The trace is checked against the final output by the automated tests.

## Run tests

From the repository root:

```bash
python3 -m unittest discover -s 18-fine-tuning/applied-labs/r40-t014 -p "test_*.py" -v
```

The tests cover normal, boundary, unmatched-prefix, invalid-input, fresh-process, and incorrect-expected-result checks.

## Limitations

This example uses integer counts in a local mock manifest. It does not inspect actual model tensors, configure a training framework, perform optimization, or measure model performance.

A prefix match only demonstrates this example's local freeze rule. It does not prove that a real model has been frozen correctly.

