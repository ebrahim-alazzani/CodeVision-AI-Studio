"""
وحدة تنفيذ الإجراءات - Actions Module
========================================
تنفيذ أوامر الماوس ولوحة المفاتيح على سطح المكتب.
كل إجراء يُسجّل في السجل (log) للتتبع.
"""

import time
import pyautogui
from config import ACTION_DELAY, TYPE_INTERVAL

# تعطيل الإيقاف الآمن عند الزاوية (لأننا نريد التحكم الكامل)
# لكن نفعّل التأخير بين الحركات للأمان
pyautogui.FAILSAFE = True   # حرك الماوس للزاوية العليا اليسرى للإيقاف الطارئ
pyautogui.PAUSE = ACTION_DELAY


def click(x: int, y: int, button: str = "left") -> dict:
    """
    نقر الماوس على إحداثيات محددة.
    button: "left", "right", "middle"
    """
    pyautogui.click(x=x, y=y, button=button)
    return {"action": "click", "x": x, "y": y, "button": button, "status": "done"}


def double_click(x: int, y: int) -> dict:
    """نقر مزدوج على إحداثيات محددة."""
    pyautogui.doubleClick(x=x, y=y)
    return {"action": "double_click", "x": x, "y": y, "status": "done"}


def type_text(text: str) -> dict:
    """
    كتابة نص باستخدام لوحة المفاتيح.
    يدعم النص العربي والإنجليزي عبر الحافظة.
    """
    # للنص العربي والأحرف الخاصة: نستخدم الحافظة
    try:
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        return {"action": "type_text", "text": text, "method": "clipboard", "status": "done"}
    except ImportError:
        # احتياطي: كتابة مباشرة (إنجليزي فقط)
        pyautogui.typewrite(text, interval=TYPE_INTERVAL)
        return {"action": "type_text", "text": text, "method": "typewrite", "status": "done"}


def press_key(key: str) -> dict:
    """
    ضغط مفتاح واحد.
    أمثلة: "enter", "tab", "escape", "backspace", "delete",
           "up", "down", "left", "right", "space",
           "f1" ... "f12", "home", "end", "pageup", "pagedown"
    """
    pyautogui.press(key)
    return {"action": "press_key", "key": key, "status": "done"}


def hotkey(*keys: str) -> dict:
    """
    ضغط مفاتيح مركبة.
    مثال: hotkey("ctrl", "c") أو hotkey("alt", "f4")
    """
    pyautogui.hotkey(*keys)
    return {"action": "hotkey", "keys": list(keys), "status": "done"}


def scroll(amount: int, x: int = None, y: int = None) -> dict:
    """
    تمرير عجلة الماوس.
    amount > 0: للأعلى، amount < 0: للأسفل
    """
    if x is not None and y is not None:
        pyautogui.scroll(amount, x=x, y=y)
    else:
        pyautogui.scroll(amount)
    return {"action": "scroll", "amount": amount, "x": x, "y": y, "status": "done"}


def move_to(x: int, y: int) -> dict:
    """تحريك الماوس إلى إحداثيات محددة بدون نقر."""
    pyautogui.moveTo(x, y, duration=0.3)
    return {"action": "move_to", "x": x, "y": y, "status": "done"}


def drag_to(start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
    """سحب من نقطة إلى أخرى."""
    pyautogui.moveTo(start_x, start_y, duration=0.2)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=0.5)
    return {
        "action": "drag_to",
        "from": [start_x, start_y],
        "to": [end_x, end_y],
        "status": "done",
    }


def wait(seconds: float) -> dict:
    """انتظار لفترة محددة (مفيد لانتظار تحميل الصفحات)."""
    time.sleep(seconds)
    return {"action": "wait", "seconds": seconds, "status": "done"}


# ──────────────────────────────────────────────
# قاموس الإجراءات المتاحة (يستخدمه الوكيل)
# ──────────────────────────────────────────────
ACTION_MAP = {
    "click": click,
    "double_click": double_click,
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "scroll": scroll,
    "move_to": move_to,
    "drag_to": drag_to,
    "wait": wait,
}


def execute_action(action_dict: dict) -> dict:
    """
    تنفيذ إجراء من قاموس JSON.
    مثال الإدخال: {"action": "click", "x": 500, "y": 300}
    """
    action_name = action_dict.get("action", "")
    func = ACTION_MAP.get(action_name)

    if func is None:
        return {"error": f"إجراء غير معروف: {action_name}"}

    # استخراج المعاملات (بدون مفتاح action)
    params = {k: v for k, v in action_dict.items() if k != "action"}

    try:
        result = func(**params)
        return result
    except Exception as e:
        return {"action": action_name, "error": str(e), "status": "failed"}


if __name__ == "__main__":
    # اختبار: تحريك الماوس لمركز الشاشة
    import pyautogui
    w, h = pyautogui.size()
    print(f"🖥️ حجم الشاشة: {w}x{h}")
    print("🖱️ تحريك الماوس لمركز الشاشة...")
    result = move_to(w // 2, h // 2)
    print(f"✅ {result}")
