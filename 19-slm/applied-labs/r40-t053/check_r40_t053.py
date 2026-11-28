#!/usr/bin/env python3
"""r40-t053 checks.

Runs the normal/boundary/failure scenarios in a *fresh subprocess*, records
inputs, expected vs actual results, and tool versions under
work/R40-T053/, and exits non-zero when an assertion fails (both the
unittest assertions and the final participant check in this script).

Run from anywhere:
    python3 19-slm/applied-labs/r40-t053/check_r40_t053.py
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

LAB_DIR = Path(__file__).resolve().parent
# repository root is three levels above this file (r40-t053 -> applied-labs
# -> 19-slm -> <repository root>).
REPO_ROOT = LAB_DIR.parent.parent.parent
WORK_DIR = REPO_ROOT / "work" / "R40-T053"

TEST_DIR = LAB_DIR
EXAMPLE_PY = LAB_DIR / "example.py"
TEST_PATTERN = "test_*.py"

SCENARIO = {
    "description": "budget 3 on 'one two three four' retains [one, two, three], removed=1",
    "text": "one two three four",
    "budget": 3,
    "expected_retained": ["one", "two", "three"],
    "expected_removed_count": 1,
}

BOUNDARY_AND_FAILURE_INPUTS = [
    {"label": "empty_input", "text": "", "budget": 5, "expected_retained": [], "expected_removed_count": 0},
    {"label": "budget_equal_to_tokens", "text": "one two three", "budget": 3, "expected_retained": ["one", "two", "three"], "expected_removed_count": 0},
    {"label": "budget_greater_than_tokens", "text": "one two", "budget": 10, "expected_retained": ["one", "two"], "expected_removed_count": 0},
    {"label": "budget_zero", "text": "one two", "budget": 0, "expected_retained": [], "expected_removed_count": 2},
    {"label": "negative_budget", "text": "one two", "budget": -1, "expect_error": "ValueError"},
]


def tool_versions() -> dict:
    versions: dict[str, Optional[str]] = {
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "git_commit": None,
        "git_branch": None,
    }
    try:
        git = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        versions["git_commit"] = git.stdout.strip()
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        versions["git_branch"] = branch.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        versions["git_commit"] = None
        versions["git_branch"] = None
    return versions


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def write_outputs(payload: dict) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in payload.items():
        target = WORK_DIR / name
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_text(json.dumps(content, indent=2, sort_keys=False), encoding="utf-8")


def extract_test_count(text: str) -> Optional[int]:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Ran "):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    return None


def main() -> int:
    inputs = {"scenario": SCENARIO, "boundary_and_failure": BOUNDARY_AND_FAILURE_INPUTS}
    expected = {
        "scenario_retained": SCENARIO["expected_retained"],
        "scenario_removed_count": SCENARIO["expected_removed_count"],
    }

    # --- actual: run the example (fresh process) -----------------------
    example_proc = run([sys.executable, str(EXAMPLE_PY)])
    example_actual = {
        "command": [sys.executable, str(EXAMPLE_PY)],
        "exit_code": example_proc.returncode,
        "stdout": example_proc.stdout,
        "stderr": example_proc.stderr,
    }

    # --- actual: run the unittest suite in a fresh process ---------------
    unittest_proc = run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(TEST_DIR), "-p", TEST_PATTERN, "-v"],
        cwd=str(REPO_ROOT),
    )
    unittest_combined = unittest_proc.stdout + unittest_proc.stderr
    unittest_actual = {
        "command": [sys.executable, "-m", "unittest", "discover", "-s", str(TEST_DIR), "-p", TEST_PATTERN, "-v"],
        "cwd": str(REPO_ROOT),
        "exit_code": unittest_proc.returncode,
        "stdout": unittest_proc.stdout,
        "stderr": unittest_proc.stderr,
        "combined": unittest_combined,
    }
    unittest_test_count = extract_test_count(unittest_combined)

    compared = {
        "inputs": inputs,
        "expected": expected,
        "example_exit_code": example_proc.returncode,
        "unittest_exit_code": unittest_proc.returncode,
        "unittest_test_count": unittest_test_count,
        "unittest_combined": unittest_combined,
    }

    # --- negative self-test: assert the check itself exits non-zero -----
    self_test = {}
    for label, code in [
        ("assert_false", "assert False, 'deliberate failure'"),
        ("pass", "pass"),
    ]:
        proc = run([sys.executable, "-c", code])
        self_test[label] = {"exit_code": proc.returncode, "nonzero_expected": True}

    tool = tool_versions()

    payload = {
        "inputs.json": inputs,
        "expected.json": expected,
        "tool_versions.json": tool,
        "actual_example_output.txt": example_actual["stdout"] + (example_actual["stderr"] if example_actual["stderr"] else ""),
        "actual_unittest_output.txt": unittest_actual["stdout"] + (unittest_actual["stderr"] if unittest_actual["stderr"] else ""),
        "compared_actual_vs_expected.json": compared,
        "check_self_test.json": self_test,
        "check_exit_code.txt": str(unittest_actual["exit_code"]),
    }
    write_outputs(payload)

    print("R40-T053 checks")
    print("  python : %s" % tool["python"])
    print("  git    : %s (branch %s)" % (tool["git_commit"], tool["git_branch"]))
    print("  unittest : Ran %s tests | exit_code=%s" % (unittest_test_count, unittest_proc.returncode))
    print("  example  : exit_code=%s" % example_proc.returncode)
    print("  outputs  : %s" % WORK_DIR)
    print(
        "  self-test: assert_false exits %s (nonzero expected=%s), pass exits %s"
        % (self_test["assert_false"]["exit_code"], self_test["assert_false"]["nonzero_expected"], self_test["pass"]["exit_code"])
    )

    assert unittest_proc.returncode == 0, "unittest suite did not pass"
    assert unittest_test_count is not None and unittest_test_count > 0, "unittest reported zero tests"
    assert example_proc.returncode == 0, "example did not run cleanly"
    assert self_test["assert_false"]["exit_code"] != 0, "assert False did not exit non-zero"
    assert self_test["pass"]["exit_code"] == 0, "pass did not exit zero"
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:  # pragma: no cover - defensive
        print("R40-T053 check FAILED: %s" % exc, file=sys.stderr)
        sys.exit(1)
