"""
إعدادات وكيل الكمبيوتر - Computer Agent Configuration
=====================================================
"""

import os

# ──────────────────────────────────────────────
# 🔑  مفتاح الـ API
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# النماذج المفضلة حسب التوفر (يتم التبديل تلقائياً في حال انشغال أحدها)
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

# ──────────────────────────────────────────────
# 📸  إعدادات لقطة الشاشة
# ──────────────────────────────────────────────
SCREENSHOT_MAX_WIDTH = 1280
SCREENSHOT_MAX_HEIGHT = 800
SCREENSHOT_QUALITY = 70

# ──────────────────────────────────────────────
# 🖱️  إعدادات التنفيذ
# ──────────────────────────────────────────────
ACTION_DELAY = 0.5
TYPE_INTERVAL = 0.03
MAX_STEPS = 25

# ──────────────────────────────────────────────
# 📂  مسارات الملفات
# ──────────────────────────────────────────────
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(AGENT_DIR, "screenshots")
LOGS_DIR = os.path.join(AGENT_DIR, "logs")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
