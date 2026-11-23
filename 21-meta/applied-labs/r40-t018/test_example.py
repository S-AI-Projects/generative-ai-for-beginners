import unittest

from example import FIXTURE, select_models


class ModelSelectionTests(unittest.TestCase):

    def test_only_model_a_is_eligible(self):
        eligible, excluded = select_models(FIXTURE, 6, 1024)

        self.assertEqual(eligible, ["Model A"])
        self.assertEqual(
            excluded,
            [
                ("Model C", "Missing required RAM or context data"),
                ("Model B", "Insufficient RAM"),
            ],
        )
    def test_model_at_exact_ram_budget_is_eligible(self):
        manifest = [
            {"name": "Boundary Model", "ram": 6, "context": 1024}
        ]

        eligible, excluded = select_models(manifest, 6, 1024)

        self.assertEqual(eligible, ["Boundary Model"])
        self.assertEqual(excluded, [])

    def test_missing_data_is_rejected_without_crashing(self):
        manifest = [
            {"name": "Broken Model", "context": 1024},
            {"name": "Valid Model", "ram": 4, "context": 2048},
        ]

        eligible, excluded = select_models(manifest, 6, 1024)

        self.assertEqual(eligible, ["Valid Model"])
        self.assertEqual(
            excluded,
            [("Broken Model", "Missing required RAM or context data")],
        )

    def test_insufficient_context_is_rejected(self):
        manifest = [
            {"name": "Small Context", "ram": 4, "context": 512}
        ]

        eligible, excluded = select_models(manifest, 6, 1024)

        self.assertEqual(eligible, [])
        self.assertEqual(
            excluded,
            [("Small Context", "Insufficient context")],
        )

    def test_non_integer_data_is_rejected(self):
        manifest = [
            {"name": "Invalid Model", "ram": "four", "context": 2048}
        ]

        eligible, excluded = select_models(manifest, 6, 1024)

        self.assertEqual(eligible, [])
        self.assertEqual(
            excluded,
            [("Invalid Model", "RAM and context must be integers")],
        )


if __name__ == "__main__":
    unittest.main()
