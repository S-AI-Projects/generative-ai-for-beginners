"""Local demonstration of an allowlisted action policy."""

import argparse
import json


POLICY = {
    "read": {
        "required": {"path"},
        "allowed": {"path"},
        "types": {"path": str},
    }
}

FIXTURES = {
    "normal": {"tool": "read", "arguments": {"path": "notes.txt"}},
    "boundary": {"tool": "delete", "arguments": {"path": "notes.txt"}},
    "failure": {"tool": "read", "arguments": {}},
}


def mock_executor(tool, arguments):
    """Return a mock result without accessing real files."""
    return f"MOCK {tool.upper()}: {arguments['path']}"


def baseline_process(action, executor):
    """Baseline: validation and execution in one function."""
    tool = action.get("tool")
    arguments = action.get("arguments")

    if tool not in POLICY:
        return {"allowed": False, "reason": "Unknown tool"}

    if not isinstance(arguments, dict):
        return {"allowed": False, "reason": "Arguments must be a dictionary"}

    schema = POLICY[tool]
    missing = schema["required"] - arguments.keys()

    if missing:
        return {
            "allowed": False,
            "reason": f"Missing required arguments: {sorted(missing)}",
        }

    unknown = arguments.keys() - schema["allowed"]

    if unknown:
        return {
            "allowed": False,
            "reason": f"Unknown arguments: {sorted(unknown)}",
        }

    for name, expected_type in schema["types"].items():
        if not isinstance(arguments[name], expected_type):
            return {
                "allowed": False,
                "reason": f"Argument '{name}' must be a string",
            }

    if not arguments["path"].strip():
        return {"allowed": False, "reason": "Path must not be empty"}

    return {
        "allowed": True,
        "reason": "Allowed",
        "result": executor(tool, arguments),
    }


def validate_action(action, policy):
    """Extracted responsibility: validate before execution."""
    if not isinstance(action, dict):
        return {"allowed": False, "reason": "Action must be a dictionary"}

    tool = action.get("tool")
    arguments = action.get("arguments")

    if tool not in policy:
        return {"allowed": False, "reason": "Unknown tool"}

    if not isinstance(arguments, dict):
        return {"allowed": False, "reason": "Arguments must be a dictionary"}

    schema = policy[tool]
    missing = schema["required"] - arguments.keys()

    if missing:
        return {
            "allowed": False,
            "reason": f"Missing required arguments: {sorted(missing)}",
        }

    unknown = arguments.keys() - schema["allowed"]

    if unknown:
        return {
            "allowed": False,
            "reason": f"Unknown arguments: {sorted(unknown)}",
        }

    for name, expected_type in schema["types"].items():
        if not isinstance(arguments[name], expected_type):
            return {
                "allowed": False,
                "reason": f"Argument '{name}' must be a string",
            }

    if not arguments["path"].strip():
        return {"allowed": False, "reason": "Path must not be empty"}

    return {"allowed": True, "reason": "Allowed"}


def refactored_process(action, executor):
    """Validate first; execute only when validation succeeds."""
    decision = validate_action(action, POLICY)

    if not decision["allowed"]:
        return decision

    return {
        "allowed": True,
        "reason": "Allowed",
        "result": executor(action["tool"], action["arguments"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=("normal", "boundary", "failure"),
        default="normal",
    )
    args = parser.parse_args()

    result = refactored_process(FIXTURES[args.scenario], mock_executor)
    print(json.dumps(result, indent=2))

    if args.scenario == "failure" and not result["allowed"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
