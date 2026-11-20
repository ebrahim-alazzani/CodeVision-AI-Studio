"""
Unit tests for core.training.train_classifier (Phase 4).
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from core.training.train_classifier import train_code_classifier


class TestTrainClassifier(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_train_code_classifier_execution(self):
        record = train_code_classifier(
            model_name="UnitTestCaseModel",
            epochs=3,
            learning_rate=0.02,
            batch_size=8,
            output_dir=self.temp_dir
        )

        self.assertEqual(record["model_name"], "UnitTestCaseModel")
        self.assertEqual(record["training_epochs"], 3)
        self.assertGreater(record["final_accuracy"], 0.65)
        self.assertIn("weights", record)
        self.assertEqual(len(record["weights"]), 8)

        out_json = self.temp_dir / "UnitTestCaseModel.json"
        self.assertTrue(out_json.exists())


if __name__ == "__main__":
    unittest.main()
