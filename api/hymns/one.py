# GET /api/hymns/one?title=제목 — 찬송 한 곡 내용 (없으면 기존 hymn.txt에서)
import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import parse_qs, urlparse, quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.hymn_files import HYMN_DIR, GITHUB_REPO, sanitize_filename
from lib.hymn_legacy import legacy_one


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            q = parse_qs(parsed.query)
            title = (q.get("title") or [""])[0].strip()
            if not title:
                self._send(400, {"detail": "title 필요"})
                return
            content = None
            repo = os.environ.get("GITHUB_REPO") or GITHUB_REPO
            filename = sanitize_filename(title) + ".txt"
            path_segment = f"{HYMN_DIR}/{filename}"
            encoded_path = quote(path_segment, safe="/")
            url = f"https://api.github.com/repos/{repo}/contents/{encoded_path}"
            headers = {"Accept": "application/vnd.github.raw"}
            token = os.environ.get("GITHUB_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as r:
                    content = r.read().decode("utf-8")
            except Exception:
                content = None
            if content is None:
                content = legacy_one(title)
            self._send(200, {"title": title, "content": content or ""})
        except Exception as e:
            self._send(500, {"detail": str(e)})

    def _send(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
