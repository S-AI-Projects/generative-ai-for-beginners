#!/usr/bin/env python3
"""
Unit and integration tests for R40-T025.
Tests typed tool dispatch, offline service adapter, validation boundaries,
pipeline failure halting, and real-service gap inspection.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import unittest
from typing import Any, Dict, List, Union

from example import (
    ALLOWED_TOOLS,
    BackendServiceError,
    DeliberateWrongResultAdapter,
    DeterministicOfflineAdapter,
    DispatchError,
    FaultyServiceAdapter,
    REAL_SERVICE_GAPS,
    ServiceBackend,
    TOOL_SPECIFICATIONS,
    TypedToolDispatcher,
    UnknownToolError,
    ValidationError,
    validate_numeric_arguments,
)


class TestNormalScenarios(unittest.TestCase):
    """Test normal addition and multiplication with deterministic offline adapter."""

    def setUp(self) -> None:
        self.adapter = DeterministicOfflineAdapter()
        self.dispatcher = TypedToolDispatcher(backend=self.adapter)

    def test_add_normal(self) -> None:
        """add(2, 3) must return 5 with status success."""
        payload = {"tool": "add", "arguments": {"a": 2, "b": 3}}
        result = self.dispatcher.dispatch(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool"], "add")
        self.assertEqual(result["arguments"], {"a": 2, "b": 3})
        self.assertEqual(result["result"], 5)
        self.assertEqual(self.adapter.call_count, 1)

    def test_multiply_normal(self) -> None:
        """multiply(2, 3) must return 6 with status success."""
        payload = {"tool": "multiply", "arguments": {"a": 2, "b": 3}}
        result = self.dispatcher.dispatch(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool"], "multiply")
        self.assertEqual(result["arguments"], {"a": 2, "b": 3})
        self.assertEqual(result["result"], 6)
        self.assertEqual(self.adapter.call_count, 1)


class TestBoundaryScenarios(unittest.TestCase):
    """Test boundary conditions: zeros, negatives, floats, and large integers."""

    def setUp(self) -> None:
        self.adapter = DeterministicOfflineAdapter()
        self.dispatcher = TypedToolDispatcher(backend=self.adapter)

    def test_zeros(self) -> None:
        """add(0, 0) -> 0 and multiply(0, 10) -> 0."""
        add_res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 0, "b": 0}})
        self.assertEqual(add_res["status"], "success")
        self.assertEqual(add_res["result"], 0)

        mul_res = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 0, "b": 10}})
        self.assertEqual(mul_res["status"], "success")
        self.assertEqual(mul_res["result"], 0)

    def test_negative_numbers(self) -> None:
        """Negative numbers must be properly handled."""
        add_res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": -5, "b": 10}})
        self.assertEqual(add_res["result"], 5)

        mul_res = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": -2, "b": 3}})
        self.assertEqual(mul_res["result"], -6)

    def test_floating_point_numbers(self) -> None:
        """Floating point numbers must preserve floating precision."""
        add_res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 0.25, "b": 0.75}})
        self.assertEqual(add_res["result"], 1.0)
        self.assertIsInstance(add_res["result"], float)

        mul_res = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 2.5, "b": 4.0}})
        self.assertEqual(mul_res["result"], 10.0)
        self.assertIsInstance(mul_res["result"], float)

    def test_large_integers(self) -> None:
        """Large numbers within Python arbitrary precision must succeed."""
        a = 10**14
        b = 10**14
        res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": a, "b": b}})
        self.assertEqual(res["result"], 2 * 10**14)


class TestTypeValidationAndErrors(unittest.TestCase):
    """Test strict argument validation and structured error envelopes."""

    def setUp(self) -> None:
        self.dispatcher = TypedToolDispatcher()

    def test_string_argument_a_rejected(self) -> None:
        """String argument 'a' must be rejected with structured ValidationError."""
        payload = {"tool": "add", "arguments": {"a": "2", "b": 3}}
        result = self.dispatcher.dispatch(payload)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["type"], "ValidationError")
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertIn("a", result["error"]["message"])
        self.assertEqual(result["error"]["details"]["parameter"], "a")
        self.assertEqual(result["error"]["details"]["received_type"], "str")

    def test_string_argument_b_rejected(self) -> None:
        """String argument 'b' must be rejected with structured ValidationError."""
        payload = {"tool": "multiply", "arguments": {"a": 2, "b": "3"}}
        result = self.dispatcher.dispatch(payload)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["type"], "ValidationError")
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertIn("b", result["error"]["message"])

    def test_boolean_strictly_rejected(self) -> None:
        """Booleans must not be coerced to integers even though bool subclasses int in Python."""
        payload_true = {"tool": "add", "arguments": {"a": True, "b": 3}}
        res_true = self.dispatcher.dispatch(payload_true)
        self.assertEqual(res_true["status"], "error")
        self.assertEqual(res_true["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertIn("boolean", res_true["error"]["message"])

        payload_false = {"tool": "add", "arguments": {"a": 2, "b": False}}
        res_false = self.dispatcher.dispatch(payload_false)
        self.assertEqual(res_false["status"], "error")
        self.assertEqual(res_false["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_non_finite_floats_rejected(self) -> None:
        """NaN, +inf, -inf must be rejected with NON_FINITE_NUMERIC_VALUE."""
        for non_finite in [float("nan"), float("inf"), float("-inf")]:
            payload = {"tool": "add", "arguments": {"a": non_finite, "b": 3}}
            res = self.dispatcher.dispatch(payload)
            self.assertEqual(res["status"], "error")
            self.assertEqual(res["error"]["code"], "NON_FINITE_NUMERIC_VALUE")

    def test_missing_argument(self) -> None:
        """Missing required parameter must return MISSING_ARGUMENT."""
        payload = {"tool": "add", "arguments": {"a": 2}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "MISSING_ARGUMENT")
        self.assertIn("b", res["error"]["details"]["missing_parameters"])

    def test_unexpected_argument(self) -> None:
        """Extraneous parameters must return UNEXPECTED_ARGUMENT."""
        payload = {"tool": "add", "arguments": {"a": 2, "b": 3, "c": 4}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNEXPECTED_ARGUMENT")
        self.assertIn("c", res["error"]["details"]["unexpected_parameters"])

    def test_invalid_arguments_type(self) -> None:
        """Arguments must be a JSON object (dict), not a list or primitive."""
        payload = {"tool": "add", "arguments": [2, 3]}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS_OBJECT")

    def test_missing_tool_name(self) -> None:
        """Missing or empty tool property must return MISSING_TOOL_NAME."""
        payload = {"arguments": {"a": 2, "b": 3}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "MISSING_TOOL_NAME")


class TestToolAllowlist(unittest.TestCase):
    """Test explicit allowlist enforcement."""

    def setUp(self) -> None:
        self.dispatcher = TypedToolDispatcher()

    def test_unknown_tool_rejected(self) -> None:
        """Unknown tool must return UnknownToolError with allowed tools list."""
        for unknown in ["divide", "subtract", "power", "system_exec"]:
            payload = {"tool": unknown, "arguments": {"a": 6, "b": 2}}
            res = self.dispatcher.dispatch(payload)
            self.assertEqual(res["status"], "error")
            self.assertEqual(res["error"]["type"], "UnknownToolError")
            self.assertEqual(res["error"]["code"], "TOOL_NOT_ALLOWED")
            self.assertEqual(res["error"]["details"]["tool"], unknown)
            self.assertEqual(res["error"]["details"]["allowed_tools"], ["add", "multiply"])


class TestPipelineExecutionAndFailureIsolation(unittest.TestCase):
    """Test multi-step pipeline execution and failure halting."""

    def setUp(self) -> None:
        self.adapter = DeterministicOfflineAdapter()
        self.dispatcher = TypedToolDispatcher(backend=self.adapter)

    def test_successful_pipeline(self) -> None:
        """A pipeline of valid calls executes all steps successfully."""
        pipeline = [
            {"tool": "add", "arguments": {"a": 2, "b": 3}},
            {"tool": "multiply", "arguments": {"a": 4, "b": 5}},
        ]
        res = self.dispatcher.dispatch_pipeline(pipeline)
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["pipeline_halted"])
        self.assertEqual(res["completed_steps"], 2)
        self.assertEqual(len(res["executed_results"]), 2)
        self.assertEqual(res["executed_results"][0]["result"], 5)
        self.assertEqual(res["executed_results"][1]["result"], 20)
        self.assertEqual(self.adapter.call_count, 2)

    def test_pipeline_halts_on_first_failure(self) -> None:
        """
        Failure halting: A failed call cannot execute another tool.
        Subsequent calls must be aborted and never invoked on the backend adapter.
        """
        pipeline = [
            {"tool": "add", "arguments": {"a": "invalid", "b": 3}},
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        ]
        res = self.dispatcher.dispatch_pipeline(pipeline)
        self.assertEqual(res["status"], "error")
        self.assertTrue(res["pipeline_halted"])
        self.assertEqual(res["failed_step_index"], 0)
        self.assertEqual(res["completed_steps"], 0)
        self.assertEqual(len(res["executed_results"]), 0)
        self.assertEqual(len(res["aborted_calls"]), 1)
        self.assertEqual(res["aborted_calls"][0]["tool"], "multiply")
        # Ensure backend adapter was NEVER called for multiply
        self.assertEqual(self.adapter.call_count, 0)

    def test_pipeline_halts_on_intermediate_failure(self) -> None:
        """Pipeline executes prior steps, but halts immediately on failure and aborts rest."""
        pipeline = [
            {"tool": "add", "arguments": {"a": 2, "b": 3}},
            {"tool": "unknown_tool", "arguments": {"a": 1, "b": 1}},
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        ]
        res = self.dispatcher.dispatch_pipeline(pipeline)
        self.assertEqual(res["status"], "error")
        self.assertTrue(res["pipeline_halted"])
        self.assertEqual(res["failed_step_index"], 1)
        self.assertEqual(res["completed_steps"], 1)
        self.assertEqual(len(res["executed_results"]), 1)
        self.assertEqual(res["executed_results"][0]["result"], 5)
        self.assertEqual(len(res["aborted_calls"]), 1)
        self.assertEqual(res["aborted_calls"][0]["tool"], "multiply")
        self.assertEqual(self.adapter.call_count, 1)


class TestCallableInterfaceAndAdapters(unittest.TestCase):
    """Test external dependency abstraction behind a callable interface."""

    def test_custom_callable_function(self) -> None:
        """A simple callable function or lambda can act as service backend."""
        def custom_backend(op: str, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
            if op == "add":
                return (a + b) * 10
            elif op == "multiply":
                return (a * b) * 10
            return 0

        dispatcher = TypedToolDispatcher(backend=custom_backend)
        res = dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 50)

    def test_deliberate_wrong_result_adapter_fails_expectation(self) -> None:
        """
        Deliberate wrong adapter produces 999;
        verifies that tests catching wrong results fail their assertions.
        """
        wrong_adapter = DeliberateWrongResultAdapter()
        dispatcher = TypedToolDispatcher(backend=wrong_adapter)
        res = dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 999)

        # Deliberate wrong assertion must raise AssertionError
        with self.assertRaises(AssertionError):
            self.assertEqual(res["result"], 5, "Expected 5, got wrong mock output 999")

    def test_faulty_backend_adapter_returns_structured_error(self) -> None:
        """Backend service errors are caught and returned in structured error envelopes."""
        faulty = FaultyServiceAdapter()
        dispatcher = TypedToolDispatcher(backend=faulty)
        res = dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["type"], "BackendServiceError")
        self.assertEqual(res["error"]["code"], "SERVICE_EXECUTION_FAILED")


class TestRealServiceGapsDocumentation(unittest.TestCase):
    """Test that real-service boundaries are documented and inspectable."""

    def test_all_service_gap_categories_present(self) -> None:
        """All expected categories of real-service gaps must be present."""
        expected_keys = [
            "network_latency_and_jitter",
            "transient_network_faults",
            "authentication_and_authorization",
            "rate_limiting_and_concurrency",
            "distributed_state_and_consistency",
            "remote_service_lifecycle_and_outages",
            "hardware_and_environment_heterogeneity",
            "llm_probabilistic_drift",
        ]
        for key in expected_keys:
            self.assertIn(key, REAL_SERVICE_GAPS)
            self.assertTrue(len(REAL_SERVICE_GAPS[key]["title"]) > 0)
            self.assertTrue(len(REAL_SERVICE_GAPS[key]["description"]) > 0)
            self.assertTrue(len(REAL_SERVICE_GAPS[key]["production_counterpart"]) > 0)

    def test_adapter_property_matches_real_service_gaps(self) -> None:
        adapter = DeterministicOfflineAdapter()
        self.assertEqual(adapter.unestablished_real_service_behaviors, REAL_SERVICE_GAPS)


class TestSubprocessCLI(unittest.TestCase):
    """Test fresh process invocation of example.py via subprocess."""

    def setUp(self) -> None:
        self.script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "example.py")
        )

    def _run_cli(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = [sys.executable, self.script_path] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_add_exit_0(self) -> None:
        res = self._run_cli(["--call", '{"tool": "add", "arguments": {"a": 2, "b": 3}}'])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"], 5)

    def test_cli_multiply_exit_0(self) -> None:
        res = self._run_cli(["--call", '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"], 6)

    def test_cli_unknown_tool_exit_1(self) -> None:
        res = self._run_cli(["--call", '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["type"], "UnknownToolError")

    def test_cli_string_argument_exit_1(self) -> None:
        res = self._run_cli(["--call", '{"tool": "add", "arguments": {"a": "2", "b": 3}}'])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["type"], "ValidationError")

    def test_cli_pipeline_halt_exit_1(self) -> None:
        pipeline_json = '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
        res = self._run_cli(["--pipeline", pipeline_json])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "error")
        self.assertTrue(data["pipeline_halted"])
        self.assertEqual(len(data["aborted_calls"]), 1)

    def test_cli_service_gaps_exit_0(self) -> None:
        res = self._run_cli(["--show-service-gaps"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("unestablished_behaviors", data)

    def test_cli_schema_exit_0(self) -> None:
        res = self._run_cli(["--show-schema"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("allowed_tools", data)

    def test_cli_deliberate_wrong_result_fails_assertion(self) -> None:
        res = self._run_cli([
            "--adapter", "deliberate-wrong",
            "--call", '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
        ])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["result"], 999)
        with self.assertRaises(AssertionError):
            self.assertEqual(data["result"], 5)


if __name__ == "__main__":
    unittest.main()
