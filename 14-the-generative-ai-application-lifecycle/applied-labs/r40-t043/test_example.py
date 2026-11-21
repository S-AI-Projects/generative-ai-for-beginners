"""
R40-T043 · Test suite for example.py
======================================

Covers:
  1. Contract requirements:
     - Missing command fails with ValueError.
     - Single string where argument array is required fails with TypeError.
     - Valid record produces a redacted summary without launching the process.
  2. Redaction verification:
     - Environment variable values are redacted ([REDACTED]), not exposed.
  3. Focus requirement:
     - Compare the direct implementation with an independent calculation/oracle table
       using identical inputs.
  4. Boundary scenarios:
     - Empty argument list, empty env dictionary, sorting of env keys.
  5. Deliberate wrong result verification:
     - Ensures checker fails with AssertionError if expected results are modified.
"""

import unittest

from example import (
    REDACTED_MARKER,
    LaunchSummary,
    reference_oracle_table,
    validate_launch_config,
)


class TestLaunchConfigContract(unittest.TestCase):
    """
    Primary contract verification:
      - Valid record produces a redacted summary without launching the process.
      - Missing command fails.
      - Single string where argument array is required fails.
    """

    def test_valid_record_produces_redacted_summary(self):
        config = {
            "command": "uvicorn",
            "args": ["app:api", "--port", "8000", "--host", "0.0.0.0"],
            "env": {
                "AZURE_OPENAI_API_KEY": "sk-secret-token-xyz-12345",
                "ENDPOINT": "https://example.openai.azure.com",
            },
        }
        summary = validate_launch_config(config)

        self.assertEqual(summary.command, "uvicorn")
        self.assertEqual(summary.args, ("app:api", "--port", "8000", "--host", "0.0.0.0"))
        self.assertEqual(summary.env_keys, ("AZURE_OPENAI_API_KEY", "ENDPOINT"))
        self.assertFalse(summary.process_launched)

        # Redaction check: real secrets must NOT appear anywhere in the summary
        self.assertEqual(summary.redacted_env["AZURE_OPENAI_API_KEY"], REDACTED_MARKER)
        self.assertEqual(summary.redacted_env["ENDPOINT"], REDACTED_MARKER)
        self.assertNotIn("sk-secret-token-xyz-12345", str(summary))

    def test_missing_command_fails(self):
        # Missing key
        with self.assertRaises(ValueError) as ctx:
            validate_launch_config({"args": ["--port", "8000"]})
        self.assertIn("Missing required 'command'", str(ctx.exception))

        # None command
        with self.assertRaises(ValueError):
            validate_launch_config({"command": None, "args": []})

        # Empty/whitespace command
        with self.assertRaises(ValueError):
            validate_launch_config({"command": "   ", "args": []})

    def test_single_string_where_array_required_fails(self):
        # Explicit contract requirement: single string where argument array required fails
        config = {
            "command": "python",
            "args": "-m http.server 8080",  # Single string instead of list/tuple
        }
        with self.assertRaises(TypeError) as ctx:
            validate_launch_config(config)
        self.assertIn("received a single string", str(ctx.exception))
        self.assertIn("strictly required", str(ctx.exception))

    def test_deliberate_wrong_command_fails(self):
        """Checker must fail if command assertion is modified."""
        summary = validate_launch_config({"command": "ollama", "args": ["run", "phi3"]})
        with self.assertRaises(AssertionError):
            self.assertEqual(summary.command, "vllm", "Intentional failure: ollama != vllm.")

    def test_deliberate_wrong_redaction_fails(self):
        """Checker must fail if unredacted secret is falsely claimed to match marker."""
        summary = validate_launch_config({
            "command": "python",
            "args": ["serve.py"],
            "env": {"API_KEY": "raw_secret"},
        })
        with self.assertRaises(AssertionError):
            self.assertEqual(summary.redacted_env["API_KEY"], "raw_secret",
                             "Intentional failure: secret should be [REDACTED].")


class TestIndependentOracleComparison(unittest.TestCase):
    """
    Focus requirement:
      Compare the direct implementation with a simpler independent calculation
      or explicit expected-result table, using identical inputs.
    """

    TEST_FIXTURES = [
        (
            "Fixture 1: Standard inference server",
            {"command": "uvicorn", "args": ["main:app", "--port", "8000"], "env": {"KEY": "val"}},
            "uvicorn",
            ["main:app", "--port", "8000"],
            ["KEY"],
        ),
        (
            "Fixture 2: Multi-flag command with multiple secrets",
            {"command": "vllm", "args": ["serve", "--model", "phi-4"], "env": {"SECRET_A": "1", "SECRET_B": "2"}},
            "vllm",
            ["serve", "--model", "phi-4"],
            ["SECRET_A", "SECRET_B"],
        ),
        (
            "Fixture 3: Empty arguments and empty env",
            {"command": "ollama", "args": [], "env": {}},
            "ollama",
            [],
            [],
        ),
    ]

    def test_comparison_with_independent_oracle(self):
        for desc, input_config, expected_cmd, expected_args, expected_env_keys in self.TEST_FIXTURES:
            with self.subTest(description=desc):
                # 1. Run direct implementation
                direct_result = validate_launch_config(input_config)

                # 2. Run independent reference calculation on identical inputs
                oracle_result = reference_oracle_table(
                    command=expected_cmd,
                    args=expected_args,
                    env_keys=expected_env_keys,
                )

                # 3. Formally verify full equivalence
                self.assertEqual(direct_result.command, oracle_result["command"])
                self.assertEqual(direct_result.args, oracle_result["args"])
                self.assertEqual(direct_result.env_keys, oracle_result["env_keys"])
                self.assertEqual(direct_result.redacted_env, oracle_result["redacted_env"])
                self.assertEqual(direct_result.formatted_command, oracle_result["formatted_command"])
                self.assertEqual(direct_result.process_launched, oracle_result["process_launched"])


class TestBoundaryScenarios(unittest.TestCase):
    """Boundary conditions: empty args list, whitespace stripping, missing env."""

    def test_empty_args_list_allowed(self):
        summary = validate_launch_config({"command": "echo", "args": []})
        self.assertEqual(summary.args, ())
        self.assertEqual(summary.formatted_command, "echo")

    def test_missing_env_defaults_to_empty(self):
        summary = validate_launch_config({"command": "ls", "args": ["-la"]})
        self.assertEqual(summary.env_keys, ())
        self.assertEqual(summary.redacted_env, {})

    def test_non_string_arg_in_array_fails(self):
        with self.assertRaises(TypeError) as ctx:
            validate_launch_config({"command": "python", "args": ["script.py", 123]})
        self.assertIn("must be a string", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
