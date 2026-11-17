"""Small, dependency-free models used by the language registry."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class LanguageProfile:
    """Recognition hints for a programming language.

    This is metadata only; parser, OCR, and reconstruction engines are kept
    separate so adding a profile cannot change the existing C# pipeline.
    """

    language_id: str
    display_name: str
    extensions: Tuple[str, ...]
    keywords: Tuple[str, ...] = ()
    patterns: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LanguageMatch:
    """A language guess with a normalized confidence and readable evidence."""

    profile: LanguageProfile
    confidence: float
    evidence: Tuple[str, ...]
