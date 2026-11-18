"""
الحلقة الرئيسية للوكيل - Agent Main Loop
==========================================
الملف الرئيسي الذي يربط كل الوحدات ويشغّل حلقة:
  التقاط ← تفكير ← تنفيذ ← تكرار
"""

import sys
import os
import time
import json
from datetime import datetime

# إضافة مجلد الوكيل إلى مسار الاستيراد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_STEPS, LOGS_DIR
from screen import capture_screenshot
from brain import init_model, think
from actions import execute_action


def print_banner():
    """طباعة شعار الوكيل."""
    banner = r"""
    ╔══════════════════════════════════════════════════╗
    ║     🤖  CodeVision Computer Agent  v1.0         ║
    ║     ─────────────────────────────────────        ║
    ║     وكيل ذكي يستخدم الكمبيوتر نيابة عنك        ║
    ║     ⚠️  حرّك الماوس للزاوية العليا لإيقافه      ║
    ╚══════════════════════════════════════════════════╝
    """
    print(banner)


def run_task(task: str, api_key: str = None, max_steps: int = None):
    """
    تشغيل مهمة واحدة على الوكيل.
    
    Args:
        task: وصف المهمة المطلوبة بالعربي أو الإنجليزي
        api_key: مفتاح Gemini API (اختياري إذا مُعيَّن في config)
        max_steps: الحد الأقصى للخطوات (اختياري)
    """
    max_steps = max_steps or MAX_STEPS

    print(f"\n🎯 المهمة: {task}")
    print(f"📊 الحد الأقصى: {max_steps} خطوة")
    print("─" * 50)

    # تهيئة النموذج
    print("🧠 تهيئة نموذج التفكير...")
    model = init_model(api_key)
    print("✅ النموذج جاهز!\n")

    # سجل الإجراءات
    action_history = []
    log_entries = []
    start_time = time.time()

    for step in range(1, max_steps + 1):
        print(f"┌─── الخطوة {step}/{max_steps} ───")

        # 1. التقاط الشاشة
        print("│ 📸 التقاط لقطة شاشة...")
        screenshot = capture_screenshot(save=True)
        print(f"│    الحجم: {screenshot.size}")

        # 2. التفكير
        print("│ 🧠 التفكير...")
        try:
            decision = think(model, screenshot, task, action_history)
        except Exception as e:
            print(f"│ ❌ خطأ في التفكير: {e}")
            break

        thought = decision.get("thought", "")
        action_name = decision.get("action", "done")
        print(f"│ 💭 التفكير: {thought}")
        print(f"│ 🎬 الإجراء: {action_name}")

        # تسجيل في السجل
        log_entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "decision": decision,
        }

        # 3. التحقق من الانتهاء
        if action_name == "done":
            summary = decision.get("summary", "تمت المهمة")
            print(f"│ ✅ انتهى! {summary}")
            log_entry["result"] = {"status": "completed", "summary": summary}
            log_entries.append(log_entry)
            break

        # 4. تنفيذ الإجراء
        print(f"│ ⚡ تنفيذ: {json.dumps(decision, ensure_ascii=False)}")
        try:
            result = execute_action(decision)
            print(f"│ ✅ النتيجة: {result.get('status', 'unknown')}")
            log_entry["result"] = result
        except Exception as e:
            print(f"│ ❌ خطأ في التنفيذ: {e}")
            log_entry["result"] = {"status": "error", "error": str(e)}
            log_entries.append(log_entry)
            break

        # إضافة للسجل
        action_history.append(
            f"{action_name}: {json.dumps({k: v for k, v in decision.items() if k not in ('action', 'thought')}, ensure_ascii=False)}"
        )
        log_entries.append(log_entry)

        print(f"└{'─' * 30}")

        # تأخير قصير قبل اللقطة التالية (انتظار تحديث الشاشة)
        time.sleep(1.0)

    else:
        print(f"\n⚠️ وصلنا للحد الأقصى ({max_steps} خطوة) بدون إكمال المهمة.")

    # حفظ السجل
    elapsed = time.time() - start_time
    log = {
        "task": task,
        "total_steps": len(log_entries),
        "elapsed_seconds": round(elapsed, 1),
        "entries": log_entries,
    }
    log_path = os.path.join(LOGS_DIR, f"task_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\n📄 السجل محفوظ في: {log_path}")
    print(f"⏱️ الوقت الإجمالي: {elapsed:.1f} ثانية")

    return log


def interactive_mode(api_key: str = None):
    """
    الوضع التفاعلي: أدخل المهام واحدة تلو الأخرى.
    """
    print_banner()
    print("💡 أدخل المهمة المطلوبة، أو اكتب 'خروج' للإنهاء.\n")

    while True:
        try:
            task = input("🎯 المهمة ➜ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 مع السلامة!")
            break

        if not task:
            continue
        if task in ("خروج", "exit", "quit", "q"):
            print("👋 مع السلامة!")
            break

        try:
            run_task(task, api_key=api_key)
        except KeyboardInterrupt:
            print("\n⛔ تم إيقاف المهمة.")
        except Exception as e:
            print(f"\n❌ خطأ: {e}")

        print("\n" + "═" * 50 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="🤖 CodeVision Computer Agent - وكيل ذكي يستخدم الكمبيوتر"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="المهمة المطلوبة (اختياري - بدونه يدخل الوضع التفاعلي)",
    )
    parser.add_argument(
        "--api-key",
        help="مفتاح Gemini API",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=MAX_STEPS,
        help=f"الحد الأقصى للخطوات (افتراضي: {MAX_STEPS})",
    )

    args = parser.parse_args()

    if args.task:
        run_task(args.task, api_key=args.api_key, max_steps=args.max_steps)
    else:
        interactive_mode(api_key=args.api_key)
