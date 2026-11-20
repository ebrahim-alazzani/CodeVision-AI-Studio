"""
Unit tests for core.ocr.code_token_normalizer & CER/WER computation (Phase 4).
"""

import unittest
from core.ocr.code_token_normalizer import (
    CodeTokenNormalizer,
    compute_cer,
    compute_wer,
    compute_levenshtein
)


class TestCodeTokenNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = CodeTokenNormalizer(strip_gutters=True)

    def test_levenshtein_distance(self):
        self.assertEqual(compute_levenshtein("", ""), 0)
        self.assertEqual(compute_levenshtein("code", "code"), 0)
        self.assertEqual(compute_levenshtein("kitten", "sitting"), 3)

    def test_cer_and_wer_metrics(self):
        ref = "Widget build(BuildContext context)"
        hyp_exact = "Widget build(BuildContext context)"
        hyp_typo = "Widqet build(Buildcontext context)"

        self.assertEqual(compute_cer(ref, hyp_exact), 0.0)
        self.assertEqual(compute_wer(ref, hyp_exact), 0.0)

        cer = compute_cer(ref, hyp_typo)
        self.assertGreater(cer, 0.0)
        self.assertLess(cer, 0.15)

    def test_flutter_dart_normalization(self):
        corrupted = "1 | @overrlde\n2 | Widqet build(Buildcontext context) = > Scaffold();"
        result = self.normalizer.normalize(corrupted, language_hint="dart")

        expected = "@override\nWidget build(BuildContext context) => Scaffold();"
        self.assertEqual(result.cleaned_code, expected)
        self.assertGreater(result.num_replacements, 0)

    def test_python_normalization(self):
        corrupted = "01: asyne def process():\n02:     retum se1f.val"
        result = self.normalizer.normalize(corrupted, language_hint="python")

        expected = "async def process():\n    return self.val"
        self.assertEqual(result.cleaned_code, expected)

    def test_smart_quotes_and_glyphs(self):
        raw = "print(“Hello World!”); // standard ‘quote’"
        result = self.normalizer.normalize(raw)
        self.assertEqual(result.cleaned_code, 'print("Hello World!"); // standard \'quote\'')

    def test_operators_repair(self):
        raw = "if (a ! = b && c < = 10 || d > = 20) x + = 1;"
        result = self.normalizer.normalize(raw)
        self.assertEqual(result.cleaned_code, "if (a != b && c <= 10 || d >= 20) x += 1;")

    def test_hex_normalization(self):
        raw = "int color = OxFFAABB;"
        result = self.normalizer.normalize(raw)
        self.assertEqual(result.cleaned_code, "int color = 0xFFAABB;")


if __name__ == "__main__":
    unittest.main()
