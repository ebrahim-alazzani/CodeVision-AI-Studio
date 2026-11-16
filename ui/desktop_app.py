"""CodeVision Studio desktop Runtime UI. Requires PySide6."""
import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QApplication, QComboBox, QDockWidget, QFileDialog,
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QPlainTextEdit, QSlider, QSplitter,
    QTabWidget, QToolBar, QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_CodeVision_UI" / "output"

LIGHT = """
QMainWindow,QWidget{background:#f4f7fb;color:#14233a;font-family:'Cairo','Segoe UI',sans-serif;font-size:13px}
QFrame#panel,QDockWidget QWidget{background:rgba(255,255,255,245);border:1px solid #e1e9f0;border-radius:14px}
QToolBar{background:rgba(255,255,255,235);border:0;border-bottom:1px solid #dfe7ef;padding:8px;spacing:8px}
QPushButton{background:#f0f6fa;border:1px solid #d8e5ed;border-radius:9px;padding:9px 13px;color:#344b63}
QPushButton:hover{background:#e2f7fa;border-color:#67c9d1} QPushButton#primary{background:#078eaa;color:white;border:0;font-weight:700}
QListWidget,QPlainTextEdit,QComboBox{background:white;border:1px solid #e0e8ef;border-radius:9px;padding:7px}
QListWidget::item{padding:9px;border-radius:7px} QListWidget::item:selected{background:#dff5f7;color:#056a7b}
QTabWidget::pane{border:1px solid #e0e8ef;background:white;border-radius:10px} QTabBar::tab{padding:9px 15px}
QSlider::groove:horizontal{height:5px;background:#dbe7ef;border-radius:3px} QSlider::handle:horizontal{width:14px;background:#06b6d4;border-radius:7px;margin:-5px 0}
QProgressBar{border:0;background:#e8eff4;border-radius:5px;height:9px} QProgressBar::chunk{background:#06b6d4;border-radius:5px}
"""
DARK = """
QMainWindow,QWidget{background:#0b1220;color:#e4edf7;font-family:'Cairo','Segoe UI',sans-serif;font-size:13px}
QFrame#panel,QDockWidget QWidget{background:#111c2b;border:1px solid #26374a;border-radius:14px}
QToolBar{background:#111a27;border:0;border-bottom:1px solid #26374a;padding:8px;spacing:8px}
QPushButton{background:#19283a;border:1px solid #2a4055;border-radius:9px;padding:9px 13px;color:#dbe8f5}
QPushButton:hover{background:#163547;border-color:#168b9a} QPushButton#primary{background:#087c97;color:white;border:0;font-weight:700}
QListWidget,QPlainTextEdit,QComboBox{background:#0f1926;border:1px solid #26374a;border-radius:9px;padding:7px;color:#e4edf7}
QListWidget::item{padding:9px;border-radius:7px} QListWidget::item:selected{background:#12394a;color:#9de8ed}
QTabWidget::pane{border:1px solid #26374a;background:#111c2b;border-radius:10px} QTabBar::tab{padding:9px 15px}
QSlider::groove:horizontal{height:5px;background:#26374a;border-radius:3px} QSlider::handle:horizontal{width:14px;background:#06b6d4;border-radius:7px;margin:-5px 0}
QProgressBar{border:0;background:#1d2b3d;border-radius:5px;height:9px} QProgressBar::chunk{background:#06b6d4;border-radius:5px}
"""


class ExtractWorker(QThread):
    progress = Signal(str)
    finished_video = Signal(str, bool, str)
    all_done = Signal()

    def __init__(self, videos):
        super().__init__(); self.videos = videos

    def run(self):
        for index, video in enumerate(self.videos, 1):
            self.progress.emit(f"{index}/{len(self.videos)} — {video.name}")
            destination = OUT / (video.stem[:45] + "_" + str(abs(hash(str(video))) % 100000))
            destination.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, str(ROOT / "codevision.py"), "--file", str(video),
                       "--output", str(destination)]
            try:
                result = subprocess.run(command, cwd=str(ROOT), capture_output=True,
                    text=True, encoding="utf-8", errors="replace")
                self.finished_video.emit(str(video), result.returncode == 0,
                    (result.stdout + "\n" + result.stderr)[-12000:])
            except Exception as exc:
                self.finished_video.emit(str(video), False, str(exc))
        self.all_done.emit()


class Studio(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("CodeVision Studio"); self.resize(1540, 940)
        self.videos = []; self.dark = False; self.latest_logs = ""; self.active_output = None
        self.player = QMediaPlayer(self); self.audio = QAudioOutput(self); self.player.setAudioOutput(self.audio)
        self.build_ui(); self.apply_theme()

    def panel(self, title):
        box=QFrame(); box.setObjectName("panel"); lay=QVBoxLayout(box); lay.setContentsMargins(14,12,14,12); lay.setSpacing(9)
        label=QLabel(title); label.setStyleSheet("font-size:15px;font-weight:800;border:0;background:transparent")
        lay.addWidget(label); return box,lay

    def build_ui(self):
        bar=QToolBar("Workspace"); bar.setMovable(False); self.addToolBar(bar)
        title=QLabel("  CodeVision Studio  ·  Video-to-Code Workspace  "); title.setStyleSheet("font-size:17px;font-weight:800")
        bar.addWidget(title); bar.addSeparator()
        add=QAction("＋ إضافة فيديوهات",self); add.triggered.connect(self.add_videos); bar.addAction(add)
        run=QAction("▶ استخراج المحدد / الكل",self); run.triggered.connect(self.start_extraction); bar.addAction(run)
        theme=QAction("◐ الثيم",self); theme.triggered.connect(self.toggle_theme); bar.addAction(theme)
        root=QWidget(); self.setCentralWidget(root); layout=QHBoxLayout(root); layout.setContentsMargins(14,12,14,14); layout.setSpacing(12)
        split=QSplitter(Qt.Horizontal); layout.addWidget(split)
        side,sl=self.panel("المكتبة والدروس"); side.setMinimumWidth(230); side.setMaximumWidth(340)
        self.video_list=QListWidget(); self.video_list.currentRowChanged.connect(self.select_video)
        sl.addWidget(self.video_list,1)
        self.queue_status=QLabel("جاهز لإضافة فيديوهات"); self.queue_status.setWordWrap(True); sl.addWidget(self.queue_status)
        self.progress=QProgressBar(); self.progress.setValue(0); sl.addWidget(self.progress)
        split.addWidget(side)
        center=QSplitter(Qt.Vertical)
        player_panel,pl=self.panel("مشغل الدرس"); self.video_widget=QVideoWidget(); self.video_widget.setMinimumHeight(350)
        self.player.setVideoOutput(self.video_widget); pl.addWidget(self.video_widget,1)
        controls=QHBoxLayout(); play=QPushButton("▶ / ⏸"); play.clicked.connect(lambda:self.player.play() if self.player.playbackState()!=QMediaPlayer.PlaybackState.PlayingState else self.player.pause()); controls.addWidget(play)
        self.clock=QLabel("00:00 / 00:00"); controls.addWidget(self.clock)
        self.seek=QSlider(Qt.Horizontal); self.seek.sliderMoved.connect(self.player.setPosition); self.player.positionChanged.connect(self.seek.setValue); self.player.durationChanged.connect(self.set_duration); controls.addWidget(self.seek,1)
        pl.addLayout(controls); center.addWidget(player_panel)
        self.player.positionChanged.connect(self.update_clock)
        tabs=QTabWidget(); self.transcript=QPlainTextEdit(); self.transcript.setReadOnly(False); tabs.addTab(self.transcript,"التفريغ الصوتي")
        self.log_view=QPlainTextEdit(); self.log_view.setReadOnly(True); tabs.addTab(self.log_view,"سجل الاستخراج")
        center.addWidget(tabs); center.setSizes([620,230]); split.addWidget(center)
        right,right_l=self.panel("المشروع المستعاد"); right.setMinimumWidth(330); right.setMaximumWidth(500)
        self.file_select=QComboBox(); self.file_select.currentIndexChanged.connect(self.open_script); right_l.addWidget(self.file_select)
        self.code=QPlainTextEdit(); self.code.setPlaceholderText("سيظهر هنا ملف الشيفرة الذي تم استخراجه..."); self.code.setFont(QFont("Cascadia Code",10)); right_l.addWidget(self.code,1)
        save=QPushButton("حفظ نسخة من الشيفرة"); save.clicked.connect(self.save_script); right_l.addWidget(save)
        split.addWidget(right); split.setSizes([260,850,390])

    def apply_theme(self): self.setStyleSheet(DARK if self.dark else LIGHT)
    def toggle_theme(self): self.dark=not self.dark; self.apply_theme()
    def add_videos(self):
        names,_=QFileDialog.getOpenFileNames(self,"اختر فيديوهات الدروس","", "Video files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v)")
        for name in names:
            p=Path(name)
            if p not in self.videos:
                self.videos.append(p); self.video_list.addItem(QListWidgetItem(p.name))
        if names:self.video_list.setCurrentRow(0 if self.video_list.currentRow()<0 else self.video_list.currentRow())
        self.queue_status.setText(f"{len(self.videos)} فيديو في المكتبة — يمكن التنقل بينها من القائمة")
    def select_video(self,row):
        if 0<=row<len(self.videos):self.player.setSource(QUrl.fromLocalFile(str(self.videos[row])))
    def start_extraction(self):
        row=self.video_list.currentRow(); selected=[self.videos[row]] if row>=0 else list(self.videos)
        if not selected:QMessageBox.information(self,"CodeVision","أضف فيديوًا واحدًا أو أكثر أولًا");return
        self.progress.setRange(0,len(selected)); self.progress.setValue(0)
        self.worker=ExtractWorker(selected); self.worker.progress.connect(self.queue_status.setText)
        self.worker.finished_video.connect(self.on_video_done); self.worker.all_done.connect(lambda:self.queue_status.setText("انتهى استخراج القائمة")); self.worker.start()
    def on_video_done(self,name,success,log):
        self.latest_logs=log; self.log_view.setPlainText(log); self.progress.setValue(self.progress.value()+1)
        self.queue_status.setText(("اكتمل: " if success else "فشل: ")+Path(name).name)
        self.load_outputs(name)
    def load_outputs(self,name):
        matches=list(OUT.glob(Path(name).stem[:45]+"_*/"+Path(name).stem[:35]+"*/"))
        if not matches:return
        self.active_output=matches[-1]; scripts=list(self.active_output.rglob("*.cs")); self.file_select.blockSignals(True); self.file_select.clear()
        for s in scripts:self.file_select.addItem(s.name,str(s))
        self.file_select.blockSignals(False)
        transcripts=list(self.active_output.rglob("transcript.json"))
        if transcripts:
            try:
                data=json.loads(transcripts[0].read_text(encoding="utf-8")); self.transcript.setPlainText("\n".join("[{:.2f}-{:.2f}] {}".format(x.get("start_sec",0),x.get("end_sec",0),x.get("text","")) for x in data.get("segments",[])))
            except Exception:pass
        if scripts:self.open_script(0)
    def open_script(self,index):
        path=self.file_select.itemData(index)
        if path and Path(path).exists():self.code.setPlainText(Path(path).read_text(encoding="utf-8",errors="replace"))
    def save_script(self):
        path,_=QFileDialog.getSaveFileName(self,"حفظ الشيفرة","reconstructed_code.cs","Source files (*.cs *.dart *.py *.txt)")
        if path:Path(path).write_text(self.code.toPlainText(),encoding="utf-8")
    def set_duration(self,d):self.seek.setRange(0,d);self.clock.setText("00:00 / "+self.time(d))
    def update_clock(self,p):self.clock.setText(self.time(p)+" / "+self.time(self.player.duration()))
    @staticmethod
    def time(ms):return f"{ms//60000:02d}:{(ms//1000)%60:02d}"


def main():
    app=QApplication(sys.argv); window=Studio(); window.showMaximized(); sys.exit(app.exec())


if __name__=="__main__":main()
