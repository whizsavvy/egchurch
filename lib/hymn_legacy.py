"""
기존 EvergreenSlideMaker/Hymn/hymn.txt 형식 파싱.
형식: "1. 제목\\n가사\\n\\n2. 제목2\\n가사2\\n\\n..."
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY_PATH = ROOT / "EvergreenSlideMaker" / "Hymn" / "hymn.txt"


def parse_legacy_hymn_txt(content: str) -> list[tuple[str, str]]:
    """전체 텍스트를 (제목, 가사) 리스트로 반환."""
    if not (content or "").strip():
        return []
    blocks = re.split(r"\n(?=\d+\.\s)", content.strip())
    out: list[tuple[str, str]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.match(r"^\d+\.\s*(.+)$", block, re.MULTILINE)
        if not match:
            continue
        title = match.group(1).split("\n")[0].strip()
        if not title:
            continue
        lines = block.split("\n")
        content_lines = lines[1:] if len(lines) > 1 else []
        body = "\n".join(content_lines).strip()
        out.append((title, body))
    return out


def load_legacy_hymns() -> list[tuple[str, str]]:
    """LEGACY_PATH 파일을 읽어 파싱. 파일 없으면 빈 리스트."""
    if not LEGACY_PATH.is_file():
        return []
    try:
        text = LEGACY_PATH.read_text(encoding="utf-8")
        return parse_legacy_hymn_txt(text)
    except Exception:
        return []


def legacy_titles() -> list[str]:
    """기존 hymn.txt에서 제목 목록만 반환."""
    return [t for t, _ in load_legacy_hymns()]


def legacy_one(title: str) -> str:
    """기존 hymn.txt에서 해당 제목의 가사만 반환. 없으면 빈 문자열."""
    for t, content in load_legacy_hymns():
        if t == title:
            return content
    return ""


def legacy_merged() -> str:
    """기존 hymn.txt 전체를 '제목\\n------\\n가사' 형식으로 병합."""
    parts = [f"{t}\n------\n{c}" for t, c in load_legacy_hymns()]
    return "\n\n".join(parts)
