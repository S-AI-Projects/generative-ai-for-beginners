import argparse
import json
import sys

REQUIRED_FIELDS = ("learner_level", "topic", "learning_goal")
ALL_FIELDS = REQUIRED_FIELDS + ("output_format",)

SCENARIOS = {
    "normal": {
        "input_facts": {
            "learner_level": "Grade 9",
            "topic": "Photosynthesis",
            "learning_goal": "Explain how plants make food",
            "output_format": "A simple explanation with examples",
        },
        "expected_decision": "ready",
        "rationale": "All required fields and the optional format are provided.",
    },
    "boundary": {
        "input_facts": {
            "learner_level": "Grade 9",
            "topic": "Photosynthesis",
            "learning_goal": "Explain how plants make food",
            "output_format": None,
        },
        "expected_decision": "minimum_ready",
        "rationale": "All three required fields are present. Output format is optional.",
    },
    "missing": {
        "input_facts": {
            "learner_level": "Grade 9",
            "topic": "Photosynthesis",
            "learning_goal": None,
            "output_format": "A short explanation",
        },
        "expected_decision": "cannot_determine",
        "rationale": "The learning goal is unknown.",
    },
    "invalid": {
        "input_facts": {
            "learner_level": "Grade 9",
            "topic": "   ",
            "learning_goal": "Explain how plants make food",
            "output_format": "A short explanation",
        },
        "expected_decision": "invalid",
        "rationale": "The required topic field is blank.",
    },
}


def decide(input_facts):
    if not isinstance(input_facts, dict) or set(input_facts) != set(ALL_FIELDS):
        raise ValueError("Input must contain exactly the four defined fields.")

    for value in input_facts.values():
        if value is not None and not isinstance(value, str):
            raise ValueError("Each field must contain text or None.")

    if any(
        isinstance(input_facts[field], str)
        and not input_facts[field].strip()
        for field in REQUIRED_FIELDS
    ):
        return "invalid"

    if any(input_facts[field] is None for field in REQUIRED_FIELDS):
        return "cannot_determine"

    if input_facts["output_format"] is None:
        return "minimum_ready"

    if isinstance(input_facts["output_format"], str) and not input_facts["output_format"].strip():
        return "ready"

    return "ready"


def run_scenario(name):
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
    actual = decide(SCENARIOS[name]["input_facts"])
    if published_decision != actual:
        raise AssertionError(
            "{}: expected {!r}, received {!r}".format(
                name, actual, published_decision
            )
        )
    return True


def check_all():
    for name, fixture in SCENARIOS.items():
        check_published_decision(name, fixture["expected_decision"])
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Educational startup prompt-readiness simulation."
    )
    parser.add_argument("--scenario", choices=tuple(SCENARIOS))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        names = [args.scenario] if args.scenario else list(SCENARIOS)
        results = [run_scenario(name) for name in names]

        if args.check:
            check_all()

        print(json.dumps({
            "simulation": True,
            "results": results,
            "checks_passed": args.check,
        }, indent=2))
    except (ValueError, AssertionError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
