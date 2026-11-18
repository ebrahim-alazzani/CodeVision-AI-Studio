"""CodeVision automated tests."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_core = _root / "core"
for p in [str(_root), str(_core)]:
    if p not in sys.path:
        sys.path.insert(0, p)
