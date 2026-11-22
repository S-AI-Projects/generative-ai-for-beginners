#!/usr/bin/env python3
"""Regression and invariant test suite for R40-T001.

Lesson 12: Designing UX for AI Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners
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

    def test_empty_message_id_rejected(self) -> None:
        """Empty or whitespace-only message ID must be rejected."""
        with self.assertRaises(ValueError):
            ChatViewStateManager.create_response("")
        with self.assertRaises(ValueError):
            ChatViewStateManager.create_response("   ")


class TestStreamingOrderingAndCompletion(unittest.TestCase):
    """Validates ordered streaming chunks and clean completion transitions."""

    def test_two_chunks_append_in_order(self) -> None:
        """Two chunks append strictly in arrival order."""
        resp = ChatViewStateManager.create_response("msg-002")
        ChatViewStateManager.append_chunk(resp, "Hello, ")
        self.assertEqual(resp.state, ResponseState.STREAMING)
        self.assertEqual(resp.content, "Hello, ")
        self.assertEqual(resp.chunks_received, 1)

        ChatViewStateManager.append_chunk(resp, "how can I assist you today?")
        self.assertEqual(resp.state, ResponseState.STREAMING)
        self.assertEqual(resp.content, "Hello, how can I assist you today?")
        self.assertEqual(resp.chunks_received, 2)

        ChatViewStateManager.complete(resp)
        self.assertEqual(resp.state, ResponseState.COMPLETE)
        self.assertEqual(resp.message_id, "msg-002")

    def test_invalid_chunk_type_rejected(self) -> None:
        """Non-string chunk must raise TypeError."""
        resp = ChatViewStateManager.create_response("msg-003")
        with self.assertRaises(TypeError):
            ChatViewStateManager.append_chunk(resp, 123)  # type: ignore


class TestErrorRecoveryAndPreservation(unittest.TestCase):
    """Validates error recovery with preservation of received partial text."""

    def test_error_preserves_received_text_with_marker(self) -> None:
        """Error transition preserves prior chunks and attaches error marker."""
        resp = ChatViewStateManager.create_response("msg-004")
        ChatViewStateManager.append_chunk(resp, "Hello, ")
        self.assertEqual(resp.content, "Hello, ")

        ChatViewStateManager.fail(resp, "Network timeout")
        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertEqual(resp.content, "Hello, [ERROR: Network timeout]")
        self.assertEqual(resp.error_message, "Network timeout")
        self.assertEqual(resp.chunks_received, 1)


class TestPostTerminalRejection(unittest.TestCase):
    """Validates terminal state boundaries and chunk rejection."""

    def test_chunks_after_completion_rejected(self) -> None:
        """Appending chunk after COMPLETE state raises ChunkRejectedError."""
        resp = ChatViewStateManager.create_response("msg-005")
        ChatViewStateManager.append_chunk(resp, "Chunk 1")
        ChatViewStateManager.complete(resp)

        with self.assertRaises(ChunkRejectedError):
            ChatViewStateManager.append_chunk(resp, "Chunk 2")

    def test_chunks_after_error_rejected(self) -> None:
        """Appending chunk after ERROR state raises ChunkRejectedError."""
        resp = ChatViewStateManager.create_response("msg-006")
        ChatViewStateManager.append_chunk(resp, "Chunk 1")
        ChatViewStateManager.fail(resp, "Fatal error")

        with self.assertRaises(ChunkRejectedError):
            ChatViewStateManager.append_chunk(resp, "Chunk 2")

    def test_cannot_complete_from_error(self) -> None:
        """Attempting to complete a failed response raises IllegalStateTransitionError."""
        resp = ChatViewStateManager.create_response("msg-007")
        ChatViewStateManager.fail(resp, "Err")
        with self.assertRaises(IllegalStateTransitionError):
            ChatViewStateManager.complete(resp)

    def test_cannot_fail_from_complete(self) -> None:
        """Attempting to fail a completed response raises IllegalStateTransitionError."""
        resp = ChatViewStateManager.create_response("msg-008")
        ChatViewStateManager.complete(resp)
        with self.assertRaises(IllegalStateTransitionError):
            ChatViewStateManager.fail(resp, "Err")


class TestScenarioHelpersAndDecisionTable(unittest.TestCase):
    """Tests high-level scenario functions and decision table validation."""

    def test_run_normal_scenario(self) -> None:
        res = run_normal_scenario()
        self.assertEqual(res["decision"], "STATE_COMPLETE_SUCCESS")
        self.assertEqual(res["state"], "complete")
        self.assertEqual(res["chunks_received"], 2)
        self.assertTrue(res["stable_id_preserved"])
        self.assertTrue(res["ordered_chunks_verified"])

    def test_run_error_scenario(self) -> None:
        res = run_error_scenario()
        self.assertEqual(res["decision"], "STATE_ERROR_RECOVERED")
        self.assertEqual(res["state"], "error")
        self.assertTrue(res["text_preserved"])
        self.assertTrue(res["content_matches_expected"])

    def test_run_boundary_scenario(self) -> None:
        res = run_boundary_scenario()
        self.assertEqual(res["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")
        self.assertTrue(res["rejection_verified"])
        self.assertEqual(res["rejection_exception"], "ChunkRejectedError")

    def test_canonical_check_passes(self) -> None:
        summary = run_canonical_check(tamper=False)
        self.assertEqual(summary["status"], "success")
        self.assertTrue(summary["all_passed"])
        self.assertEqual(summary["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateFailure(unittest.TestCase):
    """Verifies that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI subprocess invocation."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_normal_exit_0(self) -> None:
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_COMPLETE_SUCCESS")

    def test_cli_error_exit_0(self) -> None:
        res = self._run_cli(["--scenario", "error"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_ERROR_RECOVERED")

    def test_cli_boundary_exit_0(self) -> None:
        res = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")

    def test_cli_check_exit_0(self) -> None:
        res = self._run_cli(["--check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_passed"])

    def test_cli_tamper_fails_with_nonzero_exit(self) -> None:
        res = self._run_cli(["--tamper"])
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")


if __name__ == "__main__":
    unittest.main()
