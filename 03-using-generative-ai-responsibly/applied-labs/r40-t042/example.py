
ALLOWED_TOOLS = {"read": ["path"]}

FIXTURES = {"notes.txt": "This is a sample local file."}

EXECUTOR_CALLS = []


def validate_action(action):
    if not isinstance(action, dict):
        return False, "Invalid action format"

    tool = action.get("tool")

    if tool not in ALLOWED_TOOLS:
        return False, "Tool not allowed"

    arguments = action.get("arguments")

    if not isinstance(arguments, dict):
        return False, "Invalid arguments format"

    required_arguments = ALLOWED_TOOLS[tool]

    for argument in required_arguments:
        if argument not in arguments:
            return False, f"Missing required argument: {argument}"

    path = arguments["path"]

    if not isinstance(path, str) or path not in FIXTURES:
        return False, "Invalid path"

    return True, "Action allowed"


def execute_action(action):
    EXECUTOR_CALLS.append(action)

    path = action["arguments"]["path"]

    return FIXTURES[path]


def process_action(action):
    allowed, message = validate_action(action)

    if not allowed:
        return message

    return execute_action(action)


if __name__ == "__main__":

    actions = [
        {
            "tool": "read",
            "arguments": {"path": "notes.txt"}
        },
        {
            "tool": "delete",
            "arguments": {"path": "notes.txt"}
        },
        {
            "tool": "read",
            "arguments": {}
        }
    ]

    for action in actions:
        result = process_action(action)
        print(result)

    print("Executor calls:", len(EXECUTOR_CALLS))


