"""Verification harness for R40-T058 (Lesson 02 whitespace-token budget & comparison)."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "02-exploring-and-comparing-different-llms" / "applied-labs" / "r40-t058"
EXAMPLE_PATH = LAB_DIR / "example.py"
RESULTS_PATH = Path(__file__).resolve().parent / "check-results.json"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(EXAMPLE_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    tool_versions = {
        "python": sys.version,
        "platform": platform.platform(),
        "unittest_runner": f"{sys.executable} -m unittest",
    }

    cli_scenarios: list[dict[str, Any]] = []
    scenario_specs = [
        ("budget3", ["--case", "budget3"], 0),
        ("empty", ["--case", "empty"], 0),
        ("negative", ["--case", "negative"], 2),
        ("compare", ["--case", "compare"], 0),
        ("all", [], 0),
    ]

    for name, cli_args, expected_code in scenario_specs:
        proc = _run_cli(cli_args)
        assert proc.returncode == expected_code, (
            f"Scenario '{name}' exited with {proc.returncode}, expected {expected_code}: {proc.stderr}"
        )
        output: Any = (
            json.loads(proc.stdout)
            if proc.returncode == 0
            else {"stderr": proc.stderr.strip()}
        )
        cli_scenarios.append(
            {
                "name": name,
                "command": [sys.executable, str(EXAMPLE_PATH.relative_to(REPO_ROOT)), *cli_args],
                "expected_returncode": expected_code,
                "actual_returncode": proc.returncode,
                "actual_output": output,
            }
        )

    assert cli_scenarios[0]["actual_output"]["retained_tokens"] == ["one", "two", "three"]
    assert cli_scenarios[0]["actual_output"]["removed_count"] == 1
    assert cli_scenarios[0]["actual_output"]["truncated"] is True
    assert cli_scenarios[1]["actual_output"]["retained_tokens"] == []
    assert cli_scenarios[1]["actual_output"]["removed_count"] == 0
    assert "non-negative integer" in cli_scenarios[2]["actual_output"]["stderr"]
    assert cli_scenarios[3]["actual_output"]["all_correct"] is True
    assert len(cli_scenarios[3]["actual_output"]["configurations"]) == 3

    unit_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(LAB_DIR.relative_to(REPO_ROOT)),
        "-p",
        "test_*.py",
        "-v",
    ]
    unit_proc = subprocess.run(
        unit_cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    combined_unit_output = (unit_proc.stdout + "\n" + unit_proc.stderr).strip()
    assert unit_proc.returncode == 0, combined_unit_output
    assert "Ran 5 tests" in combined_unit_output, combined_unit_output
    assert combined_unit_output.endswith("OK"), combined_unit_output

    deliberate_fail_code = (
        "import sys, unittest; "
        "sys.path.insert(0, '02-exploring-and-comparing-different-llms/applied-labs/r40-t058'); "
        "import example, test_example; "
        "orig = example.check_prompt_budget; "
        "example.check_prompt_budget = lambda p, b: {**orig(p, b), 'removed_count': 0}; "
        "test_example.check_prompt_budget = example.check_prompt_budget; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestWhitespaceTokenBudget.test_budget_three_truncates_fourth_token_and_labels_approximation'); "
        "res = unittest.TextTestRunner(verbosity=2).run(suite); "
        "example.check_prompt_budget = orig; test_example.check_prompt_budget = orig; "
        "sys.exit(0 if res.wasSuccessful() else 1)"
    )
    deliberate_proc = subprocess.run(
        [sys.executable, "-c", deliberate_fail_code],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    deliberate_output = (deliberate_proc.stdout + "\n" + deliberate_proc.stderr).strip()
    assert deliberate_proc.returncode != 0, (
        "Deliberate wrong-result failure check unexpectedly passed!"
    )
    assert "AssertionError" in deliberate_output, deliberate_output

    summary = {
        "task_id": "R40-T058",
        "tool_versions": tool_versions,
        "cli_scenarios": cli_scenarios,
        "unittest_discover": {
            "command": unit_cmd,
            "expected_returncode": 0,
            "actual_returncode": unit_proc.returncode,
            "test_count": 5,
            "output": combined_unit_output,
        },
        "deliberate_wrong_result_check": {
            "expected_returncode_nonzero": True,
            "actual_returncode": deliberate_proc.returncode,
            "output": deliberate_output,
        },
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("All checks passed (5 CLI scenarios, 5 unit tests, deliberate failure exit=1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
