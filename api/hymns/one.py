# GET /api/hymns/one?title=제목 — 찬송 한 곡 내용 (없으면 기존 hymn.txt에서)
import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import parse_qs, urlparse

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
            repo = os.environ.get("GITHUB_REPO") or GITHUB_REPO
            filename = sanitize_filename(title) + ".txt"
            url = f"https://api.github.com/repos/{repo}/contents/{HYMN_DIR}/{filename}"
            headers = {"Accept": "application/vnd.github.raw"}
            token = os.environ.get("GITHUB_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    content = r.read().decode("utf-8")
                self._send(200, {"title": title, "content": content})
                return
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    self._send(e.code, {"detail": "조회 실패"})
                    return
            content = legacy_one(title)
            self._send(200, {"title": title, "content": content})
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
