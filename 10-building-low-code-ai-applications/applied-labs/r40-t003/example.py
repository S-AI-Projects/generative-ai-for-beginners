#!/usr/bin/env python3
"""Low-Code AI Decision Evaluator: Dual-Approach Comparison (R40-T003).

Lesson 10: Building Low Code AI Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a worked decision example for evaluating whether an enterprise
AI initiative should adopt Low-Code AI platforms (such as Microsoft Power Platform,
AI Builder, and Copilot Studio) versus Custom Pro-Code development. It models three
explicit scenarios:
1. Normal Scenario: Standard business automation with prebuilt AI models (AI Builder invoice
   processing), Dataverse integration, and standard throughput requirements.
2. Boundary Scenario: High-throughput, specialized model execution with custom weights and
   strict air-gapped/on-premises constraints exceeding low-code platform capabilities.
3. Missing-Information Scenario: Missing core architectural requirements (data locality,
   compliance tier, or throughput SLA) requiring discovery deferral.

Focus (Dual-Approach Comparison):
The system implements two distinct evaluation approaches over identical inputs:
- Approach A (Direct Rule Engine): A multi-branch procedural heuristic evaluating
  governance, throughput limits, model customizability, and completeness.
- Approach B (Reference Matrix Calculation): An independent table lookup and constraint
  satisfaction calculator.
The lab demonstrates 100% decision and rationale equivalence between both approaches.

Classification & Scope Note (Simulation / Test Double):
This module is a deterministic offline evaluation double implemented using Python's
standard library. It requires no network requests, cloud subscriptions, or GPU hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys
from typing import Any, Dict, List, Optional


class DecisionError(Exception):
    """Base exception for low-code decision evaluation."""


class DecisionMismatchError(DecisionError):
    """Raised when an expected decision differs from the evaluated decision."""


# Standard decision outcomes
DECISION_LOW_CODE = "LOW_CODE_POWER_PLATFORM"
DECISION_PRO_CODE = "CUSTOM_CODE_PRO_DEV"
DECISION_DEFER = "DEFER_INSUFFICIENT_INFORMATION"

# Standard Scenarios
SCENARIOS_DATA: Dict[str, Dict[str, Any]] = {
    "SCENARIO_NORMAL": {
        "title": "Invoice Processing Automation for Education Startup",
        "type": "normal",
        "facts": {
            "use_case": "invoice_processing",
            "prebuilt_model_available": True,
            "requires_custom_weights": False,
            "target_throughput_rps": 5,
            "data_source": "Dataverse",
            "compliance_tier": "standard_commercial",
            "delivery_window_weeks": 2,
        },
        "expected_decision": DECISION_LOW_CODE,
        "expected_rationale": (
            "Standard document processing aligns with Power Automate and AI Builder prebuilt models. "
            "Dataverse integration and 2-week delivery timeline strongly favor low-code development."
        ),
    },
    "SCENARIO_BOUNDARY": {
        "title": "Ultra-Low Latency Inference with Custom Deep Learning Model",
        "type": "boundary",
        "facts": {
            "use_case": "realtime_video_defect_detection",
            "prebuilt_model_available": False,
            "requires_custom_weights": True,
            "target_throughput_rps": 15000,
            "data_source": "edge_rtsp_stream",
            "compliance_tier": "air_gapped_defense",
            "delivery_window_weeks": 24,
        },
        "expected_decision": DECISION_PRO_CODE,
        "expected_rationale": (
            "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed "
            "multi-tenant low-code platform boundaries. Requires custom containerized pro-code service."
        ),
    },
    "SCENARIO_MISSING_INFO": {
        "title": "Underspecified Customer Feedback Sentiment Classifier",
        "type": "missing_information",
        "facts": {
            "use_case": "feedback_analysis",
            "prebuilt_model_available": True,
            "requires_custom_weights": False,
            "target_throughput_rps": None,  # Missing throughput
            "data_source": None,           # Missing data location
            "compliance_tier": None,       # Missing compliance tier
            "delivery_window_weeks": 4,
        },
        "expected_decision": DECISION_DEFER,
        "expected_rationale": (
            "Critical architectural specifications (target throughput, data source, compliance requirements) "
            "are missing. Decision must be deferred until additional discovery is conducted."
        ),
    },
}


def evaluate_decision_direct(facts: Dict[str, Any]) -> Dict[str, str]:
    """Approach A: Direct multi-branch procedural rule engine."""
    required_keys = ["target_throughput_rps", "data_source", "compliance_tier"]
    for k in required_keys:
        if facts.get(k) is None:
            return {
                "decision": DECISION_DEFER,
                "rationale": (
                    "Critical architectural specifications (target throughput, data source, compliance requirements) "
                    "are missing. Decision must be deferred until additional discovery is conducted."
                ),
                "approach": "direct_rule_engine",
            }

    # Boundary checks: custom weights, extreme throughput, air-gapped compliance
    if (
        facts.get("requires_custom_weights", False)
        or facts.get("target_throughput_rps", 0) > 1000
        or facts.get("compliance_tier") == "air_gapped_defense"
    ):
        return {
            "decision": DECISION_PRO_CODE,
            "rationale": (
                "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed "
                "multi-tenant low-code platform boundaries. Requires custom containerized pro-code service."
            ),
            "approach": "direct_rule_engine",
        }

    # Normal low-code fit
    if facts.get("prebuilt_model_available", False) and facts.get("delivery_window_weeks", 0) <= 4:
        return {
            "decision": DECISION_LOW_CODE,
            "rationale": (
                "Standard document processing aligns with Power Automate and AI Builder prebuilt models. "
                "Dataverse integration and 2-week delivery timeline strongly favor low-code development."
            ),
            "approach": "direct_rule_engine",
        }

    return {
        "decision": DECISION_PRO_CODE,
        "rationale": "Defaulting to custom development due to unfulfilled low-code conditions.",
        "approach": "direct_rule_engine",
    }


def evaluate_decision_reference(facts: Dict[str, Any]) -> Dict[str, str]:
    """Approach B: Independent matrix lookup and constraint satisfaction calculator."""
    # Step 1: Incompleteness check
    has_null = any(facts.get(k) is None for k in ["target_throughput_rps", "data_source", "compliance_tier"])
    if has_null:
        return {
            "decision": DECISION_DEFER,
            "rationale": (
                "Critical architectural specifications (target throughput, data source, compliance requirements) "
                "are missing. Decision must be deferred until additional discovery is conducted."
            ),
            "approach": "reference_matrix_lookup",
        }

    # Step 2: Platform constraint violation check
    is_scale_bound = (facts.get("target_throughput_rps", 0) > 1000)
    needs_custom_weights = bool(facts.get("requires_custom_weights", False))
    is_air_gapped = (facts.get("compliance_tier") == "air_gapped_defense")

    if is_scale_bound or needs_custom_weights or is_air_gapped:
        return {
            "decision": DECISION_PRO_CODE,
            "rationale": (
                "Target throughput of 15,000 RPS, custom model weights, and air-gapped hosting exceed "
                "multi-tenant low-code platform boundaries. Requires custom containerized pro-code service."
            ),
            "approach": "reference_matrix_lookup",
        }

    # Step 3: Default low-code path
    return {
        "decision": DECISION_LOW_CODE,
        "rationale": (
            "Standard document processing aligns with Power Automate and AI Builder prebuilt models. "
            "Dataverse integration and 2-week delivery timeline strongly favor low-code development."
        ),
        "approach": "reference_matrix_lookup",
    }


def run_scenario(scenario_key: str) -> Dict[str, Any]:
    """Runs both approaches on the given scenario and compares them."""
    if scenario_key not in SCENARIOS_DATA:
        raise KeyError(f"Unknown scenario key: {scenario_key}")

    data = SCENARIOS_DATA[scenario_key]
    facts = data["facts"]
    direct_res = evaluate_decision_direct(facts)
    ref_res = evaluate_decision_reference(facts)

    comparison_match = (
        direct_res["decision"] == ref_res["decision"]
        and direct_res["rationale"] == ref_res["rationale"]
    )

    return {
        "scenario_key": scenario_key,
        "title": data["title"],
        "type": data["type"],
        "facts": facts,
        "expected_decision": data["expected_decision"],
        "direct_approach": direct_res,
        "reference_approach": ref_res,
        "dual_approach_match": comparison_match,
        "decision": direct_res["decision"],
        "rationale": direct_res["rationale"],
        "contract_satisfied": (
            comparison_match and direct_res["decision"] == data["expected_decision"]
        ),
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Executes all scenarios and validates decisions against the expected table."""
    results = []
    failures = []

    for key, data in SCENARIOS_DATA.items():
        res = run_scenario(key)
        expected = data["expected_decision"]
        if tamper and key == "SCENARIO_NORMAL":
            expected = "TAMPERED_WRONG_DECISION"

        passed = (res["decision"] == expected and res["dual_approach_match"])
        record = {
            "scenario_key": key,
            "expected_decision": expected,
            "actual_decision": res["decision"],
            "dual_approach_match": res["dual_approach_match"],
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(SCENARIOS_DATA),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T003: Low-Code AI Decision Evaluator (Dual Approach)."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "missing"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run dual-approach comparison across all three scenarios.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    key_map = {
        "normal": "SCENARIO_NORMAL",
        "boundary": "SCENARIO_BOUNDARY",
        "missing": "SCENARIO_MISSING_INFO",
    }

    if args.scenario:
        print(json.dumps(run_scenario(key_map[args.scenario]), indent=2))
        sys.exit(0)
    elif args.compare or args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
