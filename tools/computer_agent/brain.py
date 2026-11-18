"""
وحدة التفكير - Brain Module (Gemini Direct REST)
=================================================
إرسال لقطة الشاشة مع المهمة إلى Google Gemini API
مباشرة عبر بروتوكول HTTP القياسي (فائق السرعة وبدون مشاكل مكتبات).
"""

import json
import re
import io
import base64
import urllib.request
import urllib.error
from PIL import Image

from config import GEMINI_API_KEY, GEMINI_MODELS, SCREENSHOT_QUALITY

# ──────────────────────────────────────────────
# برومبت النظام الذي يوجّه النموذج
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """أنت وكيل ذكي تتحكم بكمبيوتر يعمل بنظام Windows.
تستقبل لقطة شاشة حالية ومهمة مطلوبة، ويجب أن تقرر الإجراء التالي الواحد.

## الإجراءات المتاحة لك:
1. `click` - نقر: {"action": "click", "x": <int>, "y": <int>}
2. `double_click` - نقر مزدوج: {"action": "double_click", "x": <int>, "y": <int>}
3. `type_text` - كتابة نص: {"action": "type_text", "text": "<string>"}
4. `press_key` - ضغط مفتاح: {"action": "press_key", "key": "<key_name>"}
   مفاتيح شائعة: win, enter, tab, escape, backspace, delete, up, down, left, right, space
5. `hotkey` - اختصارات مركبة: {"action": "hotkey", "keys": ["ctrl", "c"]} أو ["win", "r"]
6. `scroll` - تمرير: {"action": "scroll", "amount": <int>, "x": <int>, "y": <int>}
7. `wait` - انتظار: {"action": "wait", "seconds": <float>}
8. `done` - انتهاء المهمة بنجاح: {"action": "done", "summary": "<ملخص ما تم>"}

## نصائح ذكية:
- لفتح أي برنامج (مثل المفكرة Notepad أو الآلة الحاسبة Calculator):
  1. اضغط مفتاح `win` (أو اختصار `["win", "r"]`).
  2. في الخطوة التالية اكتب اسم البرنامج واضغط enter.
- إذا كنت تريد الكتابة في حقل أو نافذة، انقر عليه أولاً لتفعيله ثم اكتب في الخطوة التالية.
- عندما تنتهي المهمة تماماً، أعد action: "done".

## صيغة الإخراج الإلزامية:
أعد كائن JSON فقط بدون أي مقدمات:
```json
{"thought": "تفكيرك وخطتك للخطوة", "action": "click", "x": 100, "y": 200}
```"""


def init_model(api_key: str = None):
    """التحقق من توفر المفتاح وإرجاعه."""
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("❌ مفتاح Gemini API غير موجود في config.py!")
    return key


def think(api_key: str, screenshot: Image.Image, task: str, history: list = None) -> dict:
    """
    إرسال لقطة الشاشة والمهمة عبر REST API والحصول على الإجراء التالي.
    """
    # تحويل الصورة إلى Base64
    buf = io.BytesIO()
    screenshot.save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
    b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")

    # صياغة محتوى الطلب
    prompt_text = f"المهمة المطلوبة: {task}\n"
    if history:
        prompt_text += "الخطوات السابقة التي قمت بها:\n"
        for i, h in enumerate(history, 1):
            prompt_text += f"  {i}. {h}\n"
    prompt_text += "\nهذه هي لقطة الشاشة الحالية بعد الإجراءات السابقة. ما هو الإجراء التالي؟ أعد JSON فقط."

    parts = [
        {"text": prompt_text},
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64_image
            }
        }
    ]

    payload = {
        "contents": [{"parts": parts}],
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 512,
        }
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    # تجربة النماذج المتاحة بالتسلسل
    last_error = None
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                candidate = res_json.get("candidates", [{}])[0]
                text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                return parse_response(text)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_error = f"{model_name} HTTP {e.code}: {err_body}"
            # إذا كان النموذج غير متاح أو مضغوط (503/404)، نجرب الذي يليه
            continue
        except Exception as e:
            last_error = f"{model_name}: {str(e)}"
            continue

    return {
        "thought": f"خطأ في الاتصال بالنموذج: {last_error}",
        "action": "done",
        "summary": "فشل الاتصال بالنموذج"
    }


def parse_response(raw: str) -> dict:
    """استخراج JSON من إخراج النموذج."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "thought": f"تعذر قراءة الرد: {raw[:150]}",
            "action": "done",
            "summary": "استجابة غير مهيكلة"
        }
