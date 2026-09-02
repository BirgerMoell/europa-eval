import unittest

from europa_eval.data import load_suite
from europa_eval.reporting import summarize


class ReportingTests(unittest.TestCase):
    def test_summary_exposes_language_profile_and_output_diagnostics(self):
        _, items = load_suite()
        english = next(item for item in items if item.id == "europa-v01-eng-reading")
        swedish = next(item for item in items if item.id == "europa-v01-swe-reading")
        repeated = (
            "this is a sufficiently long phrase that repeats exactly in this output now "
            "this is a sufficiently long phrase that repeats exactly in this output now"
        )
        samples = [
            {
                "item_id": english.id,
                "score": 1.0,
                "passed": True,
                "score_details": {},
                "response": repeated,
                "latency_ms": 1,
                "output_tokens": 20,
            },
            {
                "item_id": swedish.id,
                "score": 0.5,
                "passed": False,
                "score_details": {},
                "response": (
                    "You are taking part in an evaluation of Swedish language capability.\n"
                    "<context>\ntext\n<task>\nquestion"
                ),
                "latency_ms": 3,
                "output_tokens": 30,
            },
        ]

        summary = summarize(samples, [english, swedish])
        self.assertEqual(summary["language_profile"]["covered_languages"], 2)
        self.assertEqual(summary["language_profile"]["declared_languages"], 2)
        self.assertAlmostEqual(summary["language_profile"]["macro_language_score"], 0.75)
        self.assertEqual(summary["output_diagnostics"]["prompt_echo_count"], 1)
        self.assertEqual(summary["output_diagnostics"]["repeated_span_count"], 1)
        self.assertEqual(summary["output_diagnostics"]["median_output_tokens"], 25)


if __name__ == "__main__":
    unittest.main()
