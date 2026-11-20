"""
CodeVision Phase 4: Code Token Normalizer & OCR Error Repair Engine.

Specialized for programming tutorials. Repairs broken operators, restores corrupted
reserved keywords (Flutter/Dart, Python, TypeScript, C#, C++, Rust), normalizes glyph
confusions (0 vs O, l vs 1 vs |), strips line number gutters, and computes CER/WER.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class NormalizationResult:
    cleaned_code: str
    repaired_lines: List[str]
    num_replacements: int
    modifications: List[str]


def compute_levenshtein(s1: str, s2: str) -> int:
    """Computes exact Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0, v1 = v1, [0] * (len(s2) + 1)

    return v0[len(s2)]


def compute_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate (CER): Levenshtein distance divided by reference length."""
    ref_len = len(reference)
    if ref_len == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0
    dist = compute_levenshtein(reference, hypothesis)
    return min(1.0, dist / float(ref_len))


def compute_wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate (WER): Levenshtein distance over words divided by reference word count."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    return min(1.0, dp[n][m] / float(n))


class CodeTokenNormalizer:
    """
    Intelligent code-specific OCR repair engine.
    Targets real coding syntax artifacts across 7 languages.
    """

    # Common multi-character operators often fractured by OCR
    OPERATOR_FIXES: List[Tuple[re.Pattern, str]] = [
        (re.compile(r'=\s*>'), '=>'),      # Arrow functions / lambdas
        (re.compile(r'-\s*>'), '->'),      # Member access / return type
        (re.compile(r':\s*:'), '::'),      # Scope resolution (C++, Rust)
        (re.compile(r'!\s*='), '!='),      # Inequality
        (re.compile(r'=\s*=\s*='), '==='),# Strict equality (JS/TS)
        (re.compile(r'=\s*='), '=='),      # Equality
        (re.compile(r'<\s*='), '<='),      # Less than or equal
        (re.compile(r'>\s*='), '>='),      # Greater than or equal
        (re.compile(r'&\s*&'), '&&'),      # Logical AND
        (re.compile(r'\|\s*\|'), '||'),    # Logical OR
        (re.compile(r'\?\s*\?'), '??'),    # Null-coalescing
        (re.compile(r'\+\s*='), '+='),    # Compound addition
        (re.compile(r'-\s*='), '-='),      # Compound subtraction
        (re.compile(r'\*\s*='), '*='),    # Compound multiplication
        (re.compile(r'/\s*='), '/='),      # Compound division
    ]

    # Smart quote and bracket glyph normalizations
    GLYPH_REPLACEMENTS = {
        '“': '"', '”': '"', '„': '"', '`': '`', '’': "'", '‘': "'",
        '—': '-', '–': '-', '…': '...',
        '【': '[', '】': ']', '（': '(', '）': ')', '｛': '{', '｝': '}',
    }

    # Keyword repair dictionary (corrupted OCR forms -> canonical keyword)
    KEYWORD_CORRECTIONS = {
        # Dart / Flutter
        r'\bWidqet\b': 'Widget',
        r'\bWldget\b': 'Widget',
        r'\bBuildcontext\b': 'BuildContext',
        r'\bBuildContex\b': 'BuildContext',
        r'@overr[l1i]de\b': '@override',
        r'@overide\b': '@override',
        r'\bStatelesswidqet\b': 'StatelessWidget',
        r'\bStatelessWidqet\b': 'StatelessWidget',
        r'\bStatefulwidqet\b': 'StatefulWidget',
        r'\bStatefulWidqet\b': 'StatefulWidget',
        r'\bEdgeinsets\b': 'EdgeInsets',
        r'\bMainAxisAlianment\b': 'MainAxisAlignment',
        r'\bCrossAxisAlianment\b': 'CrossAxisAlignment',
        
        # Python
        r'\bdet\s+([a-zA-Z_])': r'def \1',
        r'\bclacc\s+([a-zA-Z_])': r'class \1',
        r'\basyne\s+def\b': 'async def',
        r'\bawalt\b': 'await',
        r'\bretum\b': 'return',
        r'\bse1f\.': 'self.',
        
        # C# / Unity / C++
        r'\bMonoBehavlour\b': 'MonoBehaviour',
        r'\bMonoBehavoir\b': 'MonoBehaviour',
        r'\bUnityEnqine\b': 'UnityEngine',
        r'\bvold\s+([a-zA-Z_])': r'void \1',
        r'\bnamespaee\b': 'namespace',
        r'\bpubllc\b': 'public',
        r'\bprlvate\b': 'private',
        
        # Web / TypeScript / Rust
        r'\bconstt\b': 'const',
        r'\bfunctlon\b': 'function',
        r'\bintertace\b': 'interface',
        r'\bstrinq\b': 'string',
        r'\bpub\s+th\b': 'pub fn',
    }

    def __init__(self, strip_gutters: bool = True):
        self.strip_gutters = strip_gutters

    def normalize(self, code_text: str, language_hint: Optional[str] = None) -> NormalizationResult:
        """
        Processes multi-line code string, repairing OCR errors, quotes, operators, and line numbers.
        """
        if not code_text or not code_text.strip():
            return NormalizationResult(code_text, [], 0, [])

        modifications = []
        num_changes = 0

        # 1. Normalize smart quotes and unicode typography
        normalized_text = code_text
        for char, repl in self.GLYPH_REPLACEMENTS.items():
            if char in normalized_text:
                normalized_text = normalized_text.replace(char, repl)
                num_changes += 1
                modifications.append(f"Glyph replace: '{char}' -> '{repl}'")

        lines = normalized_text.splitlines()

        # 2. Strip line number gutters if present (e.g. "1 |", "02:", "12   ")
        if self.strip_gutters:
            lines, gutter_stripped = self._strip_line_number_gutters(lines)
            if gutter_stripped:
                modifications.append("Stripped IDE line number gutters")
                num_changes += 1

        repaired_lines = []
        for line in lines:
            repaired_line = line

            # 3. Repair fractured operators
            for pattern, repl in self.OPERATOR_FIXES:
                if pattern.search(repaired_line):
                    repaired_line = pattern.sub(repl, repaired_line)
                    num_changes += 1

            # 4. Repair corrupted keywords
            for pattern_str, repl in self.KEYWORD_CORRECTIONS.items():
                regex = re.compile(pattern_str, re.IGNORECASE if '@' not in pattern_str else 0)
                if regex.search(repaired_line):
                    repaired_line = regex.sub(repl, repaired_line)
                    num_changes += 1

            # 5. Fix hexadecimal numbers (e.g., 0xFF read as OxFF)
            repaired_line = re.sub(r'\b[Oo]x([0-9a-fA-F]+)\b', r'0x\1', repaired_line)

            # 6. Normalize trailing spaces
            repaired_line = repaired_line.rstrip()
            repaired_lines.append(repaired_line)

        cleaned_code = "\n".join(repaired_lines)
        return NormalizationResult(
            cleaned_code=cleaned_code,
            repaired_lines=repaired_lines,
            num_replacements=num_changes,
            modifications=modifications
        )

    def _strip_line_number_gutters(self, lines: List[str]) -> Tuple[List[str], bool]:
        """Detects whether >= 35% of non-empty lines start with line number patterns and strips them."""
        non_empty = [l for l in lines if l.strip()]
        if len(non_empty) < 2:
            return lines, False

        pipe_gutter = re.compile(r'^\s*\d{1,4}\s*\|\s?')
        colon_gutter = re.compile(r'^\s*\d{1,4}\s*:\s?')
        space_gutter = re.compile(r'^\s*\d{1,4}\s{2,}')

        pipe_cnt = sum(1 for l in non_empty if pipe_gutter.match(l))
        colon_cnt = sum(1 for l in non_empty if colon_gutter.match(l))
        space_cnt = sum(1 for l in non_empty if space_gutter.match(l))

        threshold = max(2, int(len(non_empty) * 0.35))
        if pipe_cnt >= threshold:
            return [pipe_gutter.sub('', l) for l in lines], True
        if colon_cnt >= threshold:
            return [colon_gutter.sub('', l) for l in lines], True
        if space_cnt >= threshold:
            return [space_gutter.sub('', l) for l in lines], True

        return lines, False
