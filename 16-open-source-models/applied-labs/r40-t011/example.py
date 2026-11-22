"""Local teaching example for the open-model checklist in lesson 16."""

import argparse
import json
import sys


REQUIRED_FIELDS = (
    "training_datasets",
    "full_model_weights",
    "evaluation_code",
    "fine_tuning_code",
    "training_metrics",
)

SCENARIOS = {
    "normal": {
        "input_facts": {
            "training_datasets": True,
            "full_model_weights": True,
            "evaluation_code": True,
            "fine_tuning_code": True,
            "training_metrics": True,
        },
        "expected_decision": "meets_checklist",
        "rationale": (
            "All five information categories described in the lesson "
            "are publicly available in this teaching fixture."
        ),
    },
    "boundary": {
        "input_facts": {
            "training_datasets": True,
            "full_model_weights": True,
            "evaluation_code": True,
            "fine_tuning_code": True,
            "training_metrics": False,
        },
        "expected_decision": "does_not_meet_checklist",
        "rationale": (
            "Four categories are available, but training metrics are not. "
            "The complete lesson checklist is therefore not satisfied."
        ),
    },
    "missing": {
        "input_facts": {
            "training_datasets": True,
            "full_model_weights": True,
            "evaluation_code": True,
            "fine_tuning_code": True,
            "training_metrics": None,
        },
        "expected_decision": "cannot_determine",
        "rationale": (
            "Training-metrics information is unknown, not confirmed absent. "
            "There is insufficient information to decide whether the "
            "complete checklist is satisfied."
        ),
    },
}


def decide(input_facts):
    """Apply the lesson's five-category checklist."""
    if set(input_facts) != set(REQUIRED_FIELDS):
        raise ValueError("Input must contain exactly the five required fields.")

    values = [input_facts[field] for field in REQUIRED_FIELDS]

    if any(value not in (True, False, None) for value in values):
        raise ValueError("Each fact must be True, False, or None.")

    if any(value is None for value in values):
        return "cannot_determine"

    if all(value is True for value in values):
        return "meets_checklist"

    return "does_not_meet_checklist"


def run_scenario(name):
    """Return the input, calculated decision, and teaching rationale."""
    if name not in SCENARIOS:
        raise ValueError("Unknown scenario: " + name)

    fixture = SCENARIOS[name]
    return {
        "scenario": name,
        "input_facts": fixture["input_facts"],
        "decision": decide(fixture["input_facts"]),
        "expected_decision": fixture["expected_decision"],
        "rationale": fixture["rationale"],
    }


def check_published_decision(name, published_decision):
    """Fail if a published decision disagrees with the calculated result."""
    actual = decide(SCENARIOS[name]["input_facts"])

    if published_decision != actual:
        raise AssertionError(
            "{}: expected {!r}, received {!r}".format(
                name, actual, published_decision
            )
        )

    return True


def check_all():
    """Check every published scenario decision."""
    for name, fixture in SCENARIOS.items():
        check_published_decision(name, fixture["expected_decision"])
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run the local open-model checklist example."
    )
    parser.add_argument(
        "--scenario",
        choices=tuple(SCENARIOS),
        help="Run one scenario. Omit to run all three.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check all published decisions against calculated decisions.",
    )
    args = parser.parse_args()

    try:
        results = (
            [run_scenario(args.scenario)]
            if args.scenario
            else [run_scenario(name) for name in SCENARIOS]
        )

        if args.check:
            check_all()

        output = {
            "simulation": True,
            "results": results,
            "checks_passed": args.check,
        }
        print(json.dumps(output, indent=2))
    except (ValueError, AssertionError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
