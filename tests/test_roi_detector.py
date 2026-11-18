"""
Unit tests for vision.roi_detector (CodeVision Phase 3).
"""

import unittest
import numpy as np
from vision.roi_detector import CodeROIDetector, CodeRegion, ROIReport


class TestCodeROIDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CodeROIDetector()

    def test_dark_code_editor_detection(self):
        # Create synthetic dark editor (1920x1080) with horizontal code-like lines
        img = np.full((1080, 1920, 3), 30, dtype=np.uint8)
        # Draw code text lines
        for y in range(80, 900, 24):
            # Line of code (width ~800px)
            img[y : y + 3, 100 : 100 + int(600 + (y % 300))] = 220

        report = self.detector.detect(img)
        self.assertIsInstance(report, ROIReport)
        self.assertTrue(report.is_dark_theme)
        self.assertEqual(report.category, "code_editor")
        self.assertGreater(report.confidence, 0.5)

        x, y, w, h = report.primary_code_roi
        # The detected ROI should cover the code lines
        self.assertLessEqual(x, 100)
        self.assertGreater(w, 600)
        self.assertGreater(h, 700)

    def test_split_screen_detection(self):
        # Left half is dark editor, right half is bright preview
        img = np.full((1080, 1920, 3), 245, dtype=np.uint8)  # bright background
        img[:, :960] = 32  # dark left half

        # Draw code on left half only
        for y in range(100, 800, 25):
            img[y : y + 2, 80:850] = 200

        report = self.detector.detect(img)
        self.assertIsInstance(report, ROIReport)
        x, y, w, h = report.primary_code_roi
        # Should isolate left half
        self.assertLess(x + w, 1100)

    def test_crop_with_webcam_mask(self):
        img = np.full((1080, 1920, 3), 35, dtype=np.uint8)
        report = ROIReport(
            frame_width=1920,
            frame_height=1080,
            primary_code_roi=(50, 50, 1200, 900),
            category="code_editor",
            confidence=0.92,
            is_dark_theme=True,
            webcam_roi=(1000, 700, 200, 180),  # webcam inside editor region
        )

        cropped = self.detector.crop_editor_roi(img, report, mask_webcam=True)
        self.assertEqual(cropped.shape, (900, 1200, 3))
        # Masked area should have neutral fill color (25, 25, 25)
        # Relative webcam coordinates: x = 1000 - 50 = 950, y = 700 - 50 = 650
        masked_pixel = cropped[660, 960]
        np.testing.assert_array_equal(masked_pixel, np.array([25, 25, 25], dtype=np.uint8))

    def test_invalid_path_raises(self):
        with self.assertRaises(ValueError):
            self.detector.detect("non_existent_image_path_12345.png")

    def test_to_dict_serialization(self):
        region = CodeRegion(x=10, y=20, w=300, h=400, category="code_editor", confidence=0.85, is_dark_theme=True)
        report = ROIReport(
            frame_width=1920,
            frame_height=1080,
            primary_code_roi=(10, 20, 300, 400),
            category="code_editor",
            confidence=0.85,
            is_dark_theme=True,
            webcam_roi=None,
            all_regions=[region],
        )
        d = report.to_dict()
        self.assertEqual(d["frame_width"], 1920)
        self.assertEqual(d["category"], "code_editor")
        self.assertEqual(len(d["all_regions"]), 1)
        self.assertEqual(d["all_regions"][0]["w"], 300)


if __name__ == "__main__":
    unittest.main()
