"""
R40-T047 · Applied Lab: Fine-Tuning Parameter Budget & Layer Freezing
=====================================================================

This module illustrates Lesson 18 ("Fine-Tuning Your LLM") through a
**local named-parameter manifest and prefix-based layer freeze counter**.

Lesson connection
-----------------
Lesson 18 explains that full fine-tuning of every model weight is often
prohibitively expensive in compute and hosting costs. Techniques like
parameter-efficient fine-tuning (PEFT, e.g. LoRA) or selective layer freezing
freeze the majority of base-model parameters (such as the transformer encoder/backbone)
and only train task-specific layers (such as a classification head or LoRA adapters).

Before running a fine-tuning job on Microsoft Foundry, a preflight step:
  1. Inspects the model's named parameter manifest.
  2. Evaluates prefix-based freeze rules to partition parameters into frozen vs. trainable.
  3. Verifies that freeze rule prefixes actually match existing layers (catching
     configuration mistakes / typos such as "decoder" when the model only has "encoder").
  4. Publishes a worked input-to-output explanation comparing total vs trainable budget.

Simplification boundary
-----------------------
This lab operates on a lightweight integer parameter count manifest.
It does NOT:
  - Download or load actual PyTorch/ONNX model tensors or weights.
  - Require GPUs, CUDA, or physical accelerator devices.
  - Call Azure/OpenAI fine-tuning APIs or bill training compute.
  - Measure training loss, perplexity, or actual model convergence.
It isolates and verifies parameter-counting and freeze-rule logic deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ParameterBudgetReport:
    """
    Summary of parameter counting and prefix-based freeze evaluation.

    Attributes
    ----------
    total_params : int
        Sum of all parameter counts across layers.
    trainable_params : int
        Sum of parameter counts for layers that are NOT frozen.
    frozen_params : int
        Sum of parameter counts for layers that matched a freeze prefix.
    layer_states : dict[str, bool]
        Mapping of layer_name -> is_frozen (True if frozen, False if trainable).
    matched_prefixes : tuple[str, ...]
        Freeze prefixes that matched at least one layer in the manifest.
    unmatched_prefixes : tuple[str, ...]
        Freeze prefixes that did not match any layer (configuration mistake).
    explanation : str
        Human-readable worked input-to-output explanation.
    """

    total_params: int
    trainable_params: int
    frozen_params: int
    layer_states: dict[str, bool]
    matched_prefixes: tuple[str, ...]
    unmatched_prefixes: tuple[str, ...]
    explanation: str


def evaluate_parameter_budget(
    manifest: Mapping[str, int],
    freeze_prefixes: Sequence[str] = (),
    strict: bool = False,
) -> ParameterBudgetReport:
    """
    Count total and trainable parameters from a named-parameter manifest
    using prefix-based freeze rules.

    Parameters
    ----------
    manifest : Mapping[str, int]
        Mapping of layer or parameter name to parameter count (must be non-negative).
    freeze_prefixes : Sequence[str]
        Prefixes of layer names to freeze. Any layer whose name starts with one of
        these prefixes will be frozen (non-trainable).
    strict : bool, default=False
        If True, raises ValueError when any freeze prefix fails to match any layer.

    Returns
    -------
    ParameterBudgetReport
        Complete report containing parameter counts, layer breakdown, unmatched prefixes,
        and a worked textual explanation.

    Raises
    ------
    ValueError
        - If any parameter count is negative.
        - If strict is True and one or more freeze prefixes are unmatched.
    """
    for layer_name, count in manifest.items():
        if count < 0:
            raise ValueError(
                f"[R40-T047] Parameter count for {layer_name!r} must be >= 0, got {count}."
            )

    matched_prefixes_set: set[str] = set()
    layer_states: dict[str, bool] = {}

    total_params = 0
    trainable_params = 0
    frozen_params = 0

    explanation_lines: list[str] = [
        "Worked Input-to-Output Parameter Evaluation:",
        f"Input manifest: {dict(manifest)}",
        f"Configured freeze prefixes: {list(freeze_prefixes)}",
        "Layer-by-layer evaluation:",
    ]

    for layer_name, count in manifest.items():
        total_params += count
        is_frozen = False
        matching_rule = None

        for prefix in freeze_prefixes:
            if layer_name.startswith(prefix):
                is_frozen = True
                matching_rule = prefix
                matched_prefixes_set.add(prefix)
                break

        layer_states[layer_name] = is_frozen
        if is_frozen:
            frozen_params += count
            explanation_lines.append(
                f"  - Layer {layer_name!r} ({count:,} params) matches freeze prefix {matching_rule!r} -> FROZEN"
            )
        else:
            trainable_params += count
            explanation_lines.append(
                f"  - Layer {layer_name!r} ({count:,} params) matches no freeze prefix -> TRAINABLE"
            )

    unmatched_prefixes = tuple(p for p in freeze_prefixes if p not in matched_prefixes_set)
    matched_prefixes = tuple(p for p in freeze_prefixes if p in matched_prefixes_set)

    if unmatched_prefixes:
        explanation_lines.append(
            f"WARNING: Unmatched freeze prefixes detected: {list(unmatched_prefixes)}"
        )
    else:
        explanation_lines.append("All freeze prefixes matched at least one layer.")

    explanation_lines.extend([
        f"Result: total={total_params:,}, trainable={trainable_params:,}, frozen={frozen_params:,}.",
    ])

    if strict and unmatched_prefixes:
        raise ValueError(
            f"[R40-T047] Unmatched freeze prefixes: {list(unmatched_prefixes)}. "
            "Please check layer names in manifest."
        )

    return ParameterBudgetReport(
        total_params=total_params,
        trainable_params=trainable_params,
        frozen_params=frozen_params,
        layer_states=layer_states,
        matched_prefixes=matched_prefixes,
        unmatched_prefixes=unmatched_prefixes,
        explanation="\n".join(explanation_lines),
    )
