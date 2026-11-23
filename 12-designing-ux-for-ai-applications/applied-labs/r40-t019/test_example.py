import unittest

from example import ChatMessage, run_evaluation


class TestChatMessage(unittest.TestCase):

    def test_message_starts_pending_with_stable_id(self):
        message = ChatMessage("msg-001")

        self.assertEqual(message.message_id, "msg-001")
        self.assertEqual(message.status, "pending")

    def test_two_chunks_are_appended_in_order(self):
        message = ChatMessage("msg-002")

        message.append_chunk("msg-002", "Hello ")
        message.append_chunk("msg-002", "there!")

        self.assertEqual(message.text, "Hello there!")
        self.assertEqual(message.status, "streaming")

    def test_response_can_be_completed(self):
        message = ChatMessage("msg-003")

        message.append_chunk("msg-003", "Done")
        message.complete("msg-003")

        self.assertEqual(message.status, "complete")

    def test_error_preserves_received_text(self):
        message = ChatMessage("msg-004")

        message.append_chunk("msg-004", "Partial text")
        message.fail("msg-004", "Connection interrupted")

        result = message.display()

        self.assertEqual(result["text"], "Partial text")
        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["error_marker"],
            "Connection interrupted"
        )

    def test_chunk_after_completion_is_rejected(self):
        message = ChatMessage("msg-005")
        message.complete("msg-005")

        with self.assertRaises(ValueError):
            message.append_chunk("msg-005", "Too late")

    def test_chunk_after_error_is_rejected(self):
        message = ChatMessage("msg-006")
        message.fail("msg-006", "Failed")

        with self.assertRaises(ValueError):
            message.append_chunk("msg-006", "Too late")

    def test_unknown_message_id_is_rejected(self):
        message = ChatMessage("msg-007")

        with self.assertRaises(ValueError):
            message.append_chunk("wrong-id", "Hello")

    def test_evaluation_uses_three_configurations(self):
        configurations = [
            ("small", ["Hi"]),
            ("medium", ["Hello ", "there!"]),
            ("large", ["This ", "is ", "a ", "longer ", "response."]),
        ]

        self.assertEqual(len(configurations), 3)

        for name, chunks in configurations:
            message = ChatMessage("eval-" + name)

            for chunk in chunks:
                message.append_chunk(message.message_id, chunk)

            message.complete(message.message_id)

            self.assertEqual(message.status, "complete")
            self.assertEqual(message.text, "".join(chunks))


if __name__ == "__main__":
    unittest.main()
