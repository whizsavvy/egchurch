"""성경 구절 텍스트 조회 (API용)."""
from __future__ import annotations
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIBLE_DIR = ROOT / "EvergreenSlideMaker" / "bible"


def _normalized(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def get_bible_verse_text(book: str, start_verse: str, end_verse: str | None = None) -> str:
    """성경 권, 시작 장:절, (선택) 끝 장:절을 받아 구절 텍스트 반환."""
    if not book or not start_verse:
        return ""
    end = (end_verse or start_verse).strip()
    directory = str(BIBLE_DIR)
    if not os.path.isdir(directory):
        return ""

    try:
        import re
        import chardet
        file_path = None
        for f in os.listdir(directory):
            if _normalized(f).endswith(_normalized(book) + ".txt"):
                file_path = os.path.join(directory, f)
                break
        if not file_path:
            return ""
        start_chapter, start_verse_num = map(int, start_verse.strip().split(":"))
        end_chapter, end_verse_num = map(int, end.split(":"))
        result_verses = []
        collecting = False
        with open(file_path, "rb") as fp:
            raw = fp.read()
            enc = chardet.detect(raw).get("encoding") or "utf-8"
        with open(file_path, "r", encoding=enc) as file:
            for line in file:
                match = re.match(r"^[^\d]*(\d+):(\d+)", line)
                if match:
                    ch, v = map(int, match.groups())
                    if ch == start_chapter and v >= start_verse_num:
                        collecting = True
                    if collecting:
                        result_verses.append(line.strip())
                    if ch == end_chapter and v == end_verse_num:
                        break
        return "\n".join(result_verses) if result_verses else ""
    except Exception:
        return ""
