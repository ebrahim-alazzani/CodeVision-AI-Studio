"""
Unit tests for OCR Preprocessor and Code Heuristics Engine.
"""

import unittest
import numpy as np
from core.ocr.preprocessor import CodeHeuristics, ImagePreprocessor, PreprocessResult


class CodeHeuristicsTests(unittest.TestCase):
    def test_strip_pipe_gutter(self):
        """Detect and strip IDE pipe gutters e.g. '1 |', '2 |'."""
        lines = [
            "1 | using UnityEngine;",
            "2 | public class Test : MonoBehaviour",
            "3 | {",
            "4 |     void Start() {}",
            "5 | }"
        ]
        stripped = CodeHeuristics.strip_gutter_line_numbers(lines)
        expected = [
            "using UnityEngine;",
            "public class Test : MonoBehaviour",
            "{",
            "    void Start() {}",
            "}"
        ]
        self.assertEqual(expected, stripped)

    def test_strip_colon_gutter(self):
        """Detect and strip IDE colon gutters e.g. '01:', '02:'."""
        lines = [
            "01: def calculate_area(radius):",
            "02:     import math",
            "03:     return math.pi * (radius ** 2)"
        ]
        stripped = CodeHeuristics.strip_gutter_line_numbers(lines)
        expected = [
            "def calculate_area(radius):",
            "    import math",
            "    return math.pi * (radius ** 2)"
        ]
        self.assertEqual(expected, stripped)

    def test_strip_bare_number_gutter(self):
        """Detect and strip bare line numbers with trailing spaces e.g. '1   ', '2   '."""
        lines = [
            " 1    int speed = 10;",
            " 2    float health = 100.0f;",
            " 3    bool isAlive = true;"
        ]
        stripped = CodeHeuristics.strip_gutter_line_numbers(lines)
        expected = [
            "int speed = 10;",
            "float health = 100.0f;",
            "bool isAlive = true;"
        ]
        self.assertEqual(expected, stripped)

    def test_gutter_false_positive_protection(self):
        """Do not strip genuine code that starts with math or switch cases."""
        # Arithmetic expressions
        math_code = [
            "1 + 2 == 3",
            "4 * 5 == 20"
        ]
        self.assertEqual(math_code, CodeHeuristics.strip_gutter_line_numbers(math_code))

        # Switch cases
        switch_code = [
            "case 1:",
            "    doFirst();",
            "    break;",
            "case 2:",
            "    doSecond();",
            "    break;"
        ]
        # Non-monotonic / interspersed with statements: should NOT strip switch cases
        stripped = CodeHeuristics.strip_gutter_line_numbers(switch_code)
        self.assertEqual(switch_code, stripped)

    def test_strip_prompt_prefixes(self):
        """Strip terminal, REPL, and IPython prompt prefixes."""
        prompts = [
            ">>> def greet():",
            "...     return 'hello'",
            "$ npm run build",
            "# make install",
            "In [4]: result = compute(10)",
            "Out[4]: 42"
        ]
        cleaned = CodeHeuristics.strip_prompt_prefixes(prompts)
        expected = [
            "def greet():",
            "    return 'hello'",
            "npm run build",
            "make install",
            "result = compute(10)",
            "42"
        ]
        self.assertEqual(expected, cleaned)

    def test_repair_code_glyphs(self):
        """Repair smart quotes, arrow operators, brackets, and keyword OCR errors."""
        text = '“Hello World” and ‘test’ — arrow = > and - > with c0nst and functi0n'
        repaired = CodeHeuristics.repair_code_glyphs(text)
        self.assertIn('"Hello World"', repaired)
        self.assertIn("'test'", repaired)
        self.assertIn('-', repaired)
        self.assertIn('=>', repaired)
        self.assertIn('->', repaired)
        self.assertIn('const', repaired)
        self.assertIn('function', repaired)


    def test_noise_filter_gutter_integration(self):
        """NoiseFilter.clean_frame_text strips gutter line numbers cleanly."""
        from core.ocr.noise_filter import NoiseFilter
        nf = NoiseFilter()
        raw = "1 | using UnityEngine;\n2 | public class GameController : MonoBehaviour\n3 | {\n4 | }"
        cleaned = nf.clean_frame_text(raw)
        self.assertEqual(["using UnityEngine;", "public class GameController : MonoBehaviour", "{", "}"], cleaned)


class ImagePreprocessorTests(unittest.TestCase):
    def setUp(self):
        # Create a synthetic dark-theme image (RGB 30, 30, 30 like VS Code Dark)
        self.dark_image = np.full((100, 200, 3), 30, dtype=np.uint8)
        # Put some light text-like pixels in the middle
        self.dark_image[40:60, 40:160] = 220

        # Create a synthetic light-theme image (RGB 245, 245, 245)
        self.light_image = np.full((100, 200, 3), 245, dtype=np.uint8)
        # Put some dark text pixels in the middle
        self.light_image[40:60, 40:160] = 20

    def test_calculate_background_luminance(self):
        """Luminance calculation from borders."""
        dark_lum = ImagePreprocessor.calculate_background_luminance(self.dark_image)
        light_lum = ImagePreprocessor.calculate_background_luminance(self.light_image)

        self.assertLess(dark_lum, 0.25)
        self.assertGreater(light_lum, 0.85)

    def test_dark_theme_detection(self):
        """Correctly classify dark vs light themes."""
        self.assertTrue(ImagePreprocessor.is_dark_theme(self.dark_image))
        self.assertFalse(ImagePreprocessor.is_dark_theme(self.light_image))

    def test_dark_theme_inversion(self):
        """Dark theme should be inverted so background is bright and text is dark."""
        result = ImagePreprocessor.preprocess_code_image(
            self.dark_image,
            invert_dark_theme=True,
            scale_factor=1.0,
            sharpen=False
        )
        self.assertTrue(result.is_dark_theme)
        # Background was 30 -> inverted background should now be near 225
        # Sample edge pixel
        edge_pixel = result.image[2, 2]
        self.assertGreater(edge_pixel, 200)

    def test_light_theme_not_inverted(self):
        """Light theme should retain light background without unnecessary inversion."""
        result = ImagePreprocessor.preprocess_code_image(
            self.light_image,
            invert_dark_theme=True,
            scale_factor=1.0,
            sharpen=False
        )
        self.assertFalse(result.is_dark_theme)
        edge_pixel = result.image[2, 2]
        self.assertGreater(edge_pixel, 200)

    def test_resolution_upscaling(self):
        """Scaling factor increases output resolution proportionally."""
        scale = 2.5
        result = ImagePreprocessor.preprocess_code_image(
            self.dark_image,
            scale_factor=scale
        )
        orig_w, orig_h = result.original_size
        proc_w, proc_h = result.processed_size

        self.assertEqual(200, orig_w)
        self.assertEqual(100, orig_h)
        self.assertEqual(int(round(200 * scale)), proc_w)
        self.assertEqual(int(round(100 * scale)), proc_h)

    def test_binarization_mode(self):
        """Binarize option yields crisp binary image (values 0 and 255)."""
        result = ImagePreprocessor.preprocess_code_image(
            self.dark_image,
            binarize=True
        )
        unique_vals = set(np.unique(result.image))
        self.assertTrue(unique_vals.issubset({0, 255}))


if __name__ == "__main__":
    unittest.main()
