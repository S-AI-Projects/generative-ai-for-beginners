#!/usr/bin/env python3
"""Verification check runner for R40-T007.

Runs normal, missing topic, literal braces, unknown key scenarios,
worked explanation regression, canonical check, tamper mode, and unittest discovery.
Writes work/R40-T007/results.md. Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T007")
LAB_DIR = os.path.join(REPO_ROOT, "05-advanced-prompts", "applied-labs", "r40-t007")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")
RESULTS_MD = os.path.join(WORK_DIR, "results.md")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> None:
    print("=== Running R40-T007 Verification Checks ===")

    # 1. Normal scenario
    res_normal = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "normal"])
    if res_normal.returncode != 0:
        sys.stderr.write(f"Normal scenario failed: {res_normal.stderr}\n")
        sys.exit(1)
    normal_data = json.loads(res_normal.stdout)
    assert normal_data["decision"] == "TEMPLATE_RENDERED_SUCCESS"
    assert normal_data["contains_name"] is True
    assert normal_data["contains_topic"] is True
    print("✓ Normal scenario passed.")

    # 2. Missing topic scenario
    res_missing = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "missing_topic"])
    if res_missing.returncode != 0:
        sys.stderr.write(f"Missing topic scenario failed: {res_missing.stderr}\n")
        sys.exit(1)
    missing_data = json.loads(res_missing.stdout)
    assert missing_data["decision"] == "MISSING_TOPIC_REJECTED"
    assert missing_data["missing_variable_caught"] is True
    print("✓ Missing topic scenario passed.")

    # 3. Literal braces scenario
    res_braces = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "braces"])
    if res_braces.returncode != 0:
        sys.stderr.write(f"Braces scenario failed: {res_braces.stderr}\n")
        sys.exit(1)
    braces_data = json.loads(res_braces.stdout)
    assert braces_data["decision"] == "LITERAL_BRACES_PRESERVED"
    assert braces_data["braces_intact"] is True
    print("✓ Literal braces scenario passed.")

    # 4. Unknown key scenario
    res_unknown = run_cmd([sys.executable, EXAMPLE_PY, "--scenario", "unknown"])
    if res_unknown.returncode != 0:
        sys.stderr.write(f"Unknown key scenario failed: {res_unknown.stderr}\n")
        sys.exit(1)
    unknown_data = json.loads(res_unknown.stdout)
    assert unknown_data["decision"] == "UNKNOWN_KEY_REJECTED"
    assert unknown_data["unknown_key_caught"] is True
    print("✓ Unknown key scenario passed.")

    # 5. Worked explanation regression check
    res_explain = run_cmd([sys.executable, EXAMPLE_PY, "--explain"])
    if res_explain.returncode != 0:
        sys.stderr.write(f"Explain failed: {res_explain.stderr}\n")
        sys.exit(1)
    explain_data = json.loads(res_explain.stdout)
    assert explain_data["stage_2_schema_validation"]["status"] == "VALID"
    assert explain_data["stage_3_brace_handling"]["literal_preserved"] is True
    print("✓ Worked explanation regression check passed.")

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
        f.write("# R40-T007 — Verification Results\n\n")
        f.write("This report records inputs, expected vs actual outputs, exit codes, and verification status for Task R40-T007.\n\n")
        f.write("## 1. Normal Scenario\n```json\n" + json.dumps(normal_data, indent=2) + "\n```\n\n")
        f.write("## 2. Missing Topic Scenario\n```json\n" + json.dumps(missing_data, indent=2) + "\n```\n\n")
        f.write("## 3. Literal Braces Boundary Scenario\n```json\n" + json.dumps(braces_data, indent=2) + "\n```\n\n")
        f.write("## 4. Unknown Key Scenario\n```json\n" + json.dumps(unknown_data, indent=2) + "\n```\n\n")
        f.write("## 5. Worked Explanation Regression Output\n```json\n" + json.dumps(explain_data, indent=2) + "\n```\n\n")
        f.write("## 6. Tamper Test Output (Deliberate Non-Zero Exit)\n```json\n" + json.dumps(tamper_err, indent=2) + "\n```\n\n")
        f.write("## 7. Unittest Output\n```\n" + res_test.stderr + "\n```\n")

    print(f"Results successfully recorded in {RESULTS_MD}")


if __name__ == "__main__":
    main()
