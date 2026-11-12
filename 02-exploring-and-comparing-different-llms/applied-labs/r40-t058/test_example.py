"""Unit tests for Lesson 02 whitespace-token budget fixture and comparison lab."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = MODULE_DIR / "example.py"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from example import (  # noqa: E402
    TOKENIZER_KIND,
    check_prompt_budget,
    compare_controlled_configs,
)


class TestWhitespaceTokenBudget(unittest.TestCase):
    def test_budget_three_truncates_fourth_token_and_labels_approximation(self) -> None:
        report = check_prompt_budget("one two three four", 3)
        self.assertTrue(report["simulation"])
        self.assertEqual(report["tokenizer_kind"], TOKENIZER_KIND)
        self.assertIn("teaching approximation", report["tokenizer_notice"].lower())
        self.assertIn("not a model's real", report["tokenizer_notice"].lower())
        self.assertEqual(report["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(report["retained_count"], 3)
        self.assertEqual(report["removed_tokens"], ["four"])
        self.assertEqual(report["removed_count"], 1)
        self.assertTrue(report["truncated"])
        self.assertEqual(report["retention_ratio"], 0.75)

    def test_empty_and_whitespace_input_retains_none(self) -> None:
        for empty_prompt in ("", "   \t\n "):
            report = check_prompt_budget(empty_prompt, 3)
            self.assertEqual(report["input_token_count"], 0)
            self.assertEqual(report["retained_tokens"], [])
            self.assertEqual(report["retained_count"], 0)
            self.assertEqual(report["removed_tokens"], [])
            self.assertEqual(report["removed_count"], 0)
            self.assertFalse(report["truncated"])
            self.assertIsNone(report["retention_ratio"])

    def test_negative_or_invalid_budget_and_non_string_prompt_rejected(self) -> None:
        for bad_budget in (-1, -100, True, "3"):
            with self.assertRaises(ValueError):
                check_prompt_budget("one two three four", bad_budget)  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            check_prompt_budget(123, 3)  # type: ignore[arg-type]

    def test_three_controlled_configurations_comparison_and_tradeoff(self) -> None:
        comparison = compare_controlled_configs()
        self.assertTrue(comparison["all_correct"])
        configs = comparison["configurations"]
        self.assertEqual(len(configs), 3)
        self.assertEqual(
            [c["config_id"] for c in configs],
            ["tight_budget_2", "fixture_budget_3", "full_budget_4"],
        )
        self.assertEqual([c["retention_ratio"] for c in configs], [0.5, 0.75, 1.0])
        self.assertEqual([c["removed_count"] for c in configs], [2, 1, 0])
        self.assertIn("makes no claim about real-world model accuracy", comparison["trade_off_summary"])

    def test_fresh_process_cli_normal_boundary_and_failure(self) -> None:
        normal_proc = subprocess.run(
            [sys.executable, str(EXAMPLE_PATH), "--case", "budget3"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(normal_proc.returncode, 0)
        normal_payload = json.loads(normal_proc.stdout)
        self.assertEqual(normal_payload["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(normal_payload["removed_count"], 1)

        empty_proc = subprocess.run(
            [sys.executable, str(EXAMPLE_PATH), "--case", "empty"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(empty_proc.returncode, 0)
        empty_payload = json.loads(empty_proc.stdout)
        self.assertEqual(empty_payload["retained_tokens"], [])
        self.assertFalse(empty_payload["truncated"])

        neg_proc = subprocess.run(
            [sys.executable, str(EXAMPLE_PATH), "--case", "negative"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(neg_proc.returncode, 2)
        self.assertIn("non-negative integer", neg_proc.stderr)


if __name__ == "__main__":
    unittest.main()
