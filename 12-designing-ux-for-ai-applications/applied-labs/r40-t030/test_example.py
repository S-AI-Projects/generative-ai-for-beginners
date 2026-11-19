"""
Unit and regression tests for Chat-View State Lifecycle & Scenario Assessment (R40-T030).
Lesson: 12-designing-ux-for-ai-applications

Verifies:
1. Four lifecycle states: PENDING -> STREAMING -> COMPLETE and PENDING -> STREAMING -> ERROR.
2. Stable message identity across all state transitions.
3. Sequential chunk appending in arrival order.
4. Error preservation: received text preserved intact + error marker appended.
5. Boundary protection: chunks arriving after COMPLETE or ERROR are rejected with ChunkRejectedError.
6. Three applied questions: predict output, diagnose failure, choose boundary policy.
7. Subprocess CLI executions for normal, error, boundary, questions, check, and tamper modes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any, Dict

from example import (
    CANONICAL_MESSAGE_ID,
    CHUNK_1,
    CHUNK_2,
    ERROR_REASON,
    LATE_CHUNK,
    QUESTION_1,
    QUESTION_2,
    QUESTION_3,
    ChatViewMessage,
    ChatViewStateManager,
    ChunkRejectedError,
    InvalidStateTransitionError,
    MessageState,
    run_all_questions_assessment,
    run_boundary_scenario,
    run_decision_table_check,
    run_error_scenario,
    run_normal_scenario,
    verify_question_1,
    verify_question_2,
    verify_question_3,
)


class TestChatViewStateManagerLifecycle(unittest.TestCase):
    """Tests the state machine lifecycle, invariants, and transitions."""

    def test_init_pending_state(self) -> None:
        mgr = ChatViewStateManager("msg-test-01")
        self.assertEqual(mgr.message_id, "msg-test-01")
        self.assertEqual(mgr.state, MessageState.PENDING)
        self.assertEqual(mgr.content, "")
        self.assertEqual(mgr.chunks_received, 0)
        self.assertIsNone(mgr.error_message)

    def test_first_chunk_transitions_to_streaming(self) -> None:
        mgr = ChatViewStateManager("msg-test-02")
        mgr.append_chunk("Hello, ")
        self.assertEqual(mgr.state, MessageState.STREAMING)
        self.assertEqual(mgr.content, "Hello, ")
        self.assertEqual(mgr.chunks_received, 1)

    def test_second_chunk_appends_in_order(self) -> None:
        mgr = ChatViewStateManager("msg-test-03")
        mgr.append_chunk("Hello, ")
        mgr.append_chunk("world!")
        self.assertEqual(mgr.state, MessageState.STREAMING)
        self.assertEqual(mgr.content, "Hello, world!")
        self.assertEqual(mgr.chunks_received, 2)

    def test_complete_transitions_to_complete(self) -> None:
        mgr = ChatViewStateManager("msg-test-04")
        mgr.append_chunk("Alpha ")
        mgr.append_chunk("Beta")
        mgr.complete()
        self.assertEqual(mgr.state, MessageState.COMPLETE)
        self.assertEqual(mgr.content, "Alpha Beta")
        self.assertEqual(mgr.chunks_received, 2)
        self.assertIsNone(mgr.error_message)

    def test_stable_message_id_across_all_transitions(self) -> None:
        mgr = ChatViewStateManager("msg-stable-001")
        fixed_id = mgr.message_id

        mgr.append_chunk(CHUNK_1)
        self.assertEqual(mgr.message_id, fixed_id)

        mgr.append_chunk(CHUNK_2)
        self.assertEqual(mgr.message_id, fixed_id)

        mgr.complete()
        self.assertEqual(mgr.message_id, fixed_id)

        snap = mgr.get_snapshot()
        self.assertEqual(snap.message_id, fixed_id)

    def test_invalid_message_id_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            ChatViewStateManager("")
        with self.assertRaises(ValueError):
            ChatViewStateManager(None)  # type: ignore

    def test_invalid_chunk_type_raises_type_error(self) -> None:
        mgr = ChatViewStateManager("msg-type-err")
        with self.assertRaises(TypeError):
            mgr.append_chunk(123)  # type: ignore


class TestErrorRecoveryAndTextPreservation(unittest.TestCase):
    """Tests failure handling and partial text preservation."""

    def test_error_in_pending_state(self) -> None:
        mgr = ChatViewStateManager("msg-err-pending")
        mgr.fail("Initial handshake failed")
        self.assertEqual(mgr.state, MessageState.ERROR)
        self.assertEqual(mgr.content, "[ERROR: Initial handshake failed]")
        self.assertEqual(mgr.chunks_received, 0)
        self.assertEqual(mgr.error_message, "Initial handshake failed")

    def test_error_in_streaming_state_preserves_partial_text(self) -> None:
        mgr = ChatViewStateManager("msg-err-streaming")
        mgr.append_chunk(CHUNK_1)
        mgr.fail(ERROR_REASON)
        self.assertEqual(mgr.state, MessageState.ERROR)
        expected = f"{CHUNK_1}[ERROR: {ERROR_REASON}]"
        self.assertEqual(mgr.content, expected)
        self.assertEqual(mgr.chunks_received, 1)
        self.assertEqual(mgr.error_message, ERROR_REASON)

    def test_error_with_multiple_chunks_preserves_all_chunks(self) -> None:
        mgr = ChatViewStateManager("msg-err-multi")
        mgr.append_chunk("Part 1: ")
        mgr.append_chunk("Part 2: ")
        mgr.fail("Timeout reached")
        self.assertEqual(mgr.state, MessageState.ERROR)
        expected = "Part 1: Part 2: [ERROR: Timeout reached]"
        self.assertEqual(mgr.content, expected)
        self.assertEqual(mgr.chunks_received, 2)

    def test_error_empty_reason_fallback(self) -> None:
        mgr = ChatViewStateManager("msg-err-default")
        mgr.append_chunk("Some text")
        mgr.fail("")
        self.assertEqual(mgr.state, MessageState.ERROR)
        self.assertIn("[ERROR: Unspecified stream interruption]", mgr.content)

    def test_snapshot_representation(self) -> None:
        mgr = ChatViewStateManager("msg-snap-01")
        mgr.append_chunk(CHUNK_1)
        snap = mgr.get_snapshot()
        self.assertIsInstance(snap, ChatViewMessage)
        snap_dict = snap.to_dict()
        self.assertEqual(snap_dict["message_id"], "msg-snap-01")
        self.assertEqual(snap_dict["state"], "streaming")
        self.assertEqual(snap_dict["content"], CHUNK_1)
        self.assertEqual(snap_dict["chunks_received"], 1)


class TestBoundaryAndTerminalStateRejection(unittest.TestCase):
    """Tests boundary protections and terminal state immutability."""

    def test_append_after_complete_raises_chunk_rejected_error(self) -> None:
        mgr = ChatViewStateManager("msg-boundary-01")
        mgr.append_chunk(CHUNK_1)
        mgr.append_chunk(CHUNK_2)
        mgr.complete()

        with self.assertRaises(ChunkRejectedError) as ctx:
            mgr.append_chunk(LATE_CHUNK)
        self.assertIn("already in terminal state 'complete'", str(ctx.exception))

    def test_append_after_complete_preserves_content_unmodified(self) -> None:
        mgr = ChatViewStateManager("msg-boundary-02")
        mgr.append_chunk(CHUNK_1)
        mgr.append_chunk(CHUNK_2)
        mgr.complete()
        sealed_content = mgr.content

        try:
            mgr.append_chunk(LATE_CHUNK)
        except ChunkRejectedError:
            pass

        self.assertEqual(mgr.content, sealed_content)
        self.assertEqual(mgr.state, MessageState.COMPLETE)

    def test_append_after_error_raises_chunk_rejected_error(self) -> None:
        mgr = ChatViewStateManager("msg-boundary-03")
        mgr.append_chunk(CHUNK_1)
        mgr.fail(ERROR_REASON)

        with self.assertRaises(ChunkRejectedError) as ctx:
            mgr.append_chunk(LATE_CHUNK)
        self.assertIn("already in terminal state 'error'", str(ctx.exception))

    def test_append_after_error_preserves_content_unmodified(self) -> None:
        mgr = ChatViewStateManager("msg-boundary-04")
        mgr.append_chunk(CHUNK_1)
        mgr.fail(ERROR_REASON)
        sealed_content = mgr.content

        try:
            mgr.append_chunk(LATE_CHUNK)
        except ChunkRejectedError:
            pass

        self.assertEqual(mgr.content, sealed_content)
        self.assertEqual(mgr.state, MessageState.ERROR)

    def test_complete_after_complete_raises_invalid_state_transition(self) -> None:
        mgr = ChatViewStateManager("msg-trans-01")
        mgr.complete()
        with self.assertRaises(InvalidStateTransitionError):
            mgr.complete()

    def test_fail_after_complete_raises_invalid_state_transition(self) -> None:
        mgr = ChatViewStateManager("msg-trans-02")
        mgr.complete()
        with self.assertRaises(InvalidStateTransitionError):
            mgr.fail("Late failure")

    def test_complete_after_error_raises_invalid_state_transition(self) -> None:
        mgr = ChatViewStateManager("msg-trans-03")
        mgr.fail("Network failed")
        with self.assertRaises(InvalidStateTransitionError):
            mgr.complete()

    def test_fail_after_error_raises_invalid_state_transition(self) -> None:
        mgr = ChatViewStateManager("msg-trans-04")
        mgr.fail("Network failed")
        with self.assertRaises(InvalidStateTransitionError):
            mgr.fail("Second failure")


class TestAppliedQuestions(unittest.TestCase):
    """Tests the three applied scenario assessment questions."""

    def test_question_1_predict_output_factual_answer(self) -> None:
        self.assertEqual(QUESTION_1.question_id, "Q1_PREDICT_OUTPUT")
        self.assertEqual(QUESTION_1.focus_area, "predict_an_output")
        self.assertEqual(QUESTION_1.correct_option, "B")
        self.assertEqual(QUESTION_1.factual_answer["state"], "error")
        self.assertEqual(
            QUESTION_1.factual_answer["content"],
            f"{CHUNK_1}[ERROR: {ERROR_REASON}]",
        )

    def test_question_1_verification_check_passes(self) -> None:
        res1 = verify_question_1()
        self.assertTrue(res1["passed"])
        self.assertEqual(res1["status"], "PASS")
        self.assertEqual(res1["selected_option"], "B")
        self.assertEqual(res1["predicted_output"], res1["actual_output"])

    def test_question_2_diagnose_failure_factual_answer(self) -> None:
        self.assertEqual(QUESTION_2.question_id, "Q2_DIAGNOSE_FAILURE")
        self.assertEqual(QUESTION_2.focus_area, "diagnose_a_failure")
        self.assertEqual(QUESTION_2.correct_option, "B")
        self.assertEqual(QUESTION_2.factual_answer["exception_type"], "ChunkRejectedError")

    def test_question_2_verification_check_passes(self) -> None:
        res2 = verify_question_2()
        self.assertTrue(res2["passed"])
        self.assertEqual(res2["status"], "PASS")
        self.assertEqual(res2["selected_option"], "B")
        self.assertTrue(res2["actual_diagnostic_evidence"]["rejection_verified"])
        self.assertEqual(
            res2["actual_diagnostic_evidence"]["rejection_exception"],
            "ChunkRejectedError",
        )

    def test_question_3_choose_boundary_policy_factual_answer(self) -> None:
        self.assertEqual(QUESTION_3.question_id, "Q3_CHOOSE_BOUNDARY_POLICY")
        self.assertEqual(QUESTION_3.focus_area, "choose_boundary_policy")
        self.assertEqual(QUESTION_3.correct_option, "C")
        self.assertEqual(
            QUESTION_3.factual_answer["chosen_policy"],
            "POLICY_EXPLICIT_REJECTION",
        )

    def test_question_3_verification_check_passes(self) -> None:
        res3 = verify_question_3()
        self.assertTrue(res3["passed"])
        self.assertEqual(res3["status"], "PASS")
        self.assertEqual(res3["selected_option"], "C")
        self.assertTrue(res3["verification_evidence"]["error_terminal_rejection"])
        self.assertTrue(res3["verification_evidence"]["complete_terminal_rejection"])
        self.assertTrue(res3["verification_evidence"]["error_buffer_preserved"])
        self.assertTrue(res3["verification_evidence"]["complete_buffer_preserved"])

    def test_run_all_questions_assessment(self) -> None:
        res = run_all_questions_assessment()
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["total_questions"], 3)
        self.assertEqual(res["passed_questions"], 3)
        self.assertEqual(res["failed_questions"], 0)
        self.assertEqual(len(res["questions"]), 3)


class TestCanonicalScenarios(unittest.TestCase):
    """Tests the canonical scenario runners and decision table check."""

    def test_normal_scenario_contract(self) -> None:
        norm = run_normal_scenario()
        self.assertEqual(norm["scenario_id"], "SCENARIO_NORMAL")
        self.assertEqual(norm["decision"], "STATE_COMPLETE_SUCCESS")
        self.assertEqual(norm["state"], "complete")
        self.assertEqual(norm["content"], f"{CHUNK_1}{CHUNK_2}")
        self.assertEqual(norm["chunks_received"], 2)
        self.assertTrue(norm["stable_id_preserved"])
        self.assertTrue(norm["ordered_chunks_verified"])

    def test_error_scenario_contract(self) -> None:
        err = run_error_scenario()
        self.assertEqual(err["scenario_id"], "SCENARIO_ERROR")
        self.assertEqual(err["decision"], "STATE_ERROR_RECOVERED")
        self.assertEqual(err["state"], "error")
        self.assertEqual(err["content"], f"{CHUNK_1}[ERROR: {ERROR_REASON}]")
        self.assertEqual(err["chunks_received"], 1)
        self.assertTrue(err["stable_id_preserved"])
        self.assertTrue(err["partial_text_preserved"])
        self.assertTrue(err["error_marker_present"])

    def test_boundary_scenario_contract(self) -> None:
        bnd = run_boundary_scenario()
        self.assertEqual(bnd["scenario_id"], "SCENARIO_BOUNDARY")
        self.assertEqual(bnd["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")
        self.assertEqual(bnd["state"], "complete")
        self.assertEqual(bnd["content"], f"{CHUNK_1}{CHUNK_2}")
        self.assertTrue(bnd["rejection_verified"])
        self.assertEqual(bnd["rejection_exception"], "ChunkRejectedError")
        self.assertTrue(bnd["buffer_unmodified"])
        self.assertTrue(bnd["state_unmodified"])

    def test_decision_table_check_success(self) -> None:
        check = run_decision_table_check(tamper=False)
        self.assertTrue(check["all_passed"])
        self.assertEqual(check["total_scenarios"], 3)
        self.assertEqual(check["passed_scenarios"], 3)
        self.assertEqual(check["failed_scenarios"], 0)

    def test_decision_table_check_tamper_detects_failure(self) -> None:
        tamper_check = run_decision_table_check(tamper=True)
        self.assertFalse(tamper_check["all_passed"])
        self.assertEqual(tamper_check["failed_scenarios"], 1)


class TestCommandLineInterface(unittest.TestCase):
    """Tests execution of the script in fresh subprocesses across CLI flags."""

    MODULE_PATH = "12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py"

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, self.MODULE_PATH, *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_scenario_normal_subprocess(self) -> None:
        proc = self._run_cli("--scenario", "normal")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "STATE_COMPLETE_SUCCESS")
        self.assertEqual(data["state"], "complete")
        self.assertEqual(data["content"], f"{CHUNK_1}{CHUNK_2}")

    def test_cli_scenario_error_subprocess(self) -> None:
        proc = self._run_cli("--scenario", "error")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "STATE_ERROR_RECOVERED")
        self.assertEqual(data["state"], "error")
        self.assertEqual(data["content"], f"{CHUNK_1}[ERROR: {ERROR_REASON}]")

    def test_cli_scenario_boundary_subprocess(self) -> None:
        proc = self._run_cli("--scenario", "boundary")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["decision"], "CHUNK_AFTER_COMPLETION_REJECTED")
        self.assertTrue(data["rejection_verified"])
        self.assertEqual(data["rejection_exception"], "ChunkRejectedError")

    def test_cli_scenario_questions_subprocess(self) -> None:
        proc = self._run_cli("--scenario", "questions")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_questions"], 3)

    def test_cli_questions_flag_subprocess(self) -> None:
        proc = self._run_cli("--questions")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_questions"], 3)

    def test_cli_single_question_flags_subprocess(self) -> None:
        for q_num in (1, 2, 3):
            proc = self._run_cli("--question", str(q_num))
            self.assertEqual(proc.returncode, 0, f"Q{q_num} failed: {proc.stderr}")
            data = json.loads(proc.stdout)
            self.assertTrue(data["assessment"]["passed"])
            self.assertEqual(data["assessment"]["status"], "PASS")

    def test_cli_check_subprocess(self) -> None:
        proc = self._run_cli("--check")
        self.assertEqual(proc.returncode, 0, f"Stderr: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_scenarios"], 3)

    def test_cli_tamper_subprocess_exits_nonzero(self) -> None:
        proc = self._run_cli("--tamper")
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stderr)
        self.assertEqual(data["status"], "expected_tamper_failure")
        self.assertEqual(data["error_type"], "DecisionMismatchError")
        self.assertEqual(data["exit_code"], 1)

    def test_cli_no_args_exits_nonzero(self) -> None:
        proc = self._run_cli()
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
