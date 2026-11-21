"""
R40-T048 · Applied Lab: Prompt Budget Preflight with Intermediate State Invariants
==================================================================================

This module illustrates Lesson 19 ("Introduction to Small Language Models")
through a **step-by-step prompt token budget checker** for resource-constrained
SLMs (e.g., Microsoft Phi family deployed on edge/mobile devices).

Lesson connection
-----------------
In edge and mobile deployments of SLMs, available memory and context window
limits are constrained. A preflight step validates prompt length against the
configured token budget before model inference.

To ensure safety and auditability, this implementation:
  1. Executes a discrete multi-step pipeline:
     - Step 1: Input Validation
     - Step 2: Tokenization (using a teaching approximation)
     - Step 3: Budget Comparison & Slice Planning
     - Step 4: Truncation
     - Step 5: Final Report Generation
  2. **Records the intermediate state after each step** into an execution trace.
  3. Formally asserts the **invariants linking intermediate states to the final output**:
     - Token Conservation: len(tokenized_tokens) == len(retained_tokens) + removed_count
     - Sequence Reconstitution: tokenized_tokens == retained_tokens + removed_tokens
     - Bounded Capacity: len(retained_tokens) <= budget
     - Prefix Preservation: tokenized_tokens[:len(retained_tokens)] == retained_tokens

Tokenizer disclaimer — TEACHING APPROXIMATION
---------------------------------------------
WhitespaceTokenizer splits purely on whitespace. This is **not** the real
tokenizer of Phi-3/3.5/4 or any production SLM. Production models use sub-word
tokenizers (e.g. BPE, SentencePiece) with special tokens and Unicode normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TOKENIZER_LABEL = (
    "TEACHING APPROXIMATION — whitespace split only. "
    "This is NOT the real tokenizer used by Phi-3/3.5/4 or any production SLM. "
    "Real SLM tokenizers (BPE, SentencePiece) produce sub-word tokens."
)


@dataclass(frozen=True)
class StepRecord:
    """
    Snapshot of intermediate pipeline state after an individual execution step.
    """
    step_number: int
    step_name: str
    snapshot: dict[str, Any]


@dataclass(frozen=True)
class BudgetReport:
    """
    Final output of the prompt-budget preflight check.

    Attributes
    ----------
    retained_tokens : tuple[str, ...]
        Tokens kept within the budget in original order.
    removed_count : int
        Number of tokens removed by truncation.
    budget : int
        Configured token limit.
    tokenizer_label : str
        Explicit label identifying the tokenizer approximation.
    trace : tuple[StepRecord, ...]
        Ordered intermediate state records captured after each pipeline step.
    """
    retained_tokens: tuple[str, ...]
    removed_count: int
    budget: int
    tokenizer_label: str
    trace: tuple[StepRecord, ...]


class WhitespaceTokenizer:
    """
    Teaching approximation tokenizer that splits on whitespace.
    """
    def tokenize(self, text: str) -> list[str]:
        return text.split()


class PromptBudgetPipeline:
    """
    Executes prompt budget checks while recording intermediate state after each step.
    """

    def __init__(self, tokenizer: WhitespaceTokenizer | None = None) -> None:
        self.tokenizer = tokenizer or WhitespaceTokenizer()

    def run(self, prompt: str, budget: int) -> BudgetReport:
        """
        Run the preflight pipeline, recording intermediate states after every step.

        Parameters
        ----------
        prompt : str
            The input prompt string to evaluate.
        budget : int
            The maximum number of tokens allowed (must be >= 0).

        Returns
        -------
        BudgetReport
            Final report containing retained tokens, removed count, budget,
            tokenizer label, and full intermediate state execution trace.

        Raises
        ------
        ValueError
            If budget is negative (< 0).
        """
        trace: list[StepRecord] = []

        # Step 1: Validation
        if budget < 0:
            raise ValueError(
                f"[R40-T048] Budget must be >= 0, got {budget}. "
                "Negative budgets are invalid in SLM deployments."
            )
        trace.append(StepRecord(
            step_number=1,
            step_name="VALIDATE_INPUT",
            snapshot={"budget": budget, "prompt_length": len(prompt)},
        ))

        # Step 2: Tokenization
        raw_tokens = tuple(self.tokenizer.tokenize(prompt))
        trace.append(StepRecord(
            step_number=2,
            step_name="TOKENIZATION",
            snapshot={
                "tokens": raw_tokens,
                "token_count": len(raw_tokens),
            },
        ))

        # Step 3: Budget Evaluation & Planning
        initial_count = len(raw_tokens)
        planned_retained_count = min(initial_count, budget)
        planned_removed_count = max(0, initial_count - budget)
        trace.append(StepRecord(
            step_number=3,
            step_name="EVALUATE_BUDGET",
            snapshot={
                "initial_count": initial_count,
                "budget": budget,
                "planned_retained_count": planned_retained_count,
                "planned_removed_count": planned_removed_count,
                "exceeds_budget": initial_count > budget,
            },
        ))

        # Step 4: Truncation
        retained = raw_tokens[:planned_retained_count]
        removed = raw_tokens[planned_retained_count:]
        trace.append(StepRecord(
            step_number=4,
            step_name="TRUNCATION",
            snapshot={
                "retained_tokens": retained,
                "removed_tokens": removed,
                "actual_retained_count": len(retained),
                "actual_removed_count": len(removed),
            },
        ))

        # Step 5: Final Report Generation
        report = BudgetReport(
            retained_tokens=retained,
            removed_count=len(removed),
            budget=budget,
            tokenizer_label=TOKENIZER_LABEL,
            trace=tuple(trace),
        )
        return report


def verify_pipeline_invariants(report: BudgetReport) -> bool:
    """
    Formally test the invariants linking intermediate step states to the final output.

    Invariants checked:
      1. Trace Completeness: exactly 4 intermediate steps recorded prior to final report.
      2. Token Conservation:
         Step 2 token_count == len(final retained_tokens) + final removed_count
      3. Sequence Reconstitution:
         Step 2 tokens == final retained_tokens + Step 4 removed_tokens
      4. Bounded Output:
         len(final retained_tokens) <= final budget
      5. Prefix Preservation:
         Step 2 tokens[:len(final retained_tokens)] == final retained_tokens
      6. Truncation Equivalence:
         Step 3 planned counts equal Step 4 actual counts and final report counts.

    Returns True if all invariants hold; raises AssertionError otherwise.
    """
    trace_dict = {step.step_name: step.snapshot for step in report.trace}

    # Invariant 1: Completeness
    expected_steps = {"VALIDATE_INPUT", "TOKENIZATION", "EVALUATE_BUDGET", "TRUNCATION"}
    if not expected_steps.issubset(trace_dict.keys()):
        raise AssertionError("Trace missing required intermediate steps.")

    tok_snap = trace_dict["TOKENIZATION"]
    eval_snap = trace_dict["EVALUATE_BUDGET"]
    trunc_snap = trace_dict["TRUNCATION"]

    initial_tokens: tuple[str, ...] = tok_snap["tokens"]
    removed_tokens: tuple[str, ...] = trunc_snap["removed_tokens"]

    # Invariant 2: Conservation of tokens
    if len(initial_tokens) != len(report.retained_tokens) + report.removed_count:
        raise AssertionError("Invariant violation: Token conservation failed.")

    # Invariant 3: Sequence reconstitution
    if initial_tokens != (report.retained_tokens + removed_tokens):
        raise AssertionError("Invariant violation: Sequence reconstitution failed.")

    # Invariant 4: Bounded capacity
    if len(report.retained_tokens) > report.budget:
        raise AssertionError("Invariant violation: Retained count exceeds budget.")

    # Invariant 5: Prefix preservation
    if initial_tokens[:len(report.retained_tokens)] != report.retained_tokens:
        raise AssertionError("Invariant violation: Prefix preservation failed.")

    # Invariant 6: Truncation planning vs actual counts
    if eval_snap["planned_retained_count"] != len(report.retained_tokens):
        raise AssertionError("Invariant violation: Planned retained does not match output.")
    if eval_snap["planned_removed_count"] != report.removed_count:
        raise AssertionError("Invariant violation: Planned removed does not match output.")

    return True
