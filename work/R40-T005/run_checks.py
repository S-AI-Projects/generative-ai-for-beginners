#!/usr/bin/env python3
"""Verification check runner for R40-T005.

Runs normal, missing command, string arguments scenarios,
canonical check, tamper mode, and automated unittest discovery.
Writes work/R40-T005/results.md. Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T005")
LAB_DIR = os.path.join(REPO_ROOT, "14-the-generative-ai-application-lifecycle", "applied-labs", "r40-t005")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T005 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "CONFIG_VALID_REDACTED_SUMMARY"
    assert normal_data["all_redacted"] is True
    assert normal_data["process_launched"] is False
    print("✓ Normal scenario passed.")

    # 2. Missing command scenario
    res_missing = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "missing_cmd"])
    if res_missing.returncode != 0:
        sys.stderr.write(f"Missing cmd scenario failed: {res_missing.stderr}\n")
        sys.exit(1)
    missing_data = json.loads(res_missing.stdout)
    assert missing_data["decision"] == "MISSING_COMMAND_REJECTED"
    assert missing_data["validation_failed"] is True
    print("✓ Missing command scenario passed.")

    # 3. String arguments scenario
    res_string_args = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "string_args"])
    if res_string_args.returncode != 0:
        sys.stderr.write(f"String args scenario failed: {res_string_args.stderr}\n")
        sys.exit(1)
    string_args_data = json.loads(res_string_args.stdout)
    assert string_args_data["decision"] == "STRING_ARGS_REJECTED"
    assert string_args_data["validation_failed"] is True
    print("✓ String arguments scenario passed.")

    # 4. Canonical check
    res_check = run_cmd([sys.executable, EXAMPLE_PY, "--check"])
    if res_check.returncode != 0:
        sys.stderr.write(f"Canonical check failed: {res_check.stderr}\n")
        sys.exit(1)
    check_data = json.loads(res_check.stdout)
    assert check_data["all_passed"] is True
    print("✓ Canonical check passed.")

    # 5. Tamper check (MUST exit non-zero)
    res_tamper = run_cmd([sys.executable, EXAMPLE_PY, "--tamper"])
    if res_tamper.returncode == 0:
        sys.stderr.write("Tamper check unexpectedly succeeded with exit code 0!\n")
        sys.exit(1)
    tamper_err = json.loads(res_tamper.stderr)
    assert tamper_err["status"] == "expected_tamper_failure"
    assert tamper_err["error_type"] == "DecisionMismatchError"
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
        f.write("# R40-T005 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T005.\n\n")
        f.write("## 1. Normal Scenario (Valid Config with Redacted Output)\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Missing Command Failure Scenario\n```json\n" + json.dumps(missing_data, indent=2) + "\n```\n\n")
        f.write("## 3. String Arguments Failure Scenario\n```json\n" + json.dumps(string_args_data, indent=2) + "\n```\n\n")
        f.write("## 4. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 5. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
