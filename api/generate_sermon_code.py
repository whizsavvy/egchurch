# Vercel Serverless: POST /api/generate_sermon_code — 파싱된 DOCX로 설교 자막 코드 생성
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.sermon_prompt import SERMON_CODE_SYSTEM


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                self._json_response(503, {"detail": "OPENAI_API_KEY가 설정되지 않았습니다. Vercel 환경 변수에 추가해 주세요."})
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
            parsed = data.get("parsed")
            if not parsed:
                self._json_response(400, {"detail": "parsed (DOCX 파싱 결과)가 필요합니다."})
                return

            try:
                import openai
            except ImportError:
                self._json_response(503, {"detail": "openai 패키지가 설치되지 않았습니다."})
                return

            client = openai.OpenAI(api_key=api_key)
            user_msg = (
                "Below is the DOCX parsed structure (paragraphs and runs with text and color_hex). "
                "Generate ONLY the Python code lines (add_bible_slide, add_subtitle_slide). "
                "Output nothing but the code, one function call per line.\n\n"
                + json.dumps(parsed, ensure_ascii=False, indent=0)
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SERMON_CODE_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
            )
            code = (resp.choices[0].message.content or "").strip()
            # 마크다운 코드블록 제거
            if code.startswith("```"):
                lines = code.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"code": code}, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            err = str(e)
            if "api_key" in err.lower() or "auth" in err.lower():
                status = 401
            else:
                status = 500
            self._json_response(status, {"detail": f"코드 생성 실패: {err}"})

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
