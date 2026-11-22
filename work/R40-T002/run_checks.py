#!/usr/bin/env python3
"""Verification check runner for R40-T002.

Runs normal, boundary zero-match, boundary tie, invalid case,
tamper mode, and automated unittest discovery in fresh subprocesses.
Writes work/R40-T002/results.md. Exits non-zero if any assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T002")
LAB_DIR = os.path.join(REPO_ROOT, "20-mistral", "applied-labs", "r40-t002")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T002 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "RANK_A_BEFORE_B"
    assert normal_data["doc_ids"] == ["A", "B"]
    assert normal_data["scores"] == [2, 1]
    print("✓ Normal scenario passed.")

    # 2. Boundary zero-match
    res_zero = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "zero_match"])
    if res_zero.returncode != 0:
        sys.stderr.write(f"Zero match scenario failed: {res_zero.stderr}\n")
        sys.exit(1)
    zero_data = json.loads(res_zero.stdout)
    assert zero_data["decision"] == "NO_MATCH_EMPTY_RESULT"
    assert len(zero_data["results"]) == 0
    print("✓ Boundary zero-match scenario passed.")

    # 3. Boundary tie
    res_tie = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "tie"])
    if res_tie.returncode != 0:
        sys.stderr.write(f"Tie scenario failed: {res_tie.stderr}\n")
        sys.exit(1)
    tie_data = json.loads(res_tie.stdout)
    assert tie_data["decision"] == "TIE_BROKEN_A_BEFORE_B"
    assert tie_data["doc_ids"] == ["A", "B"]
    assert tie_data["scores"] == [1, 1]
    print("✓ Boundary tie scenario passed.")

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
        f.write("# R40-T002 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T002.\n\n")
        f.write("## 1. Normal Scenario ('red apple' -> A before B)\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Zero-Match Boundary Scenario ('ocean' -> [])\n```json\n" + json.dumps(zero_data, indent=2) + "\n```\n\n")
        f.write("## 3. Tie-Breaking Boundary Scenario ('apple' -> A before B)\n```json\n" + json.dumps(tie_data, indent=2) + "\n```\n\n")
        f.write("## 4. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 5. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
