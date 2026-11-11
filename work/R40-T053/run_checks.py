"""Verification harness for R40-T053 (Lesson 19 whitespace-token prompt budget).

Runs normal, boundary, and failure CLI scenarios in fresh subprocesses,
verifies unittest discovery reports a nonzero test count and passes, confirms
a deliberate wrong result fails with AssertionError and non-zero exit code,
and writes inputs, expected vs actual results, and tool versions to
work/R40-T053/check-results.json.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = (
    REPO_ROOT / "19-slm" / "applied-labs" / "r40-t053" / "example.py"
)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_equal(label: str, expected: Any, actual: Any) -> None:
    if expected != actual:
        raise AssertionError(
            f"{label} mismatch:\n  expected={expected!r}\n  actual={actual!r}"
        )


def main() -> int:
    git_ver = _run(["git", "--version"]).stdout.strip()
    tool_versions = {
        "python": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git": git_ver,
        "unittest": "stdlib",
    }

    scenarios = [
        {
            "name": "normal_budget_3_truncates_one",
            "category": "normal",
            "args": ["--prompt", "one two three four", "--budget", "3"],
            "expected_returncode": 0,
            "expected_summary": {
                "retained_tokens": ["one", "two", "three"],
                "removed_tokens": ["four"],
                "removed_count": 1,
                "truncated": True,
                "matches_independent": True,
            },
        },
        {
            "name": "boundary_exact_fit",
            "category": "boundary",
            "args": ["--prompt", "one two three", "--budget", "3"],
            "expected_returncode": 0,
            "expected_summary": {
                "retained_tokens": ["one", "two", "three"],
                "removed_tokens": [],
                "removed_count": 0,
                "truncated": False,
                "matches_independent": True,
            },
        },
        {
            "name": "boundary_empty_input",
            "category": "boundary",
            "args": ["--prompt", "", "--budget", "3"],
            "expected_returncode": 0,
            "expected_summary": {
                "retained_tokens": [],
                "removed_tokens": [],
                "removed_count": 0,
                "truncated": False,
                "matches_independent": True,
            },
        },
        {
            "name": "boundary_zero_budget",
            "category": "boundary",
            "args": ["--prompt", "one two", "--budget", "0"],
            "expected_returncode": 0,
            "expected_summary": {
                "retained_tokens": [],
                "removed_tokens": ["one", "two"],
                "removed_count": 2,
                "truncated": True,
                "matches_independent": True,
            },
        },
        {
            "name": "failure_negative_budget_rejected",
            "category": "failure",
            "args": ["--prompt", "one two", "--budget", "-1"],
            "expected_returncode": 2,
            "expected_stderr_substring": "budget must be >= 0",
        },
    ]

    recorded_scenarios: list[dict[str, Any]] = []
    for scenario in scenarios:
        cmd = [sys.executable, str(EXAMPLE_PATH), *scenario["args"]]
        proc = _run(cmd)
        _assert_equal(
            f"{scenario['name']} returncode",
            scenario["expected_returncode"],
            proc.returncode,
        )

        record: dict[str, Any] = {
            "name": scenario["name"],
            "category": scenario["category"],
            "command": cmd,
            "expected_returncode": scenario["expected_returncode"],
            "actual_returncode": proc.returncode,
        }

        if proc.returncode == 0:
            payload = json.loads(proc.stdout)
            direct = payload["direct_result"]
            expected = scenario["expected_summary"]
            _assert_equal(
                f"{scenario['name']} retained_tokens",
                expected["retained_tokens"],
                direct["retained_tokens"],
            )
            _assert_equal(
                f"{scenario['name']} removed_tokens",
                expected["removed_tokens"],
                direct["removed_tokens"],
            )
            _assert_equal(
                f"{scenario['name']} removed_count",
                expected["removed_count"],
                direct["removed_count"],
            )
            _assert_equal(
                f"{scenario['name']} truncated",
                expected["truncated"],
                direct["truncated"],
            )
            _assert_equal(
                f"{scenario['name']} matches_independent",
                expected["matches_independent"],
                payload["matches_independent"],
            )
            record["expected"] = expected
            record["actual"] = payload
        else:
            expected_sub = scenario["expected_stderr_substring"]
            if expected_sub not in proc.stderr:
                raise AssertionError(
                    f"{scenario['name']} missing {expected_sub!r} in stderr: {proc.stderr!r}"
                )
            record["expected"] = {"stderr_contains": expected_sub}
            record["actual"] = {"stderr": proc.stderr.strip()}

        recorded_scenarios.append(record)

    # Full comparison table invocation.
    table_cmd = [sys.executable, str(EXAMPLE_PATH)]
    table_proc = _run(table_cmd)
    _assert_equal("comparison table returncode", 0, table_proc.returncode)
    table_payload = json.loads(table_proc.stdout)
    for row in table_payload["comparisons"]:
        _assert_equal(f"comparison {row['case']} independent", True, row["matches_independent"])
        _assert_equal(f"comparison {row['case']} expected table", True, row["matches_expected_table"])
    _assert_equal(
        "comparison invalid negative budget rejected",
        True,
        table_payload["invalid_negative_budget"]["rejected"],
    )

    # Run unittest discover in a fresh process.
    unittest_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "19-slm/applied-labs/r40-t053",
        "-p",
        "test_*.py",
        "-v",
    ]
    ut_proc = _run(unittest_cmd)
    _assert_equal("unittest discover returncode", 0, ut_proc.returncode)
    ut_output = ut_proc.stdout + ut_proc.stderr
    match = re.search(r"Ran (\d+) tests?", ut_output)
    if not match or int(match.group(1)) <= 0:
        raise AssertionError(f"Expected nonzero test count in unittest output:\n{ut_output}")
    test_count = int(match.group(1))

    # Deliberate wrong-result check: verify unittest exits non-zero on AssertionError.
    deliberate_code = (
        "import sys, unittest; "
        "sys.path.insert(0, '19-slm/applied-labs/r40-t053'); "
        "import test_example; "
        "test_example.check_prompt_budget = lambda prompt, budget: {"
        "'simulation': True, "
        "'tokenizer_note': test_example.TOKENIZER_APPROXIMATION_NOTE, "
        "'prompt': prompt, 'budget': budget, 'total_tokens': 4, "
        "'retained_tokens': ['one', 'two', 'three', 'four'], 'retained_count': 4, "
        "'removed_tokens': [], 'removed_count': 0, 'truncated': False}; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestWhitespaceBudgetPreflight.test_normal_budget_3_retains_three_and_removes_one'); "
        "res = unittest.TextTestRunner(verbosity=2).run(suite); "
        "sys.exit(0 if res.wasSuccessful() else 1)"
    )
    delib_proc = _run([sys.executable, "-c", deliberate_code])
    delib_output = (delib_proc.stdout + delib_proc.stderr).strip()
    if delib_proc.returncode == 0 or "AssertionError" not in delib_output:
        raise AssertionError(
            f"Deliberate wrong result check did not fail with AssertionError:\n{delib_output}"
        )

    report = {
        "tool_versions": tool_versions,
        "scenarios": recorded_scenarios,
        "comparison_table_invocation": {
            "command": table_cmd,
            "expected_returncode": 0,
            "actual_returncode": table_proc.returncode,
            "actual": table_payload,
        },
        "unittest_discover": {
            "command": unittest_cmd,
            "expected_returncode": 0,
            "actual_returncode": ut_proc.returncode,
            "test_count": test_count,
            "output": ut_output.strip(),
        },
        "deliberate_wrong_result_check": {
            "expected_returncode_nonzero": True,
            "actual_returncode": delib_proc.returncode,
            "output": delib_output,
        },
    }

    (WORK_DIR / "check-results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"All checks passed ({len(recorded_scenarios)} scenarios + comparison table, "
        f"{test_count} unit tests, deliberate failure exit={delib_proc.returncode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
