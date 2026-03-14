"""
기존 EvergreenSlideMaker/Hymn/hymn.txt 를 파싱해서
data/hymns/ 제목.txt 형태로 한 곡당 한 파일 생성.
실행: python scripts/migrate_hymns_to_files.py (프로젝트 루트에서)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HYMN_SRC = ROOT / "EvergreenSlideMaker" / "Hymn" / "hymn.txt"
HYMN_DIR = ROOT / "data" / "hymns"


def sanitize_filename(title: str) -> str:
    if not title or not title.strip():
        return "untitled"
    s = title.strip()
    for c in r'\/:*?"<>|':
        s = s.replace(c, "_")
    s = re.sub(r"[\n\r]+", "_", s)
    s = s.strip("._ ") or "untitled"
    return s[:120]


def main():
    if not HYMN_SRC.exists():
        print(f"파일 없음: {HYMN_SRC}")
        sys.exit(1)
    text = HYMN_SRC.read_text(encoding="utf-8")
    # 블록 구분: "1. 제목" / "2. 제목" / ...
    blocks = re.split(r"\n(?=\d+\.\s)", text)
    count = 0
    HYMN_DIR.mkdir(parents=True, exist_ok=True)
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
        # 첫 줄 "N. 제목" 제외한 나머지가 가사
        content_lines = lines[1:] if len(lines) > 1 else []
        content = "\n".join(content_lines).strip()
        name = sanitize_filename(title) + ".txt"
        out_path = HYMN_DIR / name
        out_path.write_text(content, encoding="utf-8")
        count += 1
        print(f"  {count}. {title}")
    print(f"\n총 {count}곡 → {HYMN_DIR}")


if __name__ == "__main__":
    main()
