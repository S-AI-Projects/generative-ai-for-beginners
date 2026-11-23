#!/usr/bin/env python3
"""
Test runner and check verification script for R40-T022.

Executes all normal, boundary, and failure scenarios in fresh processes,
validates assertions, and generates work/R40-T022/results.md.
A check must exit non-zero when an assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(ROOT_DIR, "work", "R40-T022")
EXAMPLE_PATH = os.path.join(ROOT_DIR, "17-ai-agents", "applied-labs", "r40-t022", "example.py")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def main() -> int:
    print(f"=== Running R40-T022 Checks from {ROOT_DIR} ===")
    results_markdown_lines = [
        "# R40-T022 — Test and Check Results",
        "",
        "This document records all inputs, expected vs. actual outputs, exit codes, and verification assertions for Task R40-T022.",
        "",
        "---",
        "",
    ]

    # 1. Scenario 1: Normal Addition
    print("Running Check 1: Normal Addition add(2, 3) -> 5...")
    cmd1 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": 2, "b": 3}}']
    res1 = run_cmd(cmd1)
    assert res1.returncode == 0, f"Expected returncode 0, got {res1.returncode}"
    data1 = json.loads(res1.stdout)
    assert data1["status"] == "success", "Expected status 'success'"
    assert data1["result"] == 5, f"Expected result 5, got {data1['result']}"
    assert data1["tool"] == "add", f"Expected tool 'add', got {data1['tool']}"
    assert data1["arguments"] == {"a": 2, "b": 3}

    results_markdown_lines.extend([
        "## 1. Normal Scenario: Addition (`add(2, 3) -> 5`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "success",
            "tool": "add",
            "arguments": {"a": 2, "b": 3},
            "result": 5
        }, indent=2),
        "```",
        "",
        "Actual output:",
        "```json",
        res1.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res1.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Addition executed successfully with strict numeric typing.",
        "",
        "---",
        "",
    ])

    # 2. Scenario 2: Normal Multiplication
    print("Running Check 2: Normal Multiplication multiply(2, 3) -> 6...")
    cmd2 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}']
    res2 = run_cmd(cmd2)
    assert res2.returncode == 0, f"Expected returncode 0, got {res2.returncode}"
    data2 = json.loads(res2.stdout)
    assert data2["status"] == "success", "Expected status 'success'"
    assert data2["result"] == 6, f"Expected result 6, got {data2['result']}"
    assert data2["tool"] == "multiply", f"Expected tool 'multiply', got {data2['tool']}"
    assert data2["arguments"] == {"a": 2, "b": 3}

    results_markdown_lines.extend([
        "## 2. Normal Scenario: Multiplication (`multiply(2, 3) -> 6`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"multiply\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "success",
            "tool": "multiply",
            "arguments": {"a": 2, "b": 3},
            "result": 6
        }, indent=2),
        "```",
        "",
        "Actual output:",
        "```json",
        res2.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res2.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Multiplication executed successfully with strict numeric typing.",
        "",
        "---",
        "",
    ])

    # 3. Scenario 3: Unknown Tool
    print("Running Check 3: Unknown Tool Structured Error...")
    cmd3 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "divide", "arguments": {"a": 6, "b": 2}}']
    res3 = run_cmd(cmd3)
    assert res3.returncode == 1, f"Expected returncode 1, got {res3.returncode}"
    data3 = json.loads(res3.stdout)
    assert data3["status"] == "error", "Expected status 'error'"
    assert data3["error"]["type"] == "UnknownToolError", f"Expected UnknownToolError, got {data3['error']['type']}"
    assert data3["error"]["code"] == "TOOL_NOT_ALLOWED"
    assert data3["tool"] == "divide"

    results_markdown_lines.extend([
        "## 3. Failure Scenario: Unknown Tool (`divide`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"divide\", \"arguments\": {\"a\": 6, \"b\": 2}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "error",
            "error": {
                "type": "UnknownToolError",
                "code": "TOOL_NOT_ALLOWED",
                "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
                "details": {
                    "tool": "divide",
                    "allowed_tools": ["add", "multiply"]
                }
            },
            "tool": "divide",
            "arguments": {"a": 6, "b": 2}
        }, indent=2),
        "```",
        "",
        "Actual output:",
        "```json",
        res3.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res3.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Unknown tool was rejected via the explicit allowlist with a structured error envelope.",
        "",
        "---",
        "",
    ])

    # 4. Scenario 4: String Argument a
    print("Running Check 4: String Argument a Structured Error...")
    cmd4 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": "2", "b": 3}}']
    res4 = run_cmd(cmd4)
    assert res4.returncode == 1, f"Expected returncode 1, got {res4.returncode}"
    data4 = json.loads(res4.stdout)
    assert data4["status"] == "error", "Expected status 'error'"
    assert data4["error"]["type"] == "ValidationError", f"Expected ValidationError, got {data4['error']['type']}"
    assert data4["error"]["code"] == "INVALID_ARGUMENT_TYPE"
    assert data4["error"]["details"]["parameter"] == "a"
    assert data4["error"]["details"]["received_type"] == "str"

    results_markdown_lines.extend([
        "## 4. Failure Scenario: String Argument `a` (`a = \"2\"`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": \"2\", \"b\": 3}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "error",
            "error": {
                "type": "ValidationError",
                "code": "INVALID_ARGUMENT_TYPE",
                "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
                "details": {
                    "parameter": "a",
                    "expected": "number (int or float)",
                    "received_type": "str",
                    "received_value": "2"
                }
            },
            "tool": "add",
            "arguments": {"a": "2", "b": 3}
        }, indent=2),
        "```",
        "",
        "Actual output:",
        "```json",
        res4.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res4.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Numeric string argument was rejected without implicit coercion.",
        "",
        "---",
        "",
    ])

    # 5. Scenario 5: Pipeline Failure Halting / Isolation
    print("Running Check 5: Pipeline Failure Halting & Isolation...")
    cmd5 = [sys.executable, EXAMPLE_PATH, "--pipeline", '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]']
    res5 = run_cmd(cmd5)
    assert res5.returncode == 1, f"Expected returncode 1, got {res5.returncode}"
    data5 = json.loads(res5.stdout)
    assert data5["status"] == "error"
    assert data5["pipeline_halted"] is True
    assert data5["failed_step_index"] == 0
    assert len(data5["aborted_calls"]) == 1
    assert data5["aborted_calls"][0]["tool"] == "multiply"

    results_markdown_lines.extend([
        "## 5. Failure Scenario: Pipeline Halting & Tool Isolation",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --pipeline '[{\"tool\": \"add\", \"arguments\": {\"a\": \"invalid\", \"b\": 3}}, {\"tool\": \"multiply\", \"arguments\": {\"a\": 2, \"b\": 3}}]'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "error",
            "pipeline_halted": True,
            "failed_step_index": 0,
            "completed_steps": 0,
            "total_steps": 2,
            "executed_results": [],
            "aborted_calls": [
                {"tool": "multiply", "arguments": {"a": 2, "b": 3}}
            ],
            "message": "Pipeline halted: a failed call cannot execute another tool."
        }, indent=2),
        "```",
        "",
        "Actual output:",
        "```json",
        res5.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res5.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Pipeline halted immediately on the first failed call; `multiply` was aborted without execution.",
        "",
        "---",
        "",
    ])

    # 6. Scenario 6: Boundary Smallest Integers (0, 0)
    print("Running Check 6: Boundary Smallest Integers (0, 0)...")
    cmd6 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": 0, "b": 0}}']
    res6 = run_cmd(cmd6)
    assert res6.returncode == 0
    data6 = json.loads(res6.stdout)
    assert data6["result"] == 0

    results_markdown_lines.extend([
        "## 6. Boundary Scenario: Smallest Valid Integers (`add(0, 0) -> 0`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": 0, \"b\": 0}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res6.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res6.returncode}`",
        "",
        "**Result:** PASS — Zero boundary handled cleanly.",
        "",
        "---",
        "",
    ])

    # 7. Scenario 7: Boundary Decision on Booleans
    print("Running Check 7: Boundary Decision on Booleans...")
    cmd7 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": true, "b": 3}}']
    res7 = run_cmd(cmd7)
    assert res7.returncode == 1
    data7 = json.loads(res7.stdout)
    assert data7["error"]["code"] == "INVALID_ARGUMENT_TYPE"
    assert "bool" in data7["error"]["message"]

    results_markdown_lines.extend([
        "## 7. Boundary Decision: Strict Boolean Rejection (`a = true`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": true, \"b\": 3}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res7.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res7.returncode}`",
        "",
        "**Result:** PASS — Boolean primitive rejected despite Python int subclassing.",
        "",
        "---",
        "",
    ])

    # 8. Scenario 8: Unit test discovery
    print("Running Check 8: Automated unittest suite...")
    cmd8 = [sys.executable, "-m", "unittest", "discover", "-s", "17-ai-agents/applied-labs/r40-t022", "-p", "test_*.py", "-v"]
    res8 = run_cmd(cmd8)
    assert res8.returncode == 0, f"Unittest discovery failed:\n{res8.stderr}"
    assert "Ran 29 tests" in res8.stderr or "Ran 29 tests" in res8.stdout

    results_markdown_lines.extend([
        "## 8. Automated Unit Test Discovery",
        "",
        "Command:",
        "```bash",
        "python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t022 -p \"test_*.py\" -v",
        "```",
        "",
        "Test output:",
        "```text",
        res8.stderr.strip() or res8.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res8.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 29 unit and integration tests passed.",
        "",
        "---",
        "",
    ])

    # 9. Scenario 9: Deliberate failure verification
    print("Running Check 9: Deliberate wrong assertion failure check...")
    deliberate_cmd = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys, json; "
            "res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t022/example.py', "
            "'--call', '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'], capture_output=True, text=True); "
            "data = json.loads(res.stdout); "
            "assert data['result'] == 999, 'Deliberate test failure: expected 999 got ' + str(data['result'])"
        ),
    ]
    res9 = run_cmd(deliberate_cmd)
    assert res9.returncode != 0, "Deliberate wrong assertion MUST fail with nonzero exit code!"

    results_markdown_lines.extend([
        "## 9. Deliberate Failure Verification",
        "",
        "Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.",
        "",
        "Command:",
        "```bash",
        "python3 -c \"import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t022/example.py', '--call', '{\\\"tool\\\": \\\"add\\\", \\\"arguments\\\": {\\\"a\\\": 2, \\\"b\\\": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure for assertion verification'\"",
        "```",
        "",
        "Output:",
        "```text",
        res9.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res9.returncode}` (Expected non-zero: `1`)",
        "",
        "**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Check ID | Description | Status | Exit Code |",
        "|---|---|---|---|",
        "| 1 | Normal Addition (`add(2, 3) -> 5`) | PASS | 0 |",
        "| 2 | Normal Multiplication (`multiply(2, 3) -> 6`) | PASS | 0 |",
        "| 3 | Unknown Tool Error (`divide`) | PASS | 1 |",
        "| 4 | String Argument Error (`a = \"2\"`) | PASS | 1 |",
        "| 5 | Pipeline Halting & Tool Isolation | PASS | 1 |",
        "| 6 | Boundary Integers (`0, 0`) | PASS | 0 |",
        "| 7 | Boundary Decision on Booleans | PASS | 1 |",
        "| 8 | Automated Test Suite (29 tests) | PASS | 0 |",
        "| 9 | Deliberate Failure Verification | PASS | 1 (Expected Nonzero) |",
        "",
        "All checks passed successfully.",
    ])

    results_path = os.path.join(WORK_DIR, "results.md")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results_markdown_lines) + "\n")

    print(f"Results successfully written to {results_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
