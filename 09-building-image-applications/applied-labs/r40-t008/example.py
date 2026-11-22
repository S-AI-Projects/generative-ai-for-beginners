#!/usr/bin/env python3
"""Tensor-Shape Contract, Validation & Pipeline Recovery Example (R40-T008).

Lesson 09: Building Image Generation Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements tensor shape contract validation and numerical preprocessing
for synthetic image generation pipelines. In generative image workflows (e.g. DALL-E,
Stable Diffusion, or custom diffusion pipelines), input and output tensors must strictly
conform to multidimensional shape contracts (N×H×W or N×C×H×W) and valid numeric pixel
ranges before passing into neural inference graphs.

Contract Rules:
1. Shape Invariant:
   - Accepts a batch of shape N×H×W (Batch Size × Height × Width).
   - Canonical fixture: [[[0, 255], [128, 64]]] has shape (1, 2, 2).
   - Normalization preserves the exact batch shape (1, 2, 2).
2. Numeric Normalization:
   - Input integer/float pixels in 0..255 are mapped to floating point values in 0.0..1.0
     via the deterministic linear transformation x / 255.0.
   - Specifically: 0 -> 0.0, 255 -> 1.0, 128 -> 128/255, 64 -> 64/255.
3. Out-of-Bounds Rejection:
   - Any pixel < 0 or > 255 raises TensorContractError.
   - Non-numeric elements or ragged/non-rectangular dimensions raise TensorContractError.
4. Preprocessing Scope:
   - Verifies input data preprocessing and shape guarantees; does NOT evaluate model quality.
5. Focus (Failure and Pipeline Recovery):
   - Demonstrates a documented invalid case (negative pixel value), captures the detailed
     failure explanation, and demonstrates clean recovery on the subsequent valid batch.

Classification & Scope Note (Simulation / Test Double):
This module is strictly an offline tensor preprocessing test double implemented in
standard Python. It requires no PyTorch, TensorFlow, GPU acceleration, or cloud API keys.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

DEFAULT_BATCH = [[[0, 255], [128, 64]]]  # Shape (1, 2, 2)


class TensorContractError(Exception):
    """Raised when an input batch violates tensor shape or numeric range contracts."""


class DecisionMismatchError(Exception):
    """Raised when verification assertions fail."""


def inspect_batch_shape(batch: Any) -> Tuple[int, int, int]:
    """Validates that batch is a regular 3D tensor of shape N×H×W and returns dimensions."""
    if not isinstance(batch, list) or len(batch) == 0:
        raise TensorContractError("Batch must be a non-empty list representing N dimensions.")

    n = len(batch)

    # Validate H dimension
    for i, img in enumerate(batch):
        if not isinstance(img, list) or len(img) == 0:
            raise TensorContractError(f"Image at index {i} must be a non-empty 2D row list.")

    h = len(batch[0])
    for i, img in enumerate(batch):
        if len(img) != h:
            raise TensorContractError(
                f"Ragged height detected: image {i} has height {len(img)}, expected {h}."
            )

    # Validate W dimension
    for i, img in enumerate(batch):
        for j, row in enumerate(img):
            if not isinstance(row, list) or len(row) == 0:
                raise TensorContractError(f"Row at image {i}, row {j} must be a non-empty pixel list.")

    w = len(batch[0][0])
    for i, img in enumerate(batch):
        for j, row in enumerate(img):
            if len(row) != w:
                raise TensorContractError(
                    f"Ragged width detected: image {i}, row {j} has width {len(row)}, expected {w}."
                )

    return (n, h, w)


def validate_and_normalize_batch(
    batch: List[List[List[Union[int, float]]]]
) -> Tuple[List[List[List[float]]], Tuple[int, int, int]]:
    """Validates pixel ranges and normalizes N×H×W tensor pixels from [0, 255] to [0.0, 1.0]."""
    shape = inspect_batch_shape(batch)
    n, h, w = shape

    normalized: List[List[List[float]]] = []

    for i in range(n):
        norm_img: List[List[float]] = []
        for j in range(h):
            norm_row: List[float] = []
            for k in range(w):
                pixel = batch[i][j][k]
                if not isinstance(pixel, (int, float)) or isinstance(pixel, bool):
                    raise TensorContractError(
                        f"Invalid non-numeric pixel at ({i},{j},{k}): {pixel!r}"
                    )
                if pixel < 0 or pixel > 255:
                    raise TensorContractError(
                        f"Pixel value {pixel} at ({i},{j},{k}) out of bounds [0, 255]."
                    )
                # Normalize 0..255 -> 0.0..1.0
                norm_val = round(pixel / 255.0, 6)
                norm_row.append(norm_val)
            norm_img.append(norm_row)
        normalized.append(norm_img)

    return normalized, shape


class BatchPreprocessingPipeline:
    """Stateful batch processor tracking execution history and demonstrating error recovery."""

    def __init__(self) -> None:
        self.processed_count = 0
        self.error_count = 0
        self.history: List[Dict[str, Any]] = []

    def process(self, batch: Any) -> Dict[str, Any]:
        """Processes an image batch and records execution outcome."""
        try:
            norm_batch, shape = validate_and_normalize_batch(batch)
            self.processed_count += 1
            record = {
                "status": "SUCCESS",
                "shape": shape,
                "normalized_batch": norm_batch,
                "error": None,
            }
        except TensorContractError as exc:
            self.error_count += 1
            record = {
                "status": "FAILED",
                "shape": None,
                "normalized_batch": None,
                "error": str(exc),
            }
        self.history.append(record)
        return record


def run_normal_scenario() -> Dict[str, Any]:
    """Canonical scenario: [[[0, 255], [128, 64]]] -> shape (1, 2, 2), 0->0, 255->1."""
    pipeline = BatchPreprocessingPipeline()
    result = pipeline.process(DEFAULT_BATCH)

    norm_batch = result["normalized_batch"]
    shape = result["shape"]

    # Invariants: 0 -> 0.0, 255 -> 1.0, shape == (1, 2, 2)
    p00 = norm_batch[0][0][0]  # 0 -> 0.0
    p01 = norm_batch[0][0][1]  # 255 -> 1.0
    p10 = norm_batch[0][1][0]  # 128 -> ~0.501961
    p11 = norm_batch[0][1][1]  # 64 -> ~0.25098

    contract_ok = (
        shape == (1, 2, 2)
        and p00 == 0.0
        and p01 == 1.0
        and 0.50 <= p10 <= 0.51
        and 0.25 <= p11 <= 0.26
    )

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "decision": "NORMALIZATION_SUCCESS_SHAPE_PRESERVED",
        "input_batch": DEFAULT_BATCH,
        "normalized_batch": norm_batch,
        "input_shape": [1, 2, 2],
        "output_shape": list(shape),
        "zero_mapped_to_zero": (p00 == 0.0),
        "max_mapped_to_one": (p01 == 1.0),
        "contract_satisfied": contract_ok,
    }


def run_negative_pixel_scenario() -> Dict[str, Any]:
    """Out-of-bounds scenario: Negative pixel rejected."""
    pipeline = BatchPreprocessingPipeline()
    invalid_batch = [[[ -10, 255], [128, 64]]]
    res = pipeline.process(invalid_batch)

    return {
        "scenario_id": "SCENARIO_NEGATIVE_PIXEL",
        "decision": "NEGATIVE_PIXEL_REJECTED",
        "input_batch": invalid_batch,
        "error_message": res["error"],
        "failed_as_expected": (res["status"] == "FAILED"),
        "contract_satisfied": (res["status"] == "FAILED"),
    }


def run_overflow_pixel_scenario() -> Dict[str, Any]:
    """Out-of-bounds scenario: Pixel > 255 rejected."""
    pipeline = BatchPreprocessingPipeline()
    invalid_batch = [[[0, 300], [128, 64]]]
    res = pipeline.process(invalid_batch)

    return {
        "scenario_id": "SCENARIO_OVERFLOW_PIXEL",
        "decision": "OVERFLOW_PIXEL_REJECTED",
        "input_batch": invalid_batch,
        "error_message": res["error"],
        "failed_as_expected": (res["status"] == "FAILED"),
        "contract_satisfied": (res["status"] == "FAILED"),
    }


def run_pipeline_recovery_scenario() -> Dict[str, Any]:
    """Focus: Exercise documented failure, explain error, and demonstrate recovery on next input."""
    pipeline = BatchPreprocessingPipeline()

    # Step 1: Process invalid batch
    invalid_batch = [[[0, 255], [-50, 64]]]
    res1 = pipeline.process(invalid_batch)

    # Step 2: Process subsequent valid batch
    valid_batch = DEFAULT_BATCH
    res2 = pipeline.process(valid_batch)

    recovery_verified = (
        res1["status"] == "FAILED"
        and res2["status"] == "SUCCESS"
        and res2["shape"] == (1, 2, 2)
    )

    return {
        "scenario_id": "SCENARIO_RECOVERY",
        "decision": "FAILURE_DOCUMENTED_AND_RECOVERED",
        "step_1_invalid_result": res1,
        "step_2_recovery_result": res2,
        "pipeline_state": {
            "processed_count": pipeline.processed_count,
            "error_count": pipeline.error_count,
        },
        "recovery_verified": recovery_verified,
        "contract_satisfied": recovery_verified,
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical decision table across all scenarios."""
    normal = run_normal_scenario()
    negative = run_negative_pixel_scenario()
    overflow = run_overflow_pixel_scenario()
    recovery = run_pipeline_recovery_scenario()

    scenarios = [normal, negative, overflow, recovery]
    expected_decisions = {
        "SCENARIO_NORMAL": "NORMALIZATION_SUCCESS_SHAPE_PRESERVED",
        "SCENARIO_NEGATIVE_PIXEL": "NEGATIVE_PIXEL_REJECTED",
        "SCENARIO_OVERFLOW_PIXEL": "OVERFLOW_PIXEL_REJECTED",
        "SCENARIO_RECOVERY": "FAILURE_DOCUMENTED_AND_RECOVERED",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected and sc.get("contract_satisfied", False))
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T008: Tensor Shape Contract & Pipeline Recovery Example."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "negative", "overflow", "recovery"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    if args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "negative":
        print(json.dumps(run_negative_pixel_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "overflow":
        print(json.dumps(run_overflow_pixel_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "recovery":
        print(json.dumps(run_pipeline_recovery_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
