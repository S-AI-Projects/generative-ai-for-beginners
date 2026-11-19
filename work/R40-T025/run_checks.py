#!/usr/bin/env python3
"""
Test runner and check verification script for R40-T025.

Executes all normal, boundary, failure, and service-adapter scenarios in fresh processes,
validates assertions, and generates work/R40-T025/results.md.
A check must exit non-zero when an assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(ROOT_DIR, "work", "R40-T025")
EXAMPLE_PATH = os.path.join(ROOT_DIR, "17-ai-agents", "applied-labs", "r40-t025", "example.py")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def main() -> int:
    print(f"=== Running R40-T025 Checks from {ROOT_DIR} ===")
    results_markdown_lines = [
        "# R40-T025 — Verification Results",
        "",
        "This report records all inputs, expected vs. actual outputs, exit codes, and verification assertions for Task R40-T025.",
        "Focus: Put the external dependency behind a callable interface and supply the deterministic local adapter. Identify which real-service behavior this mock does not establish.",
        "",
        "---",
        "",
    ]

    # 1. Check 1: Normal Addition add(2, 3) -> 5
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
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "success",
            "tool": "add",
            "arguments": {"a": 2, "b": 3},
            "result": 5,
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
        "**Result:** PASS — Addition executed successfully via deterministic local adapter with strict numeric typing.",
        "",
        "---",
        "",
    ])

    # 2. Check 2: Normal Multiplication multiply(2, 3) -> 6
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
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"multiply\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
        "```",
        "",
        "Expected output:",
        "```json",
        json.dumps({
            "status": "success",
            "tool": "multiply",
            "arguments": {"a": 2, "b": 3},
            "result": 6,
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
        "**Result:** PASS — Multiplication executed successfully via deterministic local adapter with strict numeric typing.",
        "",
        "---",
        "",
    ])

    # 3. Check 3: Unknown Tool Error
    print("Running Check 3: Unknown Tool Error (divide)...")
    cmd3 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "divide", "arguments": {"a": 6, "b": 2}}']
    res3 = run_cmd(cmd3)
    assert res3.returncode == 1, f"Expected returncode 1, got {res3.returncode}"
    data3 = json.loads(res3.stdout)
    assert data3["status"] == "error", "Expected status 'error'"
    assert data3["error"]["type"] == "UnknownToolError", f"Expected UnknownToolError, got {data3['error']['type']}"
    assert data3["error"]["code"] == "TOOL_NOT_ALLOWED", f"Expected TOOL_NOT_ALLOWED, got {data3['error']['code']}"
    assert data3["error"]["details"]["tool"] == "divide"
    assert data3["error"]["details"]["allowed_tools"] == ["add", "multiply"]

    results_markdown_lines.extend([
        "## 3. Failure Scenario: Unknown Tool (`divide`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"divide\", \"arguments\": {\"a\": 6, \"b\": 2}}'",
        "```",
        "",
        "Expected error envelope:",
        "```json",
        json.dumps({
            "status": "error",
            "error": {
                "type": "UnknownToolError",
                "code": "TOOL_NOT_ALLOWED",
                "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
                "details": {
                    "tool": "divide",
                    "allowed_tools": ["add", "multiply"],
                },
            },
            "tool": "divide",
            "arguments": {"a": 6, "b": 2},
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
        "**Result:** PASS — Unknown tool was rejected with structured UnknownToolError envelope and exit code 1.",
        "",
        "---",
        "",
    ])

    # 4. Check 4: String Argument a Error
    print("Running Check 4: String Argument 'a' Error...")
    cmd4 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": "2", "b": 3}}']
    res4 = run_cmd(cmd4)
    assert res4.returncode == 1, f"Expected returncode 1, got {res4.returncode}"
    data4 = json.loads(res4.stdout)
    assert data4["status"] == "error", "Expected status 'error'"
    assert data4["error"]["type"] == "ValidationError", f"Expected ValidationError, got {data4['error']['type']}"
    assert data4["error"]["code"] == "INVALID_ARGUMENT_TYPE", f"Expected INVALID_ARGUMENT_TYPE, got {data4['error']['code']}"
    assert data4["error"]["details"]["parameter"] == "a"
    assert data4["error"]["details"]["received_type"] == "str"

    results_markdown_lines.extend([
        "## 4. Failure Scenario: String Argument `a = \"2\"`",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": \"2\", \"b\": 3}}'",
        "```",
        "",
        "Expected error envelope:",
        "```json",
        json.dumps({
            "status": "error",
            "error": {
                "type": "ValidationError",
                "code": "INVALID_ARGUMENT_TYPE",
                "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
                "details": {
                    "parameter": "a",
                    "expected": "finite number (int or float)",
                    "received_type": "str",
                    "received_value": "2",
                },
            },
            "tool": "add",
            "arguments": {"a": "2", "b": 3},
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
        "**Result:** PASS — String argument was rejected with structured ValidationError envelope and exit code 1.",
        "",
        "---",
        "",
    ])

    # 5. Check 5: Pipeline Failure Halting & Isolation
    print("Running Check 5: Pipeline Failure Halting & Isolation...")
    pipeline_arg = '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
    cmd5 = [sys.executable, EXAMPLE_PATH, "--pipeline", pipeline_arg]
    res5 = run_cmd(cmd5)
    assert res5.returncode == 1, f"Expected returncode 1, got {res5.returncode}"
    data5 = json.loads(res5.stdout)
    assert data5["status"] == "error", "Expected status 'error'"
    assert data5["pipeline_halted"] is True, "Expected pipeline_halted to be True"
    assert data5["failed_step_index"] == 0, f"Expected failed_step_index 0, got {data5['failed_step_index']}"
    assert data5["completed_steps"] == 0, f"Expected completed_steps 0, got {data5['completed_steps']}"
    assert len(data5["aborted_calls"]) == 1, f"Expected 1 aborted call, got {len(data5['aborted_calls'])}"
    assert data5["aborted_calls"][0]["tool"] == "multiply", "Expected multiply call to be aborted"

    results_markdown_lines.extend([
        "## 5. Pipeline Failure Halting & Tool Isolation",
        "",
        "Command:",
        "```bash",
        f"python3 17-ai-agents/applied-labs/r40-t025/example.py --pipeline '{pipeline_arg}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res5.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res5.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Pipeline halted immediately on first call failure. The subsequent tool (`multiply`) was aborted and never executed.",
        "",
        "---",
        "",
    ])

    # 6. Check 6: Boundary Zeros
    print("Running Check 6: Boundary Zeros add(0, 0) -> 0...")
    cmd6 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": 0, "b": 0}}']
    res6 = run_cmd(cmd6)
    assert res6.returncode == 0, f"Expected returncode 0, got {res6.returncode}"
    data6 = json.loads(res6.stdout)
    assert data6["result"] == 0

    results_markdown_lines.extend([
        "## 6. Boundary Scenario: Zeros (`add(0, 0) -> 0`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": 0, \"b\": 0}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res6.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res6.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Zeros properly handled as valid finite numeric boundary.",
        "",
        "---",
        "",
    ])

    # 7. Check 7: Boundary Negative Numbers
    print("Running Check 7: Boundary Negative Numbers multiply(-2, 3) -> -6...")
    cmd7 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "multiply", "arguments": {"a": -2, "b": 3}}']
    res7 = run_cmd(cmd7)
    assert res7.returncode == 0, f"Expected returncode 0, got {res7.returncode}"
    data7 = json.loads(res7.stdout)
    assert data7["result"] == -6

    results_markdown_lines.extend([
        "## 7. Boundary Scenario: Negative Numbers (`multiply(-2, 3) -> -6`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"multiply\", \"arguments\": {\"a\": -2, \"b\": 3}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res7.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res7.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Signed arithmetic correctly executed.",
        "",
        "---",
        "",
    ])

    # 8. Check 8: Boundary Decision on Booleans
    print("Running Check 8: Boundary Decision on Booleans...")
    cmd8 = [sys.executable, EXAMPLE_PATH, "--call", '{"tool": "add", "arguments": {"a": true, "b": 3}}']
    res8 = run_cmd(cmd8)
    assert res8.returncode == 1, f"Expected returncode 1, got {res8.returncode}"
    data8 = json.loads(res8.stdout)
    assert data8["status"] == "error"
    assert data8["error"]["code"] == "INVALID_ARGUMENT_TYPE"

    results_markdown_lines.extend([
        "## 8. Boundary Decision: Booleans Strictly Rejected",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --call '{\"tool\": \"add\", \"arguments\": {\"a\": true, \"b\": 3}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res8.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res8.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Booleans strictly rejected to prevent type coercion vulnerabilities in tool dispatch.",
        "",
        "---",
        "",
    ])

    # 9. Check 9: Real-Service Gaps Introspection
    print("Running Check 9: Real-Service Gaps Introspection...")
    cmd9 = [sys.executable, EXAMPLE_PATH, "--show-service-gaps"]
    res9 = run_cmd(cmd9)
    assert res9.returncode == 0, f"Expected returncode 0, got {res9.returncode}"
    data9 = json.loads(res9.stdout)
    assert "unestablished_behaviors" in data9
    assert len(data9["unestablished_behaviors"]) == 8, f"Expected 8 unestablished categories, got {len(data9['unestablished_behaviors'])}"

    results_markdown_lines.extend([
        "## 9. Real-Service Gaps Introspection (`--show-service-gaps`)",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --show-service-gaps",
        "```",
        "",
        "Actual output (abbreviated):",
        "```json",
        res9.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res9.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Explicitly exposes the 8 real-service behaviors that this local offline adapter does not establish.",
        "",
        "---",
        "",
    ])

    # 10. Check 10: Swappable Adapter Test (Deliberate Wrong Adapter)
    print("Running Check 10: Swappable Adapter Test (Deliberate Wrong Adapter)...")
    cmd10 = [sys.executable, EXAMPLE_PATH, "--adapter", "deliberate-wrong", "--call", '{"tool": "add", "arguments": {"a": 2, "b": 3}}']
    res10 = run_cmd(cmd10)
    assert res10.returncode == 0, f"Expected returncode 0, got {res10.returncode}"
    data10 = json.loads(res10.stdout)
    assert data10["result"] == 999, f"Expected deliberate wrong result 999, got {data10['result']}"

    results_markdown_lines.extend([
        "## 10. Swappable Adapter Test: Callable Interface Demonstration",
        "",
        "Command:",
        "```bash",
        "python3 17-ai-agents/applied-labs/r40-t025/example.py --adapter deliberate-wrong --call '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'",
        "```",
        "",
        "Actual output:",
        "```json",
        res10.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res10.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Callable interface allowed hot-swapping the backend adapter to `DeliberateWrongResultAdapter` without altering dispatcher logic.",
        "",
        "---",
        "",
    ])

    # 11. Check 11: Automated Test Suite Execution
    print("Running Check 11: Unit Test Suite Discovery...")
    test_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "17-ai-agents/applied-labs/r40-t025",
        "-p",
        "test_*.py",
        "-v",
    ]
    res11 = run_cmd(test_cmd)
    assert res11.returncode == 0, f"Unit tests failed with code {res11.returncode}: {res11.stderr}"
    assert "Ran 31 tests" in res11.stderr or "Ran 31 tests" in res11.stdout, "Expected 31 tests to run"
    assert "OK" in res11.stderr or "OK" in res11.stdout, "Expected OK in test output"

    results_markdown_lines.extend([
        "## 11. Automated Test Suite Execution",
        "",
        "Command:",
        "```bash",
        "python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t025 -p \"test_*.py\" -v",
        "```",
        "",
        "Test output:",
        "```text",
        res11.stderr.strip() or res11.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res11.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 31 unit, boundary, pipeline, and integration tests passed.",
        "",
        "---",
        "",
    ])

    # 12. Check 12: Deliberate Failure Verification
    print("Running Check 12: Deliberate Wrong Assertion Failure Check...")
    deliberate_cmd = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys, json; "
            "res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t025/example.py', "
            "'--call', '{\"tool\": \"add\", \"arguments\": {\"a\": 2, \"b\": 3}}'], capture_output=True, text=True); "
            "data = json.loads(res.stdout); "
            "assert data['result'] == 999, 'Deliberate test failure: expected 999 got ' + str(data['result'])"
        ),
    ]
    res12 = run_cmd(deliberate_cmd)
    assert res12.returncode != 0, "Deliberate wrong assertion MUST fail with nonzero exit code!"

    results_markdown_lines.extend([
        "## 12. Deliberate Failure Verification",
        "",
        "Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.",
        "",
        "Command:",
        "```bash",
        "python3 -c \"import subprocess, sys, json; res = subprocess.run([sys.executable, '17-ai-agents/applied-labs/r40-t025/example.py', '--call', '{\\\"tool\\\": \\\"add\\\", \\\"arguments\\\": {\\\"a\\\": 2, \\\"b\\\": 3}}'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['result'] == 999, 'Deliberate test failure for assertion verification'\"",
        "```",
        "",
        "Output:",
        "```text",
        res12.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res12.returncode}` (Expected non-zero: `1`)",
        "",
        "**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.",
        "",
        "---",
        "",
        "## Summary of Verification Checks",
        "",
        "| Check ID | Description | Status | Exit Code |",
        "|---|---|---|---|",
        "| 1 | Normal Addition (`add(2, 3) -> 5`) | PASS | 0 |",
        "| 2 | Normal Multiplication (`multiply(2, 3) -> 6`) | PASS | 0 |",
        "| 3 | Unknown Tool Error (`divide`) | PASS | 1 |",
        "| 4 | String Argument Error (`a = \"2\"`) | PASS | 1 |",
        "| 5 | Pipeline Halting & Tool Isolation | PASS | 1 |",
        "| 6 | Boundary Zeros (`0, 0`) | PASS | 0 |",
        "| 7 | Boundary Negative Arithmetic (`-2 * 3 = -6`) | PASS | 0 |",
        "| 8 | Boundary Decision on Booleans (`a = true`) | PASS | 1 |",
        "| 9 | Real-Service Gaps Introspection (8 categories) | PASS | 0 |",
        "| 10 | Swappable Adapter Test (`DeliberateWrongResultAdapter`) | PASS | 0 |",
        "| 11 | Automated Test Suite (31 unit tests) | PASS | 0 |",
        "| 12 | Deliberate Failure Verification | PASS | 1 (Expected Nonzero) |",
        "",
        "All checks passed successfully. Verification complete.",
    ])

    results_path = os.path.join(WORK_DIR, "results.md")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results_markdown_lines) + "\n")

    print(f"Results successfully written to {results_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
