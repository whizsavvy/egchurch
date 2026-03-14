# POST /api/hymns/save — 찬송 한 곡 저장 (생성/수정)
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import quote
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.hymn_files import HYMN_DIR, GITHUB_REPO, sanitize_filename


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            token = os.environ.get("GITHUB_TOKEN", "").strip()
            if not token:
                self._send(503, {"detail": "GITHUB_TOKEN이 설정되지 않았습니다."})
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send(400, {"detail": "JSON 본문이 필요합니다."})
                return
            title = (data.get("title") or "").strip()
            content = (data.get("content") or "").strip()
            if not title:
                self._send(400, {"detail": "title이 필요합니다."})
                return
            repo = os.environ.get("GITHUB_REPO") or GITHUB_REPO
            filename = sanitize_filename(title) + ".txt"
            path = f"{HYMN_DIR}/{filename}"
            path_encoded = quote(path, safe="/")
            api_url = f"https://api.github.com/repos/{repo}/contents/{path_encoded}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            }
            sha = None
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as r:
                    existing = json.loads(r.read().decode("utf-8"))
                    sha = existing.get("sha")
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    self._send(e.code, {"detail": "파일 조회 실패"})
                    return
            body_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
            put = {"message": f"chore: 찬송 저장 - {title[:30]}", "content": body_b64}
            if sha:
                put["sha"] = sha
            put_req = urllib.request.Request(api_url, data=json.dumps(put).encode("utf-8"), headers=headers, method="PUT")
            with urllib.request.urlopen(put_req, timeout=15) as r:
                pass
            self._send(200, {"ok": True, "title": title})
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode()
                err_data = json.loads(err_body) if err_body else {}
                msg = err_data.get("message", err_body)
            except Exception:
                msg = str(e)
            self._send(e.code, {"detail": msg})
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
