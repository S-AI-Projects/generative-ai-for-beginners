"""Verification harness for R40-T055 (Lesson 20 lexical retriever test double).

Runs normal, boundary, and failure CLI scenarios in fresh subprocesses,
verifies unittest discovery reports a nonzero test count and passes, confirms
a deliberate wrong result fails with AssertionError and non-zero exit code,
and writes inputs, expected vs actual results, and tool versions to
work/R40-T055/check-results.json.
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
    REPO_ROOT / "20-mistral" / "applied-labs" / "r40-t055" / "example.py"
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
            "name": "normal_red_apple_ranks_a_before_b",
            "category": "normal",
            "args": ["--query", "red apple"],
            "expected_returncode": 0,
            "expected_summary": {
                "doc_ids": ["A", "B"],
                "matched_count": 2,
                "scores": [2, 1],
            },
        },
        {
            "name": "normal_ocean_no_match",
            "category": "normal",
            "args": ["--query", "ocean"],
            "expected_returncode": 0,
            "expected_summary": {
                "doc_ids": [],
                "matched_count": 0,
                "scores": [],
            },
        },
        {
            "name": "boundary_case_insensitive_tie_break_by_doc_id",
            "category": "boundary",
            "args": ["--query", "  APPLE  "],
            "expected_returncode": 0,
            "expected_summary": {
                "doc_ids": ["A", "B"],
                "matched_count": 2,
                "scores": [1, 1],
            },
        },
        {
            "name": "boundary_empty_query",
            "category": "boundary",
            "args": ["--query", ""],
            "expected_returncode": 0,
            "expected_summary": {
                "doc_ids": [],
                "matched_count": 0,
                "scores": [],
            },
        },
        {
            "name": "failure_unknown_cli_flag_exits_nonzero",
            "category": "failure",
            "args": ["--bad-flag"],
            "expected_returncode": 2,
            "expected_stderr_substring": "unrecognized arguments",
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
            expected = scenario["expected_summary"]
            actual_scores = [item["score"] for item in payload["results"]]
            _assert_equal(f"{scenario['name']} doc_ids", expected["doc_ids"], payload["doc_ids"])
            _assert_equal(
                f"{scenario['name']} matched_count",
                expected["matched_count"],
                payload["matched_count"],
            )
            _assert_equal(f"{scenario['name']} scores", expected["scores"], actual_scores)
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

    # Full default CLI run.
    default_cmd = [sys.executable, str(EXAMPLE_PATH)]
    default_proc = _run(default_cmd)
    _assert_equal("default CLI returncode", 0, default_proc.returncode)
    default_payload = json.loads(default_proc.stdout)
    _assert_equal("default run 0 doc_ids", ["A", "B"], default_payload["runs"][0]["doc_ids"])
    _assert_equal("default run 1 doc_ids", [], default_payload["runs"][1]["doc_ids"])

    # Run unittest discover in a fresh process.
    unittest_cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "20-mistral/applied-labs/r40-t055",
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
        "sys.path.insert(0, '20-mistral/applied-labs/r40-t055'); "
        "import test_example; "
        "test_example.make_lexical_retriever = lambda docs: ("
        "lambda q: [{'doc_id': 'B', 'text': 'green apple', 'score': 1, 'matched_terms': ['apple']}, "
        "{'doc_id': 'A', 'text': 'red apple', 'score': 2, 'matched_terms': ['apple', 'red']}]); "
        "suite = unittest.defaultTestLoader.loadTestsFromName("
        "'test_example.TestLexicalRetrieverTestDouble.test_normal_red_apple_ranks_a_before_b_and_excludes_c'); "
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
        "default_invocation": {
            "command": default_cmd,
            "expected_returncode": 0,
            "actual_returncode": default_proc.returncode,
            "actual": default_payload,
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
        f"All checks passed ({len(recorded_scenarios)} scenarios + default, "
        f"{test_count} unit tests, deliberate failure exit={delib_proc.returncode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
