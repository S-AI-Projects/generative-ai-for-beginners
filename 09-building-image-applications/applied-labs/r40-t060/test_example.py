"""Unit tests for Lesson 09 synthetic image batch normalization & applied questions."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = MODULE_DIR / "example.py"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from example import (  # noqa: E402
    APPLIED_QUESTIONS,
    DEFAULT_FIXTURE_BATCH,
    normalize_image_batch,
    run_applied_questions,
)


class TestImageBatchNormalizationAndQuestions(unittest.TestCase):
    def test_normal_batch_preserves_shape_and_scales_to_unit_interval(self) -> None:
        result = normalize_image_batch(DEFAULT_FIXTURE_BATCH)
        self.assertTrue(result["simulation"])
        self.assertEqual(result["verifies"], "preprocessing_only_not_model_quality")
        self.assertEqual(result["shape"], [1, 2, 2])
        self.assertEqual(result["min_value"], 0.0)
        self.assertEqual(result["max_value"], 1.0)
        self.assertEqual(result["normalized_batch"][0][0], [0.0, 1.0])
        self.assertAlmostEqual(result["normalized_batch"][0][1][0], 128.0 / 255.0)
        self.assertAlmostEqual(result["normalized_batch"][0][1][1], 64.0 / 255.0)

    def test_boundary_edges_and_structural_validation(self) -> None:
        edges = normalize_image_batch([[[0, 255]]])
        self.assertEqual(edges["shape"], [1, 1, 2])
        self.assertEqual(edges["normalized_batch"], [[[0.0, 1.0]]])

        for bad_batch in (
            [],
            [[]],
            [[[]]],
            [[[0, 1], [2]]],  # ragged row widths
            [[[True, 0]]],  # bool rejected
            [[[float("nan"), 0]]],  # non-finite rejected
        ):
            with self.assertRaises(ValueError):
                normalize_image_batch(bad_batch)

    def test_negative_and_over_255_pixels_rejected(self) -> None:
        with self.assertRaises(ValueError) as neg_ctx:
            normalize_image_batch([[[-1, 64]]])
        self.assertIn("out of range 0..255", str(neg_ctx.exception))

        with self.assertRaises(ValueError) as high_ctx:
            normalize_image_batch([[[0, 256], [128, 64]]])
        self.assertIn("out of range 0..255", str(high_ctx.exception))

    def test_three_applied_questions_have_rationales_and_pass_checks(self) -> None:
        report = run_applied_questions()
        self.assertTrue(report["all_passed"])
        self.assertEqual(len(APPLIED_QUESTIONS), 3)
        self.assertEqual(
            [q["category"] for q in report["questions"]],
            ["predict_output", "diagnose_failure", "boundary_policy"],
        )
        for q in report["questions"]:
            self.assertTrue(q["passed"])
            self.assertTrue(q["rationale"].strip())

    def test_fresh_process_cli_normal_questions_and_failures(self) -> None:
        for case in ("normal", "boundary_edges", "questions", "all"):
            proc = subprocess.run(
                [sys.executable, str(EXAMPLE_PATH), "--case", case],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"case={case} stderr={proc.stderr}")
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["simulation"])

        for fail_case in ("invalid_negative", "invalid_over255"):
            proc = subprocess.run(
                [sys.executable, str(EXAMPLE_PATH), "--case", fail_case],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("out of range 0..255", proc.stderr)


if __name__ == "__main__":
    unittest.main()
