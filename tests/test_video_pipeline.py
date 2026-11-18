import unittest
import json
import tempfile
import shutil
from pathlib import Path

from core.video_pipeline import run_pipeline, transcribe_with_whisper
from core.reconstruction.script_categorizer import ScriptCategorizer


class VideoPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_script_categorizer_multi_language_extensions(self):
        scripts = {
            "UserService": "class UserService:\n    pass",
            "UserModel": "class UserModel:\n    pass",
            "UserController": "class UserController:\n    pass",
        }
        out_path = Path(self.temp_dir) / "categorizer_test"
        written = ScriptCategorizer.organize_export(scripts, out_path, extension=".py")
        self.assertEqual(3, len(written))
        self.assertTrue(written["UserService"].name.endswith(".py"))
        self.assertTrue(written["UserModel"].name.endswith(".py"))
        self.assertTrue(written["UserController"].name.endswith(".py"))
        self.assertEqual("Controllers", written["UserController"].parent.name)
        self.assertEqual("Models", written["UserModel"].parent.name)
        self.assertEqual("Services", written["UserService"].parent.name)

    def test_pipeline_nonexistent_video_raises_cleanly(self):
        with self.assertRaises(SystemExit):
            run_pipeline("non_existent_file.mp4", self.temp_dir)

    def test_pipeline_outputs_unextracted_without_fake_monobehaviour(self):
        # Create a mock 0-byte or invalid video file to trigger extraction on an empty video
        mock_video = Path(self.temp_dir) / "sample_empty.mp4"
        mock_video.write_bytes(b"")

        job_dir_str = run_pipeline(str(mock_video), self.temp_dir, target_lang="auto")
        job_dir = Path(job_dir_str)

        # 1. scenes.json should have [UNEXTRACTED] and 0.0 likelihood, NOT MonoBehaviour or 0.94
        scenes_file = job_dir / "scenes.json"
        self.assertTrue(scenes_file.exists())
        scenes_data = json.loads(scenes_file.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(scenes_data), 1)
        self.assertEqual("[UNEXTRACTED]", scenes_data[0]["extracted_text"])
        self.assertEqual(0.0, scenes_data[0]["code_likelihood"])
        self.assertNotIn("MonoBehaviour", scenes_data[0]["extracted_text"])

        # 2. observations.json should have 0.0 confidence, NOT 0.962
        obs_file = job_dir / "observations.json"
        self.assertTrue(obs_file.exists())
        obs_data = json.loads(obs_file.read_text(encoding="utf-8"))
        self.assertEqual(0.0, obs_data["confidence"])

        # 3. UNEXTRACTED.txt should exist
        unextracted_file = job_dir / "results" / "UNEXTRACTED.txt"
        self.assertTrue(unextracted_file.exists())
        self.assertIn("[UNEXTRACTED]", unextracted_file.read_text(encoding="utf-8"))

    def test_pipeline_target_language_specified_python(self):
        mock_video = Path(self.temp_dir) / "python_test.mp4"
        mock_video.write_bytes(b"")

        job_dir_str = run_pipeline(str(mock_video), self.temp_dir, target_lang="Python")
        job_dir = Path(job_dir_str)

        manifest_file = job_dir / "manifest.json"
        self.assertTrue(manifest_file.exists())
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual("Python", manifest["language"])
        self.assertEqual(".py", manifest["file_extension"])


if __name__ == "__main__":
    unittest.main()
