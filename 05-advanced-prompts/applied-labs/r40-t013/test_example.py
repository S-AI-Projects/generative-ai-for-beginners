
import subprocess
import sys
import unittest
from pathlib import Path

from example import (
    TEMPLATE,
    check_expected,
    render_regex,
    render_scan,
)


class TemplateTests(unittest.TestCase):

    def test_normal_input(self):
        expected = "Hello Asha. Explain Photosynthesis clearly."
        values = {"name": "Asha", "topic": "Photosynthesis"}

        self.assertEqual(render_regex(TEMPLATE, values), expected)

    def test_boundary_braces_remain_literal(self):
        expected = "Hello Asha {{admin}}. Explain Maths {advanced} clearly."
        values = {"name": "Asha {{admin}}", "topic": "Maths {advanced}"}

        self.assertEqual(render_regex(TEMPLATE, values), expected)

    def test_both_approaches_match_normal_input(self):
        values = {"name": "Asha", "topic": "Maths"}

        self.assertEqual(
            render_regex(TEMPLATE, values),
            render_scan(TEMPLATE, values)
        )

    def test_both_approaches_match_boundary_input(self):
        values = {"name": "Asha {{admin}}", "topic": "Maths {advanced}"}

        self.assertEqual(
            render_regex(TEMPLATE, values),
            render_scan(TEMPLATE, values)
        )

    def test_missing_topic_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing keys"):
            render_regex(TEMPLATE, {"name": "Asha"})

    def test_unknown_key_is_rejected(self):
        values = {"name": "Asha", "topic": "Maths", "extra": "value"}

        with self.assertRaisesRegex(ValueError, "Unknown keys"):
            render_regex(TEMPLATE, values)

    def test_unknown_template_placeholder_is_rejected(self):
        template = "Hello {{name}}. Explain {{topic}}. {{admin}}"

        with self.assertRaises(ValueError):
            render_regex(template, {"name": "Asha", "topic": "Maths"})

    def test_non_string_value_is_rejected(self):
        with self.assertRaises(ValueError):
            render_regex(TEMPLATE, {"name": "Asha", "topic": 123})

    def test_deliberately_wrong_expected_result_fails(self):
        actual = render_regex(
            TEMPLATE, {"name": "Asha", "topic": "Maths"}
        )

        with self.assertRaises(AssertionError):
            check_expected(actual, "This is deliberately incorrect.")

    def test_missing_scenario_fails_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("example.py")), "--scenario", "missing"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing keys", result.stderr)

    def test_unknown_scenario_fails_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("example.py")), "--scenario", "unknown"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown keys", result.stderr)

if __name__ == "__main__":
    unittest.main()

