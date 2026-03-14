# GET /api/hymns/list — 찬송 목록 (data/hymns/*.txt)
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
            url = f"https://api.github.com/repos/{repo}/contents/{HYMN_DIR}"
            headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    items = json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    items = []
                else:
                    self._send(500, {"detail": "목록 조회 실패"})
                    return
            if not isinstance(items, list):
                items = []
            titles = [filename_to_title(f.get("name", "")) for f in items if f.get("name", "").endswith(".txt")]
            titles.sort(key=lambda x: x)
            self._send(200, {"items": titles})
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
