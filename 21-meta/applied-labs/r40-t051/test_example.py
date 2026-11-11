"""Unit tests for the Lesson 21 synthetic model-selection example."""

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
    DEFAULT_RAM_BUDGET_GB,
    DEFAULT_REQUESTED_CONTEXT_TOKENS,
    SYNTHETIC_MANIFEST,
    select_eligible_models,
)


class TestSyntheticModelSelection(unittest.TestCase):
    def test_normal_fixture_admits_only_fixture_a(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=DEFAULT_RAM_BUDGET_GB,
            requested_context_tokens=DEFAULT_REQUESTED_CONTEXT_TOKENS,
        )

        self.assertTrue(result["simulation"])
        self.assertEqual(result["ram_budget_gb"], 6)
        self.assertEqual(result["requested_context_tokens"], 1024)
        self.assertEqual([item["name"] for item in result["eligible"]], ["Fixture A"])
        self.assertEqual([item["name"] for item in result["excluded"]], ["Fixture B"])
        self.assertEqual(
            result["excluded"][0]["reasons"],
            ["min_ram_gb 8 exceeds ram_budget_gb 6"],
        )

    def test_boundary_exact_match_for_fixture_a(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=4,
            requested_context_tokens=2048,
        )

        self.assertEqual([item["name"] for item in result["eligible"]], ["Fixture A"])
        self.assertEqual([item["name"] for item in result["excluded"]], ["Fixture B"])

    def test_boundary_exact_match_for_both_fixtures(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=8,
            requested_context_tokens=2048,
        )

        self.assertEqual(
            [item["name"] for item in result["eligible"]],
            ["Fixture A", "Fixture B"],
        )
        self.assertEqual(result["excluded"], [])

    def test_boundary_exact_match_for_fixture_b_excludes_a_on_context(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=8,
            requested_context_tokens=4096,
        )

        self.assertEqual([item["name"] for item in result["eligible"]], ["Fixture B"])
        self.assertEqual([item["name"] for item in result["excluded"]], ["Fixture A"])
        self.assertEqual(
            result["excluded"][0]["reasons"],
            ["max_context_tokens 2048 is below requested_context_tokens 4096"],
        )

    def test_boundary_context_exceeds_fixture_a_admits_only_b(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=8,
            requested_context_tokens=2049,
        )

        self.assertEqual([item["name"] for item in result["eligible"]], ["Fixture B"])
        self.assertEqual([item["name"] for item in result["excluded"]], ["Fixture A"])
        self.assertEqual(
            result["excluded"][0]["reasons"],
            ["max_context_tokens 2048 is below requested_context_tokens 2049"],
        )

    def test_failure_both_ram_and_context_reported(self) -> None:
        result = select_eligible_models(
            SYNTHETIC_MANIFEST,
            ram_budget_gb=2,
            requested_context_tokens=5000,
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(len(result["excluded"]), 2)
        self.assertEqual(
            result["excluded"][0]["reasons"],
            [
                "min_ram_gb 4 exceeds ram_budget_gb 2",
                "max_context_tokens 2048 is below requested_context_tokens 5000",
            ],
        )
        self.assertEqual(
            result["excluded"][1]["reasons"],
            [
                "min_ram_gb 8 exceeds ram_budget_gb 2",
                "max_context_tokens 4096 is below requested_context_tokens 5000",
            ],
        )

    def test_failure_invalid_inputs_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=-1, requested_context_tokens=1024)

        with self.assertRaises(ValueError):
            select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=6, requested_context_tokens=0)

        with self.assertRaises(ValueError):
            select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=True, requested_context_tokens=1024)

        with self.assertRaises(ValueError):
            select_eligible_models([{"name": "Bad", "min_ram_gb": -2, "max_context_tokens": 1024}], 6, 1024)

    def test_fresh_process_cli_normal_and_failure_exit(self) -> None:
        script = LAB_DIR / "example.py"

        ok_proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(ok_proc.stdout)
        self.assertTrue(payload["simulation"])
        self.assertEqual([item["name"] for item in payload["eligible"]], ["Fixture A"])
        self.assertEqual([item["name"] for item in payload["excluded"]], ["Fixture B"])

        fail_proc = subprocess.run(
            [sys.executable, str(script), "--ram-budget", "-1"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(fail_proc.returncode, 0)
        self.assertIn("ram_budget_gb must be >= 0", fail_proc.stderr)


if __name__ == "__main__":
    unittest.main()
