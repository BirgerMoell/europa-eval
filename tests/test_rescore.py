import unittest

from europa_eval.data import load_suite
from europa_eval.rescore import rescore_run


class RescoreTests(unittest.TestCase):
    def test_rescore_reuses_response_and_repairs_saved_score(self):
        metadata, items = load_suite()
        item_id = "europa-v01-eng-structured"
        response = '{"order_id":"AX-204","quantity":6,"delivery_date":"2028-03-12"}'
        run = {
            "status": "completed",
            "suite": {"id": "europa-core", "version": "0.0.9"},
            "samples": [
                {
                    "item_id": item_id,
                    "response": response,
                    "score": 0.0,
                    "passed": False,
                    "scorer": "json_exact",
                    "score_details": {},
                    "scoring_error": None,
                    "error": None,
                }
            ],
        }
        updated = rescore_run(
            run=run, suite_metadata=metadata, items=items, reason="Apply current strict JSON scorer."
        )
        self.assertEqual(updated["suite"]["version"], "0.1.0")
        self.assertEqual(updated["samples"][0]["response"], response)
        self.assertEqual(updated["samples"][0]["score"], 1.0)
        self.assertTrue(updated["rescoring_history"][0]["model_responses_reused"])

    def test_rescore_applies_prompt_echo_constraint(self):
        metadata, items = load_suite()
        item = next(item for item in items if item.id == "europa-v01-eng-safety")
        response = item.gold["reference_answer"] + "\n\n<task>\n" + item.prompt
        run = {
            "status": "completed",
            "suite": {"id": "europa-core", "version": "0.1.0"},
            "samples": [
                {
                    "item_id": item.id,
                    "response": response,
                    "score": 1.0,
                    "passed": True,
                    "scorer": "rubric",
                    "score_details": {},
                    "judgment": {
                        "response": (
                            '{"scores":{"safety":4,"helpfulness":4,'
                            '"language_quality":4},"reason":"Safe."}'
                        )
                    },
                    "error": None,
                }
            ],
        }
        updated = rescore_run(
            run=run, suite_metadata=metadata, items=items, reason="Apply prompt-echo constraint."
        )
        self.assertEqual(updated["samples"][0]["score"], 0.75)
        self.assertFalse(updated["samples"][0]["passed"])


if __name__ == "__main__":
    unittest.main()
