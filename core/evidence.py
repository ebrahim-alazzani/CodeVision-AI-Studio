"""Evidence and observation domain models for multimodal CodeVision events.

These models are deliberately independent of OCR, audio, and vision libraries.
They retain provenance so each reconstructed result can be reviewed against its
source media and time range.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class EvidenceModality(str, Enum):
    VIDEO_FRAME = "video_frame"
    IMAGE_REGION = "image_region"
    OCR_TEXT = "ocr_text"
    AUDIO_SEGMENT = "audio_segment"
    TRANSCRIPT = "transcript"
    CODE = "code"


@dataclass(frozen=True)
class BoundingBox:
    """Rectangle in source-image pixels, represented as x/y/width/height."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ValueError("bounding-box coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("bounding-box dimensions must be positive")


@dataclass(frozen=True)
class Evidence:
    """One piece of source-backed evidence supporting an observation."""

    modality: EvidenceModality
    source_path: str
    timestamp_start_sec: float
    timestamp_end_sec: Optional[float] = None
    confidence: Optional[float] = None
    text: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_path.strip():
            raise ValueError("source_path must not be empty")
        if self.timestamp_start_sec < 0:
            raise ValueError("timestamp_start_sec must be non-negative")
        if (self.timestamp_end_sec is not None and
                self.timestamp_end_sec < self.timestamp_start_sec):
            raise ValueError("timestamp_end_sec must not precede its start")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class Observation:
    """A time-bounded event inferred from one or more media evidence items."""

    video_id: str
    timestamp_start_sec: float
    timestamp_end_sec: Optional[float] = None
    observation_id: str = field(default_factory=lambda: str(uuid4()))
    language_id: Optional[str] = None
    evidence: List[Evidence] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.video_id.strip():
            raise ValueError("video_id must not be empty")
        if self.timestamp_start_sec < 0:
            raise ValueError("timestamp_start_sec must be non-negative")
        if (self.timestamp_end_sec is not None and
                self.timestamp_end_sec < self.timestamp_start_sec):
            raise ValueError("timestamp_end_sec must not precede its start")
        if not self.language_id:
            return
        self.language_id = self.language_id.strip().lower() or None

    def add_evidence(self, item: Evidence) -> None:
        """Attach evidence for the same video time span."""
        if self.timestamp_end_sec is not None and item.timestamp_start_sec > self.timestamp_end_sec:
            raise ValueError("evidence starts after the observation ends")
        if item.timestamp_end_sec is not None and item.timestamp_end_sec < self.timestamp_start_sec:
            raise ValueError("evidence ends before the observation starts")
        self.evidence.append(item)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-compatible representation for persistence and APIs."""
        return {
            "observation_id": self.observation_id,
            "video_id": self.video_id,
            "timestamp_start_sec": self.timestamp_start_sec,
            "timestamp_end_sec": self.timestamp_end_sec,
            "language_id": self.language_id,
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "modality": item.modality.value,
                    "source_path": item.source_path,
                    "timestamp_start_sec": item.timestamp_start_sec,
                    "timestamp_end_sec": item.timestamp_end_sec,
                    "confidence": item.confidence,
                    "text": item.text,
                    "bounding_box": ({
                        "x": item.bounding_box.x,
                        "y": item.bounding_box.y,
                        "width": item.bounding_box.width,
                        "height": item.bounding_box.height,
                    } if item.bounding_box else None),
                    "metadata": item.metadata,
                }
                for item in self.evidence
            ],
            "attributes": self.attributes,
        }
