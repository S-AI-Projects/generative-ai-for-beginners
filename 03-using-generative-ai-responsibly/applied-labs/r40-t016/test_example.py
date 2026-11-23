import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


EXAMPLE_FILE = Path(__file__).with_name("example.py")
spec = importlib.util.spec_from_file_location("example", EXAMPLE_FILE)
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


class ActionPolicyTests(unittest.TestCase):

    def test_valid_read_is_allowed(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))
            return "MOCK READ: notes.txt"

        result = example.refactored_process(
            {"tool": "read", "arguments": {"path": "notes.txt"}},
            executor,
        )

        self.assertTrue(result["allowed"])
        self.assertEqual(result["result"], "MOCK READ: notes.txt")
        self.assertEqual(len(calls), 1)

    def test_unknown_delete_is_rejected_without_execution(self):
        calls = []

        result = example.refactored_process(
            {"tool": "delete", "arguments": {"path": "notes.txt"}},
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "Unknown tool")
        self.assertEqual(calls, [])

    def test_missing_path_is_rejected_without_execution(self):
        calls = []

        result = example.refactored_process(
            {"tool": "read", "arguments": {}},
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertIn("Missing required arguments", result["reason"])
        self.assertEqual(calls, [])

    def test_empty_path_is_rejected(self):
        calls = []

        result = example.refactored_process(
            {"tool": "read", "arguments": {"path": ""}},
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(calls, [])

    def test_unknown_argument_is_rejected(self):
        calls = []

        result = example.refactored_process(
            {
                "tool": "read",
                "arguments": {"path": "notes.txt", "admin": True},
            },
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(calls, [])

    def test_wrong_argument_type_is_rejected(self):
        calls = []

        result = example.refactored_process(
            {"tool": "read", "arguments": {"path": 123}},
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(calls, [])

    def test_baseline_and_refactor_are_equivalent(self):
        fixtures = [
            example.FIXTURES["normal"],
            example.FIXTURES["boundary"],
            example.FIXTURES["failure"],
            {"tool": "read", "arguments": {"path": ""}},
        ]

        for action in fixtures:
            baseline_calls = []
            refactored_calls = []

            def baseline_executor(tool, arguments):
                baseline_calls.append((tool, arguments.copy()))
                return example.mock_executor(tool, arguments)

            def refactored_executor(tool, arguments):
                refactored_calls.append((tool, arguments.copy()))
                return example.mock_executor(tool, arguments)

            baseline = example.baseline_process(action, baseline_executor)
            refactored = example.refactored_process(action, refactored_executor)

            self.assertEqual(baseline, refactored)
            self.assertEqual(baseline_calls, refactored_calls)

    def test_baseline_rejects_without_execution(self):
        calls = []

        result = example.baseline_process(
            example.FIXTURES["boundary"],
            lambda tool, arguments: calls.append(tool),
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(calls, [])

    def test_normal_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "normal"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("MOCK READ: notes.txt", result.stdout)

    def test_boundary_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "boundary"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Unknown tool", result.stdout)
        self.assertIn('"allowed": false', result.stdout)

    def test_failure_scenario_in_fresh_process(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_FILE), "--scenario", "failure"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Missing required arguments", result.stdout)

    def test_deliberately_wrong_assertion_fails(self):
        code = (
            "import unittest\n"
            "class WrongTest(unittest.TestCase):\n"
            " def test_wrong(self):\n"
            "  self.assertEqual('actual', 'wrong')\n"
            "suite = unittest.defaultTestLoader.loadTestsFromTestCase(WrongTest)\n"
            "result = unittest.TextTestRunner().run(suite)\n"
            "raise SystemExit(0 if result.wasSuccessful() else 1)\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAILED", result.stderr)


if __name__ == "__main__":
    unittest.main()
