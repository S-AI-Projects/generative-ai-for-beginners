"""Verification harness for R40-T054 (Lesson 11 trace-to-output invariants).

Runs normal, boundary, and failure CLI scenarios in fresh subprocesses,
verifies unittest discovery reports a nonzero test count and passes, confirms
a deliberate wrong result fails with AssertionError and non-zero exit code,
and writes inputs, expected vs actual results, and tool versions to
work/R40-T054/check-results.json.
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
    / "11-integrating-with-function-calling"
    / "applied-labs"
    / "r40-t054"
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
            "name": "normal_two_chunks_complete",
            "category": "normal",
            "args": ["--scenario", "normal"],
            "expected_returncode": 0,
            "expected_summary": {
                "scenario": "normal_two_chunks_complete",
                "statuses": ["pending", "streaming", "streaming", "complete"],
                "message_id": "msg-001",
                "final_status": "complete",
                "received_text": "Hello world",
                "error_marker": None,
            },
        },
        {
            "name": "boundary_error_preserves_text",
            "category": "boundary",
            "args": ["--scenario", "boundary_error"],
            "expected_returncode": 0,
            "expected_summary": {
                "scenario": "boundary_error_preserves_text",
                "statuses": ["pending", "streaming", "error"],
                "message_id": "msg-002",
                "final_status": "error",
                "received_text": "Partial ",
                "error_marker": "[ERROR: stream interrupted]",
                "display_text": "Partial [ERROR: stream interrupted]",
            },
        },
        {
            "name": "failure_chunk_after_completion_rejected",
            "category": "failure",
            "args": ["--scenario", "late_chunk"],
            "expected_returncode": 0,
            "expected_summary": {
                "scenario": "failure_chunk_after_completion",
                "statuses": ["pending", "streaming", "complete", "complete"],
                "message_id": "msg-003",
                "final_status": "complete",
                "received_text": "Done",
                "rejected": True,
                "last_accepted": False,
            },
        },
        {
            "name": "failure_unknown_cli_scenario_exits_nonzero",
            "category": "failure",
            "args": ["--scenario", "invalid"],
            "expected_returncode": 2,
            "expected_stderr_substring": "invalid choice",
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
            res = payload["results"][0]
            final = res["final_output"]
            statuses = [s["status"] for s in res["intermediate_states"]]
            expected = scenario["expected_summary"]
            _assert_equal(f"{scenario['name']} scenario", expected["scenario"], res["scenario"])
            _assert_equal(f"{scenario['name']} statuses", expected["statuses"], statuses)
            _assert_equal(f"{scenario['name']} message_id", expected["message_id"], final["message_id"])
            _assert_equal(f"{scenario['name']} final_status", expected["final_status"], final["status"])
            _assert_equal(f"{scenario['name']} received_text", expected["received_text"], final["received_text"])
            if "error_marker" in expected:
                _assert_equal(f"{scenario['name']} error_marker", expected["error_marker"], final["error_marker"])
            if "display_text" in expected:
                _assert_equal(f"{scenario['name']} display_text", expected["display_text"], final["display_text"])
            if "rejected" in expected:
                _assert_equal(f"{scenario['name']} rejected", expected["rejected"], res["rejected"])
                _assert_equal(
                    f"{scenario['name']} last_accepted",
                    expected["last_accepted"],
                    res["intermediate_states"][-1]["accepted"],
                )
            _assert_equal(
                f"{scenario['name']} invariants",
                True,
                all(res["invariants"].values()),
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

    # Full default CLI run (all scenarios).
    all_cmd = [sys.executable, str(EXAMPLE_PATH)]
    all_proc = _run(all_cmd)
    _assert_equal("default all scenario returncode", 0, all_proc.returncode)
    all_payload = json.loads(all_proc.stdout)
    _assert_equal("default all scenario count", 3, len(all_payload["results"]))

    # Run unittest discover in a fresh process.
    unittest_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "11-integrating-with-function-calling/applied-labs/r40-t054",
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
        "sys.path.insert(0, '11-integrating-with-function-calling/applied-labs/r40-t054'); "
        "import test_example; "
        "test_example.run_normal_case = lambda: {"
        "'scenario': 'normal_two_chunks_complete', "
        "'intermediate_states': [{'step': 0, 'action': 'init', 'accepted': True, 'chunk': None, "
        "'message_id': 'msg-001', 'status': 'pending', 'received_text': '', 'error_marker': None, 'display_text': '', 'rejection_reason': None}], "
        "'final_output': {'simulation': True, 'message_id': 'msg-001', 'status': 'complete', 'received_text': 'wrong', 'error_marker': None, 'display_text': 'wrong'}, "
        "'invariants': {'stable_message_id': True, 'monotonic_received_text': True, 'terminal_state_immutable': True, 'links_to_final_output': False}}; "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestStreamingTraceInvariants.test_normal_two_chunks_record_intermediate_states_and_invariants'); "
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
        "default_all_invocation": {
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
        f"All checks passed ({len(recorded_scenarios)} scenarios + default all, "
        f"{test_count} unit tests, deliberate failure exit={delib_proc.returncode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
