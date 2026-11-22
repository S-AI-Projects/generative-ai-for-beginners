
import argparse
import json
import string
import sys
from typing import Callable

TEMPLATE = (
    "Fixed instruction: Explain the topic '{topic}' clearly to {name}."
)

DECLARED_VARIABLES = {"name", "topic"}


def render_template(template, values):
    if not isinstance(values, dict):
        raise ValueError("Values must be a dictionary.")

    supplied = set(values)

    missing = DECLARED_VARIABLES - supplied
    unknown = supplied - DECLARED_VARIABLES

    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    if unknown:
        raise ValueError(f"Unknown keys: {sorted(unknown)}")

    for key, value in values.items():
        if not isinstance(value, str):
            raise ValueError(f"Value for {key} must be a string.")

    fields = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(template)
        if field_name is not None
    }

    if fields != DECLARED_VARIABLES:
        raise ValueError("Template fields do not match declared variables.")

    # Values are inserted once. Braces inside values remain literal.
    return template.format_map(values)


# A service is any callable that accepts a prompt and returns text.
PromptService = Callable[[str], str]


class LocalServiceAdapter:
    """Deterministic mock; this does not call a real AI service."""

    def __call__(self, prompt):
        return f"LOCAL MOCK RESPONSE: {prompt}"


def run_prompt(template, values, service):
    rendered_prompt = render_template(template, values)
    response = service(rendered_prompt)

    return {
        "rendered_prompt": rendered_prompt,
        "service_response": response,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "failure"],
        default="normal",
    )
    args = parser.parse_args()

    if args.scenario == "normal":
        values = {"name": "Asha", "topic": "fractions"}
    elif args.scenario == "boundary":
        values = {
            "name": "Asha {admin}",
            "topic": "fractions {level}",
        }
    else:
        values = {"name": "Asha"}

    try:
        result = run_prompt(
            TEMPLATE,
            values,
            LocalServiceAdapter(),
        )
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

