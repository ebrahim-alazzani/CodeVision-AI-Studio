"""CodeVision Studio UI (Streamlit), matching the AI Model Studio visual style."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_CodeVision_UI" / "output"

st.set_page_config(page_title="CodeVision Studio", page_icon="🎞️", layout="wide")
st.session_state.setdefault("dark_theme", False)
dark_theme = st.sidebar.toggle("الثيم الداكن", key="dark_theme")
if dark_theme:
    colors = {"bg":"#0b1220", "surface":"#111c2b", "ink":"#e5edf7", "muted":"#a8b7c9", "line":"rgba(148,163,184,.22)"}
else:
    colors = {"bg":"#f4f7fb", "surface":"#ffffff", "ink":"#0f172a", "muted":"#52637a", "line":"rgba(148,163,184,.24)"}
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html,body,[class*="css"],p,span,label,small,h1,h2,h3,h4,li{{font-family:'Cairo',Tahoma,sans-serif!important;color:{colors['ink']} }}
.stApp{{background:radial-gradient(ellipse 90% 38% at 50% 0%,rgba(14,165,233,.12),transparent 75%),{colors['bg']};color:{colors['ink']}}}
[data-testid="stSidebar"]{{background:{colors['surface']};border-left:1px solid {colors['line']}}}
[data-testid="stSidebar"] *{{color:{colors['ink']}!important}}
.hero{{padding:22px 26px;border-radius:20px;background:{colors['surface']};border:1px solid {colors['line']};box-shadow:0 14px 40px -24px rgba(15,23,42,.28);margin-bottom:16px}}
.hero h1{{font-size:27px;font-weight:800;margin:0;color:{colors['ink']}!important}}.hero p{{color:{colors['muted']}!important;margin:4px 0 0}}
div[data-testid="stMetric"]{{background:{colors['surface']};padding:14px 18px;border-radius:16px;border:1px solid {colors['line']};box-shadow:0 10px 30px -22px #334155}}
.block-container{{padding-top:1.7rem;max-width:1600px}}
button[kind="primary"]{{background:linear-gradient(135deg,#0284c7,#06a6b8);border:0;border-radius:11px;color:white!important}}
[data-testid="stFileUploader"]{{background:{colors['surface']};border-radius:14px;border:1px solid {colors['line']}}}
[data-testid="stFileUploader"] *{{color:{colors['ink']}!important}}
input,textarea,[data-baseweb="select"]>div{{color:{colors['ink']}!important;background:{colors['surface']}!important;border-color:{colors['line']}!important}}
[data-testid="stExpander"]{{background:{colors['surface']};border:1px solid {colors['line']};border-radius:12px}}
[data-testid="stStatusWidget"]{{background:{colors['surface']}}}
</style>
<div class="hero"><h1>CodeVision Studio</h1><p>استخرج الشيفرة والصوت من فيديوهات الدروس، ثم راجع الملفات والتفريغ على خط زمني واحد.</p></div>
""", unsafe_allow_html=True)

def initialize():
    st.session_state.setdefault("videos", {})
    st.session_state.setdefault("selected", None)

def process_video(upload):
    safe_name = Path(upload.name).name
    with tempfile.TemporaryDirectory(prefix="codevision-") as temp:
        video_path = Path(temp) / safe_name
        video_path.write_bytes(upload.getvalue())
        run_dir = OUT / (Path(safe_name).stem[:48] + "_" + str(abs(hash(safe_name)) % 100000))
        run_dir.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(ROOT / "codevision.py"), "--file", str(video_path),
               "--output", str(run_dir)]
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        dirs = [p for p in run_dir.iterdir() if p.is_dir()]
        result_dir = dirs[0] if dirs else run_dir
        transcript_file = result_dir / "transcript.json"
        transcript = None
        if transcript_file.exists():
            try:
                transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        scripts = list(result_dir.rglob("*.cs"))
        candidate_frames = list(result_dir.glob("CandidateFrames/*"))
        audio_file = result_dir / "audio.wav"
        return {"name": safe_name, "success": result.returncode == 0,
                "log": (result.stdout + "\n" + result.stderr)[-16000:],
                "transcript": transcript, "scripts": scripts,
                "frames": candidate_frames, "audio": audio_file if audio_file.exists() else None,
                "video": video_path.read_bytes()}

initialize()
with st.sidebar:
    st.markdown("### 🎞️ CodeVision")
    page = st.radio("مساحة العمل", ["الاستخراج والمراجعة", "التدريب والبيانات", "عن المشروع"], label_visibility="collapsed")
    st.caption("تشغيل محلي • البيانات تبقى على جهازك")
    st.divider()
    st.markdown("**قائمة الفيديوهات**")
    if st.session_state.videos:
        names = list(st.session_state.videos)
        selected = st.selectbox("اختر فيديو للتنقل", names, index=names.index(st.session_state.selected) if st.session_state.selected in names else 0)
        st.session_state.selected = selected
    else:
        st.caption("ارفع مجموعة فيديوهات لبدء العمل")

if page == "الاستخراج والمراجعة":
    uploads = st.file_uploader("اختر فيديوًا واحدًا أو عدة فيديوهات", type=["mp4", "mkv", "mov", "avi", "webm", "m4v"], accept_multiple_files=True)
    c1,c2,c3=st.columns([1,1,2])
    with c1: run = st.button("بدء استخراج القائمة", type="primary", disabled=not uploads, use_container_width=True)
    with c2: st.metric("الفيديوهات المختارة", len(uploads or []))
    if run and uploads:
        progress=st.progress(0, text="تهيئة قائمة الفيديوهات")
        for i, upload in enumerate(uploads):
            with st.status("معالجة {} ({}/{})".format(upload.name,i+1,len(uploads)), expanded=False) as status:
                try:
                    item=process_video(upload)
                    st.session_state.videos[upload.name]=item
                    st.session_state.selected=upload.name
                    status.update(label="اكتمل: "+upload.name if item["success"] else "تعذر: "+upload.name,state="complete" if item["success"] else "error")
                except Exception as exc:
                    st.error("{}: {}".format(upload.name,exc))
            progress.progress((i+1)/len(uploads), text="{} من {}".format(i+1,len(uploads)))
    name=st.session_state.selected
    if name and name in st.session_state.videos:
        item=st.session_state.videos[name]
        left,right=st.columns([1.15,.85],gap="large")
        with left:
            st.subheader("مشغل الدرس")
            st.video(item["video"])
            if item["audio"]: st.audio(item["audio"].read_bytes())
            st.subheader("التفريغ والخط الزمني")
            segments=(item["transcript"] or {}).get("segments",[])
            if segments:
                for seg in segments:
                    start=float(seg.get("start_sec",seg.get("start",0))); end=float(seg.get("end_sec",seg.get("end",0)))
                    with st.expander("{:02d}:{:02d} — {}".format(int(start//60),int(start%60),seg.get("text",""))):
                        st.write("من {:.2f} إلى {:.2f} ثانية".format(start,end))
            else: st.info("لم يتوفر تفريغ نصي. تحقق من وجود نموذج Whisper محليًا.")
        with right:
            st.subheader("الملفات المستعادة")
            if item["scripts"]:
                chosen=st.selectbox("ملف الشيفرة",item["scripts"],format_func=lambda p:p.name)
                code=chosen.read_text(encoding="utf-8",errors="replace")
                st.code(code,language=chosen.suffix.lstrip("."))
                st.download_button("تنزيل الملف",code,file_name=chosen.name)
            else: st.info("لم يُعثر على ملفات شيفرة مستعادة لهذا الفيديو.")
            st.subheader("إطارات مرشحة للكود")
            st.metric("عدد الإطارات",len(item["frames"]))
            if item["frames"]:
                st.image(str(item["frames"][0]),caption=item["frames"][0].name,use_container_width=True)
            with st.expander("سجل تشغيل المحرك"): st.code(item["log"] or "لا يوجد سجل")
elif page == "التدريب والبيانات":
    st.subheader("مختبر البيانات والتدريب")
    st.info("هذه اللوحة توضح المرحلة المخططة. لم يُبنَ بعد خط تدريب نموذج الرؤية ولا إدارة تسميات Dataset.")
    st.write("البيانات الحالية: مخرجات الاستخراج المحلية. الخطوة التالية هي إضافة مراجعة الإطارات وتسميتها ثم تقسيمها حسب الفيديو إلى تدريب/تحقق/اختبار.")
else:
    st.subheader("عن CodeVision")
    st.write("CodeVision يستخرج شيفرة الدروس ويجمعها مع التفريغ الصوتي والتوقيت ومصادر الأدلة.")
    st.write("الإصدار الحالي يعتمد FFmpeg وTesseract. التفريغ يحتاج faster-whisper أو openai-whisper وأوزانًا محلية.")
