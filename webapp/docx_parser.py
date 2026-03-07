"""
설교 원고 DOCX 파싱: 단락·런(run) 단위로 텍스트와 글자 색상(RGB) 추출.
RED(#FF0000)만 성경 구절로 사용하는 규칙에 맞춰 AI/프롬프트 입력용 구조 반환.
"""
from __future__ import annotations
import io
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.text.run import Run


def _get_run_color_hex(run: Run) -> str | None:
    """Run의 글자 색상을 HEX 문자열로 반환. 없으면 None."""
    if not run.font.color:
        return None
    rgb = run.font.color.rgb
    if rgb is None:
        return None
    if isinstance(rgb, str):
        return rgb[:6]
    # python-docx can return RGBColor object (has .r, .g, .b)
    if hasattr(rgb, "r") and hasattr(rgb, "g") and hasattr(rgb, "b"):
        return f"{int(rgb.r):02X}{int(rgb.g):02X}{int(rgb.b):02X}"
    if isinstance(rgb, int):
        return f"{rgb:06X}"
    try:
        return str(rgb)[:6]
    except Exception:
        return None


def _normalize_color(r: int | None, g: int | None, b: int | None) -> str | None:
    if r is None or g is None or b is None:
        return None
    return f"{r:02X}{g:02X}{b:02X}"


def parse_docx(file_content: bytes) -> list[dict[str, Any]]:
    """
    DOCX 바이트를 파싱하여 단락별로 runs(텍스트 + 색상 등) 리스트 반환.
    반환 형식: [ {"runs": [ {"text": "...", "color_hex": "FF0000" | null, "bold": bool, "italic": bool } ], "paragraph_index": int }, ... ]
    """
    doc = Document(io.BytesIO(file_content))
    result: list[dict[str, Any]] = []
    for pi, para in enumerate(doc.paragraphs):
        runs_data: list[dict[str, Any]] = []
        for run in para.runs:
            color_hex = _get_run_color_hex(run)
            runs_data.append({
                "text": run.text or "",
                "color_hex": color_hex,
                "bold": bool(run.font.bold) if run.font.bold is not None else False,
                "italic": bool(run.font.italic) if run.font.italic is not None else False,
            })
        result.append({
            "paragraph_index": pi,
            "runs": runs_data,
        })
    return result


def get_red_runs_summary(parsed: list[dict[str, Any]]) -> list[str]:
    """파싱 결과에서 RED(#FF0000) 런의 텍스트만 순서대로 추출 (디버그/미리보기용)."""
    RED = "FF0000"
    lines: list[str] = []
    for block in parsed:
        for r in block["runs"]:
            if (r.get("color_hex") or "").upper() == RED and (r.get("text") or "").strip():
                lines.append((r.get("text") or "").strip())
    return lines
