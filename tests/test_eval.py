"""Exercise repeated real MCP calls through the collector, without a model."""
import unittest
import run_eval
import scenarios


class EvidenceCollectionTests(unittest.TestCase):
    def test_repeated_empty_queries_survive_log_capture(self):
        for attempt in (1, 2):
            record = run_eval.run_once(scenarios.SCENARIOS[1], attempt)
            self.assertIsNone(record["crashed"])
            self.assertIn("No listings matched", record["error"])
            self.assertEqual(record["model_calls"], 0)
            self.assertIn("search_listings (via MCP)", record["trace"])

    def test_original_search_cases_rotate_by_attempt(self):
        for attempt, expected in [(1, "lst_002"), (2, "lst_003")]:
            record = run_eval.run_once(scenarios.SCENARIOS[4], attempt)
            self.assertIsNone(record["crashed"])
            self.assertEqual(record["expected_id"], expected)
            self.assertIn(expected, [x["id"] for x in record["output"]])
