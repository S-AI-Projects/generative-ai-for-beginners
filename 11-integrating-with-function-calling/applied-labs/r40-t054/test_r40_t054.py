#!/usr/bin/env python3
"""Tests for the r40-t054 message-state + history-invariant example.

These tests exercise the stated contract:
  - normal scenario: two chunks append in order, identity stays stable
  - the task's focus: the intermediate state recorded after each step, and
    the invariant linking that recorded history to the final output
    (reconstruct_text_from_history(history) == message.text)
  - boundary scenarios: smallest valid case (zero chunks then complete),
    single chunk, exact terminal-state boundary
  - failure scenarios: chunks/completion/failure after finalize are
    rejected, and rejected steps do not grow history
  - a deliberately wrong result is rejected by assertion

Run from the repository root:
    python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t054 -p "test_*.py"
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from example import (  # noqa: E402
    State,
    append_chunk,
    complete_message,
    create_message,
    fail_message,
    reconstruct_text_from_history,
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


class RecordedStateInvariantScenario(unittest.TestCase):
    """This task's focus: record state after each step, test the invariant
    linking the recorded history to the final output."""

    def test_history_has_one_snapshot_per_successful_step(self):
        msg = create_message("msg-history")
        self.assertEqual(len(msg.history), 1)  # "create"
        append_chunk(msg, "a")
        self.assertEqual(len(msg.history), 2)
        append_chunk(msg, "b")
        self.assertEqual(len(msg.history), 3)
        complete_message(msg)
        self.assertEqual(len(msg.history), 4)

    def test_each_intermediate_snapshot_matches_live_state_at_that_point(self):
        msg = create_message("msg-intermediate")
        append_chunk(msg, "Here are some ")
        # The snapshot recorded by this step must match the live message's
        # state and text *at the moment it was taken*, not just at the end.
        self.assertEqual(msg.history[-1].text, "Here are some ")
        self.assertEqual(msg.history[-1].state, State.STREAMING)

        append_chunk(msg, "Azure courses.")
        self.assertEqual(msg.history[-1].text, "Here are some Azure courses.")
        self.assertEqual(msg.history[-1].state, State.STREAMING)

        complete_message(msg)
        self.assertEqual(msg.history[-1].text, "Here are some Azure courses.")
        self.assertEqual(msg.history[-1].state, State.COMPLETE)

    def test_reconstruction_invariant_holds_on_normal_completion(self):
        msg = create_message("msg-invariant-normal")
        append_chunk(msg, "Here are some ")
        append_chunk(msg, "Azure courses.")
        complete_message(msg)
        self.assertEqual(reconstruct_text_from_history(msg.history), msg.text)

    def test_reconstruction_invariant_holds_on_error(self):
        msg = create_message("msg-invariant-error")
        append_chunk(msg, "Here are some ")
        fail_message(msg, "upstream timeout")
        self.assertEqual(reconstruct_text_from_history(msg.history), msg.text)

    def test_reconstruction_invariant_holds_with_zero_chunks(self):
        msg = create_message("msg-invariant-empty")
        complete_message(msg)
        self.assertEqual(reconstruct_text_from_history(msg.history), "")
        self.assertEqual(reconstruct_text_from_history(msg.history), msg.text)

    def test_rejected_step_does_not_grow_history(self):
        msg = create_message("msg-rejected-history")
        complete_message(msg)
        history_len_before = len(msg.history)
        with self.assertRaises(ValueError):
            append_chunk(msg, "late chunk")
        self.assertEqual(len(msg.history), history_len_before)

    def test_wrong_reconstruction_is_not_silently_accepted(self):
        # A deliberately wrong reconstruction (dropping the second chunk)
        # must be rejected by the invariant check.
        msg = create_message("msg-invariant-wrong")
        append_chunk(msg, "Here are some ")
        append_chunk(msg, "Azure courses.")
        complete_message(msg)
        wrong_reconstruction = "Here are some "  # missing the second chunk
        self.assertNotEqual(wrong_reconstruction, msg.text)
        self.assertEqual(reconstruct_text_from_history(msg.history), msg.text)


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

    def test_empty_message_id_rejected(self):
        with self.assertRaises(ValueError):
            create_message("")


if __name__ == "__main__":
    unittest.main()
