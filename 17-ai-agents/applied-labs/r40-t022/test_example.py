#!/usr/bin/env python3
"""
Unit and integration test suite for R40-T022: Typed Tool Dispatch.

This module verifies:
1. Normal successful tool dispatches: add(2,3) -> 5, multiply(2,3) -> 6.
2. Boundary cases: smallest integers (0, -1), floats, fractions, non-coercion.
3. Invalid cases: unknown tools, string arguments, boolean arguments, NaN, Inf, missing args.
4. Failure isolation: a failed call cannot execute another tool.
5. CLI invocations in fresh processes via subprocess.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import unittest
from typing import Any, Dict, List

from example import (
    ALLOWED_TOOLS,
    TOOL_REGISTRY,
    ToolDispatcher,
    UnknownToolError,
    ValidationError,
    add,
    multiply,
)


class TestBasicToolFunctions(unittest.TestCase):
    """Direct tests for the underlying mathematical functions."""

    def test_add_normal(self):
        self.assertEqual(add(2, 3), 5)
        self.assertIsInstance(add(2, 3), int)

    def test_multiply_normal(self):
        self.assertEqual(multiply(2, 3), 6)
        self.assertIsInstance(multiply(2, 3), int)

    def test_add_boundaries(self):
        # Smallest integers: zero and negative numbers
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(-5, -7), -12)
        # Floats
        self.assertAlmostEqual(add(0.25, 0.75), 1.0)
        self.assertAlmostEqual(add(1e-8, 2e-8), 3e-8)

    def test_multiply_boundaries(self):
        # Zero boundaries
        self.assertEqual(multiply(0, 0), 0)
        self.assertEqual(multiply(0, 10), 0)
        self.assertEqual(multiply(-1, 1), -1)
        self.assertEqual(multiply(-4, -5), 20)
        # Floats
        self.assertAlmostEqual(multiply(2.5, 4.0), 10.0)
        self.assertAlmostEqual(multiply(-2.5, 2.0), -5.0)


class TestArgumentValidation(unittest.TestCase):
    """Tests for defensive schema and type validation."""

    def setUp(self):
        self.dispatcher = ToolDispatcher()

    def test_valid_integer_arguments(self):
        self.assertEqual(self.dispatcher.validate_numeric_argument("a", 2), 2)
        self.assertEqual(self.dispatcher.validate_numeric_argument("b", 0), 0)
        self.assertEqual(self.dispatcher.validate_numeric_argument("a", -10), -10)

    def test_valid_float_arguments(self):
        self.assertEqual(self.dispatcher.validate_numeric_argument("a", 3.14), 3.14)
        self.assertEqual(self.dispatcher.validate_numeric_argument("b", -0.001), -0.001)

    def test_boundary_boolean_rejection(self):
        """
        Boundary decision: Python booleans subclass int, but in JSON / agent payloads,
        booleans (true/false) are distinct primitives.
        Accepting bool as number is dangerous, so bool MUST be rejected.
        """
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_numeric_argument("a", True)
        self.assertEqual(ctx.exception.code, "INVALID_ARGUMENT_TYPE")
        self.assertIn("bool", ctx.exception.message)

        with self.assertRaises(ValidationError) as ctx2:
            self.dispatcher.validate_numeric_argument("b", False)
        self.assertEqual(ctx2.exception.code, "INVALID_ARGUMENT_TYPE")

    def test_string_rejection(self):
        """
        Boundary decision: Strings representing numbers (e.g. '2') must not be coerced.
        The requirement specifically states string arguments are structured errors.
        """
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_numeric_argument("a", "2")
        self.assertEqual(ctx.exception.code, "INVALID_ARGUMENT_TYPE")
        self.assertIn("str", ctx.exception.message)

        with self.assertRaises(ValidationError):
            self.dispatcher.validate_numeric_argument("a", "hello")

        with self.assertRaises(ValidationError):
            self.dispatcher.validate_numeric_argument("a", "")

    def test_non_finite_float_rejection(self):
        """
        Boundary decision: NaN, Infinity, -Infinity are not permissible in standard JSON
        and violate discrete arithmetic contracts.
        """
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_numeric_argument("a", float("nan"))
        self.assertEqual(ctx.exception.code, "NON_FINITE_NUMERIC_VALUE")

        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_numeric_argument("a", float("inf"))
        self.assertEqual(ctx.exception.code, "NON_FINITE_NUMERIC_VALUE")

        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_numeric_argument("a", float("-inf"))
        self.assertEqual(ctx.exception.code, "NON_FINITE_NUMERIC_VALUE")

    def test_non_numeric_types_rejection(self):
        """None, lists, dicts must be rejected."""
        with self.assertRaises(ValidationError):
            self.dispatcher.validate_numeric_argument("a", None)

        with self.assertRaises(ValidationError):
            self.dispatcher.validate_numeric_argument("a", [1, 2])

        with self.assertRaises(ValidationError):
            self.dispatcher.validate_numeric_argument("a", {"x": 1})

    def test_schema_missing_and_unexpected_arguments(self):
        # Missing parameter 'b'
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_call("add", {"a": 2})
        self.assertEqual(ctx.exception.code, "MISSING_ARGUMENT")
        self.assertIn("b", ctx.exception.details["missing"])

        # Missing parameter 'a'
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_call("multiply", {"b": 3})
        self.assertEqual(ctx.exception.code, "MISSING_ARGUMENT")
        self.assertIn("a", ctx.exception.details["missing"])

        # Unexpected extra parameter 'c'
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_call("add", {"a": 2, "b": 3, "c": 4})
        self.assertEqual(ctx.exception.code, "UNEXPECTED_ARGUMENT")
        self.assertIn("c", ctx.exception.details["unexpected"])

        # Non-dict arguments
        with self.assertRaises(ValidationError) as ctx:
            self.dispatcher.validate_call("add", [2, 3])
        self.assertEqual(ctx.exception.code, "INVALID_ARGUMENTS_OBJECT")


class TestToolAllowlist(unittest.TestCase):
    """Tests for explicit tool allowlist enforcement."""

    def setUp(self):
        self.dispatcher = ToolDispatcher()

    def test_allowed_tools_pass(self):
        self.assertIn("add", self.dispatcher.registry)
        self.assertIn("multiply", self.dispatcher.registry)

    def test_unknown_tools_raise_unknown_tool_error(self):
        unknown_candidates = ["divide", "subtract", "power", "system_exec", "eval", "", "ADD"]
        for candidate in unknown_candidates:
            with self.assertRaises(UnknownToolError) as ctx:
                self.dispatcher.validate_call(candidate, {"a": 2, "b": 3})
            self.assertEqual(ctx.exception.code, "TOOL_NOT_ALLOWED")
            self.assertEqual(ctx.exception.details["tool"], candidate)
            self.assertEqual(ctx.exception.details["allowed_tools"], ["add", "multiply"])


class TestSingleDispatchAndStructuredEnvelopes(unittest.TestCase):
    """Tests for structured envelope outputs and error formats."""

    def setUp(self):
        self.dispatcher = ToolDispatcher()

    def test_add_success_envelope(self):
        res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tool"], "add")
        self.assertEqual(res["result"], 5)
        self.assertEqual(res["arguments"], {"a": 2, "b": 3})

    def test_multiply_success_envelope(self):
        res = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tool"], "multiply")
        self.assertEqual(res["result"], 6)
        self.assertEqual(res["arguments"], {"a": 2, "b": 3})

    def test_unknown_tool_structured_error(self):
        res = self.dispatcher.dispatch({"tool": "power", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["tool"], "power")
        self.assertEqual(res["error"]["type"], "UnknownToolError")
        self.assertEqual(res["error"]["code"], "TOOL_NOT_ALLOWED")
        self.assertIn("power", res["error"]["message"])

    def test_string_argument_a_structured_error(self):
        res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["tool"], "add")
        self.assertEqual(res["error"]["type"], "ValidationError")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertEqual(res["error"]["details"]["parameter"], "a")
        self.assertEqual(res["error"]["details"]["received_type"], "str")

    def test_invalid_payload_envelope(self):
        res = self.dispatcher.dispatch("not a dict")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_PAYLOAD")


class TestExecutionIsolationAndHalting(unittest.TestCase):
    """
    Tests proving that:
    1. A failed single call cannot execute any tool function.
    2. In a pipeline/chain, a failed call immediately halts execution and
       cannot execute subsequent tools.
    """

    def test_single_failed_call_does_not_execute_tool(self):
        """Spy on functions to ensure neither is called when validation fails."""
        call_tracker = {"add_invoked": 0, "multiply_invoked": 0}

        def tracked_add(a, b):
            call_tracker["add_invoked"] += 1
            return a + b

        def tracked_multiply(a, b):
            call_tracker["multiply_invoked"] += 1
            return a * b

        custom_registry = {
            "add": {
                "function": tracked_add,
                "description": "tracked add",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
            "multiply": {
                "function": tracked_multiply,
                "description": "tracked multiply",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
        }

        dispatcher = ToolDispatcher(registry=custom_registry)

        # Call with invalid string 'a'
        res = dispatcher.dispatch({"tool": "add", "arguments": {"a": "bad", "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(call_tracker["add_invoked"], 0)
        self.assertEqual(call_tracker["multiply_invoked"], 0)

        # Call with unknown tool
        res_unknown = dispatcher.dispatch({"tool": "unknown", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res_unknown["status"], "error")
        self.assertEqual(call_tracker["add_invoked"], 0)
        self.assertEqual(call_tracker["multiply_invoked"], 0)

    def test_pipeline_halts_on_failure_blocking_subsequent_tools(self):
        """
        Contract rule: 'a failed call cannot execute another tool.'
        In a pipeline where call 0 fails, call 1 must be aborted and never run.
        """
        call_tracker = {"add_invoked": 0, "multiply_invoked": 0}

        def tracked_add(a, b):
            call_tracker["add_invoked"] += 1
            return a + b

        def tracked_multiply(a, b):
            call_tracker["multiply_invoked"] += 1
            return a * b

        custom_registry = {
            "add": {
                "function": tracked_add,
                "description": "tracked add",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
            "multiply": {
                "function": tracked_multiply,
                "description": "tracked multiply",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
        }

        dispatcher = ToolDispatcher(registry=custom_registry)

        calls = [
            {"tool": "add", "arguments": {"a": "invalid_string", "b": 3}},
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        ]

        pipeline_result = dispatcher.dispatch_pipeline(calls)

        self.assertEqual(pipeline_result["status"], "error")
        self.assertTrue(pipeline_result["pipeline_halted"])
        self.assertEqual(pipeline_result["failed_step_index"], 0)
        self.assertEqual(pipeline_result["completed_steps"], 0)
        self.assertEqual(len(pipeline_result["aborted_calls"]), 1)
        self.assertEqual(pipeline_result["aborted_calls"][0]["tool"], "multiply")

        # Crucial assertion: multiply was NEVER invoked!
        self.assertEqual(call_tracker["add_invoked"], 0)
        self.assertEqual(call_tracker["multiply_invoked"], 0)

    def test_pipeline_mid_sequence_halting(self):
        """If step 1 succeeds, step 2 fails, step 3 must be aborted."""
        call_tracker = {"add_invoked": 0, "multiply_invoked": 0}

        def tracked_add(a, b):
            call_tracker["add_invoked"] += 1
            return a + b

        def tracked_multiply(a, b):
            call_tracker["multiply_invoked"] += 1
            return a * b

        custom_registry = {
            "add": {
                "function": tracked_add,
                "description": "tracked add",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
            "multiply": {
                "function": tracked_multiply,
                "description": "tracked multiply",
                "parameters": {"required": ["a", "b"], "expected_type": "number"},
            },
        }

        dispatcher = ToolDispatcher(registry=custom_registry)

        calls = [
            {"tool": "add", "arguments": {"a": 2, "b": 3}},       # Step 0: succeeds
            {"tool": "divide", "arguments": {"a": 6, "b": 2}},    # Step 1: fails (unknown tool)
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}},  # Step 2: must be aborted!
        ]

        res = dispatcher.dispatch_pipeline(calls)
        self.assertEqual(res["status"], "error")
        self.assertTrue(res["pipeline_halted"])
        self.assertEqual(res["completed_steps"], 1)
        self.assertEqual(res["failed_step_index"], 1)
        self.assertEqual(len(res["aborted_calls"]), 1)
        self.assertEqual(res["aborted_calls"][0]["tool"], "multiply")

        # Step 0 was called once; step 2 was NEVER called!
        self.assertEqual(call_tracker["add_invoked"], 1)
        self.assertEqual(call_tracker["multiply_invoked"], 0)


class TestSubprocessCLIExecution(unittest.TestCase):
    """Tests executing the script as a fresh external CLI process."""

    def setUp(self):
        self.script_path = os.path.join(
            os.path.dirname(__file__), "example.py"
        )

    def run_cli(self, args: List[str], stdin_data: str = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, self.script_path] + args
        return subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
        )

    def test_cli_add_normal(self):
        proc = self.run_cli(["--call", '{"tool": "add", "arguments": {"a": 2, "b": 3}}'])
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"], 5)

    def test_cli_multiply_normal(self):
        proc = self.run_cli(["--call", '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'])
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"], 6)

    def test_cli_unknown_tool_exit_code_1(self):
        proc = self.run_cli(["--call", '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'])
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["code"], "TOOL_NOT_ALLOWED")

    def test_cli_string_argument_exit_code_1(self):
        proc = self.run_cli(["--call", '{"tool": "add", "arguments": {"a": "2", "b": 3}}'])
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_cli_pipeline_halting_exit_code_1(self):
        pipeline = [
            {"tool": "add", "arguments": {"a": "invalid", "b": 3}},
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        ]
        proc = self.run_cli(["--pipeline", json.dumps(pipeline)])
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "error")
        self.assertTrue(data["pipeline_halted"])
        self.assertEqual(len(data["aborted_calls"]), 1)

    def test_cli_stdin_support(self):
        stdin_input = json.dumps({"tool": "add", "arguments": {"a": 10, "b": 20}})
        proc = self.run_cli(["--stdin"], stdin_data=stdin_input)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["result"], 30)

    def test_cli_flag_convenience(self):
        proc = self.run_cli(["--tool", "add", "--a", "2", "--b", "3"])
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["result"], 5)


class TestDeliberateFailureVerification(unittest.TestCase):
    """
    Demonstrates that the test framework detects incorrect behavior:
    A deliberately wrong result causes an assertion error and nonzero exit.
    """

    def test_deliberate_wrong_result_fails(self):
        dispatcher = ToolDispatcher()
        res = dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        # Correct result is 5. Asserting 999 must raise AssertionError.
        with self.assertRaises(AssertionError):
            self.assertEqual(res["result"], 999, "Deliberate wrong result check")


if __name__ == "__main__":
    unittest.main()
