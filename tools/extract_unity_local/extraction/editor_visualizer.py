"""
EditorVisualizer — CodeVision Extractor v5.0 Tutorial Step Capture

Detects non-code Unity Editor frames (Hierarchy, Inspector, Animator, Physics)
and extracts step-by-step tutorial screenshots and guides without impacting code OCR.

Author: Eng. Ibrahim Anas Al-Azzani
        CyberPro for Technical & Engineering Works
"""

import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from core.models import OcrResult, VideoFile


class EditorVisualizer:
    """Detects Unity Editor UI actions and exports step-by-step guides."""

    UNITY_EDITOR_KEYWORDS = [
        r'\bInspector\b', r'\bHierarchy\b', r'\bProject\b', r'\bConsole\b',
        r'\bAddComponent\b', r'\bTransform\b', r'\bBoxCollider\b', r'\bRigidBody\b',
        r'\bRigidbody2D\b', r'\bMeshRenderer\b', r'\bSpriteRenderer\b',
        r'\bAnimator\b', r'\bRectTransform\b', r'\bCanvas\b', r'\bMainCamera\b',
        r'\bMaterial\b', r'\bPrefab\b', r'\bTag\b', r'\bLayer\b', r'\bGameObject\b',
        r'\bScene\b', r'\bAsset\b', r'\bTilemap\b', r'\bAudioSource\b'
    ]

    @classmethod
    def is_editor_step_frame(cls, ocr_result: OcrResult) -> bool:
        """Return True if frame represents a Unity Editor UI step (not C# code)."""
        # If frame is identified as code candidate, ignore it for UI step
        if ocr_result.is_code:
            return False

        text = ocr_result.raw_text
        if not text or len(text.strip()) < 10:
            return False

        for kw in cls.UNITY_EDITOR_KEYWORDS:
            if re.search(kw, text, re.IGNORECASE):
                return True

        return False

    @classmethod
    def extract_steps(cls, ocr_results: List[OcrResult], video_name: str, video_dir: Path) -> List[Path]:
        """
        Extract Editor step screenshots and write TUTORIAL_STEPS.md.

        Args:
            ocr_results: List of OcrResult objects for the video.
            video_name: Name of the video file.
            video_dir: Output directory path for the video.

        Returns:
            List of saved step image paths.
        """
        steps_dir = video_dir / "TutorialSteps"
        steps_dir.mkdir(parents=True, exist_ok=True)

        step_images = []
        step_details = []

        step_index = 1
        for result in ocr_results:
            if cls.is_editor_step_frame(result):
                img_path = result.frame.image_path
                if not img_path.exists():
                    continue

                dest_name = f"Step_{step_index:02d}_{img_path.name}"
                dest_path = steps_dir / dest_name
                shutil.copy2(img_path, dest_path)
                step_images.append(dest_path)

                # Extract key text lines for step description
                lines = [l.strip() for l in result.raw_text.splitlines() if len(l.strip()) > 3]
                summary = " | ".join(lines[:3]) if lines else "Unity Editor Configuration"
                timestamp_str = f"{int(result.frame.timestamp_sec // 60):02d}:{int(result.frame.timestamp_sec % 60):02d}"

                step_details.append((step_index, timestamp_str, dest_name, summary))
                step_index += 1

        # Write TUTORIAL_STEPS.md guide if steps detected
        if step_details:
            guide_path = video_dir / "TUTORIAL_STEPS.md"
            with open(guide_path, "w", encoding="utf-8") as f:
                f.write(f"# Tutorial Step Guide — {video_name}\n\n")
                f.write("Visual guide of Unity Editor configurations, Inspector settings, and Animator setups.\n\n")
                f.write("| Step | Time | Screenshot | Detected Action / Settings |\n")
                f.write("|---|---|---|---|\n")
                for idx, time_s, img_n, desc in step_details:
                    f.write(f"| Step {idx:02d} | {time_s} | `TutorialSteps/{img_n}` | {desc} |\n")

        return step_images
