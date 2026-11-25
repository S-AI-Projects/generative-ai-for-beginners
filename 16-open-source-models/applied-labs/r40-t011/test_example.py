import unittest

from example import (
    SCENARIOS,
    check_all,
    check_published_decision,
    decide,
    run_scenario,
)


class OpenModelChecklistTests(unittest.TestCase):

    def test_normal_scenario(self):
        result = run_scenario("normal")
        self.assertEqual(result["decision"], "meets_checklist")
        self.assertEqual(
            result["decision"], result["expected_decision"]
        )

    def test_boundary_scenario(self):
        result = run_scenario("boundary")
        self.assertEqual(result["decision"], "does_not_meet_checklist")
        self.assertEqual(
            result["decision"], result["expected_decision"]
        )

    def test_missing_information_scenario(self):
        result = run_scenario("missing")
        self.assertEqual(result["decision"], "cannot_determine")
        self.assertEqual(
            result["decision"], result["expected_decision"]
        )

    def test_all_published_decisions(self):
        self.assertTrue(check_all())

    def test_checker_rejects_deliberately_wrong_decision(self):
        with self.assertRaises(AssertionError):
            check_published_decision("normal", "does_not_meet_checklist")

    def test_unknown_information_is_not_false(self):
        facts = dict(SCENARIOS["missing"]["input_facts"])
        facts["training_metrics"] = None
        self.assertEqual(decide(facts), "cannot_determine")

    def test_incomplete_input_is_rejected(self):
        with self.assertRaises(ValueError):
            decide({"training_datasets": True})


if __name__ == "__main__":
    unittest.main()
