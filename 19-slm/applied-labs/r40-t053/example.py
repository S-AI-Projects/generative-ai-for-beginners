#!/usr/bin/env python3
"""Minimal local example: a whitespace-token preflight check against a
configured budget, with retained tokens and truncation reported explicitly.

Teaching fixture only. This file performs no model download, no remote API
call, no GPU and no network access.

> **Tokenizer disclaimer**: ``tokenize_whitespace`` below is a teaching
> approximation -- plain whitespace splitting. It is **not** the real
> subword/BPE tokenizer used by Phi-3/3.5 or any other SLM/LLM, and token
> counts it produces do not predict a real model's token usage, context
> window consumption, or billing.

Public inputs and outputs, connected to lesson concepts
--------------------------------------------------------
- Tokenization boundary (lesson: SLMs run in resource-constrained
    environments, so what counts as a "token" and where a prompt gets cut
    off matters)
    tokenize_whitespace, count_tokens_naive
- Resource budget (lesson: SLMs are built for limited computational
    footprints -- a token budget stands in for that constraint)
    apply_token_budget(text, budget)
- Preflight reporting (lesson: knowing ahead of inference whether a prompt
    fits, and exactly what gets dropped if it does not)
    TokenBudgetResult.retained / removed_count / truncated
"""

from __future__ import annotations

from dataclasses import dataclass


def tokenize_whitespace(text: str) -> list[str]:
    """Split ``text`` into tokens on whitespace.

    Teaching approximation only -- not the model's real tokenizer. This is
    the "direct implementation" referenced below; it is cross-checked
    against :func:`count_tokens_naive`, a deliberately simpler, independent
    way of counting tokens on the same input.
    """
    return text.split()


def count_tokens_naive(text: str) -> int:
    """Count whitespace-separated tokens by scanning characters directly.

    This is an independent calculation from :func:`tokenize_whitespace`: it
    never calls ``str.split()`` and instead walks ``text`` one character at
    a time, counting each whitespace-to-non-whitespace transition. It
    exists only so tests can compare it against ``len(tokenize_whitespace
    (text))`` on identical inputs as a cross-check, not as a second
    production tokenizer.
    """
    count = 0
    in_token = False
    for ch in text:
        if ch.isspace():
            in_token = False
        else:
            if not in_token:
                count += 1
            in_token = True
    return count


@dataclass(frozen=True)
class TokenBudgetResult:
    """Explicit preflight report for one (text, budget) pair."""

    text: str
    budget: int
    tokens: tuple[str, ...]
    retained: tuple[str, ...]
    removed_count: int
    truncated: bool


def apply_token_budget(text: str, budget: int) -> TokenBudgetResult:
    """Check ``text`` against ``budget`` whitespace tokens.

    Retains the first ``budget`` tokens (in order) and reports how many
    were removed. A negative budget is rejected with ``ValueError`` --
    there is no meaningful "negative capacity" to truncate to.
    """
    if budget < 0:
        raise ValueError(f"budget must be >= 0, got {budget}")

    tokens = tuple(tokenize_whitespace(text))
    retained = tokens[:budget]
    removed_count = len(tokens) - len(retained)

    return TokenBudgetResult(
        text=text,
        budget=budget,
        tokens=tokens,
        retained=retained,
        removed_count=removed_count,
        truncated=removed_count > 0,
    )


# ---------------------------------------------------------------------------
# Demo entry point (minimal complete example).
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Run the headline fixture and print the lesson-linked trace."""
    text = "one two three four"
    budget = 3
    result = apply_token_budget(text, budget)

    print("[LESSON: tokenization boundary] tokenizer=whitespace (teaching approximation, not a real model tokenizer)")
    print("  text=%r -> tokens=%s" % (text, list(result.tokens)))
    print("[LESSON: resource budget] budget=%d" % budget)
    print(
        "[LESSON: preflight reporting] retained=%s removed_count=%d truncated=%s"
        % (list(result.retained), result.removed_count, result.truncated)
    )

    # Cross-check: direct implementation vs. the simpler independent count.
    direct_count = len(tokenize_whitespace(text))
    naive_count = count_tokens_naive(text)
    print(
        "[LESSON: compare implementations] tokenize_whitespace count=%d vs count_tokens_naive count=%d -> agree=%s"
        % (direct_count, naive_count, direct_count == naive_count)
    )

    empty_result = apply_token_budget("", 5)
    print(
        "[LESSON: boundary] empty input -> retained=%s removed_count=%d truncated=%s"
        % (list(empty_result.retained), empty_result.removed_count, empty_result.truncated)
    )


if __name__ == "__main__":
    run_demo()
