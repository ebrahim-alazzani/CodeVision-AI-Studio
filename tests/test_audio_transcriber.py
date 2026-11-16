import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from transcription.audio_transcriber import (
    AudioTranscriber,
    TranscriptSegment,
    TranscriptionResult,
)


class AudioTranscriberTests(unittest.TestCase):
    def test_format_time_includes_hours_and_milliseconds(self):
        self.assertEqual("01:02:03.456", AudioTranscriber._format_time(3723.456))

    def test_result_serializes_timestamped_segments(self):
        result = TranscriptionResult(Path("audio.wav"),
            [TranscriptSegment(1.25, 2.5, "مرحبا")], "ar", "test-backend")
        self.assertEqual("مرحبا", result.text)
        payload = result.to_dict()
        self.assertEqual(1.25, payload["segments"][0]["start_sec"])
        self.assertEqual("ar", payload["language"])

    def test_extract_audio_builds_wav_and_invokes_ffmpeg(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "audio.wav"

            def fake_run(command, **kwargs):
                output.write_bytes(b"0" * 100)
                class Result:
                    returncode = 0
                self.assertIn("16000", command)
                self.assertIn("-ac", command)
                return Result()

            with patch("transcription.audio_transcriber.subprocess.run", side_effect=fake_run):
                self.assertTrue(AudioTranscriber.extract_audio(Path("lesson.mp4"), output, "ffmpeg"))

    def test_transcribe_saves_audio_path_and_json_transcript(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            video = folder / "lesson.mp4"
            video.write_bytes(b"video")
            result = TranscriptionResult(folder / "audio.wav",
                [TranscriptSegment(0.0, 1.0, "hello")], "en", "mock")
            with patch.object(AudioTranscriber, "extract_audio", return_value=True), \
                 patch.object(AudioTranscriber, "transcribe_audio", return_value=result):
                output = AudioTranscriber.transcribe(video, folder)
            self.assertEqual(folder / "transcript.json", output)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("hello", data["segments"][0]["text"])
            self.assertTrue((folder / "TUTORIAL_TRANSCRIPT.md").is_file())


if __name__ == "__main__":
    unittest.main()
