"""Extensible language profile registry and conservative source detector."""

import re
from pathlib import PurePath
from typing import Dict, Iterable, List, Optional, Tuple

from .models import LanguageMatch, LanguageProfile


class LanguageRegistry:
    """Register language metadata and identify source files without guessing.

    Extension matches are used when unambiguous. For ambiguous extensions
    (for example ``.h``), source evidence is required to choose a language.
    Content detection is intentionally heuristic; it is not a parser.
    """

    def __init__(self, profiles: Iterable[LanguageProfile] = ()) -> None:
        self._profiles: Dict[str, LanguageProfile] = {}
        for profile in profiles:
            self.register(profile)

    @property
    def profiles(self) -> Tuple[LanguageProfile, ...]:
        return tuple(self._profiles.values())

    def register(self, profile: LanguageProfile) -> None:
        key = profile.language_id.strip().lower()
        if not key:
            raise ValueError("language_id must not be empty")
        if key in self._profiles:
            raise ValueError("language already registered: " + key)
        normalized = tuple(sorted({
            ext.lower() if ext.startswith(".") else "." + ext.lower()
            for ext in profile.extensions if ext.strip()
        }))
        if not normalized:
            raise ValueError("a language profile must define at least one extension")
        self._profiles[key] = LanguageProfile(
            language_id=key,
            display_name=profile.display_name.strip() or key,
            extensions=normalized,
            keywords=tuple(k.lower() for k in profile.keywords if k.strip()),
            patterns=profile.patterns,
        )

    def get(self, language_id: str) -> Optional[LanguageProfile]:
        return self._profiles.get(language_id.strip().lower())

    def detect(self, filename: Optional[str] = None,
               source: str = "") -> Optional[LanguageMatch]:
        """Return the strongest match, or ``None`` when evidence is weak/tied."""
        suffix = PurePath(filename or "").suffix.lower()
        ext_profiles = [p for p in self._profiles.values() if suffix in p.extensions]
        scored: List[Tuple[float, LanguageProfile, List[str]]] = []

        for profile in self._profiles.values():
            score = 0.0
            evidence: List[str] = []
            if suffix and suffix in profile.extensions:
                score += 0.95 if len(ext_profiles) == 1 else 0.18
                evidence.append("extension:" + suffix)
            src = source.lower()
            for keyword in profile.keywords:
                if re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", src):
                    score += 0.10
                    evidence.append("keyword:" + keyword)
            for pattern in profile.patterns:
                if re.search(pattern, source, re.MULTILINE):
                    score += 0.18
                    evidence.append("pattern:" + pattern)
            if evidence:
                scored.append((min(score, 0.99), profile, evidence))

        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored[0][0] < 0.25:
            return None
        if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.08:
            return None
        confidence, profile, evidence = scored[0]
        return LanguageMatch(profile, round(confidence, 3), tuple(evidence))

    def detect_extension(self, filename: str) -> Optional[LanguageMatch]:
        """Detect by extension only; ambiguous extensions deliberately abstain."""
        suffix = PurePath(filename).suffix.lower()
        matches = [p for p in self._profiles.values() if suffix in p.extensions]
        if len(matches) != 1:
            return None
        return LanguageMatch(matches[0], 0.95, ("extension:" + suffix,))
