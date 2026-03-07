"""
교회 자막 웹앱 API: DOCX 파싱, 슬라이드 코드 실행, PPTX 다운로드.
"""
from __future__ import annotations
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from docx_parser import get_red_runs_summary, parse_docx
from slide_runner import run_sermon_code

app = FastAPI(title="늘푸른교회 자막 웹앱", version="1.0.0")

# 정적 파일 (프론트엔드)
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class GeneratePptxBody(BaseModel):
    code: str
    hymn_list: list[str] | None = None
    card_slides: list[str] | None = None


@app.get("/")
def index():
    """프론트엔드 페이지."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "API만 사용하려면 /docs 를 이용하세요."})


@app.post("/api/parse-docx")
async def api_parse_docx(file: UploadFile = File(...)):
    """
    설교 원고 DOCX를 업로드하면 단락·런 단위로 파싱하여 반환합니다.
    RED(#FF0000) 런만 추출한 요약도 함께 반환합니다.
    """
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "DOCX 파일만 업로드 가능합니다.")
    raw = await file.read()
    try:
        parsed = parse_docx(raw)
        red_summary = get_red_runs_summary(parsed)
        return {
            "parsed": parsed,
            "red_summary": red_summary,
            "message": "이 parsed 구조를 설교 자막 프롬프트와 함께 AI에 넣고, 생성된 코드를 아래 '코드로 PPTX 생성'에 붙여넣으세요.",
        }
    except Exception as e:
        raise HTTPException(422, f"DOCX 파싱 실패: {e}") from e


@app.post("/api/generate-pptx")
async def api_generate_pptx(body: GeneratePptxBody):
    """
    설교 자막용 코드 + (선택) 찬송 목록 + (선택) 카드 슬라이드를 받아
    PPTX를 생성하고 다운로드합니다.
    """
    code = (body.code or "").strip()
    if not code:
        raise HTTPException(400, "코드를 입력해 주세요.")
    hymn_list = body.hymn_list or []
    card_slides = body.card_slides or []
    try:
        out_path = run_sermon_code(code, hymn_list=hymn_list, card_slides=card_slides)
        return FileResponse(
            out_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=os.path.basename(out_path),
        )
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"PPTX 생성 중 오류: {e}") from e


@app.get("/api/health")
def health():
    return {"status": "ok"}
