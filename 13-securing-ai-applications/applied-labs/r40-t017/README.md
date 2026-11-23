# R40-T017: Allowlisted Action Policy

## Goal

Demonstrate how an application can validate proposed tool actions before allowing them to reach an executor.

This is a local Python simulation. It does not access real files, call an AI model, or execute external tools.

## Prerequisites

- Python 3
- A local checkout of this repository
- No external packages required

## Policy

The example allows one tool:

| Tool | Required argument | Type |
|---|---|---|
| read | path | string |

Unknown tools, missing arguments, unexpected arguments, non-string paths, and empty paths are rejected.

## Run the examples

From the repository root:

```bash
python3 13-securing-ai-applications/applied-labs/r40-t017/example.py normal
python3 13-securing-ai-applications/applied-labs/r40-t017/example.py boundary
python3 13-securing-ai-applications/applied-labs/r40-t017/example.py failure
```

## Worked examples

### Allowed action

Input: `{"tool": "read", "arguments": {"path": "notes.txt"}}`

Output: `ALLOWED: MOCK READ: notes.txt`

### Unknown tool

Input: `{"tool": "delete", "arguments": {"path": "notes.txt"}}`

Output: `REJECTED: Tool is not allowed`

### Missing argument

Input: `{"tool": "read", "arguments": {}}`

Output: `REJECTED: Missing required argument: path`

## Run the regression tests

`python3 -m unittest discover -s 13-securing-ai-applications/applied-labs/r40-t017 -p "test_*.py"`

## Scope and limitations

This is a local teaching simulation using a mock executor. It does not access real files, call an AI model, or connect to external services.
