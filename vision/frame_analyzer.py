"""Lightweight visual features for ranking likely code-editor frames.

OpenCV is optional and imported lazily. This module ranks frames for review;
it does not claim to be a trained code detector.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FrameAnalysis:
    image_path: str
    width: int
    height: int
    edge_density: float
    dark_pixel_ratio: float
    code_likelihood: float
    likely_code_frame: bool


class FrameAnalyzer:
    def __init__(self, threshold: float = 0.32):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def analyze(self, image_path: Path) -> FrameAnalysis:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Frame analysis requires OpenCV: pip install opencv-python") from exc
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("Unable to read image: " + str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        edges = cv2.Canny(gray, 70, 150)
        edge_density = float((edges > 0).mean())
        dark_ratio = float((gray < 90).mean())
        # Code editors often have dense, repeated edges and dark themes. Keep
        # this score conservative and combine it with OCR in later stages.
        score = min(1.0, 0.68 * min(edge_density / 0.18, 1.0) + 0.32 * dark_ratio)
        return FrameAnalysis(str(image_path), width, height, edge_density,
                             dark_ratio, score, score >= self.threshold)

    def analyze_many(self, image_paths):
        return [self.analyze(Path(path)) for path in image_paths]


def write_report(results, destination: Path) -> None:
    import json
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
