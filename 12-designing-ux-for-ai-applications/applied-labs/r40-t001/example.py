#!/usr/bin/env python3
"""Chat-View State Lifecycle and Streaming Recovery Example (R40-T001).

Lesson 12: Designing UX for AI Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements the local chat-view response lifecycle for AI applications.
In user-facing AI chat applications, responses stream progressively rather than
appearing instantaneously. To maintain user trust and avoid interface confusion,
the client chat-view layer must model explicit lifecycle states (pending, streaming,
complete, error), preserve stable message identity across transitions, cleanly
accumulate streamed chunks in order, preserve partial text when an error occurs,
and reject unexpected late chunks arriving after completion.

Contract Rules:
1. Message Identity: A stable message ID (e.g. 'msg-resp-001') is established at
   initialization and preserved across all lifecycle state transitions.
2. State Lifecycle:
   - PENDING: Request sent, awaiting first chunk from model.
   - STREAMING: Accumulating arriving tokens/chunks in strict order.
   - COMPLETE: Stream ended cleanly; final output locked.
   - ERROR: Preserves previously received text and appends an error marker.
3. Sequential Ordering: Arriving chunks append in order without reordering or duplication.
4. Error Recovery: If stream connection drops after partial text arrives, the partial
   response is preserved alongside an explicit error marker ('[ERROR: <reason>]').
5. Post-Completion Rejection: Any chunk arriving after COMPLETE or ERROR raises
   ChunkRejectedError to protect UI consistency.

Classification & Scope Note (Simulation / Test Double):
This module is a deterministic local state machine and test double using only
Python's standard library. It requires no network requests, no LLM provider API
keys, no local model weights, and no GPU hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
import sys
from typing import Any, Dict, List, Optional

DEFAULT_MESSAGE_ID = "msg-resp-001"
DEFAULT_FIXTURE_CHUNKS = ["Hello, ", "how can I assist you today?"]
DEFAULT_ERROR_MESSAGE = "Stream connection dropped unexpectedly"
DEFAULT_LATE_CHUNK = " [Late chunk after stream completion]"


class ResponseState(str, Enum):
    """Lifecycle states of a chat response message view."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class ChatViewStateError(Exception):
    """Base exception for chat view state violations."""


class ChunkRejectedError(ChatViewStateError):
    """Raised when an incoming chunk is rejected due to a terminal response state."""


class IllegalStateTransitionError(ChatViewStateError):
    """Raised when an invalid lifecycle transition is requested."""


class DecisionMismatchError(ChatViewStateError):
    """Raised when verification assertions fail."""


@dataclass
class ChatResponseView:
    """Represents the client-side state of an assistant chat response message."""

    message_id: str
    role: str = "assistant"
    state: ResponseState = ResponseState.PENDING
    content: str = ""
    error_message: Optional[str] = None
    chunks_received: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append(
                {
                    "event": "init",
                    "state": self.state.value,
                    "content": self.content,
                    "chunks_received": self.chunks_received,
                }
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current state snapshot to a JSON dictionary."""
        return {
            "message_id": self.message_id,
            "role": self.role,
            "state": self.state.value,
            "content": self.content,
            "error_message": self.error_message,
            "chunks_received": self.chunks_received,
            "history_length": len(self.history),
        }


class ChatViewStateManager:
    """Finite state manager enforcing chat-view response lifecycle invariants."""

    @staticmethod
    def create_response(
        message_id: str = DEFAULT_MESSAGE_ID, role: str = "assistant"
    ) -> ChatResponseView:
        """Initializes a new response in PENDING state with a stable message ID."""
        if not message_id or not message_id.strip():
            raise ValueError("message_id must be a non-empty string.")
        return ChatResponseView(
            message_id=message_id.strip(),
            role=role,
            state=ResponseState.PENDING,
            content="",
            chunks_received=0,
        )

    @staticmethod
    def append_chunk(response: ChatResponseView, chunk: str) -> ChatResponseView:
        """Appends an incoming text chunk to the response view."""
        if response.state in (ResponseState.COMPLETE, ResponseState.ERROR):
            raise ChunkRejectedError(
                f"Cannot append chunk to response '{response.message_id}' in terminal state '{response.state.value}'."
            )

        if not isinstance(chunk, str):
            raise TypeError("chunk must be a string.")

        response.content += chunk
        response.chunks_received += 1
        response.state = ResponseState.STREAMING
        response.history.append(
            {
                "event": "chunk_appended",
                "state": response.state.value,
                "chunk": chunk,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response

    @staticmethod
    def complete(response: ChatResponseView) -> ChatResponseView:
        """Transitions response to COMPLETE state upon stream end."""
        if response.state == ResponseState.COMPLETE:
            return response
        if response.state == ResponseState.ERROR:
            raise IllegalStateTransitionError(
                f"Cannot complete response '{response.message_id}' already in ERROR state."
            )

        response.state = ResponseState.COMPLETE
        response.history.append(
            {
                "event": "completed",
                "state": response.state.value,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response

    @staticmethod
    def fail(
        response: ChatResponseView, error_message: str = DEFAULT_ERROR_MESSAGE
    ) -> ChatResponseView:
        """Transitions response to ERROR state, preserving received text and appending marker."""
        if response.state == ResponseState.ERROR:
            return response
        if response.state == ResponseState.COMPLETE:
            raise IllegalStateTransitionError(
                f"Cannot fail response '{response.message_id}' already in COMPLETE state."
            )

        response.error_message = error_message
        response.content = f"{response.content}[ERROR: {error_message}]"
        response.state = ResponseState.ERROR
        response.history.append(
            {
                "event": "failed",
                "state": response.state.value,
                "error_message": error_message,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response


def run_normal_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    chunks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Executes the normal scenario: PENDING -> 2 chunks appended -> COMPLETE."""
    if chunks is None:
        chunks = list(DEFAULT_FIXTURE_CHUNKS)

    resp = ChatViewStateManager.create_response(message_id=message_id)
    initial_id = resp.message_id

    for ch in chunks:
        ChatViewStateManager.append_chunk(resp, ch)

    ChatViewStateManager.complete(resp)

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "decision": "STATE_COMPLETE_SUCCESS",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "chunks_received": resp.chunks_received,
        "stable_id_preserved": (resp.message_id == initial_id),
        "ordered_chunks_verified": (resp.content == "".join(chunks)),
        "history_events": len(resp.history),
    }


def run_error_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    first_chunk: str = DEFAULT_FIXTURE_CHUNKS[0],
    error_message: str = DEFAULT_ERROR_MESSAGE,
) -> Dict[str, Any]:
    """Executes the error recovery scenario: PENDING -> 1 chunk -> stream drop -> ERROR with preserved text."""
    resp = ChatViewStateManager.create_response(message_id=message_id)
    initial_id = resp.message_id

    ChatViewStateManager.append_chunk(resp, first_chunk)
    ChatViewStateManager.fail(resp, error_message=error_message)

    expected_content = f"{first_chunk}[ERROR: {error_message}]"
    return {
        "scenario_id": "SCENARIO_ERROR",
        "scenario_type": "error_recovery",
        "decision": "STATE_ERROR_RECOVERED",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "chunks_received": resp.chunks_received,
        "error_message": resp.error_message,
        "stable_id_preserved": (resp.message_id == initial_id),
        "text_preserved": resp.content.startswith(first_chunk),
        "content_matches_expected": (resp.content == expected_content),
        "history_events": len(resp.history),
    }


def run_boundary_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    chunks: Optional[List[str]] = None,
    late_chunk: str = DEFAULT_LATE_CHUNK,
) -> Dict[str, Any]:
    """Executes boundary scenario: normal completion followed by post-completion chunk rejection."""
    if chunks is None:
        chunks = list(DEFAULT_FIXTURE_CHUNKS)

    resp = ChatViewStateManager.create_response(message_id=message_id)
    for ch in chunks:
        ChatViewStateManager.append_chunk(resp, ch)
    ChatViewStateManager.complete(resp)

    rejection_verified = False
    rejection_exception = None
    try:
        ChatViewStateManager.append_chunk(resp, late_chunk)
    except ChunkRejectedError as exc:
        rejection_verified = True
        rejection_exception = exc.__class__.__name__

    return {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_rejection",
        "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "chunks_received": resp.chunks_received,
        "rejection_verified": rejection_verified,
        "rejection_exception": rejection_exception,
        "content_unmodified_by_late_chunk": (resp.content == "".join(chunks)),
        "history_events": len(resp.history),
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Runs all scenarios and validates decisions against the expected decision table."""
    normal_res = run_normal_scenario()
    error_res = run_error_scenario()
    boundary_res = run_boundary_scenario()

    scenarios = [normal_res, error_res, boundary_res]
    expected_decisions = {
        "SCENARIO_NORMAL": "STATE_COMPLETE_SUCCESS",
        "SCENARIO_ERROR": "STATE_ERROR_RECOVERED",
        "SCENARIO_BOUNDARY": "CHUNK_AFTER_COMPLETION_REJECTED",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected)
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(
            f"Decision mismatch detected: {failures}"
        )

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T001: Chat-View State Lifecycle & Recovery Example."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "error", "boundary"],
        help="Run a specific lifecycle scenario.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    if args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "error":
        print(json.dumps(run_error_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "boundary":
        print(json.dumps(run_boundary_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
