"""Loopback-only local UI server for CodeVision Extractor."""
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
UI = Path(__file__).resolve().parent
DATA = ROOT / "_CodeVision_UI"
INBOX = DATA / "inbox"
OUTPUT = DATA / "output"
JOBS = {}
LOCK = threading.Lock()


def execute_job(job_id, video_path, output_path):
    log_path = output_path / "run.log"
    output_path.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT / "codevision.py"), "--file", str(video_path),
               "--output", str(output_path / "results")]
    try:
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            proc = subprocess.Popen(command, cwd=str(ROOT), stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
            with LOCK:
                JOBS[job_id]["process"] = proc
            code = proc.wait()
        with LOCK:
            JOBS[job_id]["status"] = "completed" if code == 0 else "failed"
            JOBS[job_id]["exit_code"] = code
    except Exception as exc:
        with LOCK:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(exc)


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        match = re.fullmatch(r"/api/jobs/([a-f0-9]+)", path)
        if match:
            job_id = match.group(1)
            with LOCK:
                job = JOBS.get(job_id)
                if not job:
                    return self._json({"error": "job not found"}, 404)
                snapshot = {k: v for k, v in job.items() if k != "process"}
            log_file = Path(snapshot["output"]) / "run.log"
            snapshot["log"] = log_file.read_text(encoding="utf-8", errors="replace")[-16000:] if log_file.exists() else ""
            result_dir = Path(snapshot["output"]) / "results"
            snapshot["scripts"] = [str(p.relative_to(result_dir)) for p in result_dir.rglob("*.cs")] if result_dir.exists() else []
            transcripts = list(result_dir.rglob("transcript.json")) if result_dir.exists() else []
            snapshot["transcript"] = None
            if transcripts:
                try:
                    snapshot["transcript"] = json.loads(transcripts[0].read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    pass
            return self._json(snapshot)
        if path.startswith("/api/files/"):
            rel = unquote(path[len("/api/files/"):])
            base = OUTPUT.resolve()
            target = (base / rel).resolve()
            if not target.is_relative_to(base) or not target.is_file():
                return self._json({"error": "file not found"}, 404)
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        asset = (UI / path.lstrip("/")).resolve()
        if not asset.is_relative_to(UI.resolve()) or not asset.is_file():
            return self._json({"error": "not found"}, 404)
        body = asset.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path != "/api/upload":
            return self._json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 2 * 1024 * 1024 * 1024:
            return self._json({"error": "video size must be between 1 byte and 2 GB"}, 413)
        name = Path(self.headers.get("X-Video-Name", "video.mp4")).name
        name = re.sub(r"[^\w. -]", "_", name).strip(" .") or "video.mp4"
        if Path(name).suffix.lower() not in {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}:
            return self._json({"error": "unsupported video extension"}, 415)
        INBOX.mkdir(parents=True, exist_ok=True)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        video_path = INBOX / (job_id + "_" + name)
        remaining = length
        with video_path.open("wb") as video_file:
            while remaining:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                video_file.write(chunk)
                remaining -= len(chunk)
        if remaining:
            video_path.unlink(missing_ok=True)
            return self._json({"error": "upload ended before the complete video arrived"}, 400)
        out = OUTPUT / job_id
        with LOCK:
            JOBS[job_id] = {"id": job_id, "name": name, "status": "queued", "output": str(out)}
        threading.Thread(target=execute_job, args=(job_id, video_path, out), daemon=True).start()
        self._json({"id": job_id, "name": name, "status": "queued"}, 202)

    def log_message(self, fmt, *args):
        print("[CodeVision UI] " + fmt % args)


def main():
    import webbrowser
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("CodeVision Studio: http://127.0.0.1:8765")
    threading.Timer(0.7, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
