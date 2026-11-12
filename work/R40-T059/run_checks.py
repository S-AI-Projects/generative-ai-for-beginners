"""Verification harness for R40-T059 (Lesson 01 startup scenarios, checker & recovery)."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "01-introduction-to-genai" / "applied-labs" / "r40-t059"
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
    mode_specs = [
        ("normal", ["--mode", "normal"], 0),
        ("boundary", ["--mode", "boundary"], 0),
        ("missing_info", ["--mode", "missing_info"], 0),
        ("recovery", ["--mode", "recovery"], 0),
        ("tamper", ["--mode", "tamper"], 1),
        ("all", ["--mode", "all"], 0),
    ]

    for name, cli_args, expected_code in mode_specs:
        proc = _run_cli(cli_args)
        assert proc.returncode == expected_code, (
            f"Mode '{name}' exited with {proc.returncode}, expected {expected_code}: {proc.stderr}"
        )
        payload = json.loads(proc.stdout)
        cli_scenarios.append(
            {
                "name": name,
                "command": [sys.executable, str(EXAMPLE_PATH.relative_to(REPO_ROOT)), *cli_args],
                "expected_returncode": expected_code,
                "actual_returncode": proc.returncode,
                "actual_output": payload,
            }
        )

    assert cli_scenarios[0]["actual_output"]["results"][0]["actual_decision"] == "serve_tutor_first_draft"
    assert cli_scenarios[1]["actual_output"]["results"][0]["actual_decision"] == "shorten_or_split_prompt"
    assert cli_scenarios[2]["actual_output"]["results"][0]["actual_decision"] == "halt_and_explain_missing_data"
    assert cli_scenarios[3]["actual_output"]["final_status"] == "recovered_valid_ok"
    assert cli_scenarios[3]["actual_output"]["recovered_count"] == 1
    assert cli_scenarios[4]["actual_output"]["all_passed"] is False
    assert len(cli_scenarios[4]["actual_output"]["mismatches"]) == 1

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
    assert "Ran 4 tests" in combined_unit_output, combined_unit_output
    assert combined_unit_output.endswith("OK"), combined_unit_output

    deliberate_fail_code = (
        "import sys, unittest; "
        "sys.path.insert(0, '01-introduction-to-genai/applied-labs/r40-t059'); "
        "import test_example; "
        "orig = test_example.WORKED_SCENARIOS['normal']['expected_decision']; "
        "test_example.WORKED_SCENARIOS['normal']['expected_decision'] = 'shorten_or_split_prompt'; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestStartupDecisionAndRecovery.test_three_worked_scenarios_match_decision_table'); "
        "res = unittest.TextTestRunner(verbosity=2).run(suite); "
        "test_example.WORKED_SCENARIOS['normal']['expected_decision'] = orig; "
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
        "task_id": "R40-T059",
        "tool_versions": tool_versions,
        "cli_scenarios": cli_scenarios,
        "unittest_discover": {
            "command": unit_cmd,
            "expected_returncode": 0,
            "actual_returncode": unit_proc.returncode,
            "test_count": 4,
            "output": combined_unit_output,
        },
        "deliberate_wrong_result_check": {
            "expected_returncode_nonzero": True,
            "actual_returncode": deliberate_proc.returncode,
            "output": deliberate_output,
        },
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("All checks passed (6 CLI modes, 4 unit tests, deliberate failure exit=1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
