#!/usr/bin/env python3
"""
R40-T022: Typed Tool Dispatch and Boundary Validation Lab
Lesson: 17-ai-agents (Generative AI for Beginners)

This module implements a lightweight, local contract fixture demonstrating
defensive tool dispatch for AI agents:
1. Explicit Tool Allowlist: Only declared tools ('add' and 'multiply') can execute.
2. Strict Numeric Validation: Arguments 'a' and 'b' must be finite numbers (int/float).
   Booleans (subclass of int in Python) and numeric strings (e.g. "2") are rejected.
3. Structured Error Envelope: Consistent JSON response format for success and errors.
4. Execution Halting / Failure Isolation: A failed call immediately halts execution
   and prevents any subsequent tool from running.
5. Local Contract Fixture: Pure Python standard library implementation with zero external
   dependencies. This is an educational fixture illustrating dispatch semantics, not a
   full Model Context Protocol (MCP) transport implementation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


# ============================================================================
# Error Classes & Envelopes
# ============================================================================

class DispatchError(Exception):
    """Base exception for tool dispatch errors."""

    def __init__(self, error_type: str, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_type = error_type
        self.code = code
        self.message = message
        self.details = details or {}

    def to_envelope(self, tool_name: Optional[str] = None, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format the exception into a structured JSON error envelope."""
        envelope: Dict[str, Any] = {
            "status": "error",
            "error": {
                "type": self.error_type,
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }
        if tool_name is not None:
            envelope["tool"] = tool_name
        if arguments is not None:
            envelope["arguments"] = arguments
        return envelope


class UnknownToolError(DispatchError):
    """Raised when an unrecognized tool name is requested."""

    def __init__(self, tool_name: str, allowed_tools: List[str]):
        super().__init__(
            error_type="UnknownToolError",
            code="TOOL_NOT_ALLOWED",
            message=f"Tool '{tool_name}' is not permitted in allowlist. Allowed tools: {sorted(allowed_tools)}",
            details={
                "tool": tool_name,
                "allowed_tools": sorted(allowed_tools),
            },
        )


class ValidationError(DispatchError):
    """Raised when tool arguments fail type or schema validation."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ValidationError",
            code=code,
            message=message,
            details=details,
        )


# ============================================================================
# Tool Implementations
# ============================================================================

def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Perform addition of two finite numeric values.

    Example:
        add(2, 3) -> 5
    """
    res = a + b
    # Preserve int type if both inputs are integers
    return int(res) if isinstance(a, int) and isinstance(b, int) and not isinstance(res, float) else res


def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Perform multiplication of two finite numeric values.

    Example:
        multiply(2, 3) -> 6
    """
    res = a * b
    # Preserve int type if both inputs are integers
    return int(res) if isinstance(a, int) and isinstance(b, int) and not isinstance(res, float) else res


# ============================================================================
# Registry and Argument Schema
# ============================================================================

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "add": {
        "function": add,
        "description": "Calculate the arithmetic sum of a and b",
        "parameters": {
            "required": ["a", "b"],
            "expected_type": "number (int or float)",
        },
    },
    "multiply": {
        "function": multiply,
        "description": "Calculate the arithmetic product of a and b",
        "parameters": {
            "required": ["a", "b"],
            "expected_type": "number (int or float)",
        },
    },
}

ALLOWED_TOOLS = set(TOOL_REGISTRY.keys())


# ============================================================================
# Validator and Dispatcher
# ============================================================================

class ToolDispatcher:
    """
    Enforces typed tool dispatch, explicit allowlists, and execution halting.
    """

    def __init__(self, registry: Optional[Dict[str, Dict[str, Any]]] = None):
        self.registry = registry if registry is not None else TOOL_REGISTRY
        self.executed_calls: List[Dict[str, Any]] = []

    def validate_numeric_argument(self, param_name: str, value: Any) -> Union[int, float]:
        """
        Validate that an argument is strictly a finite numeric value (int or float).

        Boundary decisions:
        - Booleans: In Python, bool is a subclass of int (isinstance(True, int) == True).
          However, in JSON and agent function-calling schemas, boolean is a distinct primitive.
          Boundary decision: bool values (True, False) are strictly rejected as invalid types.
        - Numeric strings (e.g. "2"): Agent JSON calls must be typed. Implicit string coercion
          masks model hallucinations and payload malformation.
          Boundary decision: Strings are strictly rejected.
        - Non-finite numbers (NaN, Infinity, -Infinity): Not permissible under JSON standard
          RFC 8259 and unsafe for discrete mathematical calculations.
          Boundary decision: Non-finite values are strictly rejected.
        - None / null: Strictly rejected.
        """
        # 1. Reject boolean values explicitly
        if isinstance(value, bool):
            raise ValidationError(
                code="INVALID_ARGUMENT_TYPE",
                message=f"Argument '{param_name}' must be a finite number (int or float), got bool: {value}",
                details={
                    "parameter": param_name,
                    "expected": "number (int or float)",
                    "received_type": "bool",
                    "received_value": value,
                },
            )

        # 2. Reject string values explicitly
        if isinstance(value, str):
            raise ValidationError(
                code="INVALID_ARGUMENT_TYPE",
                message=f"Argument '{param_name}' must be a finite number (int or float), got str: {json.dumps(value)}",
                details={
                    "parameter": param_name,
                    "expected": "number (int or float)",
                    "received_type": "str",
                    "received_value": value,
                },
            )

        # 3. Ensure instance is int or float
        if not isinstance(value, (int, float)):
            raise ValidationError(
                code="INVALID_ARGUMENT_TYPE",
                message=f"Argument '{param_name}' must be a finite number (int or float), got {type(value).__name__}",
                details={
                    "parameter": param_name,
                    "expected": "number (int or float)",
                    "received_type": type(value).__name__,
                    "received_value": repr(value),
                },
            )

        # 4. Reject non-finite floating point values (NaN, +inf, -inf)
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(
                code="NON_FINITE_NUMERIC_VALUE",
                message=f"Argument '{param_name}' must be a finite number, got non-finite float: {value}",
                details={
                    "parameter": param_name,
                    "expected": "finite number",
                    "received_type": "float",
                    "received_value": str(value),
                },
            )

        return value

    def validate_call(self, tool_name: Any, arguments: Any) -> Tuple[str, Callable[..., Any], Dict[str, Union[int, float]]]:
        """
        Validate tool presence against the allowlist and validate argument schema.
        """
        # Validate tool_name type and presence in allowlist
        if not isinstance(tool_name, str) or tool_name not in self.registry:
            allowed = list(self.registry.keys())
            raise UnknownToolError(str(tool_name), allowed)

        tool_spec = self.registry[tool_name]
        fn = tool_spec["function"]
        required_params = tool_spec["parameters"]["required"]

        # Validate arguments dictionary
        if not isinstance(arguments, dict):
            raise ValidationError(
                code="INVALID_ARGUMENTS_OBJECT",
                message=f"Tool arguments must be a JSON object / dict, got {type(arguments).__name__}",
                details={
                    "expected": "dict",
                    "received_type": type(arguments).__name__,
                },
            )

        # Check for missing required parameters
        missing = [p for p in required_params if p not in arguments]
        if missing:
            raise ValidationError(
                code="MISSING_ARGUMENT",
                message=f"Missing required argument(s) for tool '{tool_name}': {sorted(missing)}",
                details={
                    "missing": sorted(missing),
                    "required": sorted(required_params),
                },
            )

        # Check for extraneous/unexpected parameters
        unexpected = [p for p in arguments if p not in required_params]
        if unexpected:
            raise ValidationError(
                code="UNEXPECTED_ARGUMENT",
                message=f"Unexpected argument(s) for tool '{tool_name}': {sorted(unexpected)}",
                details={
                    "unexpected": sorted(unexpected),
                    "allowed": sorted(required_params),
                },
            )

        # Validate each numeric parameter
        validated_args: Dict[str, Union[int, float]] = {}
        for param in required_params:
            validated_args[param] = self.validate_numeric_argument(param, arguments[param])

        return tool_name, fn, validated_args

    def dispatch(self, call_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a single tool call through validation and execution.
        Returns a structured envelope for either success or error.
        """
        if not isinstance(call_spec, dict):
            err = ValidationError(
                code="INVALID_PAYLOAD",
                message=f"Tool call payload must be a JSON object, got {type(call_spec).__name__}",
            )
            return err.to_envelope()

        tool_name = call_spec.get("tool")
        arguments = call_spec.get("arguments")

        try:
            name, fn, validated_args = self.validate_call(tool_name, arguments)
            result = fn(**validated_args)
            envelope = {
                "status": "success",
                "tool": name,
                "arguments": validated_args,
                "result": result,
            }
            self.executed_calls.append(envelope)
            return envelope
        except DispatchError as e:
            arg_dict = arguments if isinstance(arguments, dict) else None
            envelope = e.to_envelope(tool_name=str(tool_name) if tool_name is not None else None, arguments=arg_dict)
            return envelope
        except Exception as e:  # pragma: no cover
            envelope = {
                "status": "error",
                "tool": str(tool_name),
                "error": {
                    "type": "RuntimeExecutionError",
                    "code": "EXECUTION_FAILURE",
                    "message": str(e),
                    "details": {},
                },
            }
            return envelope

    def dispatch_pipeline(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Dispatch a sequence of tool calls.

        Strict Failure Isolation Rule:
        "A failed call cannot execute another tool."
        If any tool call encounters a validation error, unknown tool error, or
        execution error, the pipeline immediately halts. No subsequent tools are
        invoked or executed.
        """
        if not isinstance(calls, list):
            err = ValidationError(
                code="INVALID_PIPELINE_PAYLOAD",
                message=f"Pipeline calls must be a list of tool call objects, got {type(calls).__name__}",
            )
            return err.to_envelope()

        results: List[Dict[str, Any]] = []
        for index, call_spec in enumerate(calls):
            result_envelope = self.dispatch(call_spec)
            if result_envelope["status"] != "success":
                # Halting execution: do not execute any remaining tool calls
                aborted = calls[index + 1 :]
                return {
                    "status": "error",
                    "pipeline_halted": True,
                    "failed_step_index": index,
                    "completed_steps": len(results),
                    "total_steps": len(calls),
                    "executed_results": results,
                    "failed_call": result_envelope,
                    "aborted_calls": aborted,
                    "message": "Pipeline halted: a failed call cannot execute another tool.",
                }
            results.append(result_envelope)

        return {
            "status": "success",
            "pipeline_halted": False,
            "completed_steps": len(results),
            "total_steps": len(calls),
            "results": results,
        }


# ============================================================================
# CLI Entrypoint
# ============================================================================

def parse_cli_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="R40-T022: Typed tool dispatch and boundary validation fixture."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--call",
        type=str,
        help="JSON string representing a single tool call, e.g. '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
    )
    group.add_argument(
        "--pipeline",
        type=str,
        help="JSON string representing a sequence of tool calls, e.g. '[{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}]'",
    )
    group.add_argument(
        "--tool",
        type=str,
        choices=["add", "multiply"],
        help="Convenience flag: name of tool to invoke (use with --a and --b)",
    )
    group.add_argument(
        "--stdin",
        action="store_true",
        help="Read a JSON tool call or pipeline array from standard input",
    )

    parser.add_argument("--a", type=str, help="Argument a (used with --tool)")
    parser.add_argument("--b", type=str, help="Argument b (used with --tool)")
    return parser.parse_args(argv)


def coerce_cli_arg(val: str) -> Any:
    """Helper for CLI --a/--b flags to preserve numbers vs string inputs."""
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_cli_args(argv)
    dispatcher = ToolDispatcher()

    if args.stdin:
        raw = sys.stdin.read().strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as err:
            envelope = ValidationError(
                code="INVALID_JSON",
                message=f"Failed to parse JSON input from stdin: {err}",
            ).to_envelope()
            print(json.dumps(envelope, indent=2))
            return 1

        if isinstance(payload, list):
            result = dispatcher.dispatch_pipeline(payload)
        else:
            result = dispatcher.dispatch(payload)

    elif args.call:
        try:
            payload = json.loads(args.call)
        except json.JSONDecodeError as err:
            envelope = ValidationError(
                code="INVALID_JSON",
                message=f"Failed to parse --call JSON: {err}",
            ).to_envelope()
            print(json.dumps(envelope, indent=2))
            return 1
        result = dispatcher.dispatch(payload)

    elif args.pipeline:
        try:
            payload = json.loads(args.pipeline)
        except json.JSONDecodeError as err:
            envelope = ValidationError(
                code="INVALID_JSON",
                message=f"Failed to parse --pipeline JSON: {err}",
            ).to_envelope()
            print(json.dumps(envelope, indent=2))
            return 1
        result = dispatcher.dispatch_pipeline(payload)

    elif args.tool:
        if args.a is None or args.b is None:
            envelope = ValidationError(
                code="MISSING_ARGUMENT",
                message="Both --a and --b must be specified when using --tool",
            ).to_envelope(tool_name=args.tool)
            print(json.dumps(envelope, indent=2))
            return 1

        a_val = coerce_cli_arg(args.a)
        b_val = coerce_cli_arg(args.b)
        call_spec = {
            "tool": args.tool,
            "arguments": {
                "a": a_val,
                "b": b_val,
            },
        }
        result = dispatcher.dispatch(call_spec)
    else:  # pragma: no cover
        parser = parse_cli_args(["--help"])
        return 1

    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
