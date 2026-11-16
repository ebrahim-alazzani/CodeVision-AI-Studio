import unittest

from vision.frame_analyzer import FrameAnalyzer


class FrameAnalyzerTests(unittest.TestCase):
    def test_threshold_range_is_validated(self):
        with self.assertRaises(ValueError):
            FrameAnalyzer(1.1)

    def test_cv_dependency_is_optional_until_used(self):
        analyzer = FrameAnalyzer()
        self.assertEqual(0.32, analyzer.threshold)


if __name__ == "__main__":
    unittest.main()
