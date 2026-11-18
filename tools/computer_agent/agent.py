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
    ║     AI Agent that controls your desktop          ║
    ║     ⚠️ Move mouse to top-left corner to STOP     ║
    ╚══════════════════════════════════════════════════╝
    """
    print(banner)


def run_task(task: str, api_key: str = None, max_steps: int = None):
    """
    تشغيل مهمة واحدة على الوكيل.
    """
    max_steps = max_steps or MAX_STEPS

    print(f"\n🎯 [Task / المهمة]: {task}")
    print(f"📊 [Max Steps]: {max_steps}")
    print("─" * 50)

    # تهيئة النموذج
    print("🧠 Initializing Gemini Brain...")
    model = init_model(api_key)
    print("✅ Model ready!\n")

    # سجل الإجراءات
    action_history = []
    log_entries = []
    start_time = time.time()

    for step in range(1, max_steps + 1):
        print(f"┌─── Step {step}/{max_steps} ───")

        # 1. التقاط الشاشة
        print("│ 📸 Capturing screen...")
        screenshot = capture_screenshot(save=True)
        print(f"│    Resolution: {screenshot.size}")

        # 2. التفكير
        print("│ 🧠 Thinking...")
        try:
            decision = think(model, screenshot, task, action_history)
        except Exception as e:
            print(f"│ ❌ Thinking Error: {e}")
            break

        thought = decision.get("thought", "")
        action_name = decision.get("action", "done")
        print(f"│ 💭 Thought: {thought}")
        print(f"│ 🎬 Action: {action_name}")

        # تسجيل في السجل
        log_entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "decision": decision,
        }

        # 3. التحقق من الانتهاء
        if action_name == "done":
            summary = decision.get("summary", "Task Completed")
            print(f"│ ✅ DONE! {summary}")
            log_entry["result"] = {"status": "completed", "summary": summary}
            log_entries.append(log_entry)
            break

        # 4. تنفيذ الإجراء
        print(f"│ ⚡ Executing: {json.dumps(decision, ensure_ascii=False)}")
        try:
            result = execute_action(decision)
            print(f"│ ✅ Result: {result.get('status', 'unknown')}")
            log_entry["result"] = result
        except Exception as e:
            print(f"│ ❌ Execution Error: {e}")
            log_entry["result"] = {"status": "error", "error": str(e)}
            log_entries.append(log_entry)
            break

        # إضافة للسجل
        action_history.append(
            f"{action_name}: {json.dumps({k: v for k, v in decision.items() if k not in ('action', 'thought')}, ensure_ascii=False)}"
        )
        log_entries.append(log_entry)

        print(f"└{'─' * 30}")

        # تأخير قصير قبل اللقطة التالية
        time.sleep(1.0)

    else:
        print(f"\n⚠️ Reached maximum steps ({max_steps}) without completion.")

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
    print(f"\n📄 Log saved to: {log_path}")
    print(f"⏱️ Total time: {elapsed:.1f} seconds")

    return log


def interactive_mode(api_key: str = None):
    """
    الوضع التفاعلي.
    """
    print_banner()
    print("💡 Enter your task in English or Arabic (type 'exit' to quit):\n")

    while True:
        try:
            task = input("🎯 Task / المهمة ➜ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not task:
            continue
        if task.lower() in ("خروج", "exit", "quit", "q"):
            print("👋 Goodbye!")
            break

        try:
            run_task(task, api_key=api_key)
        except KeyboardInterrupt:
            print("\n⛔ Task stopped by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")

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
