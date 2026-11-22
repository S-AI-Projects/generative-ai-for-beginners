
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from example import count_parameters


class ParameterAccountingTests(unittest.TestCase):

    def test_normal_parameter_counts(self):
        result = count_parameters(
            {"encoder.weight": 100, "head.weight": 20},
            "encoder"
        )
        self.assertEqual(result["total"], 120)
        self.assertEqual(result["frozen"], 100)
        self.assertEqual(result["trainable"], 20)

    def test_state_trace_matches_final_result(self):
        result = count_parameters(
            {"encoder.weight": 100, "head.weight": 20},
            "encoder"
        )
        trace = result["trace"]

        self.assertEqual(trace[0]["total"], result["total"])
        self.assertEqual(trace[1]["frozen"], result["frozen"])
        self.assertEqual(trace[2]["trainable"], result["trainable"])
        self.assertEqual(
            result["total"],
            result["frozen"] + result["trainable"]
        )

    def test_boundary_counts(self):
        result = count_parameters(
            {"encoder.weight": 1, "head.weight": 1},
            "encoder"
        )
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["frozen"], 1)
        self.assertEqual(result["trainable"], 1)

    def test_unmatched_prefix_is_reported(self):
        result = count_parameters(
            {"encoder.weight": 100, "head.weight": 20},
            "missing_layer"
        )
        self.assertTrue(result["unmatched_prefix"])
        self.assertEqual(result["matched_names"], [])
        self.assertEqual(result["trainable"], 120)

    def test_wrong_expected_result_fails(self):
        result = count_parameters(
            {"encoder.weight": 100, "head.weight": 20},
            "encoder"
        )
        with self.assertRaises(AssertionError):
            self.assertEqual(result["trainable"], 21)

    def test_empty_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            count_parameters({}, "encoder")

    def test_invalid_parameter_count_is_rejected(self):
        with self.assertRaises(ValueError):
            count_parameters({"encoder.weight": 0}, "encoder")

    def test_empty_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            count_parameters({"encoder.weight": 100}, "")

    def test_normal_scenario_in_fresh_process(self):
        script = Path(__file__).with_name("example.py")
        result = subprocess.run(
            [sys.executable, str(script), "--scenario", "normal"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["total"], 120)

    def test_boundary_scenario_in_fresh_process(self):
        script = Path(__file__).with_name("example.py")
        result = subprocess.run(
            [sys.executable, str(script), "--scenario", "boundary"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["trainable"], 1)

    def test_failure_scenario_in_fresh_process(self):
        script = Path(__file__).with_name("example.py")
        result = subprocess.run(
            [sys.executable, str(script), "--scenario", "invalid"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

