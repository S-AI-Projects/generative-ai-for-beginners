#!/usr/bin/env python3
"""Verification check runner for R40-T008.

Runs normal, negative pixel, overflow pixel, pipeline recovery scenarios,
canonical check, tamper mode, and automated unittest discovery.
Writes work/R40-T008/results.md. Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T008")
LAB_DIR = os.path.join(REPO_ROOT, "09-building-image-applications", "applied-labs", "r40-t008")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T008 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "NORMALIZATION_SUCCESS_SHAPE_PRESERVED"
    assert normal_data["output_shape"] == [1, 2, 2]
    assert normal_data["zero_mapped_to_zero"] is True
    assert normal_data["max_mapped_to_one"] is True
    print("✓ Normal scenario passed.")

    # 2. Negative pixel scenario
    res_negative = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "negative"])
    if res_negative.returncode != 0:
        sys.stderr.write(f"Negative scenario failed: {res_negative.stderr}\n")
        sys.exit(1)
    negative_data = json.loads(res_negative.stdout)
    assert negative_data["decision"] == "NEGATIVE_PIXEL_REJECTED"
    assert negative_data["failed_as_expected"] is True
    print("✓ Negative pixel scenario passed.")

    # 3. Overflow pixel scenario
    res_overflow = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "overflow"])
    if res_overflow.returncode != 0:
        sys.stderr.write(f"Overflow scenario failed: {res_overflow.stderr}\n")
        sys.exit(1)
    overflow_data = json.loads(res_overflow.stdout)
    assert overflow_data["decision"] == "OVERFLOW_PIXEL_REJECTED"
    assert overflow_data["failed_as_expected"] is True
    print("✓ Overflow pixel scenario passed.")

    # 4. Pipeline recovery scenario
    res_recovery = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "recovery"])
    if res_recovery.returncode != 0:
        sys.stderr.write(f"Recovery scenario failed: {res_recovery.stderr}\n")
        sys.exit(1)
    recovery_data = json.loads(res_recovery.stdout)
    assert recovery_data["decision"] == "FAILURE_DOCUMENTED_AND_RECOVERED"
    assert recovery_data["recovery_verified"] is True
    print("✓ Pipeline recovery scenario passed.")

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
        f.write("# R40-T008 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T008.\n\n")
        f.write("## 1. Normal Scenario (Shape Preserved, 0->0, 255->1)\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Negative Pixel Failure Scenario\n```json\n" + json.dumps(negative_data, indent=2) + "\n```\n\n")
        f.write("## 3. Overflow Pixel Failure Scenario\n```json\n" + json.dumps(overflow_data, indent=2) + "\n```\n\n")
        f.write("## 4. Pipeline Failure and Recovery Demonstration\n```json\n" + json.dumps(recovery_data, indent=2) + "\n```\n\n")
        f.write("## 5. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 6. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
