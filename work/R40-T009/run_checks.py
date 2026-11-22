#!/usr/bin/env python3
"""Verification check runner for R40-T009.

Runs normal, unknown tool, string argument, cascade prevention scenarios,
evaluation experiment, canonical check, tamper mode, and automated unittest discovery.
Writes work/R40-T009/results.md. Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T009")
LAB_DIR = os.path.join(REPO_ROOT, "17-ai-agents", "applied-labs", "r40-t009")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T009 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "TOOLS_DISPATCHED_SUCCESSFULLY"
    assert normal_data["add_result"] == 5
    assert normal_data["multiply_result"] == 6
    print("✓ Normal scenario passed.")

    # 2. Unknown tool scenario
    res_unknown = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "unknown"])
    if res_unknown.returncode != 0:
        sys.stderr.write(f"Unknown tool scenario failed: {res_unknown.stderr}\n")
        sys.exit(1)
    unknown_data = json.loads(res_unknown.stdout)
    assert unknown_data["decision"] == "UNKNOWN_TOOL_REJECTED"
    assert unknown_data["response"]["error_type"] == "UnknownToolError"
    print("✓ Unknown tool scenario passed.")

    # 3. String type scenario
    res_string = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "string_type"])
    if res_string.returncode != 0:
        sys.stderr.write(f"String type scenario failed: {res_string.stderr}\n")
        sys.exit(1)
    string_data = json.loads(res_string.stdout)
    assert string_data["decision"] == "STRING_ARG_REJECTED"
    assert string_data["response"]["error_type"] == "TypeValidationError"
    print("✓ String type scenario passed.")

    # 4. Cascade prevention scenario
    res_cascade = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "cascade"])
    if res_cascade.returncode != 0:
        sys.stderr.write(f"Cascade scenario failed: {res_cascade.stderr}\n")
        sys.exit(1)
    cascade_data = json.loads(res_cascade.stdout)
    assert cascade_data["decision"] == "CASCADE_EXECUTION_BLOCKED"
    assert cascade_data["executed_count"] == 0
    print("✓ Cascade prevention scenario passed.")

    # 5. Evaluation experiment
    res_exp = run_cmd([sys.executable, EXAMPLE_PY, "--experiment"])
    if res_exp.returncode != 0:
        sys.stderr.write(f"Experiment failed: {res_exp.stderr}\n")
        sys.exit(1)
    exp_data = json.loads(res_exp.stdout)
    assert exp_data["contract_satisfied"] is True
    print("✓ Evaluation experiment passed.")

    # 6. Canonical check
    res_check = run_cmd([sys.executable, EXAMPLE_PY, "--check"])
    if res_check.returncode != 0:
        sys.stderr.write(f"Canonical check failed: {res_check.stderr}\n")
        sys.exit(1)
    check_data = json.loads(res_check.stdout)
    assert check_data["all_passed"] is True
    print("✓ Canonical check passed.")

    # 7. Tamper check (MUST exit non-zero)
    res_tamper = run_cmd([sys.executable, EXAMPLE_PY, "--tamper"])
    if res_tamper.returncode == 0:
        sys.stderr.write("Tamper check unexpectedly succeeded with exit code 0!\n")
        sys.exit(1)
    tamper_err = json.loads(res_tamper.stderr)
    assert tamper_err["status"] == "expected_tamper_failure"
    assert tamper_err["error_type"] == "DecisionMismatchError"
    print("✓ Deliberate tamper test verified: non-zero exit on assertion mismatch.")

    # 8. Unittest discovery
    res_test = run_cmd([
        sys.executable, "-m", "unittest", "discover",
        "-s", os.path.relpath(LAB_DIR, REPO_ROOT),
        "-p", "test_*.py", "-v"
    ])
    if res_test.returncode != 0:
        sys.stderr.write(f"Unittest discovery failed:\n{res_test.stderr}\n")
        sys.exit(1)
    print("✓ Unittest discovery passed.")

    # Generate results.md
    with open(RESULTS_MD, "w") as f:
        f.write("# R40-T009 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T009.\n\n")
        f.write("## 1. Normal Scenario (add(2,3)->5, multiply(2,3)->6)\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Unknown Tool Rejection Scenario\n```json\n" + json.dumps(unknown_data, indent=2) + "\n```\n\n")
        f.write("## 3. String Type Rejection Scenario\n```json\n" + json.dumps(string_data, indent=2) + "\n```\n\n")
        f.write("## 4. Cascade Prevention Scenario\n```json\n" + json.dumps(cascade_data, indent=2) + "\n```\n\n")
        f.write("## 5. Three Controlled Configurations Evaluation Output\n```json\n" + json.dumps(exp_data, indent=2) + "\n```\n\n")
        f.write("## 6. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 7. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
