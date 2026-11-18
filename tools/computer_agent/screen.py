"""
وحدة التقاط الشاشة - Screen Capture Module
=============================================
التقاط لقطة شاشة سريعة وتجهيزها للإرسال إلى النموذج.
تستخدم مكتبة mss (أسرع من pyautogui في الالتقاط).
"""

import io
import base64
import time
import os
from PIL import Image

from config import (
    SCREENSHOT_MAX_WIDTH,
    SCREENSHOT_MAX_HEIGHT,
    SCREENSHOT_QUALITY,
    SCREENSHOTS_DIR,
)


def capture_screenshot(save: bool = True) -> Image.Image:
    """
    التقاط لقطة شاشة كاملة وإرجاعها كصورة PIL.
    تُحفظ نسخة في مجلد screenshots إذا save=True.
    يجرب عدة طرق تلقائياً حسب البيئة.
    """
    img = None

    # الطريقة 1: mss (الأسرع)
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    except Exception:
        pass

    # الطريقة 2: pyautogui (أكثر توافقاً)
    if img is None:
        try:
            import pyautogui
            img = pyautogui.screenshot()
        except Exception:
            pass

    # الطريقة 3: Win32 API مباشرة عبر PIL.ImageGrab
    if img is None:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
        except Exception:
            pass

    # الطريقة 4: صورة فارغة كحل أخير (للاختبار)
    if img is None:
        try:
            import pyautogui
            w, h = pyautogui.size()
        except Exception:
            w, h = 1920, 1080
        img = Image.new("RGB", (w, h), (30, 30, 30))

    # تقليص الحجم مع الحفاظ على النسبة
    img.thumbnail((SCREENSHOT_MAX_WIDTH, SCREENSHOT_MAX_HEIGHT), Image.LANCZOS)

    if save:
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOTS_DIR, f"screen_{ts}.jpg")
        img.save(path, "JPEG", quality=SCREENSHOT_QUALITY)

    return img


def image_to_base64(img: Image.Image) -> str:
    """تحويل صورة PIL إلى سلسلة base64 بصيغة JPEG."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def image_to_bytes(img: Image.Image) -> bytes:
    """تحويل صورة PIL إلى بايتات JPEG خام."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
    return buf.getvalue()


if __name__ == "__main__":
    # اختبار سريع
    print("📸 التقاط لقطة شاشة...")
    screenshot = capture_screenshot()
    print(f"✅ تم! الحجم: {screenshot.size}")
    b64 = image_to_base64(screenshot)
    print(f"📦 حجم Base64: {len(b64):,} حرف")
