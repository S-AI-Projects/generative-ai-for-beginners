"""
R40-T044 · Test suite for example.py
=====================================

Covers the three required scenarios:
  1. Normal scenario          → SUGGEST
  2. Boundary scenario        → SUGGEST_MINIMAL
  3. Missing-information      → CANNOT_SUGGEST

Additionally verifies:
  • The checker fails (raises AssertionError) when a decision is deliberately
    changed — satisfying the "must fail on wrong result" requirement.
  • The mock adapter is confirmed as a simulation (not a real service).

Run with:
    python3 -m unittest discover -s 06-text-generation-apps/applied-labs/r40-t044 -p "test_*.py"
or:
    python3 -m unittest 06-text-generation-apps/applied-labs/r40-t044/test_example -v
"""

import unittest

from example import (
    DECISION_CANNOT_SUGGEST,
    DECISION_SUGGEST,
    DECISION_SUGGEST_MINIMAL,
    MockTextGenerationAdapter,
    RecipeRequest,
    suggest_recipes,
)


class TestNormalScenario(unittest.TestCase):
    """
    Scenario 1 — Normal
    -------------------
    Input facts : ingredients = [chicken, potatoes, carrots], max_recipes = 3
    Expected decision : SUGGEST
    Rationale : Three named ingredients give the model enough context to return
    a rich set of recipes, directly illustrating Lesson 06's core loop of
    constructing a prompt → generating text → presenting results.

    [SIMULATION / MOCK] The MockTextGenerationAdapter returns a hard-coded
    fixture; a live Azure OpenAI call would return novel text each time.
    """

    def setUp(self):
        self.client = MockTextGenerationAdapter()
        self.request = RecipeRequest(
            ingredients=["chicken", "potatoes", "carrots"],
            max_recipes=3,
        )

    def test_decision_is_suggest(self):
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__normal__")
        self.assertEqual(decision, DECISION_SUGGEST)

    def test_response_has_recipes(self):
        response, _ = suggest_recipes(self.request, self.client, scenario_tag="__normal__")
        self.assertGreaterEqual(response.recipes_found, 2)

    def test_deliberate_wrong_decision_fails(self):
        """The checker MUST fail when the expected decision is wrong."""
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__normal__")
        with self.assertRaises(AssertionError):
            # Deliberately assert the wrong expected value
            self.assertEqual(decision, DECISION_CANNOT_SUGGEST,
                             "This assertion is intentionally wrong to prove the checker fails.")


class TestBoundaryScenario(unittest.TestCase):
    """
    Scenario 2 — Boundary
    ---------------------
    Input facts : ingredients = [tomato] (exactly one ingredient), max_recipes = 2
    Expected decision : SUGGEST_MINIMAL
    Rationale : One ingredient is the minimum viable prompt described in
    Lesson 06's recipe-generator exercise.  The model can still return at least
    one recipe, but the user should be warned the results may be limited.

    [SIMULATION / MOCK] The mock returns a single-recipe fixture for the
    boundary tag; a real model might return more or fewer recipes depending on
    its training.
    """

    def setUp(self):
        self.client = MockTextGenerationAdapter()
        self.request = RecipeRequest(
            ingredients=["tomato"],
            max_recipes=2,
        )

    def test_decision_is_suggest_minimal(self):
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__boundary__")
        self.assertEqual(decision, DECISION_SUGGEST_MINIMAL)

    def test_response_has_at_least_one_recipe(self):
        response, _ = suggest_recipes(self.request, self.client, scenario_tag="__boundary__")
        self.assertGreaterEqual(response.recipes_found, 1)

    def test_deliberate_wrong_decision_fails(self):
        """The checker MUST fail when the expected decision is wrong."""
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__boundary__")
        with self.assertRaises(AssertionError):
            self.assertEqual(decision, DECISION_SUGGEST,
                             "This assertion is intentionally wrong.")


class TestMissingInformationScenario(unittest.TestCase):
    """
    Scenario 3 — Missing information
    ---------------------------------
    Input facts : ingredients = [] (empty list), max_recipes = 3
    Expected decision : CANNOT_SUGGEST
    Rationale : Lesson 06 explains that the prompt is the primary interface to
    the model.  When no ingredients are provided the prompt lacks the essential
    fact required for a useful completion — the application must not guess.

    [SIMULATION / MOCK] The mock returns an empty string for the missing tag,
    simulating the real-world case where a model responds with "I cannot help
    without knowing the ingredients."  A real model might return a polite
    refusal sentence instead of an empty string.
    """

    def setUp(self):
        self.client = MockTextGenerationAdapter()
        self.request = RecipeRequest(
            ingredients=[],
            max_recipes=3,
        )

    def test_decision_is_cannot_suggest(self):
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__missing__")
        self.assertEqual(decision, DECISION_CANNOT_SUGGEST)

    def test_response_has_no_recipes(self):
        response, _ = suggest_recipes(self.request, self.client, scenario_tag="__missing__")
        self.assertEqual(response.recipes_found, 0)

    def test_deliberate_wrong_decision_fails(self):
        """The checker MUST fail when the expected decision is wrong."""
        _, decision = suggest_recipes(self.request, self.client, scenario_tag="__missing__")
        with self.assertRaises(AssertionError):
            self.assertEqual(decision, DECISION_SUGGEST,
                             "This assertion is intentionally wrong.")


class TestDecisionTableIntegrity(unittest.TestCase):
    """Cross-scenario integrity: changing a decision in the table must break tests."""

    def test_normal_decision_is_not_suggest_minimal(self):
        client = MockTextGenerationAdapter()
        request = RecipeRequest(ingredients=["chicken", "potatoes", "carrots"])
        _, decision = suggest_recipes(request, client, scenario_tag="__normal__")
        self.assertNotEqual(decision, DECISION_SUGGEST_MINIMAL)

    def test_missing_decision_is_not_suggest(self):
        client = MockTextGenerationAdapter()
        request = RecipeRequest(ingredients=[])
        _, decision = suggest_recipes(request, client, scenario_tag="__missing__")
        self.assertNotEqual(decision, DECISION_SUGGEST)

    def test_boundary_decision_is_not_cannot_suggest(self):
        client = MockTextGenerationAdapter()
        request = RecipeRequest(ingredients=["tomato"])
        _, decision = suggest_recipes(request, client, scenario_tag="__boundary__")
        self.assertNotEqual(decision, DECISION_CANNOT_SUGGEST)


class TestMockIsNotRealService(unittest.TestCase):
    """
    Explicitly documents that MockTextGenerationAdapter is a simulation.

    [SIMULATION / MOCK] — Real-service behaviours NOT established by the mock:
      - Non-determinism (same input always yields same output from mock).
      - Network timeouts / HTTP 429 rate-limits.
      - Token-budget truncation.
      - Safety-filter refusals.
      - Hallucinated ingredients.
    """

    def test_mock_is_deterministic(self):
        """Same prompt → same response every call (unlike a real model)."""
        client = MockTextGenerationAdapter()
        r1 = client.generate("hello __normal__")
        r2 = client.generate("hello __normal__")
        self.assertEqual(r1, r2, "Mock must be deterministic.")

    def test_mock_does_not_raise_on_any_input(self):
        """Mock never raises network or API errors."""
        client = MockTextGenerationAdapter()
        try:
            client.generate("completely unknown prompt with no tag")
        except Exception as exc:  # noqa: BLE001
            self.fail(f"Mock raised unexpectedly: {exc}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
