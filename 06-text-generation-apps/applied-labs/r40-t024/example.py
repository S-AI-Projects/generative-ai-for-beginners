#!/usr/bin/env python3
"""R40-T024: Worked Decision Example for 'Building Text Generation Applications'.

This applied lab implements a worked decision framework, intermediate state tracer,
and invariant verification system for text generation applications based on Lesson 06
("Building Text Generation Applications" in 06-text-generation-apps/README.md).

Lesson Context:
Lesson 06 covers the transition from command/UI apps to natural language text generation
applications using the OpenAI / Microsoft Foundry client libraries. Key architectural
considerations include:
1. Environment & Secret Isolation: API keys and endpoints must be separated from application
   code using environment variables (AZURE_OPENAI_API_KEY, OPENAI_API_KEY).
2. Model Families & Parameter Compatibility:
   - Reasoning models (e.g. gpt-5-mini, o-series): Steered through prompt engineering and
     reasoning controls. They do NOT support sampling parameters (`temperature`, `top_p`)
     or `max_tokens`; passing `temperature` results in an API error.
   - Open / Sampling models (e.g. Llama-3.3-70B-Instruct, Mistral): Support sampling controls
     like `temperature` (0.0 to 1.0, where 1.0 represents the creative variance boundary).
3. Token Budgeting: Output tokens cost money and latency (`max_output_tokens`), requiring
   economical budgeting and token headroom management across multi-step pipelines.
4. Multi-Step Prompt Chaining: Feeding earlier outputs (`old_prompt_result`) as context into
   subsequent prompts (e.g. recipe generation followed by shopping list synthesis excluding
   available pantry items).
5. Constraint & Allergy Filtering: Embedding user constraints (e.g. `no {filter}`) into prompt
   templates and ensuring negative constraints propagate cleanly across all downstream stages.

Contribution Focus (Task R40-T024):
Record the intermediate state after each discrete step (Validation & Configuration,
Prompt Construction, Primary Generation, Context Chaining, and Final Assembly) and test the
formal invariants linking those intermediate states to the final output.

Task Scope & Simulation Boundary:
This module is a local deterministic simulation fixture implemented strictly with Python's
standard library. No real OpenAI/Azure API calls, paid credentials, downloaded model weights,
or GPU acceleration are required.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# Enums and Domain Models
# ============================================================================

class Decision(str, Enum):
    """Pipeline execution governance decisions."""

    EXECUTE_REASONING_PIPELINE = "EXECUTE_REASONING_PIPELINE"
    EXECUTE_SAMPLING_BOUNDARY_PIPELINE = "EXECUTE_SAMPLING_BOUNDARY_PIPELINE"
    HALT_MISSING_PREREQUISITES = "HALT_MISSING_PREREQUISITES"


class PipelineStep(str, Enum):
    """Discrete pipeline steps for state tracing."""

    STEP_1_VALIDATION_AND_CONFIG = "STEP_1_VALIDATION_AND_CONFIG"
    STEP_2_PROMPT_CONSTRUCTION = "STEP_2_PROMPT_CONSTRUCTION"
    STEP_3_PRIMARY_GENERATION = "STEP_3_PRIMARY_GENERATION"
    STEP_4_CONTEXT_CHAINING = "STEP_4_CONTEXT_CHAINING"
    STEP_5_FINAL_ASSEMBLY = "STEP_5_FINAL_ASSEMBLY"


class StepStatus(str, Enum):
    """Execution status of an intermediate pipeline step."""

    SUCCESS = "SUCCESS"
    HALTED = "HALTED"
    SKIPPED = "SKIPPED"
    BOUNDARY_SATURATED = "BOUNDARY_SATURATED"


class DecisionMismatchError(Exception):
    """Raised when an evaluated decision deviates from the published expected decision."""

    def __init__(self, message: str, scenario_id: str, expected: str, actual: str, rationale: str) -> None:
        super().__init__(message)
        self.scenario_id = scenario_id
        self.expected = expected
        self.actual = actual
        self.rationale = rationale


class InvariantViolationError(Exception):
    """Raised when an invariant linking intermediate state to final output fails."""

    def __init__(self, invariant_name: str, message: str, details: Dict[str, Any]) -> None:
        super().__init__(f"Invariant '{invariant_name}' violated: {message}")
        self.invariant_name = invariant_name
        self.details = details


# ============================================================================
# Intermediate State & Pipeline Output Data Structures
# ============================================================================

class IntermediateState:
    """Snapshot of execution state recorded after each discrete pipeline step."""

    def __init__(
        self,
        step_index: int,
        step_name: PipelineStep,
        status: StepStatus,
        payload: Dict[str, Any],
        step_tokens_generated: int,
        cumulative_tokens: int,
        invariants_checked: Optional[Dict[str, bool]] = None,
        notes: str = "",
    ) -> None:
        self.step_index = step_index
        self.step_name = step_name
        self.status = status
        self.payload = payload
        self.step_tokens_generated = step_tokens_generated
        self.cumulative_tokens = cumulative_tokens
        self.invariants_checked = invariants_checked or {}
        self.notes = notes
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to JSON-serializable dictionary."""
        return {
            "step_index": self.step_index,
            "step_name": self.step_name.value,
            "status": self.status.value,
            "step_tokens_generated": self.step_tokens_generated,
            "cumulative_tokens": self.cumulative_tokens,
            "payload": self.payload,
            "invariants_checked": self.invariants_checked,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }


class PipelineOutput:
    """Final output emitted by the text generation application pipeline."""

    def __init__(
        self,
        scenario_id: str,
        scenario_type: str,
        model_id: str,
        decision: Decision,
        rationale: str,
        state_trace: List[IntermediateState],
        final_text: Optional[str],
        total_tokens_consumed: int,
        token_budget: Optional[int],
        invariants_summary: Dict[str, Any],
        diagnostic_envelope: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.scenario_id = scenario_id
        self.scenario_type = scenario_type
        self.model_id = model_id
        self.decision = decision
        self.rationale = rationale
        self.state_trace = state_trace
        self.final_text = final_text
        self.total_tokens_consumed = total_tokens_consumed
        self.token_budget = token_budget
        self.invariants_summary = invariants_summary
        self.diagnostic_envelope = diagnostic_envelope or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline output to serializable dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "model_id": self.model_id,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "total_tokens_consumed": self.total_tokens_consumed,
            "token_budget": self.token_budget,
            "final_text": self.final_text,
            "diagnostic_envelope": self.diagnostic_envelope,
            "invariants_summary": self.invariants_summary,
            "state_trace": [s.to_dict() for s in self.state_trace],
        }


# ============================================================================
# Published Decision Table (Normal, Boundary, Missing Information)
# ============================================================================

PUBLISHED_DECISION_TABLE: Dict[str, Dict[str, Any]] = {
    "SCENARIO_NORMAL": {
        "scenario_type": "normal",
        "description": "Production recipe and shopping-list assistant using Microsoft Foundry reasoning model (gpt-5-mini) with prompt engineering, no temperature, isolated environment secrets, and two-step chaining.",
        "model_id": "gpt-5-mini",
        "model_family": "reasoning",
        "facts": {
            "api_key_env_var_set": True,
            "api_endpoint_env_var_set": True,
            "temperature": None,  # Correct: reasoning models reject temperature
            "max_output_tokens": 1200,
            "prompt_inputs": {
                "no_recipes": 3,
                "ingredients": ["chicken", "potatoes", "carrots"],
                "filter_exclusion": "garlic",
            },
            "chain_shopping_list": True,
        },
        "expected_decision": Decision.EXECUTE_REASONING_PIPELINE.value,
        "expected_rationale_keywords": [
            "reasoning model",
            "gpt-5-mini",
            "temperature",
            "environment",
            "chaining",
            "garlic",
        ],
    },
    "SCENARIO_BOUNDARY": {
        "scenario_type": "boundary",
        "description": "Creative variation generation with open sampling model (Llama-3.3-70B-Instruct) at maximum temperature boundary (1.0) and tight token budget (150 tokens) exhausting headroom.",
        "model_id": "Llama-3.3-70B-Instruct",
        "model_family": "sampling",
        "facts": {
            "api_key_env_var_set": True,
            "api_endpoint_env_var_set": True,
            "temperature": 1.0,  # Exact boundary: maximum creative sampling
            "max_output_tokens": 150,  # Exact tight token boundary
            "prompt_inputs": {
                "no_recipes": 1,
                "ingredients": ["apple", "flour"],
                "filter_exclusion": "sugar",
            },
            "chain_shopping_list": True,  # Will reach boundary token saturation and safely halt chaining
        },
        "expected_decision": Decision.EXECUTE_SAMPLING_BOUNDARY_PIPELINE.value,
        "expected_rationale_keywords": [
            "sampling",
            "temperature",
            "boundary",
            "1.0",
            "token",
            "budget",
        ],
    },
    "SCENARIO_MISSING_INFO": {
        "scenario_type": "missing_information",
        "description": "Defective configuration lacking required environment secrets, passing unsupported temperature to reasoning model, and omitting required prompt facts.",
        "model_id": "gpt-5-mini",
        "model_family": "reasoning",
        "facts": {
            "api_key_env_var_set": False,  # Violates secret isolation
            "api_endpoint_env_var_set": False,
            "temperature": 0.7,  # Illegal: temperature not supported on reasoning models
            "max_output_tokens": None,  # Missing token budget
            "prompt_inputs": {
                "no_recipes": None,  # Missing quantity
                "ingredients": None,  # Missing ingredients
                "filter_exclusion": None,
            },
            "chain_shopping_list": False,
        },
        "expected_decision": Decision.HALT_MISSING_PREREQUISITES.value,
        "expected_rationale_keywords": [
            "missing",
            "environment",
            "secrets",
            "reasoning",
            "halt",
        ],
    },
}


# ============================================================================
# Deterministic Mock Generators (Local Contract Fixtures)
# ============================================================================

def _mock_generate_recipes(
    no_recipes: int,
    ingredients: List[str],
    filter_exclusion: Optional[str],
    model_family: str,
    temperature: Optional[float],
) -> Tuple[str, int]:
    """Generates mock recipe text adhering to inputs and negative allergy filters.

    Returns:
        Tuple of (recipe_text, tokens_consumed)
    """
    cleaned_filter = (filter_exclusion or "").strip().lower()

    if "chicken" in ingredients and "potatoes" in ingredients:
        recipe_catalog = [
            (
                "1. Oven-Roasted Chicken with Potatoes and Carrots:\n"
                "Ingredients:\n"
                "- 4 chicken thighs\n"
                "- 2 potatoes, cut into cubes\n"
                "- 2 carrots, cut into cubes\n"
                "- 2 tablespoons olive oil\n"
                "- 1 teaspoon dried thyme\n"
                "- 1 teaspoon dried oregano\n"
                "- Salt and pepper, to taste"
            ),
            (
                "2. Chicken and Potato Stew:\n"
                "Ingredients:\n"
                "- 2 tablespoons olive oil\n"
                "- 1 onion, diced\n"
                "- 2 chicken breasts, cut into cubes\n"
                "- 2 potatoes, cut into cubes\n"
                "- 2 carrots, cut into cubes\n"
                "- 1 teaspoon dried oregano\n"
                "- 1 teaspoon dried thyme\n"
                "- 1 cup chicken broth\n"
                "- Salt and pepper, to taste"
            ),
            (
                "3. Chicken and Potato Bake:\n"
                "Ingredients:\n"
                "- 2 tablespoons olive oil\n"
                "- 2 chicken breasts, cut into cubes\n"
                "- 2 potatoes, cut into cubes\n"
                "- 2 carrots, cut into cubes\n"
                "- 1 onion, diced\n"
                "- 1 teaspoon dried oregano\n"
                "- 1 teaspoon dried thyme\n"
                "- 1 cup chicken broth\n"
                "- Salt and pepper, to taste"
            ),
        ]
        chosen = recipe_catalog[:no_recipes]
        text = "\n\n".join(chosen)
        # Token estimation: standard 240 tokens for 3-recipe text
        tokens = 80 * len(chosen)
        return text, tokens

    elif "apple" in ingredients and "flour" in ingredients:
        text = (
            "1. Spiced Apple and Flour Pancakes:\n"
            "Ingredients:\n"
            "- 1 cup flour\n"
            "- 1/2 tsp baking powder\n"
            "- 1/2 tsp baking soda\n"
            "- 1/4 tsp salt\n"
            "- 1 egg\n"
            "- 1 cup buttermilk\n"
            "- 1/4 cup melted butter\n"
            "- 1 Granny Smith apple, peeled and grated\n"
            "- 1/4 tsp cinnamon"
        )
        # Exactly 150 tokens to demonstrate tight boundary saturation
        return text, 150

    else:
        text = f"1. Custom Dish:\nIngredients: {', '.join(ingredients)}"
        return text, 50


def _mock_generate_shopping_list(
    primary_recipe_text: str,
    pantry_ingredients: List[str],
) -> Tuple[str, List[str], int]:
    """Generates shopping list from recipe text, strictly excluding pantry items.

    Returns:
        Tuple of (shopping_list_text, shopping_list_items, tokens_consumed)
    """
    pantry_lower = {ing.strip().lower() for ing in pantry_ingredients}

    # Extract all candidate ingredient lines
    all_needed = [
        "olive oil",
        "onion",
        "thyme",
        "oregano",
        "salt",
        "pepper",
        "chicken broth",
    ]
    # Filter out anything already available in pantry
    to_buy = [item for item in all_needed if item.lower() not in pantry_lower]

    formatted_items = "\n".join(f"- {item.capitalize()}" for item in to_buy)
    text = f"Shopping List:\n{formatted_items}"
    tokens = 110
    return text, to_buy, tokens


# ============================================================================
# Invariant Checkers
# ============================================================================

def verify_token_conservation_invariant(
    state_trace: List[IntermediateState],
    total_tokens_consumed: int,
    token_budget: Optional[int],
) -> Tuple[bool, str]:
    """Tests that token usage matches sum of intermediate generation steps and stays within budget."""
    calculated_sum = sum(s.step_tokens_generated for s in state_trace)
    if calculated_sum != total_tokens_consumed:
        return (
            False,
            f"Token mismatch: sum of step tokens ({calculated_sum}) != total_tokens_consumed ({total_tokens_consumed})",
        )

    last_cumulative = state_trace[-1].cumulative_tokens if state_trace else 0
    if last_cumulative != total_tokens_consumed:
        return (
            False,
            f"State trace cumulative mismatch: final step cumulative ({last_cumulative}) != total ({total_tokens_consumed})",
        )

    if token_budget is not None and total_tokens_consumed > token_budget:
        return (
            False,
            f"Token budget exceeded: consumed {total_tokens_consumed} > budget {token_budget}",
        )

    return True, "Token conservation holds across all steps and within budget limit."


def verify_allergen_exclusion_invariant(
    filter_exclusion: Optional[str],
    state_trace: List[IntermediateState],
    final_text: Optional[str],
) -> Tuple[bool, str]:
    """Tests that specified excluded allergens/ingredients never leak into intermediate or final text."""
    if not filter_exclusion or not filter_exclusion.strip():
        return True, "No allergy filter specified; exclusion invariant vacuously satisfied."

    target = filter_exclusion.strip().lower()

    # Check Step 3 (Primary Generation)
    step3 = next((s for s in state_trace if s.step_name == PipelineStep.STEP_3_PRIMARY_GENERATION), None)
    if step3 and step3.status == StepStatus.SUCCESS:
        recipe_text = step3.payload.get("recipe_text", "").lower()
        if target in recipe_text:
            return False, f"Allergen '{target}' leaked into Step 3 primary generation text!"

    # Check Step 4 (Context Chaining)
    step4 = next((s for s in state_trace if s.step_name == PipelineStep.STEP_4_CONTEXT_CHAINING), None)
    if step4 and step4.status == StepStatus.SUCCESS:
        shopping_text = step4.payload.get("shopping_list_text", "").lower()
        if target in shopping_text:
            return False, f"Allergen '{target}' leaked into Step 4 shopping list text!"

    # Check Final Output Text
    if final_text and target in final_text.lower():
        return False, f"Allergen '{target}' leaked into final assembled output text!"

    return True, f"Allergen '{target}' is strictly absent in all intermediate and final outputs."


def verify_context_chaining_lineage_invariant(
    chain_shopping_list: bool,
    pantry_ingredients: List[str],
    state_trace: List[IntermediateState],
    final_text: Optional[str],
) -> Tuple[bool, str]:
    """Tests lineage: chained step consumes prior output and shopping list is disjoint from pantry."""
    if not chain_shopping_list:
        return True, "Context chaining was not requested."

    step3 = next((s for s in state_trace if s.step_name == PipelineStep.STEP_3_PRIMARY_GENERATION), None)
    step4 = next((s for s in state_trace if s.step_name == PipelineStep.STEP_4_CONTEXT_CHAINING), None)

    if not step3 or step3.status != StepStatus.SUCCESS:
        return True, "Primary generation did not succeed; chaining lineage not applicable."

    if not step4 or step4.status != StepStatus.SUCCESS:
        return True, "Step 4 chaining was skipped or halted; chaining lineage holds vacuously."

    recipe_text = step3.payload.get("recipe_text", "")
    chained_input_context = step4.payload.get("chained_input_context", "")

    if recipe_text not in chained_input_context:
        return False, "Lineage broken: Step 4 input context does not contain Step 3 recipe text!"

    # Verify shopping list is strictly disjoint from user's initial ingredients
    pantry_set = {p.strip().lower() for p in pantry_ingredients}
    shopping_items = step4.payload.get("shopping_list_items", [])
    overlap = pantry_set.intersection({item.lower() for item in shopping_items})
    if overlap:
        return False, f"Shopping list includes already-owned pantry ingredients: {overlap}"

    return True, "Chaining lineage intact: Step 4 embeds Step 3 context, and shopping list is disjoint from pantry."


def verify_terminal_state_monotonicity_invariant(
    state_trace: List[IntermediateState],
    final_text: Optional[str],
    total_tokens_consumed: int,
) -> Tuple[bool, str]:
    """Tests that halting in Step 1 skips all subsequent steps and produces zero output."""
    step1 = next((s for s in state_trace if s.step_name == PipelineStep.STEP_1_VALIDATION_AND_CONFIG), None)
    if not step1:
        return False, "Step 1 missing from state trace!"

    if step1.status == StepStatus.HALTED:
        downstream = [s for s in state_trace if s.step_index > 1]
        for s in downstream:
            if s.status != StepStatus.SKIPPED:
                return False, f"Step {s.step_index} was not SKIPPED after Step 1 HALT (status: {s.status})!"
        if final_text is not None:
            return False, f"Final text is not None after Step 1 HALT! ({final_text})"
        if total_tokens_consumed != 0:
            return False, f"Tokens consumed is non-zero after Step 1 HALT! ({total_tokens_consumed})"
        return True, "Terminal state monotonicity holds: downstream steps skipped, zero tokens emitted."

    return True, "Pipeline did not halt in Step 1; monotonicity holds."


def verify_all_invariants(
    facts: Dict[str, Any],
    state_trace: List[IntermediateState],
    final_text: Optional[str],
    total_tokens_consumed: int,
    token_budget: Optional[int],
) -> Dict[str, Any]:
    """Runs all formal invariants linking intermediate state to final output."""
    prompt_inputs = facts.get("prompt_inputs") or {}
    filter_exclusion = prompt_inputs.get("filter_exclusion")
    pantry_ingredients = prompt_inputs.get("ingredients") or []
    chain_shopping_list = bool(facts.get("chain_shopping_list"))

    token_ok, token_msg = verify_token_conservation_invariant(
        state_trace, total_tokens_consumed, token_budget
    )
    allergen_ok, allergen_msg = verify_allergen_exclusion_invariant(
        filter_exclusion, state_trace, final_text
    )
    chaining_ok, chaining_msg = verify_context_chaining_lineage_invariant(
        chain_shopping_list, pantry_ingredients, state_trace, final_text
    )
    terminal_ok, terminal_msg = verify_terminal_state_monotonicity_invariant(
        state_trace, final_text, total_tokens_consumed
    )

    all_hold = token_ok and allergen_ok and chaining_ok and terminal_ok

    return {
        "all_invariants_hold": all_hold,
        "token_conservation": {"holds": token_ok, "details": token_msg},
        "allergen_exclusion": {"holds": allergen_ok, "details": allergen_msg},
        "context_chaining_lineage": {"holds": chaining_ok, "details": chaining_msg},
        "terminal_state_monotonicity": {"holds": terminal_ok, "details": terminal_msg},
    }


# ============================================================================
# Core Pipeline Engine (State Machine with Step-by-Step State Tracing)
# ============================================================================

def run_text_generation_pipeline(
    facts: Dict[str, Any],
    scenario_id: str = "custom",
    scenario_type: str = "custom",
    model_id: str = "unspecified-model",
    model_family: str = "reasoning",
) -> PipelineOutput:
    """Executes the 5-step text generation application pipeline with state tracing.

    Steps:
    1. Configuration & Parameter Validation
    2. Prompt Template Construction
    3. Primary Text Generation (Recipes)
    4. Multi-Step Context Chaining (Shopping List)
    5. Final Assembly & Invariant Verification
    """
    state_trace: List[IntermediateState] = []
    cumulative_tokens = 0

    # -------------------------------------------------------------------------
    # STEP 1: Configuration & Parameter Validation
    # -------------------------------------------------------------------------
    api_key_set = bool(facts.get("api_key_env_var_set"))
    api_endpoint_set = bool(facts.get("api_endpoint_env_var_set"))
    temp = facts.get("temperature")
    token_budget = facts.get("max_output_tokens")
    prompt_inputs = facts.get("prompt_inputs")

    missing_fields: List[str] = []
    incompatible_params: List[str] = []

    if not api_key_set:
        missing_fields.append("AZURE_OPENAI_API_KEY / OPENAI_API_KEY")
    if not api_endpoint_set:
        missing_fields.append("AZURE_OPENAI_ENDPOINT")
    if token_budget is None:
        missing_fields.append("max_output_tokens")
    if not prompt_inputs or not isinstance(prompt_inputs, dict):
        missing_fields.append("prompt_inputs")
    else:
        if prompt_inputs.get("no_recipes") is None:
            missing_fields.append("prompt_inputs.no_recipes")
        if prompt_inputs.get("ingredients") is None:
            missing_fields.append("prompt_inputs.ingredients")

    # Reasoning models explicitly do NOT support temperature or top_p
    if model_family == "reasoning" and temp is not None:
        incompatible_params.append("temperature (reasoning models do not support temperature)")

    # Sampling models require temperature in [0.0, 1.0]
    if model_family == "sampling" and temp is not None:
        if not (0.0 <= temp <= 1.0):
            incompatible_params.append(f"temperature {temp} out of bounds [0.0, 1.0]")

    has_fatal_error = bool(missing_fields or incompatible_params)

    step1_status = StepStatus.HALTED if has_fatal_error else StepStatus.SUCCESS
    step1_payload = {
        "api_secrets_verified": api_key_set and api_endpoint_set,
        "model_id": model_id,
        "model_family": model_family,
        "temperature": temp,
        "token_budget": token_budget,
        "missing_fields": missing_fields,
        "incompatible_params": incompatible_params,
        "is_boundary_temperature": (temp == 1.0),
    }

    state_trace.append(
        IntermediateState(
            step_index=1,
            step_name=PipelineStep.STEP_1_VALIDATION_AND_CONFIG,
            status=step1_status,
            payload=step1_payload,
            step_tokens_generated=0,
            cumulative_tokens=cumulative_tokens,
            invariants_checked={"config_valid": not has_fatal_error},
            notes="Validated environment secrets, model parameters, and required prompt keys.",
        )
    )

    if has_fatal_error:
        # Short-circuit remaining steps
        for idx, step_name in [
            (2, PipelineStep.STEP_2_PROMPT_CONSTRUCTION),
            (3, PipelineStep.STEP_3_PRIMARY_GENERATION),
            (4, PipelineStep.STEP_4_CONTEXT_CHAINING),
            (5, PipelineStep.STEP_5_FINAL_ASSEMBLY),
        ]:
            state_trace.append(
                IntermediateState(
                    step_index=idx,
                    step_name=step_name,
                    status=StepStatus.SKIPPED,
                    payload={"reason": "PREVIOUS_STEP_HALTED"},
                    step_tokens_generated=0,
                    cumulative_tokens=cumulative_tokens,
                    notes="Step skipped due to fatal validation errors in Step 1.",
                )
            )

        rationale = (
            f"Execution safely halted at Step 1 due to missing or incompatible prerequisites: "
            f"missing fields={missing_fields}; incompatible parameters={incompatible_params}. "
            f"Lesson 06 strictly requires separating secrets and API credentials via environment variables, "
            f"specifying valid token limits, and avoiding sampling controls (temperature) on reasoning models."
        )

        inv_summary = verify_all_invariants(facts, state_trace, None, 0, token_budget)

        return PipelineOutput(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            model_id=model_id,
            decision=Decision.HALT_MISSING_PREREQUISITES,
            rationale=rationale,
            state_trace=state_trace,
            final_text=None,
            total_tokens_consumed=0,
            token_budget=token_budget,
            invariants_summary=inv_summary,
            diagnostic_envelope={
                "missing_fields": missing_fields,
                "incompatible_params": incompatible_params,
            },
        )

    # -------------------------------------------------------------------------
    # STEP 2: Prompt Template Construction
    # -------------------------------------------------------------------------
    no_recipes = prompt_inputs["no_recipes"]
    ingredients = prompt_inputs["ingredients"]
    filter_exclusion = prompt_inputs.get("filter_exclusion")

    ing_str = ", ".join(ingredients)
    base_prompt = f"Show me {no_recipes} recipes for a dish with the following ingredients: {ing_str}. Per recipe, list all the ingredients used"
    if filter_exclusion:
        prompt_text = f"{base_prompt}, no {filter_exclusion}"
    else:
        prompt_text = base_prompt

    # Prompt tokens estimate (~1 token per word + formatting)
    prompt_tokens_est = len(prompt_text.split()) + 4

    step2_payload = {
        "prompt_text": prompt_text,
        "prompt_tokens_estimate": prompt_tokens_est,
        "ingredients": ingredients,
        "no_recipes": no_recipes,
        "filter_exclusion": filter_exclusion,
    }

    state_trace.append(
        IntermediateState(
            step_index=2,
            step_name=PipelineStep.STEP_2_PROMPT_CONSTRUCTION,
            status=StepStatus.SUCCESS,
            payload=step2_payload,
            step_tokens_generated=0,  # Prompt input tokens not counted as generated output
            cumulative_tokens=cumulative_tokens,
            invariants_checked={"prompt_non_empty": bool(prompt_text)},
            notes="Constructed interpolated prompt template with allergen filter constraint.",
        )
    )

    # -------------------------------------------------------------------------
    # STEP 3: Primary Text Generation (Mock Execution)
    # -------------------------------------------------------------------------
    recipe_text, primary_tokens = _mock_generate_recipes(
        no_recipes=no_recipes,
        ingredients=ingredients,
        filter_exclusion=filter_exclusion,
        model_family=model_family,
        temperature=temp,
    )
    cumulative_tokens += primary_tokens

    step3_payload = {
        "recipe_text": recipe_text,
        "primary_tokens_consumed": primary_tokens,
        "cumulative_tokens": cumulative_tokens,
        "allergen_checked": filter_exclusion.lower() not in recipe_text.lower() if filter_exclusion else True,
    }

    state_trace.append(
        IntermediateState(
            step_index=3,
            step_name=PipelineStep.STEP_3_PRIMARY_GENERATION,
            status=StepStatus.SUCCESS,
            payload=step3_payload,
            step_tokens_generated=primary_tokens,
            cumulative_tokens=cumulative_tokens,
            invariants_checked={"allergen_excluded": step3_payload["allergen_checked"]},
            notes="Executed primary text generation of recipes matching input constraints.",
        )
    )

    # -------------------------------------------------------------------------
    # STEP 4: Context Chaining (Shopping List Synthesis)
    # -------------------------------------------------------------------------
    chain_requested = bool(facts.get("chain_shopping_list"))
    tokens_remaining = (token_budget - cumulative_tokens) if token_budget else 0

    MIN_CHAINING_HEADROOM = 60  # Minimum tokens needed for secondary shopping list

    if not chain_requested:
        step4_status = StepStatus.SKIPPED
        step4_payload = {"reason": "CHAINING_NOT_REQUESTED"}
        step4_tokens = 0
        shopping_text = None
        shopping_items = []
    elif tokens_remaining < MIN_CHAINING_HEADROOM:
        # Boundary saturation: headroom exhausted!
        step4_status = StepStatus.BOUNDARY_SATURATED
        step4_payload = {
            "reason": "INSUFFICIENT_TOKEN_HEADROOM_AT_BOUNDARY",
            "tokens_remaining": tokens_remaining,
            "min_required": MIN_CHAINING_HEADROOM,
        }
        step4_tokens = 0
        shopping_text = None
        shopping_items = []
    else:
        # Perform chaining
        chained_prompt = f"{recipe_text} Produce a shopping list for the generated recipes and please don't include ingredients that I already have."
        shopping_text, shopping_items, step4_tokens = _mock_generate_shopping_list(
            primary_recipe_text=recipe_text,
            pantry_ingredients=ingredients,
        )
        cumulative_tokens += step4_tokens
        step4_status = StepStatus.SUCCESS
        step4_payload = {
            "chained_input_context": chained_prompt,
            "shopping_list_text": shopping_text,
            "shopping_list_items": shopping_items,
            "chaining_tokens_consumed": step4_tokens,
            "cumulative_tokens": cumulative_tokens,
        }

    state_trace.append(
        IntermediateState(
            step_index=4,
            step_name=PipelineStep.STEP_4_CONTEXT_CHAINING,
            status=step4_status,
            payload=step4_payload,
            step_tokens_generated=step4_tokens,
            cumulative_tokens=cumulative_tokens,
            invariants_checked={"headroom_respected": cumulative_tokens <= (token_budget or 999999)},
            notes="Evaluated context chaining headroom and synthesized shopping list if quota allowed.",
        )
    )

    # -------------------------------------------------------------------------
    # STEP 5: Final Assembly & Invariant Verification
    # -------------------------------------------------------------------------
    if shopping_text:
        final_text = f"{recipe_text}\n\n{shopping_text}"
    else:
        final_text = recipe_text

    inv_summary = verify_all_invariants(
        facts, state_trace, final_text, cumulative_tokens, token_budget
    )

    if not inv_summary["all_invariants_hold"]:
        raise InvariantViolationError(
            "PIPELINE_INVARIANTS_FAILED",
            "One or more state trace invariants failed linking intermediate state to final output.",
            inv_summary,
        )

    # Determine Decision & Rationale
    if model_family == "sampling" and temp == 1.0:
        decision = Decision.EXECUTE_SAMPLING_BOUNDARY_PIPELINE
        rationale = (
            f"Successfully executed sampling model '{model_id}' at the creative temperature boundary of 1.0. "
            f"Under the tight token budget limit of {token_budget} tokens, primary generation consumed {primary_tokens} "
            f"tokens (100% capacity), reaching the boundary threshold. In accordance with Lesson 06 token budgeting, "
            f"secondary context chaining was safely bypassed to prevent quota overflow, and intermediate states "
            f"confirm full invariant satisfaction."
        )
    else:
        decision = Decision.EXECUTE_REASONING_PIPELINE
        rationale = (
            f"Successfully executed reasoning model '{model_id}' pipeline. In accordance with Lesson 06, "
            f"temperature sampling was omitted, API credentials were authenticated via environment variables, "
            f"and two-step context chaining safely synthesized recipes and shopping list within the {token_budget} "
            f"token budget. Negative filter '{filter_exclusion}' was strictly maintained across all intermediate states."
        )

    step5_payload = {
        "decision": decision.value,
        "total_tokens_consumed": cumulative_tokens,
        "token_budget": token_budget,
        "invariants_summary": inv_summary,
        "boundary_condition_triggered": (step4_status == StepStatus.BOUNDARY_SATURATED),
    }

    state_trace.append(
        IntermediateState(
            step_index=5,
            step_name=PipelineStep.STEP_5_FINAL_ASSEMBLY,
            status=StepStatus.SUCCESS,
            payload=step5_payload,
            step_tokens_generated=0,
            cumulative_tokens=cumulative_tokens,
            invariants_checked={"all_invariants_hold": inv_summary["all_invariants_hold"]},
            notes="Assembled final multi-step output and verified all state-to-output invariants.",
        )
    )

    return PipelineOutput(
        scenario_id=scenario_id,
        scenario_type=scenario_type,
        model_id=model_id,
        decision=decision,
        rationale=rationale,
        state_trace=state_trace,
        final_text=final_text,
        total_tokens_consumed=cumulative_tokens,
        token_budget=token_budget,
        invariants_summary=inv_summary,
    )


# ============================================================================
# Published Decision Table Checker
# ============================================================================

def check_decision_table(
    table: Dict[str, Dict[str, Any]],
    fail_on_tamper: bool = True,
) -> Dict[str, Any]:
    """Evaluates each scenario in the decision table and verifies decisions, rationales, and invariants.

    If fail_on_tamper is True, raises DecisionMismatchError when any evaluated decision
    deviates from the expected decision in the table.
    """
    scenarios_results: List[Dict[str, Any]] = []
    all_passed = True

    for scenario_id, entry in table.items():
        scenario_type = entry.get("scenario_type", "unknown")
        model_id = entry.get("model_id", "unspecified")
        model_family = entry.get("model_family", "reasoning")
        facts = entry.get("facts", {})
        expected_decision = entry.get("expected_decision")
        expected_keywords = entry.get("expected_rationale_keywords", [])

        # Execute pipeline with state tracing
        output = run_text_generation_pipeline(
            facts=facts,
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            model_id=model_id,
            model_family=model_family,
        )

        actual_decision = output.decision.value
        matches_table = (actual_decision == expected_decision)

        # Check rationale keywords
        rationale_lower = output.rationale.lower()
        missing_keywords = [kw for kw in expected_keywords if kw.lower() not in rationale_lower]
        rationale_valid = (len(missing_keywords) == 0)

        invariants_hold = output.invariants_summary.get("all_invariants_hold", False)

        scenario_passed = matches_table and rationale_valid and invariants_hold
        if not scenario_passed:
            all_passed = False

        if not matches_table and fail_on_tamper:
            raise DecisionMismatchError(
                f"Scenario '{scenario_id}' decision mismatch: expected '{expected_decision}', got '{actual_decision}'",
                scenario_id=scenario_id,
                expected=str(expected_decision),
                actual=actual_decision,
                rationale=output.rationale,
            )

        scenarios_results.append({
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "model_id": model_id,
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "matches_table": matches_table,
            "rationale_valid": rationale_valid,
            "missing_keywords": missing_keywords,
            "invariants_hold": invariants_hold,
            "total_tokens_consumed": output.total_tokens_consumed,
            "token_budget": output.token_budget,
            "status": "PASS" if scenario_passed else "FAIL",
            "rationale": output.rationale,
            "state_trace_steps": len(output.state_trace),
        })

    passed_count = sum(1 for s in scenarios_results if s["status"] == "PASS")
    failed_count = len(scenarios_results) - passed_count

    return {
        "status": "success" if all_passed else "failure",
        "total_scenarios": len(scenarios_results),
        "passed_scenarios": passed_count,
        "failed_scenarios": failed_count,
        "all_passed": all_passed,
        "scenarios": scenarios_results,
    }


# ============================================================================
# CLI Entrypoint
# ============================================================================

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="R40-T024: Worked Decision Example and State Trace Checker for Building Text Generation Applications."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run the decision table checker against all three canonical scenarios.",
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "missing"],
        help="Run a specific scenario and emit its detailed state trace and invariant summary.",
    )
    parser.add_argument(
        "--deliberate-tamper",
        metavar="SCENARIO_ID",
        help="Deliberately mutate the expected decision for the specified scenario to verify checker failure.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print the formatted intermediate state trace after each step.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output.",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parsed = parse_args(args)

    # 1. Deliberate tamper test
    if parsed.deliberate_tamper:
        tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
        target = parsed.deliberate_tamper
        if target not in tampered_table:
            print(f"Error: Unknown scenario id '{target}'. Available: {list(tampered_table.keys())}", file=sys.stderr)
            return 1

        # Mutate to incorrect decision
        original = tampered_table[target]["expected_decision"]
        tampered_table[target]["expected_decision"] = "DELIBERATELY_MUTATED_WRONG_DECISION"
        print(f"[DEMO] Mutated '{target}' expected decision from '{original}' to 'DELIBERATELY_MUTATED_WRONG_DECISION'", file=sys.stderr)

        try:
            check_decision_table(tampered_table, fail_on_tamper=True)
            print("ERROR: Checker unexpectedly passed tampered table!", file=sys.stderr)
            return 0
        except DecisionMismatchError as err:
            print(f"[EXPECTED FAILURE CONFIRMED] DecisionMismatchError caught: {err}", file=sys.stderr)
            return 1

    # 2. Single scenario run
    if parsed.scenario:
        scenario_key_map = {
            "normal": "SCENARIO_NORMAL",
            "boundary": "SCENARIO_BOUNDARY",
            "missing": "SCENARIO_MISSING_INFO",
        }
        key = scenario_key_map[parsed.scenario]
        entry = PUBLISHED_DECISION_TABLE[key]

        output = run_text_generation_pipeline(
            facts=entry["facts"],
            scenario_id=key,
            scenario_type=entry["scenario_type"],
            model_id=entry["model_id"],
            model_family=entry["model_family"],
        )

        res_dict = output.to_dict()
        if not parsed.trace:
            # Exclude full trace unless requested
            res_dict.pop("state_trace", None)

        indent = 2 if parsed.pretty else None
        print(json.dumps(res_dict, indent=indent))
        return 0

    # 3. Default or --check: Check all published table scenarios
    try:
        report = check_decision_table(PUBLISHED_DECISION_TABLE, fail_on_tamper=True)
        indent = 2 if parsed.pretty else None
        print(json.dumps(report, indent=indent))
        return 0 if report["all_passed"] else 1
    except DecisionMismatchError as err:
        print(f"Checker failed with DecisionMismatchError: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
