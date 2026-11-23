"""Local simulation of chat response states."""

import sys
from dataclasses import dataclass


@dataclass
class ChatMessage:
    message_id: str
    state: str = "pending"
    text: str = ""
    error: str = ""

    def start(self):
        if self.state != "pending":
            raise ValueError("Only pending messages can start")
        self.state = "streaming"

    def append_chunk(self, chunk):
        if self.state != "streaming":
            raise ValueError("Chunks are accepted only while streaming")
        self.text += chunk

    def complete(self):
        if self.state != "streaming":
            raise ValueError("Only streaming messages can complete")
        self.state = "complete"

    def fail(self, error):
        if self.state != "streaming":
            raise ValueError("Only streaming messages can fail")
        self.error = error
        self.state = "error"


def normal():
    message = ChatMessage("message-001")
    print("Initial:", message.state)
    message.start()
    print("After start:", message.state)
    message.append_chunk("Function call ")
    message.append_chunk("completed successfully.")
    print("Received text:", message.text)
    message.complete()
    print("Final state:", message.state)


def boundary():
    message = ChatMessage("message-002")
    message.start()
    message.append_chunk("Completed response")
    message.complete()
    print("State:", message.state)
    try:
        message.append_chunk("Late chunk")
    except ValueError as exc:
        print("Rejected:", exc)
    print("Preserved text:", message.text)


def failure():
    message = ChatMessage("message-003")
    message.start()
    message.append_chunk("Partial result")
    message.fail("Connection lost")
    print("State:", message.state)
    print("Preserved text:", message.text)
    print("Error marker:", message.error)


if __name__ == "__main__":
    scenarios = {
        "normal": normal,
        "boundary": boundary,
        "failure": failure,
    }
    choice = sys.argv[1] if len(sys.argv) > 1 else "normal"
    if choice not in scenarios:
        raise SystemExit("Use: normal, boundary, or failure")
    scenarios[choice]()
