import unittest

from core.evidence import (
    BoundingBox,
    Evidence,
    EvidenceModality,
    Observation,
)


class EvidenceModelTests(unittest.TestCase):
    def test_observation_links_audio_and_ocr_evidence(self):
        observation = Observation("lesson-01", 12.0, 15.0, language_id="Python")
        observation.add_evidence(Evidence(
            EvidenceModality.OCR_TEXT, "frames/frame_004.jpg", 12.2,
            confidence=0.91, text="def total(items):",
            bounding_box=BoundingBox(100, 200, 800, 44),
        ))
        observation.add_evidence(Evidence(
            EvidenceModality.TRANSCRIPT, "audio/lesson.wav", 12.0, 15.0,
            confidence=0.87, text="سننشئ دالة لحساب الإجمالي",
        ))

        result = observation.to_dict()
        self.assertEqual("python", result["language_id"])
        self.assertEqual(2, len(result["evidence"]))
        self.assertEqual("ocr_text", result["evidence"][0]["modality"])
        self.assertEqual(100, result["evidence"][0]["bounding_box"]["x"])

    def test_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError):
            Evidence(EvidenceModality.OCR_TEXT, "frame.jpg", 0, confidence=1.1)

    def test_rejects_invalid_time_range(self):
        with self.assertRaises(ValueError):
            Evidence(EvidenceModality.TRANSCRIPT, "audio.wav", 5, 4)

    def test_rejects_evidence_outside_observation_window(self):
        observation = Observation("lesson-01", 10, 12)
        item = Evidence(EvidenceModality.TRANSCRIPT, "audio.wav", 13, 14)
        with self.assertRaises(ValueError):
            observation.add_evidence(item)

    def test_rejects_invalid_bounding_box(self):
        with self.assertRaises(ValueError):
            BoundingBox(0, 0, 0, 10)


if __name__ == "__main__":
    unittest.main()
