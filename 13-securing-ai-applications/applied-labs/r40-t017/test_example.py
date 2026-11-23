import unittest

from example import PolicyError, run_action


class ActionPolicyTests(unittest.TestCase):

    def test_allowed_read_reaches_executor(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))
            return "MOCK READ: " + arguments["path"]

        action = {
            "tool": "read",
            "arguments": {"path": "notes.txt"},
        }

        result = run_action(action, executor)

        self.assertEqual(result, "MOCK READ: notes.txt")
        self.assertEqual(
            calls,
            [("read", {"path": "notes.txt"})],
        )

    def test_unknown_delete_never_reaches_executor(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))

        action = {
            "tool": "delete",
            "arguments": {"path": "notes.txt"},
        }

        with self.assertRaisesRegex(PolicyError, "Tool is not allowed"):
            run_action(action, executor)

        self.assertEqual(calls, [])

    def test_missing_path_never_reaches_executor(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))

        action = {
            "tool": "read",
            "arguments": {},
        }

        with self.assertRaisesRegex(
            PolicyError, "Missing required argument: path"
        ):
            run_action(action, executor)

        self.assertEqual(calls, [])

    def test_unknown_argument_is_rejected(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))

        action = {
            "tool": "read",
            "arguments": {
                "path": "notes.txt",
                "extra": "unexpected",
            },
        }

        with self.assertRaisesRegex(PolicyError, "Unknown argument"):
            run_action(action, executor)

        self.assertEqual(calls, [])

    def test_non_string_path_is_rejected(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))

        action = {
            "tool": "read",
            "arguments": {"path": 123},
        }

        with self.assertRaisesRegex(PolicyError, "must be a string"):
            run_action(action, executor)

        self.assertEqual(calls, [])

    def test_empty_path_is_rejected(self):
        calls = []

        def executor(tool, arguments):
            calls.append((tool, arguments))

        action = {
            "tool": "read",
            "arguments": {"path": "   "},
        }

        with self.assertRaisesRegex(PolicyError, "cannot be empty"):
            run_action(action, executor)

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
