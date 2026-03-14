"""찬송가 항목별 파일 저장/조회 (data/hymns/*.txt)."""
from __future__ import annotations
import re

HYMN_DIR = "data/hymns"
GITHUB_REPO = "whizsavvy/egchurch"


def sanitize_filename(title: str) -> str:
    """제목을 파일명으로 쓸 수 있게 정리. 확장자 제외."""
    if not title or not title.strip():
        return "untitled"
    s = title.strip()
    for c in r'\/:*?"<>|':
        s = s.replace(c, "_")
    s = re.sub(r"[\n\r]+", "_", s)
    s = s.strip("._ ") or "untitled"
    return s[:120]


def filename_to_title(filename: str) -> str:
    """파일명(.txt 제거)을 제목으로. 인코딩 이슈 없으면 그대로 반환."""
    if filename.endswith(".txt"):
        return filename[:-4]
    return filename
