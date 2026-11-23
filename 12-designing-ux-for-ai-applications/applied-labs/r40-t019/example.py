class ChatMessage:
    def __init__(self, message_id):
        self.message_id = message_id
        self.status = "pending"
        self.text = ""
        self.error = None

    def append_chunk(self, message_id, chunk):
        if message_id != self.message_id:
            raise ValueError("Unknown message ID")

        if self.status not in ("pending", "streaming"):
            raise ValueError("Cannot append a chunk after the response ends")

        self.text += chunk
        self.status = "streaming"

    def complete(self, message_id):
        if message_id != self.message_id:
            raise ValueError("Unknown message ID")

        if self.status not in ("pending", "streaming"):
            raise ValueError("Response cannot be completed in this state")

        self.status = "complete"

    def fail(self, message_id, error):
        if message_id != self.message_id:
            raise ValueError("Unknown message ID")

        if self.status not in ("pending", "streaming"):
            raise ValueError("Response cannot fail in this state")

        self.status = "error"
        self.error = error

    def display(self):
        result = {
            "message_id": self.message_id,
            "status": self.status,
            "text": self.text,
        }

        if self.status == "error":
            result["error_marker"] = self.error

        return result


def run_normal():
    message = ChatMessage("msg-001")
    message.append_chunk("msg-001", "Hello ")
    message.append_chunk("msg-001", "there!")
    message.complete("msg-001")
    print("Normal scenario:", message.display())


def run_boundary():
    message = ChatMessage("msg-002")
    message.append_chunk("msg-002", "A")
    message.complete("msg-002")
    print("Boundary scenario:", message.display())


def run_failure():
    message = ChatMessage("msg-003")
    message.append_chunk("msg-003", "Partial response")
    message.fail("msg-003", "Connection interrupted")
    print("Failure scenario:", message.display())


def run_evaluation():
    configurations = [
        ("small", ["Hi"]),
        ("medium", ["Hello ", "there!"]),
        ("large", ["This ", "is ", "a ", "longer ", "response."]),
    ]

    print("\nControlled configuration comparison:")

    for name, chunks in configurations:
        message = ChatMessage("eval-" + name)

        for chunk in chunks:
            message.append_chunk(message.message_id, chunk)

        message.complete(message.message_id)

        print({
            "configuration": name,
            "append_operations": len(chunks),
            "final_characters": len(message.text),
            "contract_correct": message.status == "complete",
        })


import sys


if __name__ == "__main__":
    scenarios = {
        "normal": run_normal,
        "boundary": run_boundary,
        "failure": run_failure,
        "evaluation": run_evaluation,
    }

    if len(sys.argv) == 2 and sys.argv[1] in scenarios:
        scenarios[sys.argv[1]]()
    elif len(sys.argv) == 1:
        for scenario in scenarios.values():
            scenario()
    else:
        raise SystemExit(
            "Usage: python3 example.py [normal|boundary|failure|evaluation]"
        )

