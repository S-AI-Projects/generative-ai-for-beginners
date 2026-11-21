"""
R40-T046 · Applied Lab: Introduction to Small Language Models
=============================================================

This module illustrates Lesson 19 ("Introduction to Small Language Models")
through a **prompt-budget checker** — a preflight step that tokenizes a prompt,
checks token count against a configured budget, retains only as many tokens
as the budget allows, and reports truncation explicitly.

Lesson connection
-----------------
Lesson 19 explains that SLMs run in resource-constrained environments
(mobile, edge, embedded devices) where memory and compute are strictly
limited. Before sending a prompt to a Phi model (or any SLM), an application
must:
  1. **Tokenize** the prompt to count resource units.
  2. **Check** the count against the deployment's token budget.
  3. **Truncate** to the budget if needed and **report** how many tokens
     were removed so the developer can tune prompts accordingly.

Here we capture that three-step preflight in a ``TokenBudgetChecker`` class
and supply a ``WhitespaceTokenizer`` — a whitespace-split teaching
approximation. The tokenizer is **explicitly labelled** as an approximation
(see below); a production deployment would use the model's real tokenizer
(e.g., ``tiktoken`` for GPT-family, ``sentencepiece`` for Phi).

Design: baseline then extracted responsibility
----------------------------------------------
The task requires:
  "Implement a correct baseline, then extract one named responsibility."

Baseline (``_baseline_check``)
  A single function that tokenizes, truncates, and reports — all inlined.

Extracted responsibility (``TokenizerInterface`` + ``WhitespaceTokenizer``)
  Tokenization is lifted out behind a Protocol so any tokenizer can be
  swapped in without touching the budget logic. The contract (inputs,
  outputs, error conditions) is identical before and after the extraction.
  Equivalence is proved in ``TestBaselineEquivalence``.

Tokenizer label — TEACHING APPROXIMATION
-----------------------------------------
``WhitespaceTokenizer`` splits on whitespace.  This is **not** the real
tokenizer used by Phi-3/3.5/4 or any production SLM.  Real tokenizers
(BPE, SentencePiece, WordPiece) may split a single word into multiple
sub-word tokens, merge common word pairs, or handle Unicode differently.
Counts from ``WhitespaceTokenizer`` will differ from real model counts.
  → Label: **TEACHING APPROXIMATION — not the model's real tokenizer.**

Simplification boundary
-----------------------
This module does NOT:
  • Download or load any model weights.
  • Connect to any cloud service or API.
  • Use GPU or hardware acceleration.
  • Measure real model memory or compute.
  • Use the actual tokenizer of Phi-3/3.5/4 or any other SLM.

Three scenarios
---------------
1. **Normal**: budget=3, prompt="one two three four" → retains ["one","two","three"],
   reports 1 removed token.
2. **Boundary**: budget=0 or empty prompt → retains [], reports 0 removed
   (empty-input case) or all tokens removed (zero-budget case).
3. **Failure**: negative budget → ValueError with explanation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


# ===========================================================================
# TEACHING APPROXIMATION label
# ===========================================================================

TOKENIZER_LABEL = (
    "TEACHING APPROXIMATION — whitespace split only. "
    "This is NOT the real tokenizer used by Phi-3/3.5/4 or any production SLM. "
    "Real SLM tokenizers (BPE, SentencePiece) may produce different token counts."
)


# ===========================================================================
# Domain types
# ===========================================================================

@dataclass(frozen=True)
class BudgetReport:
    """
    Result of a single prompt-budget preflight check.

    Attributes
    ----------
    retained_tokens : list[str]
        The tokens kept within the budget (in original order).
    removed_count : int
        Number of tokens removed by truncation.
    budget : int
        The configured token budget used for this check.
    tokenizer_label : str
        Human-readable label describing the tokenizer's accuracy.
        Always set to ``TOKENIZER_LABEL`` for the teaching approximation.
    """

    retained_tokens: tuple[str, ...]
    removed_count: int
    budget: int
    tokenizer_label: str = TOKENIZER_LABEL


# ===========================================================================
# Extracted responsibility: TokenizerInterface (Protocol)
# ===========================================================================

class TokenizerInterface(Protocol):
    """
    Callable interface for the tokenization responsibility.

    Any object satisfying this Protocol can be used by ``TokenBudgetChecker``.
    In production this would wrap ``tiktoken``, ``sentencepiece``, or the
    Phi model's own tokenizer; in this lab it is ``WhitespaceTokenizer``.
    """

    def tokenize(self, text: str) -> list[str]:
        """Split *text* into tokens. Must return a list (possibly empty)."""
        ...


# ===========================================================================
# TEACHING APPROXIMATION tokenizer
# ===========================================================================

class WhitespaceTokenizer:
    """
    **[TEACHING APPROXIMATION]** Tokenizer that splits on whitespace.

    This is NOT the real tokenizer of any SLM or LLM.
    See ``TOKENIZER_LABEL`` for the full disclaimer.

    Real-tokenizer behaviour this approximation does NOT establish
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - Sub-word splitting: "tokenization" might become ["token","ization"].
    - Special tokens: BOS, EOS, PAD, SEP are not inserted.
    - Unicode handling: emoji, CJK, RTL scripts are not normalised.
    - Byte-pair merges: common word pairs are not merged into one token.
    - Case normalisation varies by model.
    """

    def tokenize(self, text: str) -> list[str]:  # noqa: D102
        return text.split()


# ===========================================================================
# Baseline implementation (single function, inlined responsibility)
# ===========================================================================

def _baseline_check(prompt: str, budget: int) -> BudgetReport:
    """
    Correct baseline: tokenize, check budget, truncate, report.

    This function is kept verbatim to prove equivalence with the
    class-based version that extracts tokenization as a named responsibility.

    Raises
    ------
    ValueError
        If *budget* is negative.
    """
    if budget < 0:
        raise ValueError(
            f"[R40-T046] Token budget must be >= 0, got {budget}. "
            "A negative budget has no meaningful interpretation for a "
            "resource-constrained SLM deployment."
        )
    # Inlined tokenization (whitespace split)
    tokens = prompt.split()
    retained = tokens[:budget]
    removed = max(0, len(tokens) - budget)
    return BudgetReport(
        retained_tokens=tuple(retained),
        removed_count=removed,
        budget=budget,
    )


# ===========================================================================
# Refactored implementation: extracted tokenization responsibility
# ===========================================================================

class TokenBudgetChecker:
    """
    Prompt-budget preflight checker with tokenization as an extracted,
    named responsibility.

    Parameters
    ----------
    budget : int
        Maximum number of tokens allowed.  Must be >= 0.
    tokenizer : TokenizerInterface
        Any object satisfying ``TokenizerInterface``.  Defaults to
        ``WhitespaceTokenizer`` (teaching approximation).

    Contract (identical to ``_baseline_check``)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - budget=3, "one two three four" → retained=("one","two","three"), removed=1
    - empty prompt → retained=(), removed=0
    - budget=0, any prompt → retained=(), removed=len(tokens)
    - negative budget → ValueError

    The same contract is verified by ``TestBaselineEquivalence``.
    """

    def __init__(
        self,
        budget: int,
        tokenizer: TokenizerInterface | None = None,
    ) -> None:
        if budget < 0:
            raise ValueError(
                f"[R40-T046] Token budget must be >= 0, got {budget}. "
                "A negative budget has no meaningful interpretation for a "
                "resource-constrained SLM deployment."
            )
        self.budget = budget
        self.tokenizer: TokenizerInterface = tokenizer or WhitespaceTokenizer()

    def check(self, prompt: str) -> BudgetReport:
        """
        Run the preflight check on *prompt*.

        Returns
        -------
        BudgetReport
            Contains retained tokens, removed count, budget, and tokenizer label.
        """
        tokens = self.tokenizer.tokenize(prompt)
        retained = tokens[: self.budget]
        removed = max(0, len(tokens) - self.budget)
        return BudgetReport(
            retained_tokens=tuple(retained),
            removed_count=removed,
            budget=self.budget,
        )
