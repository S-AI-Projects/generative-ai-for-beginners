#!/usr/bin/env python3
"""Tests for the r40-t051 resource-envelope example.

These tests exercise the stated contract of the minimal local example:
  - normal scenario (budget RAM6 / context1024 admits only Fixture A)
  - boundary scenarios (exact fit, exact context, over-by-one, zero envelope)
  - failure scenarios (negative inputs raise ValueError)
  - a deliberately wrong result is rejected by assertion

Run from the repository root:
    python3 -m unittest discover -s 21-meta/applied-labs/r40-t051 -p "test_*.py"
"""

import os
import sys
import unittest

# Make `example` importable regardless of the current working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from example import (  # noqa: E402
    ModelVariant,
    eligibility_reason,
    is_eligible,
    select_models,
    SCENARIO_MANIFEST,
)

# Inputs shared by several scenarios (from the lesson brief).
BUDGET_RAM_GB = 6
REQUESTED_CONTEXT_TOKENS = 1024


class ResourceEnvelopeNormalScenario(unittest.TestCase):
    """Normal scenario: budget RAM6, requested context1024 admits only A."""

    def setUp(self):
        self.eligible, self.excluded = select_models(
            SCENARIO_MANIFEST, BUDGET_RAM_GB, REQUESTED_CONTEXT_TOKENS
        )

    def test_a_eligible(self):
        self.assertEqual([m.name for m in self.eligible], ["fixture-a"])

    def test_b_excluded(self):
        self.assertEqual([e[0].name for e in self.excluded], ["fixture-b"])

    def test_only_a_admitted(self):
        names = {m.name for m in self.eligible}
        self.assertEqual(names, {"fixture-a"})
        self.assertNotIn("fixture-b", names)
        # A deliberate wrong result that admits the over-budget Fixture B must
        # be rejected by this test.
        self.assertFalse(
            {"fixture-a", "fixture-b"} == names,
            "wrong result admitting over-budget fixture-b was not rejected",
        )

    def test_excluded_reason(self):
        reason = self.excluded[0][1]
        self.assertEqual(reason, "exceeds budget RAM")
        self.assertIsInstance(reason, str)
        self.assertTrue(reason)


class ResourceEnvelopeBoundaryScenario(unittest.TestCase):
    """Boundary fixtures: exact fit, exact context, over-by-one."""

    def test_exact_fit_admits(self):
        manifest = [ModelVariant(name="exact-fit", ram_gb=6, context_window=1024)]
        eligible, excluded = select_models(manifest, 6, 1024)
        self.assertEqual([m.name for m in eligible], ["exact-fit"])
        self.assertEqual(excluded, [])

    def test_exact_context_admits(self):
        manifest = [ModelVariant(name="exact-context", ram_gb=4, context_window=1024)]
        eligible, _ = select_models(manifest, 6, 1024)
        self.assertEqual([m.name for m in eligible], ["exact-context"])

    def test_over_budget_by_one_excluded(self):
        manifest = [ModelVariant(name="over-ram", ram_gb=7, context_window=1024)]
        eligible, excluded = select_models(manifest, 6, 1024)
        self.assertEqual([m.name for m in eligible], [])
        self.assertEqual(excluded[0][1], "exceeds budget RAM")

    def test_over_context_excluded(self):
        manifest = [ModelVariant(name="under-context", ram_gb=4, context_window=512)]
        _, excluded = select_models(manifest, 6, 1024)
        self.assertEqual(excluded[0][1], "insufficient context window")


class ResourceEnvelopeFailureScenario(unittest.TestCase):
    """Negative inputs must fail loudly (ValueError), as the contract states."""

    def test_negative_budget_raises(self):
        manifest = [ModelVariant(name="x", ram_gb=4, context_window=1024)]
        with self.assertRaises(ValueError):
            select_models(manifest, budget_ram_gb=-1, requested_context_tokens=1024)

    def test_negative_requested_context_raises(self):
        manifest = [ModelVariant(name="x", ram_gb=4, context_window=1024)]
        with self.assertRaises(ValueError):
            select_models(manifest, budget_ram_gb=6, requested_context_tokens=-1)

    def test_negative_manifest_ram_raises(self):
        with self.assertRaises(ValueError):
            select_models(
                [ModelVariant(name="bad", ram_gb=-2, context_window=1024)],
                budget_ram_gb=6,
                requested_context_tokens=1024,
            )

    def test_negative_manifest_context_raises(self):
        with self.assertRaises(ValueError):
            select_models(
                [ModelVariant(name="bad", ram_gb=4, context_window=-100)],
                budget_ram_gb=6,
                requested_context_tokens=1024,
            )


class ResourceEnvelopeEdgeScenario(unittest.TestCase):
    """Extra edge cases that are cheap to run in a fresh process."""

    def test_zero_budget_excludes_all(self):
        manifest = [ModelVariant(name="z", ram_gb=1, context_window=1)]
        eligible, excluded = select_models(manifest, budget_ram_gb=0, requested_context_tokens=0)
        self.assertEqual(eligible, [])
        self.assertEqual(len(excluded), 1)

    def test_empty_manifest(self):
        eligible, excluded = select_models([], budget_ram_gb=6, requested_context_tokens=1024)
        self.assertEqual(eligible, [])
        self.assertEqual(excluded, [])

    def test_is_eligible_deterministic(self):
        variant = ModelVariant(name="det", ram_gb=4, context_window=2048)
        self.assertTrue(is_eligible(variant, 6, 1024))
        self.assertFalse(is_eligible(variant, 3, 1024))


if __name__ == "__main__":
    unittest.main()
