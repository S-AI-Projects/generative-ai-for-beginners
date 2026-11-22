#!/usr/bin/env python3
"""Client-Configuration Validation and Offline Service Adapter (R40-T005).

Lesson 14: The Generative AI Application Lifecycle
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements configuration validation and an offline service adapter for
AI model serving infrastructure. In the GenAI application lifecycle (operationalizing,
deploying, and monitoring LLM services), server launch configurations must be validated
strictly before execution to prevent startup crashes. Furthermore, sensitive runtime
secrets (e.g. API keys, database credentials) must be redacted in audit logs.

Contract Rules:
1. Configuration Schema:
   - `command`: Non-empty string specifying the server binary/executable.
   - `arguments`: List of strings specifying command-line flags and parameters.
   - `environment`: Dictionary mapping explicitly named environment keys to string values.
2. Validation Failures:
   - Missing or empty `command` raises `ConfigurationValidationError`.
   - Arguments passed as a single string (instead of a list/array of strings) raises
     `ConfigurationValidationError`.
3. Secret Redaction:
   - All environment variable values are redacted in the generated summary report as '[REDACTED]'.
4. Execution Safety:
   - Valid configurations produce a structured redacted launch summary WITHOUT spawning any OS process.
5. Focus (Offline Service Adapter):
   - The server launch dependency is encapsulated behind a callable interface (`ServerLaunchAdapter`).
   - The deterministic `OfflineServiceAdapter` intercepts the request locally.
   - Explicitly documents real-service behaviors that this offline test double does NOT establish:
     * TCP port availability and bind collisions (`EADDRINUSE`).
     * Host operating system binary availability and file execution permissions.
     * Runtime GPU memory allocation (VRAM limits) and CUDA driver compatibility.
     * Network latency, TLS handshake, and remote API availability.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local configuration validation test double using Python's
standard library. It does not spawn OS processes or require remote cloud services.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys
from typing import Any, Callable, Dict, List, Optional


class ConfigurationValidationError(Exception):
    """Raised when server launch configuration violates schema contracts."""


class DecisionMismatchError(Exception):
    """Raised when verification assertions fail."""


# Unestablished Real-Service Behaviors
UNESTABLISHED_REAL_BEHAVIORS: List[str] = [
    "TCP port availability and bind collisions (EADDRINUSE)",
    "Operating system binary presence in PATH and execution permissions",
    "Hardware GPU memory allocation (CUDA OOM / VRAM limits)",
    "Network latency, DNS resolution, and remote API endpoint health",
    "OS signal handling (SIGTERM/SIGKILL) and multi-process lifecycle management",
]


@dataclass(frozen=True)
class ServerLaunchConfig:
    """Represents a validated server-launch configuration."""

    command: str
    arguments: List[str]
    environment: Dict[str, str]


def validate_server_config(raw_config: Dict[str, Any]) -> ServerLaunchConfig:
    """Validates raw configuration dictionary against strict server-launch schema."""
    if not isinstance(raw_config, dict):
        raise ConfigurationValidationError("Configuration must be a dictionary.")

    # 1. Command validation
    command = raw_config.get("command")
    if not command or not isinstance(command, str) or not command.strip():
        raise ConfigurationValidationError("Missing or empty required 'command' field.")

    # 2. Arguments validation
    arguments = raw_config.get("arguments")
    if isinstance(arguments, str):
        raise ConfigurationValidationError(
            "A single string was provided where an argument array is required."
        )
    if arguments is None or not isinstance(arguments, list):
        raise ConfigurationValidationError("Arguments field must be a list/array of strings.")
    for idx, arg in enumerate(arguments):
        if not isinstance(arg, str):
            raise ConfigurationValidationError(
                f"Argument at index {idx} must be a string, got {type(arg).__name__}."
            )

    # 3. Environment validation
    environment = raw_config.get("environment", {})
    if not isinstance(environment, dict):
        raise ConfigurationValidationError("Environment must be a dictionary of key-value pairs.")
    for k, v in environment.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ConfigurationValidationError(
                f"Environment key-value pairs must both be strings: ({k}: {v})."
            )

    return ServerLaunchConfig(
        command=command.strip(),
        arguments=list(arguments),
        environment=dict(environment),
    )


class OfflineServiceAdapter:
    """Deterministic offline adapter simulating server launch without spawning processes."""

    def __init__(self) -> None:
        self.launch_history: List[Dict[str, Any]] = []

    def __call__(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validates configuration and returns a redacted summary without launching the process."""
        config = validate_server_config(raw_config)

        # Redact environment values
        redacted_env = {k: "[REDACTED]" for k in config.environment.keys()}

        summary = {
            "status": "VALID_MOCK_LAUNCH_PREPARED",
            "process_launched": False,
            "command": config.command,
            "argument_count": len(config.arguments),
            "arguments": config.arguments,
            "environment_keys": sorted(list(config.environment.keys())),
            "redacted_environment": redacted_env,
            "unestablished_real_behaviors": UNESTABLISHED_REAL_BEHAVIORS,
        }
        self.launch_history.append(summary)
        return summary


def run_normal_scenario() -> Dict[str, Any]:
    """Normal scenario: Valid configuration produces redacted summary without process spawn."""
    adapter = OfflineServiceAdapter()
    raw_config = {
        "command": "uvicorn",
        "arguments": ["app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "environment": {
            "OPENAI_API_KEY": "sk-secret-token-12345",
            "MODEL_NAME": "gpt-4o",
            "DATABASE_URL": "postgresql://user:pass@db:5432/app",
        },
    }
    summary = adapter(raw_config)

    # Verify redaction
    all_redacted = all(val == "[REDACTED]" for val in summary["redacted_environment"].values())
    no_process = (summary["process_launched"] is False)

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "decision": "CONFIG_VALID_REDACTED_SUMMARY",
        "summary": summary,
        "all_redacted": all_redacted,
        "process_launched": summary["process_launched"],
        "contract_satisfied": (all_redacted and no_process),
    }


def run_missing_command_scenario() -> Dict[str, Any]:
    """Failure scenario: Missing command fails validation."""
    adapter = OfflineServiceAdapter()
    raw_config = {
        "arguments": ["--host", "0.0.0.0"],
        "environment": {"PORT": "8000"},
    }
    caught = False
    error_msg = ""
    try:
        adapter(raw_config)
    except ConfigurationValidationError as exc:
        caught = True
        error_msg = str(exc)

    return {
        "scenario_id": "SCENARIO_MISSING_COMMAND",
        "decision": "MISSING_COMMAND_REJECTED",
        "validation_failed": caught,
        "error_message": error_msg,
        "contract_satisfied": caught,
    }


def run_string_arguments_scenario() -> Dict[str, Any]:
    """Failure scenario: String argument instead of array fails validation."""
    adapter = OfflineServiceAdapter()
    raw_config = {
        "command": "uvicorn",
        "arguments": "app.main:app --host 0.0.0.0 --port 8000",  # String instead of array
        "environment": {"PORT": "8000"},
    }
    caught = False
    error_msg = ""
    try:
        adapter(raw_config)
    except ConfigurationValidationError as exc:
        caught = True
        error_msg = str(exc)

    return {
        "scenario_id": "SCENARIO_STRING_ARGS",
        "decision": "STRING_ARGS_REJECTED",
        "validation_failed": caught,
        "error_message": error_msg,
        "contract_satisfied": caught,
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical decision table across all scenarios."""
    normal = run_normal_scenario()
    missing_cmd = run_missing_command_scenario()
    string_args = run_string_arguments_scenario()

    scenarios = [normal, missing_cmd, string_args]
    expected_decisions = {
        "SCENARIO_NORMAL": "CONFIG_VALID_REDACTED_SUMMARY",
        "SCENARIO_MISSING_COMMAND": "MISSING_COMMAND_REJECTED",
        "SCENARIO_STRING_ARGS": "STRING_ARGS_REJECTED",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected and sc.get("contract_satisfied", False))
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T005: Client Configuration Validation & Offline Service Adapter."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "missing_cmd", "string_args"],
        help="Run a specific evaluation scenario.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    if args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "missing_cmd":
        print(json.dumps(run_missing_command_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "string_args":
        print(json.dumps(run_string_arguments_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
