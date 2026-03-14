# Vercel Serverless: POST /api/generate_pptx — 코드 + 찬송/카드 받아 PPTX 생성 후 바이너리 반환
import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.hymn_format import user_to_hymn_txt
from lib.slide_runner import run_sermon_code


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json_response(400, {"detail": "JSON 본문이 필요합니다."})
                return
            code = (data.get("code") or "").strip()
            if not code:
                self._json_response(400, {"detail": "코드를 입력해 주세요."})
                return
            hymn_list = data.get("hymn_list") or []
            card_slides = data.get("card_slides") or []
            hymn_txt_raw = (data.get("hymn_txt_content") or "").strip()
            hymn_txt_content = user_to_hymn_txt(hymn_txt_raw) if hymn_txt_raw else None
            full_order = bool(data.get("full_order"))
            hymn_list_intro = data.get("hymn_list_intro") or []
            if full_order and isinstance(hymn_list_intro, list) and len(hymn_list_intro) < 5:
                hymn_list_intro = (hymn_list_intro + ["", "", "", "", ""])[:5]
            out_path = run_sermon_code(
                code,
                hymn_list=hymn_list,
                card_slides=card_slides,
                hymn_txt_content=hymn_txt_content,
                full_order=full_order,
                hymn_list_intro=hymn_list_intro if full_order else None,
            )
            with open(out_path, "rb") as f:
                pptx_bytes = f.read()
            try:
                os.remove(out_path)
            except Exception:
                pass
            filename = os.path.basename(out_path)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(pptx_bytes)
        except FileNotFoundError as e:
            self._json_response(503, {"detail": str(e)})
        except RuntimeError as e:
            self._json_response(422, {"detail": str(e)})
        except Exception as e:
            self._json_response(500, {"detail": f"PPTX 생성 중 오류: {e}"})

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
