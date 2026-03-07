"""
찬송가 입력 포맷(제목 / ------ / 내용)을 load_hymn이 읽는 형식(1. 제목\\n내용)으로 변환.
"""
from __future__ import annotations


def user_to_hymn_txt(user_text: str) -> str:
    """
    사용자 입력: 한 곡당
      제목
      ------
      내용
    여러 곡은 빈 줄로 구분.
    출력: load_hymn용 "1. 제목\\n내용\\n\\n2. 제목2\\n내용2\\n\\n..."
    """
    if not (user_text or "").strip():
        return ""
    blocks: list[tuple[str, str]] = []
    raw_blocks = user_text.strip().split("\n\n")
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        sep_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "------":
                sep_idx = i
                break
        if sep_idx is None:
            continue
        title = "\n".join(lines[:sep_idx]).strip()
        content = "\n".join(lines[sep_idx + 1 :]).strip()
        if title:
            blocks.append((title, content))
    if not blocks:
        return ""
    out_lines: list[str] = []
    for i, (title, content) in enumerate(blocks, 1):
        out_lines.append(f"{i}. {title}")
        if content:
            out_lines.append(content)
        out_lines.append("")
    return "\n".join(out_lines).strip()
