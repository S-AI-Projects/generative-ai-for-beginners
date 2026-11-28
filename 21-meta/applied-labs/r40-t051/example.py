#!/usr/bin/env python3
"""Minimal local example: select Meta-family model variants that fit a
resource envelope of RAM and context window.

Teaching fixture only. The RAM/context numbers below are invented and do not
describe the named Llama variants from the lesson, any other real model, or
any real hardware. This file performs no model download, no remote API call,
no GPU and no network access. It is pure stdlib simulation on a small local
manifest.

Public inputs and outputs, connected to lesson concepts
--------------------------------------------------------
- Model metadata (lesson: "The Meta Family of Models")
    ModelVariant.name, ModelVariant.ram_gb, ModelVariant.context_window
- Resource constraints (lesson: context windows and the compute envelope a
    model needs to run)
    budget_ram_gb      -> RAM budget
    requested_context_tokens -> the context the app needs
- Eligibility (lesson: which variant can be used for this lesson/sample)
    is_eligible, eligibility_reason, select_models
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _validate_non_negative(value: int, name: str) -> None:
    """Raise ValueError when a resource quantity is negative."""
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")

# ---------------------------------------------------------------------------
# Lesson concept: model metadata.
# Every variant carries its "model card" fields. RAM and context are the two
# fields this fixture uses to decide eligibility.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelVariant:
    """Synthetic model metadata: name, RAM required (GB), context window (tokens)."""

    name: str
    ram_gb: int
    context_window: int


# Fixture A and Fixture B from the lesson brief:
#   A: RAM4 / context2048
#   B: RAM8 / context4096
# These two are the core teaching manifest for the budget scenario
# (budget RAM6, requested context1024 -> only A admits).
SCENARIO_MANIFEST: tuple[ModelVariant, ...] = (
    ModelVariant(name="fixture-a", ram_gb=4, context_window=2048),
    ModelVariant(name="fixture-b", ram_gb=8, context_window=4096),
)

# Signed-off: this manifest is a teaching fixture, NOT a claim about the real
# Llama 3.1 / Llama 3.2 / Llama 3.3 / Llama 4 variants mentioned in the lesson.
# No real hardware or cloud-service RAM/context values are asserted here.

# ---------------------------------------------------------------------------
# Lesson concept: resource constraints + eligibility.
# A variant is eligible iff it runs inside the RAM budget AND its context
# window covers the requested context.
# ---------------------------------------------------------------------------


def is_eligible(variant: ModelVariant, budget_ram_gb: int, requested_context_tokens: int) -> bool:
    """Return True when `variant` fits the resource envelope."""
    return variant.ram_gb <= budget_ram_gb and variant.context_window >= requested_context_tokens


def eligibility_reason(variant: ModelVariant, budget_ram_gb: int, requested_context_tokens: int) -> str:
    """Return a short reason why a variant is or is not eligible.

    This is a pure simulation with no remote lookup.
    """
    if variant.ram_gb > budget_ram_gb:
        return "exceeds budget RAM"
    if variant.context_window < requested_context_tokens:
        return "insufficient context window"
    return "fits envelope"


def select_models(
    manifest: Iterable[ModelVariant],
    budget_ram_gb: int,
    requested_context_tokens: int,
):
    """Select eligible variants and report why the rest are excluded.

    Public inputs : manifest (model metadata), budget_ram_gb,
                    requested_context_tokens (resource constraints).
    Public output : (eligible, excluded) — eligibility per model.
    """
    _validate_non_negative(budget_ram_gb, "budget_ram_gb")
    _validate_non_negative(requested_context_tokens, "requested_context_tokens")
    for model in manifest:
        _validate_non_negative(model.ram_gb, f"ram_gb of {model.name}")
        _validate_non_negative(model.context_window, f"context_window of {model.name}")

    manifest = list(manifest)
    eligible = [m for m in manifest if is_eligible(m, budget_ram_gb, requested_context_tokens)]
    excluded = [
        (m, eligibility_reason(m, budget_ram_gb, requested_context_tokens))
        for m in manifest
        if m not in eligible
    ]
    return sorted(eligible, key=lambda m: m.name), excluded


# ---------------------------------------------------------------------------
# Demo entry point (minimal complete example).
# ---------------------------------------------------------------------------


def run_demo(budget_ram_gb: int = 6, requested_context_tokens: int = 1024) -> None:
    """Run the fixture and print the lesson-linked table."""
    manifest = SCENARIO_MANIFEST
    eligible, excluded = select_models(manifest, budget_ram_gb, requested_context_tokens)

    print("[LESSON: model metadata] manifest entries = %d" % len(manifest))
    for m in sorted(manifest, key=lambda x: x.name):
        print(
            "  model=%s ram_gb=%d context_window=%d -> %s"
            % (
                m.name,
                m.ram_gb,
                m.context_window,
                "eligible" if is_eligible(m, budget_ram_gb, requested_context_tokens) else "excluded",
            )
        )

    print("[LESSON: resource constraints] budget_ram_gb=%d requested_context_tokens=%d" % (budget_ram_gb, requested_context_tokens))
    print("[LESSON: eligibility] eligible=%s" % ", ".join(m.name for m in eligible) or "(none)")
    for m, reason in excluded:
        print("[LESSON: eligibility] excluded=%s why=%s" % (m.name, reason))


if __name__ == "__main__":
    run_demo(6, 1024)
