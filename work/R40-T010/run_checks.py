#!/usr/bin/env python3
"""
Verification runner for Task R40-T010.
Executes scenario evaluations, decision table checks, negative tamper checks,
applied question verifications, and unit tests.
Exits non-zero on any failure and writes results.md.
"""

import datetime
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

# Add lab directory to path
LAB_DIR = Path(__file__).resolve().parent.parent.parent / "10-building-low-code-ai-applications" / "applied-labs" / "r40-t010"
sys.path.insert(0, str(LAB_DIR))

import example


def main() -> int:
    results_dir = Path(__file__).resolve().parent
    results_md_path = results_dir / "results.md"
    inputs_json_path = results_dir / "inputs.json"

    print("=== [R40-T010] Starting Comprehensive Verification ===")

    # 1. Load inputs
    with open(inputs_json_path, "r", encoding="utf-8") as f:
        inputs_data = json.load(f)

    # 2. Verify Baseline Scenarios
    print("[1/5] Evaluating Baseline Scenarios...")
    for s_id, s_info in inputs_data["baseline_scenarios"].items():
        facts = example.BASELINE_SCENARIOS[s_id]
        assessment = example.evaluate_scenario(facts)
        expected_decision = s_info["expected_decision"]
        if assessment.decision != expected_decision:
            print(f"FAILED: Scenario {s_id} got {assessment.decision}, expected {expected_decision}")
            return 1
        print(f"  ✓ {s_id}: {assessment.decision} matched.")

    # 3. Verify Decision Table (Clean and Tampered)
    print("[2/5] Verifying Decision Table Checker...")
    clean_check = example.verify_decision_table(tamper=False)
    if not clean_check.is_valid or clean_check.passed_scenarios != clean_check.total_scenarios:
        print(f"FAILED: Clean decision table verification failed: {clean_check.mismatches}")
        return 1
    print(f"  ✓ Clean table verified: {clean_check.passed_scenarios}/{clean_check.total_scenarios} passed.")

    tampered_check = example.verify_decision_table(tamper=True)
    if tampered_check.is_valid or len(tampered_check.mismatches) == 0:
        print("FAILED: Tampered check unexpectedly passed!")
        return 1
    print(f"  ✓ Tampered table properly caught: {tampered_check.mismatches[0]}")

    # 4. Verify CLI Tamper Non-Zero Exit Code
    print("[3/5] Verifying CLI Tamper Failure Detection...")
    cli_proc = subprocess.run(
        [sys.executable, str(LAB_DIR / "example.py"), "--check", "--tamper"],
        capture_output=True,
        text=True,
    )
    if cli_proc.returncode != 1:
        print(f"FAILED: CLI tamper exit code was {cli_proc.returncode}, expected 1")
        return 1
    print(f"  ✓ CLI --check --tamper cleanly exited with return code 1.")

    # 5. Evaluate Applied Questions
    print("[4/5] Evaluating Three Applied Questions...")
    q1 = example.check_question_1_predict_output()
    if not q1.passed or q1.actual != q1.expected:
        print(f"FAILED: Question 1 failed: {q1}")
        return 1
    print(f"  ✓ Q1 (Predict Output): Passed ({q1.actual})")

    q2 = example.check_question_2_diagnose_failure()
    if not q2.passed or q2.actual != q2.expected:
        print(f"FAILED: Question 2 failed: {q2}")
        return 1
    print(f"  ✓ Q2 (Diagnose Failure): Passed ({q2.actual})")

    q3 = example.check_question_3_choose_boundary_policy()
    if not q3.passed or q3.actual != q3.expected:
        print(f"FAILED: Question 3 failed: {q3}")
        return 1
    print(f"  ✓ Q3 (Choose Boundary Policy): Passed ({q3.actual})")

    # 6. Run Unittest Suite
    print("[5/5] Running Unittest Test Suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(LAB_DIR), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    if not test_result.wasSuccessful():
        print(f"FAILED: Unit tests failed (errors={len(test_result.errors)}, failures={len(test_result.failures)})")
        return 1
    if test_result.testsRun < 15:
        print(f"FAILED: Expected at least 15 tests, ran {test_result.testsRun}")
        return 1
    print(f"  ✓ Ran {test_result.testsRun} unit tests successfully.")

    # Write results.md
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results_md_content = f"""# Verification Results: R40-T010

- **Task**: R40-T010 (10 of 10)
- **Student**: Prince Verma (E26B07F1176)
- **Lesson**: 10-building-low-code-ai-applications
- **Branch**: `student/e26b07f1176/R40-T010`
- **Timestamp**: `{now_utc}`
- **Overall Status**: **PASSED (ALL CHECKS SUCCESSFUL)**

---

## 1. Baseline Scenarios Verification

| Scenario ID | Name | Expected Decision | Actual Decision | Status |
| :--- | :--- | :--- | :--- | :--- |
| `S1_NORMAL` | Invoice Processing Flow | `LOW_CODE_POWER_PLATFORM` | `LOW_CODE_POWER_PLATFORM` | **PASS** |
| `S2_BOUNDARY` | Exam Fraud Detection | `CUSTOM_CODE_PRO_DEV` | `CUSTOM_CODE_PRO_DEV` | **PASS** |
| `S3_MISSING_INFO` | Student Advisory Agent | `DEFER_INSUFFICIENT_INFORMATION` | `DEFER_INSUFFICIENT_INFORMATION` | **PASS** |

---

## 2. Decision Table Integrity & Tamper Check

- **Pristine Table Verification**: `is_valid=True`, 3/3 scenarios passed.
- **Tampered Decision Table Check**: `is_valid=False`, caught deliberate alteration.
- **CLI Exit Code Test (`--check --tamper`)**: Exited with code `1` (strict failure confirmation).

---

## 3. Applied Questions Verification

- **Q1: Predict Output (Support Ticket Summarizer)**:
  - *Expected*: `LOW_CODE_POWER_PLATFORM`
  - *Actual*: `LOW_CODE_POWER_PLATFORM`
  - *Status*: **PASS**
  - *Rationale*: Prebuilt "Create Text with GPT" AI Builder prompt template fits requirements; volume (5k/mo) and latency (10s) operate cleanly within standard connector limits.

- **Q2: Diagnose Failure (Incomplete Proposal)**:
  - *Expected*: `MISSING_OPERATIONAL_METRICS`
  - *Actual*: `MISSING_OPERATIONAL_METRICS`
  - *Status*: **PASS**
  - *Rationale*: Missing required operational fields (`compliance_tier`, `latency_sla_ms`, `monthly_volume`) prevents connector throughput and isolation assessment, triggering safe governance deferral.

- **Q3: Choose Boundary Policy (250k Daily Ingestion Surge)**:
  - *Expected*: `POLICY_HYBRID_PRO_CODE_OFFLOAD`
  - *Actual*: `POLICY_HYBRID_PRO_CODE_OFFLOAD`
  - *Status*: **PASS**
  - *Rationale*: Recommended pattern is hybrid extensibility: offload high-volume ingestion to pro-code Azure Functions while retaining Power Apps UI for citizen developer management.

---

## 4. Automated Test Suite Output

- **Test Suite**: `python3 -m unittest discover -s 10-building-low-code-ai-applications/applied-labs/r40-t010 -p "test_*.py"`
- **Total Tests Run**: {test_result.testsRun}
- **Failures**: {len(test_result.failures)}
- **Errors**: {len(test_result.errors)}
- **Result**: ALL {test_result.testsRun} TESTS PASSED

---

## 5. Scope & Hardware Disclaimer

This lab was executed exclusively using Python 3 standard library modules. No external cloud dependencies, live Power Platform tenants, Dataverse environments, paid AI Builder consumption credits, or specialized GPU acceleration were required or accessed.
"""

    with open(results_md_path, "w", encoding="utf-8") as f:
        f.write(results_md_content)

    print(f"=== [R40-T010] All Checks Passed! Generated {results_md_path} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
