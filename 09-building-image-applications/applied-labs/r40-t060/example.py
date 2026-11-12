"""Local N×H×W synthetic image batch validation & normalization lab (Lesson 09).

Illustrates image-pipeline preprocessing boundaries (batch/spatial shape preservation,
0..255 -> 0..1 scaling, and rejecting out-of-range pixels) for Lesson 09. This verifies
preprocessing only, NOT model quality, real hardware, or cloud service behavior.

Purely local simulation: Python 3.9+ standard library only (no Pillow, NumPy, model
download, paid provider, GPU, or physical device required).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Callable, Sequence

DEFAULT_FIXTURE_BATCH: list[list[list[int]]] = [[[0, 255], [128, 64]]]


def _is_valid_pixel_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_image_batch(batch: Any) -> dict[str, Any]:
    """Validate an N x H x W batch in 0..255 and normalize pixels to 0..1."""
    if not isinstance(batch, (list, tuple)) or len(batch) == 0:
        raise ValueError("Batch must be a non-empty sequence of N images (N x H x W)")

    n_count = len(batch)
    h_count: int | None = None
    w_count: int | None = None
    normalized: list[list[list[float]]] = []
    min_val = float("inf")
    max_val = float("-inf")

    for n_idx, image in enumerate(batch):
        if not isinstance(image, (list, tuple)) or len(image) == 0:
            raise ValueError(f"Image at index {n_idx} must be a non-empty H x W grid")
        if h_count is None:
            h_count = len(image)
        elif len(image) != h_count:
            raise ValueError(
                f"Inconsistent image height at index {n_idx}: expected {h_count}, got {len(image)}"
            )

        norm_rows: list[list[float]] = []
        for h_idx, row in enumerate(image):
            if not isinstance(row, (list, tuple)) or len(row) == 0:
                raise ValueError(f"Row at [{n_idx}][{h_idx}] must be a non-empty sequence of W pixels")
            if w_count is None:
                w_count = len(row)
            elif len(row) != w_count:
                raise ValueError(
                    f"Inconsistent row width at [{n_idx}][{h_idx}]: expected {w_count}, got {len(row)}"
                )

            norm_pixels: list[float] = []
            for w_idx, pixel in enumerate(row):
                if not _is_valid_pixel_number(pixel):
                    raise ValueError(
                        f"Pixel at [{n_idx}][{h_idx}][{w_idx}] must be a finite number, got {pixel!r}"
                    )
                if pixel < 0 or pixel > 255:
                    raise ValueError(
                        f"Pixel value {pixel} at [{n_idx}][{h_idx}][{w_idx}] is out of range 0..255"
                    )
                scaled = float(pixel) / 255.0
                norm_pixels.append(scaled)
                if scaled < min_val:
                    min_val = scaled
                if scaled > max_val:
                    max_val = scaled
            norm_rows.append(norm_pixels)
        normalized.append(norm_rows)

    return {
        "simulation": True,
        "verifies": "preprocessing_only_not_model_quality",
        "shape": [n_count, h_count, w_count],
        "normalized_batch": normalized,
        "min_value": min_val,
        "max_value": max_val,
    }


def _check_q1_predict_output() -> dict[str, Any]:
    out = normalize_image_batch(DEFAULT_FIXTURE_BATCH)
    assert out["shape"] == [1, 2, 2], f"Expected [1, 2, 2], got {out['shape']}"
    assert out["min_value"] == 0.0, f"Expected 0.0, got {out['min_value']}"
    assert out["max_value"] == 1.0, f"Expected 1.0, got {out['max_value']}"
    return {
        "shape": out["shape"],
        "min_value": out["min_value"],
        "max_value": out["max_value"],
    }


def _check_q2_diagnose_failure() -> dict[str, Any]:
    captured_msg = ""
    try:
        normalize_image_batch([[[0, 256], [128, 64]]])
    except ValueError as exc:
        captured_msg = str(exc)
    assert "out of range 0..255" in captured_msg, f"Unexpected error: {captured_msg}"
    return {"raises": "ValueError", "error_message": captured_msg}


def _check_q3_boundary_policy() -> dict[str, Any]:
    rejected_values: list[int] = []
    for bad in (-1, 256):
        try:
            normalize_image_batch([[[bad]]])
        except ValueError:
            rejected_values.append(bad)
    assert rejected_values == [-1, 256], f"Expected [-1, 256] rejected, got {rejected_values}"
    valid_edges = normalize_image_batch([[[0, 255]]])
    assert valid_edges["normalized_batch"] == [[[0.0, 1.0]]]
    return {
        "policy": "reject_out_of_range_with_value_error",
        "rejected_out_of_range": rejected_values,
        "valid_edges_normalized": valid_edges["normalized_batch"],
    }


APPLIED_QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "question_id": "q1_predict_output",
        "category": "predict_output",
        "question": (
            "For batch [[[0, 255], [128, 64]]], what output shape, min_value, and max_value "
            "does normalize_image_batch produce?"
        ),
        "expected_answer": {"shape": [1, 2, 2], "min_value": 0.0, "max_value": 1.0},
        "rationale": (
            "Element-wise division by 255.0 preserves all N x H x W dimensions (1, 2, 2) "
            "and maps 0 -> 0.0 and 255 -> 1.0."
        ),
        "check_fn": _check_q1_predict_output,
    },
    {
        "question_id": "q2_diagnose_failure",
        "category": "diagnose_failure",
        "question": (
            "Why does [[[0, 256], [128, 64]]] fail, and what does the error indicate?"
        ),
        "expected_answer_substring": "out of range 0..255",
        "rationale": (
            "Pixel 256 at [0][0][1] exceeds the 0..255 unsigned 8-bit domain; allowing it "
            "would yield 1.0039... outside 0..1, so validation raises ValueError."
        ),
        "check_fn": _check_q2_diagnose_failure,
    },
    {
        "question_id": "q3_boundary_policy",
        "category": "boundary_policy",
        "question": (
            "Should out-of-range pixels (-1 or 256) be silently clamped or rejected with ValueError?"
        ),
        "expected_answer": {"policy": "reject_out_of_range_with_value_error"},
        "rationale": (
            "Silent clamping hides upstream scaling or decoding bugs. Rejecting invalid pixels "
            "with ValueError enforces the 0..255 precondition for preprocessing only."
        ),
        "check_fn": _check_q3_boundary_policy,
    },
)


def run_applied_questions() -> dict[str, Any]:
    """Execute and verify all three applied questions against the local example."""
    results: list[dict[str, Any]] = []
    for item in APPLIED_QUESTIONS:
        check_fn: Callable[[], dict[str, Any]] = item["check_fn"]
        observed = check_fn()
        results.append(
            {
                "question_id": item["question_id"],
                "category": item["category"],
                "question": item["question"],
                "rationale": item["rationale"],
                "observed_check_result": observed,
                "passed": True,
            }
        )
    return {
        "simulation": True,
        "verifies": "preprocessing_only_not_model_quality",
        "all_passed": all(r["passed"] for r in results),
        "questions": results,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and normalize a local N x H x W synthetic image batch (0..255 -> 0..1) "
            "and verify the three Lesson 09 applied questions."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", "normal", "boundary_edges", "invalid_negative", "invalid_over255", "questions"),
        default="all",
        help="Scenario to run (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        if args.case == "normal":
            payload = normalize_image_batch(DEFAULT_FIXTURE_BATCH)
        elif args.case == "boundary_edges":
            payload = normalize_image_batch([[[0, 255]]])
        elif args.case == "invalid_negative":
            payload = normalize_image_batch([[[-1, 64]]])
        elif args.case == "invalid_over255":
            payload = normalize_image_batch([[[0, 256], [128, 64]]])
        elif args.case == "questions":
            payload = run_applied_questions()
        else:
            payload = {
                "simulation": True,
                "verifies": "preprocessing_only_not_model_quality",
                "normal_batch": normalize_image_batch(DEFAULT_FIXTURE_BATCH),
                "applied_questions": run_applied_questions(),
            }
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
