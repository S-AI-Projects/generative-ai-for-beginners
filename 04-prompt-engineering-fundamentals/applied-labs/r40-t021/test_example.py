"""Unit tests for R40-T021 prompt-template escaping and validation example."""

import json
import os
import subprocess
import sys
import unittest

# Ensure current directory is in sys.path for direct imports
sys.path.insert(0, os.path.dirname(__file__))

from example import (
    DECLARED_VARIABLES,
    DEFAULT_TEMPLATE,
    FIXED_INSTRUCTION,
    render_prompt,
    validate_variables,
)


class TestPromptTemplateEscaping(unittest.TestCase):
    """Test suite covering template rendering, schema validation, and boundary conditions."""

    def test_render_prompt_normal(self):
        """Normal scenario: Template renders supplied name and topic."""
        variables = {"name": "Alice", "topic": "Photosynthesis"}
        result = render_prompt(variables)

        self.assertIn(FIXED_INSTRUCTION, result)
        self.assertIn("Student Name: Alice", result)
        self.assertIn("Topic: Photosynthesis", result)
        self.assertIn("### INSTRUCTION", result)
        self.assertIn("### CONTEXT (USER DATA)", result)

    def test_render_prompt_missing_topic_fails(self):
        """Failure scenario: Missing 'topic' raises ValueError."""
        variables = {"name": "Alice"}
        with self.assertRaises(ValueError) as ctx:
            render_prompt(variables)
        self.assertIn("topic", str(ctx.exception))
        self.assertIn("Missing required", str(ctx.exception))

    def test_render_prompt_missing_name_fails(self):
        """Failure scenario: Missing 'name' raises ValueError."""
        variables = {"topic": "Photosynthesis"}
        with self.assertRaises(ValueError) as ctx:
            render_prompt(variables)
        self.assertIn("name", str(ctx.exception))
        self.assertIn("Missing required", str(ctx.exception))

    def test_render_prompt_missing_all_variables_fails(self):
        """Failure scenario: Empty variables dict raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            render_prompt({})
        err_msg = str(ctx.exception)
        self.assertIn("name", err_msg)
        self.assertIn("topic", err_msg)

    def test_render_prompt_unknown_variable_fails(self):
        """Failure scenario: Unknown variables outside declared schema raise ValueError."""
        variables = {
            "name": "Alice",
            "topic": "Photosynthesis",
            "role": "admin",
            "malicious_field": "drop database",
        }
        with self.assertRaises(ValueError) as ctx:
            render_prompt(variables)
        err_msg = str(ctx.exception)
        self.assertIn("Unknown variable(s)", err_msg)
        self.assertIn("role", err_msg)
        self.assertIn("malicious_field", err_msg)

    def test_braces_inside_user_data_remain_literal(self):
        """Boundary scenario: Braces inside user values remain literal without parsing error."""
        variables = {
            "name": "Alice {class_of_2026}",
            "topic": "Sets: {x | x > 0} and Code: {return true;}",
        }
        result = render_prompt(variables)

        # Ensure literal braces were not stripped, formatted away, or evaluated
        self.assertIn("Student Name: Alice {class_of_2026}", result)
        self.assertIn("Topic: Sets: {x | x > 0} and Code: {return true;}", result)

    def test_no_recursive_expansion_of_placeholders(self):
        """Boundary scenario: Variable value matching placeholder syntax is not recursively expanded."""
        variables = {
            "name": "{topic}",
            "topic": "Calculus",
        }
        result = render_prompt(variables)

        # Single-pass substitution guarantees {topic} in name value is not replaced with 'Calculus'
        self.assertIn("Student Name: {topic}", result)
        self.assertIn("Topic: Calculus", result)

    def test_instruction_and_data_boundary_separation(self):
        """Structural test: User data remains confined within delimited context section."""
        variables = {"name": "Bob", "topic": "Robotics"}
        result = render_prompt(variables)

        instruction_idx = result.find("### INSTRUCTION")
        context_idx = result.find("### CONTEXT (USER DATA)")
        name_idx = result.find("Student Name: Bob")
        topic_idx = result.find("Topic: Robotics")

        self.assertNotEqual(instruction_idx, -1)
        self.assertNotEqual(context_idx, -1)
        self.assertLess(instruction_idx, context_idx)
        self.assertLess(context_idx, name_idx)
        self.assertLess(name_idx, topic_idx)

    def test_non_dict_variables_type_error(self):
        """Failure scenario: Non-dict variables argument raises TypeError."""
        with self.assertRaises(TypeError):
            render_prompt(["name", "Alice"])

    def test_non_string_value_type_error(self):
        """Failure scenario: Non-string variable values raise TypeError."""
        with self.assertRaises(TypeError) as ctx:
            render_prompt({"name": 12345, "topic": "History"})
        self.assertIn("Variable 'name' must be a string", str(ctx.exception))


class TestCLIExecution(unittest.TestCase):
    """Integration test suite executing example.py as a standalone subprocess."""

    def setUp(self):
        self.example_script = os.path.join(os.path.dirname(__file__), "example.py")

    def test_cli_normal_execution(self):
        """CLI normal execution with --name and --topic exits 0 and returns valid JSON."""
        cmd = [
            sys.executable,
            self.example_script,
            "--name",
            "Alice",
            "--topic",
            "Photosynthesis",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertIn("rendered_prompt", data)
        self.assertIn("Student Name: Alice", data["rendered_prompt"])
        self.assertIn("Topic: Photosynthesis", data["rendered_prompt"])

    def test_cli_missing_topic_fails(self):
        """CLI failure scenario: Missing --topic exits non-zero."""
        cmd = [
            sys.executable,
            self.example_script,
            "--name",
            "Alice",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ValueError", proc.stderr)
        self.assertIn("topic", proc.stderr)

    def test_cli_boundary_literal_braces(self):
        """CLI boundary execution: Preserves literal braces in user inputs."""
        cmd = [
            sys.executable,
            self.example_script,
            "--name",
            "Alice {Student-42}",
            "--topic",
            "Sets: {x | x > 0}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertIn("Alice {Student-42}", data["rendered_prompt"])
        self.assertIn("Sets: {x | x > 0}", data["rendered_prompt"])

    def test_cli_unknown_key_fails(self):
        """CLI failure scenario: Passing unknown keys via --data exits non-zero."""
        cmd = [
            sys.executable,
            self.example_script,
            "--data",
            json.dumps({"name": "Alice", "topic": "Math", "extra_arg": "invalid"}),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ValueError", proc.stderr)
        self.assertIn("extra_arg", proc.stderr)


if __name__ == "__main__":
    unittest.main()
