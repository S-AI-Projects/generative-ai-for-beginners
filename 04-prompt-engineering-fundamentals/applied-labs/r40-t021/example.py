"""R40-T021: Prompt Template Escaping and Safe Variable Rendering.

Demonstrates safe variable substitution in prompt templates, strict key validation,
instruction/data boundary separation, and preserving literal curly braces in user data.

Lesson Reference:
04-prompt-engineering-fundamentals (Prompt Templates and Separating Instructions & Context).
"""

import argparse
import json
import re
import sys
from typing import Any, Dict, Optional, Set

# Fixed instruction defining tutor task behavior
FIXED_INSTRUCTION = (
    "You are an AI educational tutor assisting students with customized study plans."
)

# Template with explicit delimiters separating instruction from user data
DEFAULT_TEMPLATE = (
    "### INSTRUCTION\n"
    f"{FIXED_INSTRUCTION}\n\n"
    "### CONTEXT (USER DATA)\n"
    "- Student Name: {name}\n"
    "- Topic: {topic}"
)

# Declared schema of variables required by the template
DECLARED_VARIABLES = frozenset({"name", "topic"})


def validate_variables(
    variables: Dict[str, Any],
    declared: Set[str] = DECLARED_VARIABLES,
) -> None:
    """Validate that provided variables match the declared schema exactly.

    Rejects missing variables and unknown variables.
    """
    if not isinstance(variables, dict):
        raise TypeError(
            f"Variables must be provided as a dictionary, got {type(variables).__name__}."
        )

    provided_keys = set(variables.keys())
    missing = set(declared) - provided_keys
    if missing:
        missing_sorted = sorted(missing)
        raise ValueError(
            f"Missing required template variable(s): {', '.join(repr(k) for k in missing_sorted)}"
        )

    unknown = provided_keys - set(declared)
    if unknown:
        unknown_sorted = sorted(unknown)
        raise ValueError(
            f"Unknown variable(s) provided: {', '.join(repr(k) for k in unknown_sorted)}"
        )

    for key, value in variables.items():
        if not isinstance(value, str):
            raise TypeError(
                f"Variable '{key}' must be a string, got {type(value).__name__}."
            )


def render_prompt(
    variables: Dict[str, str],
    template: str = DEFAULT_TEMPLATE,
    declared: Set[str] = DECLARED_VARIABLES,
) -> str:
    """Render prompt template with supplied variables safely.

    1. Validates supplied keys against declared variables.
    2. Performs single-pass substitution for placeholders matching declared variables.
    3. Leaves curly braces within user data literal (no recursive interpolation).
    4. Separates fixed instruction fields from dynamic user context using delimiters.

    IMPORTANT SAFETY NOTE:
    Templating and structural delimiters ensure syntax validity and clear boundaries,
    but templating alone does NOT prevent semantic prompt injection. Downstream LLMs
    still parse user text semantically.
    """
    validate_variables(variables, declared=declared)

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            return variables[var_name]
        return match.group(0)

    # Single-pass substitution replaces {name} and {topic} directly
    rendered = re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template)
    return rendered


def main() -> None:
    """CLI entrypoint for rendering templates and demonstrating validation."""
    parser = argparse.ArgumentParser(
        description="Safe prompt template rendering with variable validation and escaping."
    )
    parser.add_argument("--name", help="Student name")
    parser.add_argument("--topic", help="Study topic")
    parser.add_argument(
        "--data",
        help="JSON string containing template variables (e.g. '{\"name\": \"Alice\", \"topic\": \"Math\"}')",
    )

    args = parser.parse_args()

    try:
        if args.data is not None:
            raw_vars = json.loads(args.data)
            if not isinstance(raw_vars, dict):
                raise TypeError("JSON data must be an object/dictionary.")
            variables = raw_vars
        elif args.name is not None or args.topic is not None:
            variables = {}
            if args.name is not None:
                variables["name"] = args.name
            if args.topic is not None:
                variables["topic"] = args.topic
        else:
            # Default fixture demonstration
            variables = {"name": "Alice", "topic": "Photosynthesis"}

        rendered = render_prompt(variables)
        print(json.dumps({"rendered_prompt": rendered}, indent=2))
    except Exception as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
