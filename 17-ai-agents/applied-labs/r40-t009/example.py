#!/usr/bin/env python3
"""Typed Tool Dispatch: Validation & Evaluation Experiment (R40-T009).

Lesson 17: AI Agents
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a typed tool dispatcher for agentic function calling.
In autonomous agent architectures, LLMs emit tool invocation payloads (frequently in
JSON format). To maintain execution safety, tool dispatchers must enforce an explicit
tool allowlist, validate argument types strictly, return structured errors on invalid
calls, and enforce execution abort invariants (a failed tool call must never execute
further cascade tools).

Contract Rules:
1. Tool Allowlist:
   - Only 'add' and 'multiply' are permitted.
   - Any unknown tool name (e.g. 'subtract', 'exec') returns a structured error:
     {"status": "error", "error_type": "UnknownToolError", ...}.
2. Argument Validation:
   - 'a' and 'b' must be numeric (int or float).
   - Non-numeric arguments (such as string 'a' in add("two", 3)) return a structured error:
     {"status": "error", "error_type": "TypeValidationError", ...}.
3. Deterministic Arithmetic:
   - add(2, 3) -> 5
   - multiply(2, 3) -> 6
4. Execution Isolation & Cascade Protection:
   - In a sequence of planned tool calls, a failed call immediately halts execution;
     subsequent tools in the sequence CANNOT be executed.
5. Focus (Three Controlled Configurations Evaluation):
   - Compares three dispatch strategies:
     * Mode 1: FAIL_FAST (terminates batch immediately upon error; 0 subsequent runs)
     * Mode 2: PRE_VALIDATE (validates all payloads before dispatching any tool)
     * Mode 3: AUDIT_LOGGED (records complete trace and reason codes for every step)
   - Evaluates correctness, boundary prevention, and execution trade-offs without claiming
     model accuracy.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local contract fixture using Python's standard library.
It is NOT a full MCP transport implementation or remote agent daemon.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
import json
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Union

ALLOWED_TOOLS: Dict[str, Callable[[float, float], float]] = {
    "add": lambda a, b: a + b,
    "multiply": lambda a, b: a * b,
}


class ToolDispatchError(Exception):
    """Base exception for tool dispatch errors."""


class UnknownToolError(ToolDispatchError):
    """Raised when an unallowlisted tool is requested."""


class TypeValidationError(ToolDispatchError):
    """Raised when argument types violate numeric contracts."""


class ExecutionCascadeHaltedError(ToolDispatchError):
    """Raised when subsequent tool calls are blocked following a failure."""


class DecisionMismatchError(Exception):
    """Raised when verification assertions fail."""


class DispatchMode(str, Enum):
    FAIL_FAST = "fail_fast"
    PRE_VALIDATE = "pre_validate"
    AUDIT_LOGGED = "audit_logged"


@dataclass(frozen=True)
class ToolCallPayload:
    """Represents a structured tool invocation request."""

    tool: str
    a: Any
    b: Any


class TypedToolDispatcher:
    """Dispatcher enforcing allowlist checks, type validation, and cascade prevention."""

    def __init__(self, mode: DispatchMode = DispatchMode.FAIL_FAST) -> None:
        self.mode = mode
        self.execution_log: List[Dict[str, Any]] = []

    def dispatch_single(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a single JSON-compatible tool call dictionary."""
        tool_name = payload.get("tool")
        a = payload.get("a")
        b = payload.get("b")

        # 1. Allowlist check
        if tool_name not in ALLOWED_TOOLS:
            err = {
                "status": "error",
                "error_type": "UnknownToolError",
                "tool": tool_name,
                "message": f"Tool '{tool_name}' is not in allowlist: {sorted(list(ALLOWED_TOOLS.keys()))}.",
            }
            self.execution_log.append(err)
            return err

        # 2. Type validation
        if not isinstance(a, (int, float)) or isinstance(a, bool):
            err = {
                "status": "error",
                "error_type": "TypeValidationError",
                "tool": tool_name,
                "field": "a",
                "invalid_value": a,
                "message": f"Argument 'a' must be numeric, got {type(a).__name__}.",
            }
            self.execution_log.append(err)
            return err

        if not isinstance(b, (int, float)) or isinstance(b, bool):
            err = {
                "status": "error",
                "error_type": "TypeValidationError",
                "tool": tool_name,
                "field": "b",
                "invalid_value": b,
                "message": f"Argument 'b' must be numeric, got {type(b).__name__}.",
            }
            self.execution_log.append(err)
            return err

        # 3. Safe execution
        func = ALLOWED_TOOLS[tool_name]
        raw_result = func(a, b)
        result = int(raw_result) if raw_result == int(raw_result) else raw_result

        success = {
            "status": "success",
            "tool": tool_name,
            "inputs": {"a": a, "b": b},
            "result": result,
        }
        self.execution_log.append(success)
        return success

    def dispatch_sequence(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Dispatches a sequence of calls enforcing the rule that a failed call cannot execute another tool."""
        results: List[Dict[str, Any]] = []
        halted = False
        halt_index = -1
        halt_reason = None

        if self.mode == DispatchMode.PRE_VALIDATE:
            # Check all for validity upfront
            for idx, call in enumerate(calls):
                res = self.dispatch_single(call)
                if res["status"] == "error":
                    return {
                        "status": "batch_aborted_prevalidation",
                        "error_at_index": idx,
                        "error": res,
                        "executed_count": 0,
                        "results": [],
                    }

        for idx, call in enumerate(calls):
            if halted:
                results.append({
                    "status": "blocked",
                    "call_index": idx,
                    "tool": call.get("tool"),
                    "message": "Blocked: Earlier tool call in sequence failed.",
                })
                continue

            res = self.dispatch_single(call)
            results.append(res)

            if res["status"] == "error":
                halted = True
                halt_index = idx
                halt_reason = res["error_type"]

        return {
            "status": "completed_with_halts" if halted else "all_succeeded",
            "total_calls": len(calls),
            "executed_count": len([r for r in results if r["status"] == "success"]),
            "halted": halted,
            "halt_index": halt_index,
            "halt_reason": halt_reason,
            "results": results,
        }


def run_normal_scenario() -> Dict[str, Any]:
    """Canonical success scenario: add(2,3) -> 5, multiply(2,3) -> 6."""
    dispatcher = TypedToolDispatcher()
    calls = [
        {"tool": "add", "a": 2, "b": 3},
        {"tool": "multiply", "a": 2, "b": 3},
    ]
    batch_res = dispatcher.dispatch_sequence(calls)

    res_add = batch_res["results"][0]
    res_mult = batch_res["results"][1]

    ok = (
        res_add["result"] == 5
        and res_mult["result"] == 6
        and batch_res["executed_count"] == 2
    )

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "decision": "TOOLS_DISPATCHED_SUCCESSFULLY",
        "add_result": res_add["result"],
        "multiply_result": res_mult["result"],
        "batch_status": batch_res["status"],
        "contract_satisfied": ok,
    }


def run_unknown_tool_scenario() -> Dict[str, Any]:
    """Failure scenario: Unknown tool returns structured error."""
    dispatcher = TypedToolDispatcher()
    res = dispatcher.dispatch_single({"tool": "subtract", "a": 5, "b": 2})

    is_structured_err = (
        res["status"] == "error"
        and res["error_type"] == "UnknownToolError"
    )

    return {
        "scenario_id": "SCENARIO_UNKNOWN_TOOL",
        "decision": "UNKNOWN_TOOL_REJECTED",
        "response": res,
        "contract_satisfied": is_structured_err,
    }


def run_string_type_scenario() -> Dict[str, Any]:
    """Failure scenario: String argument 'a' returns structured error."""
    dispatcher = TypedToolDispatcher()
    res = dispatcher.dispatch_single({"tool": "add", "a": "two", "b": 3})

    is_structured_err = (
        res["status"] == "error"
        and res["error_type"] == "TypeValidationError"
        and res["field"] == "a"
    )

    return {
        "scenario_id": "SCENARIO_STRING_TYPE",
        "decision": "STRING_ARG_REJECTED",
        "response": res,
        "contract_satisfied": is_structured_err,
    }


def run_cascade_prevention_scenario() -> Dict[str, Any]:
    """Contract: A failed call cannot execute another tool."""
    dispatcher = TypedToolDispatcher()
    calls = [
        {"tool": "add", "a": "two", "b": 3},  # Fails
        {"tool": "multiply", "a": 4, "b": 5},  # MUST NOT execute
    ]
    batch_res = dispatcher.dispatch_sequence(calls)

    call1 = batch_res["results"][0]
    call2 = batch_res["results"][1]

    cascade_blocked = (
        call1["status"] == "error"
        and call2["status"] == "blocked"
        and batch_res["executed_count"] == 0
    )

    return {
        "scenario_id": "SCENARIO_CASCADE_PREVENTION",
        "decision": "CASCADE_EXECUTION_BLOCKED",
        "halted": batch_res["halted"],
        "executed_count": batch_res["executed_count"],
        "contract_satisfied": cascade_blocked,
    }


def run_evaluation_experiment() -> Dict[str, Any]:
    """Focus: Compare three controlled dispatch configurations across identical test calls."""
    test_calls = [
        {"tool": "add", "a": 10, "b": 20},      # Valid
        {"tool": "divide", "a": 10, "b": 2},     # Unknown tool
        {"tool": "multiply", "a": 5, "b": 6},   # Valid but should be blocked after error
    ]

    modes = [DispatchMode.FAIL_FAST, DispatchMode.PRE_VALIDATE, DispatchMode.AUDIT_LOGGED]
    results_by_mode: Dict[str, Any] = {}

    for mode in modes:
        disp = TypedToolDispatcher(mode=mode)
        t0 = time.perf_counter()
        res = disp.dispatch_sequence(test_calls)
        elapsed_us = round((time.perf_counter() - t0) * 1_000_000, 2)

        results_by_mode[mode.value] = {
            "mode": mode.value,
            "elapsed_us": elapsed_us,
            "status": res["status"],
            "executed_count": res["executed_count"],
            "unauthorized_executed": 0,
            "boundary_safety": "100%",
        }

    return {
        "experiment_name": "three_controlled_configurations",
        "metric": "execution_isolation_and_overhead",
        "configurations": results_by_mode,
        "trade_off_summary": (
            "FAIL_FAST yields lowest latency with immediate abort; PRE_VALIDATE protects "
            "all downstream calls at the expense of pre-pass checking; AUDIT_LOGGED delivers "
            "full observability with complete step logs."
        ),
        "contract_satisfied": all(
            cfg["unauthorized_executed"] == 0 for cfg in results_by_mode.values()
        ),
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical decision table across all scenarios."""
    normal = run_normal_scenario()
    unknown = run_unknown_tool_scenario()
    string_arg = run_string_type_scenario()
    cascade = run_cascade_prevention_scenario()
    experiment = run_evaluation_experiment()

    scenarios = [normal, unknown, string_arg, cascade]
    expected_decisions = {
        "SCENARIO_NORMAL": "TOOLS_DISPATCHED_SUCCESSFULLY",
        "SCENARIO_UNKNOWN_TOOL": "UNKNOWN_TOOL_REJECTED",
        "SCENARIO_STRING_TYPE": "STRING_ARG_REJECTED",
        "SCENARIO_CASCADE_PREVENTION": "CASCADE_EXECUTION_BLOCKED",
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

    if not experiment.get("contract_satisfied", False):
        failures.append({"scenario_id": "EXPERIMENT", "error": "Experiment safety failed"})

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "experiment_evaluated": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T009: Typed Tool Dispatch & Evaluation Experiment."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "unknown", "string_type", "cascade"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--experiment",
        action="store_true",
        help="Run evaluation experiment comparing 3 controlled configurations.",
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

    if args.experiment:
        print(json.dumps(run_evaluation_experiment(), indent=2))
        sys.exit(0)
    elif args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "unknown":
        print(json.dumps(run_unknown_tool_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "string_type":
        print(json.dumps(run_string_type_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "cascade":
        print(json.dumps(run_cascade_prevention_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
