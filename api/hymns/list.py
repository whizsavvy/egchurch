# GET /api/hymns/list — 찬송 목록 (data/hymns/*.txt, 비어 있으면 기존 hymn.txt)
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
from lib.hymn_legacy import legacy_titles


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
            titles = []
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    items = json.loads(r.read().decode("utf-8"))
                if isinstance(items, list):
                    titles = [filename_to_title(f.get("name", "")) for f in items if f.get("name", "").endswith(".txt")]
            except urllib.error.HTTPError:
                pass  # 403, 404 등이면 legacy 사용
            except Exception:
                pass
            if not titles:
                titles = legacy_titles()
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
