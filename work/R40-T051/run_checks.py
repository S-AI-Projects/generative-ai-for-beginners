"""Verification harness for R40-T051 (Lesson 21 synthetic model selection).

Runs normal, boundary, failure, unittest discovery, and deliberate-wrong-result
checks in fresh subprocesses, exits non-zero if any assertion fails, and writes
inputs, expected vs actual results, and tool versions to work/R40-T051/.
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
EXAMPLE_PATH = REPO_ROOT / "21-meta" / "applied-labs" / "r40-t051" / "example.py"
TEST_DIR = REPO_ROOT / "21-meta" / "applied-labs" / "r40-t051"


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
            "name": "normal_default_fixture",
            "category": "normal",
            "args": [],
            "expected_returncode": 0,
            "expected_eligible": ["Fixture A"],
            "expected_excluded": [
                {
                    "name": "Fixture B",
                    "reasons": ["min_ram_gb 8 exceeds ram_budget_gb 6"],
                }
            ],
        },
        {
            "name": "boundary_exact_fixture_a",
            "category": "boundary",
            "args": ["--ram-budget", "4", "--context", "2048"],
            "expected_returncode": 0,
            "expected_eligible": ["Fixture A"],
            "expected_excluded": [
                {
                    "name": "Fixture B",
                    "reasons": ["min_ram_gb 8 exceeds ram_budget_gb 4"],
                }
            ],
        },
        {
            "name": "boundary_exact_both",
            "category": "boundary",
            "args": ["--ram-budget", "8", "--context", "2048"],
            "expected_returncode": 0,
            "expected_eligible": ["Fixture A", "Fixture B"],
            "expected_excluded": [],
        },
        {
            "name": "boundary_context_exceeds_a",
            "category": "boundary",
            "args": ["--ram-budget", "8", "--context", "2049"],
            "expected_returncode": 0,
            "expected_eligible": ["Fixture B"],
            "expected_excluded": [
                {
                    "name": "Fixture A",
                    "reasons": [
                        "max_context_tokens 2048 is below requested_context_tokens 2049"
                    ],
                }
            ],
        },
        {
            "name": "failure_both_constraints_excluded",
            "category": "failure",
            "args": ["--ram-budget", "2", "--context", "5000"],
            "expected_returncode": 0,
            "expected_eligible": [],
            "expected_excluded": [
                {
                    "name": "Fixture A",
                    "reasons": [
                        "min_ram_gb 4 exceeds ram_budget_gb 2",
                        "max_context_tokens 2048 is below requested_context_tokens 5000",
                    ],
                },
                {
                    "name": "Fixture B",
                    "reasons": [
                        "min_ram_gb 8 exceeds ram_budget_gb 2",
                        "max_context_tokens 4096 is below requested_context_tokens 5000",
                    ],
                },
            ],
        },
        {
            "name": "failure_invalid_negative_ram_budget",
            "category": "failure",
            "args": ["--ram-budget", "-1", "--context", "1024"],
            "expected_returncode": 2,
            "expected_stderr_substring": "ram_budget_gb must be >= 0",
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
            actual_eligible = [item["name"] for item in payload["eligible"]]
            actual_excluded = [
                {"name": item["name"], "reasons": item["reasons"]}
                for item in payload["excluded"]
            ]
            _assert_equal(
                f"{scenario['name']} eligible",
                scenario["expected_eligible"],
                actual_eligible,
            )
            _assert_equal(
                f"{scenario['name']} excluded",
                scenario["expected_excluded"],
                actual_excluded,
            )
            record["expected"] = {
                "eligible": scenario["expected_eligible"],
                "excluded": scenario["expected_excluded"],
            }
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

    # Run unittest discover in a fresh process.
    unittest_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "21-meta/applied-labs/r40-t051",
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

    # Deliberate wrong-result check: verify unittest exits non-zero when a result is wrong.
    deliberate_code = (
        "import sys, unittest; "
        "sys.path.insert(0, '21-meta/applied-labs/r40-t051'); "
        "import test_example; "
        "test_example.select_eligible_models = ("
        "lambda manifest, ram_budget_gb, requested_context_tokens: {"
        "'simulation': True, 'ram_budget_gb': ram_budget_gb, "
        "'requested_context_tokens': requested_context_tokens, "
        "'eligible': [{'name': 'Fixture B', 'min_ram_gb': 8, 'max_context_tokens': 4096}], "
        "'excluded': []}); "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestSyntheticModelSelection.test_normal_fixture_admits_only_fixture_a'); "
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
    print(f"All checks passed ({len(recorded_scenarios)} scenarios, {test_count} unit tests, deliberate failure exit={delib_proc.returncode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
