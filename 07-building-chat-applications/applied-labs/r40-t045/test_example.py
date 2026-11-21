"""
R40-T045 · Test suite for example.py
======================================

Covers:
  1. Normal scenario      — two chunks append in order → COMPLETE
  2. Boundary scenario    — single empty-string chunk  → COMPLETE
  3. Error scenario       — mid-stream error → text preserved, state = ERROR
  4. Post-completion chunk rejection → ValueError
  5. Post-error chunk rejection      → ValueError
  6. Error recovery       — new ChatMessage after error succeeds normally
  7. Stable message ID    — ID is set at creation and never changes
  8. Deliberate-wrong-result checks — checker exits non-zero on wrong assertion
  9. Mock-is-simulation   — determinism and no-raise guarantees

Run with:
    python3 -m unittest discover -s 07-building-chat-applications/applied-labs/r40-t045 -p "test_*.py"
or:
    python3 -m unittest 07-building-chat-applications/applied-labs/r40-t045/test_example -v
"""

import unittest

from example import (
    ChatMessage,
    MessageState,
    MockStreamingAdapter,
    run_streaming_turn,
)


# ---------------------------------------------------------------------------
# Scenario 1 — Normal
# ---------------------------------------------------------------------------

class TestNormalScenario(unittest.TestCase):
    """
    Two chunks arrive in order; both are appended; message reaches COMPLETE.

    Input facts : user_message contains __normal__ tag
    Fixture     : ("chunk","Hello, "), ("chunk","world!"), ("complete","")
    Expected    : state=COMPLETE, text="Hello, world!"

    Lesson connection (Lesson 07)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Streaming tokens progressively arrive from the generative AI model; the
    application appends each token to the displayed response. This mirrors
    the OpenAI streaming API pattern described in the lesson.

    [SIMULATION / MOCK] The mock returns fixed fixture chunks; a real model
    would produce nondeterministic tokens over a live HTTP/SSE connection.
    """

    def setUp(self):
        self.client = MockStreamingAdapter()

    def test_state_is_complete(self):
        msg = run_streaming_turn("hello __normal__", self.client)
        self.assertEqual(msg.state, MessageState.COMPLETE)

    def test_chunks_appended_in_order(self):
        msg = run_streaming_turn("hello __normal__", self.client)
        self.assertEqual(msg.text, "Hello, world!")

    def test_message_id_is_stable(self):
        """ID assigned at creation must not change after streaming."""
        msg = ChatMessage()
        original_id = msg.message_id
        msg.apply_chunk("a")
        msg.apply_chunk("b")
        msg.mark_complete()
        self.assertEqual(msg.message_id, original_id)

    def test_deliberate_wrong_state_fails(self):
        """Checker MUST fail when the expected state is wrong."""
        msg = run_streaming_turn("hello __normal__", self.client)
        with self.assertRaises(AssertionError):
            self.assertEqual(msg.state, MessageState.ERROR,
                             "Intentionally wrong expected value.")

    def test_deliberate_wrong_text_fails(self):
        """Checker MUST fail when the expected text is wrong."""
        msg = run_streaming_turn("hello __normal__", self.client)
        with self.assertRaises(AssertionError):
            self.assertEqual(msg.text, "WRONG TEXT",
                             "Intentionally wrong expected value.")


# ---------------------------------------------------------------------------
# Scenario 2 — Boundary
# ---------------------------------------------------------------------------

class TestBoundaryScenario(unittest.TestCase):
    """
    Single empty-string chunk (minimum valid chunk) followed by complete.

    Input facts : user_message contains __boundary__ tag
    Fixture     : ("chunk",""), ("complete","")
    Expected    : state=COMPLETE, text=""

    Lesson connection
    ~~~~~~~~~~~~~~~~~
    A real model might produce a delta with zero visible characters (e.g.,
    a newline or a whitespace token). The state machine must handle this
    without treating it as an error — the app should still reach COMPLETE.

    [SIMULATION / MOCK] Empty-chunk behaviour is a boundary condition that
    a real streaming endpoint may exhibit; the mock reproduces it deterministically.
    """

    def setUp(self):
        self.client = MockStreamingAdapter()

    def test_state_is_complete(self):
        msg = run_streaming_turn("test __boundary__", self.client)
        self.assertEqual(msg.state, MessageState.COMPLETE)

    def test_text_is_empty_string(self):
        msg = run_streaming_turn("test __boundary__", self.client)
        self.assertEqual(msg.text, "")

    def test_deliberate_wrong_state_fails(self):
        msg = run_streaming_turn("test __boundary__", self.client)
        with self.assertRaises(AssertionError):
            self.assertEqual(msg.state, MessageState.PENDING,
                             "Intentionally wrong expected value.")


# ---------------------------------------------------------------------------
# Scenario 3 — Error (mid-stream)
# ---------------------------------------------------------------------------

class TestErrorScenario(unittest.TestCase):
    """
    A chunk arrives, then an error event: text is preserved, state = ERROR.

    Input facts : user_message contains __error__ tag
    Fixture     : ("chunk","Partial "), ("error","Simulated network timeout…")
    Expected    : state=ERROR, text="Partial " (text NOT discarded)

    Lesson connection
    ~~~~~~~~~~~~~~~~~
    Lesson 07 lists Reliability & Safety and Transparency as key responsible-AI
    principles. Preserving received text and surfacing an error marker satisfies
    both: the user sees what arrived and knows something went wrong.

    [SIMULATION / MOCK] A real network timeout or safety-filter refusal would
    arrive as an openai.APIError or a finish_reason="content_filter" event;
    the mock simulates this with a plain ("error", detail) tuple.
    """

    def setUp(self):
        self.client = MockStreamingAdapter()

    def test_state_is_error(self):
        msg = run_streaming_turn("ask __error__", self.client)
        self.assertEqual(msg.state, MessageState.ERROR)

    def test_received_text_is_preserved(self):
        """Text received before the error must NOT be discarded."""
        msg = run_streaming_turn("ask __error__", self.client)
        self.assertEqual(msg.text, "Partial ")

    def test_error_detail_is_set(self):
        msg = run_streaming_turn("ask __error__", self.client)
        self.assertIn("timeout", msg.error_detail.lower())

    def test_deliberate_wrong_state_fails(self):
        msg = run_streaming_turn("ask __error__", self.client)
        with self.assertRaises(AssertionError):
            self.assertEqual(msg.state, MessageState.COMPLETE,
                             "Intentionally wrong expected value.")

    def test_deliberate_wrong_text_fails(self):
        msg = run_streaming_turn("ask __error__", self.client)
        with self.assertRaises(AssertionError):
            self.assertEqual(msg.text, "",
                             "Intentionally wrong: text should be preserved.")


# ---------------------------------------------------------------------------
# Post-terminal rejection
# ---------------------------------------------------------------------------

class TestPostCompletionChunkRejected(unittest.TestCase):
    """
    A stray chunk arriving after COMPLETE is rejected (raises ValueError).

    Input facts : user_message contains __post_complete__ tag
    Fixture     : ("chunk","Done."), ("complete",""), ("chunk","STRAY")
    Expected    : ValueError raised; final message.text does NOT contain "STRAY"

    Lesson connection
    ~~~~~~~~~~~~~~~~~
    A streaming endpoint may send buffered data after the [DONE] sentinel due
    to race conditions. Rejecting post-terminal chunks prevents silent text
    corruption — a Reliability & Safety concern from Lesson 07.

    [SIMULATION / MOCK] The mock injects a stray chunk after complete; a real
    service may do this due to network buffering.
    """

    def test_stray_chunk_does_not_corrupt_text(self):
        """run_streaming_turn catches ValueError; STRAY must not appear in text."""
        client = MockStreamingAdapter()
        msg = run_streaming_turn("send __post_complete__", client)
        self.assertNotIn("STRAY", msg.text)

    def test_apply_chunk_on_complete_raises(self):
        """Direct API: apply_chunk on COMPLETE message raises ValueError."""
        msg = ChatMessage()
        msg.apply_chunk("hello")
        msg.mark_complete()
        with self.assertRaises(ValueError):
            msg.apply_chunk("stray")

    def test_deliberate_wrong_raises_fails(self):
        """Checker MUST fail when we incorrectly expect NO ValueError."""
        msg = ChatMessage()
        msg.apply_chunk("hello")
        msg.mark_complete()
        with self.assertRaises(AssertionError):
            # Incorrectly asserting no exception is raised
            try:
                msg.apply_chunk("stray")
            except ValueError:
                raise AssertionError("ValueError WAS raised (as expected), "
                                     "but we're asserting the opposite to prove failure.")


class TestPostErrorChunkRejected(unittest.TestCase):
    """
    A stray chunk arriving after ERROR is rejected (raises ValueError).

    Input facts : user_message contains __post_error__ tag
    Fixture     : ("chunk","Oops "), ("error","…"), ("chunk","STRAY")
    Expected    : ValueError raised; final message.text does NOT contain "STRAY"

    [SIMULATION / MOCK] Same rationale as post-completion rejection.
    """

    def test_stray_chunk_does_not_corrupt_error_message(self):
        client = MockStreamingAdapter()
        msg = run_streaming_turn("send __post_error__", client)
        self.assertNotIn("STRAY", msg.text)

    def test_apply_chunk_on_error_raises(self):
        msg = ChatMessage()
        msg.apply_chunk("oops ")
        msg.mark_error("upstream failure")
        with self.assertRaises(ValueError):
            msg.apply_chunk("stray")


# ---------------------------------------------------------------------------
# Error recovery
# ---------------------------------------------------------------------------

class TestErrorRecovery(unittest.TestCase):
    """
    After an error, starting a new ChatMessage for the next turn succeeds.

    Invalid/missing-data case demonstrated
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Turn 1 fails mid-stream with an error.
    2. Caller creates a new ChatMessage (new stable ID).
    3. Turn 2 completes normally.

    This documents the recovery pattern: the caller must NOT reuse the
    errored message object; it must create a fresh one.

    [SIMULATION / MOCK] In a real app the caller would also re-construct the
    conversation context (system message + history) before the retry.
    """

    def test_recovery_on_next_valid_input(self):
        client = MockStreamingAdapter()

        # Turn 1: error
        msg1 = run_streaming_turn("first __error__", client)
        self.assertEqual(msg1.state, MessageState.ERROR)

        # Turn 2: normal — new ChatMessage, completely independent
        msg2 = run_streaming_turn("second __normal__", client)
        self.assertEqual(msg2.state, MessageState.COMPLETE)
        self.assertEqual(msg2.text, "Hello, world!")

    def test_error_and_recovery_have_different_message_ids(self):
        client = MockStreamingAdapter()
        msg1 = run_streaming_turn("t1 __error__", client)
        msg2 = run_streaming_turn("t2 __normal__", client)
        self.assertNotEqual(msg1.message_id, msg2.message_id)


# ---------------------------------------------------------------------------
# Mock-is-simulation documentation
# ---------------------------------------------------------------------------

class TestMockIsNotRealService(unittest.TestCase):
    """
    Explicitly documents that MockStreamingAdapter is a simulation.

    [SIMULATION / MOCK] — Real-service behaviours NOT established by the mock:
      - Non-determinism (same tag → same events every call).
      - Network back-pressure / HTTP 429 rate-limits.
      - Token-budget truncation.
      - Safety-filter refusals.
      - Server-assigned message IDs.
      - True concurrent streaming.
    """

    def test_mock_is_deterministic(self):
        client = MockStreamingAdapter()
        events1 = list(client.stream_response("x __normal__"))
        events2 = list(client.stream_response("x __normal__"))
        self.assertEqual(events1, events2)

    def test_mock_does_not_raise_on_unknown_tag(self):
        client = MockStreamingAdapter()
        try:
            list(client.stream_response("completely unknown message"))
        except Exception as exc:  # noqa: BLE001
            self.fail(f"Mock raised unexpectedly: {exc}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
