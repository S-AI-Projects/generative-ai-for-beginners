"""
R40-T036 · Applied Lab: Prefix-Based Layer Freezing and Trainable Parameter Budget
==================================================================================

This module extends Lesson 18 ("Fine-Tuning Your LLM") by implementing a
deterministic parameter budget calculator and prefix-based layer freezing engine.

Lesson connection
-----------------
Lesson 18 explains how fine-tuning retrains pre-trained language models for specialized
tasks. Because training all parameters in a modern LLM (e.g., 7B or 70B weights) requires
immense memory and GPU compute, practical fine-tuning strategies selectively freeze
backbone layers (e.g. self-attention, feedforward networks) and only train task-specific
adapters or classification heads.

In production LLM fine-tuning:
  1. Trainable budget calculation is essential to estimate GPU VRAM and gradient buffer
     requirements before launching distributed training runs.
  2. Prefix-based freeze rules (e.g. freezing "encoder" or "transformer.layers.0") allow
     engineers to freeze large model subgraphs without manually listing every parameter.
  3. Configuration mistakes—such as typos in freeze prefixes (e.g., "encodr" instead of
     "encoder")—must be caught immediately. In framework code without validation, an
     unmatched freeze prefix silently fails to freeze parameters, leading to unintended
     full-parameter training and catastrophic GPU Out-Of-Memory (OOM) crashes.

Simplification boundary
-----------------------
This local lab isolates the parameter accounting and prefix-matching logic using in-memory
named-parameter manifests. It does NOT:
  - Download neural weights or run PyTorch / HuggingFace model architectures.
  - Require physical GPUs or cloud accelerators.
  - Claim real-world downstream model accuracy or convergence speed.

Focus: Refactoring by Extracting a Named Responsibility
-------------------------------------------------------
We first implement a monolithic baseline (`baseline_freeze_budget`) that combines
validation, rule matching, accounting, and reporting in a single procedure.
We then extract the prefix matching and classification responsibility into a dedicated,
reusable class (`PrefixFreezeMatcher`). Both implementations share the exact same contract,
and tests verify byte-for-byte behavioral equivalence across all fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ParameterClassification:
    """
    Classification of an individual model parameter layer.

    Attributes
    ----------
    name : str
        Name of the parameter tensor or module.
    count : int
        Number of parameters in this layer.
    is_frozen : bool
        Whether the layer is frozen (non-trainable).
    matched_prefix : str | None
        The freeze prefix that matched this layer, or None if trainable.
    """
    name: str
    count: int
    is_frozen: bool
    matched_prefix: str | None


@dataclass(frozen=True)
class FineTuningBudgetSummary:
    """
    Summary of model parameter counts and freeze status.

    Attributes
    ----------
    total_params : int
        Total parameter count across all layers in the manifest.
    trainable_params : int
        Number of parameters that will receive gradients during training.
    frozen_params : int
        Number of parameters frozen (weights kept static).
    trainable_percentage : float
        Percentage of total parameters that are trainable (0.0 to 100.0).
    unmatched_prefixes : tuple[str, ...]
        Freeze prefixes specified by the user that did not match any layer name.
    frozen_layers : tuple[str, ...]
        Names of layers that are frozen.
    trainable_layers : tuple[str, ...]
        Names of layers that remain trainable.
    """
    total_params: int
    trainable_params: int
    frozen_params: int
    trainable_percentage: float
    unmatched_prefixes: tuple[str, ...]
    frozen_layers: tuple[str, ...]
    trainable_layers: tuple[str, ...]


# ---------------------------------------------------------------------------
# Baseline: Monolithic Implementation
# ---------------------------------------------------------------------------

def baseline_freeze_budget(
    manifest: Mapping[str, int],
    freeze_prefixes: Sequence[str] = (),
) -> FineTuningBudgetSummary:
    """
    Monolithic baseline implementation that validates inputs, checks prefixes,
    counts parameters, and reports unmatched freeze rules in a single procedure.
    """
    if not isinstance(manifest, Mapping):
        raise TypeError(f"Manifest must be a mapping, got {type(manifest).__name__}")
    if not isinstance(freeze_prefixes, (list, tuple, set)):
        raise TypeError(f"freeze_prefixes must be a sequence, got {type(freeze_prefixes).__name__}")

    # Validate parameters
    for name, count in manifest.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid layer name: {name!r}. Must be a non-empty string.")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Invalid parameter count for {name!r}: {count!r}. Must be non-negative integer.")

    cleaned_prefixes = tuple(p.strip() for p in freeze_prefixes if isinstance(p, str) and p.strip())

    total_params = 0
    frozen_params = 0
    matched_prefixes_set = set()
    frozen_layers_list = []
    trainable_layers_list = []

    for name, count in manifest.items():
        total_params += count
        is_frozen = False
        matched_prefix = None
        for prefix in cleaned_prefixes:
            if name.startswith(prefix):
                is_frozen = True
                matched_prefix = prefix
                matched_prefixes_set.add(prefix)
                break

        if is_frozen:
            frozen_params += count
            frozen_layers_list.append(name)
        else:
            trainable_layers_list.append(name)

    trainable_params = total_params - frozen_params
    trainable_pct = (trainable_params / total_params * 100.0) if total_params > 0 else 0.0

    unmatched = tuple(p for p in cleaned_prefixes if p not in matched_prefixes_set)

    return FineTuningBudgetSummary(
        total_params=total_params,
        trainable_params=trainable_params,
        frozen_params=frozen_params,
        trainable_percentage=round(trainable_pct, 4),
        unmatched_prefixes=unmatched,
        frozen_layers=tuple(frozen_layers_list),
        trainable_layers=tuple(trainable_layers_list),
    )


# ---------------------------------------------------------------------------
# Refactored: Extracted Named Responsibility (PrefixFreezeMatcher)
# ---------------------------------------------------------------------------

class PrefixFreezeMatcher:
    """
    Extracted named responsibility: Encapsulates prefix rule compilation,
    layer classification, and detection of unmatched freeze prefixes.
    """

    def __init__(self, freeze_prefixes: Sequence[str] = ()) -> None:
        if not isinstance(freeze_prefixes, (list, tuple, set)):
            raise TypeError(f"freeze_prefixes must be a sequence, got {type(freeze_prefixes).__name__}")

        self._prefixes: tuple[str, ...] = tuple(
            p.strip() for p in freeze_prefixes if isinstance(p, str) and p.strip()
        )

    @property
    def configured_prefixes(self) -> tuple[str, ...]:
        return self._prefixes

    def match_layer(self, layer_name: str) -> tuple[bool, str | None]:
        """
        Check whether a single layer name matches any configured freeze prefix.

        Returns
        -------
        tuple[bool, str | None]
            (True, matched_prefix) if frozen, else (False, None).
        """
        for prefix in self._prefixes:
            if layer_name.startswith(prefix):
                return True, prefix
        return False, None

    def classify_manifest(
        self, manifest: Mapping[str, int]
    ) -> tuple[list[ParameterClassification], tuple[str, ...]]:
        """
        Classify all layers in a manifest and identify unmatched prefixes.

        Returns
        -------
        tuple[list[ParameterClassification], tuple[str, ...]]
            Classified parameter records and tuple of unmatched freeze prefixes.
        """
        classifications: list[ParameterClassification] = []
        matched_prefixes = set()

        for name, count in manifest.items():
            is_frozen, matched_prefix = self.match_layer(name)
            if is_frozen and matched_prefix:
                matched_prefixes.add(matched_prefix)
            classifications.append(
                ParameterClassification(
                    name=name,
                    count=count,
                    is_frozen=is_frozen,
                    matched_prefix=matched_prefix,
                )
            )

        unmatched = tuple(p for p in self._prefixes if p not in matched_prefixes)
        return classifications, unmatched


def count_fine_tuning_parameters(
    manifest: Mapping[str, int],
    freeze_prefixes: Sequence[str] = (),
) -> FineTuningBudgetSummary:
    """
    Refactored parameter budget calculator that delegates classification
    to the extracted `PrefixFreezeMatcher` responsibility.

    Parameters
    ----------
    manifest : Mapping[str, int]
        Mapping of layer/parameter names to parameter counts.
    freeze_prefixes : Sequence[str]
        Prefixes of layers to freeze.

    Returns
    -------
    FineTuningBudgetSummary
        Complete breakdown of total, trainable, and frozen parameters,
        along with any unmatched freeze prefixes.
    """
    if not isinstance(manifest, Mapping):
        raise TypeError(f"Manifest must be a mapping, got {type(manifest).__name__}")

    # Validate layer names and parameter counts
    for name, count in manifest.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid layer name: {name!r}. Must be a non-empty string.")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Invalid parameter count for {name!r}: {count!r}. Must be non-negative integer.")

    matcher = PrefixFreezeMatcher(freeze_prefixes)
    classifications, unmatched_prefixes = matcher.classify_manifest(manifest)

    total_params = sum(item.count for item in classifications)
    frozen_params = sum(item.count for item in classifications if item.is_frozen)
    trainable_params = total_params - frozen_params

    trainable_pct = (trainable_params / total_params * 100.0) if total_params > 0 else 0.0

    frozen_layers = tuple(item.name for item in classifications if item.is_frozen)
    trainable_layers = tuple(item.name for item in classifications if not item.is_frozen)

    return FineTuningBudgetSummary(
        total_params=total_params,
        trainable_params=trainable_params,
        frozen_params=frozen_params,
        trainable_percentage=round(trainable_pct, 4),
        unmatched_prefixes=unmatched_prefixes,
        frozen_layers=frozen_layers,
        trainable_layers=trainable_layers,
    )


def prove_before_after_equivalence(
    manifest: Mapping[str, int],
    freeze_prefixes: Sequence[str] = (),
) -> tuple[bool, FineTuningBudgetSummary, FineTuningBudgetSummary]:
    """
    Helper to execute both baseline and refactored implementations on the same
    fixture and return equivalence status alongside both results.
    """
    baseline_result = baseline_freeze_budget(manifest, freeze_prefixes)
    refactored_result = count_fine_tuning_parameters(manifest, freeze_prefixes)
    is_equivalent = baseline_result == refactored_result
    return is_equivalent, baseline_result, refactored_result
