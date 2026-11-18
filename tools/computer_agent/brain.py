"""
وحدة التفكير - Brain Module (Gemini VLM)
==========================================
إرسال لقطة الشاشة مع المهمة إلى نموذج Gemini 
والحصول على الإجراء التالي بصيغة JSON.

يستخدم مكتبة google-genai الجديدة (بديل google-generativeai المُهملة).
"""

import json
import re
from PIL import Image
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

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
   مفاتيح: enter, tab, escape, backspace, delete, up, down, left, right, space, f1-f12
5. `hotkey` - مفاتيح مركبة: {"action": "hotkey", "keys": ["ctrl", "c"]}
6. `scroll` - تمرير: {"action": "scroll", "amount": <int>, "x": <int>, "y": <int>}
   amount موجب=أعلى، سالب=أسفل
7. `wait` - انتظار: {"action": "wait", "seconds": <float>}
8. `done` - انتهاء المهمة: {"action": "done", "summary": "<ملخص ما تم>"}

## قواعد مهمة:
- أعد إجراء واحد فقط في كل مرة.
- الإحداثيات (x, y) تشير لمكان النقر على الشاشة بالبكسل.
- انظر بعناية للقطة الشاشة لتحديد الإحداثيات بدقة.
- إذا كنت تريد الكتابة في حقل، انقر عليه أولاً ثم اكتب في الخطوة التالية.
- عندما تنتهي من المهمة بالكامل، أعد action: "done".
- إذا حصل خطأ أو لم تستطع الاستمرار، أعد done مع شرح.

## صيغة الإخراج:
أعد JSON فقط بالشكل:
```json
{"thought": "تفكيرك المختصر", "action": "...", ...}
```"""


def init_model(api_key: str = None):
    """تهيئة عميل Gemini باستخدام google-genai الجديدة."""
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError(
            "❌ مفتاح Gemini API غير موجود!\n"
            "   ➡️  عيّنه في config.py أو كمتغير بيئة:\n"
            '   set GEMINI_API_KEY=your_key_here'
        )
    client = genai.Client(api_key=key)
    return client


def think(client, screenshot: Image.Image, task: str, history: list = None) -> dict:
    """
    إرسال لقطة الشاشة والمهمة للنموذج والحصول على الإجراء التالي.
    
    Args:
        client: عميل genai.Client
        screenshot: صورة PIL للشاشة
        task: وصف المهمة
        history: قائمة الإجراءات السابقة
    
    Returns:
        dict مع مفاتيح: thought, action, وأي معاملات إضافية
    """
    # بناء الرسالة
    parts = []

    # إضافة السجل السابق إن وُجد
    if history:
        history_text = "الإجراءات السابقة في هذه المهمة:\n"
        for i, h in enumerate(history, 1):
            history_text += f"  {i}. {h}\n"
        parts.append(history_text)

    parts.append(f"المهمة المطلوبة: {task}")
    parts.append("لقطة الشاشة الحالية:")
    parts.append(screenshot)
    parts.append("ما هو الإجراء التالي؟ أعد JSON فقط.")

    # استدعاء النموذج
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            max_output_tokens=512,
        ),
    )
    raw_text = response.text.strip()

    # استخراج JSON من الإخراج
    return parse_response(raw_text)


def parse_response(raw: str) -> dict:
    """استخراج JSON من إخراج النموذج (قد يكون مغلفاً بـ ```json)."""
    # محاولة 1: استخراج من كتلة كود
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # محاولة 2: البحث عن أول { ... }
    match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # محاولة 3: النص الكامل كـ JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "thought": f"فشل تحليل الإخراج: {raw[:200]}",
            "action": "done",
            "summary": "خطأ في فهم إخراج النموذج",
        }


if __name__ == "__main__":
    print("🧠 اختبار وحدة التفكير...")
    test_json = '```json\n{"thought": "أرى سطح المكتب", "action": "click", "x": 100, "y": 200}\n```'
    result = parse_response(test_json)
    print(f"✅ تحليل JSON: {result}")
