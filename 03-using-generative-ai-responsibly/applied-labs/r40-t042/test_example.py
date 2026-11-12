
import unittest

from example import process_action, EXECUTOR_CALLS


class TestActionValidation(unittest.TestCase):

    def setUp(self):
        EXECUTOR_CALLS.clear()

    def test_valid_read(self):
        action = {
            "tool": "read",
            "arguments": {"path": "notes.txt"}
        }

        result = process_action(action)

        self.assertEqual(result, "This is a sample local file.")
        self.assertEqual(len(EXECUTOR_CALLS), 1)

    def test_unknown_delete_tool(self):
        action = {
            "tool": "delete",
            "arguments": {"path": "notes.txt"}
        }

        result = process_action(action)

        self.assertEqual(result, "Tool not allowed")
        self.assertEqual(len(EXECUTOR_CALLS), 0)

    def test_missing_required_argument(self):
        action = {
            "tool": "read",
            "arguments": {}
        }

        result = process_action(action)

        self.assertEqual(
            result,
            "Missing required argument: path"
        )
        self.assertEqual(len(EXECUTOR_CALLS), 0)

    def test_invalid_path(self):
        action = {
            "tool": "read",
            "arguments": {"path": "unknown.txt"}
        }

        result = process_action(action)

        self.assertEqual(result, "Invalid path")
        self.assertEqual(len(EXECUTOR_CALLS), 0)


if __name__ == "__main__":
    unittest.main()

