"""
CyberPro AI - Dual-Pane Studio & Chat Operations Center v3.5
===========================================================
Professional Cyberpunk Desktop Control Center with:
1. Left Pane:  Interactive Multimodal AI Chat (Text, File Attachments, Voice Notes)
2. Right Pane: Live Operations Telemetry, AI Reasoning Stream & Steps Feed
3. Physical Agency: Visible cursor glides, target ripples, and Chrome bypass
4. Auto-Pilot: Automatic initialization and welcoming on startup
"""

import sys
import os
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pyautogui

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from config import AI_BACKEND, OLLAMA_MODEL, MAX_STEPS, LOGS_DIR
from screen import capture_screenshot
from brain import init_brain, think
from actions import execute_action
from overlay import get_overlay
from voice_speaker import speak, set_voice_enabled, is_voice_enabled

PRESETS = [
    ("📝 Notepad Note", "open notepad and type Welcome to CyberPro AI Agent! Controlled locally by Qwen."),
    ("🧮 Calculator", "open calculator and calculate 25 * 4"),
    ("🌐 Chrome Search", "open chrome and search for cyberpro ai agent"),
    ("📁 File Explorer", "open file explorer"),
    ("🎨 Paint Canvas", "open paint"),
]


class CyberProDualStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ CyberPro AI - Dual-Pane Studio v3.5")

        screen_w, screen_h = pyautogui.size()
        win_w = min(1060, screen_w - 60)
        win_h = min(680, screen_h - 90)
        win_x = 30
        win_y = 40
        self.root.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
        self.root.configure(bg="#040814")
        self.root.attributes("-topmost", False)

        self.is_running = False
        self.abort_flag = False
        self.worker_thread = None

        # Multimodal Inputs
        self.attached_file = None
        self.is_recording = False
        self.audio_frames = []
        self.record_stream = None

        self._init_theme()
        self._build_topbar()
        self._build_panes()

        # Auto-pilot initial greeting on startup
        self.root.after(400, self._on_startup)

    def _init_theme(self):
        self.c_bg = "#040814"
        self.c_header = "#071224"
        self.c_card = "#07172e"
        self.c_terminal = "#020610"
        self.c_cyan = "#00f3ff"
        self.c_green = "#00ff88"
        self.c_yellow = "#ffd600"
        self.c_red = "#ff1744"
        self.c_purple = "#c084fc"
        self.c_text = "#e0f7fa"
        self.c_dim = "#78909c"
        self.c_border = "#0d2847"

    def _build_topbar(self):
        topbar = tk.Frame(self.root, bg=self.c_header, height=48, bd=1, relief="solid")
        topbar.pack(fill="x", side="top")

        left = tk.Frame(topbar, bg=self.c_header)
        left.pack(side="left", padx=14, pady=8)

        logo = tk.Label(
            left,
            text=" 🛡️ CYBERPRO AI ",
            fg="#040812",
            bg=self.c_cyan,
            font=("Segoe UI", 10, "bold")
        )
        logo.pack(side="left")

        title = tk.Label(
            left,
            text=" DUAL STUDIO v3.5 (MULTIMODAL)",
            fg=self.c_cyan,
            bg=self.c_header,
            font=("Segoe UI", 9, "bold")
        )
        title.pack(side="left", padx=6)

        right = tk.Frame(topbar, bg=self.c_header)
        right.pack(side="right", padx=14)

        self.tts_btn = tk.Button(
            right,
            text="🔊 الصوت: مفعّل",
            fg=self.c_cyan,
            bg="#0e284d",
            activebackground=self.c_cyan,
            activeforeground="#040812",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=8,
            pady=3,
            command=self.toggle_tts
        )
        self.tts_btn.pack(side="left", padx=8)

        status_box = tk.Frame(right, bg="#0d2542", bd=1)
        status_box.pack(side="right", pady=8)

        self.engine_dot = tk.Label(status_box, text="●", fg=self.c_green, bg="#0d2542", font=("Segoe UI", 8))
        self.engine_dot.pack(side="left", padx=(6, 2))

        self.engine_name = tk.Label(
            status_box,
            text=f"LOCAL ENGINE: {OLLAMA_MODEL.upper()} ",
            fg="#e0f7fa",
            bg="#0d2542",
            font=("Segoe UI", 8, "bold")
        )
        self.engine_name.pack(side="left", padx=(0, 6), pady=2)

    def _build_panes(self):
        main_container = tk.Frame(self.root, bg=self.c_bg)
        main_container.pack(fill="both", expand=True, padx=12, pady=10)

        # ----------------------------------------------------
        # 💬 LEFT PANE: Multimodal Chat & Mission Controller
        # ----------------------------------------------------
        left_pane = tk.Frame(main_container, bg=self.c_card, bd=1, relief="solid")
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 6))

        pane_header_left = tk.Frame(left_pane, bg="#0a1d38", height=32)
        pane_header_left.pack(fill="x")

        tk.Label(
            pane_header_left,
            text="💬 AI CHAT & MULTIMODAL CONTROLLER",
            fg=self.c_cyan,
            bg="#0a1d38",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=10, pady=6)

        clear_btn = tk.Button(
            pane_header_left,
            text="🧹 مسح المحادثة",
            fg=self.c_dim,
            bg="#0d2542",
            activebackground=self.c_red,
            activeforeground="#ffffff",
            font=("Segoe UI", 8),
            bd=0,
            padx=8,
            pady=2,
            command=self.clear_chat
        )
        clear_btn.pack(side="right", padx=8, pady=4)

        # Quick Mission Chips Bar
        chips_frame = tk.Frame(left_pane, bg=self.c_card)
        chips_frame.pack(fill="x", padx=10, pady=(6, 4))

        tk.Label(
            chips_frame,
            text="⚡ Quick Missions (أزرار المهام السريعة):",
            fg=self.c_green,
            bg=self.c_card,
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        chips_row = tk.Frame(chips_frame, bg=self.c_card)
        chips_row.pack(fill="x")

        for label, task in PRESETS:
            btn = tk.Button(
                chips_row,
                text=label,
                fg=self.c_text,
                bg="#0e284d",
                activebackground=self.c_cyan,
                activeforeground="#040812",
                font=("Segoe UI", 8),
                bd=1,
                relief="flat",
                padx=4,
                pady=3,
                command=lambda t=task: self.send_task(t)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")

        # Chat Stream Area
        chat_box = tk.Frame(left_pane, bg=self.c_terminal)
        chat_box.pack(fill="both", expand=True, padx=10, pady=6)

        self.chat_text = tk.Text(
            chat_box,
            fg=self.c_text,
            bg=self.c_terminal,
            insertbackground=self.c_cyan,
            font=("Segoe UI", 9),
            bd=0,
            padx=10,
            pady=10,
            wrap="word"
        )
        self.chat_text.pack(side="left", fill="both", expand=True)

        chat_scroll = tk.Scrollbar(chat_box, command=self.chat_text.yview)
        chat_scroll.pack(side="right", fill="y")
        self.chat_text.config(yscrollcommand=chat_scroll.set)

        self.chat_text.tag_config("user_msg", foreground=self.c_cyan, font=("Segoe UI", 9, "bold"))
        self.chat_text.tag_config("ai_msg", foreground="#ffffff", font=("Segoe UI", 9))
        self.chat_text.tag_config("sys_msg", foreground=self.c_dim, font=("Segoe UI", 8, "italic"))
        self.chat_text.tag_config("success", foreground=self.c_green, font=("Segoe UI", 9, "bold"))
        self.chat_text.tag_config("attach_msg", foreground=self.c_purple, font=("Segoe UI", 8, "bold"))
        self.chat_text.tag_config("welcome", foreground=self.c_yellow, font=("Segoe UI", 9))

        # Attached File Chip Bar
        self.attach_bar = tk.Frame(left_pane, bg="#0d2542")
        self.attach_lbl = tk.Label(self.attach_bar, text="", fg=self.c_purple, bg="#0d2542", font=("Segoe UI", 8, "bold"))
        self.attach_lbl.pack(side="left", padx=8, pady=3)
        remove_attach_btn = tk.Button(self.attach_bar, text="✕", fg=self.c_red, bg="#0d2542", bd=0, font=("Segoe UI", 8, "bold"), command=self.remove_attachment)
        remove_attach_btn.pack(side="right", padx=6)

        # Voice Recording Status Bar
        self.voice_bar = tk.Frame(left_pane, bg="#3b0712")
        self.voice_lbl = tk.Label(self.voice_bar, text="🔴 جارٍ تسجيل الصوت... تحدث بوضوح ثم اضغط على زر الميكروفون مجدداً لإنهاء التسجيل والتفريغ", fg="#ff5252", bg="#3b0712", font=("Segoe UI", 8, "bold"))
        self.voice_lbl.pack(fill="x", padx=8, pady=4)

        # Bottom Multimodal Input Toolbar
        input_container = tk.Frame(left_pane, bg="#071224", bd=1, relief="solid")
        input_container.pack(fill="x", padx=10, pady=(0, 10))

        input_row = tk.Frame(input_container, bg="#071224")
        input_row.pack(fill="x", padx=8, pady=6)

        # 📎 Attach File Button
        self.attach_btn = tk.Button(
            input_row,
            text="📎 ملف",
            fg=self.c_text,
            bg="#0e284d",
            activebackground=self.c_purple,
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=8,
            pady=4,
            command=self.pick_file
        )
        self.attach_btn.pack(side="left", padx=(0, 4))

        # 🎙️ Voice Recording Button
        self.voice_btn = tk.Button(
            input_row,
            text="🎙️ صوت",
            fg=self.c_text,
            bg="#0e284d",
            activebackground=self.c_red,
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=8,
            pady=4,
            command=self.toggle_voice_record
        )
        self.voice_btn.pack(side="left", padx=(0, 6))

        # Text Input
        self.user_input = tk.Entry(
            input_row,
            fg="#ffffff",
            bg=self.c_terminal,
            insertbackground=self.c_cyan,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid"
        )
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=4)
        self.user_input.insert(0, "open chrome and search for cyberpro ai agent")
        self.user_input.bind("<Return>", lambda e: self.on_send())

        # ⚡ Send Button
        self.send_btn = tk.Button(
            input_row,
            text="⚡ إرسال المهمة",
            fg="#040812",
            bg=self.c_green,
            activebackground="#00e676",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=4,
            command=self.on_send
        )
        self.send_btn.pack(side="right")

        # ----------------------------------------------------
        # ⚡ RIGHT PANE: Live Operations & Telemetry Center
        # ----------------------------------------------------
        right_pane = tk.Frame(main_container, bg=self.c_card, width=440, bd=1, relief="solid")
        right_pane.pack(side="right", fill="both", expand=True, padx=(6, 0))

        pane_header_right = tk.Frame(right_pane, bg="#0a1d38", height=32)
        pane_header_right.pack(fill="x")

        tk.Label(
            pane_header_right,
            text="⚡ LIVE OPERATIONS & STEP TELEMETRY",
            fg=self.c_green,
            bg="#0a1d38",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=10, pady=6)

        # Real-time Thought Card
        thought_card = tk.Frame(right_pane, bg="#0b1e3b", bd=1, relief="solid")
        thought_card.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            thought_card,
            text="🧠 LIVE AI REASONING (تفكير النموذج اللحظي):",
            fg=self.c_yellow,
            bg="#0b1e3b",
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(4, 2))

        self.live_thought_lbl = tk.Label(
            thought_card,
            text="المساعد مستعد لتلقي المهمة وتنفيذها على سطح المكتب...",
            fg="#ffffff",
            bg="#0b1e3b",
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=400,
            justify="left"
        )
        self.live_thought_lbl.pack(fill="x", padx=8, pady=(0, 6))

        # Real-time Steps Checklist Feed
        steps_box = tk.Frame(right_pane, bg=self.c_terminal)
        steps_box.pack(fill="both", expand=True, padx=10, pady=4)

        self.steps_list = tk.Listbox(
            steps_box,
            fg=self.c_cyan,
            bg=self.c_terminal,
            selectbackground="#0d2542",
            selectforeground=self.c_green,
            font=("Consolas", 9),
            bd=0,
            highlightthickness=0
        )
        self.steps_list.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        steps_scroll = tk.Scrollbar(steps_box, command=self.steps_list.yview)
        steps_scroll.pack(side="right", fill="y")
        self.steps_list.config(yscrollcommand=steps_scroll.set)

        # Status & Safety Bar
        status_bar = tk.Frame(right_pane, bg="#071224", bd=1, relief="solid")
        status_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.status_text_lbl = tk.Label(
            status_bar,
            text="STATUS: READY ● Waiting for mission",
            fg=self.c_green,
            bg="#071224",
            font=("Segoe UI", 8, "bold")
        )
        self.status_text_lbl.pack(side="left", padx=8, pady=6)

        self.stop_btn = tk.Button(
            status_bar,
            text="🛑 ABORT",
            fg="#ffffff",
            bg=self.c_red,
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=8,
            pady=2,
            state="disabled",
            command=self.abort_task
        )
        self.stop_btn.pack(side="right", padx=8, pady=4)

    # ----------------------------------------------------
    # 🚀 Auto-Pilot Startup & Greetings
    # ----------------------------------------------------
    def _on_startup(self):
        welcome_banner = (
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║    🛡️ مرحباً بك في CyberPro AI - Dual Studio v3.5!           ║\n"
            "║    ─────────────────────────────────────────────────────      ║\n"
            "║    ● المحرك المحلي: Qwen 2.5 Coder متصل عبر Ollama           ║\n"
            "║    ● الرد الصوتي (TTS): يتحدث معك بالصوت باللغتين            ║\n"
            "║    ● التفريغ الصوتي: Faster-Whisper جاهز للتسجيل الصوتي      ║\n"
            "║    ● الأدوات: الأوامر النصية، إرفاق الملفات، والتنقل الذكي   ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
        )
        self._append_chat("welcome", welcome_banner)
        self._append_chat("sys_msg", "✨ النظام في وضع الاستعداد الكامل (Ready) - يمكنك الضغط على مهمة سريعة أو البدء فوراً.")
        speak("مرحباً بك! أنا وكيلك الذكي CyberPro AI، متصل ومستعد لتنفيذ أوامرك على سطح المكتب.")

    def toggle_tts(self):
        curr = is_voice_enabled()
        set_voice_enabled(not curr)
        if not curr:
            self.tts_btn.config(text="🔊 الصوت: مفعّل", fg=self.c_cyan)
            speak("تم تفعيل الصوت.")
        else:
            self.tts_btn.config(text="🔇 الصوت: مكتوم", fg=self.c_dim)

    # ----------------------------------------------------
    # 📎 File Attachment Handler
    # ----------------------------------------------------
    def pick_file(self):
        fp = filedialog.askopenfilename(
            title="اختر ملفاً لربطه بالمهمة",
            filetypes=[("All Files", "*.*"), ("Text & Code", "*.txt;*.py;*.cs;*.dart;*.json;*.md"), ("Images", "*.png;*.jpg;*.jpeg")]
        )
        if fp and os.path.exists(fp):
            self.attached_file = fp
            fname = os.path.basename(fp)
            fsize_kb = os.path.getsize(fp) // 1024
            self.attach_lbl.config(text=f"📎 المرفق النشط: {fname} ({fsize_kb} KB)")
            self.attach_bar.pack(fill="x", padx=10, pady=(0, 4), before=self.user_input.master.master)
            self._append_chat("attach_msg", f"📎 تم إرفاق الملف: {fname} ({fp})")

    def remove_attachment(self):
        self.attached_file = None
        self.attach_bar.pack_forget()

    # ----------------------------------------------------
    # 🎙️ Voice Recording & Faster-Whisper Transcription
    # ----------------------------------------------------
    def toggle_voice_record(self):
        if not self.is_recording:
            self._start_voice_recording()
        else:
            self._stop_voice_recording()

    def _start_voice_recording(self):
        try:
            import sounddevice as sd
            self.is_recording = True
            self.audio_frames = []
            self.voice_btn.config(text="⏹️ إيقاف", bg=self.c_red, fg="#ffffff")
            self.voice_bar.pack(fill="x", padx=10, pady=(0, 4), before=self.user_input.master.master)

            def audio_callback(indata, frames, time_info, status):
                if self.is_recording:
                    self.audio_frames.append(indata.copy())

            self.record_stream = sd.InputStream(samplerate=16000, channels=1, dtype='float32', callback=audio_callback)
            self.record_stream.start()
            self._append_chat("sys_msg", "🎙️ بدأ تسجيل الصوت... تحدث الآن بأمرك وسيقوم Whisper بتفريغه.")
        except Exception as e:
            messagebox.showwarning("Voice Recording", f"تعذر فتح الميكروفون: {e}")
            self.is_recording = False

    def _stop_voice_recording(self):
        self.is_recording = False
        self.voice_btn.config(text="🎙️ صوت", bg="#0e284d", fg=self.c_text)
        self.voice_bar.pack_forget()

        if self.record_stream:
            try:
                self.record_stream.stop()
                self.record_stream.close()
            except Exception:
                pass

        if not self.audio_frames:
            return

        self._append_chat("sys_msg", "⏳ جارٍ معالجة الصوت وتفريغه بواسطة Faster-Whisper...")

        # Transcribe in a thread to keep GUI responsive
        threading.Thread(target=self._transcribe_audio_thread, daemon=True).start()

    def _transcribe_audio_thread(self):
        try:
            audio_data = np.concatenate(self.audio_frames, axis=0).flatten()
            if len(audio_data) < 8000:
                self.root.after(0, lambda: self._append_chat("sys_msg", "⚠️ مدة التسجيل قصيرة جداً."))
                return

            from faster_whisper import WhisperModel
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_data, vad_filter=True)
            text_result = " ".join([s.text.strip() for s in segments if s.text.strip()]).strip()

            if text_result:
                def _apply():
                    self.user_input.delete(0, tk.END)
                    self.user_input.insert(0, text_result)
                    self._append_chat("user_msg", f"🎙️ الصوت المسجل: \"{text_result}\"")
                self.root.after(0, _apply)
            else:
                self.root.after(0, lambda: self._append_chat("sys_msg", "⚠️ لم يتم التعرف على كلمات واضحة."))
        except Exception as ex:
            self.root.after(0, lambda: self._append_chat("sys_msg", f"⚠️ تعذر التفريغ: {ex}"))

    # ----------------------------------------------------
    # 💬 Chat Utilities
    # ----------------------------------------------------
    def _append_chat(self, tag: str, text: str):
        self.chat_text.insert(tk.END, f"{text}\n", tag)
        self.chat_text.see(tk.END)

    def clear_chat(self):
        self.chat_text.delete("1.0", tk.END)
        self.steps_list.delete(0, tk.END)
        self._on_startup()

    def on_send(self):
        text = self.user_input.get().strip()
        if text and not self.is_running:
            self.send_task(text)

    # ----------------------------------------------------
    # 🎯 Mission Execution Loop
    # ----------------------------------------------------
    def send_task(self, task_text: str):
        if self.is_running:
            return

        full_task = task_text
        if self.attached_file:
            full_task += f" [Attached file: {self.attached_file}]"

        self.is_running = True
        self.abort_flag = False
        self.send_btn.config(state="disabled", text="⚡ RUNNING...")
        self.stop_btn.config(state="normal")
        self.status_text_lbl.config(text="STATUS: EXECUTING MISSION ●", fg=self.c_cyan)

        # Log in Chat
        self._append_chat("user_msg", f"\n🎯 MISSION: {full_task}")
        self.steps_list.delete(0, tk.END)
        self.steps_list.insert(tk.END, f"🎯 STARTING: {task_text[:35]}...")
        self.steps_list.insert(tk.END, "─" * 40)
        speak(f"بدء تنفيذ المهمة: {task_text[:40]}")

        # Start execution worker thread
        self.worker_thread = threading.Thread(
            target=self._task_worker,
            args=(full_task,),
            daemon=True
        )
        self.worker_thread.start()

    def abort_task(self):
        self.abort_flag = True
        self._append_chat("sys_msg", "🛑 Mission aborted by operator.")
        self.status_text_lbl.config(text="STATUS: ABORTED", fg=self.c_red)
        speak("تم إيقاف المهمة.")

    def _task_worker(self, task_text: str):
        hud = get_overlay()
        try:
            hud.start()
            hud.set_mission(task_text)
        except Exception:
            pass

        try:
            engine_mode = init_brain()
        except Exception as e:
            self._append_chat("sys_msg", f"Engine connection error: {e}")
            self._finish_task("Engine Error")
            return

        history = []
        log_entries = []
        summary = "Completed"

        # Brief settle delay
        time.sleep(0.4)

        for step in range(1, MAX_STEPS + 1):
            if self.abort_flag:
                break

            # 1. Sense
            screenshot = capture_screenshot(save=True)

            # 2. Think
            decision = think(engine_mode, screenshot, task_text, history)
            thought = decision.get("thought", "Determining next step...")
            action = decision.get("action", "done")

            # Update Thought & Steps in UI
            self._update_telemetry(step, action, thought)
            hud.update_status(step, MAX_STEPS, action, thought)

            step_record = {
                "step": step,
                "thought": thought,
                "decision": decision
            }

            if action == "done":
                summary = decision.get("summary", "Mission Completed Successfully.")
                self._update_completion(summary)
                hud.update_status(step, MAX_STEPS, "MISSION ACCOMPLISHED ✅", summary)
                time.sleep(1.2)
                break

            # 3. Act
            param_summary = {k: v for k, v in decision.items() if k not in ("action", "thought")}
            result = execute_action(decision)
            status_text = result.get("status", "unknown")

            step_record["result"] = result
            log_entries.append(step_record)
            history.append(f"{action} {param_summary} -> {status_text}")

            self._add_step_log(f"   ✔ Status: {status_text}")
            time.sleep(1.0)

        self._finish_task(summary)

    def _update_telemetry(self, step: int, action: str, thought: str):
        def _apply():
            self.live_thought_lbl.config(text=thought)
            self.steps_list.insert(tk.END, f"▶ Step {step}: {action.upper()}")
            self.steps_list.yview_moveto(1.0)
            self._append_chat("sys_msg", f"  ⚡ Step {step}: {action.upper()} ({thought[:60]}...)")
        self.root.after(0, _apply)

    def _add_step_log(self, log_msg: str):
        def _apply():
            self.steps_list.insert(tk.END, log_msg)
            self.steps_list.yview_moveto(1.0)
        self.root.after(0, _apply)

    def _update_completion(self, summary: str):
        def _apply():
            self._append_chat("success", f"✅ MISSION ACCOMPLISHED: {summary}")
            self.steps_list.insert(tk.END, f"✅ FINISHED: {summary}")
            self.steps_list.yview_moveto(1.0)
            speak(f"تم إنجاز المهمة بنجاح! {summary[:40]}")
        self.root.after(0, _apply)

    def _finish_task(self, summary: str):
        def _apply():
            self.is_running = False
            self.send_btn.config(state="normal", text="⚡ إرسال المهمة")
            self.stop_btn.config(state="disabled")
            self.status_text_lbl.config(text="STATUS: READY ● Finished", fg=self.c_green)
            self._append_chat("sys_msg", "✨ Ready for the next mission!\n")
        self.root.after(0, _apply)


def launch_gui():
    root = tk.Tk()
    app = CyberProDualStudio(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
