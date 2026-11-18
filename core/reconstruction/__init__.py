# CodeVision Extractor — Code Reconstruction Layer
import sys
from pathlib import Path

_core_dir = Path(__file__).resolve().parent.parent
_root_dir = _core_dir.parent
for p in [str(_core_dir), str(_root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.reconstruction.ace_aligner import ACEAligner, LineObservation, DocumentLine

__all__ = [
    "ACEAligner",
    "LineObservation",
    "DocumentLine",
]
