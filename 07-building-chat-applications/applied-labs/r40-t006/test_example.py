#!/usr/bin/env python3
"""Regression, invariant, and refactoring equivalence test suite for R40-T006.

Lesson 07: Building Generative AI-Powered Chat Applications
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
    DEFAULT_MESSAGE_ID,
    BaselineChatResponseManager,
    ChunkRejectedError,
    DecisionMismatchError,
    IllegalStateTransitionError,
    RefactoredChatResponseManager,
    ResponseState,
    StreamingContentBuffer,
    run_boundary_scenario,
    run_canonical_check,
    run_error_scenario,
    run_normal_scenario,
    verify_before_after_refactor_equivalence,
)

EXAMPLE_PY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "example.py")
)


class TestCoreStateContract(unittest.TestCase):
    """Core response view lifecycle contract tests."""

    def test_two_chunks_append_in_order(self) -> None:
        mgr = RefactoredChatResponseManager("msg-01")
        self.assertEqual(mgr.state, ResponseState.PENDING)

        mgr.append_chunk("Hello, ")
        self.assertEqual(mgr.state, ResponseState.STREAMING)

        mgr.append_chunk("how can I assist you today?")
        self.assertEqual(mgr.state, ResponseState.STREAMING)

        mgr.complete()
        self.assertEqual(mgr.state, ResponseState.COMPLETE)

        snap = mgr.snapshot()
        self.assertEqual(snap["content"], "Hello, how can I assist you today?")
        self.assertEqual(snap["chunks_received"], 2)

    def test_error_preserves_received_text_with_marker(self) -> None:
        mgr = RefactoredChatResponseManager("msg-02")
        mgr.append_chunk("Hello, ")
        mgr.fail("Timeout drop")

        self.assertEqual(mgr.state, ResponseState.ERROR)
        snap = mgr.snapshot()
        self.assertEqual(snap["content"], "Hello, [ERROR: Timeout drop]")
        self.assertEqual(snap["chunks_received"], 1)

    def test_chunks_after_completion_rejected(self) -> None:
        mgr = RefactoredChatResponseManager("msg-03")
        mgr.append_chunk("Hello, ")
        mgr.complete()

        with self.assertRaises(ChunkRejectedError):
            mgr.append_chunk("Late chunk")

    def test_chunks_after_error_rejected(self) -> None:
        mgr = RefactoredChatResponseManager("msg-04")
        mgr.append_chunk("Hello, ")
        mgr.fail("Dropped")

        with self.assertRaises(ChunkRejectedError):
            mgr.append_chunk("Late chunk")


class TestRefactoringResponsibilityExtraction(unittest.TestCase):
    """Focus: Verifies extracted responsibility and before/after equivalence."""

    def test_extracted_streaming_buffer_unit(self) -> None:
        buf = StreamingContentBuffer()
        buf.append("Part 1")
        buf.append("Part 2")
        self.assertEqual(buf.count(), 2)
        self.assertEqual(buf.get_text(), "Part 1Part 2")
        buf.apply_error_marker("err")
        self.assertEqual(buf.get_text(), "Part 1Part 2[ERROR: err]")

    def test_baseline_and_refactored_equivalence(self) -> None:
        equiv = verify_before_after_refactor_equivalence()
        self.assertTrue(equiv["all_equivalent"])
        self.assertTrue(equiv["normal_path_equivalent"])
        self.assertTrue(equiv["error_path_equivalent"])
        self.assertTrue(equiv["boundary_path_equivalent"])


class TestCanonicalCheckAndTamper(unittest.TestCase):
    """Canonical checks and deliberate tamper detection."""

    def test_canonical_check_passes(self) -> None:
        res = run_canonical_check(tamper=False)
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["refactor_equivalence_verified"])
        self.assertEqual(res["failed_scenarios"], 0)

    def test_canonical_check_fails_on_tamper(self) -> None:
        with self.assertRaises(DecisionMismatchError):
            run_canonical_check(tamper=True)


class TestDeliberateWrongResult(unittest.TestCase):
    """Demonstrates that a deliberate wrong result makes the test fail."""

    def test_deliberate_wrong_result_fails(self) -> None:
        res = run_normal_scenario()
        with self.assertRaises(AssertionError):
            self.assertEqual(res["decision"], "TAMPERED_WRONG_RESULT")


class TestCLIExecution(unittest.TestCase):
    """Validates CLI execution in fresh subprocesses."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, EXAMPLE_PY] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_scenario_normal(self) -> None:
        res = self._run_cli(["--scenario", "normal"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_COMPLETE_SUCCESS")

    def test_cli_scenario_error(self) -> None:
        res = self._run_cli(["--scenario", "error"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "STATE_ERROR_RECOVERED")

    def test_cli_scenario_boundary(self) -> None:
        res = self._run_cli(["--scenario", "boundary"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")

    def test_cli_refactor_check(self) -> None:
        res = self._run_cli(["--refactor-check"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["all_equivalent"])

    def test_cli_check(self) -> None:
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
