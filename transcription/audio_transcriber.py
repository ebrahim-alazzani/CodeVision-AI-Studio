"""Optional offline transcription adapters used by CodeVision Runtime."""

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str
    confidence: Optional[float] = None


@dataclass
class TranscriptionResult:
    audio_path: Path
    segments: List[TranscriptSegment]
    language: Optional[str] = None
    backend: str = ""

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    def to_dict(self):
        return {"audio_path": str(self.audio_path), "language": self.language,
                "backend": self.backend, "segments": [asdict(s) for s in self.segments]}


class AudioTranscriber:
    """Extract 16 kHz mono audio and use installed local Whisper models."""

    @staticmethod
    def extract_audio(video_path: Path, output_wav: Path,
                      ffmpeg_bin: str = "ffmpeg") -> bool:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        cmd = [ffmpeg_bin, "-y", "-i", str(video_path), "-vn", "-acodec",
               "pcm_s16le", "-ar", "16000", "-ac", """1""", str(output_wav)]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=600)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and output_wav.is_file() and output_wav.stat().st_size > 44

    @classmethod
    def transcribe_audio(cls, audio_path: Path, model_name: str = "small",
                         language: Optional[str] = None, device: str = "cpu",
                         backend: str = "auto") -> TranscriptionResult:
        if not audio_path.is_file():
            raise FileNotFoundError(str(audio_path))
        if backend not in ("auto", "faster-whisper", "openai-whisper"):
            raise ValueError("unsupported transcription backend")
        candidates = ["faster-whisper", "openai-whisper"] if backend == "auto" else [backend]
        for name in candidates:
            try:
                if name == "faster-whisper":
                    from faster_whisper import WhisperModel
                    model = WhisperModel(model_name, device=device,
                                         compute_type="int8" if device == "cpu" else "float16")
                    segments, info = model.transcribe(str(audio_path), language=language,
                                                      vad_filter=True)
                    output = [TranscriptSegment(float(s.start), float(s.end), s.text.strip())
                              for s in segments if s.text.strip()]
                    return TranscriptionResult(audio_path, output,
                                               getattr(info, "language", language), name)
                import whisper
                result = whisper.load_model(model_name).transcribe(
                    str(audio_path), language=language, fp16=False)
                output = [TranscriptSegment(float(s["start"]), float(s["end"]), s["text"].strip())
                          for s in result.get("segments", []) if s.get("text", "").strip()]
                return TranscriptionResult(audio_path, output,
                                           result.get("language", language), name)
            except ImportError:
                continue
        raise RuntimeError("No local Whisper backend is installed")

    @classmethod
    def transcribe(cls, video_path: Path, video_dir: Path,
                   ffmpeg_bin: str = "ffmpeg", model_name: str = "small",
                   language: Optional[str] = None, device: str = "cpu",
                   backend: str = "auto") -> Optional[Path]:
        """Preserve legacy CLI behavior while saving timestamped JSON/Markdown."""
        video_dir.mkdir(parents=True, exist_ok=True)
        wav_path = video_dir / "audio.wav"
        if not cls.extract_audio(video_path, wav_path, ffmpeg_bin):
            return None
        json_path = video_dir / "transcript.json"
        try:
            result = cls.transcribe_audio(wav_path, model_name, language, device, backend)
            json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            lines = ["# Video transcription — " + video_path.name, "",
                     "Language: " + (result.language or "unknown"), "Backend: " + result.backend, ""]
            for segment in result.segments:
                lines.append("**[{} – {}]** {}".format(
                    cls._format_time(segment.start_sec), cls._format_time(segment.end_sec), segment.text))
                lines.append("")
            (video_dir / "TUTORIAL_TRANSCRIPT.md").write_text("\n".join(lines), encoding="utf-8")
        except RuntimeError as exc:
            json_path.write_text(json.dumps({"audio_path": str(wav_path),
                "transcription_status": "backend_unavailable", "message": str(exc),
                "language": language, "segments": []}, ensure_ascii=False, indent=2), encoding="utf-8")
            (video_dir / "TUTORIAL_TRANSCRIPT.md").write_text(
                "# Audio extracted\n\nNo local transcription backend is installed.\n", encoding="utf-8")
        return json_path

    @staticmethod
    def _format_time(seconds: float) -> str:
        milliseconds = int(max(0.0, seconds) * 1000)
        hours, rest = divmod(milliseconds, 3600000)
        minutes, rest = divmod(rest, 60000)
        secs, millis = divmod(rest, 1000)
        return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, secs, millis)
