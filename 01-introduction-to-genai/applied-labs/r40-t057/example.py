"""Educational startup three-scenario worked example & decision-table checker (Lesson 01).

Illustrates "Scenario: our educational startup" from 01-introduction-to-genai/README.md
by representing normal, boundary, and missing-information cases as structured input facts,
a deterministic decision rule table, and a rationale tied to Lesson 01 concepts (natural-
language prompts, token window limit n, non-determinism, and first-draft limitations).

Purely local simulation: uses standard library only and calls no real LLM, tokenizer,
cloud service, GPU, or physical device.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any, Mapping, Sequence

REQUIRED_FACT_FIELDS: tuple[str, ...] = (
    "role",
    "task_type",
    "prompt_text",
    "estimated_tokens",
    "max_input_tokens",
    "human_review_enabled",
)

PUBLISHED_DECISION_TABLE: tuple[dict[str, str], ...] = (
    {
        "rule_id": "R1",
        "condition": "Any required input fact is missing or empty (None or blank string).",
        "decision": "request_missing_information",
    },
    {
        "rule_id": "R2",
        "condition": "estimated_tokens >= max_input_tokens (token-window boundary reached or exceeded).",
        "decision": "chunk_prompt_at_token_limit",
    },
    {
        "rule_id": "R3",
        "condition": "human_review_enabled is False (no teacher/human verification step).",
        "decision": "require_human_review_gate",
    },
    {
        "rule_id": "R4",
        "condition": "All required facts present, estimated_tokens < max_input_tokens, and human_review_enabled is True.",
        "decision": "approve_llm_draft",
    },
)

WORKED_SCENARIOS: dict[str, dict[str, Any]] = {
    "normal": {
        "scenario_id": "normal",
        "title": "Normal scenario: personalized concept explanation with human review",
        "input_facts": {
            "role": "student",
            "task_type": "concept_explanation",
            "prompt_text": "Explain fractions with two everyday visual examples for a 10-year-old.",
            "estimated_tokens": 18,
            "max_input_tokens": 100,
            "human_review_enabled": True,
        },
        "expected_decision": "approve_llm_draft",
        "rationale": (
            "Lesson 01 frames our educational startup around accessible, personalized learning "
            "using natural-language prompts as a strong first draft checked by humans because "
            "LLMs are non-deterministic. All required facts are supplied, estimated_tokens (18) "
            "leaves headroom inside max_input_tokens (100), and human_review_enabled is True."
        ),
        "worked_trace": (
            "R1 (missing info): False (all 6 required facts present); "
            "R2 (token boundary): False (18 < 100); "
            "R3 (no human review): False (human_review_enabled=True); "
            "R4 fires -> approve_llm_draft."
        ),
    },
    "boundary": {
        "scenario_id": "boundary",
        "title": "Boundary scenario: prompt hits exact max_input_tokens limit n",
        "input_facts": {
            "role": "teacher",
            "task_type": "article_summarization",
            "prompt_text": "Summarize this curriculum reading passage at the exact 100-token context limit.",
            "estimated_tokens": 100,
            "max_input_tokens": 100,
            "human_review_enabled": True,
        },
        "expected_decision": "chunk_prompt_at_token_limit",
        "rationale": (
            "Lesson 01 explains that an LLM accepts n tokens and predicts output tokens one by one "
            "in an expanding window, which can stop mid-sentence near the limit. Because "
            "estimated_tokens (100) equals max_input_tokens (100), zero window capacity remains "
            "for generated output tokens, so the teacher prompt must be chunked or shortened first."
        ),
        "worked_trace": (
            "R1 (missing info): False (all 6 required facts present); "
            "R2 (token boundary): True (estimated_tokens 100 >= max_input_tokens 100) -> "
            "chunk_prompt_at_token_limit."
        ),
    },
    "missing_info": {
        "scenario_id": "missing_info",
        "title": "Missing-information scenario: empty prompt and unspecified token/review facts",
        "input_facts": {
            "role": "teacher",
            "task_type": "essay_feedback",
            "prompt_text": "",
            "estimated_tokens": None,
            "max_input_tokens": 100,
            "human_review_enabled": None,
        },
        "expected_decision": "request_missing_information",
        "rationale": (
            "Lesson 01 defines a prompt as the natural-language instruction/input required to "
            "produce a completion and warns that LLM output requires mitigation against fabrications. "
            "With prompt_text empty and estimated_tokens and human_review_enabled omitted, the "
            "startup workflow cannot check token limits or governance safeguards and must request missing facts."
        ),
        "worked_trace": (
            "R1 (missing info): True (missing fields: ['prompt_text', 'estimated_tokens', "
            "'human_review_enabled']) -> request_missing_information."
        ),
    },
}


def find_missing_fact_fields(facts: Mapping[str, Any]) -> list[str]:
    """Return ordered list of required fact fields that are missing or blank."""
    missing: list[str] = []
    for field in REQUIRED_FACT_FIELDS:
        if field not in facts or facts[field] is None:
            missing.append(field)
            continue
        value = facts[field]
        if isinstance(value, str) and not value.strip():
            missing.append(field)
    return missing


def evaluate_decision_table(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate PUBLISHED_DECISION_TABLE using only the supplied input facts."""
    if not isinstance(facts, Mapping):
        raise ValueError("input_facts must be a mapping")

    trace: list[str] = []
    missing_fields = find_missing_fact_fields(facts)
    if missing_fields:
        trace.append(f"R1 matched: missing or blank fields {missing_fields}")
        return {
            "rule_id": "R1",
            "decision": "request_missing_information",
            "missing_fields": missing_fields,
            "trace": trace,
        }
    trace.append("R1 skipped: all required facts present")

    estimated_tokens = facts["estimated_tokens"]
    max_input_tokens = facts["max_input_tokens"]
    if (
        not isinstance(estimated_tokens, int)
        or isinstance(estimated_tokens, bool)
        or estimated_tokens < 0
    ):
        raise ValueError("'estimated_tokens' must be a non-negative integer")
    if (
        not isinstance(max_input_tokens, int)
        or isinstance(max_input_tokens, bool)
        or max_input_tokens <= 0
    ):
        raise ValueError("'max_input_tokens' must be a positive integer")

    if estimated_tokens >= max_input_tokens:
        trace.append(
            f"R2 matched: estimated_tokens ({estimated_tokens}) >= max_input_tokens ({max_input_tokens})"
        )
        return {
            "rule_id": "R2",
            "decision": "chunk_prompt_at_token_limit",
            "missing_fields": [],
            "trace": trace,
        }
    trace.append(
        f"R2 skipped: estimated_tokens ({estimated_tokens}) < max_input_tokens ({max_input_tokens})"
    )

    human_review_enabled = facts["human_review_enabled"]
    if not isinstance(human_review_enabled, bool):
        raise ValueError("'human_review_enabled' must be a boolean when provided")

    if not human_review_enabled:
        trace.append("R3 matched: human_review_enabled is False")
        return {
            "rule_id": "R3",
            "decision": "require_human_review_gate",
            "missing_fields": [],
            "trace": trace,
        }
    trace.append("R3 skipped: human_review_enabled is True")
    trace.append("R4 matched: all guardrails satisfied")
    return {
        "rule_id": "R4",
        "decision": "approve_llm_draft",
        "missing_fields": [],
        "trace": trace,
    }


def check_published_scenarios(
    scenarios: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Verify every published worked scenario matches PUBLISHED_DECISION_TABLE."""
    target = WORKED_SCENARIOS if scenarios is None else scenarios
    if not target:
        raise ValueError("scenarios mapping cannot be empty")

    results: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    for scenario_id, scenario in target.items():
        facts = scenario.get("input_facts")
        expected_decision = scenario.get("expected_decision")
        rationale = str(scenario.get("rationale", "")).strip()
        if not rationale:
            raise ValueError(f"Scenario '{scenario_id}' is missing a lesson rationale")

        evaluation = evaluate_decision_table(facts)
        actual_decision = evaluation["decision"]
        passed = actual_decision == expected_decision

        entry = {
            "scenario_id": scenario_id,
            "title": scenario.get("title", scenario_id),
            "input_facts": dict(facts),
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "rule_id": evaluation["rule_id"],
            "trace": evaluation["trace"],
            "worked_trace": scenario.get("worked_trace", ""),
            "rationale": rationale,
            "passed": passed,
        }
        results.append(entry)
        if not passed:
            mismatches.append(
                {
                    "scenario_id": scenario_id,
                    "expected_decision": expected_decision,
                    "actual_decision": actual_decision,
                }
            )

    return {
        "simulation": True,
        "checked_count": len(results),
        "all_passed": len(mismatches) == 0,
        "mismatches": mismatches,
        "results": results,
    }


def assert_published_scenarios(
    scenarios: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Check published scenarios and raise AssertionError on any decision mismatch."""
    report = check_published_scenarios(scenarios)
    if not report["all_passed"]:
        details = "; ".join(
            f"{m['scenario_id']}: expected '{m['expected_decision']}' != actual '{m['actual_decision']}'"
            for m in report["mismatches"]
        )
        raise AssertionError(f"Decision-table check failed: {details}")
    return report


def build_tampered_scenarios(
    scenario_id: str = "normal",
    wrong_decision: str = "chunk_prompt_at_token_limit",
) -> dict[str, dict[str, Any]]:
    """Return a copy of WORKED_SCENARIOS with one expected decision deliberately altered."""
    if scenario_id not in WORKED_SCENARIOS:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")
    tampered = copy.deepcopy(WORKED_SCENARIOS)
    tampered[scenario_id]["expected_decision"] = wrong_decision
    return tampered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate and check the three worked educational-startup scenarios from Lesson 01."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=("all", *WORKED_SCENARIOS.keys()),
        default="all",
        help="Scenario to run and verify (default: all)",
    )
    parser.add_argument(
        "--tamper-decision",
        metavar="DECISION",
        default=None,
        help="Deliberately replace expected_decision with DECISION to verify failure detection.",
    )
    args = parser.parse_args(argv)

    if args.tamper_decision is not None:
        target_id = "normal" if args.scenario == "all" else args.scenario
        tampered = build_tampered_scenarios(target_id, args.tamper_decision)
        selected = tampered if args.scenario == "all" else {target_id: tampered[target_id]}
    elif args.scenario == "all":
        selected = WORKED_SCENARIOS
    else:
        selected = {args.scenario: WORKED_SCENARIOS[args.scenario]}

    report = check_published_scenarios(selected)
    print(json.dumps(report, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
