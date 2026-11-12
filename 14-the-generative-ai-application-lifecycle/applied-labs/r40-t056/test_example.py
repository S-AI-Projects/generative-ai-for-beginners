"""Unit tests for Lesson 14 launch configuration validation & redaction."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from example import (  # noqa: E402
    REDACTED_MARKER,
    SYNTHETIC_FIXTURES,
    redact_env_values,
    run_fixture_equivalence_suite,
    validate_launch_config,
    validate_launch_config_baseline,
)


class TestLaunchConfigValidationAndRedaction(unittest.TestCase):
    def test_valid_config_redacts_secrets_and_never_launches_process(self) -> None:
        with mock.patch("subprocess.Popen") as popen_mock, mock.patch(
            "subprocess.run"
        ) as run_mock:
            report = validate_launch_config(SYNTHETIC_FIXTURES["valid"])

        popen_mock.assert_not_called()
        run_mock.assert_not_called()
        self.assertTrue(report["simulation"])
        self.assertFalse(report["launched"])
        self.assertEqual(report["command"], "python3")
        self.assertEqual(report["args"], ["-m", "http.server", "8080"])
        self.assertEqual(report["env_keys"], ["APP_ENV", "API_KEY"])
        self.assertEqual(
            report["redacted_env"],
            {"APP_ENV": REDACTED_MARKER, "API_KEY": REDACTED_MARKER},
        )
        serialized = json.dumps(report)
        self.assertNotIn("synthetic-secret-value", serialized)
        self.assertNotIn("local-sim", serialized)

    def test_boundary_empty_args_array_and_empty_env(self) -> None:
        report = validate_launch_config(SYNTHETIC_FIXTURES["boundary_empty_args_and_env"])
        self.assertEqual(report["command"], "uvicorn")
        self.assertEqual(report["args"], [])
        self.assertEqual(report["env_keys"], [])
        self.assertEqual(report["redacted_env"], {})
        self.assertFalse(report["launched"])

    def test_failure_missing_command_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing or empty 'command'"):
            validate_launch_config(SYNTHETIC_FIXTURES["invalid_missing_command"])
        with self.assertRaisesRegex(ValueError, "Missing or empty 'command'"):
            validate_launch_config({"command": "   ", "args": [], "env": {}})

    def test_failure_single_string_args_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a single string"):
            validate_launch_config(SYNTHETIC_FIXTURES["invalid_string_args"])
        with self.assertRaises(ValueError):
            validate_launch_config({"command": "python3", "args": [123], "env": {}})

    def test_extracted_redact_env_values_and_invalid_env_cases(self) -> None:
        redacted = redact_env_values({"TOKEN": "abc", "EMPTY_VAL": ""})
        self.assertEqual(redacted, {"TOKEN": REDACTED_MARKER, "EMPTY_VAL": REDACTED_MARKER})

        with self.assertRaises(ValueError):
            redact_env_values(["NOT_A_MAP"])
        with self.assertRaises(ValueError):
            redact_env_values({"": "val"})
        with self.assertRaises(ValueError):
            redact_env_values({"PORT": 8080})

    def test_before_after_baseline_equivalence_across_all_fixtures(self) -> None:
        suite = run_fixture_equivalence_suite("all")
        self.assertTrue(suite["all_equivalent"])
        self.assertEqual(len(suite["cases"]), len(SYNTHETIC_FIXTURES))

        for name, fixture in SYNTHETIC_FIXTURES.items():
            with self.subTest(case=name):
                try:
                    expected = validate_launch_config_baseline(fixture)
                except ValueError as baseline_exc:
                    with self.assertRaises(ValueError) as ref_ctx:
                        validate_launch_config(fixture)
                    self.assertEqual(str(ref_ctx.exception), str(baseline_exc))
                else:
                    actual = validate_launch_config(fixture)
                    self.assertEqual(actual, expected)

    def test_fresh_process_cli_normal_and_failure_exits(self) -> None:
        script = LAB_DIR / "example.py"

        all_proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
        )
        all_payload = json.loads(all_proc.stdout)
        self.assertTrue(all_payload["simulation"])
        self.assertTrue(all_payload["all_equivalent"])

        valid_proc = subprocess.run(
            [sys.executable, str(script), "--case", "valid"],
            capture_output=True,
            text=True,
            check=True,
        )
        valid_payload = json.loads(valid_proc.stdout)
        self.assertTrue(valid_payload["equivalent"])
        self.assertNotIn("synthetic-secret-value", valid_proc.stdout)

        for bad_case in ("invalid_missing_command", "invalid_string_args"):
            fail_proc = subprocess.run(
                [sys.executable, str(script), "--case", bad_case],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(fail_proc.returncode, 0)
            self.assertIn("Error:", fail_proc.stderr)


if __name__ == "__main__":
    unittest.main()
