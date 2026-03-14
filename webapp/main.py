"""
교회 자막 웹앱 API: DOCX 파싱, 설교 코드 생성, PPTX 다운로드.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
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
    from lib.hymn_files import sanitize_filename, filename_to_title
    from lib.hymn_legacy import legacy_titles, legacy_one, legacy_merged
    from lib.sermon_prompt import SERMON_CODE_SYSTEM
    from lib.bible_verse import get_bible_verse_text
except ImportError:
    user_to_hymn_txt = None
    sanitize_filename = None
    filename_to_title = None
    legacy_titles = None
    legacy_one = None
    legacy_merged = None
    SERMON_CODE_SYSTEM = ""
    get_bible_verse_text = None

HYMN_DIR_LOCAL = _ROOT / "data" / "hymns"

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


def _hymn_dir():
    HYMN_DIR_LOCAL.mkdir(parents=True, exist_ok=True)
    return HYMN_DIR_LOCAL


@app.get("/api/hymns/list")
def api_hymns_list():
    """찬송 목록 (로컬: data/hymns/*.txt, 비어 있으면 기존 hymn.txt)."""
    items = []
    if HYMN_DIR_LOCAL.exists():
        for f in sorted(_hymn_dir().iterdir()):
            if f.suffix.lower() == ".txt" and f.is_file():
                items.append(filename_to_title(f.name) if filename_to_title else f.stem)
    if not items and legacy_titles:
        items = legacy_titles()
    items.sort(key=lambda x: x)
    return {"items": items}


@app.get("/api/hymns/one")
def api_hymns_one(title: str = ""):
    """찬송 한 곡 내용 (없으면 기존 hymn.txt에서)."""
    title = (title or "").strip()
    if not title or not sanitize_filename:
        raise HTTPException(400, "title 필요")
    path = _hymn_dir() / (sanitize_filename(title) + ".txt")
    if path.is_file():
        return {"title": title, "content": path.read_text(encoding="utf-8")}
    if legacy_one:
        return {"title": title, "content": legacy_one(title)}
    return {"title": title, "content": ""}


@app.get("/api/hymns/merged")
def api_hymns_merged():
    """PPT용 병합 문자열 (비어 있으면 기존 hymn.txt)."""
    parts = []
    if HYMN_DIR_LOCAL.exists():
        for f in sorted(_hymn_dir().iterdir()):
            if f.suffix.lower() == ".txt" and f.is_file():
                title = filename_to_title(f.name) if filename_to_title else f.stem
                content = f.read_text(encoding="utf-8").strip()
                parts.append(title + "\n------\n" + content)
    if not parts and legacy_merged:
        return PlainTextResponse(legacy_merged(), media_type="text/plain; charset=utf-8")
    return PlainTextResponse("\n\n".join(parts), media_type="text/plain; charset=utf-8")


class HymnSaveBody(BaseModel):
    title: str = ""
    content: str = ""


class HymnDeleteBody(BaseModel):
    title: str = ""


@app.post("/api/hymns/save")
def api_hymns_save(body: HymnSaveBody):
    """찬송 한 곡 저장 (로컬 파일)."""
    title = (body.title or "").strip()
    if not title or not sanitize_filename:
        raise HTTPException(400, "title 필요")
    path = _hymn_dir() / (sanitize_filename(title) + ".txt")
    path.write_text((body.content or "").strip(), encoding="utf-8")
    return {"ok": True, "title": title}


@app.post("/api/hymns/delete")
def api_hymns_delete(body: HymnDeleteBody):
    """찬송 한 곡 삭제."""
    title = (body.title or "").strip()
    if not title or not sanitize_filename:
        raise HTTPException(400, "title 필요")
    path = _hymn_dir() / (sanitize_filename(title) + ".txt")
    if path.is_file():
        path.unlink()
    return {"ok": True, "title": title}


@app.get("/api/get_bible_verse")
def api_get_bible_verse(book: str = "", start: str = "", end: str | None = None):
    """성경 구절 텍스트 조회 (상세 팝업용)."""
    if not get_bible_verse_text or not book or not start:
        raise HTTPException(400, "book, start 필요")
    text = get_bible_verse_text(book, start, end or start)
    return {"text": text, "book": book, "start": start, "end": end or start}


@app.get("/api/health")
def health():
    return {"status": "ok"}
