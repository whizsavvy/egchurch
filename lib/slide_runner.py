"""
설교 자막용 코드를 실행해 PPTX를 생성합니다.
프로젝트 루트에 EvergreenSlideMaker 폴더가 있어야 합니다.
"""
from __future__ import annotations
import datetime
import os
import sys
import tempfile
from pathlib import Path

# 루트 = lib의 상위 (Vercel이면 배포 루트)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from pptx import Presentation
from pptx.util import Cm

_setting_path = ROOT / "EvergreenSlideMaker" / "setting.py"
if not _setting_path.exists():
    raise FileNotFoundError(
        f"EvergreenSlideMaker/setting.py를 찾을 수 없습니다. 프로젝트 루트: {ROOT}"
    )
import importlib.util
_spec = importlib.util.spec_from_file_location("setting", _setting_path)
_setting = importlib.util.module_from_spec(_spec)
import datetime as _dt
_setting.datetime = _dt
_spec.loader.exec_module(_setting)
_setting.folder_path = str(ROOT / "EvergreenSlideMaker")
folder_path = _setting.folder_path
add_bible_slide = _setting.add_bible_slide
add_subtitle_slide = _setting.add_subtitle_slide
add_hymn_slide = getattr(_setting, "add_hymn_slide", None)
add_card_slide = getattr(_setting, "add_card_slide", None)
directory = os.path.join(folder_path, "bible")


def run_sermon_code(
    code: str,
    output_filename: str | None = None,
    hymn_list: list[str] | None = None,
    card_slides: list[str] | None = None,
) -> str:
    prs = Presentation()
    prs.slide_width = Cm(33.867)
    prs.slide_height = Cm(19.05)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    out_name = output_filename or f"{today}_늘푸른교회_.pptx"
    out_path = os.path.join(tempfile.gettempdir(), out_name)

    local_globals = {
        "prs": prs,
        "directory": directory,
        "add_bible_slide": add_bible_slide,
        "add_subtitle_slide": add_subtitle_slide,
    }
    try:
        exec(code, local_globals)
    except Exception as e:
        raise RuntimeError(f"슬라이드 코드 실행 중 오류: {e}") from e

    if hymn_list and add_hymn_slide:
        for title in hymn_list:
            if title.strip():
                add_hymn_slide(prs, title.strip())
    if card_slides and add_card_slide:
        for text in card_slides:
            if text.strip():
                add_card_slide(prs, input_text=text.strip())

    prs.save(out_path)
    return out_path
