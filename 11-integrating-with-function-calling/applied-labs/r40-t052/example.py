#!/usr/bin/env python3
"""Minimal local example: a response message state machine with a stable
message ID, modelling pending / streaming / complete / error states.

Teaching fixture only. This file performs no model download, no remote API
call, no GPU and no network access. It is pure stdlib simulation of how a
single Responses API message accumulates streamed text locally, not a claim
about Azure OpenAI's actual streaming wire format or timing.

Public inputs and outputs, connected to lesson concepts
--------------------------------------------------------
- Message identity (lesson: Step 1 "creating messages" / the Responses API's
    per-item identity such as `call_id`)
    Message.message_id -- assigned once at creation, never reassigned.
- Streaming state (lesson: building up a response incrementally before using
    it downstream, e.g. `response.output` / `output_text`)
    Message.state, Message.text, append_chunk
- Completion and recovery (lesson: Assignment hint to "create error handling
    when the function call ... does not return any suitable courses")
    complete_message, fail_message, eligibility of further chunks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    """The four states a message can be in."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


# States in which a message is considered finalized: no further chunks,
# completion or failure may be applied. This is the one boundary decision
# this fixture makes: PENDING and STREAMING both accept more chunks (a
# message is still "open" the moment it exists, even before its first
# chunk); COMPLETE and ERROR are terminal and reject every further mutation.
_TERMINAL_STATES = (State.COMPLETE, State.ERROR)


@dataclass
class Message:
    """A single response message tracked by a stable ``message_id``.

    ``text`` accumulates chunks in the order they are appended. ``error`` is
    set only when the message ends in :class:`State.ERROR`.
    """

    message_id: str
    state: State = State.PENDING
    text: str = field(default="")
    error: str | None = None


def create_message(message_id: str) -> Message:
    """Create a new message in the PENDING state with no accumulated text."""
    if not message_id:
        raise ValueError("message_id must be a non-empty string")
    return Message(message_id=message_id)


def _reject_if_finalized(message: Message, action: str) -> None:
    if message.state in _TERMINAL_STATES:
        raise ValueError(
            f"{action} rejected: message {message.message_id!r} is already "
            f"finalized in state {message.state.value!r}"
        )


def append_chunk(message: Message, chunk: str) -> Message:
    """Append one streamed text chunk, in order, to ``message``.

    Valid from PENDING or STREAMING (both move to STREAMING). Rejected with
    ValueError once the message is COMPLETE or ERROR -- the boundary this
    fixture enforces.
    """
    _reject_if_finalized(message, "chunk")
    message.state = State.STREAMING
    message.text += chunk
    return message


def complete_message(message: Message) -> Message:
    """Finalize ``message`` as COMPLETE. Valid from PENDING or STREAMING only."""
    _reject_if_finalized(message, "completion")
    message.state = State.COMPLETE
    return message


def fail_message(message: Message, reason: str) -> Message:
    """Finalize ``message`` as ERROR, preserving any text already received.

    The already-received text (possibly empty) is kept, and a visible error
    marker is appended so downstream code can see exactly where the stream
    stopped and why.
    """
    _reject_if_finalized(message, "failure")
    message.error = reason
    message.text += f"[ERROR: {reason}]"
    message.state = State.ERROR
    return message


# ---------------------------------------------------------------------------
# Demo entry point (minimal complete example).
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Run the two headline fixtures and print the lesson-linked trace."""
    print("[LESSON: message identity] creating message id=msg-1")
    ok = create_message("msg-1")
    print("  state=%s text=%r" % (ok.state.value, ok.text))

    append_chunk(ok, "Here are some ")
    print("[LESSON: streaming state] chunk 1 appended -> state=%s text=%r" % (ok.state.value, ok.text))
    append_chunk(ok, "Azure courses.")
    print("[LESSON: streaming state] chunk 2 appended -> state=%s text=%r" % (ok.state.value, ok.text))
    complete_message(ok)
    print("[LESSON: completion] state=%s text=%r message_id=%s" % (ok.state.value, ok.text, ok.message_id))

    print("[LESSON: message identity] creating message id=msg-2")
    broken = create_message("msg-2")
    append_chunk(broken, "Here are some ")
    fail_message(broken, "upstream timeout")
    print(
        "[LESSON: recovery] state=%s text=%r error=%r message_id=%s"
        % (broken.state.value, broken.text, broken.error, broken.message_id)
    )

    try:
        append_chunk(broken, "more text")
    except ValueError as exc:
        print("[LESSON: boundary] chunk after finalize rejected: %s" % exc)


if __name__ == "__main__":
    run_demo()
