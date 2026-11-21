"""
R40-T043 · Applied Lab: Generative AI Server Launch Configuration Validator
============================================================================

This module illustrates Lesson 14 ("The Generative AI Application Lifecycle")
by implementing a **preflight launch configuration validator and secret redactor**
for LLMOps deployment workflows.

Lesson connection
-----------------
Lesson 14 covers the operationalization stage of the GenAI lifecycle. Deploying
local or edge LLM model servers (e.g., Ollama, vLLM, Triton, or Uvicorn inference
endpoints) requires strict validation of startup arguments and environment variables.

In production LLMOps:
  1. Launch commands and argument arrays must be validated before process execution
     to prevent shell injection, malformed flags, or improper string splitting.
  2. The configuration must be logged for auditability, but sensitive environment
     values (API keys, endpoints, secrets) must be **redacted** in the summary.
  3. Preflight validation must generate the redacted summary **without launching
     the physical process**.

Simplification boundary
-----------------------
This lab operates purely as an in-memory configuration validator.
It does NOT:
  - Spawn real OS subprocesses or bind network ports.
  - Require live LLM weights or GPU devices.
  - Connect to cloud registries or management endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


REDACTED_MARKER = "[REDACTED]"


@dataclass(frozen=True)
class LaunchSummary:
    """
    Validated and redacted summary of a local server launch configuration.

    Attributes
    ----------
    command : str
        The validated binary or executable name.
    args : tuple[str, ...]
        The validated argument list.
    env_keys : tuple[str, ...]
        Explicitly configured environment variable keys.
    redacted_env : dict[str, str]
        Mapping of env keys to redacted placeholder values (no secrets leaked).
    formatted_command : str
        Safe representation of command and args suitable for audit logging.
    process_launched : bool
        Always False — validates without launching the actual process.
    """
    command: str
    args: tuple[str, ...]
    env_keys: tuple[str, ...]
    redacted_env: dict[str, str]
    formatted_command: str
    process_launched: bool = False


def validate_launch_config(config: Mapping[str, Any]) -> LaunchSummary:
    """
    Validate server launch configuration and produce a redacted summary.

    Parameters
    ----------
    config : Mapping[str, Any]
        Dictionary containing:
          - "command": str (required, non-empty)
          - "args": Sequence[str] (required, must be a list/tuple, NOT a string)
          - "env": Mapping[str, str] (optional, default empty)

    Returns
    -------
    LaunchSummary
        Redacted summary with process_launched=False.

    Raises
    ------
    ValueError
        If "command" is missing, empty, or whitespace.
    TypeError
        If "args" is a single string instead of an argument array (list/tuple),
        or if "args" is missing.
    """
    # 1. Validate Command
    if "command" not in config or config["command"] is None:
        raise ValueError("[R40-T043] Missing required 'command' in launch configuration.")

    command_raw = config["command"]
    if not isinstance(command_raw, str) or not command_raw.strip():
        raise ValueError("[R40-T043] Command must be a non-empty string.")
    command = command_raw.strip()

    # 2. Validate Argument Array
    if "args" not in config or config["args"] is None:
        raise TypeError("[R40-T043] Missing 'args'. An argument array (list or tuple) is required.")

    args_raw = config["args"]
    if isinstance(args_raw, str):
        # Explicit contract requirement: single string where argument array required must fail
        raise TypeError(
            f"[R40-T043] Invalid argument array: received a single string {args_raw!r}. "
            "An array (list or tuple of strings) is strictly required to prevent shell injection."
        )

    if not isinstance(args_raw, (list, tuple)):
        raise TypeError(
            f"[R40-T043] 'args' must be a list or tuple of strings, got {type(args_raw).__name__}."
        )

    for idx, item in enumerate(args_raw):
        if not isinstance(item, str):
            raise TypeError(
                f"[R40-T043] Argument at index {idx} must be a string, got {type(item).__name__}."
            )

    args = tuple(args_raw)

    # 3. Validate and Redact Environment Keys
    env_raw = config.get("env", {})
    if not isinstance(env_raw, Mapping):
        raise TypeError("[R40-T043] 'env' must be a dictionary mapping keys to values.")

    env_keys = tuple(sorted(str(k) for k in env_raw.keys()))
    redacted_env = {key: REDACTED_MARKER for key in env_keys}

    # 4. Format Audit Representation
    formatted_cmd = f"{command} " + " ".join(args) if args else command

    # 5. Return Summary without Launching Process
    return LaunchSummary(
        command=command,
        args=args,
        env_keys=env_keys,
        redacted_env=redacted_env,
        formatted_command=formatted_cmd,
        process_launched=False,
    )


# ---------------------------------------------------------------------------
# Independent Reference Oracle (Focus Requirement)
# ---------------------------------------------------------------------------

def reference_oracle_table(
    command: str,
    args: list[str],
    env_keys: list[str],
) -> dict[str, Any]:
    """
    Independent, simplified calculation used as a verification oracle
    for identical inputs.
    """
    sorted_keys = tuple(sorted(env_keys))
    return {
        "command": command.strip(),
        "args": tuple(args),
        "env_keys": sorted_keys,
        "redacted_env": {k: REDACTED_MARKER for k in sorted_keys},
        "formatted_command": f"{command.strip()} " + " ".join(args) if args else command.strip(),
        "process_launched": False,
    }
