import unittest

from europa_eval.data import load_suite, validate_suite


class DataTests(unittest.TestCase):
    def test_bundled_suite_is_parallel_and_valid(self):
        metadata, items = load_suite()

        self.assertEqual(validate_suite(metadata=metadata, items=items), [])
        self.assertEqual(metadata["version"], "0.1.0")
        self.assertEqual(len(items), 432)
        self.assertEqual(len(metadata["languages"]), 36)
        self.assertEqual(len(metadata["template_ids"]), 12)
        self.assertEqual(len({item.domain for item in items}), 5)
        self.assertEqual(len({item.task_type for item in items}), 6)
        self.assertEqual(len({item.pair_id for item in items if item.pair_id}), 36)
        for language in metadata["languages"]:
            language_items = [item for item in items if item.language == language]
            self.assertEqual(len(language_items), 12)
            self.assertEqual(
                {item.template_id for item in language_items}, set(metadata["template_ids"])
            )

    def test_every_item_has_multilingual_provenance(self):
        _, items = load_suite()

        self.assertTrue(all(item.source.url.startswith("https://") for item in items))
        self.assertTrue(all(item.source.license for item in items))
        self.assertTrue(all(item.language and item.script and item.template_id for item in items))
        counts = {
            state: len([item for item in items if item.review_status == state])
            for state in {item.review_status for item in items}
        }
        self.assertEqual(counts, {"source_native": 12, "machine_translated": 420})


if __name__ == "__main__":
    unittest.main()
