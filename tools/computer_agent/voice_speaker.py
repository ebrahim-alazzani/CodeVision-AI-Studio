"""
Voice Speaker Module (Bilingual Neural & Offline TTS)
====================================================
Speaks naturally in Arabic and English using Edge-TTS (Natural Neural Voices),
with instant offline fallback to Windows SAPI (pyttsx3).
Non-blocking: Always speaks in background thread without freezing the GUI.
"""

import os
import re
import tempfile
import asyncio
import threading

_ENABLED = True
_LOCK = threading.Lock()


def is_arabic(text: str) -> bool:
    """Checks if text contains Arabic characters."""
    return bool(re.search(r"[\u0600-\u06FF]", text))


def speak(text: str):
    """Speaks the provided text asynchronously without blocking."""
    global _ENABLED
    if not _ENABLED or not text or not str(text).strip():
        return

    clean_text = str(text).strip()
    # Strip emojis and markdown
    clean_text = re.sub(r"[#*`_~]", "", clean_text)
    clean_text = re.sub(r"[^\w\s\u0600-\u06FF.,!?:-]", "", clean_text).strip()
    if not clean_text:
        return

    threading.Thread(target=_speak_worker, args=(clean_text,), daemon=True).start()


def _speak_worker(text: str):
    with _LOCK:
        # 1. Try High Quality Edge-TTS
        try:
            import edge_tts
            import pygame

            voice = "ar-SA-HamedNeural" if is_arabic(text) else "en-US-ChristopherNeural"
            temp_path = os.path.join(tempfile.gettempdir(), f"cyberpro_voice_{os.getpid()}.mp3")

            async def _generate():
                comm = edge_tts.Communicate(text, voice)
                await comm.save(temp_path)

            asyncio.run(_generate())

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                try:
                    pygame.mixer.music.unload()
                    os.remove(temp_path)
                except Exception:
                    pass
                return
        except Exception:
            pass

        # 2. Offline Fallback via pyttsx3 (SAPI5)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 165)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass


def set_voice_enabled(enabled: bool):
    global _ENABLED
    _ENABLED = enabled


def is_voice_enabled() -> bool:
    return _ENABLED
