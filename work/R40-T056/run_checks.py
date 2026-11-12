"""Verification harness for R40-T056 (Lesson 14 launch config & secret redaction).

Runs normal, boundary, and failure CLI scenarios in fresh subprocesses,
verifies unittest discovery reports a nonzero test count and passes, confirms
a deliberate wrong result fails with AssertionError and non-zero exit code,
and writes inputs, expected vs actual results, and tool versions to
work/R40-T056/check-results.json.
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
    REPO_ROOT
    / "14-the-generative-ai-application-lifecycle"
    / "applied-labs"
    / "r40-t056"
    / "example.py"
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
            "name": "normal_valid_redacted",
            "category": "normal",
            "args": ["--case", "valid"],
            "expected_returncode": 0,
            "expected_summary": {
                "launched": False,
                "equivalent": True,
                "command": "python3",
                "args": ["-m", "http.server", "8080"],
                "env_keys": ["APP_ENV", "API_KEY"],
                "redacted_env": {"APP_ENV": "<REDACTED>", "API_KEY": "<REDACTED>"},
            },
            "forbidden_substrings": ["synthetic-secret-value", "local-sim"],
        },
        {
            "name": "boundary_empty_args_and_env",
            "category": "boundary",
            "args": ["--case", "boundary_empty_args_and_env"],
            "expected_returncode": 0,
            "expected_summary": {
                "launched": False,
                "equivalent": True,
                "command": "uvicorn",
                "args": [],
                "env_keys": [],
                "redacted_env": {},
            },
            "forbidden_substrings": [],
        },
        {
            "name": "failure_missing_command",
            "category": "failure",
            "args": ["--case", "invalid_missing_command"],
            "expected_returncode": 2,
            "expected_stderr_substring": "Missing or empty 'command'",
        },
        {
            "name": "failure_single_string_args",
            "category": "failure",
            "args": ["--case", "invalid_string_args"],
            "expected_returncode": 2,
            "expected_stderr_substring": "not a single string",
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
            report_obj = payload["report"]
            expected = scenario["expected_summary"]
            _assert_equal(f"{scenario['name']} equivalent", expected["equivalent"], payload["equivalent"])
            _assert_equal(f"{scenario['name']} launched", expected["launched"], report_obj["launched"])
            _assert_equal(f"{scenario['name']} command", expected["command"], report_obj["command"])
            _assert_equal(f"{scenario['name']} args", expected["args"], report_obj["args"])
            _assert_equal(f"{scenario['name']} env_keys", expected["env_keys"], report_obj["env_keys"])
            _assert_equal(
                f"{scenario['name']} redacted_env",
                expected["redacted_env"],
                report_obj["redacted_env"],
            )
            for secret in scenario["forbidden_substrings"]:
                if secret in proc.stdout:
                    raise AssertionError(f"{scenario['name']} leaked secret {secret!r}")
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

    # Full equivalence suite CLI run.
    all_cmd = [sys.executable, str(EXAMPLE_PATH)]
    all_proc = _run(all_cmd)
    _assert_equal("all equivalence suite returncode", 0, all_proc.returncode)
    all_payload = json.loads(all_proc.stdout)
    _assert_equal("all_equivalent", True, all_payload["all_equivalent"])

    # Run unittest discover in a fresh process.
    unittest_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "14-the-generative-ai-application-lifecycle/applied-labs/r40-t056",
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
        "sys.path.insert(0, '14-the-generative-ai-application-lifecycle/applied-labs/r40-t056'); "
        "import test_example; "
        "test_example.validate_launch_config = lambda cfg: {"
        "'simulation': True, 'launched': False, 'command': cfg['command'], "
        "'args': list(cfg['args']), 'env_keys': list(cfg['env'].keys()), "
        "'redacted_env': dict(cfg['env'])}; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestLaunchConfigValidationAndRedaction.test_valid_config_redacts_secrets_and_never_launches_process'); "
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
        "all_equivalence_invocation": {
            "command": all_cmd,
            "expected_returncode": 0,
            "actual_returncode": all_proc.returncode,
            "actual": all_payload,
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
        f"All checks passed ({len(recorded_scenarios)} scenarios + equivalence suite, "
        f"{test_count} unit tests, deliberate failure exit={delib_proc.returncode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
