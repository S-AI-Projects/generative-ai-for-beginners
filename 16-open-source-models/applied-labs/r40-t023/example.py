#!/usr/bin/env python3
"""R40-T023: Worked Decision Example for 'What are Open Source Models?'

This applied lab implements a worked decision framework and comparison checker
for classifying AI models based on the transparency criteria taught in Lesson 16
("What are Open Source Models?" in 16-open-source-models/README.md).

Lesson Context:
Traditional open-source software is governed by OSI criteria. For LLMs, the
lesson identifies five key criteria required to align with the traditional
definition of open source:
1. Publicly available training datasets.
2. Publicly available full model weights as part of the training.
3. Publicly available evaluation code.
4. Publicly available fine-tuning code.
5. Publicly available full model weights and training metrics/logs.

Models meeting all criteria (such as AllenAI OLMo) qualify as traditional open source.
Models that release weights but withhold training datasets or metrics (such as Llama 2,
Mistral, or Falcon) fall on the boundary and are termed "open models" or "open weights".
Models with unverified or missing disclosures cannot be classified and are "undetermined".

Task Scope:
This is a small local contract fixture running entirely with Python's standard library.
No real model downloads, cloud API keys, GPU acceleration, or physical devices are required.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Decision(str, Enum):
    """Classification decisions for model openness."""

    OPEN_SOURCE = "OPEN_SOURCE"
    OPEN_WEIGHTS = "OPEN_WEIGHTS"
    UNDETERMINED = "UNDETERMINED"
    PROPRIETARY = "PROPRIETARY"


class DecisionMismatchError(Exception):
    """Raised when an evaluated decision deviates from the expected decision."""

    def __init__(self, message: str, scenario_id: str, expected: str, actual: str, rationale: str) -> None:
        super().__init__(message)
        self.scenario_id = scenario_id
        self.expected = expected
        self.actual = actual
        self.rationale = rationale


# The six core transparency criteria taught in Lesson 16
REQUIRED_CRITERIA_KEYS = (
    "model_weights_public",
    "training_datasets_public",
    "evaluation_code_public",
    "fine_tuning_code_public",
    "training_metrics_public",
    "osi_approved_license",
)


# ---------------------------------------------------------------------------
# Published Decision Table (Three Core Scenarios: Normal, Boundary, Missing)
# ---------------------------------------------------------------------------
PUBLISHED_DECISION_TABLE: Dict[str, Dict[str, Any]] = {
    "SCENARIO_NORMAL": {
        "scenario_type": "normal",
        "description": "Fully disclosed open-source foundation model meeting all Lesson 16 criteria (exemplar: AllenAI OLMo).",
        "model_id": "allenai-olmo-7b-fixture",
        "model_name": "OLMo-7B-OpenSource-Fixture",
        "facts": {
            "model_weights_public": True,
            "training_datasets_public": True,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": True,
            "osi_approved_license": True,
        },
        "expected_decision": Decision.OPEN_SOURCE.value,
        "expected_rationale_keywords": [
            "training datasets",
            "model weights",
            "evaluation code",
            "fine-tuning code",
            "training metrics",
            "OLMo",
        ],
    },
    "SCENARIO_BOUNDARY": {
        "scenario_type": "boundary",
        "description": "Open-weights model with public weights/fine-tuning but withheld training data and metrics (exemplar: Llama 2, Mistral).",
        "model_id": "llama-2-chat-fixture",
        "model_name": "Llama-2-Like-Chat-Fixture",
        "facts": {
            "model_weights_public": True,
            "training_datasets_public": False,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": False,
            "osi_approved_license": False,
        },
        "expected_decision": Decision.OPEN_WEIGHTS.value,
        "expected_rationale_keywords": [
            "open model",
            "open weights",
            "withheld",
            "boundary",
        ],
    },
    "SCENARIO_MISSING_INFO": {
        "scenario_type": "missing_information",
        "description": "Candidate model with incomplete or unverified disclosures for critical audit fields.",
        "model_id": "unverified-candidate-v1",
        "model_name": "Candidate-LLM-Incomplete-Fixture",
        "facts": {
            "model_weights_public": True,
            "training_datasets_public": None,  # Missing / unverified disclosure
            "evaluation_code_public": True,
            "fine_tuning_code_public": None,  # Missing / unverified disclosure
            "training_metrics_public": None,  # Missing / unverified disclosure
            "osi_approved_license": None,  # Missing / unverified license
        },
        "expected_decision": Decision.UNDETERMINED.value,
        "expected_rationale_keywords": [
            "missing",
            "unverified",
            "transparency",
            "undetermined",
        ],
    },
}


# ---------------------------------------------------------------------------
# Approach 1: Direct Rule Engine (Structured Evaluation with Lesson Rationale)
# ---------------------------------------------------------------------------
def evaluate_model_direct(facts: Dict[str, Any], model_id: str = "custom-model") -> Dict[str, Any]:
    """Direct implementation evaluating model transparency facts against Lesson 16 criteria.

    Returns a rich structured evaluation dictionary containing decision, decision_code,
    criteria summary, missing criteria, and an educational rationale tied to Lesson 16.
    """
    if not isinstance(facts, dict):
        raise TypeError(f"Model facts must be a dictionary, got {type(facts).__name__}")

    # Identify missing or unspecified criteria
    missing_criteria: List[str] = [
        key for key in REQUIRED_CRITERIA_KEYS if facts.get(key) is None
    ]

    # Evaluate criteria counts
    satisfied_criteria: List[str] = [
        key for key in REQUIRED_CRITERIA_KEYS if facts.get(key) is True
    ]
    withheld_criteria: List[str] = [
        key for key in REQUIRED_CRITERIA_KEYS if facts.get(key) is False
    ]

    # 1. Missing information check (preempts classification if essential criteria are unknown)
    if missing_criteria:
        decision = Decision.UNDETERMINED.value
        decision_code = "DECISION_UNDETERMINED_MISSING_DISCLOSURES"
        missing_list_str = ", ".join(f"'{k}'" for k in sorted(missing_criteria))
        rationale = (
            f"Cannot determine classification for model '{model_id}' because {len(missing_criteria)} "
            f"essential transparency criteria are missing or unverified: [{missing_list_str}], "
            f"leaving the status undetermined. "
            f"As stated in Lesson 16, a rigorous openness assessment requires verified public disclosure "
            f"of training datasets, weights, code, and metrics before classifying a model."
        )

    # 2. Closed / Proprietary check
    elif facts.get("model_weights_public") is False:
        decision = Decision.PROPRIETARY.value
        decision_code = "DECISION_PROPRIETARY"
        rationale = (
            f"Model '{model_id}' is proprietary/closed. The model weights are withheld and not "
            f"publicly accessible for local deployment or inspection."
        )

    # 3. Traditional Open Source check (All 5 Lesson 16 criteria + OSI license met)
    elif len(satisfied_criteria) == len(REQUIRED_CRITERIA_KEYS):
        decision = Decision.OPEN_SOURCE.value
        decision_code = "DECISION_OPEN_SOURCE"
        rationale = (
            f"Model '{model_id}' fully aligns with the traditional definition of open source defined "
            f"in Lesson 16 (exemplified by AllenAI OLMo). All six critical artifacts—training datasets, "
            f"model weights, evaluation code, fine-tuning code, training metrics, and an OSI-approved license—"
            f"are fully public and accessible without proprietary restrictions."
        )

    # 4. Open Weights / Open Model boundary check
    elif facts.get("model_weights_public") is True:
        decision = Decision.OPEN_WEIGHTS.value
        decision_code = "DECISION_OPEN_WEIGHTS"
        withheld_list_str = ", ".join(f"'{k}'" for k in sorted(withheld_criteria))
        rationale = (
            f"Model '{model_id}' provides public model weights for inference and local adaptation, "
            f"but key pre-training artifacts remain withheld: [{withheld_list_str}]. Under the Lesson 16 "
            f"framework, this falls on the boundary: it is classified as an 'open model' or 'open weights' "
            f"model (similar to Llama 2 or Mistral), rather than traditional open source."
        )

    else:
        # Fallback edge case
        decision = Decision.UNDETERMINED.value
        decision_code = "DECISION_UNDETERMINED_EDGE_CASE"
        rationale = f"Model '{model_id}' facts present an unclassifiable combination of attributes."

    return {
        "status": "success",
        "approach": "direct_rule_engine",
        "model_id": model_id,
        "decision": decision,
        "decision_code": decision_code,
        "rationale": rationale,
        "criteria_summary": {
            "total_required": len(REQUIRED_CRITERIA_KEYS),
            "satisfied_count": len(satisfied_criteria),
            "withheld_count": len(withheld_criteria),
            "missing_count": len(missing_criteria),
            "satisfied": satisfied_criteria,
            "withheld": withheld_criteria,
            "missing": missing_criteria,
        },
        "raw_facts": facts,
    }


# ---------------------------------------------------------------------------
# Approach 2: Simpler Independent Calculation (Minimal Baseline Oracle)
# ---------------------------------------------------------------------------
def evaluate_model_independent(facts: Dict[str, Any]) -> str:
    """Minimal independent reference calculation using basic boolean logic.

    Serves as an independent mathematical baseline to cross-check the direct rule engine.
    Given the exact same input facts, it returns only the decision string without rich formatting.
    """
    if not isinstance(facts, dict):
        raise TypeError(f"Facts must be a dict, got {type(facts).__name__}")

    # Check for any missing or None required fields
    for key in REQUIRED_CRITERIA_KEYS:
        if facts.get(key) is None:
            return Decision.UNDETERMINED.value

    # Check weights availability
    if not facts.get("model_weights_public"):
        return Decision.PROPRIETARY.value

    # Check full open source criteria (all 6 must be True)
    if all(facts.get(k) is True for k in REQUIRED_CRITERIA_KEYS):
        return Decision.OPEN_SOURCE.value

    # If weights are public but some criteria are False, it's open weights
    return Decision.OPEN_WEIGHTS.value


# ---------------------------------------------------------------------------
# Decision Table Comparison Checker
# ---------------------------------------------------------------------------
def check_decision_table(
    table: Dict[str, Dict[str, Any]],
    fail_on_tamper: bool = True,
) -> Dict[str, Any]:
    """Runs the comparison checker across all scenarios in the decision table.

    For each scenario:
    1. Evaluates using Approach 1 (direct_rule_engine).
    2. Evaluates using Approach 2 (independent_calculation).
    3. Cross-compares Approach 1 decision, Approach 2 decision, and Table expected decision.
    4. Validates that the educational rationale contains lesson-tied keywords.

    If fail_on_tamper is True and any decision disagrees, raises DecisionMismatchError.
    """
    checked_scenarios: List[Dict[str, Any]] = []
    total_scenarios = len(table)
    passed_scenarios = 0

    for scenario_id, entry in table.items():
        model_id = entry.get("model_id", scenario_id)
        facts = entry.get("facts", {})
        expected_decision = entry.get("expected_decision")
        expected_keywords = entry.get("expected_rationale_keywords", [])

        # Approach 1: Direct Rule Engine
        direct_result = evaluate_model_direct(facts, model_id=model_id)
        direct_decision = direct_result["decision"]
        rationale = direct_result["rationale"]

        # Approach 2: Independent Calculation
        independent_decision = evaluate_model_independent(facts)

        # Cross-approach comparison
        approaches_agree = direct_decision == independent_decision
        matches_table = direct_decision == expected_decision

        # Keyword verification for educational rationale
        missing_keywords = [
            kw for kw in expected_keywords if kw.lower() not in rationale.lower()
        ]
        rationale_valid = len(missing_keywords) == 0

        is_pass = approaches_agree and matches_table and rationale_valid

        scenario_record = {
            "scenario_id": scenario_id,
            "scenario_type": entry.get("scenario_type"),
            "model_id": model_id,
            "expected_decision": expected_decision,
            "direct_decision": direct_decision,
            "independent_decision": independent_decision,
            "approaches_agree": approaches_agree,
            "matches_table": matches_table,
            "rationale_valid": rationale_valid,
            "missing_keywords": missing_keywords,
            "status": "PASS" if is_pass else "FAIL",
            "rationale": rationale,
        }
        checked_scenarios.append(scenario_record)

        if is_pass:
            passed_scenarios += 1
        elif fail_on_tamper:
            raise DecisionMismatchError(
                message=(
                    f"Decision check failed for '{scenario_id}'. "
                    f"Expected='{expected_decision}', Direct='{direct_decision}', "
                    f"Independent='{independent_decision}'. "
                    f"Keyword mismatches: {missing_keywords}"
                ),
                scenario_id=scenario_id,
                expected=str(expected_decision),
                actual=str(direct_decision),
                rationale=rationale,
            )

    all_passed = passed_scenarios == total_scenarios
    return {
        "status": "success" if all_passed else "failure",
        "total_scenarios": total_scenarios,
        "passed_scenarios": passed_scenarios,
        "failed_scenarios": total_scenarios - passed_scenarios,
        "all_passed": all_passed,
        "scenarios": checked_scenarios,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Constructs the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="R40-T023: Open Source Model worked decision example and comparison checker."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Run the comparison checker across the published decision table (default).",
    )
    group.add_argument(
        "--scenario",
        choices=["normal", "boundary", "missing_info", "all"],
        help="Evaluate a specific scenario from the published decision table.",
    )
    group.add_argument(
        "--call",
        type=str,
        help="Evaluate a custom model facts JSON payload against both approaches.",
    )
    group.add_argument(
        "--tamper-test",
        action="store_true",
        help="Deliberately mutate a scenario decision to verify the checker exits non-zero on failure.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI execution handler."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.tamper_test:
            # Deliberately modify a decision in the table to test the checker's failure detection
            tampered_table = copy.deepcopy(PUBLISHED_DECISION_TABLE)
            tampered_table["SCENARIO_NORMAL"]["expected_decision"] = Decision.OPEN_WEIGHTS.value
            sys.stderr.write(
                "Executing deliberate failure verification: Tampering SCENARIO_NORMAL expected_decision to 'OPEN_WEIGHTS'...\n"
            )
            check_decision_table(tampered_table, fail_on_tamper=True)
            sys.stderr.write("ERROR: Checker failed to detect deliberate tamper!\n")
            return 0  # Should not be reached

        if args.scenario:
            scenario_map = {
                "normal": "SCENARIO_NORMAL",
                "boundary": "SCENARIO_BOUNDARY",
                "missing_info": "SCENARIO_MISSING_INFO",
            }
            if args.scenario == "all":
                table_to_run = PUBLISHED_DECISION_TABLE
            else:
                key = scenario_map[args.scenario]
                table_to_run = {key: PUBLISHED_DECISION_TABLE[key]}

            report = check_decision_table(table_to_run, fail_on_tamper=False)
            print(json.dumps(report, indent=2))
            return 0 if report["all_passed"] else 1

        if args.call:
            try:
                payload = json.loads(args.call)
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"Error parsing JSON payload: {exc}\n")
                return 1

            facts = payload.get("facts", payload)
            model_id = payload.get("model_id", "custom-model")
            direct = evaluate_model_direct(facts, model_id=model_id)
            independent = evaluate_model_independent(facts)
            output = {
                "direct_evaluation": direct,
                "independent_decision": independent,
                "approaches_agree": direct["decision"] == independent,
            }
            print(json.dumps(output, indent=2))
            return 0

        # Default action: --check across the full decision table
        report = check_decision_table(PUBLISHED_DECISION_TABLE, fail_on_tamper=True)
        print(json.dumps(report, indent=2))
        return 0

    except DecisionMismatchError as err:
        sys.stderr.write(f"DecisionMismatchError: {err}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"Unexpected error: {err}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
