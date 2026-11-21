"""
Text Generation Application Decision Preflight & Evaluator (R40-T031).

Demonstrates configuration decisions for text generation applications based on
task type (factual/summarization vs creative), available token budget boundaries,
and prompt input validation, in line with Lesson 06 principles.
"""

from typing import Dict, Any, Tuple, List


# Formal published decision table for Lesson 06 worked example
DECISION_TABLE: List[Dict[str, Any]] = [
    {
        "id": "scenario_normal",
        "description": "Normal scenario: Valid prompt with factual summarization task and ample budget",
        "input": {
            "prompt": "Summarize the key features of renewable energy sources in 3 bullet points.",
            "task_type": "summarization",
            "available_budget": 500,
        },
        "expected_decision": "EXECUTE_DETERMINISTIC",
        "expected_status": "READY",
        "rationale": "Valid prompt provided for factual task; configure deterministic low temperature (0.2) and bounded max_tokens (150).",
    },
    {
        "id": "scenario_boundary",
        "description": "Boundary scenario: Valid prompt for creative task right at lower budget threshold",
        "input": {
            "prompt": "Generate a concise slogan for a green energy campaign.",
            "task_type": "creative",
            "available_budget": 35,
        },
        "expected_decision": "CONSTRAIN_BUDGET_EXECUTE",
        "expected_status": "BUDGET_CONSTRAINED",
        "rationale": "Prompt is valid and within minimum token floor, but available budget is at the lower boundary (35 tokens); max_tokens is constrained to remaining budget with creative temperature (0.8).",
    },
    {
        "id": "scenario_missing_info",
        "description": "Missing-information scenario: Empty/whitespace prompt string",
        "input": {
            "prompt": "   ",
            "task_type": "summarization",
            "available_budget": 200,
        },
        "expected_decision": "REJECT_MISSING_PROMPT",
        "expected_status": "ERROR_MISSING_PROMPT",
        "rationale": "Prompt text is empty or missing; cannot execute generation without instructional prompt text.",
    },
]


def approximate_token_count(text: str) -> int:
    """Teaching approximation using whitespace tokenization."""
    if not text:
        return 0
    return len(text.strip().split())


def evaluate_generation_request(prompt: str, task_type: str, available_budget: int) -> Dict[str, Any]:
    """
    Evaluates generation parameters and returns a preflight decision and configuration.

    Parameters:
        prompt: User input prompt string.
        task_type: "summarization", "factual", "creative", or "general".
        available_budget: Max tokens available for both prompt and completion.

    Returns:
        dict containing decision, status, rationale, and runtime parameters.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return {
            "decision": "REJECT_MISSING_PROMPT",
            "status": "ERROR_MISSING_PROMPT",
            "rationale": "Prompt text is empty or missing; cannot execute generation without instructional prompt text.",
            "parameters": {
                "temperature": 0.0,
                "max_tokens": 0,
                "stream": False,
            },
        }

    if not isinstance(available_budget, int) or available_budget <= 0:
        return {
            "decision": "REJECT_INVALID_BUDGET",
            "status": "ERROR_INVALID_BUDGET",
            "rationale": "Available token budget must be a positive integer.",
            "parameters": {
                "temperature": 0.0,
                "max_tokens": 0,
                "stream": False,
            },
        }

    prompt_tokens = approximate_token_count(prompt)
    if prompt_tokens > available_budget:
        return {
            "decision": "REJECT_BUDGET_EXCEEDED",
            "status": "ERROR_BUDGET_EXCEEDED",
            "rationale": f"Prompt length ({prompt_tokens} tokens) exceeds total budget ({available_budget}).",
            "parameters": {
                "temperature": 0.0,
                "max_tokens": 0,
                "stream": False,
            },
        }

    remaining_budget = available_budget - prompt_tokens
    # Lower boundary check: when remaining budget is less than 50 tokens
    if remaining_budget < 50:
        temp = 0.8 if task_type == "creative" else 0.2
        return {
            "decision": "CONSTRAIN_BUDGET_EXECUTE",
            "status": "BUDGET_CONSTRAINED",
            "rationale": f"Prompt is valid and within minimum token floor, but available budget is at the lower boundary ({available_budget} tokens); max_tokens is constrained to remaining budget with {'creative temperature (0.8)' if task_type == 'creative' else 'low temperature (0.2)'}.",
            "parameters": {
                "temperature": temp,
                "max_tokens": remaining_budget,
                "stream": False,
            },
        }

    # Normal scenario
    if task_type in ("summarization", "factual"):
        temp = 0.2
        max_tokens = min(150, remaining_budget)
    else:
        temp = 0.7
        max_tokens = min(300, remaining_budget)

    return {
        "decision": "EXECUTE_DETERMINISTIC" if task_type in ("summarization", "factual") else "EXECUTE_CREATIVE",
        "status": "READY",
        "rationale": "Valid prompt provided for factual task; configure deterministic low temperature (0.2) and bounded max_tokens (150).",
        "parameters": {
            "temperature": temp,
            "max_tokens": max_tokens,
            "stream": False,
        },
    }


def check_decision_table(table: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validates a published decision table against the evaluator.
    Returns (True, []) if all scenarios match expected decisions, else (False, error_messages).
    """
    errors = []
    for item in table:
        inp = item["input"]
        result = evaluate_generation_request(
            prompt=inp.get("prompt", ""),
            task_type=inp.get("task_type", ""),
            available_budget=inp.get("available_budget", 0),
        )
        if result["decision"] != item["expected_decision"]:
            errors.append(
                f"Mismatch in {item['id']}: expected decision '{item['expected_decision']}', got '{result['decision']}'"
            )
        if result["status"] != item["expected_status"]:
            errors.append(
                f"Mismatch in {item['id']}: expected status '{item['expected_status']}', got '{result['status']}'"
            )
    return (len(errors) == 0, errors)
