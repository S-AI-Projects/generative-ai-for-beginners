"""Local synthetic response-streaming state machine for Lesson 11.

Models local pending, streaming, complete, and error states for a single
response with a stable message_id. All fixtures and transitions are purely
local in-memory simulations (no network calls, model downloads, or live APIs).
"""

from __future__ import annotations

import argparse
import json
import sys
from enum import Enum
from typing import Any, Sequence


class ResponseState(str, Enum):
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


TERMINAL_STATES = frozenset({ResponseState.COMPLETE, ResponseState.ERROR})

# Smallest valid, boundary, and invalid teaching fixtures.
SYNTHETIC_FIXTURE: dict[str, Any] = {
    "smallest_valid": {
        "message_id": "msg-valid-001",
        "chunks": ["Hello ", "world"],
    },
    "boundary_error_preserves_text": {
        "message_id": "msg-boundary-002",
        "chunks": ["Partial "],
        "error_reason": "stream interrupted",
    },
    "boundary_zero_chunk_complete": {
        "message_id": "msg-boundary-003",
        "chunks": [],
    },
    "invalid_chunk_after_completion": {
        "message_id": "msg-invalid-004",
        "chunks": ["Done"],
        "late_chunk": " late",
    },
}


class LocalStreamingResponse:
    """In-memory streaming response lifecycle with a stable message ID."""

    def __init__(self, message_id: str) -> None:
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("message_id must be a non-empty string")
        self._message_id = message_id
        self._state = ResponseState.PENDING
        self._chunks: list[str] = []
        self._error_reason: str | None = None
        self._error_marker: str | None = None

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

    def append_chunk(self, chunk: str) -> str:
        if not isinstance(chunk, str):
            raise ValueError(f"chunk must be a str, got {type(chunk).__name__}")
        # Boundary decision: terminal states (complete, error) reject all new chunks.
        if self._state in TERMINAL_STATES:
            raise ValueError(
                f"Cannot append chunk when response '{self._message_id}' "
                f"is in terminal state '{self._state.value}'"
            )
        self._state = ResponseState.STREAMING
        self._chunks.append(chunk)
        return self.received_text

    def complete(self) -> str:
        if self._state in TERMINAL_STATES:
            raise ValueError(
                f"Cannot complete response '{self._message_id}' "
                f"from terminal state '{self._state.value}'"
            )
        # Boundary decision: 0-chunk completion directly from pending is allowed.
        self._state = ResponseState.COMPLETE
        return self.received_text

    def fail(self, reason: str) -> str:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("error reason must be a non-empty string")
        if self._state in TERMINAL_STATES:
            raise ValueError(
                f"Cannot fail response '{self._message_id}' "
                f"from terminal state '{self._state.value}'"
            )
        self._state = ResponseState.ERROR
        self._error_reason = reason.strip()
        self._error_marker = f"[ERROR: {self._error_reason}]"
        return self.display_text

    def to_dict(self) -> dict[str, Any]:
        return {
            "simulation": True,
            "message_id": self._message_id,
            "status": self._state.value,
            "chunks_received": list(self._chunks),
            "received_text": self.received_text,
            "error_marker": self._error_marker,
            "display_text": self.display_text,
        }


def run_smallest_valid_case(
    message_id: str = SYNTHETIC_FIXTURE["smallest_valid"]["message_id"],
    chunks: Sequence[str] = SYNTHETIC_FIXTURE["smallest_valid"]["chunks"],
) -> dict[str, Any]:
    response = LocalStreamingResponse(message_id)
    transitions = [response.state.value]
    for chunk in chunks:
        response.append_chunk(chunk)
        transitions.append(response.state.value)
    response.complete()
    transitions.append(response.state.value)
    return {
        "case": "smallest_valid",
        "transitions": transitions,
        "result": response.to_dict(),
    }


def run_boundary_error_case(
    message_id: str = SYNTHETIC_FIXTURE["boundary_error_preserves_text"]["message_id"],
    chunks: Sequence[str] = SYNTHETIC_FIXTURE["boundary_error_preserves_text"]["chunks"],
    error_reason: str = SYNTHETIC_FIXTURE["boundary_error_preserves_text"]["error_reason"],
) -> dict[str, Any]:
    response = LocalStreamingResponse(message_id)
    transitions = [response.state.value]
    for chunk in chunks:
        response.append_chunk(chunk)
        transitions.append(response.state.value)
    response.fail(error_reason)
    transitions.append(response.state.value)
    return {
        "case": "boundary_error_preserves_text",
        "transitions": transitions,
        "result": response.to_dict(),
    }


def run_boundary_zero_chunk_case(
    message_id: str = SYNTHETIC_FIXTURE["boundary_zero_chunk_complete"]["message_id"],
) -> dict[str, Any]:
    response = LocalStreamingResponse(message_id)
    transitions = [response.state.value]
    response.complete()
    transitions.append(response.state.value)
    return {
        "case": "boundary_zero_chunk_complete",
        "transitions": transitions,
        "result": response.to_dict(),
    }


def run_invalid_late_chunk_case(
    message_id: str = SYNTHETIC_FIXTURE["invalid_chunk_after_completion"]["message_id"],
    chunks: Sequence[str] = SYNTHETIC_FIXTURE["invalid_chunk_after_completion"]["chunks"],
    late_chunk: str = SYNTHETIC_FIXTURE["invalid_chunk_after_completion"]["late_chunk"],
) -> dict[str, Any]:
    response = LocalStreamingResponse(message_id)
    transitions = [response.state.value]
    for chunk in chunks:
        response.append_chunk(chunk)
        transitions.append(response.state.value)
    response.complete()
    transitions.append(response.state.value)

    rejected = False
    rejection_reason: str | None = None
    try:
        response.append_chunk(late_chunk)
    except ValueError as exc:
        rejected = True
        rejection_reason = str(exc)

    return {
        "case": "invalid_chunk_after_completion",
        "transitions": transitions,
        "late_chunk": late_chunk,
        "rejected": rejected,
        "rejection_reason": rejection_reason,
        "result": response.to_dict(),
    }


def run_fixture_suite(scenario: str = "all") -> dict[str, Any]:
    runners = {
        "valid": run_smallest_valid_case,
        "boundary_error": run_boundary_error_case,
        "boundary_zero": run_boundary_zero_chunk_case,
        "invalid_late_chunk": run_invalid_late_chunk_case,
    }
    if scenario == "all":
        cases = [runner() for runner in runners.values()]
    elif scenario in runners:
        cases = [runners[scenario]()]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return {"simulation": True, "scenario": scenario, "cases": cases}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate local response streaming states (pending, streaming, "
            "complete, error) with a stable message ID."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=("all", "valid", "boundary_error", "boundary_zero", "invalid_late_chunk"),
        default="all",
        help="Fixture case to run (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        payload = run_fixture_suite(args.scenario)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
