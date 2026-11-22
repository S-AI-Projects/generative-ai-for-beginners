#!/usr/bin/env python3
"""Chat-View State Lifecycle: Refactored Teaching Example (R40-T006).

Lesson 07: Building Generative AI-Powered Chat Applications
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab models the local chat-view response lifecycle for generative AI chat
applications. It implements a correct baseline state machine, and then refactors it
by extracting one named responsibility (StreamingContentBuffer) to achieve clean
separation of concerns between lifecycle state transitions and chunk concatenation /
error marker formatting.

Contract Rules:
1. Message Identity: A stable message ID (e.g. 'msg-resp-001') is assigned at request
   initialization and remains unchanged across all transitions.
2. State Lifecycle:
   - PENDING: Request initiated, awaiting initial chunk.
   - STREAMING: Sequentially appending arriving chunks in order.
   - COMPLETE: Stream finalized; further appends locked.
   - ERROR: Preserves previously received text and appends an error marker.
3. Sequential Ordering: Two sequential chunks append strictly in arrival order:
   Chunk 1 ('Hello, ') followed by Chunk 2 ('how can I assist you today?').
4. Error Recovery: If stream connection drops after receiving partial content, the
   partial text is preserved and appended with '[ERROR: <reason>]'.
5. Post-Completion Rejection: Any chunk arriving after COMPLETE or ERROR raises
   ChunkRejectedError.

Focus (Baseline vs. Refactored Equivalence):
- Baseline implementation (`BaselineChatResponseManager`) combines state tracking and
  content string manipulation into a single monolithic class.
- Refactored implementation extracts `StreamingContentBuffer` as a dedicated class
  responsible strictly for buffer accumulation, preservation, and error marker formatting.
- The lab proves 100% before/after equivalence on all fixtures and scenarios.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local client-side state machine simulation using Python's
standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.
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
DEFAULT_ERROR_MESSAGE = "Stream connection dropped"
DEFAULT_LATE_CHUNK = " [Late chunk arriving after stream close]"


class ResponseState(str, Enum):
    """Lifecycle states of a chat response message view."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class ChatViewStateError(Exception):
    """Base exception for chat view state violations."""


class ChunkRejectedError(ChatViewStateError):
    """Raised when an incoming chunk is rejected due to terminal response state."""


class IllegalStateTransitionError(ChatViewStateError):
    """Raised when an illegal lifecycle transition is requested."""


class DecisionMismatchError(ChatViewStateError):
    """Raised when an assertion or verification check detects an unexpected outcome."""


# ---------------------------------------------------------------------------
# 1. BASELINE IMPLEMENTATION (Monolithic responsibility)
# ---------------------------------------------------------------------------


class BaselineChatResponseManager:
    """Baseline monolithic manager combining state coordination and content formatting."""

    def __init__(self, message_id: str = DEFAULT_MESSAGE_ID) -> None:
        if not message_id or not message_id.strip():
            raise ValueError("message_id must be non-empty.")
        self.message_id = message_id.strip()
        self.state = ResponseState.PENDING
        self.content = ""
        self.error_message: Optional[str] = None
        self.chunks_received = 0

    def append_chunk(self, chunk: str) -> None:
        if self.state in (ResponseState.COMPLETE, ResponseState.ERROR):
            raise ChunkRejectedError(
                f"Cannot append to response in terminal state '{self.state.value}'."
            )
        if not isinstance(chunk, str):
            raise TypeError("chunk must be a string.")
        self.content += chunk
        self.chunks_received += 1
        self.state = ResponseState.STREAMING

    def complete(self) -> None:
        if self.state == ResponseState.COMPLETE:
            return
        if self.state == ResponseState.ERROR:
            raise IllegalStateTransitionError("Cannot complete from ERROR state.")
        self.state = ResponseState.COMPLETE

    def fail(self, error_message: str = DEFAULT_ERROR_MESSAGE) -> None:
        if self.state == ResponseState.ERROR:
            return
        if self.state == ResponseState.COMPLETE:
            raise IllegalStateTransitionError("Cannot fail from COMPLETE state.")
        self.error_message = error_message
        self.content = f"{self.content}[ERROR: {error_message}]"
        self.state = ResponseState.ERROR

    def snapshot(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "state": self.state.value,
            "content": self.content,
            "chunks_received": self.chunks_received,
            "error_message": self.error_message,
        }


# ---------------------------------------------------------------------------
# 2. REFACTORED IMPLEMENTATION (Extracted StreamingContentBuffer responsibility)
# ---------------------------------------------------------------------------


class StreamingContentBuffer:
    """Extracted Responsibility: Pure buffer management, text preservation, and error formatting."""

    def __init__(self) -> None:
        self.text = ""
        self.chunks_received = 0

    def append(self, chunk: str) -> None:
        if not isinstance(chunk, str):
            raise TypeError("chunk must be a string.")
        self.text += chunk
        self.chunks_received += 1

    def apply_error_marker(self, error_message: str) -> None:
        self.text = f"{self.text}[ERROR: {error_message}]"

    def get_text(self) -> str:
        return self.text

    def count(self) -> int:
        return self.chunks_received


class RefactoredChatResponseManager:
    """Refactored coordinator: Focused strictly on lifecycle transitions and boundary enforcement."""

    def __init__(self, message_id: str = DEFAULT_MESSAGE_ID) -> None:
        if not message_id or not message_id.strip():
            raise ValueError("message_id must be non-empty.")
        self.message_id = message_id.strip()
        self.state = ResponseState.PENDING
        self.buffer = StreamingContentBuffer()
        self.error_message: Optional[str] = None

    def append_chunk(self, chunk: str) -> None:
        if self.state in (ResponseState.COMPLETE, ResponseState.ERROR):
            raise ChunkRejectedError(
                f"Cannot append to response in terminal state '{self.state.value}'."
            )
        self.buffer.append(chunk)
        self.state = ResponseState.STREAMING

    def complete(self) -> None:
        if self.state == ResponseState.COMPLETE:
            return
        if self.state == ResponseState.ERROR:
            raise IllegalStateTransitionError("Cannot complete from ERROR state.")
        self.state = ResponseState.COMPLETE

    def fail(self, error_message: str = DEFAULT_ERROR_MESSAGE) -> None:
        if self.state == ResponseState.ERROR:
            return
        if self.state == ResponseState.COMPLETE:
            raise IllegalStateTransitionError("Cannot fail from COMPLETE state.")
        self.error_message = error_message
        self.buffer.apply_error_marker(error_message)
        self.state = ResponseState.ERROR

    def snapshot(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "state": self.state.value,
            "content": self.buffer.get_text(),
            "chunks_received": self.buffer.count(),
            "error_message": self.error_message,
        }


# ---------------------------------------------------------------------------
# SCENARIOS AND VERIFICATION
# ---------------------------------------------------------------------------


def run_normal_scenario() -> Dict[str, Any]:
    """Normal scenario: PENDING -> chunk 1 -> chunk 2 -> COMPLETE."""
    refactored = RefactoredChatResponseManager()
    for ch in DEFAULT_FIXTURE_CHUNKS:
        refactored.append_chunk(ch)
    refactored.complete()

    snap = refactored.snapshot()
    expected_content = "".join(DEFAULT_FIXTURE_CHUNKS)

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "decision": "STATE_COMPLETE_SUCCESS",
        "state": snap["state"],
        "content": snap["content"],
        "chunks_received": snap["chunks_received"],
        "contract_satisfied": (
            snap["state"] == "complete"
            and snap["content"] == expected_content
            and snap["chunks_received"] == 2
        ),
    }


def run_error_scenario() -> Dict[str, Any]:
    """Error scenario: PENDING -> chunk 1 -> stream drop -> ERROR with preserved text."""
    refactored = RefactoredChatResponseManager()
    refactored.append_chunk(DEFAULT_FIXTURE_CHUNKS[0])
    refactored.fail(DEFAULT_ERROR_MESSAGE)

    snap = refactored.snapshot()
    expected_content = f"{DEFAULT_FIXTURE_CHUNKS[0]}[ERROR: {DEFAULT_ERROR_MESSAGE}]"

    return {
        "scenario_id": "SCENARIO_ERROR",
        "decision": "STATE_ERROR_RECOVERED",
        "state": snap["state"],
        "content": snap["content"],
        "chunks_received": snap["chunks_received"],
        "contract_satisfied": (
            snap["state"] == "error"
            and snap["content"] == expected_content
            and snap["chunks_received"] == 1
        ),
    }


def run_boundary_scenario() -> Dict[str, Any]:
    """Boundary scenario: post-completion chunk rejection."""
    refactored = RefactoredChatResponseManager()
    for ch in DEFAULT_FIXTURE_CHUNKS:
        refactored.append_chunk(ch)
    refactored.complete()

    rejection_verified = False
    rejection_exc = None
    try:
        refactored.append_chunk(DEFAULT_LATE_CHUNK)
    except ChunkRejectedError as exc:
        rejection_verified = True
        rejection_exc = exc.__class__.__name__

    snap = refactored.snapshot()
    return {
        "scenario_id": "SCENARIO_BOUNDARY",
        "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "state": snap["state"],
        "content": snap["content"],
        "rejection_verified": rejection_verified,
        "rejection_exception": rejection_exc,
        "contract_satisfied": rejection_verified,
    }


def verify_before_after_refactor_equivalence() -> Dict[str, Any]:
    """Focus: Proves exact behavioral equivalence between baseline and refactored manager."""
    # Test 1: Normal path equivalence
    base_norm = BaselineChatResponseManager("msg-test")
    ref_norm = RefactoredChatResponseManager("msg-test")
    for ch in DEFAULT_FIXTURE_CHUNKS:
        base_norm.append_chunk(ch)
        ref_norm.append_chunk(ch)
    base_norm.complete()
    ref_norm.complete()
    normal_match = (base_norm.snapshot() == ref_norm.snapshot())

    # Test 2: Error path equivalence
    base_err = BaselineChatResponseManager("msg-test")
    ref_err = RefactoredChatResponseManager("msg-test")
    base_err.append_chunk(DEFAULT_FIXTURE_CHUNKS[0])
    ref_err.append_chunk(DEFAULT_FIXTURE_CHUNKS[0])
    base_err.fail(DEFAULT_ERROR_MESSAGE)
    ref_err.fail(DEFAULT_ERROR_MESSAGE)
    error_match = (base_err.snapshot() == ref_err.snapshot())

    # Test 3: Boundary rejection equivalence
    base_rej_caught = False
    ref_rej_caught = False
    try:
        base_norm.append_chunk("late")
    except ChunkRejectedError:
        base_rej_caught = True
    try:
        ref_norm.append_chunk("late")
    except ChunkRejectedError:
        ref_rej_caught = True
    boundary_match = (base_rej_caught and ref_rej_caught)

    all_matched = (normal_match and error_match and boundary_match)
    return {
        "status": "success",
        "normal_path_equivalent": normal_match,
        "error_path_equivalent": error_match,
        "boundary_path_equivalent": boundary_match,
        "all_equivalent": all_matched,
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical decision table across all scenarios."""
    normal = run_normal_scenario()
    error = run_error_scenario()
    boundary = run_boundary_scenario()
    equiv = verify_before_after_refactor_equivalence()

    scenarios = [normal, error, boundary]
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
        passed = (actual == expected and sc.get("contract_satisfied", False))
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if not equiv["all_equivalent"]:
        failures.append({"scenario_id": "REFACTOR_EQUIVALENCE", "error": "Equivalence check failed"})

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "refactor_equivalence_verified": equiv["all_equivalent"],
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T006: Chat-View State Lifecycle Refactoring Example."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "error", "boundary"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--refactor-check",
        action="store_true",
        help="Verify baseline and refactored equivalence.",
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

    if args.refactor_check:
        print(json.dumps(verify_before_after_refactor_equivalence(), indent=2))
        sys.exit(0)
    elif args.scenario == "normal":
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
