"""
Open Source Models Assessment: Scenarios, Decision Checker & Applied Questions (R40-T040).

Demonstrates decision making for model selection (Strict Open Source vs Open Weights vs Proprietary)
in alignment with Lesson 16 ("What are Open Source Models?"). Includes three applied questions
covering output prediction, failure diagnosis, and boundary policy selection with executable checks.
"""

from typing import Dict, Any, List, Tuple


DECISION_TABLE: List[Dict[str, Any]] = [
    {
        "id": "scenario_normal",
        "description": "Normal scenario: Full transparency required with public weights, dataset, and code",
        "input": {
            "requires_on_prem": True,
            "requires_full_open_source": True,
            "commercial_use": True,
            "has_public_weights": True,
            "has_public_dataset": True,
        },
        "expected_decision": "SELECT_FULL_OPEN_SOURCE",
        "model_category": "open_source_strict",
        "rationale": "All criteria met (public weights, public dataset, open licensing); aligns with OSI/AllenAI OLMo open source criteria.",
    },
    {
        "id": "scenario_boundary",
        "description": "Boundary scenario: Public weights available for local deployment, but training dataset is private",
        "input": {
            "requires_on_prem": True,
            "requires_full_open_source": False,
            "commercial_use": True,
            "has_public_weights": True,
            "has_public_dataset": False,
        },
        "expected_decision": "SELECT_OPEN_WEIGHTS_MODEL",
        "model_category": "open_weights",
        "rationale": "Model weights are downloadable for local execution, but private training data classifies it as an open-weights model rather than strict open source.",
    },
    {
        "id": "scenario_missing_info",
        "description": "Missing-information scenario: Weight distribution status is unknown/missing",
        "input": {
            "requires_on_prem": True,
            "requires_full_open_source": False,
            "commercial_use": True,
            "has_public_weights": None,
            "has_public_dataset": False,
        },
        "expected_decision": "REJECT_INSUFFICIENT_SPECIFICATION",
        "model_category": "unknown",
        "rationale": "Model weight availability is missing (None); cannot evaluate suitability for local deployment.",
    },
]


def evaluate_model_selection(facts: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates input facts against Lesson 16 open source model taxonomy."""
    has_weights = facts.get("has_public_weights")
    if has_weights is None:
        return {
            "decision": "REJECT_INSUFFICIENT_SPECIFICATION",
            "model_category": "unknown",
            "rationale": "Model weight availability is missing (None); cannot evaluate suitability for local deployment.",
        }

    has_dataset = bool(facts.get("has_public_dataset", False))
    requires_full = bool(facts.get("requires_full_open_source", False))

    if not has_weights:
        return {
            "decision": "REJECT_PROPRIETARY_OR_UNAVAILABLE",
            "model_category": "closed_proprietary",
            "rationale": "Weights are not publicly downloadable; cannot run on-premises without cloud vendor lock-in.",
        }

    if has_dataset and requires_full:
        return {
            "decision": "SELECT_FULL_OPEN_SOURCE",
            "model_category": "open_source_strict",
            "rationale": "All criteria met (public weights, public dataset, open licensing); aligns with OSI/AllenAI OLMo open source criteria.",
        }

    return {
        "decision": "SELECT_OPEN_WEIGHTS_MODEL",
        "model_category": "open_weights",
        "rationale": "Model weights are downloadable for local execution, but private training data classifies it as an open-weights model rather than strict open source.",
    }


def check_decision_table(table: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validates the published decision table against the evaluator."""
    errors = []
    for item in table:
        res = evaluate_model_selection(item["input"])
        if res["decision"] != item["expected_decision"]:
            errors.append(f"{item['id']}: expected '{item['expected_decision']}', got '{res['decision']}'")
        if res["model_category"] != item["model_category"]:
            errors.append(f"{item['id']}: expected category '{item['model_category']}', got '{res['model_category']}'")
    return (len(errors) == 0, errors)


# Three applied questions tied to the lesson and local example
APPLIED_QUESTIONS = [
    {
        "id": "q1_predict_output",
        "question": "Given a deployment requiring on-premises execution where weights are downloadable but datasets are private, what decision is predicted?",
        "expected_answer": "SELECT_OPEN_WEIGHTS_MODEL",
        "rationale": "According to Lesson 16, models like Llama 2 and Mistral publish weights but not complete training datasets, fitting the open-weights category.",
    },
    {
        "id": "q2_diagnose_failure",
        "question": "Why does evaluating an input with has_public_weights=None fail?",
        "expected_answer": "REJECT_INSUFFICIENT_SPECIFICATION",
        "rationale": "Without explicit weight availability status, the system cannot verify whether the model can be hosted offline or requires proprietary API access.",
    },
    {
        "id": "q3_choose_boundary_policy",
        "question": "When a project mandates strict OSI compliance (code, weights, and training datasets must all be public), which model category policy must be chosen?",
        "expected_answer": "SELECT_FULL_OPEN_SOURCE",
        "rationale": "True open source models (e.g. OLMo) satisfy the OSI definition by openly providing dataset, code, metrics, and weights.",
    },
]


def check_applied_question(question_id: str, candidate_answer: str) -> Tuple[bool, str]:
    """Executes verification for an applied question answer."""
    match = next((q for q in APPLIED_QUESTIONS if q["id"] == question_id), None)
    if not match:
        return False, f"Unknown question ID: {question_id}"
    if candidate_answer == match["expected_answer"]:
        return True, match["rationale"]
    return False, f"Incorrect answer '{candidate_answer}'. Expected '{match['expected_answer']}'"
