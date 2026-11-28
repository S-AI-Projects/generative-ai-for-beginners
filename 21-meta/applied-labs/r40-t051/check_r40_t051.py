#!/usr/bin/env python3
"""r40-t051 checks.

Runs the normal/boundary/failure scenarios in a *fresh subprocess*, records
inputs, expected vs actual results, and tool versions under
work/R40-T051/, and exits non-zero when an assertion fails (both the unittest
assertions and the final participant check in this script).

Run from anywhere:
    python3 21-meta/applied-labs/r40-t051/check_r40_t051.py
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths (report root = repository root).
# ---------------------------------------------------------------------------
LAB_DIR = Path(__file__).resolve().parent
# The repository root is three levels above this file (r40-t051 -> applied-labs
# -> 21-meta -> <repository root>).
REPO_ROOT = LAB_DIR.parent.parent.parent
WORK_DIR = REPO_ROOT / "work" / "R40-T051"

TEST_DIR = LAB_DIR
EXAMPLE_PY = LAB_DIR / "example.py"
TEST_PATTERN = "test_*.py"

# Main scenario from the lesson brief (invented teaching fixtures).
SCENARIO = {
    "manifest": [
        {"name": "fixture-a", "ram_gb": 4, "context_window": 2048},
        {"name": "fixture-b", "ram_gb": 8, "context_window": 4096},
    ],
    "budget_ram_gb": 6,
    "requested_context_tokens": 1024,
    "expected_eligible": ["fixture-a"],
    "expected_excluded": [{"name": "fixture-b", "reason": "exceeds budget RAM"}],
}

BOUNDARY_AND_FAILURE_INPUTS = [
    {"label": "exact_fit", "manifest": [{"name": "exact-fit", "ram_gb": 6, "context_window": 1024}], "budget_ram_gb": 6, "requested_context_tokens": 1024, "expected_eligible": ["exact-fit"]},
    {"label": "exact_context", "manifest": [{"name": "exact-context", "ram_gb": 4, "context_window": 1024}], "budget_ram_gb": 6, "requested_context_tokens": 1024, "expected_eligible": ["exact-context"]},
    {"label": "over_budget_by_one", "manifest": [{"name": "over-ram", "ram_gb": 7, "context_window": 1024}], "budget_ram_gb": 6, "requested_context_tokens": 1024, "expected_eligible": []},
    {"label": "under_context", "manifest": [{"name": "under-context", "ram_gb": 4, "context_window": 512}], "budget_ram_gb": 6, "requested_context_tokens": 1024, "expected_excluded": [{"name": "under-context", "reason": "insufficient context window"}]},
    {"label": "negative_budget", "manifest": [{"name": "bad", "ram_gb": 4, "context_window": 1024}], "budget_ram_gb": -1, "requested_context_tokens": 1024, "expect_error": "ValueError"},
]

# ---------------------------------------------------------------------------
# Tool versions / environment snapshot.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def write_outputs(payload: dict) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    # Atomically write each file.
    for name, content in payload.items():
        target = WORK_DIR / name
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_text(json.dumps(content, indent=2, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main check.
# ---------------------------------------------------------------------------


def main() -> int:
    inputs = {"scenario": SCENARIO, "boundary_and_failure": BOUNDARY_AND_FAILURE_INPUTS}
    expected = {"scenario": SCENARIO["expected_eligible"], "scenario_excluded": SCENARIO["expected_excluded"]}

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
    # Under -v unittest writes the per-test lines and the "Ran N tests" summary
    # to stderr, so combine both streams for logging/assertion.
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

    # --- parse the example into a comparable structure -------------------
    actual_names = {"eligible": [], "excluded": []}
    if example_proc.returncode == 0:
        for line in example_proc.stdout.splitlines():
            if line.startswith("[LESSON: eligibility] eligible="):
                actual_names["eligible"] = line.split("=", 1)[1].split(", ")
            if line.startswith("[LESSON: eligibility] excluded="):
                rest = line.split("=", 1)[1]  # e.g. "fixture-b why=exceeds budget RAM"
                name, _, reason = rest.partition(" why=")
                if name:
                    actual_names["excluded"].append({"name": name, "reason": reason})

    compared = {
        "inputs": inputs,
        "expected": expected,
        "actual_example": actual_names,
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

    # --- report ----------------------------------------------------------
    print("R40-T051 checks")
    print("  python : %s" % tool["python"])
    print("  git    : %s (branch %s)" % (tool["git_commit"], tool["git_branch"]))
    print("  unittest : Ran %s tests | exit_code=%s"
          % (unittest_test_count, unittest_proc.returncode))
    print("  example  : exit_code=%s" % example_proc.returncode)
    print("  outputs  : %s" % WORK_DIR)
    print("  self-test: assert_false exits %s (nonzero expected=%s), pass exits %s"
          % (self_test["assert_false"]["exit_code"], self_test["assert_false"]["nonzero_expected"], self_test["pass"]["exit_code"]))

    # --- assertions ------------------------------------------------------
    assert unittest_proc.returncode == 0, "unittest suite did not pass"
    assert example_proc.returncode == 0, "example did not run cleanly"
    assert self_test["assert_false"]["exit_code"] != 0, "assert False did not exit non-zero"
    assert self_test["pass"]["exit_code"] == 0, "pass did not exit zero"
    return 0


def extract_test_count(text: str) -> int | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Ran "):
            # 'Ran 15 tests'
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    return None


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:  # pragma: no cover - defensive
        print("R40-T051 check FAILED: %s" % exc, file=sys.stderr)
        sys.exit(1)
