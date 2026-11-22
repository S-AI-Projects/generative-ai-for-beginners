#!/usr/bin/env python3
"""Verification check runner for R40-T001.

Runs normal, error recovery, boundary rejection, decision table check,
deliberate tamper, and automated unit test discovery in fresh subprocesses.
Validates all assertions and writes work/R40-T001/results.md.
A check strictly exits non-zero if any assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T001")
LAB_DIR = os.path.join(REPO_ROOT, "12-designing-ux-for-ai-applications", "applied-labs", "r40-t001")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Runs a command in a fresh subprocess with output captured."""
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T001 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "STATE_COMPLETE_SUCCESS", "Normal decision mismatch"
    assert normal_data["state"] == "complete", "Normal state mismatch"
    assert normal_data["content"] == "Hello, how can I assist you today?", "Normal content mismatch"
    assert normal_data["chunks_received"] == 2, "Normal chunks mismatch"
    print("✓ Normal scenario passed.")

    # 2. Error recovery scenario
    res_error = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "error"])
    if res_error.returncode != 0:
        sys.stderr.write(f"Error scenario failed: {res_error.stderr}\n")
        sys.exit(1)
    error_data = json.loads(res_error.stdout)
    assert error_data["decision"] == "STATE_ERROR_RECOVERED", "Error decision mismatch"
    assert error_data["state"] == "error", "Error state mismatch"
    assert error_data["content"] == "Hello, [ERROR: Stream connection dropped unexpectedly]", "Error content mismatch"
    assert error_data["chunks_received"] == 1, "Error chunks mismatch"
    print("✓ Error recovery scenario passed.")

    # 3. Boundary rejection scenario
    res_boundary = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "boundary"])
    if res_boundary.returncode != 0:
        sys.stderr.write(f"Boundary scenario failed: {res_boundary.stderr}\n")
        sys.exit(1)
    boundary_data = json.loads(res_boundary.stdout)
    assert boundary_data["decision"] == "CHUNK_AFTER_COMPLETION_REJECTED", "Boundary decision mismatch"
    assert boundary_data["rejection_verified"] is True, "Boundary rejection not verified"
    assert boundary_data["rejection_exception"] == "ChunkRejectedError", "Boundary exception mismatch"
    print("✓ Boundary scenario passed.")

    # 4. Canonical check
    res_check = run_cmd([sys.executable, EXAMPLE_PY, "--check"])
    if res_check.returncode != 0:
        sys.stderr.write(f"Canonical check failed: {res_check.stderr}\n")
        sys.exit(1)
    check_data = json.loads(res_check.stdout)
    assert check_data["all_passed"] is True, "Canonical check all_passed mismatch"
    print("✓ Canonical check passed.")

    # 5. Deliberate tamper check (MUST exit non-zero)
    res_tamper = run_cmd([sys.executable, EXAMPLE_PY, "--tamper"])
    if res_tamper.returncode == 0:
        sys.stderr.write("Tamper check unexpectedly succeeded with exit code 0!\n")
        sys.exit(1)
    tamper_err = json.loads(res_tamper.stderr)
    assert tamper_err["status"] == "expected_tamper_failure", "Tamper status mismatch"
    assert tamper_err["error_type"] == "DecisionMismatchError", "Tamper error type mismatch"
    print("✓ Deliberate tamper test verified: non-zero exit on assertion mismatch.")

    # 6. Unittest discovery
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
        f.write("# R40-T001 — Verification Results\n\n")
        f.write("This report records the inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T001.\n\n")
        f.write("## 1. Normal Scenario\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Error Recovery Scenario\n```json\n" + json.dumps(error_data, indent=2) + "\n```\n\n")
        f.write("## 3. Boundary Rejection Scenario\n```json\n" + json.dumps(boundary_data, indent=2) + "\n```\n\n")
        f.write("## 4. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 5. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
