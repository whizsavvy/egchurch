# Vercel Serverless: POST /api/generate_pptx — 코드 + 찬송/카드 받아 PPTX 생성 후 바이너리 반환
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _get_runner():
    from lib.hymn_format import user_to_hymn_txt
    from lib.slide_runner import run_sermon_code, run_worship_order
    return user_to_hymn_txt, run_sermon_code, run_worship_order


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        def safe_send(status, data):
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        try:
            try:
                user_to_hymn_txt, run_sermon_code, run_worship_order = _get_runner()
            except Exception as load_err:
                safe_send(503, {"detail": f"PPT 엔진 로드 실패: {load_err}. EvergreenSlideMaker가 배포에 포함되어 있는지 확인하세요."})
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length else b"{}"
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    safe_send(400, {"detail": "JSON 본문이 필요합니다."})
                    return

                worship_order = data.get("worship_order")
                if isinstance(worship_order, list) and len(worship_order) > 0:
                    hymn_txt_raw = (data.get("hymn_txt_content") or "").strip()
                    hymn_txt_content = user_to_hymn_txt(hymn_txt_raw) if hymn_txt_raw else None
                    out_path = run_worship_order(worship_order, hymn_txt_content=hymn_txt_content)
                else:
                    code = (data.get("code") or "").strip()
                    if not code:
                        safe_send(400, {"detail": "코드 또는 worship_order를 입력해 주세요."})
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
                safe_send(503, {"detail": str(e)})
            except ImportError as e:
                safe_send(503, {"detail": f"모듈 로드 실패: {e}. EvergreenSlideMaker 폴더가 배포에 포함되어 있는지 확인하세요."})
            except RuntimeError as e:
                safe_send(422, {"detail": str(e)})
            except Exception as e:
                msg = str(e).strip() or type(e).__name__
                if not msg:
                    msg = "알 수 없는 오류"
                safe_send(500, {"detail": f"PPTX 생성 중 오류: {msg}"})
        except Exception as outer:
            try:
                safe_send(500, {"detail": f"서버 오류: {outer}"})
            except Exception:
                pass

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
