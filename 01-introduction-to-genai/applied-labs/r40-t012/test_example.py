import unittest

from example import (
    SCENARIOS,
    check_all,
    check_published_decision,
    decide,
    run_scenario,
)


class EducationalStartupTests(unittest.TestCase):

    def test_normal_scenario(self):
        self.assertEqual(run_scenario("normal")["decision"], "ready")

    def test_boundary_scenario(self):
        self.assertEqual(run_scenario("boundary")["decision"], "minimum_ready")

    def test_missing_information(self):
        self.assertEqual(run_scenario("missing")["decision"], "cannot_determine")

    def test_invalid_blank_field(self):
        self.assertEqual(run_scenario("invalid")["decision"], "invalid")

    def test_all_published_decisions(self):
        self.assertTrue(check_all())

    def test_checker_rejects_wrong_decision(self):
        with self.assertRaises(AssertionError):
            check_published_decision("normal", "minimum_ready")

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            run_scenario("unknown")

    def test_missing_fields(self):
        with self.assertRaises(ValueError):
            decide({"topic": "Maths"})

    def test_non_text_value(self):
        facts = dict(SCENARIOS["normal"]["input_facts"])
        facts["topic"] = 123
        with self.assertRaises(ValueError):
            decide(facts)


if __name__ == "__main__":
    unittest.main()
