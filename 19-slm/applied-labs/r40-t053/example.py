"""Local whitespace-token prompt-budget simulation for Lesson 19 (SLMs).

Approximates prompt tokenization using whitespace splitting purely as a
deterministic teaching fixture—this is NOT the real tokenizer of Phi-3/3.5 or
any production SLM, and makes no claims about real hardware or model behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

TOKENIZER_APPROXIMATION_NOTE = (
    "whitespace teaching approximation, not the model's real tokenizer"
)

# Explicit expected-result table for identical fixture inputs.
EXPECTED_FIXTURE_TABLE: tuple[dict[str, Any], ...] = (
    {
        "case": "normal_budget_3_truncates_one",
        "prompt": "one two three four",
        "budget": 3,
        "expected": {
            "total_tokens": 4,
            "retained_tokens": ["one", "two", "three"],
            "retained_count": 3,
            "removed_tokens": ["four"],
            "removed_count": 1,
            "truncated": True,
        },
    },
    {
        "case": "boundary_exact_fit",
        "prompt": "one two three",
        "budget": 3,
        "expected": {
            "total_tokens": 3,
            "retained_tokens": ["one", "two", "three"],
            "retained_count": 3,
            "removed_tokens": [],
            "removed_count": 0,
            "truncated": False,
        },
    },
    {
        "case": "boundary_empty_input",
        "prompt": "",
        "budget": 3,
        "expected": {
            "total_tokens": 0,
            "retained_tokens": [],
            "retained_count": 0,
            "removed_tokens": [],
            "removed_count": 0,
            "truncated": False,
        },
    },
    {
        "case": "boundary_zero_budget",
        "prompt": "one two",
        "budget": 0,
        "expected": {
            "total_tokens": 2,
            "retained_tokens": [],
            "retained_count": 0,
            "removed_tokens": ["one", "two"],
            "removed_count": 2,
            "truncated": True,
        },
    },
)


def _validate_inputs(prompt: str, budget: int) -> int:
    if not isinstance(prompt, str):
        raise ValueError(f"prompt must be a str, got {type(prompt).__name__}")
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise ValueError(f"budget must be an int, got {type(budget).__name__}")
    if budget < 0:
        raise ValueError("budget must be >= 0")
    return budget


def check_prompt_budget(prompt: str, budget: int) -> dict[str, Any]:
    """Direct implementation using slice-based whitespace token budgeting."""
    valid_budget = _validate_inputs(prompt, budget)
    tokens = prompt.split()
    retained = tokens[:valid_budget]
    removed = tokens[valid_budget:]

    return {
        "simulation": True,
        "tokenizer_note": TOKENIZER_APPROXIMATION_NOTE,
        "prompt": prompt,
        "budget": valid_budget,
        "total_tokens": len(tokens),
        "retained_tokens": retained,
        "retained_count": len(retained),
        "removed_tokens": removed,
        "removed_count": len(removed),
        "truncated": len(removed) > 0,
    }


def independent_budget_calculation(prompt: str, budget: int) -> dict[str, Any]:
    """Simpler independent calculation without list slicing for cross-checking."""
    valid_budget = _validate_inputs(prompt, budget)
    tokens = prompt.split()
    total = len(tokens)
    retained: list[str] = []
    removed: list[str] = []

    for index, token in enumerate(tokens):
        if index < valid_budget:
            retained.append(token)
        else:
            removed.append(token)

    retained_count = min(total, valid_budget)
    removed_count = max(0, total - valid_budget)
    return {
        "total_tokens": total,
        "retained_tokens": retained,
        "retained_count": retained_count,
        "removed_tokens": removed,
        "removed_count": removed_count,
        "truncated": total > valid_budget,
    }


def run_comparison_fixtures() -> dict[str, Any]:
    """Compare direct implementation, independent calculation, and expected table."""
    comparable_keys = (
        "total_tokens",
        "retained_tokens",
        "retained_count",
        "removed_tokens",
        "removed_count",
        "truncated",
    )
    comparisons: list[dict[str, Any]] = []

    for row in EXPECTED_FIXTURE_TABLE:
        prompt = row["prompt"]
        budget = row["budget"]
        direct = check_prompt_budget(prompt, budget)
        independent = independent_budget_calculation(prompt, budget)

        direct_summary = {key: direct[key] for key in comparable_keys}
        comparisons.append(
            {
                "case": row["case"],
                "prompt": prompt,
                "budget": budget,
                "direct_result": direct,
                "independent_result": independent,
                "expected_table_result": row["expected"],
                "matches_independent": direct_summary == independent,
                "matches_expected_table": direct_summary == row["expected"],
            }
        )

    invalid_budget_rejected = False
    invalid_budget_error: str | None = None
    try:
        check_prompt_budget("one two", -1)
    except ValueError as exc:
        invalid_budget_rejected = True
        invalid_budget_error = str(exc)

    return {
        "simulation": True,
        "tokenizer_note": TOKENIZER_APPROXIMATION_NOTE,
        "comparisons": comparisons,
        "invalid_negative_budget": {
            "prompt": "one two",
            "budget": -1,
            "rejected": invalid_budget_rejected,
            "error": invalid_budget_error,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check prompt whitespace-token length against a budget using a "
            "teaching approximation."
        )
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Optional prompt text to check directly (requires --budget).",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=None,
        help="Non-negative integer token budget for direct check.",
    )
    args = parser.parse_args(argv)

    if args.prompt is not None or args.budget is not None:
        if args.prompt is None or args.budget is None:
            print("Error: --prompt and --budget must be provided together", file=sys.stderr)
            return 2
        try:
            direct = check_prompt_budget(args.prompt, args.budget)
            independent = independent_budget_calculation(args.prompt, args.budget)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        payload = {
            "simulation": True,
            "tokenizer_note": TOKENIZER_APPROXIMATION_NOTE,
            "direct_result": direct,
            "independent_result": independent,
            "matches_independent": all(
                direct[k] == independent[k] for k in independent
            ),
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(json.dumps(run_comparison_fixtures(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
