"""Local launch-configuration validator and secret redactor for Lesson 14.

Demonstrates a correct baseline validator alongside a refactored version that
extracts `redact_env_values` as one named responsibility while preserving the
exact contract and proving before/after equivalence on local fixtures.

Purely local simulation: no subprocess is launched, and no network calls,
downloads, paid providers, GPUs, or physical devices are used.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping, Sequence

REDACTED_MARKER = "<REDACTED>"

SYNTHETIC_FIXTURES: dict[str, dict[str, Any]] = {
    "valid": {
        "command": "python3",
        "args": ["-m", "http.server", "8080"],
        "env": {
            "APP_ENV": "local-sim",
            "API_KEY": "synthetic-secret-value",
        },
    },
    "boundary_empty_args_and_env": {
        "command": "uvicorn",
        "args": [],
        "env": {},
    },
    "invalid_missing_command": {
        "args": ["--port", "8080"],
        "env": {"API_KEY": "synthetic-secret-value"},
    },
    "invalid_string_args": {
        "command": "python3",
        "args": "--port 8080",
        "env": {"API_KEY": "synthetic-secret-value"},
    },
}


def _validate_command_and_args(config: Mapping[str, Any]) -> tuple[str, list[str]]:
    if not isinstance(config, Mapping):
        raise ValueError("config must be a mapping")

    command = config.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("Missing or empty 'command'")

    if "args" not in config:
        raise ValueError("Missing 'args' argument array")
    raw_args = config["args"]
    if isinstance(raw_args, (str, bytes)):
        raise ValueError(
            "'args' must be an argument array (list/tuple of strings), "
            "not a single string"
        )
    if not isinstance(raw_args, (list, tuple)):
        raise ValueError("'args' must be an argument array (list/tuple of strings)")

    validated_args: list[str] = []
    for index, arg in enumerate(raw_args):
        if not isinstance(arg, str):
            raise ValueError(f"args[{index}] must be a string")
        validated_args.append(arg)

    return command, validated_args


def validate_launch_config_baseline(config: Mapping[str, Any]) -> dict[str, Any]:
    """Correct baseline implementation before extracting env redaction."""
    command, validated_args = _validate_command_and_args(config)

    if "env" not in config or not isinstance(config["env"], Mapping):
        raise ValueError("'env' must be a mapping of explicit key/value strings")

    redacted_env: dict[str, str] = {}
    for key, value in config["env"].items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Environment variable keys must be non-empty strings")
        if not isinstance(value, str):
            raise ValueError(f"Environment value for '{key}' must be a string")
        redacted_env[key] = REDACTED_MARKER

    return {
        "simulation": True,
        "launched": False,
        "command": command,
        "args": validated_args,
        "env_keys": list(redacted_env.keys()),
        "redacted_env": redacted_env,
    }


def redact_env_values(env: Any) -> dict[str, str]:
    """Extracted named responsibility: validate env keys/values and redact values."""
    if not isinstance(env, Mapping):
        raise ValueError("'env' must be a mapping of explicit key/value strings")

    redacted: dict[str, str] = {}
    for key, value in env.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Environment variable keys must be non-empty strings")
        if not isinstance(value, str):
            raise ValueError(f"Environment value for '{key}' must be a string")
        redacted[key] = REDACTED_MARKER
    return redacted


def validate_launch_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Refactored implementation preserving the exact baseline contract."""
    command, validated_args = _validate_command_and_args(config)
    if "env" not in config:
        raise ValueError("'env' must be a mapping of explicit key/value strings")
    redacted_env = redact_env_values(config["env"])

    return {
        "simulation": True,
        "launched": False,
        "command": command,
        "args": validated_args,
        "env_keys": list(redacted_env.keys()),
        "redacted_env": redacted_env,
    }


def _evaluate_both(config: Mapping[str, Any]) -> dict[str, Any]:
    """Run baseline and refactored implementations and compare contract equivalence."""
    baseline_res: dict[str, Any] | None = None
    baseline_err: str | None = None
    try:
        baseline_res = validate_launch_config_baseline(config)
    except ValueError as exc:
        baseline_err = str(exc)

    refactored_res: dict[str, Any] | None = None
    refactored_err: str | None = None
    try:
        refactored_res = validate_launch_config(config)
    except ValueError as exc:
        refactored_err = str(exc)

    equivalent = (baseline_res == refactored_res) and (baseline_err == refactored_err)
    return {
        "equivalent": equivalent,
        "baseline_result": baseline_res,
        "refactored_result": refactored_res,
        "baseline_error": baseline_err,
        "refactored_error": refactored_err,
    }


def run_fixture_equivalence_suite(case: str = "all") -> dict[str, Any]:
    if case != "all":
        if case not in SYNTHETIC_FIXTURES:
            raise ValueError(f"Unknown case: {case}")
        outcome = _evaluate_both(SYNTHETIC_FIXTURES[case])
        if outcome["refactored_error"] is not None:
            raise ValueError(outcome["refactored_error"])
        return {
            "simulation": True,
            "case": case,
            "equivalent": outcome["equivalent"],
            "report": outcome["refactored_result"],
        }

    cases: list[dict[str, Any]] = []
    for name, fixture in SYNTHETIC_FIXTURES.items():
        outcome = _evaluate_both(fixture)
        cases.append({"case": name, **outcome})

    return {
        "simulation": True,
        "all_equivalent": all(item["equivalent"] for item in cases),
        "cases": cases,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a simulated local server launch configuration, redact "
            "environment values, and prove baseline/refactored equivalence."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", *SYNTHETIC_FIXTURES.keys()),
        default="all",
        help="Fixture case to evaluate (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        payload = run_fixture_equivalence_suite(args.case)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
