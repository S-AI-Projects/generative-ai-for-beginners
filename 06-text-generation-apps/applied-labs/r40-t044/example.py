"""
R40-T044 · Applied Lab: Building Text Generation Applications
=============================================================

This module illustrates Lesson 06 ("Building Text Generation Applications")
through a *prompt-engineering decision table* for a recipe-suggestion assistant.

Lesson connection
-----------------
Lesson 06 teaches that text-generation apps work by:
  1. Constructing a **prompt** (ingredients, constraints, format instructions).
  2. Calling a **language-model API** that returns a text completion.
  3. Post-processing the completion text into an application result.

Here we capture that three-step pipeline in a single callable interface
(``TextGenerationClient``) and supply a **deterministic local adapter**
(``MockTextGenerationAdapter``) so the lab runs without a paid model, GPU,
or network access.

Simplification boundary
-----------------------
The mock returns hard-coded fixtures.  A real service would:
  • Generate *novel, nondeterministic* text for every call.
  • Understand natural-language nuance (e.g. partial ingredient lists).
  • Fail in ways this mock does **not** establish:
      - Network timeouts / rate-limits (HTTP 429).
      - Token-budget exhaustion (completion truncated mid-sentence).
      - Safety-filter refusals.
      - Hallucinated ingredients not present in the prompt.
  Therefore: tests that pass here do NOT prove a real-service integration
  is correct — they only verify the *application logic* (prompt construction,
  response parsing, decision mapping) in isolation.

Three scenarios
---------------
1. **Normal**: prompt has named ingredients → model suggests recipes → decision SUGGEST.
2. **Boundary**: prompt has exactly one ingredient (minimum viable prompt) → decision SUGGEST_MINIMAL.
3. **Missing-information**: prompt has no ingredients → decision CANNOT_SUGGEST.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecipeRequest:
    """Input facts for a recipe-suggestion call."""
    ingredients: list[str]
    max_recipes: int = 3
    dietary_filter: str = ""


@dataclass(frozen=True)
class RecipeResponse:
    """Parsed output from the text-generation service."""
    raw_text: str
    recipes_found: int


# ---------------------------------------------------------------------------
# Decision table
# ---------------------------------------------------------------------------

DECISION_SUGGEST = "SUGGEST"
DECISION_SUGGEST_MINIMAL = "SUGGEST_MINIMAL"
DECISION_CANNOT_SUGGEST = "CANNOT_SUGGEST"


def decide(response: RecipeResponse, request: RecipeRequest) -> str:
    """
    Map (response, request) → decision label.

    Decision table
    ~~~~~~~~~~~~~~
    ┌──────────────────────┬────────────────────────┬──────────────────────────┐
    │ Scenario             │ Condition              │ Decision                 │
    ├──────────────────────┼────────────────────────┼──────────────────────────┤
    │ Normal               │ ≥2 ingredients AND     │ SUGGEST                  │
    │                      │ recipes_found ≥ 2      │                          │
    ├──────────────────────┼────────────────────────┼──────────────────────────┤
    │ Boundary             │ exactly 1 ingredient   │ SUGGEST_MINIMAL          │
    │                      │ AND recipes_found ≥ 1  │                          │
    ├──────────────────────┼────────────────────────┼──────────────────────────┤
    │ Missing-information  │ 0 ingredients OR       │ CANNOT_SUGGEST           │
    │                      │ recipes_found == 0     │                          │
    └──────────────────────┴────────────────────────┴──────────────────────────┘

    Rationale (tied to the lesson)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * Lesson 06 emphasises that the *prompt* is the primary interface to the
      model.  When no ingredients are supplied the prompt lacks the key fact
      the model needs → we must not guess.
    * A single ingredient is a valid but *minimal* prompt; the model may
      return at least one recipe but the user should be warned the results
      may be limited.
    * Two or more ingredients give the model enough context to return a rich
      completion suitable for direct presentation.
    """
    n_ing = len(request.ingredients)

    if n_ing == 0 or response.recipes_found == 0:
        return DECISION_CANNOT_SUGGEST

    if n_ing == 1:
        return DECISION_SUGGEST_MINIMAL

    return DECISION_SUGGEST


# ---------------------------------------------------------------------------
# Callable interface (the external-dependency contract)
# ---------------------------------------------------------------------------

class TextGenerationClient(Protocol):
    """
    Callable interface that wraps the external text-generation dependency.

    Any object implementing this protocol can be used by ``suggest_recipes``.
    In production this would be backed by an Azure OpenAI / OpenAI Responses
    API call; in tests it is backed by ``MockTextGenerationAdapter``.
    """

    def generate(self, prompt: str) -> str:
        """Send *prompt* and return the raw completion text."""
        ...


# ---------------------------------------------------------------------------
# Deterministic local adapter (mock)
# ---------------------------------------------------------------------------

# Fixture responses keyed by scenario tag embedded in the prompt.
_FIXTURE_MAP: dict[str, str] = {
    "__normal__": (
        "1. Roasted Chicken with Potatoes\n"
        "2. Chicken and Carrot Stew\n"
        "3. One-Pot Chicken Dinner\n"
    ),
    "__boundary__": (
        "1. Simple Tomato Soup\n"
    ),
    "__missing__": "",   # model cannot help without ingredients
}


class MockTextGenerationAdapter:
    """
    **Deterministic local adapter** — no network, no GPU, no paid provider.

    It inspects the prompt for a scenario tag (``__normal__``, ``__boundary__``,
    ``__missing__``) inserted by the application and returns a pre-written
    fixture string.

    Real-service behaviour this mock does NOT establish
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * Non-determinism: a real model returns different text on each call.
    * Token limits: the mock never truncates; a real model may cut off mid-line.
    * Network errors / rate-limits: the mock never raises ``openai.APIError``.
    * Safety refusals: the mock never declines a prompt.
    * Hallucination: the mock never invents ingredients absent from the prompt.
    * Latency / cost: the mock is instantaneous and free.

    **[SIMULATION / MOCK]** — Label is explicit per assignment requirements.
    """

    def generate(self, prompt: str) -> str:  # noqa: D102
        for tag, fixture in _FIXTURE_MAP.items():
            if tag in prompt:
                return fixture
        # Fallback: treat unknown prompts as missing-information
        return ""


# ---------------------------------------------------------------------------
# Application logic
# ---------------------------------------------------------------------------

def _build_prompt(request: RecipeRequest, scenario_tag: str = "") -> str:
    """Construct the text-generation prompt from the request facts."""
    if not request.ingredients:
        ingredients_str = "(none provided)"
    else:
        ingredients_str = ", ".join(request.ingredients)

    filter_clause = ""
    if request.dietary_filter:
        filter_clause = f" No {request.dietary_filter}."

    prompt = (
        f"Show me {request.max_recipes} recipes for a dish using: "
        f"{ingredients_str}.{filter_clause} "
        f"List each recipe on a new numbered line. {scenario_tag}"
    )
    return prompt


def _parse_response(raw_text: str) -> RecipeResponse:
    """Count numbered recipes in the raw completion."""
    import re
    lines = raw_text.strip().splitlines()
    numbered = [l for l in lines if re.match(r"^\d+\.", l.strip())]
    return RecipeResponse(raw_text=raw_text, recipes_found=len(numbered))


def suggest_recipes(
    request: RecipeRequest,
    client: TextGenerationClient,
    scenario_tag: str = "",
) -> tuple[RecipeResponse, str]:
    """
    Full application pipeline.

    Parameters
    ----------
    request:
        Input facts (ingredients, max_recipes, dietary_filter).
    client:
        Any object satisfying ``TextGenerationClient`` (real or mock).
    scenario_tag:
        Optional tag injected into the prompt so the mock can return the
        correct fixture.  Production callers omit this.

    Returns
    -------
    (response, decision) where *decision* is one of the DECISION_* constants.
    """
    prompt = _build_prompt(request, scenario_tag=scenario_tag)
    raw = client.generate(prompt)
    response = _parse_response(raw)
    decision = decide(response, request)
    return response, decision
