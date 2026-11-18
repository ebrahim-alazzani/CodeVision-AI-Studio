"""
Actions Module
==============
Executes physical keyboard, mouse, and system operations on Windows.
Includes key normalization, coordinate scaling, and safety failsafes.
"""

import subprocess
import time
import pyautogui
from config import ACTION_DELAY, TYPE_INTERVAL

# PyAutoGUI Safety configuration
pyautogui.FAILSAFE = True
pyautogui.PAUSE = ACTION_DELAY

# Common key aliases to prevent PyAutoGUI KeyError
KEY_ALIASES = {
    "win": "winleft",
    "windows": "winleft",
    "super": "winleft",
    "cmd": "winleft",
    "command": "winleft",
    "ctrl": "ctrlleft",
    "control": "ctrlleft",
    "alt": "altleft",
    "shift": "shiftleft",
    "return": "enter",
    "esc": "escape",
    "del": "delete",
    "ins": "insert",
}


def normalize_key(key_name: str) -> str:
    """Translates common key synonyms to valid PyAutoGUI keys."""
    k = str(key_name).strip().lower()
    return KEY_ALIASES.get(k, k)

# Known applications mapping
APP_COMMANDS = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "chrome": "start chrome --new-window \"https://www.google.com\"",
    "browser": "start chrome --new-window \"https://www.google.com\"",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
}


def get_screen_size() -> tuple[int, int]:
    """Returns actual display width and height."""
    try:
        return pyautogui.size()
    except Exception:
        return 1920, 1080


def scale_coordinates(x: int, y: int, ref_w: int = 1280, ref_h: int = 800) -> tuple[int, int]:
    """
    Scales coordinates if the model predicts based on downsampled perception.
    """
    screen_w, screen_h = get_screen_size()
    if x > screen_w or y > screen_h:
        scaled_x = int((x / ref_w) * screen_w)
        scaled_y = int((y / ref_h) * screen_h)
        return max(0, min(scaled_x, screen_w - 1)), max(0, min(scaled_y, screen_h - 1))
    return max(0, min(x, screen_w - 1)), max(0, min(y, screen_h - 1))


def launch_app(app: str) -> dict:
    """
    Launches an application instantly using Windows Shell,
    moves the mouse cursor smoothly to demonstrate physical control,
    and brings the new window to focus.
    """
    app_key = str(app).lower().strip()
    cmd = APP_COMMANDS.get(app_key, app_key)

    # 1. Visually glide the mouse cursor across the screen to show AI agency
    screen_w, screen_h = get_screen_size()
    glide_x = screen_w // 2 + 120
    glide_y = screen_h // 2 - 80

    try:
        from overlay import get_overlay
        get_overlay().show_click(glide_x, glide_y)
    except Exception:
        pass

    pyautogui.moveTo(glide_x, glide_y, duration=0.4, tween=pyautogui.easeInOutQuad)

    # 2. Launch the application reliably
    try:
        if cmd.startswith("start "):
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen([cmd], shell=True)
        time.sleep(1.5)

        # If launching Chrome or Browser: ensure focus and bypass profile chooser if present
        if app_key in ("chrome", "browser"):
            # Press enter in case Chrome opened profile selection
            pyautogui.press("enter")
            time.sleep(0.8)
            # Click near address bar location to guarantee focus for subsequent typing
            addr_x = screen_w // 2
            addr_y = 82
            pyautogui.click(addr_x, addr_y)
            time.sleep(0.3)

        return {"status": "success", "action": "launch_app", "app": app_key}
    except Exception as e:
        return {"status": "failed", "action": "launch_app", "error": str(e)}


def click(x: int, y: int, button: str = "left") -> dict:
    """Clicks at screen coordinate (x, y) with visible mouse glide and ripple."""
    target_x, target_y = scale_coordinates(x, y)

    # Visually glide mouse to the target coordinate
    pyautogui.moveTo(target_x, target_y, duration=0.4, tween=pyautogui.easeInOutQuad)

    # Trigger visual HUD click ripple
    try:
        from overlay import get_overlay
        get_overlay().show_click(target_x, target_y)
    except Exception:
        pass

    pyautogui.click(x=target_x, y=target_y, button=button)
    return {"status": "success", "action": "click", "x": target_x, "y": target_y, "button": button}


def double_click(x: int, y: int) -> dict:
    """Double clicks at screen coordinate (x, y) with visible mouse glide."""
    target_x, target_y = scale_coordinates(x, y)
    pyautogui.moveTo(target_x, target_y, duration=0.4, tween=pyautogui.easeInOutQuad)
    try:
        from overlay import get_overlay
        get_overlay().show_click(target_x, target_y)
    except Exception:
        pass
    pyautogui.doubleClick(x=target_x, y=target_y)
    return {"status": "success", "action": "double_click", "x": target_x, "y": target_y}


def right_click(x: int, y: int) -> dict:
    """Right clicks at screen coordinate (x, y)."""
    return click(x, y, button="right")


def move_to(x: int, y: int) -> dict:
    """Moves mouse smoothly to coordinate (x, y)."""
    target_x, target_y = scale_coordinates(x, y)
    pyautogui.moveTo(target_x, target_y, duration=0.2)
    return {"status": "success", "action": "move_to", "x": target_x, "y": target_y}


def type_text(text: str) -> dict:
    """
    Types text into the active focused field.
    Uses pyautogui.typewrite for ASCII text (required for Windows 11 Start Menu & Run dialog),
    and clipboard paste for Arabic / Unicode characters.
    """
    text_str = str(text)
    is_ascii = all(ord(c) < 128 for c in text_str)

    if is_ascii:
        try:
            # Direct keystrokes so Windows 11 Start Menu accepts input
            pyautogui.typewrite(text_str, interval=0.03)
            return {"status": "success", "action": "type_text", "method": "typewrite", "text": text_str}
        except Exception:
            pass

    # Clipboard paste for Arabic or non-ASCII unicode
    try:
        import pyperclip
        pyperclip.copy(text_str)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        return {"status": "success", "action": "type_text", "method": "clipboard", "text": text_str}
    except Exception as e:
        pyautogui.typewrite(text_str, interval=0.03)
        return {"status": "success", "action": "type_text", "method": "fallback", "text": text_str}


def press_key(key: str) -> dict:
    """Presses a single keyboard key safely with alias normalization."""
    normalized = normalize_key(key)
    try:
        pyautogui.press(normalized)
        # Settle delay for Windows Start Menu and Run Dialog to appear
        if normalized in ("winleft", "winright", "enter"):
            time.sleep(0.5)
        return {"status": "success", "action": "press_key", "key": normalized}
    except Exception as e:
        if normalized == "winleft":
            import ctypes
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0x0002, 0)
            time.sleep(0.5)
            return {"status": "success", "action": "press_key", "key": "winleft", "fallback": "ctypes"}
        return {"status": "failed", "action": "press_key", "error": str(e)}


def hotkey(*keys) -> dict:
    """Executes a shortcut combination (e.g., ['win', 'r'] or ['ctrl', 'c'])."""
    normalized_keys = [normalize_key(k) for k in keys]
    try:
        pyautogui.hotkey(*normalized_keys)
        # Settle delay for Windows Run dialog or system shortcuts
        if "winleft" in normalized_keys and "r" in normalized_keys:
            time.sleep(0.6)
        return {"status": "success", "action": "hotkey", "keys": normalized_keys}
    except Exception as e:
        return {"status": "failed", "action": "hotkey", "error": str(e)}


def scroll(amount: int, x: int = None, y: int = None) -> dict:
    """Scrolls mouse wheel. Positive amount = up, negative amount = down."""
    if x is not None and y is not None:
        target_x, target_y = scale_coordinates(x, y)
        pyautogui.scroll(amount, x=target_x, y=target_y)
    else:
        pyautogui.scroll(amount)
    return {"status": "success", "action": "scroll", "amount": amount}


def wait(seconds: float = 1.0) -> dict:
    """Waits for window load or animation completion."""
    time.sleep(max(0.1, min(float(seconds), 10.0)))
    return {"status": "success", "action": "wait", "seconds": seconds}


# Action registry
ACTIONS_MAP = {
    "launch_app": launch_app,
    "click": click,
    "double_click": double_click,
    "right_click": right_click,
    "move_to": move_to,
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "scroll": scroll,
    "wait": wait,
}


def execute_action(action_dict: dict) -> dict:
    """Dispatches JSON action dictionary to python execution functions."""
    action_name = action_dict.get("action", "").lower().strip()
    if action_name == "done":
        return {"status": "completed", "summary": action_dict.get("summary", "Done")}

    func = ACTIONS_MAP.get(action_name)
    if func is None:
        return {"status": "failed", "error": f"Unknown action: {action_name}"}

    # Extract all parameters except 'action' and 'thought'
    params = {k: v for k, v in action_dict.items() if k not in ("action", "thought")}

    # Support list of keys for hotkey
    if action_name == "hotkey" and "keys" in params and isinstance(params["keys"], list):
        return hotkey(*params["keys"])

    try:
        return func(**params)
    except Exception as e:
        return {"status": "failed", "action": action_name, "error": str(e)}
