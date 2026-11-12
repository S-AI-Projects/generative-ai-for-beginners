import unittest

from example import search


class TestSearch(unittest.TestCase):

    def test_red_returns_two_equal_matches(self):
        results = search("red")

        self.assertEqual(
            results,
            [
                {"id": 1, "score": 1},
                {"id": 2, "score": 1}
            ]
        )

    def test_unmatched_query_returns_empty_list(self):
        self.assertEqual(search("orange"), [])

    def test_minimum_score_filters_results(self):
        self.assertEqual(search("red", min_score=2), [])

    def test_blue_is_omitted_by_default(self):
        results = search("red")

        result_ids = [result["id"] for result in results]

        self.assertNotIn(3, result_ids)

    def test_multiple_matching_words(self):
        results = search("red apple")

        self.assertEqual(
            results,
            [
                {"id": 1, "score": 2},
                {"id": 2, "score": 1}
            ]
        )

    def test_empty_query_raises_error(self):
        with self.assertRaises(ValueError):
            search("")

    def test_negative_minimum_score_raises_error(self):
        with self.assertRaises(ValueError):
            search("red", min_score=-1)


if __name__ == "__main__":
    unittest.main()
