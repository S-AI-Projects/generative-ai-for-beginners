"""
Unit tests for R40-T035 Tensor-Shape Contract & Offline Service Adapter.
"""

from __future__ import annotations

import unittest

from example import (
    DeterministicLocalImageAdapter,
    ImageBatchService,
    InvalidPixelValueError,
    InvalidTensorShapeError,
    NormalizedBatchResult,
    UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
    validate_and_normalize_batch,
)


class TestTensorShapeContract(unittest.TestCase):
    """Core contract tests for image batch validation, shape preservation, and pixel normalization."""

    def test_required_contract_fixture(self) -> None:
        """
        Contract requirement:
        Batch [[[0, 255], [128, 64]]] stays shape (1, 2, 2);
        0 -> 0.0 and 255 -> 1.0;
        all values normalized into [0.0, 1.0].
        """
        raw_batch = [[[0, 255], [128, 64]]]
        result = validate_and_normalize_batch(raw_batch)

        # Verify shape preservation
        self.assertEqual(result.shape, (1, 2, 2))
        self.assertEqual(len(result.normalized_batch), 1)
        self.assertEqual(len(result.normalized_batch[0]), 2)
        self.assertEqual(len(result.normalized_batch[0][0]), 2)

        # Verify exact pixel normalization
        first_image = result.normalized_batch[0]
        self.assertEqual(first_image[0][0], 0.0)
        self.assertEqual(first_image[0][1], 1.0)
        self.assertAlmostEqual(first_image[1][0], 128 / 255.0, places=4)
        self.assertAlmostEqual(first_image[1][1], 64 / 255.0, places=4)

        # Verify min and max bounds
        self.assertEqual(result.min_pixel, 0.0)
        self.assertEqual(result.max_pixel, 1.0)

    def test_negative_pixel_is_rejected(self) -> None:
        """Pixels < 0 must be rejected with InvalidPixelValueError."""
        invalid_batch = [[[0, -1], [128, 64]]]
        with self.assertRaises(InvalidPixelValueError) as ctx:
            validate_and_normalize_batch(invalid_batch)
        self.assertIn("Invalid pixel value -1", str(ctx.exception))

    def test_pixel_greater_than_255_is_rejected(self) -> None:
        """Pixels > 255 must be rejected with InvalidPixelValueError."""
        invalid_batch = [[[0, 256], [128, 64]]]
        with self.assertRaises(InvalidPixelValueError) as ctx:
            validate_and_normalize_batch(invalid_batch)
        self.assertIn("Invalid pixel value 256", str(ctx.exception))

    def test_non_numeric_pixel_raises_type_error(self) -> None:
        """Non-numeric or boolean values must raise TypeError."""
        with self.assertRaises(TypeError):
            validate_and_normalize_batch([[[0, "255"], [128, 64]]])

        with self.assertRaises(TypeError):
            validate_and_normalize_batch([[[0, True], [128, 64]]])

    def test_ragged_tensor_width_rejected(self) -> None:
        """Inconsistent row width within an image raises InvalidTensorShapeError."""
        ragged_batch = [[[0, 255], [128]]]
        with self.assertRaises(InvalidTensorShapeError) as ctx:
            validate_and_normalize_batch(ragged_batch)
        self.assertIn("Ragged batch", str(ctx.exception))

    def test_ragged_tensor_height_rejected(self) -> None:
        """Inconsistent image heights across a batch raise InvalidTensorShapeError."""
        ragged_batch = [
            [[0, 255], [128, 64]],
            [[0, 255]],  # only 1 row instead of 2
        ]
        with self.assertRaises(InvalidTensorShapeError) as ctx:
            validate_and_normalize_batch(ragged_batch)
        self.assertIn("Ragged batch", str(ctx.exception))

    def test_multi_image_batch_processing(self) -> None:
        """A batch of multiple images (N=2, H=3, W=2) preserves dimensions correctly."""
        batch = [
            [[0, 50], [100, 150], [200, 255]],
            [[10, 20], [30, 40], [50, 60]],
        ]
        result = validate_and_normalize_batch(batch)

        self.assertEqual(result.shape, (2, 3, 2))
        self.assertEqual(len(result.normalized_batch), 2)
        self.assertEqual(len(result.normalized_batch[0]), 3)
        self.assertEqual(len(result.normalized_batch[0][0]), 2)
        self.assertEqual(result.min_pixel, 0.0)
        self.assertEqual(result.max_pixel, 1.0)

    def test_empty_batch_boundary(self) -> None:
        """An empty batch yields a valid result with shape (0, 0, 0)."""
        result = validate_and_normalize_batch([])
        self.assertEqual(result.shape, (0, 0, 0))
        self.assertEqual(result.normalized_batch, ())


class TestFocusCallableInterfaceAndAdapter(unittest.TestCase):
    """Focus requirements: Callable interface, offline adapter, and unestablished real-service behaviors."""

    def setUp(self) -> None:
        self.adapter = DeterministicLocalImageAdapter()

    def test_adapter_satisfies_callable_interface(self) -> None:
        """Verify adapter can be invoked via __call__ and process_batch."""
        raw_batch = [[[0, 255], [128, 64]]]

        # Test __call__ interface
        call_result = self.adapter(raw_batch)
        self.assertIsInstance(call_result, NormalizedBatchResult)
        self.assertEqual(call_result.shape, (1, 2, 2))

        # Test process_batch method
        proc_result = self.adapter.process_batch(raw_batch)
        self.assertEqual(call_result, proc_result)

    def test_adapter_identifies_unestablished_real_service_behaviors(self) -> None:
        """
        Verify that the adapter explicitly identifies which real-service behaviors
        this local mock does not establish.
        """
        raw_batch = [[[0, 255], [128, 64]]]
        result = self.adapter(raw_batch)

        self.assertTrue(result.is_mock)
        self.assertGreater(len(result.unestablished_behaviors), 0)

        # Check key unestablished aspects
        behaviors_text = " ".join(result.unestablished_behaviors).lower()
        self.assertIn("network", behaviors_text)
        self.assertIn("authentication", behaviors_text)
        self.assertIn("diffusion", behaviors_text)
        self.assertIn("safety", behaviors_text)

    def test_dependency_injection_with_custom_adapter(self) -> None:
        """Verify that downstream client code can accept any ImageBatchService callable."""
        def dummy_client(service: ImageBatchService, batch: list) -> NormalizedBatchResult:
            return service(batch)

        result = dummy_client(self.adapter, [[[0, 255], [128, 64]]])
        self.assertEqual(result.shape, (1, 2, 2))
        self.assertEqual(result.normalized_batch[0][0][1], 1.0)


class TestDeliberateWrongAssertions(unittest.TestCase):
    """
    Deliberate wrong result checks to confirm that the test framework
    fails with non-zero exit code if results deviate.
    """

    def test_deliberate_wrong_shape_assertion_fails(self) -> None:
        """Asserting an incorrect tensor shape raises AssertionError."""
        result = validate_and_normalize_batch([[[0, 255], [128, 64]]])
        with self.assertRaises(AssertionError):
            self.assertEqual(result.shape, (99, 99, 99))

    def test_deliberate_wrong_pixel_value_fails(self) -> None:
        """Asserting an incorrect normalized pixel value raises AssertionError."""
        result = validate_and_normalize_batch([[[0, 255], [128, 64]]])
        with self.assertRaises(AssertionError):
            self.assertEqual(result.normalized_batch[0][0][0], 0.999)


if __name__ == "__main__":
    unittest.main()
