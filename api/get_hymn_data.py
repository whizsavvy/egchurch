# Vercel Serverless: GET /api/get_hymn_data — GitHub에서 찬송가 목록 불러오기
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# GitHub raw URL (main 브랜치)
GITHUB_RAW = os.environ.get("HYMN_GITHUB_RAW") or "https://raw.githubusercontent.com/whizsavvy/egchurch/main/data/hymn_data.json"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            try:
                req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent": "egchurch-app"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read().decode("utf-8")
                    data = json.loads(body)
            except Exception:
                data = {"content": "", "intro": ""}
            if not isinstance(data, dict):
                data = {"content": "", "intro": ""}
            out = {"content": data.get("content", "") or "", "intro": data.get("intro", "") or ""}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(e)}, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
