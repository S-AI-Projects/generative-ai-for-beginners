#!/usr/bin/env python3
"""
Applied Lab: Chat-View State Lifecycle & Scenario Assessment (R40-T030)
Lesson: 12-designing-ux-for-ai-applications

Contract & Focus:
- Models local pending, streaming, complete and error states for one response with a stable message ID.
- Two chunks append in order ("Hello, " then "how can I assist you today?").
- An error preserves received text with an error marker ("[ERROR: <reason>]").
- Chunks arriving after completion are strictly rejected with ChunkRejectedError.
- Focus: Three applied questions about the local example:
  1. Predict an output (forecasting final state and preserved buffer under partial streaming error)
  2. Diagnose a failure (root cause analysis of late chunk arrival on a finalized message)
  3. Choose a boundary policy (selecting and justifying fail-fast terminal rejection vs silent dropping)
  Each question provides a factual answer, rationale, and executable verification check.

Classification & Scope Note:
- Simulation / Test Double: Local deterministic state machine; requires no network access,
  no cloud API keys, no local weights download, and no GPU or physical hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import json
import sys
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Domain Enums & Exceptions
# =============================================================================

class MessageState(str, Enum):
    """Lifecycle states for a single chat response in the chat-view layer."""
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class ChatViewStateError(Exception):
    """Base exception for chat-view state management errors."""
    pass


class InvalidStateTransitionError(ChatViewStateError):
    """Raised when an illegal lifecycle transition is attempted."""
    pass


class ChunkRejectedError(ChatViewStateError):
    """Raised when a chunk is received after reaching a terminal state (complete or error)."""
    pass


# =============================================================================
# Core Domain Model: ChatViewMessage & ChatViewStateManager
# =============================================================================

@dataclass
class ChatViewMessage:
    """State snapshot for a single response message."""
    message_id: str
    state: MessageState
    content: str
    chunks_received: int
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "state": self.state.value,
            "content": self.content,
            "chunks_received": self.chunks_received,
            "error_message": self.error_message,
        }


class ChatViewStateManager:
    """
    Manages the lifecycle of a single streamed chat response view.
    
    Invariants enforced:
    1. Stable Message Identity: message_id is immutable throughout all transitions.
    2. Ordered Token Concatenation: Chunks append in strict arrival sequence.
    3. Error Preservation: Connection/generation errors never wipe previously received text;
       an error marker is appended to preserve partial utility for the user.
    4. Terminal State Protection: Once in COMPLETE or ERROR, further chunk arrivals
       are strictly rejected to prevent buffer corruption or transcript desynchronization.
    """

    def __init__(self, message_id: str) -> None:
        if not message_id or not isinstance(message_id, str):
            raise ValueError("message_id must be a non-empty string.")
        self._message_id: str = message_id
        self._state: MessageState = MessageState.PENDING
        self._content: str = ""
        self._chunks_received: int = 0
        self._error_message: Optional[str] = None
        self._history: List[Tuple[MessageState, str]] = [(self._state, self._content)]

    @property
    def message_id(self) -> str:
        return self._message_id

    @property
    def state(self) -> MessageState:
        return self._state

    @property
    def content(self) -> str:
        return self._content

    @property
    def chunks_received(self) -> int:
        return self._chunks_received

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    def append_chunk(self, chunk: str) -> None:
        """
        Appends an incoming text chunk to the active response buffer.
        
        Transitions PENDING -> STREAMING on first chunk, or remains in STREAMING.
        Raises ChunkRejectedError if called when already in COMPLETE or ERROR.
        """
        if self._state in (MessageState.COMPLETE, MessageState.ERROR):
            raise ChunkRejectedError(
                f"Cannot append chunk '{chunk}' to message '{self._message_id}': "
                f"response is already in terminal state '{self._state.value}'."
            )

        if not isinstance(chunk, str):
            raise TypeError(f"Chunk must be a string, got {type(chunk).__name__}")

        if self._state == MessageState.PENDING:
            self._state = MessageState.STREAMING

        self._content += chunk
        self._chunks_received += 1
        self._history.append((self._state, self._content))

    def complete(self) -> None:
        """
        Finalizes the streaming response into the COMPLETE state.
        Raises InvalidStateTransitionError if called from ERROR or if already COMPLETE.
        """
        if self._state == MessageState.ERROR:
            raise InvalidStateTransitionError(
                f"Cannot complete message '{self._message_id}' that ended in ERROR state."
            )
        if self._state == MessageState.COMPLETE:
            raise InvalidStateTransitionError(
                f"Message '{self._message_id}' is already finalized in COMPLETE state."
            )

        self._state = MessageState.COMPLETE
        self._history.append((self._state, self._content))

    def fail(self, error_reason: str) -> None:
        """
        Marks the response as failed. Preserves already received content and appends
        an in-place error marker: '[ERROR: <error_reason>]'.
        """
        if self._state == MessageState.COMPLETE:
            raise InvalidStateTransitionError(
                f"Cannot fail message '{self._message_id}' that has already reached COMPLETE state."
            )
        if self._state == MessageState.ERROR:
            raise InvalidStateTransitionError(
                f"Message '{self._message_id}' is already in ERROR state."
            )

        if not error_reason or not isinstance(error_reason, str):
            error_reason = "Unspecified stream interruption"

        self._state = MessageState.ERROR
        self._error_message = error_reason
        error_marker = f"[ERROR: {error_reason}]"
        self._content = f"{self._content}{error_marker}"
        self._history.append((self._state, self._content))

    def get_snapshot(self) -> ChatViewMessage:
        """Returns an immutable snapshot of current message state."""
        return ChatViewMessage(
            message_id=self._message_id,
            state=self._state,
            content=self._content,
            chunks_received=self._chunks_received,
            error_message=self._error_message,
        )


# =============================================================================
# Canonical Fixtures
# =============================================================================

CANONICAL_MESSAGE_ID = "msg-resp-001"
CHUNK_1 = "Hello, "
CHUNK_2 = "how can I assist you today?"
ERROR_REASON = "Stream connection dropped"
LATE_CHUNK = " [Late chunk arriving after stream close]"


# =============================================================================
# Canonical Scenario Runners
# =============================================================================

def run_normal_scenario(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executes normal scenario:
    PENDING -> STREAMING (chunk 1) -> STREAMING (chunk 2) -> COMPLETE.
    """
    mgr = ChatViewStateManager(message_id=message_id)
    initial_id = mgr.message_id
    initial_state = mgr.state.value

    # Chunk 1
    mgr.append_chunk(CHUNK_1)
    state_after_c1 = mgr.state.value

    # Chunk 2
    mgr.append_chunk(CHUNK_2)
    state_after_c2 = mgr.state.value

    # Complete
    mgr.complete()
    final_snap = mgr.get_snapshot()

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "decision": "STATE_COMPLETE_SUCCESS",
        "message_id": final_snap.message_id,
        "state": final_snap.state.value,
        "content": final_snap.content,
        "chunks_received": final_snap.chunks_received,
        "error_message": final_snap.error_message,
        "stable_id_preserved": (initial_id == final_snap.message_id),
        "ordered_chunks_verified": (final_snap.content == f"{CHUNK_1}{CHUNK_2}"),
        "state_transitions": [initial_state, state_after_c1, state_after_c2, final_snap.state.value],
        "rationale": (
            f"Response '{final_snap.message_id}' initialized in PENDING state, "
            f"sequentially appended 2 chunks in arrival order, and completed successfully with stable ID."
        ),
        "classification": "chat_view_state_simulation",
    }


def run_error_scenario(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executes error recovery scenario:
    PENDING -> STREAMING (chunk 1) -> ERROR (stream drop preserves chunk 1 + error marker).
    """
    mgr = ChatViewStateManager(message_id=message_id)
    initial_id = mgr.message_id

    # Chunk 1 arrives
    mgr.append_chunk(CHUNK_1)

    # Interruption occurs
    mgr.fail(ERROR_REASON)
    final_snap = mgr.get_snapshot()

    expected_content = f"{CHUNK_1}[ERROR: {ERROR_REASON}]"

    return {
        "scenario_id": "SCENARIO_ERROR",
        "scenario_type": "error_recovery",
        "decision": "STATE_ERROR_RECOVERED",
        "message_id": final_snap.message_id,
        "state": final_snap.state.value,
        "content": final_snap.content,
        "chunks_received": final_snap.chunks_received,
        "error_message": final_snap.error_message,
        "stable_id_preserved": (initial_id == final_snap.message_id),
        "partial_text_preserved": final_snap.content.startswith(CHUNK_1),
        "error_marker_present": f"[ERROR: {ERROR_REASON}]" in final_snap.content,
        "rationale": (
            f"Response '{final_snap.message_id}' received chunk 1 ('{CHUNK_1}') before stream failed. "
            f"The error preserved previously received text intact and appended error marker."
        ),
        "classification": "chat_view_state_simulation",
    }


def run_boundary_scenario(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executes boundary scenario:
    Normal completion followed by an attempted late chunk; verifies ChunkRejectedError.
    """
    mgr = ChatViewStateManager(message_id=message_id)
    mgr.append_chunk(CHUNK_1)
    mgr.append_chunk(CHUNK_2)
    mgr.complete()

    content_before_late = mgr.content
    state_before_late = mgr.state.value

    rejection_caught = False
    rejection_type = ""
    rejection_message = ""

    try:
        mgr.append_chunk(LATE_CHUNK)
    except ChunkRejectedError as exc:
        rejection_caught = True
        rejection_type = type(exc).__name__
        rejection_message = str(exc)

    final_snap = mgr.get_snapshot()
    buffer_unmodified = (final_snap.content == content_before_late)
    state_unmodified = (final_snap.state.value == state_before_late)

    return {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_rejection",
        "decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "message_id": final_snap.message_id,
        "state": final_snap.state.value,
        "content": final_snap.content,
        "chunks_received": final_snap.chunks_received,
        "attempted_late_chunk": LATE_CHUNK,
        "rejection_verified": rejection_caught,
        "rejection_exception": rejection_type,
        "buffer_unmodified": buffer_unmodified,
        "state_unmodified": state_unmodified,
        "rejection_message": rejection_message,
        "rationale": (
            f"Response '{final_snap.message_id}' reached COMPLETE state. Incoming late chunk "
            f"'{LATE_CHUNK}' was rejected with ChunkRejectedError, preserving the finalized response "
            f"buffer without corruption."
        ),
        "classification": "chat_view_state_simulation",
    }


# =============================================================================
# The Three Applied Questions: Formulation, Rationale & Executable Checks
# =============================================================================

@dataclass
class AppliedQuestion:
    """Structure for an applied scenario assessment question."""
    question_id: str
    focus_area: str
    title: str
    prompt: str
    options: Dict[str, str]
    correct_option: str
    factual_answer: Any
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "focus_area": self.focus_area,
            "title": self.title,
            "prompt": self.prompt,
            "options": self.options,
            "correct_option": self.correct_option,
            "factual_answer": self.factual_answer,
            "rationale": self.rationale,
        }


# Definition of Question 1: Predict an Output
QUESTION_1 = AppliedQuestion(
    question_id="Q1_PREDICT_OUTPUT",
    focus_area="predict_an_output",
    title="Predict Output Under Mid-Stream Network Interruption",
    prompt=(
        "A response is initiated with message ID 'msg-resp-001' in PENDING state. "
        "Chunk 1 ('Hello, ') arrives successfully. Before Chunk 2 can be received, "
        "the stream aborts with error 'Stream connection dropped'. "
        "What is the exact final state and content buffer of 'msg-resp-001'?"
    ),
    options={
        "A": "state='error', content='' (Buffer cleared to avoid showing incomplete text)",
        "B": "state='error', content='Hello, [ERROR: Stream connection dropped]' (Text preserved + marker appended)",
        "C": "state='complete', content='Hello, ' (Truncated stream coerced to complete)",
        "D": "state='pending', content='Hello, ' (State remains pending awaiting reconnect)",
    },
    correct_option="B",
    factual_answer={
        "message_id": CANONICAL_MESSAGE_ID,
        "state": MessageState.ERROR.value,
        "content": f"{CHUNK_1}[ERROR: {ERROR_REASON}]",
        "chunks_received": 1,
    },
    rationale=(
        "In AI user experience design (Lesson 12: Reliability & Transparency), partial stream "
        "failures must never discard already-rendered tokens. Preserving previously received "
        "text retains immediate utility for the user, while an explicit in-place error marker "
        "explains the failure without silent data loss or disruptive layout collapse."
    ),
)

# Definition of Question 2: Diagnose a Failure
QUESTION_2 = AppliedQuestion(
    question_id="Q2_DIAGNOSE_FAILURE",
    focus_area="diagnose_a_failure",
    title="Diagnose Late Chunk Arrival on Finalized Message",
    prompt=(
        "A client chat-view component successfully finalizes 'msg-resp-001' after receiving "
        "Chunk 1 ('Hello, ') and Chunk 2 ('how can I assist you today?'), entering COMPLETE state. "
        "A delayed network packet subsequently attempts to deliver "
        "' [Late chunk arriving after stream close]'. The application raises ChunkRejectedError. "
        "What is the root cause of this failure and what UX invariant does it enforce?"
    ),
    options={
        "A": "Root Cause: Network packet payload size exceeded max buffer limit.",
        "B": "Root Cause: Attempted mutation of a sealed message in terminal COMPLETE state; enforces transcript immutability.",
        "C": "Root Cause: HTTP 404 stream endpoint not found on server.",
        "D": "Root Cause: Message ID mismatch between client session and server socket.",
    },
    correct_option="B",
    factual_answer={
        "exception_type": "ChunkRejectedError",
        "root_cause": "Attempted buffer append on message already in terminal COMPLETE state",
        "invariant_enforced": "Terminal state immutability protects finalized conversation history from out-of-order race conditions.",
        "final_buffer_preserved": f"{CHUNK_1}{CHUNK_2}",
    },
    rationale=(
        "In asynchronous streaming architectures, network retries or lagged transport packets "
        "can arrive after a completion event. Permitting post-completion appends causes text "
        "flickering, transcript corruption, and broken user trust. The state machine must enforce "
        "terminal sealing: once COMPLETE or ERROR is reached, the buffer is immutable."
    ),
)

# Definition of Question 3: Choose a Boundary Policy
QUESTION_3 = AppliedQuestion(
    question_id="Q3_CHOOSE_BOUNDARY_POLICY",
    focus_area="choose_boundary_policy",
    title="Choose Boundary Policy for Terminal State Chunk Interceptions",
    prompt=(
        "When designing the client chat-view state manager, how should incoming chunks arriving "
        "after a terminal state (COMPLETE or ERROR) be handled at the system boundary? "
        "Choose the most robust boundary policy."
    ),
    options={
        "A": "POLICY_SILENT_DISCARD: Discard late chunks silently without raising exceptions or logging.",
        "B": "POLICY_UNCONDITIONAL_APPEND: Append all arriving chunks unconditionally whenever they arrive.",
        "C": "POLICY_EXPLICIT_REJECTION: Raise ChunkRejectedError immediately (fail-fast) while preserving finalized buffer.",
        "D": "POLICY_RESET_PENDING: Reset message state back to PENDING and resume streaming from scratch.",
    },
    correct_option="C",
    factual_answer={
        "chosen_policy": "POLICY_EXPLICIT_REJECTION",
        "exception": "ChunkRejectedError",
        "buffer_action": "NO_MUTATION",
        "system_behavior": "Fail-fast notification to monitoring/telemetry while preserving user-visible transcript integrity.",
    },
    rationale=(
        "Silent discard (Policy A) masks transport protocol bugs and duplicate delivery defects "
        "from telemetry. Unconditional append (Policy B) causes race condition corruptions. Resetting "
        "(Policy D) destroys existing conversational context. Explicit rejection (Policy C) enforces "
        "fail-fast boundaries, guarantees buffer immutability, and provides observable diagnostic signals."
    ),
)


# Executable checks for each applied question
def verify_question_1(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executable check for Question 1:
    Predicts and asserts exact output of partial stream failure.
    """
    scenario_res = run_error_scenario(message_id=message_id)
    actual_state = scenario_res["state"]
    actual_content = scenario_res["content"]
    actual_chunks = scenario_res["chunks_received"]

    expected = QUESTION_1.factual_answer
    passed = (
        actual_state == expected["state"]
        and actual_content == expected["content"]
        and actual_chunks == expected["chunks_received"]
        and scenario_res["message_id"] == expected["message_id"]
    )

    return {
        "question_id": QUESTION_1.question_id,
        "focus_area": QUESTION_1.focus_area,
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "selected_option": QUESTION_1.correct_option,
        "predicted_output": expected,
        "actual_output": {
            "message_id": scenario_res["message_id"],
            "state": actual_state,
            "content": actual_content,
            "chunks_received": actual_chunks,
        },
        "rationale": QUESTION_1.rationale,
        "classification": "chat_view_state_simulation",
    }


def verify_question_2(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executable check for Question 2:
    Diagnoses root cause of late chunk failure on completed response.
    """
    scenario_res = run_boundary_scenario(message_id=message_id)
    expected = QUESTION_2.factual_answer

    passed = (
        scenario_res["rejection_verified"] is True
        and scenario_res["rejection_exception"] == expected["exception_type"]
        and scenario_res["content"] == expected["final_buffer_preserved"]
        and scenario_res["buffer_unmodified"] is True
    )

    return {
        "question_id": QUESTION_2.question_id,
        "focus_area": QUESTION_2.focus_area,
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "selected_option": QUESTION_2.correct_option,
        "diagnosis": expected,
        "actual_diagnostic_evidence": {
            "rejection_verified": scenario_res["rejection_verified"],
            "rejection_exception": scenario_res["rejection_exception"],
            "rejection_message": scenario_res["rejection_message"],
            "content_retained": scenario_res["content"],
        },
        "rationale": QUESTION_2.rationale,
        "classification": "chat_view_state_simulation",
    }


def verify_question_3(message_id: str = CANONICAL_MESSAGE_ID) -> Dict[str, Any]:
    """
    Executable check for Question 3:
    Evaluates and verifies chosen boundary policy for terminal state protection.
    """
    mgr = ChatViewStateManager(message_id=message_id)
    mgr.append_chunk(CHUNK_1)
    mgr.fail(ERROR_REASON)
    error_buffer = mgr.content

    # Attempt late chunk after ERROR
    error_rejection_caught = False
    try:
        mgr.append_chunk(LATE_CHUNK)
    except ChunkRejectedError:
        error_rejection_caught = True

    # Attempt late chunk after COMPLETE
    mgr_comp = ChatViewStateManager(message_id=f"{message_id}-comp")
    mgr_comp.append_chunk(CHUNK_1)
    mgr_comp.complete()
    complete_buffer = mgr_comp.content

    complete_rejection_caught = False
    try:
        mgr_comp.append_chunk(LATE_CHUNK)
    except ChunkRejectedError:
        complete_rejection_caught = True

    passed = (
        error_rejection_caught is True
        and complete_rejection_caught is True
        and mgr.content == error_buffer
        and mgr_comp.content == complete_buffer
    )

    return {
        "question_id": QUESTION_3.question_id,
        "focus_area": QUESTION_3.focus_area,
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "selected_option": QUESTION_3.correct_option,
        "chosen_policy": QUESTION_3.factual_answer["chosen_policy"],
        "policy_specification": QUESTION_3.factual_answer,
        "verification_evidence": {
            "error_terminal_rejection": error_rejection_caught,
            "complete_terminal_rejection": complete_rejection_caught,
            "error_buffer_preserved": mgr.content == error_buffer,
            "complete_buffer_preserved": mgr_comp.content == complete_buffer,
        },
        "rationale": QUESTION_3.rationale,
        "classification": "chat_view_state_simulation",
    }


def run_all_questions_assessment() -> Dict[str, Any]:
    """Runs verification across all three applied questions."""
    q1 = verify_question_1()
    q2 = verify_question_2()
    q3 = verify_question_3()

    all_passed = q1["passed"] and q2["passed"] and q3["passed"]

    return {
        "status": "success" if all_passed else "failure",
        "total_questions": 3,
        "passed_questions": sum(1 for q in [q1, q2, q3] if q["passed"]),
        "failed_questions": sum(1 for q in [q1, q2, q3] if not q["passed"]),
        "all_passed": all_passed,
        "questions": [
            {
                "question": QUESTION_1.to_dict(),
                "assessment": q1,
            },
            {
                "question": QUESTION_2.to_dict(),
                "assessment": q2,
            },
            {
                "question": QUESTION_3.to_dict(),
                "assessment": q3,
            },
        ],
        "classification": "chat_view_state_simulation",
    }


# =============================================================================
# Canonical Decision Table Check
# =============================================================================

CANONICAL_DECISION_TABLE = [
    {
        "scenario_id": "SCENARIO_NORMAL",
        "scenario_type": "normal",
        "expected_decision": "STATE_COMPLETE_SUCCESS",
        "expected_state": "complete",
        "expected_content": f"{CHUNK_1}{CHUNK_2}",
        "expected_chunks": 2,
    },
    {
        "scenario_id": "SCENARIO_ERROR",
        "scenario_type": "error_recovery",
        "expected_decision": "STATE_ERROR_RECOVERED",
        "expected_state": "error",
        "expected_content": f"{CHUNK_1}[ERROR: {ERROR_REASON}]",
        "expected_chunks": 1,
    },
    {
        "scenario_id": "SCENARIO_BOUNDARY",
        "scenario_type": "boundary_rejection",
        "expected_decision": "CHUNK_AFTER_COMPLETION_REJECTED",
        "expected_state": "complete",
        "expected_content": f"{CHUNK_1}{CHUNK_2}",
        "expected_chunks": 2,
    },
]


def run_decision_table_check(tamper: bool = False) -> Dict[str, Any]:
    """
    Validates implementation against canonical decision table.
    If tamper=True, deliberately introduces a specification mismatch to trigger failure.
    """
    normal = run_normal_scenario()
    error = run_error_scenario()
    boundary = run_boundary_scenario()

    results_map = {
        "SCENARIO_NORMAL": normal,
        "SCENARIO_ERROR": error,
        "SCENARIO_BOUNDARY": boundary,
    }

    scenarios_evaluated = []
    failed_count = 0

    for item in CANONICAL_DECISION_TABLE:
        sc_id = item["scenario_id"]
        actual = results_map[sc_id]

        expected_decision = item["expected_decision"]
        if tamper and sc_id == "SCENARIO_NORMAL":
            # Deliberate tamper mutation
            expected_decision = "TAMPERED_WRONG_DECISION"

        decision_matches = (actual["decision"] == expected_decision)
        state_matches = (actual["state"] == item["expected_state"])
        content_matches = (actual["content"] == item["expected_content"])
        chunks_matches = (actual["chunks_received"] == item["expected_chunks"])

        scenario_passed = decision_matches and state_matches and content_matches and chunks_matches
        if not scenario_passed:
            failed_count += 1

        scenarios_evaluated.append({
            "scenario_id": sc_id,
            "scenario_type": item["scenario_type"],
            "expected_decision": expected_decision,
            "actual_decision": actual["decision"],
            "expected_state": item["expected_state"],
            "actual_state": actual["state"],
            "matches_table": scenario_passed,
            "status": "PASS" if scenario_passed else "FAIL",
            "message_id": actual["message_id"],
            "content": actual["content"],
            "rationale": actual["rationale"],
        })

    all_passed = (failed_count == 0)

    return {
        "status": "success" if all_passed else "failure",
        "total_scenarios": len(CANONICAL_DECISION_TABLE),
        "passed_scenarios": len(CANONICAL_DECISION_TABLE) - failed_count,
        "failed_scenarios": failed_count,
        "all_passed": all_passed,
        "classification": "chat_view_state_simulation",
        "scenarios": scenarios_evaluated,
    }


# =============================================================================
# CLI Interface
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Applied Lab: Chat-View State Lifecycle & Scenario Assessment (R40-T030)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scenario",
        choices=["normal", "error", "boundary", "questions"],
        help="Run a specific canonical scenario or questions assessment.",
    )
    group.add_argument(
        "--questions",
        action="store_true",
        help="Evaluate all three applied questions (predict output, diagnose failure, choose boundary policy).",
    )
    group.add_argument(
        "--question",
        type=int,
        choices=[1, 2, 3],
        help="Evaluate a single applied question by number (1, 2, or 3).",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Run the canonical decision table check across all lifecycle scenarios.",
    )
    group.add_argument(
        "--tamper",
        action="store_true",
        help="Inject a deliberate expectation violation to demonstrate non-zero exit on failure.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.scenario == "normal":
        result = run_normal_scenario()
        print(json.dumps(result, indent=2))
        return 0

    if args.scenario == "error":
        result = run_error_scenario()
        print(json.dumps(result, indent=2))
        return 0

    if args.scenario == "boundary":
        result = run_boundary_scenario()
        print(json.dumps(result, indent=2))
        return 0

    if args.scenario == "questions" or args.questions:
        result = run_all_questions_assessment()
        print(json.dumps(result, indent=2))
        return 0 if result["all_passed"] else 1

    if args.question == 1:
        res1 = verify_question_1()
        output = {
            "question": QUESTION_1.to_dict(),
            "assessment": res1,
        }
        print(json.dumps(output, indent=2))
        return 0 if res1["passed"] else 1

    if args.question == 2:
        res2 = verify_question_2()
        output = {
            "question": QUESTION_2.to_dict(),
            "assessment": res2,
        }
        print(json.dumps(output, indent=2))
        return 0 if res2["passed"] else 1

    if args.question == 3:
        res3 = verify_question_3()
        output = {
            "question": QUESTION_3.to_dict(),
            "assessment": res3,
        }
        print(json.dumps(output, indent=2))
        return 0 if res3["passed"] else 1

    if args.check:
        result = run_decision_table_check(tamper=False)
        print(json.dumps(result, indent=2))
        return 0 if result["all_passed"] else 1

    if args.tamper:
        result = run_decision_table_check(tamper=True)
        err_output = {
            "status": "expected_tamper_failure",
            "error_type": "DecisionMismatchError",
            "error_message": f"Verification failed: {result['failed_scenarios']} scenario(s) did not match canonical decision table.",
            "exit_code": 1,
            "classification": "chat_view_state_simulation",
            "rationale": "Deliberately mutated expectation failed assertion as expected.",
            "details": result,
        }
        print(json.dumps(err_output, indent=2), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
