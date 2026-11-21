"""
R40-T045 · Applied Lab: Building Generative AI-Powered Chat Applications
=========================================================================

This module illustrates Lesson 07 ("Building Generative AI-Powered Chat
Applications") through a **streaming-response state machine** for a single
chat message.

Lesson connection
-----------------
Lesson 07 explains that AI-powered chat applications must:
  1. Assign each response a **stable message ID** so the UI can track it.
  2. Stream tokens progressively (PENDING → streaming chunks → COMPLETE).
  3. Handle **errors** gracefully — preserving already-received text and
     marking the message with an error state rather than discarding it.
  4. Maintain **context** across turns (reliability & safety metric from the
     lesson's key-metrics table).

Here we capture those requirements in a ``StreamingChatClient`` Protocol and
a ``ChatMessage`` state machine, then supply a ``MockStreamingAdapter`` that
returns deterministic fixture chunks without any network or model access.

Simplification boundary
-----------------------
The mock returns hard-coded chunk sequences.  A real service would:
  • Stream tokens over a live HTTP/SSE connection (network errors, back-pressure).
  • Produce *nondeterministic* text — different tokens every call.
  • Enforce token budgets and may truncate mid-sentence.
  • Apply safety filters and may refuse a prompt mid-stream.
  • Use a real message-ID scheme (e.g., UUID assigned by the server).
  Therefore: tests that pass here prove *state-machine logic* only.
  They do NOT prove a live streaming integration is correct.

Invalid / missing-data case
---------------------------
``ChatMessage.apply_chunk()`` raises ``ValueError`` with an explanation when:
  • A chunk arrives after the message is already COMPLETE.
  • A chunk arrives after the message is in ERROR state.
The caller can recover by starting a **new** ``ChatMessage`` for the next turn,
which is demonstrated in ``TestErrorRecovery``.

Three scenarios
---------------
1. **Normal**: two chunks arrive in order → text appended → COMPLETE.
2. **Boundary**: single empty-string chunk (minimum valid chunk) → COMPLETE.
3. **Error**: an error event mid-stream → text preserved, state = ERROR.
   Post-completion / post-error chunk injection → ValueError raised.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterator, Protocol


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class MessageState(Enum):
    PENDING = auto()
    STREAMING = auto()
    COMPLETE = auto()
    ERROR = auto()


@dataclass
class ChatMessage:
    """
    A single chat response with a stable ID and streaming state.

    State transitions
    ~~~~~~~~~~~~~~~~~
    PENDING  --chunk-->  STREAMING  --chunk-->  STREAMING  --complete-->  COMPLETE
    PENDING  --error-->  ERROR
    STREAMING --error-->  ERROR          (text so far is preserved)
    COMPLETE  --chunk-->  ValueError     (chunk after completion rejected)
    ERROR     --chunk-->  ValueError     (chunk after error rejected)
    """

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: MessageState = field(default=MessageState.PENDING)
    text: str = field(default="")
    error_detail: str = field(default="")

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def apply_chunk(self, chunk: str) -> None:
        """
        Append *chunk* to the message text and advance state to STREAMING.

        Raises
        ------
        ValueError
            If the message is already COMPLETE or ERROR — chunks after
            terminal states are rejected.  The caller should start a new
            ``ChatMessage`` for the next turn.

        Error explanation
        ~~~~~~~~~~~~~~~~~
        A real streaming endpoint may send a spurious delta after the
        [DONE] sentinel due to race conditions or buffered data.  Rejecting
        post-terminal chunks here prevents silent text corruption and forces
        the UI to discard or log the stray event.
        """
        if self.state is MessageState.COMPLETE:
            raise ValueError(
                f"[R40-T045] Chunk rejected: message {self.message_id!r} is "
                f"already COMPLETE. Start a new ChatMessage for the next turn."
            )
        if self.state is MessageState.ERROR:
            raise ValueError(
                f"[R40-T045] Chunk rejected: message {self.message_id!r} is "
                f"in ERROR state (detail: {self.error_detail!r}). "
                f"Start a new ChatMessage to recover."
            )
        self.text += chunk
        self.state = MessageState.STREAMING

    def mark_complete(self) -> None:
        """Transition STREAMING → COMPLETE (or PENDING → COMPLETE for empty responses)."""
        if self.state not in (MessageState.STREAMING, MessageState.PENDING):
            raise ValueError(
                f"[R40-T045] Cannot complete message in state {self.state.name}."
            )
        self.state = MessageState.COMPLETE

    def mark_error(self, detail: str) -> None:
        """
        Transition any non-terminal state → ERROR, preserving received text.

        The error_detail field records a human-readable explanation so the
        UI can display it alongside the partial response (Lesson 07:
        reliability & safety, transparency).
        """
        if self.state in (MessageState.COMPLETE, MessageState.ERROR):
            raise ValueError(
                f"[R40-T045] Cannot mark error on a terminal message "
                f"(current state: {self.state.name})."
            )
        self.error_detail = detail
        self.state = MessageState.ERROR


# ---------------------------------------------------------------------------
# Callable interface (external-dependency contract)
# ---------------------------------------------------------------------------

class StreamingChatClient(Protocol):
    """
    Callable interface that wraps the external streaming chat dependency.

    ``stream_response`` yields events as (event_type, payload) tuples:
      - ``("chunk", str)``   — a text delta to append.
      - ``("complete", "")`` — signals successful end of stream.
      - ``("error", str)``   — signals a mid-stream error with detail.

    Any object satisfying this Protocol can be used by ``run_streaming_turn``.
    In production this is backed by an Azure OpenAI streaming call; in tests
    it is backed by ``MockStreamingAdapter``.
    """

    def stream_response(self, user_message: str) -> Iterator[tuple[str, str]]:
        """Yield (event_type, payload) events for *user_message*."""
        ...


# ---------------------------------------------------------------------------
# Deterministic local adapter (mock)
# ---------------------------------------------------------------------------

# Fixture event sequences keyed by scenario tag in the user message.
_FIXTURE_STREAMS: dict[str, list[tuple[str, str]]] = {
    "__normal__": [
        ("chunk", "Hello, "),
        ("chunk", "world!"),
        ("complete", ""),
    ],
    "__boundary__": [
        ("chunk", ""),          # minimum valid chunk: empty string
        ("complete", ""),
    ],
    "__error__": [
        ("chunk", "Partial "),
        ("error", "Simulated network timeout after first chunk."),
    ],
    "__post_complete__": [
        ("chunk", "Done."),
        ("complete", ""),
        ("chunk", "STRAY"),     # stray chunk — must be rejected
    ],
    "__post_error__": [
        ("chunk", "Oops "),
        ("error", "Simulated upstream error."),
        ("chunk", "STRAY"),     # chunk after error — must be rejected
    ],
}


class MockStreamingAdapter:
    """
    **Deterministic local adapter** — no network, no GPU, no paid provider.

    Inspects *user_message* for a scenario tag and yields the matching
    fixture event sequence.

    **[SIMULATION / MOCK]** — Real-service behaviour this mock does NOT establish:
    - Non-determinism: real model yields different tokens each call.
    - Network back-pressure / HTTP 429 rate-limits.
    - Token-budget truncation (completion cut off mid-sentence).
    - Safety-filter refusals mid-stream.
    - Server-assigned message IDs (mock uses uuid4 generated locally).
    - True concurrent streaming (mock is synchronous).
    """

    def stream_response(self, user_message: str) -> Iterator[tuple[str, str]]:  # noqa: D102
        for tag, events in _FIXTURE_STREAMS.items():
            if tag in user_message:
                yield from events
                return
        # Unknown tag → empty complete (safe fallback)
        yield ("complete", "")


# ---------------------------------------------------------------------------
# Application logic
# ---------------------------------------------------------------------------

def run_streaming_turn(
    user_message: str,
    client: StreamingChatClient,
) -> ChatMessage:
    """
    Execute one chat turn, consuming the event stream into a ``ChatMessage``.

    Parameters
    ----------
    user_message:
        The user's input text (may contain a scenario tag for the mock).
    client:
        Any object satisfying ``StreamingChatClient``.

    Returns
    -------
    A ``ChatMessage`` in state COMPLETE or ERROR.

    Notes
    -----
    Post-terminal chunks (stray events after COMPLETE or ERROR) are caught
    here, logged to ``error_detail``, and do not corrupt the message text.
    The function still returns the message so the caller can inspect it.
    """
    msg = ChatMessage()
    for event_type, payload in client.stream_response(user_message):
        if event_type == "chunk":
            try:
                msg.apply_chunk(payload)
            except ValueError as exc:
                # Stray chunk after terminal state — record and stop.
                msg.error_detail = str(exc)
                break
        elif event_type == "complete":
            msg.mark_complete()
            break
        elif event_type == "error":
            msg.mark_error(payload)
            break
    # Safety net: if stream ended without a terminal event
    if msg.state is MessageState.STREAMING:
        msg.mark_complete()
    return msg
