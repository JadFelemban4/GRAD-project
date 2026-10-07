import unittest
from backend.catalog import metadata


class ArabicContractTests(unittest.TestCase):
    def test_arabic_changes_words_without_changing_scientific_contract(self):
        english = metadata()
        arabic = metadata(locale="ar")
        self.assertEqual(arabic["locale"], "ar")
        self.assertRegex(arabic["tour"][0]["title"], r"[\u0600-\u06ff]")
        for section in ("concepts", "actions", "observations", "tour", "viva", "scenarios"):
            self.assertEqual(len(english[section]), len(arabic[section]))
        for section in ("concepts", "actions", "observations"):
            for original, translated in zip(english[section], arabic[section]):
                self.assertEqual(original["id"], translated["id"])
                self.assertEqual(original["source"], translated["source"])
        for original, translated in zip(english["actions"], arabic["actions"]):
            for key in ("lo", "hi", "slew", "unit"):
                self.assertEqual(original[key], translated[key])
        self.assertEqual(english["thresholds"], arabic["thresholds"])
        self.assertEqual(english["preview_s"], arabic["preview_s"])

    def test_arbitrary_locale_is_rejected(self):
        with self.assertRaises(ValueError):
            metadata(locale="../../content")


if __name__ == "__main__":
    unittest.main()
