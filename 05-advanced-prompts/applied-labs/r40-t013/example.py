
import argparse
import json
import re
import sys


TEMPLATE = "Hello {{name}}. Explain {{topic}} clearly."
ALLOWED_KEYS = {"name", "topic"}
PLACEHOLDER = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")


def validate(template, values):
    if not isinstance(values, dict):
        raise ValueError("Values must be a dictionary.")

    missing = ALLOWED_KEYS - set(values)
    unknown = set(values) - ALLOWED_KEYS

    if missing:
        raise ValueError("Missing keys: " + ", ".join(sorted(missing)))

    if unknown:
        raise ValueError("Unknown keys: " + ", ".join(sorted(unknown)))

    if not all(isinstance(value, str) for value in values.values()):
        raise ValueError("All values must be strings.")

    found = set(PLACEHOLDER.findall(template))

    if found != ALLOWED_KEYS:
        raise ValueError("Template placeholders do not match declared keys.")

    return values


# Approach A: Replace placeholders using a regular expression.
def render_regex(template, values):
    validate(template, values)
    return PLACEHOLDER.sub(
        lambda match: values[match.group(1)],
        template
    )


# Approach B: Scan the template from left to right.
def render_scan(template, values):
    validate(template, values)

    output = []
    position = 0

    while position < len(template):
        match = PLACEHOLDER.search(template, position)

        if match is None:
            output.append(template[position:])
            break

        output.append(template[position:match.start()])
        output.append(values[match.group(1)])
        position = match.end()

    return "".join(output)


SCENARIOS = {
    "normal": {
        "values": {"name": "Asha", "topic": "Photosynthesis"},
        "expected": "Hello Asha. Explain Photosynthesis clearly."
    },
    "boundary": {
        "values": {
            "name": "Asha {{admin}}",
            "topic": "Maths {advanced}"
        },
        "expected": "Hello Asha {{admin}}. Explain Maths {advanced} clearly."
    }
}


def check_expected(actual, expected):
    if actual != expected:
        raise AssertionError(
            "Expected {!r}, got {!r}".format(expected, actual)
        )


def run_scenario(name):
    if name not in SCENARIOS:
        raise ValueError("Unknown scenario: " + name)

    fixture = SCENARIOS[name]
    first = render_regex(TEMPLATE, fixture["values"])
    second = render_scan(TEMPLATE, fixture["values"])

    check_expected(first, fixture["expected"])
    check_expected(second, fixture["expected"])

    return {
        "scenario": name,
        "input": fixture["values"],
        "regex_result": first,
        "scan_result": second,
        "expected": fixture["expected"],
        "approaches_match": first == second
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=("normal", "boundary", "missing", "unknown")
    )
    args = parser.parse_args()

    try:
        if args.scenario in ("missing", "unknown"):
            values = (
                {"name": "Asha"}
                if args.scenario == "missing"
                else {"name": "Asha", "topic": "Maths", "extra": "value"}
            )
            render_regex(TEMPLATE, values)
            raise AssertionError("Invalid input was unexpectedly accepted.")

        names = [args.scenario] if args.scenario else list(SCENARIOS)
        results = [run_scenario(name) for name in names]

        print(json.dumps({"results": results}, indent=2))
        return 0

    except (ValueError, AssertionError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

