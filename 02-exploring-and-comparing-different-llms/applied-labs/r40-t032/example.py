"""
Token-Budget Preflight & Truncation with Failure Recovery (R40-T032).

Deterministic local whitespace-token preflight checker for prompt length budgeting.
Note: The tokenizer used here is a teaching approximation (whitespace-based splitting),
not the model's real subword/BPE tokenizer.
"""

from typing import List, Dict, Any, Optional


class TokenBudgetPreflight:
    """
    Deterministic whitespace token budget checker.
    Labels tokenization explicitly as an educational approximation.
    """
    TOKENIZER_LABEL = "Teaching approximation (whitespace-based, not real model BPE tokenizer)"

    def __init__(self, budget: int):
        if not isinstance(budget, int) or budget < 0:
            raise ValueError(f"Negative or invalid budget rejected: {budget}. Budget must be non-negative integer.")
        self.budget = budget
        self.last_error: Optional[str] = None
        self.recovered: bool = False

    def tokenize(self, text: str) -> List[str]:
        """Teaching approximation: splits on whitespace."""
        if not text:
            return []
        return text.strip().split()

    def process(self, prompt: Any) -> Dict[str, Any]:
        """
        Validates prompt against token budget and handles deterministic truncation.
        Raises ValueError/TypeError on invalid/missing data.
        Records error and supports stateful recovery demonstration on subsequent valid input.
        """
        if prompt is None:
            self.last_error = "Invalid/missing data: prompt cannot be None."
            raise ValueError(self.last_error)

        if not isinstance(prompt, str):
            self.last_error = f"Invalid data type: prompt must be string, got {type(prompt).__name__}."
            raise TypeError(self.last_error)

        # Check if recovering from a previous documented failure
        if self.last_error is not None:
            self.recovered = True
            self.last_error = None

        tokens = self.tokenize(prompt)
        total_tokens = len(tokens)

        if total_tokens <= self.budget:
            retained = tokens
            removed_count = 0
            is_truncated = False
        else:
            retained = tokens[:self.budget]
            removed_count = total_tokens - self.budget
            is_truncated = True

        return {
            "prompt": prompt,
            "budget": self.budget,
            "total_tokens": total_tokens,
            "retained_tokens": retained,
            "removed_count": removed_count,
            "is_truncated": is_truncated,
            "tokenizer": self.TOKENIZER_LABEL,
            "recovered_from_previous_error": self.recovered,
            "status": "SUCCESS",
        }
