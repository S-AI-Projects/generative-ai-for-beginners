#!/usr/bin/env python3
"""Verification check runner for R40-T023.

Runs all normal, boundary, missing-information, comparison checker, unit test,
and deliberate failure scenarios in fresh subprocesses.
Validates assertions and generates work/R40-T023/results.md.
A check strictly exits non-zero if any assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T023")
LAB_DIR = os.path.join(REPO_ROOT, "16-open-source-models", "applied-labs", "r40-t023")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Runs command in fresh process with output captured."""
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> int:
    results_markdown_lines: List[str] = [
        "# R40-T023 — Verification Results",
        "",
        "This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T023.",
        "",
        "---",
        "",
    ]

    # 1. Normal Scenario
    print("Running Check 1: Normal scenario (OLMo exemplar)...")
    cmd1 = [sys.executable, EXAMPLE_PY, "--scenario", "normal"]
    res1 = run_cmd(cmd1)
    assert res1.returncode == 0, f"Check 1 failed: exit {res1.returncode}, stderr: {res1.stderr}"
    data1 = json.loads(res1.stdout)
    assert data1["all_passed"] is True
    assert data1["scenarios"][0]["direct_decision"] == "OPEN_SOURCE"
    assert data1["scenarios"][0]["independent_decision"] == "OPEN_SOURCE"
    assert data1["scenarios"][0]["approaches_agree"] is True

    results_markdown_lines.extend([
        "## 1. Normal Scenario (AllenAI OLMo Exemplar)",
        "",
        "Command:",
        "```bash",
        "python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario normal",
        "```",
        "",
        "Expected Decision: `OPEN_SOURCE`",
        "",
        "Actual Output:",
        "```json",
        res1.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res1.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Meets all 5 lesson criteria plus OSI license. Direct rule engine and independent calculation agree.",
        "",
        "---",
        "",
    ])

    # 2. Boundary Scenario
    print("Running Check 2: Boundary scenario (Llama 2 / Mistral exemplar)...")
    cmd2 = [sys.executable, EXAMPLE_PY, "--scenario", "boundary"]
    res2 = run_cmd(cmd2)
    assert res2.returncode == 0, f"Check 2 failed: exit {res2.returncode}, stderr: {res2.stderr}"
    data2 = json.loads(res2.stdout)
    assert data2["all_passed"] is True
    assert data2["scenarios"][0]["direct_decision"] == "OPEN_WEIGHTS"
    assert data2["scenarios"][0]["independent_decision"] == "OPEN_WEIGHTS"
    assert data2["scenarios"][0]["approaches_agree"] is True

    results_markdown_lines.extend([
        "## 2. Boundary Scenario (Llama 2 / Mistral Exemplar)",
        "",
        "Command:",
        "```bash",
        "python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario boundary",
        "```",
        "",
        "Expected Decision: `OPEN_WEIGHTS`",
        "",
        "Actual Output:",
        "```json",
        res2.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res2.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Weights and fine-tuning are public, but training data and metrics are withheld. Correctly categorized as an open model / open weights boundary.",
        "",
        "---",
        "",
    ])

    # 3. Missing Information Scenario
    print("Running Check 3: Missing information scenario (unverified disclosures)...")
    cmd3 = [sys.executable, EXAMPLE_PY, "--scenario", "missing_info"]
    res3 = run_cmd(cmd3)
    assert res3.returncode == 0, f"Check 3 failed: exit {res3.returncode}, stderr: {res3.stderr}"
    data3 = json.loads(res3.stdout)
    assert data3["all_passed"] is True
    assert data3["scenarios"][0]["direct_decision"] == "UNDETERMINED"
    assert data3["scenarios"][0]["independent_decision"] == "UNDETERMINED"
    assert data3["scenarios"][0]["approaches_agree"] is True

    results_markdown_lines.extend([
        "## 3. Missing Information Scenario (Unverified Disclosures)",
        "",
        "Command:",
        "```bash",
        "python3 16-open-source-models/applied-labs/r40-t023/example.py --scenario missing_info",
        "```",
        "",
        "Expected Decision: `UNDETERMINED`",
        "",
        "Actual Output:",
        "```json",
        res3.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res3.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Required transparency criteria are `None`, appropriately yielding `UNDETERMINED` across both approaches.",
        "",
        "---",
        "",
    ])

    # 4. Full Published Decision Table Comparison Checker
    print("Running Check 4: Full published decision table checker...")
    cmd4 = [sys.executable, EXAMPLE_PY, "--check"]
    res4 = run_cmd(cmd4)
    assert res4.returncode == 0, f"Check 4 failed: exit {res4.returncode}, stderr: {res4.stderr}"
    data4 = json.loads(res4.stdout)
    assert data4["all_passed"] is True
    assert data4["total_scenarios"] == 3
    assert data4["passed_scenarios"] == 3
    assert data4["failed_scenarios"] == 0

    results_markdown_lines.extend([
        "## 4. Full Decision Table Comparison Checker",
        "",
        "Command:",
        "```bash",
        "python3 16-open-source-models/applied-labs/r40-t023/example.py --check",
        "```",
        "",
        "Actual Output:",
        "```json",
        res4.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res4.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 3 scenarios verified; Approach 1 (direct engine) and Approach 2 (independent baseline) agree across every scenario.",
        "",
        "---",
        "",
    ])

    # 5. Custom Payload Evaluation via --call
    print("Running Check 5: Custom payload evaluation via --call...")
    call_payload = json.dumps({
        "model_id": "custom-eval-model",
        "facts": {
            "model_weights_public": True,
            "training_datasets_public": True,
            "evaluation_code_public": True,
            "fine_tuning_code_public": True,
            "training_metrics_public": True,
            "osi_approved_license": True,
        },
    })
    cmd5 = [sys.executable, EXAMPLE_PY, "--call", call_payload]
    res5 = run_cmd(cmd5)
    assert res5.returncode == 0, f"Check 5 failed: exit {res5.returncode}, stderr: {res5.stderr}"
    data5 = json.loads(res5.stdout)
    assert data5["direct_evaluation"]["decision"] == "OPEN_SOURCE"
    assert data5["independent_decision"] == "OPEN_SOURCE"
    assert data5["approaches_agree"] is True

    results_markdown_lines.extend([
        "## 5. Custom JSON Payload Evaluation",
        "",
        "Command:",
        "```bash",
        f"python3 16-open-source-models/applied-labs/r40-t023/example.py --call '{call_payload}'",
        "```",
        "",
        "Actual Output:",
        "```json",
        res5.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res5.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Custom JSON payload processed cleanly by both approaches.",
        "",
        "---",
        "",
    ])

    # 6. Deliberate Tamper Test Detection
    print("Running Check 6: Tamper test failure verification...")
    cmd6 = [sys.executable, EXAMPLE_PY, "--tamper-test"]
    res6 = run_cmd(cmd6)
    assert res6.returncode == 1, f"Check 6 failed: expected returncode 1, got {res6.returncode}"
    assert "DecisionMismatchError" in res6.stderr, f"Missing DecisionMismatchError in stderr: {res6.stderr}"

    results_markdown_lines.extend([
        "## 6. Deliberate Tamper Test Verification",
        "",
        "Command:",
        "```bash",
        "python3 16-open-source-models/applied-labs/r40-t023/example.py --tamper-test",
        "```",
        "",
        "Actual Stderr:",
        "```text",
        res6.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res6.returncode}` (Expected non-zero: `1`)",
        "",
        "**Result:** PASS — Deliberately changing a decision in the table triggers `DecisionMismatchError` and exits with code 1.",
        "",
        "---",
        "",
    ])

    # 7. Automated Unit Test Discovery
    print("Running Check 7: Automated unit test suite...")
    cmd7 = [sys.executable, "-m", "unittest", "discover", "-s", LAB_DIR, "-p", "test_*.py", "-v"]
    res7 = run_cmd(cmd7)
    assert res7.returncode == 0, f"Check 7 failed: exit {res7.returncode}, stderr: {res7.stderr}"
    assert "Ran 23 tests" in res7.stderr or "Ran 23 tests" in res7.stdout

    results_markdown_lines.extend([
        "## 7. Automated Unit Test Discovery",
        "",
        "Command:",
        "```bash",
        "python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t023 -p \"test_*.py\" -v",
        "```",
        "",
        "Test Output:",
        "```text",
        res7.stderr.strip() or res7.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res7.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 23 unit and CLI tests passed.",
        "",
        "---",
        "",
    ])

    # 8. Deliberate Wrong Assertion Failure Check
    print("Running Check 8: Deliberate wrong assertion failure check...")
    cmd8 = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys, json; "
            "res = subprocess.run([sys.executable, '16-open-source-models/applied-labs/r40-t023/example.py', "
            "'--scenario', 'normal'], capture_output=True, text=True); "
            "data = json.loads(res.stdout); "
            "assert data['scenarios'][0]['direct_decision'] == 'FORCED_WRONG_DECISION', "
            "'Deliberate test failure: expected FORCED_WRONG_DECISION'"
        ),
    ]
    res8 = run_cmd(cmd8)
    assert res8.returncode != 0, "Check 8 failed: deliberate wrong assertion MUST fail with nonzero exit code!"

    results_markdown_lines.extend([
        "## 8. Deliberate Wrong Assertion Verification",
        "",
        "Demonstrates that an assertion check strictly fails and exits nonzero when an assertion fails.",
        "",
        "Command:",
        "```bash",
        "python3 -c \"import subprocess, sys, json; res = subprocess.run([sys.executable, '16-open-source-models/applied-labs/r40-t023/example.py', '--scenario', 'normal'], capture_output=True, text=True); data = json.loads(res.stdout); assert data['scenarios'][0]['direct_decision'] == 'FORCED_WRONG_DECISION'\"",
        "```",
        "",
        "Actual Output:",
        "```text",
        res8.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res8.returncode}` (Expected non-zero: `1`)",
        "",
        "**Result:** PASS — Deliberate wrong expectation triggered `AssertionError` and returned exit code 1 as required.",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Check ID | Description | Status | Exit Code |",
        "|---|---|---|---|",
        "| 1 | Normal Scenario (`AllenAI OLMo -> OPEN_SOURCE`) | PASS | 0 |",
        "| 2 | Boundary Scenario (`Llama 2 / Mistral -> OPEN_WEIGHTS`) | PASS | 0 |",
        "| 3 | Missing Information Scenario (`Unverified -> UNDETERMINED`) | PASS | 0 |",
        "| 4 | Full Decision Table Comparison Checker | PASS | 0 |",
        "| 5 | Custom JSON Payload Evaluation | PASS | 0 |",
        "| 6 | Deliberate Tamper Test Detection | PASS | 1 (Expected Nonzero) |",
        "| 7 | Automated Unit Test Suite (23 tests) | PASS | 0 |",
        "| 8 | Deliberate Wrong Assertion Verification | PASS | 1 (Expected Nonzero) |",
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
