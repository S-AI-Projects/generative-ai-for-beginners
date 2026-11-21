"""
R40-T048 · Test suite for example.py
======================================

Covers:
  1. Normal scenario:
     Budget 3 with "one two three four" retains [one,two,three] and reports 1 removed token.
  2. Boundary scenarios:
     - Empty prompt: retains none, reports 0 removed.
     - Budget 0: retains none, reports all tokens removed.
     - Excess budget: retains all tokens, reports 0 removed.
  3. Failure scenario:
     - Negative budget rejected with ValueError.
  4. Tokenizer labeling:
     - Labeled as a teaching approximation, not the real model tokenizer.
  5. Focus: Intermediate states and invariants:
     - Intermediate state recorded after each step in report.trace.
     - Invariants linking intermediate states to final output verified.
  6. Deliberate wrong result checks:
     - Deliberate incorrect assertion fails with AssertionError.
"""

import unittest

from example import (
    TOKENIZER_LABEL,
    BudgetReport,
    PromptBudgetPipeline,
    StepRecord,
    WhitespaceTokenizer,
    verify_pipeline_invariants,
)


class TestNormalScenario(unittest.TestCase):
    """
    Contract requirement:
      Budget 3 with "one two three four" retains [one,two,three] and reports one removed token.
    """

    def setUp(self):
        self.pipeline = PromptBudgetPipeline()
        self.report = self.pipeline.run("one two three four", budget=3)

    def test_retained_tokens(self):
        self.assertEqual(self.report.retained_tokens, ("one", "two", "three"))

    def test_removed_count(self):
        self.assertEqual(self.report.removed_count, 1)

    def test_budget_value(self):
        self.assertEqual(self.report.budget, 3)

    def test_tokenizer_label_teaching_approximation(self):
        self.assertIn("TEACHING APPROXIMATION", self.report.tokenizer_label)
        self.assertIn("NOT the real tokenizer", self.report.tokenizer_label)

    def test_invariants_pass(self):
        self.assertTrue(verify_pipeline_invariants(self.report))

    def test_deliberate_wrong_retained_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.retained_tokens, ("one", "two"),
                             "Intentional failure to test verification.")

    def test_deliberate_wrong_removed_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.removed_count, 0,
                             "Intentional failure to test verification.")


class TestBoundaryScenarios(unittest.TestCase):
    """
    Contract requirement:
      Empty input retains none.
    Plus zero budget and excess budget boundaries.
    """

    def setUp(self):
        self.pipeline = PromptBudgetPipeline()

    def test_empty_input_retains_none(self):
        report = self.pipeline.run("", budget=3)
        self.assertEqual(report.retained_tokens, ())
        self.assertEqual(report.removed_count, 0)
        self.assertTrue(verify_pipeline_invariants(report))

    def test_zero_budget_retains_none(self):
        report = self.pipeline.run("one two three", budget=0)
        self.assertEqual(report.retained_tokens, ())
        self.assertEqual(report.removed_count, 3)
        self.assertTrue(verify_pipeline_invariants(report))

    def test_excess_budget_retains_all(self):
        report = self.pipeline.run("hello world", budget=10)
        self.assertEqual(report.retained_tokens, ("hello", "world"))
        self.assertEqual(report.removed_count, 0)
        self.assertTrue(verify_pipeline_invariants(report))


class TestFailureScenarios(unittest.TestCase):
    """
    Contract requirement:
      Reject a negative budget.
    """

    def setUp(self):
        self.pipeline = PromptBudgetPipeline()

    def test_negative_budget_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.pipeline.run("test prompt", budget=-1)
        self.assertIn("Budget must be >= 0", str(ctx.exception))

    def test_deliberate_wrong_no_exception_fails(self):
        with self.assertRaises(AssertionError):
            try:
                self.pipeline.run("test prompt", budget=-1)
            except ValueError:
                raise AssertionError("Expected failure: ValueError was raised as required.")


class TestIntermediateStateAndInvariants(unittest.TestCase):
    """
    Focus requirement:
      Record the intermediate state after each step and test the invariant
      linking that state to the final output.
    """

    def setUp(self):
        self.pipeline = PromptBudgetPipeline()
        self.report = self.pipeline.run("alpha beta gamma delta epsilon", budget=3)

    def test_intermediate_steps_recorded(self):
        step_names = [record.step_name for record in self.report.trace]
        self.assertEqual(step_names, [
            "VALIDATE_INPUT",
            "TOKENIZATION",
            "EVALUATE_BUDGET",
            "TRUNCATION",
        ])

    def test_token_conservation_invariant(self):
        """Initial tokens must equal retained tokens count plus removed tokens count."""
        tok_snap = self.report.trace[1].snapshot
        initial_count = tok_snap["token_count"]
        self.assertEqual(initial_count, len(self.report.retained_tokens) + self.report.removed_count)

    def test_sequence_reconstitution_invariant(self):
        """Initial token tuple must equal retained tokens concatenated with removed tokens."""
        tok_snap = self.report.trace[1].snapshot
        trunc_snap = self.report.trace[3].snapshot
        initial_tokens = tok_snap["tokens"]
        reconstituted = self.report.retained_tokens + trunc_snap["removed_tokens"]
        self.assertEqual(initial_tokens, reconstituted)

    def test_prefix_preservation_invariant(self):
        """Retained tokens must exactly match the prefix of the initial token stream."""
        tok_snap = self.report.trace[1].snapshot
        initial_tokens = tok_snap["tokens"]
        self.assertEqual(initial_tokens[:len(self.report.retained_tokens)], self.report.retained_tokens)

    def test_deliberate_invariant_violation_fails(self):
        """Corrupting the report must cause verify_pipeline_invariants to raise AssertionError."""
        corrupted = BudgetReport(
            retained_tokens=("alpha", "beta"),
            removed_count=0,  # Corrupted: 5 tokens initial, 2 retained, but 0 reported removed
            budget=3,
            tokenizer_label=TOKENIZER_LABEL,
            trace=self.report.trace,
        )
        with self.assertRaises(AssertionError):
            verify_pipeline_invariants(corrupted)


class TestSimulationContract(unittest.TestCase):
    """
    Ensure the tokenizer is confirmed as a deterministic local mock.
    """

    def test_deterministic_output(self):
        tok = WhitespaceTokenizer()
        self.assertEqual(tok.tokenize("a b c"), tok.tokenize("a b c"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
