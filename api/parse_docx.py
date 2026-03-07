# Vercel Serverless: POST /api/parse_docx — DOCX 업로드 시 파싱 후 JSON 반환
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.docx_parser import get_red_runs_summary, parse_docx


def parse_multipart(body: bytes, content_type: str):
    if not content_type or "boundary=" not in content_type:
        return None
    boundary = content_type.split("boundary=")[-1].strip().strip('"').strip()
    if not boundary:
        return None
    boundary_b = boundary.encode() if isinstance(boundary, str) else boundary
    parts = body.split(b"--" + boundary_b)
    for part in parts:
        if b"Content-Disposition: form-data" not in part or b"filename=" not in part:
            continue
        if b"\r\n\r\n" in part:
            _, rest = part.split(b"\r\n\r\n", 1)
        elif b"\n\n" in part:
            _, rest = part.split(b"\n\n", 1)
        else:
            continue
        if rest.endswith(b"\r\n"):
            rest = rest[:-2]
        return rest
    return None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""
            content_type = self.headers.get("Content-Type", "")
            raw = parse_multipart(body, content_type)
            if not raw:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "DOCX 파일을 첨부해 주세요."}, ensure_ascii=False).encode("utf-8"))
                return
            parsed = parse_docx(raw)
            red_summary = get_red_runs_summary(parsed)
            out = {
                "parsed": parsed,
                "red_summary": red_summary,
                "message": "이 parsed 구조를 설교 자막 프롬프트와 함께 AI에 넣고, 생성된 코드를 4단계에 붙여넣으세요.",
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.send_response(422)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": f"DOCX 파싱 실패: {e}"}, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
