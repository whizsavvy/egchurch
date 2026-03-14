# GET /api/hymns/merged — PPT용 전체 병합 문자열 (제목\n------\n가사 형식)
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.hymn_files import HYMN_DIR, GITHUB_REPO, filename_to_title


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            repo = os.environ.get("GITHUB_REPO") or GITHUB_REPO
            token = os.environ.get("GITHUB_TOKEN", "").strip()
            list_url = f"https://api.github.com/repos/{repo}/contents/{HYMN_DIR}"
            headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(list_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    items = json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"")
                    return
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"")
                return
            if not isinstance(items, list):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"")
                return
            files = [f for f in items if f.get("name", "").endswith(".txt")]
            files.sort(key=lambda f: filename_to_title(f.get("name", "")))
            parts = []
            raw_headers = {"Accept": "application/vnd.github.raw"}
            if token:
                raw_headers["Authorization"] = f"Bearer {token}"
            for f in files:
                name = f.get("name", "")
                title = filename_to_title(name)
                try:
                    rreq = urllib.request.Request(
                        f"https://api.github.com/repos/{repo}/contents/{HYMN_DIR}/{name}",
                        headers=raw_headers,
                    )
                    with urllib.request.urlopen(rreq, timeout=10) as r:
                        raw = r.read().decode("utf-8")
                    content = raw.strip()
                except Exception:
                    content = ""
                parts.append(title + "\n------\n" + content)
            merged = "\n\n".join(parts)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(merged.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
