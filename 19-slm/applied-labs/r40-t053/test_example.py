"""Unit tests for Lesson 19 whitespace-token prompt-budget example."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from example import (  # noqa: E402
    EXPECTED_FIXTURE_TABLE,
    TOKENIZER_APPROXIMATION_NOTE,
    check_prompt_budget,
    independent_budget_calculation,
    run_comparison_fixtures,
)


class TestWhitespaceBudgetPreflight(unittest.TestCase):
    def test_normal_budget_3_retains_three_and_removes_one(self) -> None:
        result = check_prompt_budget("one two three four", 3)

        self.assertTrue(result["simulation"])
        self.assertEqual(result["tokenizer_note"], TOKENIZER_APPROXIMATION_NOTE)
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_tokens"], ["four"])
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])

    def test_boundary_empty_and_whitespace_only_retain_none(self) -> None:
        for text in ("", "   \t\n "):
            result = check_prompt_budget(text, 3)
            self.assertEqual(result["total_tokens"], 0)
            self.assertEqual(result["retained_tokens"], [])
            self.assertEqual(result["removed_tokens"], [])
            self.assertEqual(result["removed_count"], 0)
            self.assertFalse(result["truncated"])

    def test_boundary_exact_fit_and_zero_budget(self) -> None:
        exact = check_prompt_budget("one two three", 3)
        self.assertEqual(exact["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(exact["removed_count"], 0)
        self.assertFalse(exact["truncated"])

        zero = check_prompt_budget("one two", 0)
        self.assertEqual(zero["retained_tokens"], [])
        self.assertEqual(zero["removed_tokens"], ["one", "two"])
        self.assertEqual(zero["removed_count"], 2)
        self.assertTrue(zero["truncated"])

    def test_comparison_matches_independent_and_expected_table(self) -> None:
        summary = run_comparison_fixtures()
        self.assertEqual(len(summary["comparisons"]), len(EXPECTED_FIXTURE_TABLE))
        for item in summary["comparisons"]:
            self.assertTrue(item["matches_independent"], item["case"])
            self.assertTrue(item["matches_expected_table"], item["case"])
            direct = item["direct_result"]
            independent = item["independent_result"]
            self.assertEqual(
                direct["retained_count"] + direct["removed_count"],
                direct["total_tokens"],
            )
            self.assertEqual(
                independent["retained_count"] + independent["removed_count"],
                independent["total_tokens"],
            )
        self.assertTrue(summary["invalid_negative_budget"]["rejected"])

    def test_failure_negative_and_invalid_inputs_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "budget must be >= 0"):
            check_prompt_budget("one two", -1)
        with self.assertRaisesRegex(ValueError, "budget must be >= 0"):
            independent_budget_calculation("one two", -1)
        with self.assertRaises(ValueError):
            check_prompt_budget("one", True)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            check_prompt_budget(123, 3)  # type: ignore[arg-type]

    def test_fresh_process_cli_normal_and_negative_budget(self) -> None:
        script = LAB_DIR / "example.py"

        ok_proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(ok_proc.stdout)
        self.assertTrue(payload["simulation"])
        self.assertEqual(payload["tokenizer_note"], TOKENIZER_APPROXIMATION_NOTE)
        self.assertTrue(all(c["matches_independent"] for c in payload["comparisons"]))
        self.assertTrue(all(c["matches_expected_table"] for c in payload["comparisons"]))

        direct_proc = subprocess.run(
            [sys.executable, str(script), "--prompt", "one two three four", "--budget", "3"],
            capture_output=True,
            text=True,
            check=True,
        )
        direct_payload = json.loads(direct_proc.stdout)
        self.assertTrue(direct_payload["matches_independent"])
        self.assertEqual(
            direct_payload["direct_result"]["retained_tokens"],
            ["one", "two", "three"],
        )
        self.assertEqual(direct_payload["direct_result"]["removed_count"], 1)

        fail_proc = subprocess.run(
            [sys.executable, str(script), "--prompt", "one two", "--budget", "-1"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(fail_proc.returncode, 0)
        self.assertIn("budget must be >= 0", fail_proc.stderr)


if __name__ == "__main__":
    unittest.main()
