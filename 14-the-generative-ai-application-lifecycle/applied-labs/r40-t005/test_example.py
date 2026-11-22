#!/usr/bin/env python3
"""Regression and invariant test suite for R40-T005.

Lesson 14: The Generative AI Application Lifecycle
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    UNESTABLISHED_REAL_BEHAVIORS,
    ConfigurationValidationError,
    DecisionMismatchError,
    OfflineServiceAdapter,
    run_canonical_check,
    run_missing_command_scenario,
    run_normal_scenario,
    run_string_arguments_scenario,
    validate_server_config,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestConfigValidationContract(unittest.TestCase):
    """Core configuration validation requirements."""

    def test_missing_command_fails(self) -> None:
        """Missing or empty command raises ConfigurationValidationError."""
        with self.assertRaises(ConfigurationValidationError):
            validate_server_config({"arguments": ["--port", "8000"]})
        with self.assertRaises(ConfigurationValidationError):
            validate_server_config({"command": "   ", "arguments": ["--port", "8000"]})

    def test_single_string_arguments_fails(self) -> None:
        """Single string where argument array is required raises ConfigurationValidationError."""
        with self.assertRaises(ConfigurationValidationError):
            validate_server_config({
                "command": "python3",
                "arguments": "-m uvicorn app:main --port 8000",
            })

    def test_non_list_arguments_fails(self) -> None:
        """Non-list arguments field raises ConfigurationValidationError."""
        with self.assertRaises(ConfigurationValidationError):
            validate_server_config({
                "command": "python3",
                "arguments": 12345,
            })

    def test_valid_config_produces_redacted_summary_without_process(self) -> None:
        """Valid configuration produces redacted summary and does not spawn process."""
        adapter = OfflineServiceAdapter()
        raw = {
            "command": "uvicorn",
            "arguments": ["app.main:app", "--port", "8000"],
            "environment": {
                "SECRET_KEY": "super-secret-token",
                "ENV": "production",
            },
        }
        res = adapter(raw)
        self.assertEqual(res["command"], "uvicorn")
        self.assertFalse(res["process_launched"])
        self.assertEqual(res["redacted_environment"]["SECRET_KEY"], "[REDACTED]")
        self.assertEqual(res["redacted_environment"]["ENV"], "[REDACTED]")
        self.assertEqual(len(res["unestablished_real_behaviors"]), len(UNESTABLISHED_REAL_BEHAVIORS))


class TestFocusCallableInterfaceAndLimitations(unittest.TestCase):
    """Focus: Encapsulation behind callable interface and unestablished behaviors."""

    def test_callable_adapter_interface(self) -> None:
        """OfflineServiceAdapter is callable and conforms to adapter protocol."""
        adapter = OfflineServiceAdapter()
        self.assertTrue(callable(adapter))
        res = adapter({"command": "echo", "arguments": ["hello"], "environment": {}})
        self.assertEqual(res["command"], "echo")

    def test_unestablished_real_behaviors_documented(self) -> None:
        """Adapter explicitly documents unestablished real-service behaviors."""
        adapter = OfflineServiceAdapter()
        res = adapter({"command": "server", "arguments": [], "environment": {}})
        behaviors = res["unestablished_real_behaviors"]
        self.assertTrue(any("EADDRINUSE" in b for b in behaviors))
        self.assertTrue(any("GPU memory" in b for b in behaviors))


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Canonical verification checks and deliberate tamper detection."""

    def test_canonical_check_passes(self) -> None:
        res = run_canonical_check(tamper=False)
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateWrongResult(unittest.TestCase):
    """Demonstrates that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI execution in fresh subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal(self) -> None:
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "CONFIG_VALID_REDACTED_SUMMARY")

    def test_cli_scenario_missing_cmd(self) -> None:
        res = self._run_cli(["--scenario", "missing_cmd"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "MISSING_COMMAND_REJECTED")

    def test_cli_scenario_string_args(self) -> None:
        res = self._run_cli(["--scenario", "string_args"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STRING_ARGS_REJECTED")

    def test_cli_check(self) -> None:
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")


if __name__ == "__main__":
    unittest.main()
