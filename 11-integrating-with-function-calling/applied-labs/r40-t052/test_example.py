"""Unit tests for the Lesson 11 local response-streaming state machine."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from example import (  # noqa: E402
    LocalStreamingResponse,
    ResponseState,
    run_boundary_error_case,
    run_boundary_zero_chunk_case,
    run_fixture_suite,
    run_invalid_late_chunk_case,
    run_smallest_valid_case,
)


class TestLocalStreamingResponse(unittest.TestCase):
    def test_smallest_valid_two_chunks_append_in_order(self) -> None:
        outcome = run_smallest_valid_case()
        result = outcome["result"]

        self.assertTrue(result["simulation"])
        self.assertEqual(outcome["transitions"], ["pending", "streaming", "streaming", "complete"])
        self.assertEqual(result["message_id"], "msg-valid-001")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["chunks_received"], ["Hello ", "world"])
        self.assertEqual(result["received_text"], "Hello world")
        self.assertIsNone(result["error_marker"])
        self.assertEqual(result["display_text"], "Hello world")

    def test_boundary_error_preserves_received_text_with_marker(self) -> None:
        outcome = run_boundary_error_case()
        result = outcome["result"]

        self.assertEqual(outcome["transitions"], ["pending", "streaming", "error"])
        self.assertEqual(result["message_id"], "msg-boundary-002")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["received_text"], "Partial ")
        self.assertEqual(result["error_marker"], "[ERROR: stream interrupted]")
        self.assertEqual(result["display_text"], "Partial [ERROR: stream interrupted]")

    def test_boundary_zero_chunk_completion_and_empty_string_delta(self) -> None:
        zero_outcome = run_boundary_zero_chunk_case()
        self.assertEqual(zero_outcome["transitions"], ["pending", "complete"])
        self.assertEqual(zero_outcome["result"]["received_text"], "")

        resp = LocalStreamingResponse("msg-empty-delta")
        self.assertEqual(resp.state, ResponseState.PENDING)
        resp.append_chunk("")
        self.assertEqual(resp.state, ResponseState.STREAMING)
        self.assertEqual(resp.received_text, "")
        resp.complete()
        self.assertEqual(resp.state, ResponseState.COMPLETE)
        self.assertEqual(resp.message_id, "msg-empty-delta")

    def test_boundary_error_from_pending_before_any_chunk(self) -> None:
        resp = LocalStreamingResponse("msg-pending-err")
        display = resp.fail("upstream timeout")

        self.assertEqual(resp.state, ResponseState.ERROR)
        self.assertEqual(resp.received_text, "")
        self.assertEqual(display, "[ERROR: upstream timeout]")

    def test_invalid_chunk_after_completion_rejected_and_state_preserved(self) -> None:
        outcome = run_invalid_late_chunk_case()
        result = outcome["result"]

        self.assertTrue(outcome["rejected"])
        self.assertIn("terminal state 'complete'", outcome["rejection_reason"])
        self.assertEqual(result["message_id"], "msg-invalid-004")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["received_text"], "Done")

    def test_invalid_transitions_and_bad_inputs_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            LocalStreamingResponse("")
        with self.assertRaises(ValueError):
            LocalStreamingResponse("   ")

        resp = LocalStreamingResponse("msg-err-terminal")
        resp.append_chunk("first ")
        resp.fail("connection lost")

        with self.assertRaises(ValueError):
            resp.append_chunk("second")
        with self.assertRaises(ValueError):
            resp.complete()
        with self.assertRaises(ValueError):
            resp.fail("another error")
        self.assertEqual(resp.received_text, "first ")
        self.assertEqual(resp.display_text, "first [ERROR: connection lost]")

        resp2 = LocalStreamingResponse("msg-bad-chunk")
        with self.assertRaises(ValueError):
            resp2.append_chunk(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            resp2.fail("   ")

    def test_fresh_process_cli_normal_and_invalid_scenario(self) -> None:
        script = LAB_DIR / "example.py"
        ok_proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(ok_proc.stdout)
        self.assertTrue(payload["simulation"])
        self.assertEqual(
            [case["case"] for case in payload["cases"]],
            [
                "smallest_valid",
                "boundary_error_preserves_text",
                "boundary_zero_chunk_complete",
                "invalid_chunk_after_completion",
            ],
        )

        bad_proc = subprocess.run(
            [sys.executable, str(script), "--scenario", "unknown"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(bad_proc.returncode, 0)

        with self.assertRaises(ValueError):
            run_fixture_suite("unknown")


if __name__ == "__main__":
    unittest.main()
