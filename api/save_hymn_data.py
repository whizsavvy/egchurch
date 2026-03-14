# Vercel Serverless: POST /api/save_hymn_data — GitHub에 찬송가 목록 저장
import base64
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GITHUB_REPO = os.environ.get("GITHUB_REPO") or "whizsavvy/egchurch"
DATA_PATH = "data/hymn_data.json"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            token = os.environ.get("GITHUB_TOKEN", "").strip()
            if not token:
                self._json_response(503, {"detail": "GITHUB_TOKEN이 설정되지 않았습니다. Vercel 환경 변수에 추가해 주세요."})
                return
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json_response(400, {"detail": "JSON 본문이 필요합니다."})
                return
            content = (data.get("content") or "").strip()
            intro = (data.get("intro") or "").strip()
            payload = {"content": content, "intro": intro}
            body_json = json.dumps(payload, ensure_ascii=False, indent=2)
            body_b64 = base64.b64encode(body_json.encode("utf-8")).decode("ascii")

            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_PATH}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            }
            get_req = urllib.request.Request(api_url, headers=headers)
            try:
                with urllib.request.urlopen(get_req, timeout=10) as r:
                    existing = json.loads(r.read().decode("utf-8"))
                    sha = existing.get("sha")
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    self._json_response(e.code, {"detail": "GitHub API 오류: " + str(e.read().decode())})
                    return
                sha = None

            put_body = {"message": "chore: update hymn_data.json", "content": body_b64}
            if sha:
                put_body["sha"] = sha
            put_req = urllib.request.Request(
                api_url,
                data=json.dumps(put_body).encode("utf-8"),
                headers=headers,
                method="PUT",
            )
            with urllib.request.urlopen(put_req, timeout=15) as r:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else str(e)
            self._json_response(e.code, {"detail": "GitHub API 오류: " + err_body})
        except Exception as e:
            self._json_response(500, {"detail": str(e)})

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
