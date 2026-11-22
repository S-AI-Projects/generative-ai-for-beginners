#!/usr/bin/env python3
"""Regression, shape invariant, and pipeline recovery test suite for R40-T008.

Lesson 09: Building Image Generation Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    DEFAULT_BATCH,
    BatchPreprocessingPipeline,
    DecisionMismatchError,
    TensorContractError,
    inspect_batch_shape,
    run_canonical_check,
    run_negative_pixel_scenario,
    run_normal_scenario,
    run_overflow_pixel_scenario,
    run_pipeline_recovery_scenario,
    validate_and_normalize_batch,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestTensorShapeAndNormalizationContract(unittest.TestCase):
    """Core tensor-shape and normalization contract tests."""

    def test_canonical_batch_shape_preserved(self) -> None:
        """Batch [[[0, 255], [128, 64]]] stays shape (1, 2, 2); 0->0 and 255->1."""
        norm, shape = validate_and_normalize_batch(DEFAULT_BATCH)
        self.assertEqual(shape, (1, 2, 2))
        self.assertEqual(len(norm), 1)
        self.assertEqual(len(norm[0]), 2)
        self.assertEqual(len(norm[0][0]), 2)

        self.assertEqual(norm[0][0][0], 0.0)
        self.assertEqual(norm[0][0][1], 1.0)
        self.assertAlmostEqual(norm[0][1][0], 128 / 255.0, places=4)
        self.assertAlmostEqual(norm[0][1][1], 64 / 255.0, places=4)

    def test_negative_pixel_rejected(self) -> None:
        """Negative pixel raises TensorContractError."""
        invalid = [[[ -1, 255], [128, 64]]]
        with self.assertRaises(TensorContractError):
            validate_and_normalize_batch(invalid)

    def test_overflow_pixel_rejected(self) -> None:
        """Pixel > 255 raises TensorContractError."""
        invalid = [[[0, 256], [128, 64]]]
        with self.assertRaises(TensorContractError):
            validate_and_normalize_batch(invalid)

    def test_ragged_dimensions_rejected(self) -> None:
        """Ragged/inconsistent dimensions raise TensorContractError."""
        ragged_width = [[[0, 255], [128]]]
        with self.assertRaises(TensorContractError):
            validate_and_normalize_batch(ragged_width)

    def test_non_numeric_elements_rejected(self) -> None:
        """Non-numeric elements raise TensorContractError."""
        invalid = [[[0, "white"], [128, 64]]]  # type: ignore
        with self.assertRaises(TensorContractError):
            validate_and_normalize_batch(invalid)


class TestPipelineFailureAndRecovery(unittest.TestCase):
    """Focus: Exercise documented failure, explain error, and demonstrate recovery on next input."""

    def test_failure_and_subsequent_recovery(self) -> None:
        pipeline = BatchPreprocessingPipeline()

        # Step 1: Documented failure
        invalid_batch = [[[0, 255], [-100, 64]]]
        res1 = pipeline.process(invalid_batch)
        self.assertEqual(res1["status"], "FAILED")
        self.assertIn("out of bounds", res1["error"])

        # Step 2: Next valid input recovers cleanly
        res2 = pipeline.process(DEFAULT_BATCH)
        self.assertEqual(res2["status"], "SUCCESS")
        self.assertEqual(res2["shape"], (1, 2, 2))
        self.assertEqual(res2["normalized_batch"][0][0][0], 0.0)
        self.assertEqual(res2["normalized_batch"][0][0][1], 1.0)

        # Confirm pipeline state accurately tracks error and success
        self.assertEqual(pipeline.error_count, 1)
        self.assertEqual(pipeline.processed_count, 1)


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Canonical verification checks and deliberate tamper detection."""

    def test_canonical_check_passes(self) -> None:
        res = run_canonical_check(tamper=False)
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateWrongResult(unittest.TestCase):
    """Demonstrates that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI execution in fresh subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal(self) -> None:
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "NORMALIZATION_SUCCESS_SHAPE_PRESERVED")

    def test_cli_scenario_negative(self) -> None:
        res = self._run_cli(["--scenario", "negative"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "NEGATIVE_PIXEL_REJECTED")

    def test_cli_scenario_overflow(self) -> None:
        res = self._run_cli(["--scenario", "overflow"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "OVERFLOW_PIXEL_REJECTED")

    def test_cli_scenario_recovery(self) -> None:
        res = self._run_cli(["--scenario", "recovery"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "FAILURE_DOCUMENTED_AND_RECOVERED")

    def test_cli_check(self) -> None:
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")


if __name__ == "__main__":
    unittest.main()
