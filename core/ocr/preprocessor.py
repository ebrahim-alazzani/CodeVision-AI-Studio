"""
CodeVision OCR Preprocessor and Code Heuristics Engine.

Handles:
1. Statistical code editor gutter line number detection and stripping
   ("1 |", "23:", "  4 ") without damaging actual code statements.
2. Shell and REPL prompt prefix cleaning ($, #, >>>, In [1]:).
3. Programming syntax glyph repairs and keyword OCR confusion fixes.
4. Dark-theme edge luminance calculation and background inversion
   (turning dark themes like VS Code / PyCharm / Visual Studio into high-contrast
   dark-on-light text for optimal OCR accuracy).
5. Contrast boosting, bicubic upscaling for small punctuation, and adaptive thresholding.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class PreprocessResult:
    """Result of image preprocessing for OCR."""
    image: np.ndarray
    is_dark_theme: bool
    background_luminance: float
    original_size: Tuple[int, int]   # (width, height)
    processed_size: Tuple[int, int]  # (width, height)
    scale_factor: float


class CodeHeuristics:
    """
    Code heuristics for cleaning OCR output text, stripping editor gutter line numbers,
    removing terminal/REPL prompts, and repairing common programming OCR glyph corruptions.
    """

    # Common OCR typo patterns in programming keywords and symbols
    KEYWORD_CORRECTIONS: List[Tuple[re.Pattern, str]] = [
        # JavaScript / TypeScript / general
        (re.compile(r'\bc[o0O][nm]st\b'), 'const'),
        (re.compile(r'\bfuncti[o0]n\b'), 'function'),
        (re.compile(r'\bl[eé]t\b'), 'let'),
        (re.compile(r'^[\|!1]et\b', re.MULTILINE), 'let'),
        (re.compile(r'^[\|!1]mport\b', re.MULTILINE), 'import'),
        (re.compile(r'\bimpor[t7]\b'), 'import'),
        (re.compile(r'\bre[t7]urn\b'), 'return'),
        (re.compile(r'\b[a@]sync\b'), 'async'),
        (re.compile(r'\bawa[i1]t\b'), 'await'),
        (re.compile(r'\bint[e3]rface\b'), 'interface'),
        (re.compile(r'\bstr[uü]ct\b'), 'struct'),
        (re.compile(r'\bpackag[e3]\b'), 'package'),

        # C# / Unity / OOP
        (re.compile(r'\bpubl[i1]c\b'), 'public'),
        (re.compile(r'\bpr[i1]vate\b'), 'private'),
        (re.compile(r'\bprot[e3]cted\b'), 'protected'),
        (re.compile(r'\bstat[i1]c\b'), 'static'),
        (re.compile(r'\bstr[i1]ng\b'), 'string'),
        (re.compile(r'\bvo[i1]d\b'), 'void'),
        (re.compile(r'\bMonoB[eé]hav[i1]our\b'), 'MonoBehaviour'),
        (re.compile(r'\bUn[i1]ty[eé]ng[i1]ne\b'), 'UnityEngine'),

        # SQL
        (re.compile(r'\bSE[L1]ECT\b'), 'SELECT'),
        (re.compile(r'\bFR[O0]M\b'), 'FROM'),
        (re.compile(r'\bWH[E3]RE\b'), 'WHERE'),
    ]

    @staticmethod
    def strip_gutter_line_numbers(lines: List[str]) -> List[str]:
        """
        Detect and strip column line numbers (gutters) found on code editors
        (e.g., "1 |", "23:", "  4 ") using statistical and sequence verification.

        Safeguards:
        - Avoids corrupting real code statements (e.g. "case 1:", "1 + 2", dictionary keys).
        - Requires a high proportion of matching lines or monotonic increasing sequence.
        """
        non_empty = [(idx, line) for idx, line in enumerate(lines) if line.strip()]
        if len(non_empty) < 2:
            return list(lines)

        # Gutter patterns: (compiled_regex, pattern_name)
        # Group 1 captures the number, and the pattern matches the delimiter and trailing space
        patterns = [
            # 1) Pipe: "1 | code", "12 |   code", "  1| code"
            (re.compile(r'^\s*(\d{1,5})\s*\|\s?'), 'pipe'),
            # 2) Colon: "1: code", "01:   code", "  12: code"
            (re.compile(r'^\s*(\d{1,5})\s*:\s?'), 'colon'),
            # 3) Bare number with at least 2 trailing spaces: "1   code", " 23    int x"
            (re.compile(r'^\s*(\d{1,5})\s{2,}'), 'bare'),
            # 4) Angle bracket: "1 > code", "12 > code"
            (re.compile(r'^\s*(\d{1,5})\s*>\s?'), 'arrow'),
            # 5) Dot numbered: "1. code", "02. class"
            (re.compile(r'^\s*(\d{1,5})\.\s+'), 'dot'),
        ]

        total_non_empty = len(non_empty)

        for pat, pat_name in patterns:
            matched_indices = []
            extracted_numbers = []

            for idx, line in non_empty:
                m = pat.match(line)
                if m:
                    matched_indices.append(idx)
                    try:
                        extracted_numbers.append(int(m.group(1)))
                    except ValueError:
                        pass

            if not matched_indices or len(matched_indices) < 2:
                continue

            match_ratio = len(matched_indices) / total_non_empty

            # Check for monotonicity: editor line numbers are strictly increasing
            is_monotonic = False
            if len(extracted_numbers) >= 2:
                increases = sum(
                    1 for i in range(len(extracted_numbers) - 1)
                    if extracted_numbers[i + 1] > extracted_numbers[i]
                )
                monotonic_ratio = increases / (len(extracted_numbers) - 1)
                is_monotonic = monotonic_ratio >= 0.75

            # Acceptance criteria:
            # - For pipe/arrow gutters, 35% match or monotonic is sufficient (pipes rarely appear at line start in code).
            # - For colon/bare/dot, require higher threshold or monotonicity to avoid false positives with labels/cases.
            is_valid_gutter = False
            if pat_name in ('pipe', 'arrow'):
                if match_ratio >= 0.35 or (is_monotonic and len(matched_indices) >= 2):
                    is_valid_gutter = True
            elif pat_name == 'colon':
                # Beware of "case 1:", "default:", labels
                # If monotonic numbers, it is genuinely a gutter!
                if is_monotonic and (match_ratio >= 0.35 or len(matched_indices) >= 3):
                    is_valid_gutter = True
                elif match_ratio >= 0.50 and is_monotonic:
                    is_valid_gutter = True
            elif pat_name in ('bare', 'dot'):
                if is_monotonic and (match_ratio >= 0.40 or len(matched_indices) >= 3):
                    is_valid_gutter = True

            if is_valid_gutter:
                # Strip gutter from all matching lines, preserving any indent that followed the delimiter
                result = list(lines)
                for i in range(len(result)):
                    result[i] = pat.sub('', result[i])
                return result

        return list(lines)

    @staticmethod
    def strip_prompt_prefixes(lines: List[str]) -> List[str]:
        """
        Strip terminal, PowerShell, and REPL prompt prefixes while preserving
        code indentation that follows the prompt.
        """
        result = []
        for line in lines:
            # Multi-character prompts first
            # Python REPL: >>> or ... (strip prompt and at most one trailing space)
            cleaned = re.sub(r'^(\s*)>>>\s?', r'\1', line)
            cleaned = re.sub(r'^(\s*)\.\.\.\s?', r'\1', cleaned)
            # IPython / Jupyter: In [1]: or Out[1]:
            cleaned = re.sub(r'^(\s*)In\s*\[\d+\]:\s?', r'\1', cleaned)
            cleaned = re.sub(r'^(\s*)Out\s*\[\d+\]:\s?', r'\1', cleaned)
            # PowerShell: PS C:\...>
            cleaned = re.sub(r'^(\s*)PS\s+[A-Za-z]:\\[^>]*>\s?', r'\1', cleaned)
            # Shell / Bash: $, #, >, » (strip prompt and at most one trailing space)
            cleaned = re.sub(r'^(\s*)[$#>»]\s?', r'\1', cleaned)
            result.append(cleaned)
        return result

    @classmethod
    def repair_code_glyphs(cls, text: str) -> str:
        """
        Normalize smart quotes, repair arrow operators, and fix common OCR keyword misreadings.
        """
        repaired = text

        # 1. Normalize smart quotes to standard ASCII quotes
        repaired = re.sub(r'[“”„‟«»]', '"', repaired)
        repaired = re.sub(r'[‘’‚‛`]', lambda m: '`' if m.group(0) == '`' else "'", repaired)
        repaired = re.sub(r'[—–]', '-', repaired)  # em-dash and en-dash to hyphen

        # 2. Fix common OCR spacing artifacts in arrow and comparison operators
        repaired = re.sub(r'=\s*>', '=>', repaired)
        repaired = re.sub(r'-\s*>', '->', repaired)
        repaired = re.sub(r'<\s*=', '<=', repaired)
        repaired = re.sub(r'>\s*=', '>=', repaired)
        repaired = re.sub(r'!\s*=', '!=', repaired)
        repaired = re.sub(r'=\s*=\s*=', '===', repaired)
        repaired = re.sub(r'=\s*=', '==', repaired)

        # 3. Fix bracket spacing artifacts
        repaired = re.sub(r'\{\s*\}', '{}', repaired)
        repaired = re.sub(r'\(\s*\)', '()', repaired)
        repaired = re.sub(r'\[\s*\]', '[]', repaired)

        # 4. Fix keyword misreadings
        for pattern, replacement in cls.KEYWORD_CORRECTIONS:
            repaired = pattern.sub(replacement, repaired)

        return repaired

    @classmethod
    def clean_code_lines(
        cls,
        raw_lines: List[str],
        strip_gutters: bool = True,
        strip_prompts: bool = True,
        repair_glyphs: bool = True
    ) -> List[str]:
        """Run full heuristics cleaning pipeline on lines of code."""
        lines = list(raw_lines)

        if repair_glyphs:
            lines = [cls.repair_code_glyphs(l) for l in lines]

        if strip_gutters:
            lines = cls.strip_gutter_line_numbers(lines)

        if strip_prompts:
            lines = cls.strip_prompt_prefixes(lines)

        # Trim trailing whitespace
        lines = [l.rstrip() for l in lines]
        return lines


class ImagePreprocessor:
    """
    Image preprocessing pipeline tailored for code snippet OCR.
    
    Provides:
    - Background luminance estimation via edge border sampling.
    - Dark-theme detection and inversion (dark-on-light text for Tesseract).
    - Parametric contrast boosting and bicubic resolution upscaling.
    - Adaptive thresholding for crisp code syntax boundaries.
    """

    @staticmethod
    def calculate_background_luminance(
        image: Union[np.ndarray, "Image.Image", str, Path],
        sample_count: int = 60
    ) -> float:
        """
        Calculate relative background luminance by sampling the four outer image borders.
        
        Returns:
            Float between 0.0 (pitch black) and 1.0 (pure white).
        """
        arr = ImagePreprocessor._to_grayscale_numpy(image)
        h, w = arr.shape[:2]
        if h == 0 or w == 0:
            return 0.5

        samples = []

        # Sample top and bottom borders (inward 3 pixels to avoid window chrome artifacts)
        top_y = min(h - 1, 3)
        bot_y = max(0, h - 4)
        for i in range(sample_count):
            x = int(math.floor((w * i) / sample_count))
            samples.append(float(arr[top_y, x]))
            samples.append(float(arr[bot_y, x]))

        # Sample left and right borders
        left_x = min(w - 1, 3)
        right_x = max(0, w - 4)
        for j in range(sample_count):
            y = int(math.floor((h * j) / sample_count))
            samples.append(float(arr[y, left_x]))
            samples.append(float(arr[y, right_x]))

        if not samples:
            return 0.5

        # Median/mean border luminance normalized to [0.0, 1.0]
        mean_lum = sum(samples) / (len(samples) * 255.0)
        return float(mean_lum)

    @staticmethod
    def is_dark_theme(
        image: Union[np.ndarray, "Image.Image", str, Path],
        threshold: float = 0.50
    ) -> bool:
        """Returns True if the image is detected as a dark-theme editor."""
        lum = ImagePreprocessor.calculate_background_luminance(image)
        return lum < threshold

    @classmethod
    def preprocess_code_image(
        cls,
        image: Union[np.ndarray, "Image.Image", str, Path],
        invert_dark_theme: bool = True,
        contrast_boost: float = 0.30,
        scale_factor: float = 2.0,
        binarize: bool = False,
        sharpen: bool = True
    ) -> PreprocessResult:
        """
        Preprocess code screenshot / video frame for optimal OCR reading.

        Steps:
        1. Convert to grayscale.
        2. Sample edge luminance and detect dark theme (VS Code / PyCharm / Visual Studio).
        3. Invert if dark theme so text is dark on white background.
        4. Upscale using bicubic interpolation for small punctuation clarity.
        5. Apply contrast boost.
        6. Apply optional sharpening or binarization.

        Args:
            image: Input image (np.ndarray, PIL Image, or file path).
            invert_dark_theme: If True, inverts dark background to light.
            contrast_boost: Contrast enhancement factor (0.0 to 1.0).
            scale_factor: Resolution scale factor (default 2.0).
            binarize: If True, applies adaptive/Otsu thresholding.
            sharpen: If True, applies unsharp mask kernel.

        Returns:
            PreprocessResult containing processed numpy image and metadata.
        """
        gray = cls._to_grayscale_numpy(image)
        orig_h, orig_w = gray.shape[:2]

        # 1. Edge luminance detection
        bg_lum = cls.calculate_background_luminance(gray)
        is_dark = bg_lum < 0.50

        # 2. Inversion for dark theme
        should_invert = is_dark and invert_dark_theme
        if should_invert:
            gray = 255 - gray

        # 3. High-resolution scaling (bicubic)
        target_w = max(1, int(round(orig_w * scale_factor)))
        target_h = max(1, int(round(orig_h * scale_factor)))

        if scale_factor != 1.0:
            if HAS_CV2:
                scaled = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
            elif HAS_PIL:
                pil_img = Image.fromarray(gray)
                scaled_pil = pil_img.resize((target_w, target_h), Image.Resampling.BICUBIC)
                scaled = np.array(scaled_pil, dtype=np.uint8)
            else:
                scaled = gray
        else:
            scaled = gray

        # 4. Contrast enhancement
        # Sigmoid-like contrast transfer factor:
        # factor = (259 * (contrast_boost * 255 + 255)) / (255 * (259 - contrast_boost * 255))
        c_boost = max(0.0, min(0.99, contrast_boost))
        factor = (259.0 * (c_boost * 255.0 + 255.0)) / (255.0 * (259.0 - c_boost * 255.0))
        enhanced = factor * (scaled.astype(np.float32) - 128.0) + 128.0
        enhanced = np.clip(enhanced, 0.0, 255.0).astype(np.uint8)

        # 5. Punctuation sharpening
        if sharpen and not binarize:
            if HAS_CV2:
                # Mild unsharp mask kernel to bring out dots, colons, brackets
                kernel = np.array([
                    [ 0, -0.5,  0],
                    [-0.5, 3.0, -0.5],
                    [ 0, -0.5,  0]
                ], dtype=np.float32)
                enhanced = cv2.filter2D(enhanced, -1, kernel)
                enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            elif HAS_PIL:
                pil_img = Image.fromarray(enhanced)
                enhanced_pil = pil_img.filter(ImageFilter.SHARPEN)
                enhanced = np.array(enhanced_pil, dtype=np.uint8)

        # 6. Binarization (optional)
        if binarize:
            if HAS_CV2:
                _, enhanced = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:
                # Manual Otsu threshold
                enhanced = (enhanced > 140).astype(np.uint8) * 255

        return PreprocessResult(
            image=enhanced,
            is_dark_theme=is_dark,
            background_luminance=round(bg_lum, 4),
            original_size=(orig_w, orig_h),
            processed_size=(target_w, target_h),
            scale_factor=scale_factor
        )

    @staticmethod
    def _to_grayscale_numpy(image: Union[np.ndarray, "Image.Image", str, Path]) -> np.ndarray:
        """Convert input image from various formats to a 2D uint8 numpy grayscale array."""
        if isinstance(image, (str, Path)):
            p = str(image)
            if HAS_CV2:
                mat = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
                if mat is not None:
                    return mat
            if HAS_PIL:
                with Image.open(p) as img:
                    return np.array(img.convert('L'), dtype=np.uint8)
            raise ValueError(f"Could not load image from path: {p}")

        if HAS_PIL and isinstance(image, Image.Image):
            return np.array(image.convert('L'), dtype=np.uint8)

        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                return image.astype(np.uint8)
            elif image.ndim == 3:
                channels = image.shape[2]
                if channels == 1:
                    return image[:, :, 0].astype(np.uint8)
                elif channels == 3:
                    if HAS_CV2:
                        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    else:
                        # Standard sRGB relative luminance weights
                        r = image[:, :, 0].astype(np.float32)
                        g = image[:, :, 1].astype(np.float32)
                        b = image[:, :, 2].astype(np.float32)
                        gray = 0.299 * r + 0.587 * g + 0.114 * b
                        return np.clip(gray, 0, 255).astype(np.uint8)
                elif channels == 4:
                    if HAS_CV2:
                        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
                    else:
                        r = image[:, :, 0].astype(np.float32)
                        g = image[:, :, 1].astype(np.float32)
                        b = image[:, :, 2].astype(np.float32)
                        gray = 0.299 * r + 0.587 * g + 0.114 * b
                        return np.clip(gray, 0, 255).astype(np.uint8)

        raise TypeError(f"Unsupported image type: {type(image)}")
