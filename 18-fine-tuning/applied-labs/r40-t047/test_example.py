"""
R40-T047 · Test suite for example.py
======================================

Covers:
  1. Regression test: exact task example
     encoder:100, head:20 with encoder frozen gives total=120 and trainable=20.
  2. Unmatched freeze prefix reporting:
     An unmatched prefix (e.g. 'decoder') is reported in unmatched_prefixes.
  3. Boundary scenarios:
     - Empty manifest {} -> total=0, trainable=0, frozen=0
     - No freeze prefixes [] -> all parameters trainable (trainable=total)
     - All layers frozen -> trainable=0, frozen=total
  4. Failure / validation scenarios:
     - Negative parameter count -> raises ValueError
     - Strict mode with unmatched prefix -> raises ValueError
  5. Worked input-to-output explanation:
     - Output contains step-by-step reasoning tied to Lesson 18.
  6. Deliberate wrong result verification:
     - Deliberate wrong assertion fails with AssertionError.
  7. Simulation & mock limits documentation.

Run with:
    python3 -m unittest discover -s 18-fine-tuning/applied-labs/r40-t047 -p "test_*.py"
"""

import unittest

from example import (
    ParameterBudgetReport,
    evaluate_parameter_budget,
)


# ---------------------------------------------------------------------------
# Scenario 1 — Regression Test (Exact Task Example)
# ---------------------------------------------------------------------------

class TestRegressionExactExample(unittest.TestCase):
    """
    Exact requirement from R40-T047 specification:
      encoder:100, head:20 with encoder frozen gives total=120 and trainable=20.

    Input facts:
      manifest = {"encoder": 100, "head": 20}
      freeze_prefixes = ["encoder"]

    Expected:
      total_params = 120
      trainable_params = 20
      frozen_params = 100
      unmatched_prefixes = ()
    """

    def setUp(self):
        self.manifest = {"encoder": 100, "head": 20}
        self.freeze_prefixes = ["encoder"]
        self.report = evaluate_parameter_budget(self.manifest, self.freeze_prefixes)

    def test_total_parameters_is_120(self):
        self.assertEqual(self.report.total_params, 120)

    def test_trainable_parameters_is_20(self):
        self.assertEqual(self.report.trainable_params, 20)

    def test_frozen_parameters_is_100(self):
        self.assertEqual(self.report.frozen_params, 100)

    def test_layer_states_correct(self):
        self.assertTrue(self.report.layer_states["encoder"])
        self.assertFalse(self.report.layer_states["head"])

    def test_no_unmatched_prefixes(self):
        self.assertEqual(self.report.unmatched_prefixes, ())

    def test_deliberate_wrong_total_fails(self):
        """Deliberate wrong assertion must fail to prove checker verification."""
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.total_params, 999,
                             "Deliberate wrong assertion to ensure test catches error.")

    def test_deliberate_wrong_trainable_fails(self):
        """Deliberate wrong assertion for trainable parameter count."""
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.trainable_params, 100,
                             "Deliberate wrong assertion to ensure test catches error.")


# ---------------------------------------------------------------------------
# Scenario 2 — Unmatched Freeze Prefix Reporting
# ---------------------------------------------------------------------------

class TestUnmatchedFreezePrefix(unittest.TestCase):
    """
    Requirement: an unmatched freeze prefix is reported.

    When a developer configures a freeze prefix (e.g. 'decoder' or 'adapter')
    that does not match any layer in the manifest, the checker must report it
    explicitly in unmatched_prefixes and highlight it in the explanation.
    """

    def setUp(self):
        self.manifest = {"encoder": 100, "head": 20}
        self.freeze_prefixes = ["encoder", "decoder"]
        self.report = evaluate_parameter_budget(self.manifest, self.freeze_prefixes)

    def test_unmatched_prefix_reported(self):
        self.assertEqual(self.report.unmatched_prefixes, ("decoder",))

    def test_matched_prefix_recorded(self):
        self.assertEqual(self.report.matched_prefixes, ("encoder",))

    def test_counts_still_accurate(self):
        self.assertEqual(self.report.total_params, 120)
        self.assertEqual(self.report.trainable_params, 20)
        self.assertEqual(self.report.frozen_params, 100)

    def test_explanation_contains_warning(self):
        self.assertIn("WARNING: Unmatched freeze prefixes detected: ['decoder']",
                      self.report.explanation)

    def test_strict_mode_raises_on_unmatched(self):
        """In strict mode, unmatched prefixes raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            evaluate_parameter_budget(self.manifest, self.freeze_prefixes, strict=True)
        self.assertIn("decoder", str(ctx.exception))

    def test_deliberate_wrong_unmatched_fails(self):
        with self.assertRaises(AssertionError):
            self.assertEqual(self.report.unmatched_prefixes, (),
                             "Deliberate wrong assertion: decoder was unmatched.")


# ---------------------------------------------------------------------------
# Scenario 3 — Boundary Scenarios
# ---------------------------------------------------------------------------

class TestBoundaryScenarios(unittest.TestCase):
    """
    Boundary cases:
      - Empty manifest
      - No freeze prefixes (all trainable)
      - All prefixes frozen (trainable = 0)
    """

    def test_empty_manifest(self):
        report = evaluate_parameter_budget({}, ["encoder"])
        self.assertEqual(report.total_params, 0)
        self.assertEqual(report.trainable_params, 0)
        self.assertEqual(report.frozen_params, 0)
        self.assertEqual(report.unmatched_prefixes, ("encoder",))

    def test_no_freeze_prefixes_all_trainable(self):
        manifest = {"encoder": 100, "head": 20}
        report = evaluate_parameter_budget(manifest, [])
        self.assertEqual(report.total_params, 120)
        self.assertEqual(report.trainable_params, 120)
        self.assertEqual(report.frozen_params, 0)
        self.assertEqual(report.unmatched_prefixes, ())

    def test_all_layers_frozen(self):
        manifest = {"encoder": 100, "head": 20}
        report = evaluate_parameter_budget(manifest, ["encoder", "head"])
        self.assertEqual(report.total_params, 120)
        self.assertEqual(report.trainable_params, 0)
        self.assertEqual(report.frozen_params, 120)
        self.assertEqual(report.unmatched_prefixes, ())


# ---------------------------------------------------------------------------
# Scenario 4 — Validation & Failure Scenarios
# ---------------------------------------------------------------------------

class TestValidationFailures(unittest.TestCase):
    """
    Failure conditions: negative parameter counts must be rejected.
    """

    def test_negative_parameter_count_raises(self):
        with self.assertRaises(ValueError) as ctx:
            evaluate_parameter_budget({"encoder": -10, "head": 20}, ["encoder"])
        self.assertIn("encoder", str(ctx.exception))
        self.assertIn("-10", str(ctx.exception))

    def test_deliberate_no_exception_fails(self):
        """Deliberately assert that no exception is raised on invalid input."""
        with self.assertRaises(AssertionError):
            try:
                evaluate_parameter_budget({"encoder": -50}, [])
            except ValueError:
                raise AssertionError("ValueError correctly occurred; intentional failure test.")


# ---------------------------------------------------------------------------
# Scenario 5 — Worked Input-to-Output Explanation
# ---------------------------------------------------------------------------

class TestWorkedExplanation(unittest.TestCase):
    """
    Focus requirement:
      Publish a worked input-to-output explanation and execute the exact
      example as a regression test.
    """

    def test_explanation_contains_worked_steps(self):
        manifest = {"encoder": 100, "head": 20}
        report = evaluate_parameter_budget(manifest, ["encoder"])
        expl = report.explanation

        self.assertIn("Input manifest: {'encoder': 100, 'head': 20}", expl)
        self.assertIn("Configured freeze prefixes: ['encoder']", expl)
        self.assertIn("Layer 'encoder' (100 params) matches freeze prefix 'encoder' -> FROZEN", expl)
        self.assertIn("Layer 'head' (20 params) matches no freeze prefix -> TRAINABLE", expl)
        self.assertIn("Result: total=120, trainable=20, frozen=100.", expl)


# ---------------------------------------------------------------------------
# Scenario 6 — Simulation Documentation
# ---------------------------------------------------------------------------

class TestSimulationContract(unittest.TestCase):
    """
    Explicitly documents that this is a parameter-budget calculation mock.
    No live PyTorch tensor or model inference is claimed.
    """

    def test_pure_deterministic_calculation(self):
        manifest = {"encoder": 100, "head": 20}
        r1 = evaluate_parameter_budget(manifest, ["encoder"])
        r2 = evaluate_parameter_budget(manifest, ["encoder"])
        self.assertEqual(r1.total_params, r2.total_params)
        self.assertEqual(r1.trainable_params, r2.trainable_params)
        self.assertEqual(r1.explanation, r2.explanation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
