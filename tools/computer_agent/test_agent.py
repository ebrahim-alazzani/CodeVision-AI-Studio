"""
اختبار سريع للوكيل - Quick Test
=================================
يختبر جميع الوحدات بدون الحاجة لمفتاح API.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_screen():
    """اختبار التقاط الشاشة."""
    print("=" * 50)
    print("📸 اختبار 1: التقاط الشاشة")
    print("=" * 50)
    from screen import capture_screenshot, image_to_base64

    img = capture_screenshot(save=True)
    print(f"  ✅ الحجم: {img.size[0]}x{img.size[1]}")
    
    b64 = image_to_base64(img)
    print(f"  ✅ Base64: {len(b64):,} حرف ({len(b64) / 1024:.0f} KB)")
    print()
    return True


def test_actions():
    """اختبار الإجراءات (بدون تنفيذ فعلي خطير)."""
    print("=" * 50)
    print("🖱️ اختبار 2: وحدة الإجراءات")
    print("=" * 50)
    import pyautogui
    
    w, h = pyautogui.size()
    print(f"  ✅ حجم الشاشة: {w}x{h}")
    
    pos = pyautogui.position()
    print(f"  ✅ موقع الماوس: {pos}")

    from actions import execute_action
    
    # اختبار: تحريك الماوس لمركز الشاشة
    result = execute_action({"action": "move_to", "x": w // 2, "y": h // 2})
    print(f"  ✅ تحريك الماوس: {result['status']}")
    
    # اختبار: انتظار
    result = execute_action({"action": "wait", "seconds": 0.1})
    print(f"  ✅ انتظار: {result['status']}")
    
    # اختبار: إجراء غير معروف
    result = execute_action({"action": "fly_to_moon"})
    print(f"  ✅ إجراء خاطئ: {result.get('error', 'لا خطأ')}")
    print()
    return True


def test_brain_parser():
    """اختبار محلل إخراج النموذج."""
    print("=" * 50)
    print("🧠 اختبار 3: محلل إخراج النموذج")
    print("=" * 50)
    from brain import parse_response

    # حالة 1: JSON في كتلة كود
    r1 = parse_response('```json\n{"thought": "أرى الزر", "action": "click", "x": 100, "y": 200}\n```')
    assert r1["action"] == "click", f"فشل: {r1}"
    print(f"  ✅ كتلة كود: action={r1['action']}")

    # حالة 2: JSON مباشر
    r2 = parse_response('{"thought": "جاهز", "action": "done", "summary": "تم"}')
    assert r2["action"] == "done", f"فشل: {r2}"
    print(f"  ✅ JSON مباشر: action={r2['action']}")

    # حالة 3: نص مع JSON مدمج
    r3 = parse_response('سأنقر هنا {"thought": "النقر", "action": "click", "x": 50, "y": 50} هذا ما أفعله')
    assert r3["action"] == "click", f"فشل: {r3}"
    print(f"  ✅ JSON مدمج: action={r3['action']}")

    # حالة 4: نص بدون JSON
    r4 = parse_response("لا أعرف ماذا أفعل")
    assert r4["action"] == "done", f"فشل: {r4}"
    print(f"  ✅ بدون JSON: action={r4['action']} (تراجع آمن)")
    print()
    return True


def test_config():
    """اختبار الإعدادات."""
    print("=" * 50)
    print("⚙️ اختبار 4: الإعدادات")
    print("=" * 50)
    from config import SCREENSHOTS_DIR, LOGS_DIR, GEMINI_API_KEY

    print(f"  ✅ مجلد اللقطات: {SCREENSHOTS_DIR}")
    print(f"     موجود: {os.path.isdir(SCREENSHOTS_DIR)}")
    print(f"  ✅ مجلد السجلات: {LOGS_DIR}")
    print(f"     موجود: {os.path.isdir(LOGS_DIR)}")
    
    if GEMINI_API_KEY:
        print(f"  ✅ مفتاح API: مُعيَّن ({GEMINI_API_KEY[:8]}...)")
    else:
        print("  ⚠️ مفتاح API: غير مُعيَّن (عيّنه قبل تشغيل الوكيل)")
    print()
    return True


if __name__ == "__main__":
    print()
    print("🤖 اختبار شامل لوكيل الكمبيوتر")
    print("━" * 50)
    print()

    results = {}
    tests = [
        ("الإعدادات", test_config),
        ("الشاشة", test_screen),
        ("الإجراءات", test_actions),
        ("المحلل", test_brain_parser),
    ]

    for name, func in tests:
        try:
            results[name] = func()
        except Exception as e:
            print(f"  ❌ فشل: {e}")
            results[name] = False

    # ملخص
    print("━" * 50)
    print("📊 ملخص النتائج:")
    all_pass = True
    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"   {icon} {name}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\n🎉 جميع الاختبارات نجحت!")
        print("\n💡 الخطوة التالية:")
        print("   1. عيّن مفتاح Gemini API:")
        print('      set GEMINI_API_KEY=your_key_here')
        print("   2. شغّل الوكيل:")
        print('      python agent.py "افتح المفكرة واكتب مرحباً"')
    else:
        print("\n⚠️ بعض الاختبارات فشلت. راجع الأخطاء أعلاه.")
