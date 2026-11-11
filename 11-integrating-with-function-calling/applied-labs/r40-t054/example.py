"""Local response-streaming state tracker with step-by-step trace invariants.

Models local pending, streaming, complete, and error states for one response
with a stable message_id, records the intermediate state after every step, and
verifies invariants linking intermediate snapshots to the final output.
Purely local in-memory simulation (no network calls, models, or live APIs).
"""

from __future__ import annotations

import argparse
import json
import sys
from enum import Enum
from typing import Any, Mapping, Sequence


class ResponseState(str, Enum):
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


TERMINAL_STATES = frozenset({ResponseState.COMPLETE, ResponseState.ERROR})

SYNTHETIC_FIXTURES: dict[str, Any] = {
    "normal_two_chunks_complete": {
        "message_id": "msg-001",
        "chunks": ["Hello ", "world"],
    },
    "boundary_error_preserves_text": {
        "message_id": "msg-002",
        "chunks": ["Partial "],
        "error_reason": "stream interrupted",
    },
    "failure_chunk_after_completion": {
        "message_id": "msg-003",
        "chunks": ["Done"],
        "late_chunk": " late",
    },
}


class LocalStreamingTracker:
    """Tracks one streaming response and records intermediate state per step."""

    def __init__(self, message_id: str) -> None:
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("message_id must be a non-empty string")
        self._message_id = message_id
        self._state = ResponseState.PENDING
        self._chunks: list[str] = []
        self._error_marker: str | None = None
        self._snapshots: list[dict[str, Any]] = []
        self._record_snapshot(action="init", accepted=True)

    @property
    def message_id(self) -> str:
        return self._message_id

    @property
    def state(self) -> ResponseState:
        return self._state

    @property
    def received_text(self) -> str:
        return "".join(self._chunks)

    @property
    def display_text(self) -> str:
        if self._error_marker is None:
            return self.received_text
        return f"{self.received_text}{self._error_marker}"

    @property
    def snapshots(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._snapshots]

    def _record_snapshot(
        self,
        *,
        action: str,
        accepted: bool,
        chunk: str | None = None,
        rejection_reason: str | None = None,
    ) -> None:
        self._snapshots.append(
            {
                "step": len(self._snapshots),
                "action": action,
                "accepted": accepted,
                "chunk": chunk,
                "message_id": self._message_id,
                "status": self._state.value,
                "received_text": self.received_text,
                "error_marker": self._error_marker,
                "display_text": self.display_text,
                "rejection_reason": rejection_reason,
            }
        )

    def append_chunk(self, chunk: str) -> str:
        if not isinstance(chunk, str):
            reason = f"chunk must be a str, got {type(chunk).__name__}"
            self._record_snapshot(
                action="append_chunk",
                accepted=False,
                rejection_reason=reason,
            )
            raise ValueError(reason)

        if self._state in TERMINAL_STATES:
            reason = (
                f"Cannot append chunk when response '{self._message_id}' "
                f"is in terminal state '{self._state.value}'"
            )
            self._record_snapshot(
                action="append_chunk",
                accepted=False,
                chunk=chunk,
                rejection_reason=reason,
            )
            raise ValueError(reason)

        self._state = ResponseState.STREAMING
        self._chunks.append(chunk)
        self._record_snapshot(action="append_chunk", accepted=True, chunk=chunk)
        return self.received_text

    def complete(self) -> str:
        if self._state in TERMINAL_STATES:
            reason = (
                f"Cannot complete response '{self._message_id}' "
                f"from terminal state '{self._state.value}'"
            )
            self._record_snapshot(
                action="complete",
                accepted=False,
                rejection_reason=reason,
            )
            raise ValueError(reason)

        self._state = ResponseState.COMPLETE
        self._record_snapshot(action="complete", accepted=True)
        return self.received_text

    def fail(self, error_reason: str) -> str:
        if not isinstance(error_reason, str) or not error_reason.strip():
            reason = "error_reason must be a non-empty string"
            self._record_snapshot(
                action="fail",
                accepted=False,
                rejection_reason=reason,
            )
            raise ValueError(reason)

        if self._state in TERMINAL_STATES:
            reason = (
                f"Cannot fail response '{self._message_id}' "
                f"from terminal state '{self._state.value}'"
            )
            self._record_snapshot(
                action="fail",
                accepted=False,
                rejection_reason=reason,
            )
            raise ValueError(reason)

        self._state = ResponseState.ERROR
        self._error_marker = f"[ERROR: {error_reason.strip()}]"
        self._record_snapshot(action="fail", accepted=True)
        return self.display_text

    def final_output(self) -> dict[str, Any]:
        return {
            "simulation": True,
            "message_id": self._message_id,
            "status": self._state.value,
            "received_text": self.received_text,
            "error_marker": self._error_marker,
            "display_text": self.display_text,
        }


def verify_trace_invariants(
    snapshots: Sequence[Mapping[str, Any]],
    final_output: dict[str, Any],
) -> dict[str, bool]:
    """Verify invariants linking recorded intermediate snapshots to final_output."""
    if not snapshots:
        raise AssertionError("snapshots must not be empty")

    target_id = final_output["message_id"]
    stable_message_id = all(snap["message_id"] == target_id for snap in snapshots)
    if not stable_message_id:
        raise AssertionError("message_id changed across intermediate snapshots")

    monotonic_received_text = True
    accepted_chunks: list[str] = []
    terminal_seen = False
    terminal_state_immutable = True

    for index, snap in enumerate(snapshots):
        if snap["action"] == "append_chunk" and snap["accepted"]:
            accepted_chunks.append(snap["chunk"])
        if index > 0:
            prev = snapshots[index - 1]
            if not snap["received_text"].startswith(prev["received_text"]):
                monotonic_received_text = False
            if terminal_seen and (
                snap["accepted"]
                or snap["status"] != prev["status"]
                or snap["received_text"] != prev["received_text"]
                or snap["error_marker"] != prev["error_marker"]
                or snap["display_text"] != prev["display_text"]
            ):
                terminal_state_immutable = False
        if snap["status"] in ("complete", "error"):
            terminal_seen = True

    if not monotonic_received_text:
        raise AssertionError("received_text was not monotonically preserved across steps")
    if not terminal_state_immutable:
        raise AssertionError("terminal state mutated after reaching complete/error")

    last = snapshots[-1]
    links_to_final_output = (
        last["message_id"] == final_output["message_id"]
        and last["status"] == final_output["status"]
        and last["received_text"] == final_output["received_text"]
        and last["error_marker"] == final_output["error_marker"]
        and last["display_text"] == final_output["display_text"]
        and "".join(accepted_chunks) == final_output["received_text"]
    )
    if not links_to_final_output:
        raise AssertionError("intermediate trace does not match final_output")

    if final_output["status"] == "error":
        if not final_output["error_marker"] or (
            final_output["display_text"]
            != f"{final_output['received_text']}{final_output['error_marker']}"
        ):
            raise AssertionError("error output missing preserved text + error marker")
    elif final_output["status"] == "complete":
        if (
            final_output["error_marker"] is not None
            or final_output["display_text"] != final_output["received_text"]
        ):
            raise AssertionError("complete output must not carry an error marker")

    return {
        "stable_message_id": stable_message_id,
        "monotonic_received_text": monotonic_received_text,
        "terminal_state_immutable": terminal_state_immutable,
        "links_to_final_output": links_to_final_output,
    }


def run_normal_case() -> dict[str, Any]:
    cfg = SYNTHETIC_FIXTURES["normal_two_chunks_complete"]
    tracker = LocalStreamingTracker(cfg["message_id"])
    for chunk in cfg["chunks"]:
        tracker.append_chunk(chunk)
    tracker.complete()
    snapshots = tracker.snapshots
    final_output = tracker.final_output()
    invariants = verify_trace_invariants(snapshots, final_output)
    return {
        "scenario": "normal_two_chunks_complete",
        "intermediate_states": snapshots,
        "final_output": final_output,
        "invariants": invariants,
    }


def run_boundary_error_case() -> dict[str, Any]:
    cfg = SYNTHETIC_FIXTURES["boundary_error_preserves_text"]
    tracker = LocalStreamingTracker(cfg["message_id"])
    for chunk in cfg["chunks"]:
        tracker.append_chunk(chunk)
    tracker.fail(cfg["error_reason"])
    snapshots = tracker.snapshots
    final_output = tracker.final_output()
    invariants = verify_trace_invariants(snapshots, final_output)
    return {
        "scenario": "boundary_error_preserves_text",
        "intermediate_states": snapshots,
        "final_output": final_output,
        "invariants": invariants,
    }


def run_failure_late_chunk_case() -> dict[str, Any]:
    cfg = SYNTHETIC_FIXTURES["failure_chunk_after_completion"]
    tracker = LocalStreamingTracker(cfg["message_id"])
    for chunk in cfg["chunks"]:
        tracker.append_chunk(chunk)
    tracker.complete()

    rejected = False
    rejection_error: str | None = None
    try:
        tracker.append_chunk(cfg["late_chunk"])
    except ValueError as exc:
        rejected = True
        rejection_error = str(exc)

    snapshots = tracker.snapshots
    final_output = tracker.final_output()
    invariants = verify_trace_invariants(snapshots, final_output)
    return {
        "scenario": "failure_chunk_after_completion",
        "rejected": rejected,
        "rejection_error": rejection_error,
        "intermediate_states": snapshots,
        "final_output": final_output,
        "invariants": invariants,
    }


def run_scenario(name: str = "all") -> dict[str, Any]:
    runners = {
        "normal": run_normal_case,
        "boundary_error": run_boundary_error_case,
        "late_chunk": run_failure_late_chunk_case,
    }
    if name == "all":
        results = [runner() for runner in runners.values()]
    elif name in runners:
        results = [runners[name]()]
    else:
        raise ValueError(f"Unknown scenario: {name}")
    return {"simulation": True, "scenario": name, "results": results}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate local streaming states with intermediate snapshots and "
            "trace-to-output invariant verification."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=("all", "normal", "boundary_error", "late_chunk"),
        default="all",
        help="Scenario to run (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        payload = run_scenario(args.scenario)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
