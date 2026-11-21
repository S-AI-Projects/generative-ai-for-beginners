"""
R40-T046 · Test suite for example.py
======================================

Covers:
  1. Normal scenario        — budget=3, "one two three four"
                              → retained=["one","two","three"], removed=1
  2. Boundary scenario A    — empty prompt → retained=[], removed=0
  3. Boundary scenario B    — budget=0, non-empty prompt → retained=[], removed=N
  4. Boundary scenario C    — budget > token count → all tokens retained, removed=0
  5. Failure scenario       — negative budget → ValueError
  6. Baseline equivalence   — _baseline_check and TokenBudgetChecker produce
                              identical BudgetReports on all fixture inputs
  7. Tokenizer label        — TOKENIZER_LABEL present in every BudgetReport
  8. Deliberate-wrong-result checks — checker exits non-zero on wrong assertion

Run with:
    python3 -m unittest discover -s 19-slm/applied-labs/r40-t046 -p "test_*.py"
or:
    python3 -m unittest 19-slm/applied-labs/r40-t046/test_example -v
"""

import unittest

from example import (
    TOKENIZER_LABEL,
    BudgetReport,
    TokenBudgetChecker,
    WhitespaceTokenizer,
    _baseline_check,
)


# ---------------------------------------------------------------------------
# Scenario 1 — Normal
# ---------------------------------------------------------------------------

class TestNormalScenario(unittest.TestCase):
    """
    Budget 3 with "one two three four":
      - Retains ["one","two","three"]
      - Reports 1 removed token

    Input facts : budget=3, prompt="one two three four"
    Expected    : retained=("one","two","three"), removed=1

    Lesson connection (Lesson 19)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SLMs run in resource-constrained environments. The preflight step
    tokenizes the prompt, checks the budget, and truncates — exactly the
    three-step pipeline described for edge/mobile deployments of Phi models.

    [TEACHING APPROXIMATION] WhitespaceTokenizer is used; a real Phi tokenizer
    would produce different token counts.
    """

    PROMPT = "one two three four"
    BUDGET = 3

    def setUp(self):
        self.checker = TokenBudgetChecker(budget=self.BUDGET)
        self.report = self.checker.check(self.PROMPT)

    def test_retained_tokens(self):
        self.assertEqual(self.report.retained_tokens, ("one", "two", "three"))

    def test_removed_count(self):
        self.assertEqual(self.report.removed_count, 1)

    def test_budget_recorded(self):
        self.assertEqual(self.report.budget, self.BUDGET)

    def test_tokenizer_label_present(self):
        """Every report must carry the TEACHING APPROXIMATION label."""
        self.assertIn("TEACHING APPROXIMATION", self.report.tokenizer_label)
        self.assertIn("NOT the real tokenizer", self.report.tokenizer_label)

    def test_deliberate_wrong_retained_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.retained_tokens, ("one", "two"),
                             "Intentionally wrong: missing third token.")

    def test_deliberate_wrong_removed_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.removed_count, 0,
                             "Intentionally wrong: removed should be 1.")


# ---------------------------------------------------------------------------
# Scenario 2 — Boundary A: empty prompt
# ---------------------------------------------------------------------------

class TestBoundaryEmptyPrompt(unittest.TestCase):
    """
    Empty input retains none.

    Input facts : budget=3, prompt=""
    Expected    : retained=(), removed=0

    Lesson connection
    ~~~~~~~~~~~~~~~~~
    A missing or empty prompt is a common preflight edge case. The checker
    must handle it without error and report zero retained tokens.
    """

    def setUp(self):
        self.checker = TokenBudgetChecker(budget=3)
        self.report = self.checker.check("")

    def test_retained_is_empty(self):
        self.assertEqual(self.report.retained_tokens, ())

    def test_removed_is_zero(self):
        self.assertEqual(self.report.removed_count, 0)

    def test_tokenizer_label_present(self):
        self.assertIn("TEACHING APPROXIMATION", self.report.tokenizer_label)

    def test_deliberate_wrong_retained_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.retained_tokens, ("one",),
                             "Intentionally wrong: empty should stay empty.")


# ---------------------------------------------------------------------------
# Scenario 2 — Boundary B: budget=0
# ---------------------------------------------------------------------------

class TestBoundaryZeroBudget(unittest.TestCase):
    """
    Budget 0 retains nothing, reports all tokens removed.

    Input facts : budget=0, prompt="one two three"
    Expected    : retained=(), removed=3
    """

    def setUp(self):
        self.checker = TokenBudgetChecker(budget=0)
        self.report = self.checker.check("one two three")

    def test_retained_is_empty(self):
        self.assertEqual(self.report.retained_tokens, ())

    def test_removed_equals_token_count(self):
        self.assertEqual(self.report.removed_count, 3)

    def test_deliberate_wrong_removed_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.removed_count, 0,
                             "Intentionally wrong: all tokens should be removed.")


# ---------------------------------------------------------------------------
# Scenario 2 — Boundary C: budget > token count
# ---------------------------------------------------------------------------

class TestBoundaryBudgetExceedsTokens(unittest.TestCase):
    """
    Budget larger than the prompt's token count → all tokens retained, removed=0.

    Input facts : budget=10, prompt="hello world"
    Expected    : retained=("hello","world"), removed=0
    """

    def setUp(self):
        self.checker = TokenBudgetChecker(budget=10)
        self.report = self.checker.check("hello world")

    def test_all_tokens_retained(self):
        self.assertEqual(self.report.retained_tokens, ("hello", "world"))

    def test_removed_is_zero(self):
        self.assertEqual(self.report.removed_count, 0)


# ---------------------------------------------------------------------------
# Scenario 3 — Failure: negative budget
# ---------------------------------------------------------------------------

class TestNegativeBudgetRejected(unittest.TestCase):
    """
    A negative budget is rejected with a ValueError.

    Input facts : budget=-1
    Expected    : ValueError raised with explanation

    Lesson connection
    ~~~~~~~~~~~~~~~~~
    A negative token budget has no meaningful interpretation for a
    resource-constrained SLM deployment. The checker must refuse it
    immediately and explain how to recover (use budget >= 0).
    """

    def test_negative_budget_raises_at_construction(self):
        with self.assertRaises(ValueError) as ctx:
            TokenBudgetChecker(budget=-1)
        self.assertIn("-1", str(ctx.exception))

    def test_error_message_explains_constraint(self):
        with self.assertRaises(ValueError) as ctx:
            TokenBudgetChecker(budget=-5)
        self.assertIn("0", str(ctx.exception))

    def test_deliberate_no_error_fails(self):
        """Checker MUST fail when we incorrectly expect no ValueError."""
        with self.assertRaises(AssertionError):
            try:
                TokenBudgetChecker(budget=-1)
            except ValueError:
                raise AssertionError("ValueError WAS raised (as expected), "
                                     "but we incorrectly claimed it would not be.")

    def test_baseline_also_rejects_negative(self):
        """_baseline_check must also reject negative budget."""
        with self.assertRaises(ValueError):
            _baseline_check("test", -1)


# ---------------------------------------------------------------------------
# Baseline equivalence
# ---------------------------------------------------------------------------

# Fixture inputs to test equivalence across
_EQUIVALENCE_FIXTURES = [
    ("one two three four", 3),
    ("", 3),
    ("one two three", 0),
    ("hello world", 10),
    ("single", 1),
    ("a b c d e", 5),
]


class TestBaselineEquivalence(unittest.TestCase):
    """
    Prove that TokenBudgetChecker (extracted responsibility) produces
    identical BudgetReports to _baseline_check (inlined baseline)
    on all fixture inputs.

    This satisfies the task requirement:
    "Keep the same contract and prove before/after equivalence on the fixture."
    """

    def _assert_equivalent(self, prompt: str, budget: int) -> None:
        baseline = _baseline_check(prompt, budget)
        checker = TokenBudgetChecker(budget=budget)
        refactored = checker.check(prompt)

        self.assertEqual(
            baseline.retained_tokens, refactored.retained_tokens,
            f"retained_tokens differ for prompt={prompt!r}, budget={budget}",
        )
        self.assertEqual(
            baseline.removed_count, refactored.removed_count,
            f"removed_count differs for prompt={prompt!r}, budget={budget}",
        )
        self.assertEqual(
            baseline.budget, refactored.budget,
            f"budget field differs for prompt={prompt!r}, budget={budget}",
        )

    def test_equivalence_normal(self):
        self._assert_equivalent("one two three four", 3)

    def test_equivalence_empty_prompt(self):
        self._assert_equivalent("", 3)

    def test_equivalence_zero_budget(self):
        self._assert_equivalent("one two three", 0)

    def test_equivalence_budget_exceeds_tokens(self):
        self._assert_equivalent("hello world", 10)

    def test_equivalence_single_token(self):
        self._assert_equivalent("single", 1)

    def test_equivalence_exact_budget(self):
        self._assert_equivalent("a b c d e", 5)

    def test_all_fixtures(self):
        """Run all equivalence fixtures in one sweep."""
        for prompt, budget in _EQUIVALENCE_FIXTURES:
            with self.subTest(prompt=prompt, budget=budget):
                self._assert_equivalent(prompt, budget)


# ---------------------------------------------------------------------------
# Tokenizer label
# ---------------------------------------------------------------------------

class TestTokenizerLabel(unittest.TestCase):
    """
    Every BudgetReport must carry the TEACHING APPROXIMATION label,
    explicitly stating this is not the model's real tokenizer.
    """

    def test_label_contains_teaching_approximation(self):
        self.assertIn("TEACHING APPROXIMATION", TOKENIZER_LABEL)

    def test_label_says_not_real_tokenizer(self):
        self.assertIn("NOT the real tokenizer", TOKENIZER_LABEL)

    def test_report_label_matches_constant(self):
        checker = TokenBudgetChecker(budget=3)
        report = checker.check("one two three")
        self.assertEqual(report.tokenizer_label, TOKENIZER_LABEL)

    def test_whitespace_tokenizer_is_deterministic(self):
        """Same input → same tokens every call (not a real model)."""
        tok = WhitespaceTokenizer()
        self.assertEqual(tok.tokenize("one two three"), tok.tokenize("one two three"))

    def test_whitespace_tokenizer_does_not_subword_split(self):
        """
        [TEACHING APPROXIMATION] documents: real tokenizers may split
        "tokenization" into sub-word tokens; this mock does not.
        """
        tok = WhitespaceTokenizer()
        result = tok.tokenize("tokenization")
        # Whitespace split keeps it as one token — different from real BPE
        self.assertEqual(result, ["tokenization"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
