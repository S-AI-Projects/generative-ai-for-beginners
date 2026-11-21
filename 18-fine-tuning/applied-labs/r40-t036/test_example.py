"""
Unit tests for R40-T036 Parameter Budget Calculator and Prefix-Based Layer Freezing.
"""

from __future__ import annotations

import unittest

from example import (
    FineTuningBudgetSummary,
    PrefixFreezeMatcher,
    baseline_freeze_budget,
    count_fine_tuning_parameters,
    prove_before_after_equivalence,
)


class TestParameterBudgetContract(unittest.TestCase):
    """Core contract tests for fine-tuning parameter budget and layer freezing."""

    def test_required_contract_encoder_head(self) -> None:
        """
        Contract requirement:
        encoder:100, head:20 with encoder frozen gives total=120 and trainable=20.
        """
        manifest = {"encoder": 100, "head": 20}
        freeze_prefixes = ["encoder"]

        result = count_fine_tuning_parameters(manifest, freeze_prefixes)

        self.assertEqual(result.total_params, 120)
        self.assertEqual(result.trainable_params, 20)
        self.assertEqual(result.frozen_params, 100)
        self.assertEqual(result.frozen_layers, ("encoder",))
        self.assertEqual(result.trainable_layers, ("head",))
        self.assertEqual(result.unmatched_prefixes, ())
        self.assertAlmostEqual(result.trainable_percentage, (20 / 120) * 100.0, places=4)

    def test_unmatched_freeze_prefix_is_reported(self) -> None:
        """
        Contract requirement:
        An unmatched freeze prefix is detected and reported in the summary.
        """
        manifest = {"encoder": 100, "head": 20}
        freeze_prefixes = ["encoder", "decoder", "backbone"]

        result = count_fine_tuning_parameters(manifest, freeze_prefixes)

        self.assertEqual(result.total_params, 120)
        self.assertEqual(result.trainable_params, 20)
        self.assertEqual(result.frozen_params, 100)
        # decoder and backbone did not match any layer
        self.assertEqual(result.unmatched_prefixes, ("decoder", "backbone"))

    def test_multiple_freeze_prefixes_and_nested_modules(self) -> None:
        """Prefix matching works on hierarchical/nested PyTorch-style layer paths."""
        manifest = {
            "transformer.encoder.layer_0.weight": 100,
            "transformer.encoder.layer_1.weight": 100,
            "transformer.decoder.layer_0.weight": 80,
            "transformer.embedding.weight": 40,
            "lm_head.weight": 30,
        }
        freeze_prefixes = ["transformer.encoder", "transformer.embedding"]

        result = count_fine_tuning_parameters(manifest, freeze_prefixes)

        self.assertEqual(result.total_params, 350)
        self.assertEqual(result.frozen_params, 240)
        self.assertEqual(result.trainable_params, 110)
        self.assertEqual(result.unmatched_prefixes, ())
        self.assertEqual(len(result.frozen_layers), 3)
        self.assertEqual(len(result.trainable_layers), 2)

    def test_empty_freeze_prefixes_leaves_all_trainable(self) -> None:
        """When no freeze prefixes are provided, 100% of parameters remain trainable."""
        manifest = {"encoder": 100, "head": 20}
        result = count_fine_tuning_parameters(manifest, freeze_prefixes=())

        self.assertEqual(result.total_params, 120)
        self.assertEqual(result.trainable_params, 120)
        self.assertEqual(result.frozen_params, 0)
        self.assertEqual(result.trainable_percentage, 100.0)
        self.assertEqual(result.unmatched_prefixes, ())

    def test_all_layers_frozen(self) -> None:
        """When all layers match freeze rules, trainable parameters are 0."""
        manifest = {"encoder": 100, "head": 20}
        result = count_fine_tuning_parameters(manifest, freeze_prefixes=["encoder", "head"])

        self.assertEqual(result.total_params, 120)
        self.assertEqual(result.trainable_params, 0)
        self.assertEqual(result.frozen_params, 120)
        self.assertEqual(result.trainable_percentage, 0.0)

    def test_empty_manifest_returns_zero_budget(self) -> None:
        """Empty manifest safely evaluates to 0 total and 0 trainable parameters."""
        manifest: dict[str, int] = {}
        result = count_fine_tuning_parameters(manifest, freeze_prefixes=["encoder"])

        self.assertEqual(result.total_params, 0)
        self.assertEqual(result.trainable_params, 0)
        self.assertEqual(result.frozen_params, 0)
        self.assertEqual(result.trainable_percentage, 0.0)
        self.assertEqual(result.unmatched_prefixes, ("encoder",))


class TestValidationFailures(unittest.TestCase):
    """Failure scenario tests checking input validation and error handling."""

    def test_negative_parameter_count_raises_value_error(self) -> None:
        """Negative parameter count must fail validation."""
        manifest = {"encoder": -10, "head": 20}
        with self.assertRaises(ValueError) as ctx:
            count_fine_tuning_parameters(manifest, ["encoder"])
        self.assertIn("Invalid parameter count", str(ctx.exception))

    def test_empty_layer_name_raises_value_error(self) -> None:
        """Empty or whitespace-only layer names fail validation."""
        manifest = {"": 100}
        with self.assertRaises(ValueError) as ctx:
            count_fine_tuning_parameters(manifest, [])
        self.assertIn("Invalid layer name", str(ctx.exception))

    def test_invalid_manifest_type_raises_type_error(self) -> None:
        """Non-mapping manifest input raises TypeError."""
        with self.assertRaises(TypeError):
            count_fine_tuning_parameters([("encoder", 100)], ["encoder"])  # type: ignore

    def test_invalid_freeze_prefixes_type_raises_type_error(self) -> None:
        """Non-sequence freeze prefixes input raises TypeError."""
        with self.assertRaises(TypeError):
            count_fine_tuning_parameters({"encoder": 100}, "encoder")  # type: ignore


class TestExtractedResponsibility(unittest.TestCase):
    """Direct unit tests for the extracted PrefixFreezeMatcher class."""

    def test_matcher_unit_functionality(self) -> None:
        """Matcher correctly compiles prefixes, tests layers, and tracks unmatched rules."""
        matcher = PrefixFreezeMatcher(["encoder", "layer.norm", "typo_prefix"])

        is_frozen, matched = matcher.match_layer("encoder.block1.weight")
        self.assertTrue(is_frozen)
        self.assertEqual(matched, "encoder")

        is_frozen, matched = matcher.match_layer("head.bias")
        self.assertFalse(is_frozen)
        self.assertIsNone(matched)

        classifications, unmatched = matcher.classify_manifest({
            "encoder.block1.weight": 50,
            "layer.norm.weight": 10,
            "head.bias": 5,
        })

        self.assertEqual(len(classifications), 3)
        self.assertEqual(unmatched, ("typo_prefix",))


class TestFocusBeforeAfterEquivalence(unittest.TestCase):
    """
    Focus requirement:
    Prove before/after equivalence on the contract fixture and diverse test cases.
    """

    def test_contract_fixture_before_after_equivalence(self) -> None:
        """
        Verify exact equivalence between baseline_freeze_budget and
        refactored count_fine_tuning_parameters on the core contract fixture:
        encoder:100, head:20 with encoder frozen.
        """
        fixture = {"encoder": 100, "head": 20}
        freeze_rules = ["encoder"]

        is_eq, baseline_res, refactored_res = prove_before_after_equivalence(fixture, freeze_rules)

        self.assertTrue(is_eq, "Baseline and refactored outputs diverged on contract fixture!")
        self.assertEqual(baseline_res.total_params, refactored_res.total_params)
        self.assertEqual(baseline_res.trainable_params, refactored_res.trainable_params)
        self.assertEqual(baseline_res.frozen_params, refactored_res.frozen_params)
        self.assertEqual(baseline_res.trainable_percentage, refactored_res.trainable_percentage)
        self.assertEqual(baseline_res.unmatched_prefixes, refactored_res.unmatched_prefixes)
        self.assertEqual(baseline_res.frozen_layers, refactored_res.frozen_layers)
        self.assertEqual(baseline_res.trainable_layers, refactored_res.trainable_layers)

    def test_diverse_fixtures_before_after_equivalence(self) -> None:
        """
        Verify equivalence across multiple complex fixtures:
        - Unmatched prefixes
        - Empty prefixes
        - Deeply nested module paths
        - All layers frozen
        """
        test_cases = [
            (
                {"encoder": 100, "head": 20},
                ["encoder", "missing_rule"],
            ),
            (
                {"a.1": 10, "a.2": 20, "b.1": 30, "c.1": 40},
                ["a.", "b."],
            ),
            (
                {"layer_1": 50, "layer_2": 50},
                [],
            ),
            (
                {"full_freeze": 500},
                ["full_freeze"],
            ),
        ]

        for idx, (manifest, prefixes) in enumerate(test_cases):
            with self.subTest(case_idx=idx):
                is_eq, base, refac = prove_before_after_equivalence(manifest, prefixes)
                self.assertTrue(is_eq, f"Equivalence failed for case {idx}: {manifest} with {prefixes}")
                self.assertEqual(base, refac)


class TestDeliberateWrongAssertions(unittest.TestCase):
    """
    Deliberate wrong result checks to confirm that the test framework
    fails with non-zero exit code if results deviate.
    """

    def test_deliberate_wrong_trainable_count_fails(self) -> None:
        """Asserting an incorrect trainable parameter count raises AssertionError."""
        result = count_fine_tuning_parameters({"encoder": 100, "head": 20}, ["encoder"])
        with self.assertRaises(AssertionError):
            self.assertEqual(result.trainable_params, 9999)

    def test_deliberate_wrong_unmatched_prefix_fails(self) -> None:
        """Asserting an incorrect unmatched prefix raises AssertionError."""
        result = count_fine_tuning_parameters({"encoder": 100, "head": 20}, ["encoder", "decoder"])
        with self.assertRaises(AssertionError):
            self.assertEqual(result.unmatched_prefixes, ("non_existent_prefix",))


if __name__ == "__main__":
    unittest.main()
