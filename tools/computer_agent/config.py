"""
Desktop AI Agent - Configuration
================================
Supports Local Ollama (Qwen 2.5 Coder) as the default engine,
with optional Cloud fallback.
"""

import os

# ----------------------------------------------------
# 🧠 AI Brain Engine Selection
# ----------------------------------------------------
# Options: "ollama" (100% Local & Offline) | "gemini" (Cloud Vision)
AI_BACKEND = os.environ.get("AI_BACKEND", "ollama")

# ----------------------------------------------------
# 💻 Local Ollama Settings (Default)
# ----------------------------------------------------
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder-7b:latest")

# ----------------------------------------------------
# ☁️ Cloud Gemini Settings (Optional Backup)
# ----------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.5-pro",
]

# ----------------------------------------------------
# 📸 Screen Capture Settings
# ----------------------------------------------------
SCREENSHOT_MAX_WIDTH = 1280
SCREENSHOT_MAX_HEIGHT = 800
SCREENSHOT_QUALITY = 75

# ----------------------------------------------------
# 🖱️ Execution & Speed Settings (Turbo Responsive)
# ----------------------------------------------------
ACTION_DELAY = 0.08      # Snappy delay after each action (seconds)
TYPE_INTERVAL = 0.005    # Fast typing interval
MAX_STEPS = 25           # Maximum action loop steps per task

# ----------------------------------------------------
# 📂 File Paths
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
