#!/usr/bin/env python3
"""Tests for the r40-t052 message-state example.

These tests exercise the stated contract:
  - normal scenario: two chunks append in order, identity stays stable
  - boundary scenarios: smallest valid case (zero chunks, straight to
    complete), exactly one chunk, and the exact terminal-state boundary
  - failure scenarios: chunks/completion/failure after finalize are rejected
  - a deliberately wrong result is rejected by assertion

Run from the repository root:
    python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t052 -p "test_*.py"
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from example import (  # noqa: E402
    Message,
    State,
    append_chunk,
    complete_message,
    create_message,
    fail_message,
)


class NormalScenario(unittest.TestCase):
    """Two chunks append in order; message_id stays stable throughout."""

    def test_two_chunks_append_in_order(self):
        msg = create_message("msg-normal")
        append_chunk(msg, "Here are some ")
        append_chunk(msg, "Azure courses.")
        complete_message(msg)
        self.assertEqual(msg.text, "Here are some Azure courses.")
        self.assertEqual(msg.state, State.COMPLETE)

    def test_message_id_stable_across_transitions(self):
        msg = create_message("msg-stable")
        append_chunk(msg, "a")
        append_chunk(msg, "b")
        complete_message(msg)
        self.assertEqual(msg.message_id, "msg-stable")

    def test_wrong_chunk_order_is_not_silently_accepted(self):
        # A deliberately wrong expectation (reversed chunk order) must fail.
        msg = create_message("msg-order")
        append_chunk(msg, "Here are some ")
        append_chunk(msg, "Azure courses.")
        wrong_expected = "Azure courses.Here are some "
        self.assertNotEqual(msg.text, wrong_expected)
        self.assertEqual(msg.text, "Here are some Azure courses.")


class BoundaryScenario(unittest.TestCase):
    """Smallest valid case and exact terminal-state boundary."""

    def test_smallest_valid_case_zero_chunks_then_complete(self):
        msg = create_message("msg-empty")
        complete_message(msg)
        self.assertEqual(msg.text, "")
        self.assertEqual(msg.state, State.COMPLETE)

    def test_single_chunk_then_complete(self):
        msg = create_message("msg-one")
        append_chunk(msg, "only chunk")
        complete_message(msg)
        self.assertEqual(msg.text, "only chunk")
        self.assertEqual(msg.state, State.COMPLETE)

    def test_pending_accepts_first_chunk(self):
        msg = create_message("msg-pending")
        self.assertEqual(msg.state, State.PENDING)
        append_chunk(msg, "x")
        self.assertEqual(msg.state, State.STREAMING)

    def test_chunk_exactly_at_complete_boundary_is_rejected(self):
        # The instant a message becomes COMPLETE, it is terminal: this is
        # the exact boundary this fixture enforces.
        msg = create_message("msg-boundary")
        append_chunk(msg, "a")
        complete_message(msg)
        with self.assertRaises(ValueError):
            append_chunk(msg, "too late")


class ErrorScenario(unittest.TestCase):
    """An error preserves received text with an error marker."""

    def test_error_preserves_received_text_with_marker(self):
        msg = create_message("msg-error")
        append_chunk(msg, "Here are some ")
        fail_message(msg, "upstream timeout")
        self.assertEqual(msg.state, State.ERROR)
        self.assertTrue(msg.text.startswith("Here are some "))
        self.assertIn("[ERROR: upstream timeout]", msg.text)

    def test_error_with_no_prior_text_still_records_marker(self):
        msg = create_message("msg-error-empty")
        fail_message(msg, "connection refused")
        self.assertEqual(msg.text, "[ERROR: connection refused]")

    def test_error_reason_recorded(self):
        msg = create_message("msg-error-reason")
        fail_message(msg, "upstream timeout")
        self.assertEqual(msg.error, "upstream timeout")


class InvalidScenario(unittest.TestCase):
    """Chunks (or finalization) after completion/error are rejected."""

    def test_chunk_after_completion_rejected(self):
        msg = create_message("msg-after-complete")
        complete_message(msg)
        with self.assertRaises(ValueError):
            append_chunk(msg, "late chunk")

    def test_chunk_after_error_rejected(self):
        msg = create_message("msg-after-error")
        fail_message(msg, "boom")
        with self.assertRaises(ValueError):
            append_chunk(msg, "late chunk")

    def test_double_complete_rejected(self):
        msg = create_message("msg-double-complete")
        complete_message(msg)
        with self.assertRaises(ValueError):
            complete_message(msg)

    def test_complete_after_error_rejected(self):
        msg = create_message("msg-complete-after-error")
        fail_message(msg, "boom")
        with self.assertRaises(ValueError):
            complete_message(msg)

    def test_fail_after_completion_rejected(self):
        msg = create_message("msg-fail-after-complete")
        complete_message(msg)
        with self.assertRaises(ValueError):
            fail_message(msg, "too late")

    def test_empty_message_id_rejected(self):
        with self.assertRaises(ValueError):
            create_message("")


if __name__ == "__main__":
    unittest.main()
