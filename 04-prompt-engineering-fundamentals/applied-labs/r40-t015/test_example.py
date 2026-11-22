
import subprocess
import sys
import unittest
from pathlib import Path
import importlib.util

EXAMPLE_FILE = Path(__file__).with_name("example.py")

spec = importlib.util.spec_from_file_location("example", EXAMPLE_FILE)
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)

TEMPLATE = example.TEMPLATE
LocalServiceAdapter = example.LocalServiceAdapter
render_template = example.render_template
run_prompt = example.run_prompt


class PromptTemplateTests(unittest.TestCase):

    def test_normal_template_rendering(self):
        result = render_template(
            TEMPLATE,
            {"name": "Asha", "topic": "fractions"},
        )
        self.assertEqual(
            result,
            "Fixed instruction: Explain the topic 'fractions' clearly to Asha.",
        )

    def test_missing_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing keys"):
            render_template(TEMPLATE, {"name": "Asha"})

    def test_unknown_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown keys"):
            render_template(
                TEMPLATE,
                {
                    "name": "Asha",
                    "topic": "fractions",
                    "extra": "unexpected",
                },
            )

    def test_braces_in_user_data_remain_literal(self):
        result = render_template(
            TEMPLATE,
            {
                "name": "Asha {admin}",
                "topic": "fractions {level}",
            },
        )
        self.assertIn("Asha {admin}", result)
        self.assertIn("fractions {level}", result)

    def test_non_string_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be a string"):
            render_template(
                TEMPLATE,
                {"name": "Asha", "topic": 123},
            )

    def test_local_adapter_is_deterministic(self):
        adapter = LocalServiceAdapter()
        first = adapter("Hello")
        second = adapter("Hello")
        self.assertEqual(first, second)
        self.assertEqual(first, "LOCAL MOCK RESPONSE: Hello")

    def test_service_is_called_with_rendered_prompt(self):
        received = []

        def fake_service(prompt):
            received.append(prompt)
            return "Test response"

        result = run_prompt(
            TEMPLATE,
            {"name": "Asha", "topic": "fractions"},
            fake_service,
        )
        self.assertEqual(received, [result["rendered_prompt"]])
        self.assertEqual(result["service_response"], "Test response")

    def test_normal_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "normal"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("fractions", result.stdout)

    def test_boundary_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "boundary"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("{admin}", result.stdout)
        self.assertIn("{level}", result.stdout)

    def test_failure_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "failure"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing keys", result.stderr)


if __name__ == "__main__":
    unittest.main()

