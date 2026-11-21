"""
R40-T035 · Applied Lab: Tensor-Shape Contract & Offline Service Adapter
========================================================================

This module extends Lesson 09 ("Building Image Generation Applications") by
implementing a deterministic local service adapter that validates and normalizes
synthetic image batches prior to model processing.

Lesson connection
-----------------
Lesson 09 covers building image generation and editing applications with models
like `gpt-image`. In modern computer vision and generative diffusion pipelines:
  1. Image tensors are fed as batches of spatial matrices (N x H x W).
  2. Input pixel intensities must be validated (within [0, 255]) and normalized
     to standard floating-point bounds [0.0, 1.0].
  3. Preprocessing must strictly preserve batch and spatial tensor dimensions so
     subsequent convolutional or transformer layers receive expected shapes.
  4. Real-world applications rely on remote cloud APIs (e.g., Azure OpenAI /
     Microsoft Foundry) that charge for inference, require network access, and
     enforce rate limits. Isolating preprocessing behind a callable interface
     allows robust offline testing and prevents invalid data from reaching expensive
     downstream endpoints.

Simplification boundary
-----------------------
This local implementation validates numeric arrays in memory. It does NOT:
  - Download or execute real neural diffusion weights.
  - Require physical GPU hardware or cloud subscriptions.
  - Make claims about real-world image generation fidelity or prompt adherence.

Focus: Callable Interface & Offline Service Adapter
---------------------------------------------------
We define an abstract callable interface (`ImageBatchService`) representing the
external image service dependency, and provide `DeterministicLocalImageAdapter`,
a local offline test double that executes the contract deterministically while
explicitly declaring the real-service behaviors it does not establish.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence


class ImageTensorValidationError(ValueError):
    """Base exception for image tensor validation failures."""
    pass


class InvalidPixelValueError(ImageTensorValidationError):
    """Raised when pixel values fall outside the valid [0, 255] range."""
    pass


class InvalidTensorShapeError(ImageTensorValidationError):
    """Raised when batch dimensions are ragged or not a valid 3D tensor."""
    pass


@dataclass(frozen=True)
class NormalizedBatchResult:
    """
    Result of image batch validation and normalization.

    Attributes
    ----------
    normalized_batch : tuple[tuple[tuple[float, ...], ...], ...]
        The normalized pixel values scaled to [0.0, 1.0].
    shape : tuple[int, int, int]
        Tensor shape representing (batch_size, height, width).
    min_pixel : float
        Minimum normalized pixel value in the batch.
    max_pixel : float
        Maximum normalized pixel value in the batch.
    is_mock : bool
        Flag indicating whether this was produced by an offline adapter (True).
    unestablished_behaviors : tuple[str, ...]
        Real-service behaviors that this local mock does not establish.
    """
    normalized_batch: tuple[tuple[tuple[float, ...], ...], ...]
    shape: tuple[int, int, int]
    min_pixel: float
    max_pixel: float
    is_mock: bool = True
    unestablished_behaviors: tuple[str, ...] = ()


UNESTABLISHED_REAL_SERVICE_BEHAVIORS: tuple[str, ...] = (
    "Network transport latency, socket timeouts, and connection pooling",
    "Cloud authentication, subscription keys, and tenant authorization",
    "Neural diffusion denoising steps, UNet/transformer weight evaluation, and latent decoding",
    "Cloud content safety filters and prompt moderation checks",
    "Base64 image serialization/deserialization and binary PNG/JPEG encoding",
)


def validate_and_normalize_batch(
    batch: Sequence[Sequence[Sequence[float | int]]],
) -> NormalizedBatchResult:
    """
    Validate and normalize an N x H x W image batch.

    Parameters
    ----------
    batch : Sequence[Sequence[Sequence[float | int]]]
        A 3D sequence representing batch of images: N images, each H rows, each W columns.
        Raw pixel values must be numeric in range [0, 255].

    Returns
    -------
    NormalizedBatchResult
        Normalized batch with pixels in [0.0, 1.0] and preserved shape (N, H, W).

    Raises
    ------
    TypeError
        If batch is not a sequence or contains non-numeric elements.
    InvalidTensorShapeError
        If dimensions are ragged or not 3-dimensional.
    InvalidPixelValueError
        If any pixel value is negative (< 0) or exceeds 255 (> 255).
    """
    if not isinstance(batch, (list, tuple)):
        raise TypeError(f"Batch must be a sequence of images, got {type(batch).__name__}")

    n = len(batch)
    if n == 0:
        return NormalizedBatchResult(
            normalized_batch=(),
            shape=(0, 0, 0),
            min_pixel=0.0,
            max_pixel=0.0,
            is_mock=True,
            unestablished_behaviors=UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
        )

    # Validate first image to get expected H and W
    first_img = batch[0]
    if not isinstance(first_img, (list, tuple)):
        raise InvalidTensorShapeError(f"Each item in batch must be a 2D image matrix, got {type(first_img).__name__}")

    h = len(first_img)
    if h == 0:
        raise InvalidTensorShapeError("Image height must be greater than 0")

    first_row = first_img[0]
    if not isinstance(first_row, (list, tuple)):
        raise InvalidTensorShapeError(f"Each row in image must be a 1D pixel sequence, got {type(first_row).__name__}")

    w = len(first_row)
    if w == 0:
        raise InvalidTensorShapeError("Image width must be greater than 0")

    normalized_images: list[tuple[tuple[float, ...], ...]] = []
    all_normalized_pixels: list[float] = []

    for img_idx, img in enumerate(batch):
        if not isinstance(img, (list, tuple)):
            raise InvalidTensorShapeError(f"Image {img_idx} is not a valid 2D matrix")
        if len(img) != h:
            raise InvalidTensorShapeError(
                f"Ragged batch: image {img_idx} has height {len(img)}, expected {h}"
            )

        normalized_rows: list[tuple[float, ...]] = []
        for row_idx, row in enumerate(img):
            if not isinstance(row, (list, tuple)):
                raise InvalidTensorShapeError(
                    f"Image {img_idx}, row {row_idx} is not a valid pixel sequence"
                )
            if len(row) != w:
                raise InvalidTensorShapeError(
                    f"Ragged batch: image {img_idx}, row {row_idx} has width {len(row)}, expected {w}"
                )

            normalized_pixels: list[float] = []
            for col_idx, pixel in enumerate(row):
                if not isinstance(pixel, (int, float)) or isinstance(pixel, bool):
                    raise TypeError(
                        f"Pixel at ({img_idx}, {row_idx}, {col_idx}) must be numeric, got {type(pixel).__name__}"
                    )
                if pixel < 0 or pixel > 255:
                    raise InvalidPixelValueError(
                        f"Invalid pixel value {pixel} at ({img_idx}, {row_idx}, {col_idx}). "
                        f"Must be between 0 and 255 inclusive."
                    )

                # Normalize 0..255 -> 0.0..1.0
                norm_val = round(float(pixel) / 255.0, 6)
                normalized_pixels.append(norm_val)
                all_normalized_pixels.append(norm_val)

            normalized_rows.append(tuple(normalized_pixels))
        normalized_images.append(tuple(normalized_rows))

    min_val = min(all_normalized_pixels) if all_normalized_pixels else 0.0
    max_val = max(all_normalized_pixels) if all_normalized_pixels else 0.0

    return NormalizedBatchResult(
        normalized_batch=tuple(normalized_images),
        shape=(n, h, w),
        min_pixel=min_val,
        max_pixel=max_val,
        is_mock=True,
        unestablished_behaviors=UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
    )


class ImageBatchService(Protocol):
    """
    Callable interface defining the boundary for image batch processing dependencies.
    """

    def __call__(
        self, batch: Sequence[Sequence[Sequence[float | int]]]
    ) -> NormalizedBatchResult:
        """Process an image batch and return normalized results."""
        ...


class DeterministicLocalImageAdapter:
    """
    Deterministic offline adapter satisfying ImageBatchService.

    Executes input validation and normalization locally without making network calls,
    requiring GPU resources, or claiming model generation quality.
    """

    def __init__(
        self,
        custom_validator: Callable[[Sequence[Sequence[Sequence[float | int]]]], NormalizedBatchResult] | None = None,
    ) -> None:
        self._validator = custom_validator or validate_and_normalize_batch

    @property
    def unestablished_behaviors(self) -> tuple[str, ...]:
        return UNESTABLISHED_REAL_SERVICE_BEHAVIORS

    def process_batch(
        self, batch: Sequence[Sequence[Sequence[float | int]]]
    ) -> NormalizedBatchResult:
        """Explicit method to process batch."""
        return self._validator(batch)

    def __call__(
        self, batch: Sequence[Sequence[Sequence[float | int]]]
    ) -> NormalizedBatchResult:
        """Callable interface invocation."""
        return self.process_batch(batch)
