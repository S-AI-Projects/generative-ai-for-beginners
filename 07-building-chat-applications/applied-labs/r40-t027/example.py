#!/usr/bin/env python3
"""Chat-View State Lifecycle and Streaming Recovery Worked Example (R40-T027).

Lesson 07: Building Generative AI-Powered Chat Applications.
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab models the local chat-view response lifecycle for generative AI chat
applications. In production systems (such as OpenAI Responses API or Azure OpenAI),
chat responses are streamed incrementally rather than delivered in a single batch.
The client chat-view layer must manage message identity, progressive chunk
rendering, clean stream termination, resilient error recovery, and strict boundary
protections against late or corrupted packets.

Contract Rules Implemented:
1. Message Identity: A stable message ID (e.g. 'msg-resp-001') is assigned at
   request initiation and remains constant across all state transitions.
2. State Lifecycle: Models four local states:
   - PENDING: Request in flight, awaiting initial chunk (content: empty).
   - STREAMING: Sequentially accumulating arriving chunks in order.
   - COMPLETE: Stream closed successfully; response finalized.
   - ERROR: Preserves previously received text and appends an explicit error marker.
3. Sequential Ordering: Two sequential chunks append strictly in arrival order:
   Chunk 1 ('Hello, ') followed by Chunk 2 ('how can I assist you today?').
4. Error Recovery: If stream fails after receiving partial content, already received
   text is NEVER discarded; an error marker ('[ERROR: <reason>]') is appended.
5. Terminal State Invariant: Any chunk received after stream completion (or failure)
   is strictly REJECTED by raising ChunkRejectedError, protecting state integrity.

Classification & Scope Note (Simulation / Test Double):
This module is a deterministic local state machine and test double using only
Python's standard library. It requires no network requests, no LLM provider API
keys, no local model weights, and no GPU or physical hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
import sys
from typing import Any, Dict, List, Optional


class ResponseState(str, Enum):
    """Lifecycle states of a chat response message view."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class ChatViewStateError(Exception):
    """Base exception for chat view state errors."""


class ChunkRejectedError(ChatViewStateError):
    """Raised when an incoming chunk is rejected due to terminal response state."""


class IllegalStateTransitionError(ChatViewStateError):
    """Raised when an illegal lifecycle transition is requested."""


class DecisionMismatchError(ChatViewStateError):
    """Raised when an assertion or verification check detects an unexpected outcome."""


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
        """Serializes current state snapshot to a JSON-compatible dictionary."""
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
    """Finite state manager enforcing the chat-view response lifecycle contract."""

    @staticmethod
    def create_response(
        message_id: str = "msg-resp-001", role: str = "assistant"
    ) -> ChatResponseView:
        """Initializes a new response in PENDING state with a stable message ID."""
        if not message_id or not message_id.strip():
            raise ValueError("message_id must be a non-empty string.")
        return ChatResponseView(
            message_id=message_id,
            role=role,
            state=ResponseState.PENDING,
            content="",
            error_message=None,
            chunks_received=0,
        )

    @staticmethod
    def append_chunk(response: ChatResponseView, chunk: str) -> ChatResponseView:
        """Appends an incoming chunk to the response content buffer in order.

        Transitions:
        - PENDING -> STREAMING: on first chunk arrival.
        - STREAMING -> STREAMING: on subsequent chunk arrival.
        - COMPLETE / ERROR -> Rejection: raises ChunkRejectedError.
        """
        if response.state in (ResponseState.COMPLETE, ResponseState.ERROR):
            rejection_event = {
                "event": "chunk_rejected",
                "attempted_chunk": chunk,
                "current_state": response.state.value,
                "reason": f"Cannot append chunk '{chunk}' in terminal state '{response.state.value}'.",
            }
            response.history.append(rejection_event)
            raise ChunkRejectedError(
                f"Chunk rejected: response '{response.message_id}' is in terminal state '{response.state.value}'."
            )

        # Transition PENDING to STREAMING on first chunk
        if response.state == ResponseState.PENDING:
            response.state = ResponseState.STREAMING

        response.content += chunk
        response.chunks_received += 1
        response.history.append(
            {
                "event": "chunk_appended",
                "chunk": chunk,
                "state": response.state.value,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response

    @staticmethod
    def complete_response(response: ChatResponseView) -> ChatResponseView:
        """Transitions a response to COMPLETE state upon stream termination."""
        if response.state == ResponseState.ERROR:
            raise IllegalStateTransitionError(
                f"Cannot complete response '{response.message_id}' from error state."
            )
        if response.state == ResponseState.COMPLETE:
            # Idempotent completion
            return response

        response.state = ResponseState.COMPLETE
        response.history.append(
            {
                "event": "stream_completed",
                "state": response.state.value,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response

    @staticmethod
    def fail_response(
        response: ChatResponseView,
        error_msg: str,
        marker_template: str = "[ERROR: {error}]",
    ) -> ChatResponseView:
        """Transitions a response to ERROR state while strictly preserving received text."""
        if response.state == ResponseState.COMPLETE:
            raise IllegalStateTransitionError(
                f"Cannot fail response '{response.message_id}' after it has already completed."
            )

        marker = marker_template.format(error=error_msg)
        separator = (
            ""
            if (
                not response.content
                or response.content.endswith(" ")
                or response.content.endswith("\n")
            )
            else " "
        )

        preserved_text = response.content
        response.content = f"{response.content}{separator}{marker}"
        response.state = ResponseState.ERROR
        response.error_message = error_msg
        response.history.append(
            {
                "event": "stream_error",
                "error": error_msg,
                "marker": marker,
                "preserved_text": preserved_text,
                "state": response.state.value,
                "content": response.content,
                "chunks_received": response.chunks_received,
            }
        )
        return response


# =============================================================================
# Canonical Fixtures & Scenario Workflows
# =============================================================================

DEFAULT_MESSAGE_ID = "msg-resp-001"
DEFAULT_FIXTURE_CHUNKS = ["Hello, ", "how can I assist you today?"]
DEFAULT_ERROR_MESSAGE = "Stream connection dropped"
DEFAULT_LATE_CHUNK = " [Late chunk arriving after stream close]"


def run_normal_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    chunks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Executes the normal two-chunk streaming scenario to full completion."""
    if chunks is None:
        chunks = list(DEFAULT_FIXTURE_CHUNKS)

    manager = ChatViewStateManager()
    resp = manager.create_response(message_id=message_id)

    # Initial pending check
    assert resp.state == ResponseState.PENDING
    assert resp.content == ""
    assert resp.chunks_received == 0
    assert resp.message_id == message_id

    # Append chunk 1
    manager.append_chunk(resp, chunks[0])
    assert resp.state == ResponseState.STREAMING
    assert resp.content == chunks[0]
    assert resp.chunks_received == 1
    assert resp.message_id == message_id

    # Append chunk 2
    manager.append_chunk(resp, chunks[1])
    assert resp.state == ResponseState.STREAMING
    assert resp.content == "".join(chunks)
    assert resp.chunks_received == 2
    assert resp.message_id == message_id

    # Complete stream
    manager.complete_response(resp)
    assert resp.state == ResponseState.COMPLETE
    assert resp.content == "".join(chunks)
    assert resp.error_message is None
    assert resp.message_id == message_id

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "decision": "STATE_COMPLETE_SUCCESS",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "chunks_received": resp.chunks_received,
        "error_message": resp.error_message,
        "stable_id_preserved": (resp.message_id == message_id),
        "ordered_chunks_verified": (resp.content == "".join(chunks)),
        "rationale": (
            f"Response '{message_id}' initialized in PENDING state, sequentially appended "
            f"{len(chunks)} chunks in arrival order, and completed successfully with stable ID."
        ),
        "classification": "chat_view_state_simulation",
    }


def run_error_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    chunks: Optional[List[str]] = None,
    error_msg: str = DEFAULT_ERROR_MESSAGE,
) -> Dict[str, Any]:
    """Executes the error recovery scenario preserving received text with an error marker."""
    if chunks is None:
        chunks = list(DEFAULT_FIXTURE_CHUNKS)

    manager = ChatViewStateManager()
    resp = manager.create_response(message_id=message_id)

    # Receive partial chunk
    manager.append_chunk(resp, chunks[0])
    preserved_prefix = resp.content

    # Network / transport failure occurs
    manager.fail_response(resp, error_msg=error_msg)

    assert resp.state == ResponseState.ERROR
    assert resp.error_message == error_msg
    assert resp.message_id == message_id
    assert preserved_prefix in resp.content
    assert f"[ERROR: {error_msg}]" in resp.content

    return {
        "scenario_id": "SCENARIO_ERROR",
        "scenario_type": "error_recovery",
        "decision": "STATE_ERROR_RECOVERED",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "preserved_prefix": preserved_prefix,
        "error_marker": f"[ERROR: {error_msg}]",
        "error_message": resp.error_message,
        "chunks_received": resp.chunks_received,
        "text_preserved": (preserved_prefix in resp.content),
        "rationale": (
            f"Response '{message_id}' received chunk 1 ('{preserved_prefix}') before stream failed. "
            f"The error preserved previously received text intact and appended error marker."
        ),
        "classification": "chat_view_state_simulation",
    }


def run_boundary_scenario(
    message_id: str = DEFAULT_MESSAGE_ID,
    chunks: Optional[List[str]] = None,
    late_chunk: str = DEFAULT_LATE_CHUNK,
) -> Dict[str, Any]:
    """Executes the boundary scenario verifying rejection of chunks arriving after completion."""
    if chunks is None:
        chunks = list(DEFAULT_FIXTURE_CHUNKS)

    manager = ChatViewStateManager()
    resp = manager.create_response(message_id=message_id)

    # Bring to COMPLETE state
    for ch in chunks:
        manager.append_chunk(resp, ch)
    manager.complete_response(resp)

    expected_content = "".join(chunks)
    assert resp.state == ResponseState.COMPLETE
    assert resp.content == expected_content

    # Attempt to append chunk after completion
    rejection_caught = False
    rejection_exception_name = None
    try:
        manager.append_chunk(resp, late_chunk)
    except ChunkRejectedError as exc:
        rejection_caught = True
        rejection_exception_name = exc.__class__.__name__

    # Content and state must be unaffected
    assert rejection_caught is True
    assert resp.state == ResponseState.COMPLETE
    assert resp.content == expected_content
    assert resp.chunks_received == len(chunks)

    return {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_rejection",
        "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "message_id": resp.message_id,
        "state": resp.state.value,
        "content": resp.content,
        "chunks_received": resp.chunks_received,
        "attempted_late_chunk": late_chunk,
        "rejection_verified": rejection_caught,
        "rejection_exception": rejection_exception_name,
        "rationale": (
            f"Response '{message_id}' reached COMPLETE state. Incoming late chunk "
            f"'{late_chunk}' was rejected with {rejection_exception_name}, preserving "
            f"the finalized response buffer without corruption."
        ),
        "classification": "chat_view_state_simulation",
    }


# =============================================================================
# Canonical Decision Table & Verification Engine
# =============================================================================

CANONICAL_DECISION_TABLE = [
    {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "expected_decision": "STATE_COMPLETE_SUCCESS",
        "expected_state": "complete",
        "expected_chunks_received": 2,
        "expected_content": "Hello, how can I assist you today?",
    },
    {
        "scenario_id": "SCENARIO_ERROR",
        "scenario_type": "error_recovery",
        "expected_decision": "STATE_ERROR_RECOVERED",
        "expected_state": "error",
        "expected_chunks_received": 1,
        "expected_content": "Hello, [ERROR: Stream connection dropped]",
    },
    {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_rejection",
        "expected_decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "expected_state": "complete",
        "expected_chunks_received": 2,
        "expected_content": "Hello, how can I assist you today?",
    },
]


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Runs all canonical scenarios and validates them against the decision table.

    If tamper=True, deliberately introduces a specification mismatch to prove
    that regressions and unexpected results strictly fail verification.
    """
    results: List[Dict[str, Any]] = []
    scenarios_data = [
        run_normal_scenario(),
        run_error_scenario(),
        run_boundary_scenario(),
    ]

    for expected_spec, actual_data in zip(CANONICAL_DECISION_TABLE, scenarios_data):
        expected_decision = expected_spec["expected_decision"]
        if tamper and expected_spec["scenario_id"] == "SCENARIO_NORMAL":
            # Deliberately mutate expectation to simulate wrong assertion
            expected_decision = "DELIBERATE_MUTATED_DECISION"

        matches = (
            actual_data["decision"] == expected_decision
            and actual_data["state"] == expected_spec["expected_state"]
            and actual_data["chunks_received"] == expected_spec["expected_chunks_received"]
            and actual_data["content"] == expected_spec["expected_content"]
        )

        item = {
            "scenario_id": expected_spec["scenario_id"],
            "scenario_type": expected_spec["scenario_type"],
            "expected_decision": expected_decision,
            "actual_decision": actual_data["decision"],
            "expected_state": expected_spec["expected_state"],
            "actual_state": actual_data["state"],
            "matches_table": matches,
            "status": "PASS" if matches else "FAIL",
            "message_id": actual_data["message_id"],
            "content": actual_data["content"],
            "rationale": actual_data["rationale"],
        }
        results.append(item)

    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    passed_count = len(results) - failed_count

    summary = {
        "status": "success" if failed_count == 0 else "failure",
        "total_scenarios": len(results),
        "passed_scenarios": passed_count,
        "failed_scenarios": failed_count,
        "all_passed": (failed_count == 0),
        "classification": "chat_view_state_simulation",
        "scenarios": results,
    }

    if failed_count > 0:
        raise DecisionMismatchError(
            f"Verification failed: {failed_count} scenario(s) did not match the canonical decision table."
        )

    return summary


# =============================================================================
# CLI Entrypoint
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Configures command line arguments."""
    parser = argparse.ArgumentParser(
        description="R40-T027: Chat-View State Lifecycle & Recovery Worked Example"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scenario",
        choices=["normal", "error", "boundary"],
        help="Run an individual scenario and output structured JSON.",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Run all canonical scenarios against the decision table.",
    )
    group.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate a deliberate regression to prove failure detection.",
    )
    return parser


def main() -> int:
    """CLI main function."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.scenario == "normal":
            data = run_normal_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.scenario == "error":
            data = run_error_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.scenario == "boundary":
            data = run_boundary_scenario()
            print(json.dumps(data, indent=2))
            return 0

        if args.check:
            data = run_canonical_check(tamper=False)
            print(json.dumps(data, indent=2))
            return 0

        if args.tamper:
            try:
                run_canonical_check(tamper=True)
            except DecisionMismatchError as err:
                tamper_output = {
                    "status": "expected_tamper_failure",
                    "error_type": err.__class__.__name__,
                    "error_message": str(err),
                    "exit_code": 1,
                    "classification": "chat_view_state_simulation",
                    "rationale": "Deliberately mutated expectation failed assertion as expected.",
                }
                print(json.dumps(tamper_output, indent=2), file=sys.stderr)
                return 1
            # If tamper unexpectedly passed, return error
            print("ERROR: Tampered execution did not fail!", file=sys.stderr)
            return 2

    except Exception as exc:
        print(f"Execution failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
