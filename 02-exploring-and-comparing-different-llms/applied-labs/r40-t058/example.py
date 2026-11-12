"""Deterministic local whitespace-token budget fixture and comparison lab for Lesson 02.

Illustrates prompt-length / context-window boundaries when comparing LLM configurations
from 02-exploring-and-comparing-different-llms/README.md. Uses Python standard library
whitespace splitting as an explicit teaching approximation, NOT a model's real tokenizer.

Purely local simulation: no model download, paid provider, GPU, or physical device is used,
and no real-world model accuracy, latency, hardware, or cloud cost is claimed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

TOKENIZER_KIND = "whitespace_teaching_approximation"
TOKENIZER_NOTICE = (
    "Teaching approximation only (str.split whitespace splitting), not a model's real "
    "subword/BPE tokenizer."
)

FIXTURE_CASES: dict[str, dict[str, Any]] = {
    "budget3": {
        "prompt": "one two three four",
        "budget": 3,
    },
    "empty": {
        "prompt": "",
        "budget": 3,
    },
    "negative": {
        "prompt": "one two three four",
        "budget": -1,
    },
}

CONTROLLED_COMPARISON_CONFIGS: tuple[dict[str, Any], ...] = (
    {
        "config_id": "tight_budget_2",
        "description": "Tight preflight budget retaining 2 tokens",
        "prompt": "one two three four",
        "budget": 2,
        "expected_retained_tokens": ["one", "two"],
        "expected_removed_count": 2,
        "expected_truncated": True,
    },
    {
        "config_id": "fixture_budget_3",
        "description": "Reference fixture budget retaining 3 tokens",
        "prompt": "one two three four",
        "budget": 3,
        "expected_retained_tokens": ["one", "two", "three"],
        "expected_removed_count": 1,
        "expected_truncated": True,
    },
    {
        "config_id": "full_budget_4",
        "description": "Sufficient budget retaining all 4 tokens",
        "prompt": "one two three four",
        "budget": 4,
        "expected_retained_tokens": ["one", "two", "three", "four"],
        "expected_removed_count": 0,
        "expected_truncated": False,
    },
)


def tokenize_whitespace_approx(prompt: str) -> list[str]:
    """Split prompt on whitespace as a teaching approximation of tokenization."""
    if not isinstance(prompt, str):
        raise ValueError("Prompt must be a string")
    return prompt.split()


def check_prompt_budget(prompt: str, budget: int) -> dict[str, Any]:
    """Check whitespace-token prompt length against budget and report truncation."""
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("Prompt token budget must be a non-negative integer")

    tokens = tokenize_whitespace_approx(prompt)
    retained_tokens = tokens[:budget]
    removed_tokens = tokens[budget:]
    input_token_count = len(tokens)
    retention_ratio = (
        round(len(retained_tokens) / input_token_count, 4)
        if input_token_count > 0
        else None
    )

    return {
        "simulation": True,
        "tokenizer_kind": TOKENIZER_KIND,
        "tokenizer_notice": TOKENIZER_NOTICE,
        "budget": budget,
        "input_token_count": input_token_count,
        "retained_tokens": retained_tokens,
        "retained_count": len(retained_tokens),
        "removed_tokens": removed_tokens,
        "removed_count": len(removed_tokens),
        "truncated": len(removed_tokens) > 0,
        "retention_ratio": retention_ratio,
    }


def compare_controlled_configs(
    configs: Sequence[dict[str, Any]] = CONTROLLED_COMPARISON_CONFIGS,
) -> dict[str, Any]:
    """Compare three controlled budget configurations using token_retention_ratio."""
    comparisons: list[dict[str, Any]] = []
    for cfg in configs:
        result = check_prompt_budget(cfg["prompt"], cfg["budget"])
        correct = (
            result["retained_tokens"] == cfg["expected_retained_tokens"]
            and result["removed_count"] == cfg["expected_removed_count"]
            and result["truncated"] is cfg["expected_truncated"]
        )
        comparisons.append(
            {
                "config_id": cfg["config_id"],
                "description": cfg["description"],
                "budget": cfg["budget"],
                "input_token_count": result["input_token_count"],
                "retained_tokens": result["retained_tokens"],
                "removed_count": result["removed_count"],
                "truncated": result["truncated"],
                "retention_ratio": result["retention_ratio"],
                "correct": correct,
            }
        )

    return {
        "simulation": True,
        "tokenizer_kind": TOKENIZER_KIND,
        "tokenizer_notice": TOKENIZER_NOTICE,
        "metric": "token_retention_ratio (retained_count / input_token_count)",
        "all_correct": all(item["correct"] for item in comparisons),
        "trade_off_summary": (
            "Across budgets 2, 3, and 4 on the 4-token prompt 'one two three four', "
            "tightening the budget lowers token_retention_ratio (1.00 -> 0.75 -> 0.50) "
            "and drops more tail tokens (0 -> 1 -> 2). This measures whitespace-budget "
            "truncation only and makes no claim about real-world model accuracy."
        ),
        "configurations": comparisons,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Lesson 02 whitespace-token budget fixture (teaching approximation) "
            "and compare controlled budget configurations."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", *FIXTURE_CASES.keys(), "compare"),
        default="all",
        help="Fixture or comparison case to run (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        if args.case in FIXTURE_CASES:
            fixture = FIXTURE_CASES[args.case]
            payload = check_prompt_budget(fixture["prompt"], fixture["budget"])
        elif args.case == "compare":
            payload = compare_controlled_configs()
        else:
            payload = {
                "simulation": True,
                "tokenizer_kind": TOKENIZER_KIND,
                "tokenizer_notice": TOKENIZER_NOTICE,
                "budget3_fixture": check_prompt_budget(
                    FIXTURE_CASES["budget3"]["prompt"],
                    FIXTURE_CASES["budget3"]["budget"],
                ),
                "empty_fixture": check_prompt_budget(
                    FIXTURE_CASES["empty"]["prompt"],
                    FIXTURE_CASES["empty"]["budget"],
                ),
                "controlled_comparison": compare_controlled_configs(),
            }
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
