#!/usr/bin/env python3
"""
R40-T025: Typed Tool Dispatch — Offline Service Adapter Lab
Lesson: 17-ai-agents (Generative AI for Beginners)

This module implements a defensive, typed tool dispatcher and a deterministic
offline service adapter for AI agent architectures:
1. Explicit Tool Allowlist: Only declared tools ('add' and 'multiply') can execute.
   Unknown tool requests are rejected with a structured UnknownToolError.
2. Strict Numeric Validation: Arguments 'a' and 'b' must be finite numbers (int/float).
   Booleans (subclass of int in Python), numeric strings (e.g. "2"), non-finite floats
   (NaN, inf), missing arguments, and extraneous arguments are strictly rejected.
3. Callable Interface & Deterministic Local Adapter:
   External service dependencies (e.g. remote calculator services or MCP tools) are
   placed behind a callable interface (ServiceBackend / ArithmeticServiceProtocol).
   A deterministic local adapter (DeterministicOfflineAdapter) executes arithmetic
   in-memory without network, credentials, GPU, or model dependencies.
4. Structured Error Envelopes: Consistent JSON envelope for success and errors.
5. Execution Halting / Failure Isolation: A failed call immediately halts execution
   in multi-step pipelines and guarantees that a failed call cannot execute another tool.
6. Real-Service Behavior Boundaries: Explicitly documents and inspects which real-service
   behaviors (e.g. network latency, rate limits, transient outages, auth) this local
   offline mock does NOT establish.

Scope Note:
This is a local contract fixture demonstrating dispatch and adapter mechanics;
it is not a full Model Context Protocol (MCP) transport implementation.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
import json
import math
import sys
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union


# ============================================================================
# Real-Service Behaviors Not Established by This Local Mock
# ============================================================================

REAL_SERVICE_GAPS: Dict[str, Dict[str, str]] = {
    "network_latency_and_jitter": {
        "title": "Network Transport Latency & Jitter",
        "description": (
            "The offline adapter executes synchronously in-memory (0ms simulated "
            "transport delay). It does not establish network round-trip time (RTT), "
            "packet queuing, latency jitter (p50/p95/p99), or bandwidth constraints."
        ),
        "production_counterpart": "TCP/HTTP/gRPC network stack with variable latency and timeout envelopes.",
    },
    "transient_network_faults": {
        "title": "Transient Network & Connection Failures",
        "description": (
            "The offline adapter does not simulate dropped packets, socket timeouts, "
            "connection resets, TLS negotiation failures, or half-open socket hangs."
        ),
        "production_counterpart": "Transport retry policies, exponential backoff, and circuit breakers.",
    },
    "authentication_and_authorization": {
        "title": "Authentication & Access Control",
        "description": (
            "The offline adapter executes without authentication tokens, API keys, "
            "OAuth2 bearer negotiation, mTLS certificates, or IAM role checks."
        ),
        "production_counterpart": "Identity providers, token refresh cycles, and cloud IAM authorization.",
    },
    "rate_limiting_and_concurrency": {
        "title": "Rate Limiting & Concurrency Contention",
        "description": (
            "The offline adapter handles unbounded sequential calls without throttling. "
            "It does not establish HTTP 429 Too Many Requests, token bucket rate limits, "
            "worker pool saturation, or distributed lock contention."
        ),
        "production_counterpart": "API gateway throttling, quota budgets, and distributed concurrency limits.",
    },
    "distributed_state_and_consistency": {
        "title": "Distributed State & Idempotency",
        "description": (
            "The offline adapter maintains no distributed state. It does not establish "
            "idempotency keys, distributed transaction rollbacks, replica lag, or "
            "eventual consistency drift across multi-region clusters."
        ),
        "production_counterpart": "Distributed databases, message queues, and consensus protocols (e.g. Raft).",
    },
    "remote_service_lifecycle_and_outages": {
        "title": "Remote Service Outages & HTTP Status Codes",
        "description": (
            "The offline adapter is always available in-process. It does not establish "
            "HTTP 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, "
            "or 504 Gateway Timeout downstream dependency failures."
        ),
        "production_counterpart": "Service health checks, blue/green rollouts, and failover routing.",
    },
    "hardware_and_environment_heterogeneity": {
        "title": "Hardware & Environment Heterogeneity",
        "description": (
            "The offline adapter relies strictly on the host CPU and Python runtime. "
            "It does not establish GPU kernel launch overhead, specialized accelerator "
            "precision differences, container cold-starts, or VM memory cgroups."
        ),
        "production_counterpart": "Cloud VM instances, container orchestrators (K8s), and hardware accelerators.",
    },
    "llm_probabilistic_drift": {
        "title": "Model Non-Determinism & Hallucination Drift",
        "description": (
            "The offline fixture validates deterministic JSON payloads. It does not model "
            "probabilistic LLM sampling drift, prompt injection exploits, context truncation, "
            "or malformed schema generation from stochastic models."
        ),
        "production_counterpart": "Model guardrails, temperature controls, and output schema verifiers.",
    },
}


# ============================================================================
# Error Classes & Envelopes
# ============================================================================

class DispatchError(Exception):
    """Base exception for tool dispatch and validation errors."""

    def __init__(
        self,
        error_type: str,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.code = code
        self.message = message
        self.details = details or {}

    def to_envelope(
        self,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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


class BackendServiceError(DispatchError):
    """Raised when the backend service execution fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="BackendServiceError",
            code="SERVICE_EXECUTION_FAILED",
            message=message,
            details=details,
        )


# ============================================================================
# Service Interface (Callable Dependency Abstraction)
# ============================================================================

class ArithmeticServiceProtocol(Protocol):
    """
    Callable interface for the arithmetic external service dependency.

    Any external dependency (remote HTTP service, gRPC worker, cloud calculator,
    or local offline adapter) must satisfy this callable signature.
    """

    def __call__(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        """Execute the arithmetic operation on operands a and b."""
        ...


class ServiceBackend(ABC):
    """
    Abstract base class providing an explicit callable interface for service backends.
    """

    @abstractmethod
    def execute(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        """Perform the requested arithmetic operation."""
        raise NotImplementedError

    def __call__(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        """Allow backend instances to be called directly as callables."""
        return self.execute(operation, a, b)


# ============================================================================
# Deterministic Local Offline Adapter Implementation
# ============================================================================

class DeterministicOfflineAdapter(ServiceBackend):
    """
    Deterministic local offline adapter implementing the arithmetic service interface.

    Features:
    - Zero external network calls or cloud dependencies.
    - Pure standard library arithmetic with exact type preservation (int/float).
    - Diagnostic execution tracing (call counts, invocation history).
    - Explicit introspection of unestablished real-service behaviors.
    """

    def __init__(self) -> None:
        self.call_history: List[Dict[str, Any]] = []
        self.call_count: int = 0

    def execute(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        """
        Execute arithmetic operation locally and deterministically.
        """
        self.call_count += 1
        if operation == "add":
            raw_res = a + b
        elif operation == "multiply":
            raw_res = a * b
        else:
            raise BackendServiceError(
                f"Unsupported operation '{operation}' encountered in backend adapter.",
                details={"operation": operation},
            )

        # Preserve int type if both operands are int and result is whole
        if isinstance(a, int) and isinstance(b, int) and not isinstance(raw_res, float):
            result: Union[int, float] = int(raw_res)
        else:
            result = raw_res

        self.call_history.append({
            "call_index": self.call_count,
            "operation": operation,
            "operands": {"a": a, "b": b},
            "result": result,
        })
        return result

    @property
    def unestablished_real_service_behaviors(self) -> Dict[str, Dict[str, str]]:
        """Return the dictionary of real-service behaviors this adapter does not establish."""
        return REAL_SERVICE_GAPS


class DeliberateWrongResultAdapter(ServiceBackend):
    """
    Test adapter that returns an intentionally incorrect result.
    Used for verifying that test frameworks and check suites catch wrong outputs.
    """

    def execute(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        # Return 999 regardless of inputs to test assertion failure
        return 999


class FaultyServiceAdapter(ServiceBackend):
    """
    Test adapter that simulates an unexpected backend execution exception.
    """

    def execute(
        self,
        operation: str,
        a: Union[int, float],
        b: Union[int, float],
    ) -> Union[int, float]:
        raise BackendServiceError(
            f"Simulated backend failure during '{operation}'",
            details={"operation": operation, "a": a, "b": b},
        )


# ============================================================================
# Tool Registry and Schema
# ============================================================================

ALLOWED_TOOLS: List[str] = ["add", "multiply"]

TOOL_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    "add": {
        "description": "Calculates the arithmetic sum of two finite numeric operands (a + b).",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First finite numeric operand (int or float)."},
                "b": {"type": "number", "description": "Second finite numeric operand (int or float)."},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
    },
    "multiply": {
        "description": "Calculates the arithmetic product of two finite numeric operands (a * b).",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First finite numeric operand (int or float)."},
                "b": {"type": "number", "description": "Second finite numeric operand (int or float)."},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
    },
}


# ============================================================================
# Argument Validation Logic
# ============================================================================

def validate_numeric_arguments(tool: str, raw_arguments: Any) -> Tuple[Union[int, float], Union[int, float]]:
    """
    Validate that raw_arguments is a dictionary containing exactly numeric 'a' and 'b'.

    Strict validation rules:
    1. raw_arguments must be a dict (object).
    2. 'a' and 'b' must be present (MISSING_ARGUMENT).
    3. No additional arguments permitted (UNEXPECTED_ARGUMENT).
    4. Booleans (bool) are strictly rejected (INVALID_ARGUMENT_TYPE).
       In Python, bool subclasses int, but in JSON / tool schemas bool is distinct.
    5. Strings (e.g. "2") are strictly rejected (INVALID_ARGUMENT_TYPE).
    6. Non-finite numbers (NaN, Infinity) are strictly rejected (NON_FINITE_NUMERIC_VALUE).
    7. Operands must be finite int or float.

    Returns:
        Tuple (a, b) of validated numeric values.

    Raises:
        ValidationError: on any contract violation.
    """
    if not isinstance(raw_arguments, dict):
        raise ValidationError(
            code="INVALID_ARGUMENTS_OBJECT",
            message=f"Tool arguments must be a JSON object, got {type(raw_arguments).__name__}",
            details={"received_type": type(raw_arguments).__name__},
        )

    # Check for missing arguments
    required = ["a", "b"]
    missing = [param for param in required if param not in raw_arguments]
    if missing:
        raise ValidationError(
            code="MISSING_ARGUMENT",
            message=f"Tool '{tool}' requires parameter(s): {missing}",
            details={"missing_parameters": missing, "required": required},
        )

    # Check for extraneous arguments
    unexpected = [param for param in raw_arguments.keys() if param not in required]
    if unexpected:
        raise ValidationError(
            code="UNEXPECTED_ARGUMENT",
            message=f"Tool '{tool}' received unexpected parameter(s): {sorted(unexpected)}",
            details={"unexpected_parameters": sorted(unexpected), "allowed_parameters": required},
        )

    validated: Dict[str, Union[int, float]] = {}
    for param in ["a", "b"]:
        val = raw_arguments[param]

        # 1. Reject booleans strictly (bool is a subclass of int in Python)
        if isinstance(val, bool):
            raise ValidationError(
                code="INVALID_ARGUMENT_TYPE",
                message=f"Argument '{param}' cannot be boolean; must be a finite number (int or float)",
                details={
                    "parameter": param,
                    "expected": "finite number (int or float)",
                    "received_type": "bool",
                    "received_value": str(val),
                },
            )

        # 2. Reject non-numeric types (e.g. str, list, dict, None)
        if not isinstance(val, (int, float)):
            type_name = type(val).__name__
            val_str = repr(val) if not isinstance(val, str) else f'"{val}"'
            raise ValidationError(
                code="INVALID_ARGUMENT_TYPE",
                message=f"Argument '{param}' must be a finite number (int or float), got {type_name}: {val_str}",
                details={
                    "parameter": param,
                    "expected": "finite number (int or float)",
                    "received_type": type_name,
                    "received_value": val if not isinstance(val, (dict, list)) else type_name,
                },
            )

        # 3. Reject non-finite floats (NaN, +inf, -inf)
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                raise ValidationError(
                    code="NON_FINITE_NUMERIC_VALUE",
                    message=f"Argument '{param}' must be a finite number; received non-finite float '{val}'",
                    details={
                        "parameter": param,
                        "expected": "finite number (int or float)",
                        "received_value": str(val),
                    },
                )

        validated[param] = val

    return validated["a"], validated["b"]


# ============================================================================
# Typed Tool Dispatcher
# ============================================================================

class TypedToolDispatcher:
    """
    Defensive tool dispatcher for AI agent runtimes.

    Coordinates:
    - Allowlist checking
    - Parameter schema and type validation
    - Delegation to a callable service backend adapter
    - Uniform structured error envelope generation
    - Sequential pipeline execution with failure isolation
    """

    def __init__(
        self,
        backend: Optional[Union[ServiceBackend, Callable[[str, Union[int, float], Union[int, float]], Union[int, float]]]] = None,
        allowed_tools: Optional[List[str]] = None,
    ) -> None:
        self.backend = backend if backend is not None else DeterministicOfflineAdapter()
        self.allowed_tools: List[str] = allowed_tools if allowed_tools is not None else list(ALLOWED_TOOLS)

    def dispatch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a single JSON tool call payload.

        Payload schema:
            {
                "tool": "add" | "multiply",
                "arguments": {"a": number, "b": number}
            }

        Returns:
            Structured success or error envelope.
        """
        if not isinstance(payload, dict):
            err = ValidationError(
                code="INVALID_PAYLOAD",
                message=f"Tool call payload must be a JSON object, got {type(payload).__name__}",
                details={"received_type": type(payload).__name__},
            )
            return err.to_envelope()

        tool_name = payload.get("tool")
        arguments = payload.get("arguments")

        if not isinstance(tool_name, str) or not tool_name:
            err = ValidationError(
                code="MISSING_TOOL_NAME",
                message="Tool call payload must specify a non-empty string 'tool' property",
                details={"received_tool": tool_name},
            )
            return err.to_envelope(tool_name=tool_name, arguments=arguments)

        # 1. Allowlist enforcement
        if tool_name not in self.allowed_tools:
            err = UnknownToolError(tool_name, self.allowed_tools)
            return err.to_envelope(tool_name=tool_name, arguments=arguments)

        # 2. Strict numeric argument validation
        try:
            val_a, val_b = validate_numeric_arguments(tool_name, arguments)
        except ValidationError as e:
            return e.to_envelope(tool_name=tool_name, arguments=arguments)

        # 3. Delegation to callable service backend adapter
        try:
            result = self.backend(tool_name, val_a, val_b)
        except DispatchError as e:
            return e.to_envelope(tool_name=tool_name, arguments=arguments)
        except Exception as e:
            err = BackendServiceError(
                f"Unexpected failure in backend adapter during '{tool_name}': {str(e)}",
                details={"exception": type(e).__name__, "message": str(e)},
            )
            return err.to_envelope(tool_name=tool_name, arguments=arguments)

        # 4. Uniform success envelope
        return {
            "status": "success",
            "tool": tool_name,
            "arguments": {"a": val_a, "b": val_b},
            "result": result,
        }

    def dispatch_pipeline(self, pipeline_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Dispatch a sequential pipeline of tool calls with failure halting.

        Contract:
        - Executes calls sequentially in order.
        - If any call fails (validation error, unknown tool, or backend error),
          the pipeline halts IMMEDIATELY.
        - Subsequent calls are aborted and cannot execute another tool.
        """
        if not isinstance(pipeline_calls, list):
            err = ValidationError(
                code="INVALID_PIPELINE_PAYLOAD",
                message=f"Pipeline payload must be a JSON list of tool calls, got {type(pipeline_calls).__name__}",
                details={"received_type": type(pipeline_calls).__name__},
            )
            return err.to_envelope()

        executed_results: List[Dict[str, Any]] = []

        for idx, call_payload in enumerate(pipeline_calls):
            step_result = self.dispatch(call_payload)

            if step_result.get("status") == "success":
                executed_results.append(step_result)
            else:
                # Failure encountered: halt immediately and isolate subsequent tools
                aborted_calls = pipeline_calls[idx + 1 :]
                return {
                    "status": "error",
                    "pipeline_halted": True,
                    "failed_step_index": idx,
                    "completed_steps": len(executed_results),
                    "total_steps": len(pipeline_calls),
                    "executed_results": executed_results,
                    "failed_call": step_result,
                    "aborted_calls": aborted_calls,
                    "message": "Pipeline halted: a failed call cannot execute another tool.",
                }

        return {
            "status": "success",
            "pipeline_halted": False,
            "completed_steps": len(executed_results),
            "total_steps": len(pipeline_calls),
            "executed_results": executed_results,
        }


# ============================================================================
# CLI Driver
# ============================================================================

def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="R40-T025: Typed Tool Dispatch and Offline Service Adapter Lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--call",
        type=str,
        help="JSON string representing a single tool call, e.g. '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
    )
    group.add_argument(
        "--pipeline",
        type=str,
        help="JSON string representing a list of tool calls to execute sequentially with failure halting.",
    )
    group.add_argument(
        "--show-service-gaps",
        action="store_true",
        help="Display the real-service behaviors and boundaries that this local offline adapter does NOT establish.",
    )
    group.add_argument(
        "--show-schema",
        action="store_true",
        help="Display the tool specifications and JSON schemas for allowed tools.",
    )

    parser.add_argument(
        "--adapter",
        choices=["offline", "deliberate-wrong", "faulty"],
        default="offline",
        help="Select the callable backend adapter (default: 'offline' deterministic adapter).",
    )
    return parser.parse_args(args)


def main(cli_args: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint."""
    parsed = parse_cli_args(cli_args)

    if parsed.show_service_gaps:
        print(json.dumps({
            "scope": "offline_service_adapter_contract_fixture",
            "description": "Explicit catalog of real-service behaviors NOT established by this local mock.",
            "unestablished_behaviors": REAL_SERVICE_GAPS,
        }, indent=2))
        return 0

    if parsed.show_schema:
        print(json.dumps({
            "allowed_tools": ALLOWED_TOOLS,
            "specifications": TOOL_SPECIFICATIONS,
        }, indent=2))
        return 0

    # Instantiate chosen backend adapter
    if parsed.adapter == "offline":
        backend: ServiceBackend = DeterministicOfflineAdapter()
    elif parsed.adapter == "deliberate-wrong":
        backend = DeliberateWrongResultAdapter()
    elif parsed.adapter == "faulty":
        backend = FaultyServiceAdapter()
    else:
        backend = DeterministicOfflineAdapter()

    dispatcher = TypedToolDispatcher(backend=backend)

    if parsed.call:
        try:
            payload = json.loads(parsed.call)
        except json.JSONDecodeError as e:
            err_envelope = {
                "status": "error",
                "error": {
                    "type": "JSONDecodeError",
                    "code": "MALFORMED_JSON_STRING",
                    "message": f"Invalid JSON provided to --call: {str(e)}",
                    "details": {"raw_input": parsed.call},
                },
            }
            print(json.dumps(err_envelope, indent=2))
            return 1

        result = dispatcher.dispatch(payload)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "success" else 1

    if parsed.pipeline:
        try:
            pipeline_payload = json.loads(parsed.pipeline)
        except json.JSONDecodeError as e:
            err_envelope = {
                "status": "error",
                "error": {
                    "type": "JSONDecodeError",
                    "code": "MALFORMED_JSON_STRING",
                    "message": f"Invalid JSON provided to --pipeline: {str(e)}",
                    "details": {"raw_input": parsed.pipeline},
                },
            }
            print(json.dumps(err_envelope, indent=2))
            return 1

        result = dispatcher.dispatch_pipeline(pipeline_payload)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "success" else 1

    # Default help message if no arguments provided
    print(json.dumps({
        "status": "info",
        "message": "Use --call '<json>' or --pipeline '<json>' to dispatch tools. Use --show-service-gaps to inspect mock boundaries.",
        "usage_example": "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
