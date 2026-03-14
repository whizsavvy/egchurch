# POST /api/hymns/delete — 찬송 한 곡 삭제
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
            req = urllib.request.Request(api_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    existing = json.loads(r.read().decode("utf-8"))
                    sha = existing.get("sha")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self._send(200, {"ok": True, "title": title})
                    return
                self._send(e.code, {"detail": "파일을 찾을 수 없습니다."})
                return
            if not sha:
                self._send(400, {"detail": "삭제할 수 없습니다."})
                return
            del_body = {"message": f"chore: 찬송 삭제 - {title[:30]}", "sha": sha}
            del_req = urllib.request.Request(api_url, data=json.dumps(del_body).encode("utf-8"), headers=headers, method="DELETE")
            with urllib.request.urlopen(del_req, timeout=15) as r:
                pass
            self._send(200, {"ok": True, "title": title})
        except urllib.error.HTTPError as e:
            try:
                msg = e.read().decode()
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
