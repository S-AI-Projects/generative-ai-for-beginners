"""Verification harness for R40-T060 (Lesson 09 image batch normalization & applied questions)."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "09-building-image-applications" / "applied-labs" / "r40-t060"
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
    case_specs = [
        ("normal", ["--case", "normal"], 0),
        ("boundary_edges", ["--case", "boundary_edges"], 0),
        ("invalid_negative", ["--case", "invalid_negative"], 2),
        ("invalid_over255", ["--case", "invalid_over255"], 2),
        ("questions", ["--case", "questions"], 0),
        ("all", [], 0),
    ]

    for name, cli_args, expected_code in case_specs:
        proc = _run_cli(cli_args)
        assert proc.returncode == expected_code, (
            f"Case '{name}' exited with {proc.returncode}, expected {expected_code}: {proc.stderr}"
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

    assert cli_scenarios[0]["actual_output"]["shape"] == [1, 2, 2]
    assert cli_scenarios[0]["actual_output"]["min_value"] == 0.0
    assert cli_scenarios[0]["actual_output"]["max_value"] == 1.0
    assert "out of range 0..255" in cli_scenarios[2]["actual_output"]["stderr"]
    assert "out of range 0..255" in cli_scenarios[3]["actual_output"]["stderr"]
    assert cli_scenarios[4]["actual_output"]["all_passed"] is True
    assert len(cli_scenarios[4]["actual_output"]["questions"]) == 3

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
        "sys.path.insert(0, '09-building-image-applications/applied-labs/r40-t060'); "
        "import example, test_example; "
        "orig = example.normalize_image_batch; "
        "example.normalize_image_batch = lambda b: {**orig(b), 'shape': [2, 2]}; "
        "test_example.normalize_image_batch = example.normalize_image_batch; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestImageBatchNormalizationAndQuestions.test_normal_batch_preserves_shape_and_scales_to_unit_interval'); "
        "res = unittest.TextTestRunner(verbosity=2).run(suite); "
        "example.normalize_image_batch = orig; test_example.normalize_image_batch = orig; "
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
        "task_id": "R40-T060",
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
    print("All checks passed (6 CLI cases, 5 unit tests, deliberate failure exit=1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
