#!/usr/bin/env python3
"""
Verification Script for Task R40-T030
Lesson: 12-designing-ux-for-ai-applications

Executes all verification checks:
1. Normal Scenario (--scenario normal)
2. Error Recovery Scenario (--scenario error)
3. Boundary Scenario (--scenario boundary)
4. Question 1 Assessment (--question 1)
5. Question 2 Assessment (--question 2)
6. Question 3 Assessment (--question 3)
7. Full Questions Assessment (--questions)
8. Decision Table Check (--check)
9. Deliberate Tamper Test (--tamper) -> non-zero exit validation
10. Automated Unit Test Discovery Suite (python3 -m unittest discover ...)

Generates work/R40-T030/results.md recording inputs, expected vs actual outputs,
exit codes, and pass/fail statuses.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MODULE_PATH = os.path.join(
    REPO_ROOT,
    "12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py",
)
TEST_DIR = os.path.join(
    REPO_ROOT,
    "12-designing-ux-for-ai-applications/applied-labs/r40-t030",
)
RESULTS_MD = os.path.join(REPO_ROOT, "work/R40-T030/results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Runs a command and returns CompletedProcess."""
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    print(f"=== Starting Verification Checks for R40-T030 ===")
    print(f"Repository Root: {REPO_ROOT}")
    print(f"Target Module:   {MODULE_PATH}")
    print(f"Test Directory:  {TEST_DIR}")
    print()

    results_markdown_lines = [
        "# R40-T030 — Verification Results",
        "",
        "This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T030.",
        "**Focus:** Model local pending, streaming, complete and error states for one response with a stable message ID. Two chunks append in order; an error preserves received text with an error marker; chunks after completion are rejected.",
        "**Applied Questions Assessment:** Predict an output, diagnose a failure, and choose a boundary policy, each with architectural rationale and executable verification check.",
        "",
        "---",
        "",
    ]

    # -------------------------------------------------------------------------
    # 1. Normal Scenario
    # -------------------------------------------------------------------------
    print("Running Check 1: Normal Scenario (--scenario normal)...")
    cmd1 = [sys.executable, MODULE_PATH, "--scenario", "normal"]
    res1 = run_cmd(cmd1)
    assert res1.returncode == 0, f"Check 1 failed: exit {res1.returncode}, stderr: {res1.stderr}"
    data1 = json.loads(res1.stdout)
    assert data1["decision"] == "STATE_COMPLETE_SUCCESS", f"Check 1 decision mismatch: {data1['decision']}"
    assert data1["state"] == "complete", f"Check 1 state mismatch: {data1['state']}"
    assert data1["content"] == "Hello, how can I assist you today?", f"Check 1 content mismatch: {data1['content']}"
    assert data1["chunks_received"] == 2, f"Check 1 chunks mismatch: {data1['chunks_received']}"
    assert data1["stable_id_preserved"] is True, "Check 1 stable ID not preserved"
    print("  ✓ Check 1 Passed: Normal scenario completed with stable ID and ordered chunks.")

    results_markdown_lines.extend([
        "## 1. Normal Scenario (`--scenario normal`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario normal",
        "```",
        "",
        "Expected Decision: `STATE_COMPLETE_SUCCESS`  ",
        "Expected State: `complete`  ",
        "Expected Content: `\"Hello, how can I assist you today?\"`  ",
        "Expected Chunks Received: `2`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data1, indent=2),
        "```",
        "",
        f"Exit code: `{res1.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Stable message ID preserved, two chunks appended strictly in order, and transitioned cleanly PENDING -> STREAMING -> COMPLETE.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 2. Error Recovery Scenario
    # -------------------------------------------------------------------------
    print("Running Check 2: Error Recovery Scenario (--scenario error)...")
    cmd2 = [sys.executable, MODULE_PATH, "--scenario", "error"]
    res2 = run_cmd(cmd2)
    assert res2.returncode == 0, f"Check 2 failed: exit {res2.returncode}, stderr: {res2.stderr}"
    data2 = json.loads(res2.stdout)
    assert data2["decision"] == "STATE_ERROR_RECOVERED", f"Check 2 decision mismatch: {data2['decision']}"
    assert data2["state"] == "error", f"Check 2 state mismatch: {data2['state']}"
    assert data2["content"] == "Hello, [ERROR: Stream connection dropped]", f"Check 2 content mismatch: {data2['content']}"
    assert data2["partial_text_preserved"] is True, "Check 2 partial text was not preserved"
    assert data2["error_marker_present"] is True, "Check 2 error marker missing"
    print("  ✓ Check 2 Passed: Error scenario preserved partial text and appended error marker.")

    results_markdown_lines.extend([
        "## 2. Error Recovery Scenario (`--scenario error`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario error",
        "```",
        "",
        "Expected Decision: `STATE_ERROR_RECOVERED`  ",
        "Expected State: `error`  ",
        "Expected Content: `\"Hello, [ERROR: Stream connection dropped]\"`  ",
        "Expected Partial Text Preservation: `true`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data2, indent=2),
        "```",
        "",
        f"Exit code: `{res2.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Previously received text intact ('Hello, ') with error marker appended in-place upon mid-stream failure.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 3. Boundary Scenario
    # -------------------------------------------------------------------------
    print("Running Check 3: Boundary Scenario (--scenario boundary)...")
    cmd3 = [sys.executable, MODULE_PATH, "--scenario", "boundary"]
    res3 = run_cmd(cmd3)
    assert res3.returncode == 0, f"Check 3 failed: exit {res3.returncode}, stderr: {res3.stderr}"
    data3 = json.loads(res3.stdout)
    assert data3["decision"] == "CHUNK_AFTER_COMPLETION_REJECTED", f"Check 3 decision mismatch: {data3['decision']}"
    assert data3["rejection_verified"] is True, "Check 3 rejection not verified"
    assert data3["rejection_exception"] == "ChunkRejectedError", f"Check 3 exception mismatch: {data3['rejection_exception']}"
    assert data3["buffer_unmodified"] is True, "Check 3 buffer was modified on late chunk"
    print("  ✓ Check 3 Passed: Boundary scenario rejected late chunk with ChunkRejectedError.")

    results_markdown_lines.extend([
        "## 3. Boundary Scenario — Late Chunk Rejection (`--scenario boundary`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --scenario boundary",
        "```",
        "",
        "Expected Decision: `CHUNK_AFTER_COMPLETION_REJECTED`  ",
        "Expected Rejection Exception: `ChunkRejectedError`  ",
        "Expected Buffer Unmodified: `true`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data3, indent=2),
        "```",
        "",
        f"Exit code: `{res3.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Delayed chunk rejected by raising ChunkRejectedError, preserving sealed buffer without corruption.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 4. Question 1 Assessment
    # -------------------------------------------------------------------------
    print("Running Check 4: Question 1 Assessment (--question 1)...")
    cmd4 = [sys.executable, MODULE_PATH, "--question", "1"]
    res4 = run_cmd(cmd4)
    assert res4.returncode == 0, f"Check 4 failed: exit {res4.returncode}, stderr: {res4.stderr}"
    data4 = json.loads(res4.stdout)
    assert data4["assessment"]["passed"] is True, f"Check 4 assessment failed: {data4}"
    assert data4["assessment"]["selected_option"] == "B", f"Check 4 wrong option: {data4['assessment']['selected_option']}"
    print("  ✓ Check 4 Passed: Question 1 (predict output) verified accurately.")

    results_markdown_lines.extend([
        "## 4. Applied Question 1: Predict an Output (`--question 1`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 1",
        "```",
        "",
        "**Question Focus:** `predict_an_output`  ",
        f"**Question Prompt:** {data4['question']['prompt']}  ",
        "**Selected Option:** `B` (`state='error', content='Hello, [ERROR: Stream connection dropped]'`)  ",
        "**Status:** `PASS`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data4, indent=2),
        "```",
        "",
        f"Exit code: `{res4.returncode}` (Expected: `0`)",
        "",
        f"**Rationale:** {data4['question']['rationale']}",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 5. Question 2 Assessment
    # -------------------------------------------------------------------------
    print("Running Check 5: Question 2 Assessment (--question 2)...")
    cmd5 = [sys.executable, MODULE_PATH, "--question", "2"]
    res5 = run_cmd(cmd5)
    assert res5.returncode == 0, f"Check 5 failed: exit {res5.returncode}, stderr: {res5.stderr}"
    data5 = json.loads(res5.stdout)
    assert data5["assessment"]["passed"] is True, f"Check 5 assessment failed: {data5}"
    assert data5["assessment"]["selected_option"] == "B", f"Check 5 wrong option: {data5['assessment']['selected_option']}"
    print("  ✓ Check 5 Passed: Question 2 (diagnose failure) verified accurately.")

    results_markdown_lines.extend([
        "## 5. Applied Question 2: Diagnose a Failure (`--question 2`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 2",
        "```",
        "",
        "**Question Focus:** `diagnose_a_failure`  ",
        f"**Question Prompt:** {data5['question']['prompt']}  ",
        "**Selected Option:** `B` (Attempted mutation of sealed message in terminal COMPLETE state)  ",
        "**Status:** `PASS`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data5, indent=2),
        "```",
        "",
        f"Exit code: `{res5.returncode}` (Expected: `0`)",
        "",
        f"**Rationale:** {data5['question']['rationale']}",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 6. Question 3 Assessment
    # -------------------------------------------------------------------------
    print("Running Check 6: Question 3 Assessment (--question 3)...")
    cmd6 = [sys.executable, MODULE_PATH, "--question", "3"]
    res6 = run_cmd(cmd6)
    assert res6.returncode == 0, f"Check 6 failed: exit {res6.returncode}, stderr: {res6.stderr}"
    data6 = json.loads(res6.stdout)
    assert data6["assessment"]["passed"] is True, f"Check 6 assessment failed: {data6}"
    assert data6["assessment"]["selected_option"] == "C", f"Check 6 wrong option: {data6['assessment']['selected_option']}"
    print("  ✓ Check 6 Passed: Question 3 (choose boundary policy) verified accurately.")

    results_markdown_lines.extend([
        "## 6. Applied Question 3: Choose a Boundary Policy (`--question 3`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --question 3",
        "```",
        "",
        "**Question Focus:** `choose_boundary_policy`  ",
        f"**Question Prompt:** {data6['question']['prompt']}  ",
        "**Selected Option:** `C` (`POLICY_EXPLICIT_REJECTION`: Fail-Fast with ChunkRejectedError)  ",
        "**Status:** `PASS`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data6, indent=2),
        "```",
        "",
        f"Exit code: `{res6.returncode}` (Expected: `0`)",
        "",
        f"**Rationale:** {data6['question']['rationale']}",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 7. Full Questions Assessment Suite
    # -------------------------------------------------------------------------
    print("Running Check 7: Full Questions Assessment (--questions)...")
    cmd7 = [sys.executable, MODULE_PATH, "--questions"]
    res7 = run_cmd(cmd7)
    assert res7.returncode == 0, f"Check 7 failed: exit {res7.returncode}, stderr: {res7.stderr}"
    data7 = json.loads(res7.stdout)
    assert data7["all_passed"] is True, f"Check 7 failed questions: {data7}"
    assert data7["total_questions"] == 3, f"Check 7 total count mismatch: {data7['total_questions']}"
    print("  ✓ Check 7 Passed: All 3 applied questions passed verification.")

    results_markdown_lines.extend([
        "## 7. Full Questions Assessment Suite (`--questions`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --questions",
        "```",
        "",
        "Expected Status: `success`  ",
        "Expected Passed Questions: `3 / 3`  ",
        "Expected All Passed: `true`",
        "",
        "Actual Summary:",
        "```json",
        json.dumps({
            "status": data7["status"],
            "total_questions": data7["total_questions"],
            "passed_questions": data7["passed_questions"],
            "failed_questions": data7["failed_questions"],
            "all_passed": data7["all_passed"],
        }, indent=2),
        "```",
        "",
        f"Exit code: `{res7.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 3 applied scenario assessment questions verified with factual answers and rationales.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 8. Decision Table Check
    # -------------------------------------------------------------------------
    print("Running Check 8: Decision Table Check (--check)...")
    cmd8 = [sys.executable, MODULE_PATH, "--check"]
    res8 = run_cmd(cmd8)
    assert res8.returncode == 0, f"Check 8 failed: exit {res8.returncode}, stderr: {res8.stderr}"
    data8 = json.loads(res8.stdout)
    assert data8["all_passed"] is True, f"Check 8 failed: {data8}"
    assert data8["total_scenarios"] == 3, f"Check 8 count mismatch: {data8['total_scenarios']}"
    print("  ✓ Check 8 Passed: Decision table check validated 3/3 scenarios.")

    results_markdown_lines.extend([
        "## 8. Canonical Decision Table Check (`--check`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --check",
        "```",
        "",
        "Expected Status: `success`  ",
        "Expected Passed Scenarios: `3 / 3`  ",
        "Expected All Passed: `true`",
        "",
        "Actual Output:",
        "```json",
        json.dumps(data8, indent=2),
        "```",
        "",
        f"Exit code: `{res8.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All canonical scenarios matched expected decisions, states, contents, and invariants.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 9. Deliberate Tamper Test
    # -------------------------------------------------------------------------
    print("Running Check 9: Deliberate Tamper Test (--tamper)...")
    cmd9 = [sys.executable, MODULE_PATH, "--tamper"]
    res9 = run_cmd(cmd9)
    assert res9.returncode == 1, f"Check 9 failed: expected exit 1, got {res9.returncode}"
    data9 = json.loads(res9.stderr)
    assert data9["status"] == "expected_tamper_failure", f"Check 9 status mismatch: {data9}"
    assert data9["error_type"] == "DecisionMismatchError", f"Check 9 error type mismatch: {data9}"
    print("  ✓ Check 9 Passed: Deliberate tamper test failed with exit code 1 as expected.")

    results_markdown_lines.extend([
        "## 9. Deliberate Tamper Regression Test (`--tamper`)",
        "",
        "Command:",
        "```bash",
        "python3 12-designing-ux-for-ai-applications/applied-labs/r40-t030/example.py --tamper",
        "```",
        "",
        "Expected Exit Code: `1`  ",
        "Expected Error Type: `DecisionMismatchError`  ",
        "Expected Status: `expected_tamper_failure`",
        "",
        "Actual Stderr Output:",
        "```json",
        json.dumps(data9, indent=2),
        "```",
        "",
        f"Exit code: `{res9.returncode}` (Expected: `1`)",
        "",
        "**Result:** PASS — Deliberate wrong expectation strictly failed assertion with exit code 1, proving regression sensitivity.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 10. Automated Unit Test Discovery Suite
    # -------------------------------------------------------------------------
    print("Running Check 10: Automated Unit Test Discovery Suite...")
    cmd10 = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        TEST_DIR,
        "-p",
        "test_*.py",
        "-v",
    ]
    res10 = run_cmd(cmd10)
    assert res10.returncode == 0, f"Check 10 failed: exit {res10.returncode}, stderr: {res10.stderr}"
    assert "Ran 41 tests" in res10.stderr or "Ran 41 tests" in res10.stdout, f"Check 10 count mismatch:\n{res10.stderr}"
    print("  ✓ Check 10 Passed: All 41 unit tests executed and passed cleanly via unittest discovery.")

    results_markdown_lines.extend([
        "## 10. Automated Unit Test Discovery Suite",
        "",
        "Command:",
        "```bash",
        "python3 -m unittest discover -s 12-designing-ux-for-ai-applications/applied-labs/r40-t030 -p \"test_*.py\" -v",
        "```",
        "",
        "Expected Status: `OK` with non-zero test count (41 tests)  ",
        "Expected Exit Code: `0`",
        "",
        "Actual Test Runner Output:",
        "```",
        res10.stderr.strip() if res10.stderr else res10.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res10.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 41 unit tests passed in fresh process without failures or errors.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # Summary Table
    # -------------------------------------------------------------------------
    results_markdown_lines.extend([
        "## 11. Summary of Verification Checks",
        "",
        "| # | Check / Scenario | Invocation / Action | Expected Result | Actual Result | Exit Code | Status |",
        "|---|---|---|---|---|---|---|",
        "| 1 | `SCENARIO_NORMAL` | `--scenario normal` | `STATE_COMPLETE_SUCCESS` | `STATE_COMPLETE_SUCCESS` | `0` | **PASS** |",
        "| 2 | `SCENARIO_ERROR` | `--scenario error` | `STATE_ERROR_RECOVERED` | `STATE_ERROR_RECOVERED` | `0` | **PASS** |",
        "| 3 | `SCENARIO_BOUNDARY` | `--scenario boundary` | `CHUNK_AFTER_COMPLETION_REJECTED` | `CHUNK_AFTER_COMPLETION_REJECTED` | `0` | **PASS** |",
        "| 4 | `QUESTION_1` | `--question 1` | `Q1_PREDICT_OUTPUT` (Opt B) | `Q1_PREDICT_OUTPUT` (Opt B) | `0` | **PASS** |",
        "| 5 | `QUESTION_2` | `--question 2` | `Q2_DIAGNOSE_FAILURE` (Opt B) | `Q2_DIAGNOSE_FAILURE` (Opt B) | `0` | **PASS** |",
        "| 6 | `QUESTION_3` | `--question 3` | `Q3_CHOOSE_BOUNDARY_POLICY` (Opt C) | `Q3_CHOOSE_BOUNDARY_POLICY` (Opt C) | `0` | **PASS** |",
        "| 7 | `QUESTIONS_ALL` | `--questions` | `3/3 passed` | `3/3 passed` | `0` | **PASS** |",
        "| 8 | `CANONICAL_CHECK` | `--check` | `all_passed: true` | `all_passed: true` | `0` | **PASS** |",
        "| 9 | `DELIBERATE_TAMPER` | `--tamper` | Exit `1` (`DecisionMismatchError`) | Exit `1` (`DecisionMismatchError`) | `1` | **PASS** |",
        "| 10 | `UNIT_TEST_SUITE` | `unittest discover` | `41/41 tests OK` | `41/41 tests OK` | `0` | **PASS** |",
        "",
        "All 10 checks passed successfully. Verification complete.",
        "",
    ])

    print(f"Writing results report to {RESULTS_MD}...")
    with open(RESULTS_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(results_markdown_lines))
    print(f"Successfully generated {RESULTS_MD}")
    print("=== Verification Suite Complete: 10/10 Passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
