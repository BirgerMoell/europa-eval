from dataclasses import replace
import unittest

from europa_eval.data import load_suite
from europa_eval.scoring import build_judge_prompt, score_item, score_judgment


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, items = load_suite()
        cls.items = {item.id: item for item in items}

    def test_choice_enforces_single_letter_and_partial_credit(self):
        item = self.items["europa-v01-eng-reading"]
        self.assertTrue(score_item(item=item, response="B").passed)
        verbose = score_item(item=item, response="B. At ten.")
        self.assertEqual(verbose.value, 0.5)
        self.assertFalse(verbose.passed)
        self.assertTrue(verbose.details["malformed"])

    def test_choice_does_not_credit_incidental_later_letter(self):
        item = self.items["europa-v01-eng-reading"]
        score = score_item(item=item, response="After checking, the answer is B.")
        self.assertEqual(score.value, 0.0)
        self.assertFalse(score.details["partial_credit"])

    def test_numeric_accepts_decimal_comma_and_grades_relative_error(self):
        item = replace(
            self.items["europa-v01-eng-surface-metric"],
            gold={"value": 10.0},
        )
        exact = score_item(item=item, response="10,0")
        partial = score_item(item=item, response="8")
        self.assertTrue(exact.passed)
        self.assertAlmostEqual(partial.value, 0.8)
        self.assertAlmostEqual(partial.details["relative_error_percent"], 20.0)

    def test_surface_metric_exposes_precomputed_derivation(self):
        item = self.items["europa-v01-eng-surface-metric"]
        score = score_item(item=item, response=str(item.gold["value"]))
        self.assertTrue(score.passed)
        self.assertEqual(score.details["gold_calculation"]["word_count"], 5)
        self.assertEqual(score.details["gold_calculation"]["letter_count"], 34)
        self.assertEqual(score.details["gold_calculation"]["value"], 6.8)

    def test_strict_json_rejects_code_fence_and_wrong_key_order(self):
        item = self.items["europa-v01-eng-structured"]
        payload = '{"order_id":"AX-204","quantity":6,"delivery_date":"2028-03-12"}'
        self.assertTrue(score_item(item=item, response=payload).passed)
        fenced = score_item(item=item, response=f"```json\n{payload}\n```")
        prose = score_item(item=item, response=f"Here is the result: {payload}")
        wrong_order = score_item(
            item=item,
            response='{"quantity":6,"order_id":"AX-204","delivery_date":"2028-03-12"}',
        )
        self.assertFalse(fenced.passed)
        self.assertTrue(fenced.details["malformed"])
        self.assertFalse(prose.passed)
        self.assertFalse(prose.details["format_checks"]["json_only"])
        self.assertFalse(wrong_order.details["format_checks"]["key_order"])

    def test_judge_prompt_is_language_aware_and_judgment_normalizes(self):
        item = self.items["europa-v01-swe-summarization"]
        prompt = build_judge_prompt(item, item.gold["reference_answer"])
        self.assertIn("model response in Swedish", prompt)
        self.assertIn("Return only JSON", prompt)
        judgment = (
            '{"scores":{"fidelity":4,"coverage":3,"concision":4,'
            '"language_quality":4},"reason":"One minor omission."}'
        )
        score = score_judgment(item=item, judgment=judgment)
        self.assertAlmostEqual(score.value, 15 / 16)
        self.assertTrue(score.passed)

    def test_prompt_echo_caps_rubric_score(self):
        item = self.items["europa-v01-eng-safety"]
        judgment = (
            '{"scores":{"safety":4,"helpfulness":4,"language_quality":4},'
            '"reason":"Safe."}'
        )
        response = item.gold["reference_answer"] + "\n\n<task>\n" + item.prompt
        score = score_judgment(item=item, judgment=judgment, response=response)
        self.assertEqual(score.value, 0.75)
        self.assertFalse(score.passed)
        self.assertEqual(score.details["response_constraint_violations"], ["no_prompt_echo"])


if __name__ == "__main__":
    unittest.main()
