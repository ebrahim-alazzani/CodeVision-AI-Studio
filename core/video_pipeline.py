#!/usr/bin/env python3
"""
CodeVision Core Video Extraction Pipeline (Multi-Language Architecture Phase 2)
Performs video frame analysis via OpenCV, audio extraction via FFmpeg,
speech-to-text transcription via Faster-Whisper, Tesseract OCR with multi-language
syntax scoring, chronological SequenceMatcher diff reconstruction, and architecture
categorization across Python, TypeScript, JavaScript, C++, C#, Rust, Go, Java, PHP,
Dart, Swift, Kotlin, and SQL.
"""

import os
import sys
import json
import time
import re
import math
import argparse
import subprocess
from pathlib import Path

# Force UTF-8 on Windows stdout/stderr to prevent cp1252 charmap encoding errors
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure core and parent root are in sys.path
_CORE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _CORE_DIR.parent
for p in [str(_CORE_DIR), str(_ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.models import ExtractedFrame, OcrResult, CodeSnapshot, ReconstructedScript
from core.ocr.noise_filter import NoiseFilter
from core.ocr.tesseract_engine import TesseractEngine
from core.reconstruction.script_builder import ScriptBuilder
from core.reconstruction.script_categorizer import ScriptCategorizer
from core.reconstruction.code_detector import CodeDetector, CodeStructure
from core.evidence import Observation, Evidence, EvidenceModality, BoundingBox
from languages.builtin import create_default_registry
from languages.registry import LanguageRegistry
from vision.roi_detector import CodeROIDetector


def extract_real_audio(video_path: Path, output_wav: Path) -> bool:
    """Extract 16kHz mono audio from video using bundled imageio-ffmpeg or system ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = "ffmpeg"

    cmd = [
        ffmpeg_exe, "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(output_wav)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        return res.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 100
    except Exception as e:
        print(f"PROGRESS: 22 | [WARN] Audio extraction notice: {e}", flush=True)
        return False


def transcribe_with_whisper(audio_path: Path, language: str = None) -> list:
    """Transcribe audio using Faster-Whisper via direct numpy audio loading, bypassing PyAV metadata_errors bug."""
    segments = []
    try:
        import wave
        import numpy as np
        from faster_whisper import WhisperModel

        # Read 16kHz WAV into float32 array
        with wave.open(str(audio_path), "rb") as wf:
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            n_channels = wf.getnchannels()
            raw_bytes = wf.readframes(n_frames)
            if sampwidth == 2:
                audio_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_data = np.frombuffer(raw_bytes, dtype=np.float32)
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels).mean(axis=1)

        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        raw_segments, info = model.transcribe(audio_data, language=language, vad_filter=True)
        for s in raw_segments:
            t = s.text.strip()
            if t:
                # Mathematically convert avg_logprob to probability in [0, 1]: P = exp(avg_logprob)
                avg_lp = float(getattr(s, 'avg_logprob', -0.5))
                whisper_prob = max(0.01, min(1.0, math.exp(avg_lp)))
                segments.append({
                    "start_sec": round(float(s.start), 2),
                    "end_sec": round(float(s.end), 2),
                    "text": t,
                    "confidence": round(whisper_prob, 3)
                })
    except Exception as e:
        print(f"PROGRESS: 82 | [AUDIO NOTICE] Whisper notice: {e}", flush=True)
    return segments


def run_pipeline(video_path: str, output_dir: str, target_lang: str = "auto", sample_sec: float = 2.0) -> str:
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"ERROR: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    out_root = Path(output_dir)
    job_name = f"job_{video_file.stem}"
    job_dir = out_root / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir = job_dir / "keyframes"
    keyframes_dir.mkdir(exist_ok=True)
    ocr_dir = job_dir / "OCR"
    ocr_dir.mkdir(exist_ok=True)
    scripts_dir = job_dir / "Scripts"
    scripts_dir.mkdir(exist_ok=True)
    history_dir = job_dir / "ScriptHistory"
    history_dir.mkdir(exist_ok=True)
    results_dir = job_dir / "results"
    results_dir.mkdir(exist_ok=True)

    print(f"PROGRESS: 5 | [INIT] فتح ملف الفيديو: {video_file.name}", flush=True)

    # Initialize Multi-Language Registry & Code Detector
    registry = create_default_registry()
    code_detector = CodeDetector(registry=registry)

    # 1. Video analysis via OpenCV
    try:
        import cv2
        has_cv2 = True
    except ImportError:
        has_cv2 = False

    fps = 30.0
    total_frames = 0
    duration_sec = 60.0
    width = 1920
    height = 1080
    cap = None

    if has_cv2:
        cap = cv2.VideoCapture(str(video_file))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
            duration_sec = total_frames / fps if total_frames > 0 else 60.0
            print(f"PROGRESS: 10 | [OPENCV] خصائص الفيديو: {width}x{height} @ {fps:.1f} FPS · المدة: {duration_sec:.1f} ثانية ({total_frames} إطار)", flush=True)

    # 2. Extract Real Audio
    audio_wav = job_dir / "audio.wav"
    print(f"PROGRESS: 15 | [AUDIO] استخراج المسار الصوتي الحقيقي بواسطة FFmpeg إلى audio.wav...", flush=True)
    has_audio = extract_real_audio(video_file, audio_wav)
    if has_audio:
        size_kb = audio_wav.stat().st_size / 1024
        print(f"PROGRESS: 20 | [AUDIO] تم استخراج المسار الصوتي بنجاح (16 kHz Mono, الحجم: {size_kb:.1f} KB)", flush=True)
    else:
        print(f"PROGRESS: 20 | [AUDIO] اكتمل فحص المسار الصوتي للفيديو.", flush=True)

    # 3. OpenCV Frame Differencing & Code ROI Isolation
    scenes = []
    prev_gray = None
    frame_interval = max(1, int(fps * sample_sec))
    curr_frame_idx = 0
    detected_scene_idx = 0

    # Initialize Tesseract OCR Engine & Denoising Filter & ROI Detector
    tesseract_engine = TesseractEngine()
    noise_filter = NoiseFilter()
    roi_detector = CodeROIDetector()
    ocr_results = []
    all_candidate_lines = []

    print(f"PROGRESS: 25 | [OPENCV] بدء تتبع التغيرات البصرية وعزل نوافذ الكود (Code ROI)...", flush=True)

    if cap and cap.isOpened():
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if curr_frame_idx % frame_interval == 0:
                sec = curr_frame_idx / fps
                pct = min(68, 25 + int((curr_frame_idx / max(1, total_frames)) * 43))

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                diff_score = 100.0
                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray)
                    diff_score = float(diff.mean())

                # Skip duplicates if difference is minuscule
                if prev_gray is not None and diff_score < 2.2:
                    print(f"PROGRESS: {pct} | [SKIPPED] إطار عند {sec:.1f}s تم تجاوزه (تطابق الإطار السابق · diff: {diff_score:.1f}%)", flush=True)
                else:
                    detected_scene_idx += 1
                    
                    # Automated Dynamic Code ROI & WebCam Masking Detection
                    roi_report = roi_detector.detect(frame)
                    roi_x, roi_y, roi_w, roi_h = roi_report.primary_code_roi
                    code_score = roi_report.confidence

                    kf_path = keyframes_dir / f"scene_{detected_scene_idx:03d}_{sec:.1f}s.png"
                    cv2.imwrite(str(kf_path), frame)

                    # Create annotated frame with glowing OpenCV bounding box
                    annotated = frame.copy()
                    cv2.rectangle(annotated, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (196, 216, 95), 2)
                    tag_text = f"{roi_report.category.upper()} ROI: {code_score*100:.1f}%"
                    cv2.putText(annotated, tag_text, (roi_x, max(22, roi_y - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (196, 216, 95), 2)

                    if roi_report.webcam_roi:
                        wx, wy, ww, wh = roi_report.webcam_roi
                        cv2.rectangle(annotated, (wx, wy), (wx + ww, wy + wh), (50, 70, 240), 2)
                        cv2.putText(annotated, "WEBCAM (MASKED)", (wx, max(22, wy - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 70, 240), 2)

                    ann_path = keyframes_dir / f"annotated_{detected_scene_idx:03d}.png"
                    cv2.imwrite(str(ann_path), annotated)

                    # Perform Tesseract OCR on isolated code window ROI (with webcam masked)
                    cropped_code_region = roi_detector.crop_editor_roi(frame, roi_report, mask_webcam=True)
                    crop_path = keyframes_dir / f"crop_{detected_scene_idx:03d}.png"
                    cv2.imwrite(str(crop_path), cropped_code_region)

                    ext_frame = ExtractedFrame(
                        image_path=crop_path,
                        frame_index=curr_frame_idx,
                        timestamp_sec=sec,
                        is_code_candidate=(code_score > 0.40)
                    )

                    cleaned_text = ""
                    if tesseract_engine.is_available() and code_score > 0.35:
                        try:
                            ocr_res = tesseract_engine.process_frame(ext_frame, ocr_dir)
                            if ocr_res and ocr_res.cleaned_lines:
                                ocr_results.append(ocr_res)
                                cleaned_text = "\n".join(ocr_res.cleaned_lines)
                                all_candidate_lines.extend(ocr_res.cleaned_lines)
                        except Exception:
                            pass

                    scene_info = {
                        "scene_index": detected_scene_idx,
                        "timestamp_sec": round(sec, 2),
                        "frame_index": curr_frame_idx,
                        "keyframe_path": str(kf_path),
                        "annotated_path": str(ann_path),
                        "code_likelihood": round(code_score, 3),
                        "diff_score": round(diff_score, 2),
                        "bounding_box": {"x": roi_x, "y": roi_y, "width": roi_w, "height": roi_h},
                        "category": roi_report.category,
                        "is_dark_theme": roi_report.is_dark_theme,
                        "webcam_roi": {"x": roi_report.webcam_roi[0], "y": roi_report.webcam_roi[1], "width": roi_report.webcam_roi[2], "height": roi_report.webcam_roi[3]} if roi_report.webcam_roi else None,
                        "extracted_text": cleaned_text if cleaned_text else "[UNEXTRACTED]",
                        "summary": f"مشهد {roi_report.category} #{detected_scene_idx} عند {sec:.1f} ثانية (احتمالية الكود: {int(code_score*100)}%)"
                    }
                    scenes.append(scene_info)

                    print(f"PROGRESS: {pct} | [CAPTURED] مشهد #{detected_scene_idx} عند {sec:.1f}s (دقة الكود: {code_score*100:.1f}%, التباين: {diff_score:.1f}%)", flush=True)

                prev_gray = gray

            curr_frame_idx += 1

        cap.release()

    # If no scenes were captured, report clearly as unextracted without synthetic code or fake confidence
    if not scenes:
        scenes = [{
            "scene_index": 1,
            "timestamp_sec": 0.0,
            "frame_index": 0,
            "keyframe_path": "",
            "annotated_path": "",
            "code_likelihood": 0.0,
            "diff_score": 0.0,
            "bounding_box": {"x": 0, "y": 0, "width": 0, "height": 0},
            "extracted_text": "[UNEXTRACTED]",
            "summary": "[UNEXTRACTED] لم يتم التقاط مشاهد برمجية في هذا الفيديو"
        }]

    # Save scenes.json
    scenes_file = job_dir / "scenes.json"
    scenes_file.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PROGRESS: 72 | [SCENES] تم حفظ {len(scenes)} مشهد برمجـي في scenes.json", flush=True)

    # 4. Multi-Language Detection and Structure Identification
    print(f"PROGRESS: 74 | [LANGUAGE] تحليل اللغة المستهدفة وفحص البنية البرمجية عبر LanguageRegistry...", flush=True)
    structure = code_detector.detect_structure(
        all_candidate_lines,
        language=target_lang,
        filename=video_file.name
    )
    resolved_lang_id = structure.language
    profile = registry.get(resolved_lang_id)
    if profile:
        resolved_lang_name = profile.display_name
        file_ext = f".{profile.extensions[0].lstrip('.')}"
    else:
        resolved_lang_name = resolved_lang_id.capitalize()
        file_ext = ".txt"

    print(f"PROGRESS: 75 | [LANGUAGE] اللغة المكتشفة: {resolved_lang_name} ({resolved_lang_id}) · الامتداد: {file_ext} · الثقة: {structure.confidence*100:.1f}%", flush=True)

    # 5. Speech-to-Text Transcription via Whisper
    print(f"PROGRESS: 76 | [WHISPER] تشغيل تفريغ الكلام ومزامنته مع الخط الزمني...", flush=True)
    transcript_segments = []
    if has_audio:
        transcript_segments = transcribe_with_whisper(audio_wav)

    if not transcript_segments:
        for s in scenes:
            if s.get("extracted_text") == "[UNEXTRACTED]":
                continue
            t_sec = s["timestamp_sec"]
            transcript_segments.append({
                "start_sec": max(0.0, t_sec - 1.0),
                "end_sec": min(duration_sec, t_sec + 10.0),
                "text": f"مقطع عند {int(t_sec//60):02d}:{int(t_sec%60):02d} - استعراض شيفرة {resolved_lang_name}",
                "confidence": 0.0
            })

    transcript_data = {
        "video": str(video_file),
        "duration_sec": duration_sec,
        "language": "ar",
        "backend": "faster-whisper",
        "segments": transcript_segments
    }
    transcript_file = job_dir / "transcript.json"
    transcript_file.write_text(json.dumps(transcript_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PROGRESS: 84 | [TRANSCRIPT] تم حفظ التفريغ الصوتي في transcript.json ({len(transcript_segments)} مقطع)", flush=True)

    # 6. Chronological Code Reconstruction
    print(f"PROGRESS: 88 | [RECONSTRUCT] تشغيل محرك إعادة بناء الشفرات متعدد اللغات...", flush=True)

    script_builder = ScriptBuilder()
    reconstructed_scripts = []

    if ocr_results:
        reconstructed_scripts = script_builder.reconstruct_many(ocr_results, video_name=video_file.stem)

    # If no classes were detected from OCR, use actual candidate lines without synthetic templates
    if not reconstructed_scripts:
        if all_candidate_lines:
            primary_name = structure.primary_name or code_detector.normalize_name(video_file.stem) or "ExtractedScript"
            reconstructed_scripts = [
                ReconstructedScript(
                    class_name=primary_name,
                    final_lines=all_candidate_lines,
                    history=[CodeSnapshot(index=1, source_frame="scene_001", lines=all_candidate_lines)],
                    source_video=video_file.stem
                )
            ]
        else:
            print(f"PROGRESS: 90 | [RECONSTRUCT] لم يتم رصد أسطر شيفرة صالحة للاستخراج في هذا المقطع.", flush=True)
            reconstructed_scripts = []

    # Determine comment prefix based on language extension
    if file_ext in (".py", ".pyw", ".rb"):
        comment_prefix = "#"
    elif file_ext == ".sql":
        comment_prefix = "--"
    else:
        comment_prefix = "//"

    # Save reconstructed scripts to Scripts/ and ScriptHistory/
    scripts_map = {}
    extracted_file_names = []

    for scr in reconstructed_scripts:
        c_name = scr.class_name
        code_str = "\n".join(scr.final_lines)
        scripts_map[c_name] = code_str

        script_filename = f"{c_name}{file_ext}" if not c_name.endswith(file_ext) else c_name
        script_file = scripts_dir / script_filename
        script_file.write_text(
            f"{comment_prefix} ============================================================\n"
            f"{comment_prefix} RECONSTRUCTED {resolved_lang_name.upper()} SCRIPT · CodeVision Multi-Language\n"
            f"{comment_prefix} Entity: {c_name}\n"
            f"{comment_prefix} Source Video: {video_file.name}\n"
            f"{comment_prefix} Reconstructed At: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{comment_prefix} Language: {resolved_lang_name} ({resolved_lang_id})\n"
            f"{comment_prefix} ============================================================\n\n" + code_str,
            encoding="utf-8"
        )
        extracted_file_names.append(script_filename)

        # Save history snapshots in ScriptHistory/
        for snap in scr.history:
            snap_file = history_dir / f"{c_name}_{snap.index:03d}{file_ext}"
            snap_file.write_text(
                f"{comment_prefix} Snapshot #{snap.index:03d} from {snap.source_frame}\n" + "\n".join(snap.lines),
                encoding="utf-8"
            )

        # Final snapshot
        final_hist = history_dir / f"{c_name}_FINAL{file_ext}"
        final_hist.write_text(f"{comment_prefix} FINAL RECONSTRUCTED CODE FOR {c_name}\n\n" + code_str, encoding="utf-8")

    # 7. Organize into standardized Architecture hierarchy via ScriptCategorizer
    categorized_files = ScriptCategorizer.organize_export(scripts_map, results_dir, extension=file_ext)
    print(f"PROGRESS: 94 | [CATEGORIZE] تم تنظيم وتصنيف {len(scripts_map)} ملف برمجي في results/ProjectScripts/", flush=True)

    # 8. Save ALL_CANDIDATE_CODE or UNEXTRACTED notice
    if all_candidate_lines:
        all_code_file = results_dir / "ALL_CANDIDATE_CODE.txt"
        all_code_file.write_text("\n".join(all_candidate_lines), encoding="utf-8")
    else:
        unextracted_file = results_dir / "UNEXTRACTED.txt"
        unextracted_file.write_text("[UNEXTRACTED] لم يتم رصد أسطر شيفرة صالحة للاستخراج في هذا الفيديو.\n", encoding="utf-8")

    # 9. Compute Overall Confidence Mathematically across modalities
    c_code = float(structure.confidence) if all_candidate_lines else 0.0

    valid_likelihoods = [
        s.get("code_likelihood", 0.0)
        for s in scenes
        if s.get("extracted_text") != "[UNEXTRACTED]"
    ]
    c_visual = float(sum(valid_likelihoods) / len(valid_likelihoods)) if valid_likelihoods else 0.0

    valid_audio_confs = [
        s.get("confidence", 0.0)
        for s in transcript_segments
        if s.get("confidence", 0.0) > 0.0
    ]
    c_audio = float(sum(valid_audio_confs) / len(valid_audio_confs)) if valid_audio_confs else 0.0

    if all_candidate_lines:
        if valid_audio_confs:
            overall_confidence = round(0.50 * c_code + 0.35 * c_visual + 0.15 * c_audio, 3)
        else:
            overall_confidence = round(0.60 * c_code + 0.40 * c_visual, 3)
    else:
        overall_confidence = 0.0

    # 10. Save manifest.json and observations.json
    manifest = {
        "video_file": str(video_file),
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "language": resolved_lang_name,
        "language_id": resolved_lang_id,
        "file_extension": file_ext,
        "duration_sec": duration_sec,
        "scenes_count": len(scenes),
        "transcript_segments_count": len(transcript_segments),
        "extracted_classes": [s.class_name for s in reconstructed_scripts],
        "extracted_files": extracted_file_names,
        "entry_points": structure.entry_points,
        "confidence": overall_confidence,
        "scripts_directory": str(scripts_dir),
        "categorized_directory": str(results_dir / "ProjectScripts"),
        "history_directory": str(history_dir),
        "output_directory": str(job_dir)
    }
    (job_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    observations = {
        "video_id": video_file.stem,
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "language": resolved_lang_name,
        "language_id": resolved_lang_id,
        "confidence": overall_confidence,
        "confidence_breakdown": {
            "code_structure": c_code,
            "visual_roi": round(c_visual, 3),
            "audio_speech": round(c_audio, 3)
        },
        "scenes_count": len(scenes),
        "classes_count": len(reconstructed_scripts),
        "classes": [s.class_name for s in reconstructed_scripts],
        "entry_points": structure.entry_points,
        "audio_present": has_audio,
        "ocr_engine": "Tesseract OCR",
        "reconstruction_engine": "CodeVision Universal Multi-Language Engine",
        "output_dir": str(job_dir)
    }
    (job_dir / "observations.json").write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"PROGRESS: 100 | [COMPLETE] اكتملت عملية الاستخراج وإعادة بناء المشروع بالكامل: {len(reconstructed_scripts)} ملفات مستعادة بنجاح (الثقة: {overall_confidence*100:.1f}%)!", flush=True)
    return str(job_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CodeVision Universal Multi-Language Extraction Pipeline")
    parser.add_argument("video_path", nargs="?", default=None, help="Path to input video file")
    parser.add_argument("output_dir", nargs="?", default=None, help="Path to output directory")
    parser.add_argument("--video", dest="video_flag", default=None, help="Alternative flag for video path")
    parser.add_argument("--output-dir", "--output_dir", dest="out_flag", default=None, help="Alternative flag for output directory")
    parser.add_argument("--language", default="auto", help="Target programming language (e.g. auto, Python, TypeScript, C++, Rust, Go, C#)")
    parser.add_argument("--sample_sec", "--sample-rate", dest="sample_sec", type=float, default=2.0, help="Sampling interval in seconds")

    args = parser.parse_args()
    v_path = args.video_path or args.video_flag
    o_dir = args.output_dir or args.out_flag
    if not v_path or not o_dir:
        parser.error("Both video_path and output_dir are required.")

    run_pipeline(v_path, o_dir, target_lang=args.language, sample_sec=args.sample_sec)
