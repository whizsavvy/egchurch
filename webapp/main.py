"""
교회 자막 웹앱 API: DOCX 파싱, 설교 코드 생성, PPTX 다운로드.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from docx_parser import get_red_runs_summary, parse_docx
from slide_runner import run_sermon_code, run_worship_order

# lib 경로 (설교 코드 생성·찬송 포맷용)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
try:
    from lib.hymn_format import user_to_hymn_txt
    from lib.sermon_prompt import SERMON_CODE_SYSTEM
except ImportError:
    user_to_hymn_txt = None
    SERMON_CODE_SYSTEM = ""

app = FastAPI(title="늘푸른교회 자막 웹앱", version="1.0.0")

# 정적 파일 (프론트엔드)
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class GeneratePptxBody(BaseModel):
    code: str = ""
    worship_order: list[dict] | None = None
    hymn_list: list[str] | None = None
    card_slides: list[str] | None = None
    hymn_txt_content: str | None = None
    full_order: bool = False
    hymn_list_intro: list[str] | None = None


class GenerateSermonCodeBody(BaseModel):
    parsed: list[dict]


@app.get("/")
def index():
    """프론트엔드 페이지."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "API만 사용하려면 /docs 를 이용하세요."})


@app.post("/api/parse-docx")
@app.post("/api/parse_docx")
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


@app.post("/api/generate_sermon_code")
async def api_generate_sermon_code(body: GenerateSermonCodeBody):
    """파싱된 DOCX로 설교 자막 코드를 AI가 생성합니다. OPENAI_API_KEY 필요."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(503, "OPENAI_API_KEY가 설정되지 않았습니다.")
    if not (body.parsed or []):
        raise HTTPException(400, "parsed (DOCX 파싱 결과)가 필요합니다.")
    try:
        import openai
    except ImportError:
        raise HTTPException(503, "openai 패키지가 설치되지 않았습니다.")
    client = openai.OpenAI(api_key=api_key)
    user_msg = (
        "Below is the DOCX parsed structure. Generate ONLY the Python code lines "
        "(add_bible_slide, add_subtitle_slide). Output nothing but the code, one per line.\n\n"
        + __import__("json").dumps(body.parsed, ensure_ascii=False, indent=0)
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
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    return {"code": code}


@app.post("/api/generate-pptx")
@app.post("/api/generate_pptx")
async def api_generate_pptx(body: GeneratePptxBody):
    """
    worship_order가 있으면 순서대로 PPT 생성; 없으면 code + 찬송/카드로 생성합니다.
    """
    worship_order = body.worship_order or []
    if isinstance(worship_order, list) and len(worship_order) > 0:
        hymn_txt_raw = (body.hymn_txt_content or "").strip()
        hymn_txt_content = user_to_hymn_txt(hymn_txt_raw) if hymn_txt_raw and user_to_hymn_txt else None
        try:
            out_path = run_worship_order(worship_order, hymn_txt_content=hymn_txt_content)
            return FileResponse(
                out_path,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                filename=os.path.basename(out_path),
            )
        except FileNotFoundError as e:
            raise HTTPException(503, str(e)) from e
        except Exception as e:
            raise HTTPException(500, f"PPTX 생성 중 오류: {e}") from e

    code = (body.code or "").strip()
    if not code:
        raise HTTPException(400, "코드 또는 worship_order를 입력해 주세요.")
    hymn_list = body.hymn_list or []
    card_slides = body.card_slides or []
    hymn_txt_raw = (body.hymn_txt_content or "").strip()
    hymn_txt_content = user_to_hymn_txt(hymn_txt_raw) if hymn_txt_raw and user_to_hymn_txt else None
    full_order = body.full_order
    hymn_list_intro = body.hymn_list_intro or []
    if full_order and len(hymn_list_intro) < 5:
        hymn_list_intro = (hymn_list_intro + ["", "", "", "", ""])[:5]
    try:
        out_path = run_sermon_code(
            code,
            hymn_list=hymn_list,
            card_slides=card_slides,
            hymn_txt_content=hymn_txt_content,
            full_order=full_order,
            hymn_list_intro=hymn_list_intro if full_order else None,
        )
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
