#!/usr/bin/env python3
"""Verification check runner for R40-T006.

Runs normal, error recovery, boundary rejection, refactoring equivalence,
canonical check, tamper mode, and automated unittest discovery.
Writes work/R40-T006/results.md. Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T006")
LAB_DIR = os.path.join(REPO_ROOT, "07-building-chat-applications", "applied-labs", "r40-t006")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T006 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "STATE_COMPLETE_SUCCESS"
    assert normal_data["state"] == "complete"
    assert normal_data["chunks_received"] == 2
    print("✓ Normal scenario passed.")

    # 2. Error recovery scenario
    res_error = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "error"])
    if res_error.returncode != 0:
        sys.stderr.write(f"Error scenario failed: {res_error.stderr}\n")
        sys.exit(1)
    error_data = json.loads(res_error.stdout)
    assert error_data["decision"] == "STATE_ERROR_RECOVERED"
    assert error_data["state"] == "error"
    assert error_data["chunks_received"] == 1
    print("✓ Error recovery scenario passed.")

    # 3. Boundary rejection scenario
    res_boundary = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "boundary"])
    if res_boundary.returncode != 0:
        sys.stderr.write(f"Boundary scenario failed: {res_boundary.stderr}\n")
        sys.exit(1)
    boundary_data = json.loads(res_boundary.stdout)
    assert boundary_data["decision"] == "CHUNK_AFTER_COMPLETION_REJECTED"
    assert boundary_data["rejection_verified"] is True
    print("✓ Boundary rejection scenario passed.")

    # 4. Refactoring equivalence check
    res_equiv = run_cmd([sys.executable, EXAMPLE_PY, "--refactor-check"])
    if res_equiv.returncode != 0:
        sys.stderr.write(f"Equivalence check failed: {res_equiv.stderr}\n")
        sys.exit(1)
    equiv_data = json.loads(res_equiv.stdout)
    assert equiv_data["all_equivalent"] is True
    print("✓ Refactoring equivalence check passed.")

    # 5. Canonical check
    res_check = run_cmd([sys.executable, EXAMPLE_PY, "--check"])
    if res_check.returncode != 0:
        sys.stderr.write(f"Canonical check failed: {res_check.stderr}\n")
        sys.exit(1)
    check_data = json.loads(res_check.stdout)
    assert check_data["all_passed"] is True
    print("✓ Canonical check passed.")

    # 6. Tamper check (MUST exit non-zero)
    res_tamper = run_cmd([sys.executable, EXAMPLE_PY, "--tamper"])
    if res_tamper.returncode == 0:
        sys.stderr.write("Tamper check unexpectedly succeeded with exit code 0!\n")
        sys.exit(1)
    tamper_err = json.loads(res_tamper.stderr)
    assert tamper_err["status"] == "expected_tamper_failure"
    assert tamper_err["error_type"] == "DecisionMismatchError"
    print("✓ Deliberate tamper test verified: non-zero exit on assertion mismatch.")

    # 7. Unittest discovery
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
        f.write("# R40-T006 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T006.\n\n")
        f.write("## 1. Normal Scenario\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Error Recovery Scenario\n```json\n" + json.dumps(error_data, indent=2) + "\n```\n\n")
        f.write("## 3. Boundary Rejection Scenario\n```json\n" + json.dumps(boundary_data, indent=2) + "\n```\n\n")
        f.write("## 4. Refactoring Equivalence Proof\n```json\n" + json.dumps(equiv_data, indent=2) + "\n```\n\n")
        f.write("## 5. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 6. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
