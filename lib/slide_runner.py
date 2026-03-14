"""
설교 자막용 코드를 실행해 PPTX를 생성합니다.
프로젝트 루트에 EvergreenSlideMaker 폴더가 있어야 합니다.
"""
from __future__ import annotations
import datetime
import os
import shutil
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
add_image_slide = getattr(_setting, "add_image_slide", None)
add_blank_slide = getattr(_setting, "add_blank_slide", None)
directory = os.path.join(folder_path, "bible")


def _add_intro_slides(prs, hymn_list_intro: list[str], pic_dic: str) -> None:
    """exe.py create_presentation 앞부분: 이미지 → 찬송 5곡 → 카드(성가대/통성기도/대표기도)."""
    if not add_image_slide or not add_blank_slide or not add_hymn_slide or not add_card_slide:
        return
    add_image_slide(prs, pic_dic + "2026.png", text="주일 1부 예배")
    add_image_slide(prs, pic_dic + "2026.png", text="주일 2부 예배")
    add_blank_slide(prs)
    if hymn_list_intro and len(hymn_list_intro) > 0:
        add_hymn_slide(prs, hymn_list_intro[0])
    add_image_slide(prs, pic_dic + "2026_신앙고백1.JPG")
    add_image_slide(prs, pic_dic + "2026_신앙고백2.JPG")
    add_blank_slide(prs)
    for i in range(1, min(5, len(hymn_list_intro))):
        add_hymn_slide(prs, hymn_list_intro[i])
    add_card_slide(prs, input_text="성가대 찬양")
    add_card_slide(prs, input_text="통성기도", background_color="000000")
    add_card_slide(prs, input_text="대표기도")


def _add_outro_slides(prs) -> None:
    """exe.py create_presentation 뒷부분: 찬송 → 통성기도/광고 → 찬송 → 축도."""
    if not add_hymn_slide or not add_card_slide:
        return
    add_hymn_slide(prs, "주님 다시 오실 때 까지")
    add_card_slide(prs, input_text="통성기도", background_color="000000")
    add_card_slide(prs, input_text="광고")
    add_hymn_slide(prs, "우리 오늘 눈물로")
    add_card_slide(prs, input_text="축도")


def run_sermon_code(
    code: str,
    output_filename: str | None = None,
    hymn_list: list[str] | None = None,
    card_slides: list[str] | None = None,
    hymn_txt_content: str | None = None,
    full_order: bool = False,
    hymn_list_intro: list[str] | None = None,
) -> str:
    """
    full_order=True 이면 exe.py create_presentation과 동일 순서:
    인도/이미지 → 찬송 5곡 → 성가대/통성/대표 → 설교코드(exec) → 주님 다시~ → 통성/광고 → 우리 오늘~ → 축도.
    hymn_list_intro: 인도용 찬송 5곡 [0]~[4] (full_order일 때만 사용).
    """
    temp_evergreen = None
    if hymn_txt_content and hymn_txt_content.strip():
        temp_evergreen = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "EvergreenSlideMaker", temp_evergreen / "EvergreenSlideMaker")
            hymn_file = temp_evergreen / "EvergreenSlideMaker" / "Hymn" / "hymn.txt"
            hymn_file.parent.mkdir(parents=True, exist_ok=True)
            hymn_file.write_text(hymn_txt_content.strip(), encoding="utf-8")
            _setting.folder_path = str(temp_evergreen / "EvergreenSlideMaker")
        except Exception:
            if temp_evergreen and temp_evergreen.exists():
                shutil.rmtree(temp_evergreen, ignore_errors=True)
            raise

    try:
        prs = Presentation()
        prs.slide_width = Cm(33.867)
        prs.slide_height = Cm(19.05)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        out_name = output_filename or f"{today}_늘푸른교회_.pptx"
        out_path = os.path.join(tempfile.gettempdir(), out_name)
        run_directory = os.path.join(_setting.folder_path, "bible")
        pic_dic = _setting.folder_path + "/image/"

        if full_order and hymn_list_intro:
            _add_intro_slides(prs, hymn_list_intro, pic_dic)

        local_globals = {
            "prs": prs,
            "directory": run_directory,
            "add_bible_slide": add_bible_slide,
            "add_subtitle_slide": add_subtitle_slide,
        }
        try:
            exec(code, local_globals)
        except Exception as e:
            raise RuntimeError(f"슬라이드 코드 실행 중 오류: {e}") from e

        if full_order:
            _add_outro_slides(prs)
        else:
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
    finally:
        if temp_evergreen and temp_evergreen.exists():
            shutil.rmtree(temp_evergreen, ignore_errors=True)
        _setting.folder_path = str(ROOT / "EvergreenSlideMaker")


def run_worship_order(
    order: list[dict],
    hymn_txt_content: str | None = None,
    output_filename: str | None = None,
) -> str:
    """
    예배 순서 배열로 PPT 생성.
    order 항목: { type: "image"|"blank"|"hymn"|"card"|"bible"|"subtitle", ... }
    - image: src (파일명), text (선택)
    - hymn: title
    - card: text, bgColor (선택, 기본 000000 for 통성기도 등)
    - bible: book, start, end (선택)
    - subtitle: text
    """
    src_evergreen = ROOT / "EvergreenSlideMaker"
    if not src_evergreen.is_dir():
        raise FileNotFoundError(f"EvergreenSlideMaker 폴더를 찾을 수 없습니다: {ROOT}")
    temp_evergreen = Path(tempfile.mkdtemp())
    try:
        shutil.copytree(src_evergreen, temp_evergreen / "EvergreenSlideMaker")
        _setting.folder_path = str(temp_evergreen / "EvergreenSlideMaker")
        if hymn_txt_content and hymn_txt_content.strip():
            hymn_file = temp_evergreen / "EvergreenSlideMaker" / "Hymn" / "hymn.txt"
            hymn_file.parent.mkdir(parents=True, exist_ok=True)
            hymn_file.write_text(hymn_txt_content.strip(), encoding="utf-8")
    except Exception as e:
        if temp_evergreen.exists():
            shutil.rmtree(temp_evergreen, ignore_errors=True)
        raise RuntimeError(f"EvergreenSlideMaker 복사 실패: {e}") from e

    try:
        prs = Presentation()
        prs.slide_width = Cm(33.867)
        prs.slide_height = Cm(19.05)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        out_name = output_filename or f"{today}_늘푸른교회_.pptx"
        out_path = os.path.join(tempfile.gettempdir(), out_name)
        pic_dic = _setting.folder_path + "/image/"
        run_directory = os.path.join(_setting.folder_path, "bible")

        for item in order or []:
            t = (item.get("type") or "").strip().lower()
            if t == "image":
                src = (item.get("src") or item.get("path") or "2026.png").strip()
                text = (item.get("text") or "").strip()
                if add_image_slide:
                    add_image_slide(prs, pic_dic + src, text=text)
            elif t == "blank":
                if add_blank_slide:
                    add_blank_slide(prs)
            elif t == "hymn":
                title = (item.get("title") or item.get("text") or "").strip()
                if title and title != "(찬송 선택)" and add_hymn_slide:
                    add_hymn_slide(prs, title)
            elif t == "card":
                text = (item.get("text") or "").strip()
                if not text:
                    continue
                bg = (item.get("bgColor") or item.get("background_color") or "00FF00").strip()
                if add_card_slide:
                    add_card_slide(prs, input_text=text, background_color=bg)
            elif t == "bible":
                book = (item.get("book") or "").strip()
                start = (item.get("start") or item.get("startVerse") or "").strip()
                end = (item.get("end") or item.get("endVerse") or "").strip()
                if book and start and add_bible_slide:
                    add_bible_slide(prs, run_directory, book, start, end if end else start)
            elif t == "subtitle":
                text = (item.get("text") or "").strip()
                if text and add_subtitle_slide:
                    add_subtitle_slide(prs, input_text=text)

        prs.save(out_path)
        return out_path
    except Exception as e:
        if temp_evergreen.exists():
            shutil.rmtree(temp_evergreen, ignore_errors=True)
        _setting.folder_path = str(ROOT / "EvergreenSlideMaker")
        raise RuntimeError(f"PPT 생성 중 오류: {e}") from e
    finally:
        if temp_evergreen.exists():
            shutil.rmtree(temp_evergreen, ignore_errors=True)
        _setting.folder_path = str(ROOT / "EvergreenSlideMaker")
