import unittest

from example import ChatMessage


class ChatMessageTests(unittest.TestCase):
    def test_two_chunks_complete_in_order(self):
        message = ChatMessage("message-001")
        message.start()
        message.append_chunk("Hello ")
        message.append_chunk("world")
        message.complete()

        self.assertEqual(message.text, "Hello world")
        self.assertEqual(message.state, "complete")
        self.assertEqual(message.message_id, "message-001")

    def test_error_preserves_received_text(self):
        message = ChatMessage("message-002")
        message.start()
        message.append_chunk("Partial result")
        message.fail("Connection lost")

        self.assertEqual(message.text, "Partial result")
        self.assertEqual(message.state, "error")
        self.assertEqual(message.error, "Connection lost")

    def test_chunk_after_completion_is_rejected(self):
        message = ChatMessage("message-003")
        message.start()
        message.append_chunk("Finished")
        message.complete()

        with self.assertRaises(ValueError):
            message.append_chunk("Late text")

        self.assertEqual(message.text, "Finished")

    def test_chunk_after_error_is_rejected(self):
        message = ChatMessage("message-004")
        message.start()
        message.append_chunk("Partial")
        message.fail("Connection lost")

        with self.assertRaises(ValueError):
            message.append_chunk("Late text")

        self.assertEqual(message.text, "Partial")

    def test_cannot_complete_before_streaming(self):
        message = ChatMessage("message-005")

        with self.assertRaises(ValueError):
            message.complete()

    def test_cannot_start_twice(self):
        message = ChatMessage("message-006")
        message.start()

        with self.assertRaises(ValueError):
            message.start()


if __name__ == "__main__":
    unittest.main()
