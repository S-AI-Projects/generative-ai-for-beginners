"""Unit tests for Lesson 11 intermediate-state trace and invariant checks."""

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
    LocalStreamingTracker,
    ResponseState,
    run_boundary_error_case,
    run_failure_late_chunk_case,
    run_normal_case,
    verify_trace_invariants,
)


class TestStreamingTraceInvariants(unittest.TestCase):
    def test_normal_two_chunks_record_intermediate_states_and_invariants(self) -> None:
        outcome = run_normal_case()
        states = outcome["intermediate_states"]
        final = outcome["final_output"]

        self.assertTrue(final["simulation"])
        self.assertEqual([s["status"] for s in states], ["pending", "streaming", "streaming", "complete"])
        self.assertEqual([s["received_text"] for s in states], ["", "Hello ", "Hello world", "Hello world"])
        self.assertEqual(final["message_id"], "msg-001")
        self.assertEqual(final["status"], "complete")
        self.assertEqual(final["received_text"], "Hello world")
        self.assertIsNone(final["error_marker"])
        self.assertTrue(all(outcome["invariants"].values()))

    def test_boundary_error_preserves_text_with_marker_and_invariants(self) -> None:
        outcome = run_boundary_error_case()
        states = outcome["intermediate_states"]
        final = outcome["final_output"]

        self.assertEqual([s["status"] for s in states], ["pending", "streaming", "error"])
        self.assertEqual(final["message_id"], "msg-002")
        self.assertEqual(final["status"], "error")
        self.assertEqual(final["received_text"], "Partial ")
        self.assertEqual(final["error_marker"], "[ERROR: stream interrupted]")
        self.assertEqual(final["display_text"], "Partial [ERROR: stream interrupted]")
        self.assertTrue(all(outcome["invariants"].values()))

    def test_boundary_zero_chunk_complete_and_error_from_pending(self) -> None:
        t1 = LocalStreamingTracker("msg-zero")
        t1.complete()
        self.assertEqual([s["status"] for s in t1.snapshots], ["pending", "complete"])
        invariants_1 = verify_trace_invariants(t1.snapshots, t1.final_output())
        self.assertTrue(all(invariants_1.values()))

        t2 = LocalStreamingTracker("msg-pending-err")
        t2.fail("timeout")
        self.assertEqual([s["status"] for s in t2.snapshots], ["pending", "error"])
        self.assertEqual(t2.final_output()["display_text"], "[ERROR: timeout]")
        invariants_2 = verify_trace_invariants(t2.snapshots, t2.final_output())
        self.assertTrue(all(invariants_2.values()))

    def test_failure_chunk_after_completion_rejected_and_logged(self) -> None:
        outcome = run_failure_late_chunk_case()
        states = outcome["intermediate_states"]
        final = outcome["final_output"]

        self.assertTrue(outcome["rejected"])
        self.assertIn("terminal state 'complete'", outcome["rejection_error"])
        self.assertEqual(len(states), 4)
        self.assertFalse(states[-1]["accepted"])
        self.assertEqual(states[-1]["status"], "complete")
        self.assertEqual(states[-1]["received_text"], "Done")
        self.assertEqual(final["message_id"], "msg-003")
        self.assertEqual(final["received_text"], "Done")
        self.assertTrue(all(outcome["invariants"].values()))

    def test_invariant_fails_if_final_output_diverges_from_intermediate_trace(self) -> None:
        outcome = run_normal_case()
        corrupted_final = dict(outcome["final_output"])
        corrupted_final["received_text"] = "corrupted"

        with self.assertRaises(AssertionError):
            verify_trace_invariants(outcome["intermediate_states"], corrupted_final)

        corrupted_states = [dict(s) for s in outcome["intermediate_states"]]
        corrupted_states[1]["message_id"] = "msg-other"
        with self.assertRaises(AssertionError):
            verify_trace_invariants(corrupted_states, outcome["final_output"])

    def test_invalid_inputs_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            LocalStreamingTracker("")
        tracker = LocalStreamingTracker("msg-bad")
        with self.assertRaises(ValueError):
            tracker.append_chunk(99)  # type: ignore[arg-type]
        self.assertEqual(tracker.state, ResponseState.PENDING)
        self.assertFalse(tracker.snapshots[-1]["accepted"])

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
        self.assertEqual(len(payload["results"]), 3)
        for res in payload["results"]:
            self.assertTrue(all(res["invariants"].values()))

        bad_proc = subprocess.run(
            [sys.executable, str(script), "--scenario", "invalid"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(bad_proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
