#!/usr/bin/env python3
"""Verification check runner for R40-T024.

Runs all normal, boundary, missing-information, state trace, full checker,
deliberate tamper failure, and unit test scenarios in fresh subprocesses.
Validates assertions and generates work/R40-T024/results.md.
A check strictly exits non-zero if any assertion fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R40-T024")
LAB_DIR = os.path.join(REPO_ROOT, "06-text-generation-apps", "applied-labs", "r40-t024")
EXAMPLE_PY = os.path.join(LAB_DIR, "example.py")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Runs command in fresh process with output captured."""
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> int:
    results_markdown_lines: List[str] = [
        "# R40-T024 — Verification Results",
        "",
        "This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T024.",
        "Focus: Record the intermediate state after each step and test the invariant linking that state to the final output.",
        "",
        "---",
        "",
    ]

    # -------------------------------------------------------------------------
    # 1. Normal Scenario (gpt-5-mini Reasoning Pipeline)
    # -------------------------------------------------------------------------
    print("Running Check 1: Normal scenario (gpt-5-mini reasoning pipeline)...")
    cmd1 = [sys.executable, EXAMPLE_PY, "--scenario", "normal"]
    res1 = run_cmd(cmd1)
    assert res1.returncode == 0, f"Check 1 failed: exit {res1.returncode}, stderr: {res1.stderr}"
    data1 = json.loads(res1.stdout)
    assert data1["decision"] == "EXECUTE_REASONING_PIPELINE", f"Wrong decision: {data1['decision']}"
    assert data1["total_tokens_consumed"] == 350, f"Expected 350 tokens, got {data1['total_tokens_consumed']}"
    assert data1["token_budget"] == 1200
    assert data1["invariants_summary"]["all_invariants_hold"] is True
    assert "garlic" not in data1["final_text"].lower(), "Garlic leaked into final output!"

    results_markdown_lines.extend([
        "## 1. Normal Scenario (Microsoft Foundry reasoning model `gpt-5-mini`)",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario normal",
        "```",
        "",
        "Expected Decision: `EXECUTE_REASONING_PIPELINE`",
        "",
        "Actual Output:",
        "```json",
        res1.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res1.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Model parameters follow Lesson 06 (no temperature on reasoning model, secrets isolated, multi-step chaining within token budget, allergy filter respected). All 4 formal invariants hold.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 2. Boundary Scenario (Llama-3.3-70B-Instruct at temperature=1.0 & budget saturation)
    # -------------------------------------------------------------------------
    print("Running Check 2: Boundary scenario (Llama-3.3-70B-Instruct at temperature=1.0)...")
    cmd2 = [sys.executable, EXAMPLE_PY, "--scenario", "boundary"]
    res2 = run_cmd(cmd2)
    assert res2.returncode == 0, f"Check 2 failed: exit {res2.returncode}, stderr: {res2.stderr}"
    data2 = json.loads(res2.stdout)
    assert data2["decision"] == "EXECUTE_SAMPLING_BOUNDARY_PIPELINE", f"Wrong decision: {data2['decision']}"
    assert data2["total_tokens_consumed"] == 150, f"Expected 150 tokens, got {data2['total_tokens_consumed']}"
    assert data2["token_budget"] == 150
    assert data2["invariants_summary"]["all_invariants_hold"] is True
    assert "sugar" not in data2["final_text"].lower(), "Sugar leaked into final output!"

    results_markdown_lines.extend([
        "## 2. Boundary Scenario (Open Sampling Model `Llama-3.3-70B-Instruct` at Temperature Boundary)",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario boundary",
        "```",
        "",
        "Expected Decision: `EXECUTE_SAMPLING_BOUNDARY_PIPELINE`",
        "",
        "Actual Output:",
        "```json",
        res2.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res2.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Sampling model operates at maximum allowable temperature boundary (1.0). Primary generation reaches exact token capacity (150/150 tokens = 100%), safely bypassing secondary context chaining to avoid token truncation/overflow. All 4 formal invariants hold.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 3. Missing Information Scenario (Unconfigured secrets, missing facts, invalid params)
    # -------------------------------------------------------------------------
    print("Running Check 3: Missing information scenario (unconfigured credentials & prompt facts)...")
    cmd3 = [sys.executable, EXAMPLE_PY, "--scenario", "missing"]
    res3 = run_cmd(cmd3)
    assert res3.returncode == 0, f"Check 3 failed: exit {res3.returncode}, stderr: {res3.stderr}"
    data3 = json.loads(res3.stdout)
    assert data3["decision"] == "HALT_MISSING_PREREQUISITES", f"Wrong decision: {data3['decision']}"
    assert data3["total_tokens_consumed"] == 0, f"Expected 0 tokens consumed on halt, got {data3['total_tokens_consumed']}"
    assert data3["final_text"] is None, "Final text must be None on halt!"
    assert len(data3["diagnostic_envelope"]["missing_fields"]) > 0
    assert len(data3["diagnostic_envelope"]["incompatible_params"]) > 0
    assert data3["invariants_summary"]["all_invariants_hold"] is True

    results_markdown_lines.extend([
        "## 3. Missing Information Scenario (Unconfigured Secrets & Missing Facts)",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario missing",
        "```",
        "",
        "Expected Decision: `HALT_MISSING_PREREQUISITES`",
        "",
        "Actual Output:",
        "```json",
        res3.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res3.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Essential prerequisites are missing or incompatible (`AZURE_OPENAI_API_KEY`, prompt ingredients, and illegal `temperature` on reasoning model). The pipeline safely halts at Step 1, producing 0 tokens and no output.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 4. Full Published Decision Table Checker
    # -------------------------------------------------------------------------
    print("Running Check 4: Full published decision table checker...")
    cmd4 = [sys.executable, EXAMPLE_PY, "--check"]
    res4 = run_cmd(cmd4)
    assert res4.returncode == 0, f"Check 4 failed: exit {res4.returncode}, stderr: {res4.stderr}"
    data4 = json.loads(res4.stdout)
    assert data4["all_passed"] is True
    assert data4["total_scenarios"] == 3
    assert data4["passed_scenarios"] == 3
    assert data4["failed_scenarios"] == 0

    results_markdown_lines.extend([
        "## 4. Full Decision Table Checker",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --check",
        "```",
        "",
        "Actual Output:",
        "```json",
        res4.stdout.strip(),
        "```",
        "",
        f"Exit code: `{res4.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 3 canonical scenarios pass table matching, educational rationale validation, and invariant checks.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 5. Intermediate State Trace Inspection (--trace)
    # -------------------------------------------------------------------------
    print("Running Check 5: Intermediate state trace inspection...")
    cmd5 = [sys.executable, EXAMPLE_PY, "--scenario", "normal", "--trace"]
    res5 = run_cmd(cmd5)
    assert res5.returncode == 0, f"Check 5 failed: exit {res5.returncode}, stderr: {res5.stderr}"
    data5 = json.loads(res5.stdout)
    assert "state_trace" in data5
    assert len(data5["state_trace"]) == 5
    for idx, s in enumerate(data5["state_trace"], start=1):
        assert s["step_index"] == idx
        assert s["status"] == "SUCCESS"

    results_markdown_lines.extend([
        "## 5. Intermediate State Trace Inspection (--trace)",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario normal --trace",
        "```",
        "",
        "Actual Output (Truncated State Trace Summary):",
        "```json",
        json.dumps({
            "scenario_id": data5["scenario_id"],
            "decision": data5["decision"],
            "total_tokens_consumed": data5["total_tokens_consumed"],
            "state_trace_summary": [
                {
                    "step_index": s["step_index"],
                    "step_name": s["step_name"],
                    "status": s["status"],
                    "step_tokens_generated": s["step_tokens_generated"],
                    "cumulative_tokens": s["cumulative_tokens"],
                }
                for s in data5["state_trace"]
            ],
            "invariants_summary": data5["invariants_summary"],
        }, indent=2),
        "```",
        "",
        f"Exit code: `{res5.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — Intermediate states sequentially recorded across all 5 discrete pipeline stages with monotonic token accumulation and invariant verification.",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 6. Deliberate Tamper Failure Verification
    # -------------------------------------------------------------------------
    print("Running Check 6: Deliberate tamper failure verification...")
    cmd6 = [sys.executable, EXAMPLE_PY, "--deliberate-tamper", "SCENARIO_NORMAL"]
    res6 = run_cmd(cmd6)
    assert res6.returncode == 1, f"Check 6 failed: expected returncode 1, got {res6.returncode}"
    assert "DecisionMismatchError caught" in res6.stderr, f"Missing DecisionMismatchError in stderr: {res6.stderr}"

    results_markdown_lines.extend([
        "## 6. Deliberate Tamper Failure Verification",
        "",
        "Command:",
        "```bash",
        "python3 06-text-generation-apps/applied-labs/r40-t024/example.py --deliberate-tamper SCENARIO_NORMAL",
        "```",
        "",
        "Actual Stderr:",
        "```text",
        res6.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res6.returncode}` (Expected non-zero: `1`)",
        "",
        "**Result:** PASS — Deliberately changing a decision in the published table triggers `DecisionMismatchError` and immediately exits non-zero (exit code 1).",
        "",
        "---",
        "",
    ])

    # -------------------------------------------------------------------------
    # 7. Automated Unit Test Suite Discovery
    # -------------------------------------------------------------------------
    print("Running Check 7: Automated unit test suite...")
    cmd7 = [sys.executable, "-m", "unittest", "discover", "-s", LAB_DIR, "-p", "test_*.py", "-v"]
    res7 = run_cmd(cmd7)
    assert res7.returncode == 0, f"Check 7 failed: exit {res7.returncode}, stderr: {res7.stderr}"
    assert "Ran 28 tests" in res7.stderr or "Ran 28 tests" in res7.stdout, "Expected 28 tests!"

    results_markdown_lines.extend([
        "## 7. Automated Unit Test Suite Discovery",
        "",
        "Command:",
        "```bash",
        "python3 -m unittest discover -s 06-text-generation-apps/applied-labs/r40-t024 -p \"test_*.py\" -v",
        "```",
        "",
        "Actual Output (Stderr Summary):",
        "```text",
        res7.stderr.strip(),
        "```",
        "",
        f"Exit code: `{res7.returncode}` (Expected: `0`)",
        "",
        "**Result:** PASS — All 28 automated tests passed in a fresh process, testing state tracing, individual invariant violations, scenario rationales, tamper detection, and subprocess execution.",
        "",
        "---",
        "",
        "## 8. Summary of Contribution & Invariant Verification",
        "",
        "| Scenario | Model Family | Decision | State Trace Steps | Tokens Consumed | All Invariants Hold? |",
        "|---|---|---|---|---|---|",
        "| `SCENARIO_NORMAL` | Reasoning (`gpt-5-mini`) | `EXECUTE_REASONING_PIPELINE` | 5 | 350 / 1200 | **YES** |",
        "| `SCENARIO_BOUNDARY` | Sampling (`Llama-3.3-70B`) | `EXECUTE_SAMPLING_BOUNDARY_PIPELINE` | 5 | 150 / 150 | **YES** |",
        "| `SCENARIO_MISSING_INFO` | Reasoning (`gpt-5-mini`) | `HALT_MISSING_PREREQUISITES` | 5 (1 Halted, 4 Skipped) | 0 / None | **YES** |",
        "",
        "All checks passed successfully. Verification complete.",
    ])

    results_md_path = os.path.join(WORK_DIR, "results.md")
    with open(results_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results_markdown_lines) + "\n")
    print(f"Results successfully written to {results_md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
