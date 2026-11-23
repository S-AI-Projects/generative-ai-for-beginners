"""A local teaching example of allowlisted action validation."""

ALLOWED_ACTIONS = {
    "read": {
        "required": {"path": str},
        "optional": set(),
    }
}


class PolicyError(ValueError):
    """Raised when an action does not satisfy the policy."""


def validate_action(action):
    """Validate an action before it can reach the executor."""
    if not isinstance(action, dict):
        raise PolicyError("Action must be a dictionary")

    if set(action) != {"tool", "arguments"}:
        raise PolicyError("Action must contain only tool and arguments")

    tool = action["tool"]
    arguments = action["arguments"]

    if not isinstance(tool, str) or tool not in ALLOWED_ACTIONS:
        raise PolicyError("Tool is not allowed")

    if not isinstance(arguments, dict):
        raise PolicyError("Arguments must be a dictionary")

    schema = ALLOWED_ACTIONS[tool]
    required = schema["required"]
    optional = schema["optional"]

    missing = set(required) - set(arguments)
    if missing:
        raise PolicyError("Missing required argument: " + ", ".join(sorted(missing)))

    unknown = set(arguments) - set(required) - optional
    if unknown:
        raise PolicyError("Unknown argument: " + ", ".join(sorted(unknown)))

    for name, expected_type in required.items():
        if not isinstance(arguments[name], expected_type):
            raise PolicyError("Argument '" + name + "' must be a string")

        if not arguments[name].strip():
            raise PolicyError("Argument '" + name + "' cannot be empty")

    return tool, arguments


def mock_executor(tool, arguments):
    """Return a simulated result without accessing real files."""
    if tool == "read":
        return "MOCK READ: " + arguments["path"]

    raise RuntimeError("Unexpected tool reached the mock executor")


def run_action(action, executor=mock_executor):
    """Validate first; execute only when the policy allows the action."""
    tool, arguments = validate_action(action)
    return executor(tool, arguments)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Local action-policy demonstration")
    parser.add_argument(
        "scenario",
        choices=["normal", "boundary", "failure"],
        help="Choose a demonstration scenario",
    )
    args = parser.parse_args()

    scenarios = {
        "normal": {
            "tool": "read",
            "arguments": {"path": "notes.txt"},
        },
        "boundary": {
            "tool": "delete",
            "arguments": {"path": "notes.txt"},
        },
        "failure": {
            "tool": "read",
            "arguments": {},
        },
    }

    try:
        result = run_action(scenarios[args.scenario])
        print("ALLOWED:", result)
    except PolicyError as error:
        print("REJECTED:", error)


if __name__ == "__main__":
    main()
