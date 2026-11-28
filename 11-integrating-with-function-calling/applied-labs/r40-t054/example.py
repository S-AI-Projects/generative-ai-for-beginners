#!/usr/bin/env python3
"""Minimal local example: a response message state machine with a stable
message ID that records its own intermediate state after every step, and an
invariant that rebuilds the final output purely from that recorded history.

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
- Recorded intermediate state + invariant (this task's focus): every step
    (create / append_chunk / complete / fail) appends one immutable
    StateSnapshot to Message.history. reconstruct_text_from_history rebuilds
    the final text from that history alone, independent of the live
    Message object, and must agree with it.
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


# A message is terminal the instant it becomes COMPLETE or ERROR: no further
# chunk, completion or failure may be applied once terminal. PENDING and
# STREAMING are both "open".
_TERMINAL_STATES = (State.COMPLETE, State.ERROR)


@dataclass(frozen=True)
class StateSnapshot:
    """An immutable record of the message's state right after one step.

    ``chunk`` is set only for an ``"append_chunk"`` step; it is the exact
    text that step appended, which is what lets
    :func:`reconstruct_text_from_history` rebuild the final text without
    looking at the live ``Message`` at all.
    """

    step: int
    action: str  # "create" | "append_chunk" | "complete" | "fail"
    state: State
    text: str
    error: str | None = None
    chunk: str | None = None


@dataclass
class Message:
    """A single response message tracked by a stable ``message_id``.

    ``text`` accumulates chunks in the order they are appended. ``history``
    records one :class:`StateSnapshot` per successfully applied step, in
    order; a rejected step (see ``_reject_if_finalized``) never grows
    ``history``.
    """

    message_id: str
    state: State = State.PENDING
    text: str = field(default="")
    error: str | None = None
    history: list[StateSnapshot] = field(default_factory=list)

    def _record(self, action: str, chunk: str | None = None) -> None:
        self.history.append(
            StateSnapshot(
                step=len(self.history),
                action=action,
                state=self.state,
                text=self.text,
                error=self.error,
                chunk=chunk,
            )
        )


def create_message(message_id: str) -> Message:
    """Create a new message in the PENDING state, with step 0 recorded."""
    if not message_id:
        raise ValueError("message_id must be a non-empty string")
    message = Message(message_id=message_id)
    message._record("create")
    return message


def _reject_if_finalized(message: Message, action: str) -> None:
    if message.state in _TERMINAL_STATES:
        raise ValueError(
            f"{action} rejected: message {message.message_id!r} is already "
            f"finalized in state {message.state.value!r}"
        )


def append_chunk(message: Message, chunk: str) -> Message:
    """Append one streamed text chunk, in order, to ``message``.

    Valid from PENDING or STREAMING (both move to STREAMING). Rejected with
    ValueError once the message is COMPLETE or ERROR; a rejected call does
    not record a new history step.
    """
    _reject_if_finalized(message, "chunk")
    message.state = State.STREAMING
    message.text += chunk
    message._record("append_chunk", chunk=chunk)
    return message


def complete_message(message: Message) -> Message:
    """Finalize ``message`` as COMPLETE. Valid from PENDING or STREAMING only."""
    _reject_if_finalized(message, "completion")
    message.state = State.COMPLETE
    message._record("complete")
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
    message._record("fail", chunk=f"[ERROR: {reason}]")
    return message


def reconstruct_text_from_history(history: list[StateSnapshot]) -> str:
    """Rebuild the final text from recorded history alone.

    This never reads a live ``Message``: it only concatenates the
    ``chunk`` value recorded at each ``append_chunk``/``fail`` step, in
    order. The invariant this fixture tests is that this reconstruction
    always equals the live message's final ``text`` -- i.e. the recorded
    intermediate states fully explain the final output, with nothing
    happening "off the record".
    """
    text = ""
    for snapshot in history:
        if snapshot.chunk is not None:
            text += snapshot.chunk
    return text


# ---------------------------------------------------------------------------
# Demo entry point (minimal complete example).
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Run the two headline fixtures and print the lesson-linked trace."""
    print("[LESSON: message identity] creating message id=msg-1")
    ok = create_message("msg-1")
    print("  step=%d action=%s state=%s text=%r" % (ok.history[-1].step, ok.history[-1].action, ok.state.value, ok.text))

    append_chunk(ok, "Here are some ")
    print(
        "[LESSON: streaming state] step=%d chunk appended -> state=%s text=%r"
        % (ok.history[-1].step, ok.state.value, ok.text)
    )
    append_chunk(ok, "Azure courses.")
    print(
        "[LESSON: streaming state] step=%d chunk appended -> state=%s text=%r"
        % (ok.history[-1].step, ok.state.value, ok.text)
    )
    complete_message(ok)
    print(
        "[LESSON: completion] step=%d state=%s text=%r message_id=%s"
        % (ok.history[-1].step, ok.state.value, ok.text, ok.message_id)
    )

    reconstructed = reconstruct_text_from_history(ok.history)
    print(
        "[LESSON: invariant] reconstruct_text_from_history(history)=%r == message.text=%r -> %s"
        % (reconstructed, ok.text, reconstructed == ok.text)
    )

    print("[LESSON: message identity] creating message id=msg-2")
    broken = create_message("msg-2")
    append_chunk(broken, "Here are some ")
    fail_message(broken, "upstream timeout")
    print(
        "[LESSON: recovery] state=%s text=%r error=%r message_id=%s"
        % (broken.state.value, broken.text, broken.error, broken.message_id)
    )
    print(
        "[LESSON: invariant] reconstruct_text_from_history(history)=%r == message.text=%r -> %s"
        % (reconstruct_text_from_history(broken.history), broken.text, reconstruct_text_from_history(broken.history) == broken.text)
    )

    try:
        append_chunk(broken, "more text")
    except ValueError as exc:
        print("[LESSON: boundary] chunk after finalize rejected: %s" % exc)
        print("[LESSON: invariant] history length unchanged by rejected step: %d" % len(broken.history))


if __name__ == "__main__":
    run_demo()
