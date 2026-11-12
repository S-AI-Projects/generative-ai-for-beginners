"""Educational startup three-scenario worked example, checker & recovery lab (Lesson 01).

Illustrates "Scenario: our educational startup" from 01-introduction-to-genai/README.md:
- Three worked scenarios (`normal`, `boundary`, `missing_info`) each represented by
  `input_facts`, an explicit expected `decision`, and a Lesson 01 `rationale`.
- A deterministic decision-table checker (`check_decision_table` / `assert_decision_table`)
  that fails loudly whenever an expected decision is deliberately altered.
- A stateful `StartupSessionProcessor` and `run_error_and_recovery_sequence` demonstrating
  explicit error explanation on invalid/missing data and clean recovery on the next valid input.

Purely local simulation: standard library only; no model download, paid provider, GPU, or
physical device is required.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any, Mapping, Sequence

REQUIRED_FACT_FIELDS: tuple[str, ...] = (
    "learner_level",
    "learning_goal",
    "prompt",
    "prompt_tokens",
    "max_window_tokens",
    "teacher_review_gate",
)

DECISION_TABLE: tuple[dict[str, str], ...] = (
    {
        "rule_id": "M1",
        "condition": "Any required input fact is None or blank string.",
        "decision": "halt_and_explain_missing_data",
    },
    {
        "rule_id": "B1",
        "condition": "prompt_tokens >= max_window_tokens (reaches or exceeds n-token limit).",
        "decision": "shorten_or_split_prompt",
    },
    {
        "rule_id": "R1",
        "condition": "teacher_review_gate is False (no human oversight before student use).",
        "decision": "route_to_teacher_review",
    },
    {
        "rule_id": "N1",
        "condition": "All facts present, prompt_tokens < max_window_tokens, teacher_review_gate is True.",
        "decision": "serve_tutor_first_draft",
    },
)

WORKED_SCENARIOS: dict[str, dict[str, Any]] = {
    "normal": {
        "scenario_id": "normal",
        "title": "Normal scenario: 24/7 virtual tutor draft with teacher review gate",
        "input_facts": {
            "learner_level": "middle_school",
            "learning_goal": "virtual_tutor_qa",
            "prompt": "Explain why seasons change using two everyday observations.",
            "prompt_tokens": 24,
            "max_window_tokens": 256,
            "teacher_review_gate": True,
        },
        "expected_decision": "serve_tutor_first_draft",
        "rationale": (
            "Lesson 01 sets our startup's mission around accessible, personalized learning with "
            "virtual tutors responding to natural-language prompts. Because prompt_tokens (24) "
            "fits inside max_window_tokens (256) and teacher_review_gate is True to inspect "
            "non-deterministic first-draft output, serving a tutor first draft is approved."
        ),
    },
    "boundary": {
        "scenario_id": "boundary",
        "title": "Boundary scenario: prompt reaches exact n-token window ceiling (256 == 256)",
        "input_facts": {
            "learner_level": "high_school",
            "learning_goal": "code_explanation",
            "prompt": "Explain every line of this recursion helper at the exact 256-token limit.",
            "prompt_tokens": 256,
            "max_window_tokens": 256,
            "teacher_review_gate": True,
        },
        "expected_decision": "shorten_or_split_prompt",
        "rationale": (
            "Lesson 01 explains that an LLM accepts n tokens and predicts output tokens one by one "
            "in an expanding window, sometimes stopping mid-sentence when context fills up. At "
            "the exact boundary prompt_tokens == max_window_tokens (256), zero window headroom "
            "remains for generated output tokens, so the prompt must be shortened or split."
        ),
    },
    "missing_info": {
        "scenario_id": "missing_info",
        "title": "Missing-information scenario: omitted learner level, empty prompt, and missing count",
        "input_facts": {
            "learner_level": None,
            "learning_goal": "quiz_drafting",
            "prompt": "",
            "prompt_tokens": None,
            "max_window_tokens": 256,
            "teacher_review_gate": True,
        },
        "expected_decision": "halt_and_explain_missing_data",
        "rationale": (
            "Lesson 01 defines the prompt as the natural-language instruction needed before any "
            "completion can be generated and warns against ungrounded fabrications. With "
            "learner_level, prompt, and prompt_tokens missing, the startup must halt, explain "
            "which fields are absent, and wait for a valid follow-up request."
        ),
    },
}


def detect_missing_fields(facts: Mapping[str, Any]) -> list[str]:
    """Return ordered required field names that are absent, None, or blank."""
    missing: list[str] = []
    for field in REQUIRED_FACT_FIELDS:
        if field not in facts or facts[field] is None:
            missing.append(field)
            continue
        val = facts[field]
        if isinstance(val, str) and not val.strip():
            missing.append(field)
    return missing


def evaluate_startup_rules(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministically evaluate DECISION_TABLE using input_facts only."""
    if not isinstance(facts, Mapping):
        raise ValueError("input_facts must be a mapping")

    missing = detect_missing_fields(facts)
    if missing:
        return {
            "rule_id": "M1",
            "decision": "halt_and_explain_missing_data",
            "missing_fields": missing,
            "error_explanation": (
                f"Cannot evaluate tutor request: missing or blank required field(s): {', '.join(missing)}."
            ),
            "remediation_hint": (
                "Provide non-empty strings for 'learner_level', 'learning_goal', and 'prompt', "
                "integer token counts, and boolean 'teacher_review_gate'."
            ),
        }

    prompt_tokens = facts["prompt_tokens"]
    max_window_tokens = facts["max_window_tokens"]
    if (
        not isinstance(prompt_tokens, int)
        or isinstance(prompt_tokens, bool)
        or prompt_tokens < 0
    ):
        raise ValueError("'prompt_tokens' must be a non-negative integer")
    if (
        not isinstance(max_window_tokens, int)
        or isinstance(max_window_tokens, bool)
        or max_window_tokens <= 0
    ):
        raise ValueError("'max_window_tokens' must be a positive integer")

    teacher_review_gate = facts["teacher_review_gate"]
    if not isinstance(teacher_review_gate, bool):
        raise ValueError("'teacher_review_gate' must be a boolean")

    if prompt_tokens >= max_window_tokens:
        return {
            "rule_id": "B1",
            "decision": "shorten_or_split_prompt",
            "missing_fields": [],
            "error_explanation": None,
            "remediation_hint": (
                f"Reduce prompt_tokens ({prompt_tokens}) below max_window_tokens ({max_window_tokens}) "
                "to leave room in the expanding token window."
            ),
        }

    if not teacher_review_gate:
        return {
            "rule_id": "R1",
            "decision": "route_to_teacher_review",
            "missing_fields": [],
            "error_explanation": None,
            "remediation_hint": "Enable teacher_review_gate before delivering AI drafts to learners.",
        }

    return {
        "rule_id": "N1",
        "decision": "serve_tutor_first_draft",
        "missing_fields": [],
        "error_explanation": None,
        "remediation_hint": None,
    }


def check_decision_table(
    scenarios: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare each published scenario's expected decision against evaluate_startup_rules."""
    target = WORKED_SCENARIOS if scenarios is None else scenarios
    if not target:
        raise ValueError("scenarios mapping cannot be empty")

    results: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    for scenario_id, entry in target.items():
        facts = entry.get("input_facts")
        expected = entry.get("expected_decision")
        rationale = str(entry.get("rationale", "")).strip()
        if not rationale:
            raise ValueError(f"Scenario '{scenario_id}' must include a non-empty lesson rationale")

        evaluated = evaluate_startup_rules(facts)
        actual = evaluated["decision"]
        passed = actual == expected

        results.append(
            {
                "scenario_id": scenario_id,
                "title": entry.get("title", scenario_id),
                "input_facts": dict(facts),
                "expected_decision": expected,
                "actual_decision": actual,
                "rule_id": evaluated["rule_id"],
                "error_explanation": evaluated["error_explanation"],
                "remediation_hint": evaluated["remediation_hint"],
                "rationale": rationale,
                "passed": passed,
            }
        )
        if not passed:
            mismatches.append(
                {
                    "scenario_id": scenario_id,
                    "expected_decision": expected,
                    "actual_decision": actual,
                }
            )

    return {
        "simulation": True,
        "checked_count": len(results),
        "all_passed": len(mismatches) == 0,
        "mismatches": mismatches,
        "results": results,
    }


def assert_decision_table(
    scenarios: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run check_decision_table and raise AssertionError if any scenario mismatches."""
    report = check_decision_table(scenarios)
    if not report["all_passed"]:
        summary = "; ".join(
            f"{m['scenario_id']}: expected '{m['expected_decision']}' != actual '{m['actual_decision']}'"
            for m in report["mismatches"]
        )
        raise AssertionError(f"Decision-table mismatch: {summary}")
    return report


class StartupSessionProcessor:
    """Processes sequential requests, explaining errors and recovering cleanly on valid input."""

    def __init__(self) -> None:
        self.error_count = 0
        self.recovered_count = 0
        self.last_had_error = False
        self.history: list[dict[str, Any]] = []

    def process(self, step_name: str, facts: Mapping[str, Any]) -> dict[str, Any]:
        try:
            evaluated = evaluate_startup_rules(facts)
        except ValueError as exc:
            self.error_count += 1
            self.last_had_error = True
            record = {
                "step": step_name,
                "status": "invalid_input_error_explained",
                "decision": "reject_invalid_input",
                "error_explanation": f"Invalid input fact rejected cleanly: {exc}",
                "recovered_after_prior_error": False,
            }
            self.history.append(record)
            return record

        if evaluated["decision"] == "halt_and_explain_missing_data":
            self.error_count += 1
            self.last_had_error = True
            record = {
                "step": step_name,
                "status": "missing_data_error_explained",
                "decision": evaluated["decision"],
                "error_explanation": evaluated["error_explanation"],
                "remediation_hint": evaluated["remediation_hint"],
                "recovered_after_prior_error": False,
            }
            self.history.append(record)
            return record

        recovered = self.last_had_error
        if recovered:
            self.recovered_count += 1
        self.last_had_error = False
        record = {
            "step": step_name,
            "status": "recovered_valid_ok" if recovered else "valid_ok",
            "decision": evaluated["decision"],
            "rule_id": evaluated["rule_id"],
            "error_explanation": None,
            "recovered_after_prior_error": recovered,
        }
        self.history.append(record)
        return record


def run_error_and_recovery_sequence() -> dict[str, Any]:
    """Exercise documented missing/invalid inputs, explain errors, and recover on valid input."""
    processor = StartupSessionProcessor()
    step_missing = processor.process(
        "step_1_missing_info", WORKED_SCENARIOS["missing_info"]["input_facts"]
    )
    step_invalid = processor.process(
        "step_2_negative_tokens",
        {
            **WORKED_SCENARIOS["normal"]["input_facts"],
            "prompt_tokens": -5,
        },
    )
    step_recovered = processor.process(
        "step_3_valid_recovery", WORKED_SCENARIOS["normal"]["input_facts"]
    )

    return {
        "simulation": True,
        "error_count": processor.error_count,
        "recovered_count": processor.recovered_count,
        "final_status": step_recovered["status"],
        "final_decision": step_recovered["decision"],
        "steps": [step_missing, step_invalid, step_recovered],
    }


def build_tampered_table(
    scenario_id: str = "normal",
    wrong_decision: str = "shorten_or_split_prompt",
) -> dict[str, dict[str, Any]]:
    """Return a copy of WORKED_SCENARIOS with one expected decision changed."""
    if scenario_id not in WORKED_SCENARIOS:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")
    copy_table = copy.deepcopy(WORKED_SCENARIOS)
    copy_table[scenario_id]["expected_decision"] = wrong_decision
    return copy_table


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Lesson 01 three-scenario decision-table checker and error/recovery demo."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("all", "normal", "boundary", "missing_info", "recovery", "tamper"),
        default="all",
        help="Scenario or verification mode to run (default: all)",
    )
    args = parser.parse_args(argv)

    if args.mode in WORKED_SCENARIOS:
        payload = check_decision_table({args.mode: WORKED_SCENARIOS[args.mode]})
        print(json.dumps(payload, indent=2))
        return 0 if payload["all_passed"] else 1

    if args.mode == "recovery":
        payload = run_error_and_recovery_sequence()
        print(json.dumps(payload, indent=2))
        return 0 if payload["final_status"] == "recovered_valid_ok" else 1

    if args.mode == "tamper":
        payload = check_decision_table(build_tampered_table("normal", "shorten_or_split_prompt"))
        print(json.dumps(payload, indent=2))
        return 0 if payload["all_passed"] else 1

    table_report = check_decision_table(WORKED_SCENARIOS)
    recovery_report = run_error_and_recovery_sequence()
    payload = {
        "simulation": True,
        "decision_table_check": table_report,
        "error_and_recovery_demo": recovery_report,
    }
    print(json.dumps(payload, indent=2))
    return 0 if (table_report["all_passed"] and recovery_report["recovered_count"] == 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
