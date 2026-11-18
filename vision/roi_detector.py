"""
CodeVision Phase 3: Automated Code Editor ROI & Viewport Detector.

Detects code editor viewports, excludes taskbars, window chrome, and webcam
picture-in-picture (PiP), producing an accurate bounding box for OCR ingestion.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class CodeRegion:
    x: int
    y: int
    w: int
    h: int
    category: str  # "code_editor", "terminal", "browser", "slide", "webcam"
    confidence: float
    is_dark_theme: bool

    @property
    def box(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ROIReport:
    frame_width: int
    frame_height: int
    primary_code_roi: Tuple[int, int, int, int]
    category: str
    confidence: float
    is_dark_theme: bool
    webcam_roi: Optional[Tuple[int, int, int, int]] = None
    all_regions: List[CodeRegion] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.all_regions:
            data["all_regions"] = [r.to_dict() if isinstance(r, CodeRegion) else r for r in self.all_regions]
        return data


class CodeROIDetector:
    """
    Intelligent viewport detection for programming videos.
    Identifies active code editor boundaries, masks webcam overlays,
    and crops out irrelevant operating system elements (taskbars, title bars).
    """

    def __init__(
        self,
        min_editor_area_ratio: float = 0.20,
        max_webcam_area_ratio: float = 0.18,
        min_code_edge_density: float = 0.015,
    ):
        self.min_editor_area_ratio = min_editor_area_ratio
        self.max_webcam_area_ratio = max_webcam_area_ratio
        self.min_code_edge_density = min_code_edge_density

    def detect(self, image_or_path: Union[str, Path, np.ndarray]) -> ROIReport:
        import cv2

        if isinstance(image_or_path, (str, Path)):
            img = cv2.imread(str(image_or_path))
            if img is None:
                raise ValueError(f"Failed to load image from: {image_or_path}")
        else:
            img = image_or_path

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

        # 1. Dark theme detection
        mean_lum = float(gray.mean())
        is_dark_theme = mean_lum < 115.0

        # 2. Check for Webcam PiP in corners
        webcam_roi = self._detect_webcam_pip(img, gray, w, h)

        # 3. Code Line Structure Detection (Horizontal morphology)
        # Edges of code text lines form repeated horizontal clusters
        edges = cv2.Canny(gray, 40, 140)
        
        # Mask out webcam area from edge calculation if found
        if webcam_roi:
            wx, wy, ww, wh = webcam_roi
            edges[wy : wy + wh, wx : wx + ww] = 0

        # Horizontal kernel connects characters into code lines
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        line_bands = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_h)

        # Vertical kernel groups adjacent lines into unified editor blocks (typical line spacing 18-35px)
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
        code_blocks = cv2.morphologyEx(line_bands, cv2.MORPH_DILATE, kernel_v)

        # 4. Find large contours representing editor panes
        contours, _ = cv2.findContours(code_blocks, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidate_boxes = []
        total_frame_area = w * h

        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            bounding_area = bw * bh
            # Filter out tiny noise and thin vertical separator lines
            if bounding_area < (total_frame_area * 0.03):
                continue
            if bw > 120 and bh > 100:
                candidate_boxes.append((x, y, bw, bh))

        # 5. Determine primary code ROI
        if candidate_boxes:
            # Union of candidate text blocks gives the active code viewport
            min_x = min(b[0] for b in candidate_boxes)
            min_y = min(b[1] for b in candidate_boxes)
            max_x = max(b[0] + b[2] for b in candidate_boxes)
            max_y = max(b[1] + b[3] for b in candidate_boxes)

            # Pad slightly while staying within frame bounds
            pad_x = 12
            pad_y = 12
            fx = max(0, min_x - pad_x)
            fy = max(0, min_y - pad_y)
            fw = min(w - fx, (max_x - min_x) + (2 * pad_x))
            fh = min(h - fy, (max_y - min_y) + (2 * pad_y))

            # Exclude taskbar (bottom 48px if close to bottom)
            if (fy + fh) > (h - 55) and fy < (h - 200):
                fh = (h - 55) - fy

            # Exclude window title bar (top 35px if starts at 0)
            if fy < 38 and fh > 200:
                fy = 35
                fh = fh - 35

            editor_box = (int(fx), int(fy), int(fw), int(fh))
        else:
            # Fallback to standard 16:9 safe zone (strip title bar 38px, taskbar 50px)
            top_bar = 38 if h > 600 else 0
            taskbar = 50 if h > 600 else 0
            editor_box = (0, top_bar, w, max(100, h - top_bar - taskbar))

        # 6. Compute real confidence based on edge density and text line regularity
        ex, ey, ew, eh = editor_box
        roi_edges = edges[ey : ey + eh, ex : ex + ew]
        edge_dens = float((roi_edges > 0).mean()) if roi_edges.size > 0 else 0.0
        
        # Categorize
        if edge_dens >= self.min_code_edge_density and ew > (w * 0.25):
            category = "code_editor"
            confidence = min(0.99, max(0.55, 0.40 + (edge_dens * 15.0)))
        elif mean_lum > 200.0:
            category = "slide"
            confidence = 0.75
        elif mean_lum < 40.0 and edge_dens < 0.008:
            category = "terminal"
            confidence = 0.70
        else:
            category = "code_editor" if is_dark_theme else "browser"
            confidence = 0.65

        primary_region = CodeRegion(
            x=editor_box[0],
            y=editor_box[1],
            w=editor_box[2],
            h=editor_box[3],
            category=category,
            confidence=round(confidence, 3),
            is_dark_theme=is_dark_theme,
        )

        all_regions = [primary_region]
        if webcam_roi:
            all_regions.append(
                CodeRegion(
                    x=webcam_roi[0],
                    y=webcam_roi[1],
                    w=webcam_roi[2],
                    h=webcam_roi[3],
                    category="webcam",
                    confidence=0.88,
                    is_dark_theme=False,
                )
            )

        return ROIReport(
            frame_width=w,
            frame_height=h,
            primary_code_roi=editor_box,
            category=category,
            confidence=round(confidence, 3),
            is_dark_theme=is_dark_theme,
            webcam_roi=webcam_roi,
            all_regions=all_regions,
        )

    def _detect_webcam_pip(
        self, img: np.ndarray, gray: np.ndarray, w: int, h: int
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Detects corner webcam PiP (talking head) overlay.
        Checks bottom-right, bottom-left, top-right corners.
        """
        import cv2

        total_area = w * h
        max_area = total_area * self.max_webcam_area_ratio
        min_area = total_area * 0.02

        corners = [
            ("bottom_right", int(w * 0.65), int(h * 0.55), w, h),
            ("bottom_left", 0, int(h * 0.55), int(w * 0.35), h),
            ("top_right", int(w * 0.65), 0, w, int(h * 0.45)),
        ]

        for _, cx1, cy1, cx2, cy2 in corners:
            corner_bgr = img[cy1:cy2, cx1:cx2]
            if corner_bgr.size == 0:
                continue

            # Convert to HSV to detect skin tones / face region
            hsv = cv2.cvtColor(corner_bgr, cv2.COLOR_BGR2HSV)
            # Typical human skin tone range in HSV
            skin_mask = cv2.inRange(hsv, np.array([0, 28, 50]), np.array([25, 255, 255]))
            skin_ratio = float((skin_mask > 0).mean())

            # Detect box-like borders in this corner
            corner_gray = gray[cy1:cy2, cx1:cx2]
            edges = cv2.Canny(corner_gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area <= area <= max_area:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    aspect = bw / float(bh)
                    # PiP webcams usually have aspect ratio 4:3 (1.33) or 16:9 (1.77) or 1:1
                    if 0.75 <= aspect <= 1.85:
                        # If significant skin tone or high color variance inside this box
                        box_skin = skin_mask[y : y + bh, x : x + bw]
                        box_skin_ratio = float((box_skin > 0).mean()) if box_skin.size > 0 else 0
                        if box_skin_ratio > 0.08 or skin_ratio > 0.12:
                            return (cx1 + x, cy1 + y, bw, bh)

        return None

    def crop_editor_roi(
        self, img: np.ndarray, report: ROIReport, mask_webcam: bool = True
    ) -> np.ndarray:
        """
        Crops image to primary editor ROI and optionally masks out webcam with neutral background color.
        """
        x, y, w, h = report.primary_code_roi
        cropped = img[y : y + h, x : x + w].copy()

        if mask_webcam and report.webcam_roi:
            wx, wy, ww, wh = report.webcam_roi
            # Convert webcam coordinates relative to cropped region
            rel_wx = wx - x
            rel_wy = wy - y
            # Check if webcam overlaps with the cropped area
            if (
                rel_wx < w
                and rel_wy < h
                and (rel_wx + ww) > 0
                and (rel_wy + wh) > 0
            ):
                rx1 = max(0, rel_wx)
                ry1 = max(0, rel_wy)
                rx2 = min(w, rel_wx + ww)
                ry2 = min(h, rel_wy + wh)
                # Fill with neutral background color
                fill_color = (25, 25, 25) if report.is_dark_theme else (240, 240, 240)
                cropped[ry1:ry2, rx1:rx2] = fill_color

        return cropped
