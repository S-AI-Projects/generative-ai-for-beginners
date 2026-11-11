"""Local synthetic model-selection example for Lesson 21 (Meta Family Models).

All manifest entries and numeric limits in this module are invented teaching
fixtures for demonstrating RAM and context-window filtering. They are not
specifications, benchmarks, or claims about real Meta Llama models or hardware.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping, Sequence

# Synthetic teaching fixtures (not real model specifications).
SYNTHETIC_MANIFEST: tuple[dict[str, Any], ...] = (
    {
        "name": "Fixture A",
        "min_ram_gb": 4,
        "max_context_tokens": 2048,
    },
    {
        "name": "Fixture B",
        "min_ram_gb": 8,
        "max_context_tokens": 4096,
    },
)

DEFAULT_RAM_BUDGET_GB = 6
DEFAULT_REQUESTED_CONTEXT_TOKENS = 1024


def _validate_non_bool_number(value: Any, field_name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number, got {type(value).__name__}")
    return value


def _validate_entry(entry: Mapping[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise ValueError(f"manifest[{index}] must be a mapping")
    for key in ("name", "min_ram_gb", "max_context_tokens"):
        if key not in entry:
            raise ValueError(f"manifest[{index}] is missing required field '{key}'")

    name = entry["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"manifest[{index}]['name'] must be a non-empty string")

    min_ram_gb = _validate_non_bool_number(
        entry["min_ram_gb"], f"manifest[{index}]['min_ram_gb']"
    )
    if min_ram_gb < 0:
        raise ValueError(f"manifest[{index}]['min_ram_gb'] must be >= 0")

    max_context_tokens = _validate_non_bool_number(
        entry["max_context_tokens"], f"manifest[{index}]['max_context_tokens']"
    )
    if isinstance(max_context_tokens, float) or max_context_tokens <= 0:
        raise ValueError(
            f"manifest[{index}]['max_context_tokens'] must be a positive integer"
        )

    return {
        "name": name,
        "min_ram_gb": min_ram_gb,
        "max_context_tokens": max_context_tokens,
    }


def select_eligible_models(
    manifest: Sequence[Mapping[str, Any]],
    ram_budget_gb: int | float,
    requested_context_tokens: int,
) -> dict[str, Any]:
    """Select synthetic manifest entries that satisfy RAM and context constraints.

    Public inputs mapped to lesson concepts:
    - manifest: Synthetic model catalog representing varied deployment footprints
      and context limits (analogous to edge vs. larger Llama variants).
    - ram_budget_gb: Simulated host/edge memory budget.
    - requested_context_tokens: Application context window needed (e.g., RAG or
      tool-calling prompts).

    Public outputs mapped to lesson concepts:
    - simulation: Explicitly marks the result as a synthetic local simulation.
    - eligible: Entries whose min_ram_gb <= ram_budget_gb and
      max_context_tokens >= requested_context_tokens.
    - excluded: Entries rejected with explicit per-constraint failure reasons.
    """
    budget = _validate_non_bool_number(ram_budget_gb, "ram_budget_gb")
    if budget < 0:
        raise ValueError("ram_budget_gb must be >= 0")

    requested_ctx = _validate_non_bool_number(
        requested_context_tokens, "requested_context_tokens"
    )
    if isinstance(requested_ctx, float) or requested_ctx <= 0:
        raise ValueError("requested_context_tokens must be a positive integer")

    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for idx, raw_entry in enumerate(manifest):
        entry = _validate_entry(raw_entry, idx)
        reasons: list[str] = []

        if entry["min_ram_gb"] > budget:
            reasons.append(
                f"min_ram_gb {entry['min_ram_gb']} exceeds ram_budget_gb {budget}"
            )
        if entry["max_context_tokens"] < requested_ctx:
            reasons.append(
                f"max_context_tokens {entry['max_context_tokens']} is below "
                f"requested_context_tokens {requested_ctx}"
            )

        if reasons:
            excluded.append({**entry, "reasons": reasons})
        else:
            eligible.append(entry)

    return {
        "simulation": True,
        "ram_budget_gb": budget,
        "requested_context_tokens": requested_ctx,
        "eligible": eligible,
        "excluded": excluded,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate selecting eligible synthetic model entries by RAM budget "
            "and requested context tokens."
        )
    )
    parser.add_argument(
        "--ram-budget",
        type=int,
        default=DEFAULT_RAM_BUDGET_GB,
        help=f"Simulated RAM budget in GB (default: {DEFAULT_RAM_BUDGET_GB})",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=DEFAULT_REQUESTED_CONTEXT_TOKENS,
        help=(
            "Requested context window in tokens "
            f"(default: {DEFAULT_REQUESTED_CONTEXT_TOKENS})"
        ),
    )
    args = parser.parse_args(argv)

    try:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=args.ram_budget,
            requested_context_tokens=args.context,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
