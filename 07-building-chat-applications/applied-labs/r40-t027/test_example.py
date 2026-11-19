#!/usr/bin/env python3
"""Regression and invariant test suite for R40-T027.

Lesson 07: Building Generative AI-Powered Chat Applications.
Tests message identity stability, sequential streaming state transitions,
error recovery with received text preservation, and post-completion chunk rejection.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from example import (
    DEFAULT_ERROR_MESSAGE,
    DEFAULT_FIXTURE_CHUNKS,
    DEFAULT_LATE_CHUNK,
    DEFAULT_MESSAGE_ID,
    ChatResponseView,
    ChatViewStateError,
    ChatViewStateManager,
    ChunkRejectedError,
    DecisionMismatchError,
    IllegalStateTransitionError,
    ResponseState,
    run_boundary_scenario,
    run_canonical_check,
    run_error_scenario,
    run_normal_scenario,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestMessageIdentityAndPending(unittest.TestCase):
    """Validates stable message identity and initial PENDING invariants."""

    def test_init_pending_state(self) -> None:
        """Initial state must be PENDING with empty content and 0 chunks."""
        resp = ChatViewStateManager.create_response("msg-001")
        self.assertEqual(resp.message_id, "msg-001")
        self.assertEqual(resp.state, ResponseState.PENDING)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.chunks_received, 0)
        self.assertIsNone(resp.error_message)
        self.assertEqual(resp.role, "assistant")

    def test_stable_message_id_persists_across_all_lifecycle_steps(self) -> None:
        """Message ID must remain unchanged across PENDING, STREAMING, and COMPLETE."""
        stable_id = "msg-stable-999"
        manager = ChatViewStateManager()
        resp = manager.create_response(stable_id)
        self.assertEqual(resp.message_id, stable_id)

        manager.append_chunk(resp, "Part 1 ")
        self.assertEqual(resp.message_id, stable_id)

        manager.append_chunk(resp, "Part 2")
        self.assertEqual(resp.message_id, stable_id)

        manager.complete_response(resp)
        self.assertEqual(resp.message_id, stable_id)

    def test_empty_or_whitespace_message_id_rejected(self) -> None:
        """Creating a response with empty or blank ID must raise ValueError."""
        with self.assertRaises(ValueError):
            ChatViewStateManager.create_response("")
        with self.assertRaises(ValueError):
            ChatViewStateManager.create_response("   ")

    def test_to_dict_serialization(self) -> None:
        """Snapshot serialization must produce JSON-serializable dictionary."""
        resp = ChatViewStateManager.create_response("msg-serial")
        snap = resp.to_dict()
        self.assertEqual(snap["message_id"], "msg-serial")
        self.assertEqual(snap["state"], "pending")
        self.assertEqual(snap["content"], "")
        self.assertIsNone(snap["error_message"])


class TestSequentialStreamingAndCompletion(unittest.TestCase):
    """Validates ordered chunk appending and stream completion transitions."""

    def test_first_chunk_transitions_pending_to_streaming(self) -> None:
        """First incoming chunk transitions state from PENDING to STREAMING."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-chunk-1")
        self.assertEqual(resp.state, ResponseState.PENDING)

        manager.append_chunk(resp, "Hello, ")
        self.assertEqual(resp.state, ResponseState.STREAMING)
        self.assertEqual(resp.content, "Hello, ")
        self.assertEqual(resp.chunks_received, 1)

    def test_subsequent_chunks_append_in_order(self) -> None:
        """Sequential chunks must concatenate in strict arrival order."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-chunk-2")
        manager.append_chunk(resp, "Hello, ")
        manager.append_chunk(resp, "how can I assist you today?")

        self.assertEqual(resp.state, ResponseState.STREAMING)
        self.assertEqual(resp.content, "Hello, how can I assist you today?")
        self.assertEqual(resp.chunks_received, 2)

    def test_multiple_chunks_order_preservation(self) -> None:
        """Multiple small chunks must maintain exact FIFO ordering."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-multi")
        parts = ["The ", "quick ", "brown ", "fox ", "jumps."]
        for p in parts:
            manager.append_chunk(resp, p)

        self.assertEqual(resp.content, "The quick brown fox jumps.")
        self.assertEqual(resp.chunks_received, 5)

    def test_complete_response_transitions_to_complete(self) -> None:
        """Calling complete_response must finalize state to COMPLETE."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-complete")
        manager.append_chunk(resp, "Done.")
        manager.complete_response(resp)

        self.assertEqual(resp.state, ResponseState.COMPLETE)
        self.assertEqual(resp.content, "Done.")
        self.assertIsNone(resp.error_message)

    def test_complete_response_is_idempotent(self) -> None:
        """Subsequent completion calls on an already completed response are no-ops."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-idempotent")
        manager.append_chunk(resp, "Final.")
        manager.complete_response(resp)
        self.assertEqual(resp.state, ResponseState.COMPLETE)

        # Second completion call
        manager.complete_response(resp)
        self.assertEqual(resp.state, ResponseState.COMPLETE)

    def test_complete_without_chunks_transitions_from_pending(self) -> None:
        """A stream may complete with empty content (0 chunks received)."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-empty")
        manager.complete_response(resp)
        self.assertEqual(resp.state, ResponseState.COMPLETE)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.chunks_received, 0)


class TestErrorRecoveryAndTextPreservation(unittest.TestCase):
    """Validates error recovery preserving previously received text with error marker."""

    def test_error_after_first_chunk_preserves_text_and_appends_marker(self) -> None:
        """Previously received text must NOT be cleared; error marker is appended."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-err-1")
        manager.append_chunk(resp, "Hello, ")
        manager.fail_response(resp, "Stream connection dropped")

        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertEqual(resp.error_message, "Stream connection dropped")
        self.assertEqual(resp.content, "Hello, [ERROR: Stream connection dropped]")
        self.assertTrue(resp.content.startswith("Hello, "))
        self.assertIn("[ERROR: Stream connection dropped]", resp.content)

    def test_error_after_multiple_chunks_preserves_full_prefix(self) -> None:
        """All chunks received prior to error must be preserved intact."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-err-multi")
        manager.append_chunk(resp, "Step 1: Downloaded data.\n")
        manager.append_chunk(resp, "Step 2: Processing tokens...")
        manager.fail_response(resp, "Server timeout")

        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertTrue(resp.content.startswith("Step 1: Downloaded data.\nStep 2: Processing tokens..."))
        self.assertTrue(resp.content.endswith("[ERROR: Server timeout]"))

    def test_error_during_pending_sets_error_marker(self) -> None:
        """Error when 0 chunks have arrived sets content to just the marker."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-err-pending")
        manager.fail_response(resp, "Gateway timeout")

        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertEqual(resp.content, "[ERROR: Gateway timeout]")
        self.assertEqual(resp.chunks_received, 0)

    def test_cannot_complete_from_error_state(self) -> None:
        """Attempting to complete an errored response raises IllegalStateTransitionError."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-err-complete")
        manager.fail_response(resp, "Fatal error")

        with self.assertRaises(IllegalStateTransitionError):
            manager.complete_response(resp)

    def test_cannot_fail_already_completed_response(self) -> None:
        """Attempting to fail a completed response raises IllegalStateTransitionError."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-comp-fail")
        manager.append_chunk(resp, "Finished.")
        manager.complete_response(resp)

        with self.assertRaises(IllegalStateTransitionError):
            manager.fail_response(resp, "Late error")


class TestChunkRejectionInTerminalStates(unittest.TestCase):
    """Validates that chunks arriving after stream completion or error are rejected."""

    def test_chunk_rejected_after_completion(self) -> None:
        """Attempting to append a chunk after stream completion raises ChunkRejectedError."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-reject-comp")
        manager.append_chunk(resp, "Hello, ")
        manager.append_chunk(resp, "world.")
        manager.complete_response(resp)

        with self.assertRaises(ChunkRejectedError) as ctx:
            manager.append_chunk(resp, " Extra late text")

        self.assertIn("terminal state 'complete'", str(ctx.exception))

    def test_state_and_content_unmodified_after_rejection_post_complete(self) -> None:
        """Rejected chunk must not corrupt content or modify COMPLETE state."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-intact-comp")
        manager.append_chunk(resp, "Safe text.")
        manager.complete_response(resp)

        try:
            manager.append_chunk(resp, "Corrupted late text")
        except ChunkRejectedError:
            pass

        self.assertEqual(resp.state, ResponseState.COMPLETE)
        self.assertEqual(resp.content, "Safe text.")
        self.assertEqual(resp.chunks_received, 1)

    def test_chunk_rejected_after_error(self) -> None:
        """Attempting to append a chunk after stream error raises ChunkRejectedError."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-reject-err")
        manager.append_chunk(resp, "Partial text")
        manager.fail_response(resp, "Network cut")

        with self.assertRaises(ChunkRejectedError) as ctx:
            manager.append_chunk(resp, " Late arrival")

        self.assertIn("terminal state 'error'", str(ctx.exception))

    def test_state_and_content_unmodified_after_rejection_post_error(self) -> None:
        """Rejected chunk must not corrupt error content or modify ERROR state."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-intact-err")
        manager.append_chunk(resp, "Initial ")
        manager.fail_response(resp, "Abort")
        expected_content = "Initial [ERROR: Abort]"

        try:
            manager.append_chunk(resp, "Ignored late text")
        except ChunkRejectedError:
            pass

        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertEqual(resp.content, expected_content)
        self.assertEqual(resp.chunks_received, 1)

    def test_rejection_event_logged_in_history(self) -> None:
        """Rejection must append an audit event into response.history."""
        manager = ChatViewStateManager()
        resp = manager.create_response("msg-audit")
        manager.complete_response(resp)

        try:
            manager.append_chunk(resp, "late chunk")
        except ChunkRejectedError:
            pass

        last_event = resp.history[-1]
        self.assertEqual(last_event["event"], "chunk_rejected")
        self.assertEqual(last_event["attempted_chunk"], "late chunk")
        self.assertEqual(last_event["current_state"], "complete")


class TestCanonicalScenariosAndChecker(unittest.TestCase):
    """Validates the canonical scenario functions and decision table checker."""

    def test_run_normal_scenario(self) -> None:
        """Normal scenario helper produces STATE_COMPLETE_SUCCESS with ordered chunks."""
        data = run_normal_scenario()
        self.assertEqual(data["decision"], "STATE_COMPLETE_SUCCESS")
        self.assertEqual(data["state"], "complete")
        self.assertEqual(data["chunks_received"], 2)
        self.assertEqual(data["content"], "Hello, how can I assist you today?")
        self.assertTrue(data["stable_id_preserved"])
        self.assertTrue(data["ordered_chunks_verified"])

    def test_run_error_scenario(self) -> None:
        """Error scenario helper produces STATE_ERROR_RECOVERED with preserved text."""
        data = run_error_scenario()
        self.assertEqual(data["decision"], "STATE_ERROR_RECOVERED")
        self.assertEqual(data["state"], "error")
        self.assertEqual(data["chunks_received"], 1)
        self.assertEqual(data["content"], "Hello, [ERROR: Stream connection dropped]")
        self.assertTrue(data["text_preserved"])

    def test_run_boundary_scenario(self) -> None:
        """Boundary scenario helper produces CHUNK_AFTER_COMPLETION_REJECTED."""
        data = run_boundary_scenario()
        self.assertEqual(data["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")
        self.assertEqual(data["state"], "complete")
        self.assertEqual(data["content"], "Hello, how can I assist you today?")
        self.assertTrue(data["rejection_verified"])
        self.assertEqual(data["rejection_exception"], "ChunkRejectedError")

    def test_canonical_check_passes_on_unmodified_table(self) -> None:
        """Canonical check passes with all_passed=True and 0 failures."""
        summary = run_canonical_check(tamper=False)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["total_scenarios"], 3)
        self.assertEqual(summary["passed_scenarios"], 3)
        self.assertEqual(summary["failed_scenarios"], 0)
        self.assertTrue(summary["all_passed"])

    def test_canonical_check_fails_on_tamper(self) -> None:
        """Tampered check must raise DecisionMismatchError."""
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestSubprocessCLIExecution(unittest.TestCase):
    """Validates CLI command line invocations in fresh isolated subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal_exit_0(self) -> None:
        """CLI --scenario normal must exit 0 and output valid JSON."""
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_COMPLETE_SUCCESS")
        self.assertEqual(data["state"], "complete")
        self.assertEqual(data["content"], "Hello, how can I assist you today?")

    def test_cli_scenario_error_exit_0(self) -> None:
        """CLI --scenario error must exit 0 and output valid JSON."""
        res = self._run_cli(["--scenario", "error"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_ERROR_RECOVERED")
        self.assertEqual(data["state"], "error")
        self.assertIn("[ERROR: Stream connection dropped]", data["content"])

    def test_cli_scenario_boundary_exit_0(self) -> None:
        """CLI --scenario boundary must exit 0 and output valid JSON."""
        res = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")
        self.assertEqual(data["rejection_exception"], "ChunkRejectedError")

    def test_cli_check_all_exit_0(self) -> None:
        """CLI --check must exit 0 and report all passed."""
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["failed_scenarios"], 0)

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        """CLI --tamper must exit with non-zero exit code (1) and output error details."""
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1, f"Expected exit code 1, got {res.returncode}")
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")
        self.assertEqual(data["error_type"], "DecisionMismatchError")
        self.assertEqual(data["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
