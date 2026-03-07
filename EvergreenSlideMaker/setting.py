import os
import re  # 정규 표현식 모듈 추가
import unicodedata
import chardet
import datetime


def normalized_str(str):
  return unicodedata.normalize('NFC', str)


folder_path = 'EvergreenSlideMaker'


def find_bible_file(directory, title):
    for file in os.listdir(directory):
        if normalized_str(file).endswith(normalized_str(title)+'.txt'):
            return os.path.join(directory, file)
    return None

def get_bible_verses(directory, title, start_verse, end_verse):
    file_path = find_bible_file(directory, title)
    if not file_path:
        return "Error: Bible book not found."

    # 시작 장:절과 종료 장:절 파싱
    start_chapter, start_verse_num = map(int, start_verse.split(':'))
    end_chapter, end_verse_num = map(int, end_verse.split(':'))

    result_verses = []
    collecting = False
    with open(file_path, "rb") as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result['encoding']
        print(f"🔍 감지된 인코딩: {encoding}")

  
    # 파일을 열고 각 줄을 읽기
    with open(file_path, 'r', encoding=encoding) as file:
        for line in file:
            # 정규 표현식을 사용하여 장:절 파싱
            match = re.match(r'^[^\d]*(\d+):(\d+)', line)
            if match:
                chapter, verse_num = map(int, match.groups())

                # 시작 조건 검사
                if chapter == start_chapter and verse_num >= start_verse_num:
                    collecting = True

                if collecting:
                    result_verses.append(line.strip())

                # 종료 조건 검사
                if chapter == end_chapter and verse_num == end_verse_num:
                    break
            else:
                continue  # 장:절 정보가 없는 줄은 무시
    return '\n'.join(result_verses) if result_verses else "No verses found in the specified range."

def load_hymn(filepath, target_title):
    # 인코딩 자동 감지
    with open(filepath, "rb") as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result['encoding']
        print(f"🔍 감지된 인코딩: {encoding}")
    
    # 감지된 인코딩으로 파일 읽기
    with open(filepath, 'r', encoding=encoding) as file:
        content = file.read()
        hymn_blocks = re.split(r'\n(?=\d+\.)', content)  # 새 찬송가 구분

        for block in hymn_blocks:
            if not block.strip():
                continue
            lines = block.strip().split('\n')
            header = lines[0]
            title_match = re.search(r'\d+\.\s*(.+)', header)
            if not title_match:
                continue
            title = title_match.group(1)

            if title.replace(" ", "") != target_title.replace(" ", ""):
                continue

            lyrics = []
            refrain = []
            current_verse = []
            refrain_collecting = False

            for line in lines[1:]:
                line = line.strip()
                if '후렴 :' in line:
                    refrain_collecting = True
                    refrain = []  # 이전 후렴 내용 초기화
                    refrain_text = line.split('후렴 :', 1)[-1].strip()
                    if refrain_text:
                        refrain.append(refrain_text)
                    continue

                if re.match(r'\(\d+\)', line) and current_verse:
                    lyrics.append('\n'.join(current_verse))  # 현재 절 저장
                    if refrain:
                        lyrics.append('\n'.join(refrain))  # 후렴 추가
                    current_verse = []  # 현재 절 초기화
                    refrain_collecting = False

                if refrain_collecting:
                    refrain.append(line)
                else:
                    current_verse.append(line)

            # 마지막 절과 후렴 추가
            if current_verse:
                lyrics.append('\n'.join(current_verse))
                if refrain:
                    lyrics.append('\n'.join(refrain))  # 마지막 절에 후렴 추가

            return '\n\n'.join(lyrics)

    return "찬송가 제목을 찾을 수 없습니다."
  
today = datetime.datetime.now().strftime('%Y-%m-%d')

def wrap_text_by_max_length(text, max_length):
    words = text.split()
    wrapped_text = ""
    current_line = ""

    for word in words:
        if len(current_line + word) <= max_length:
            current_line += word + " "
        else:
            wrapped_text += current_line.strip() + "\n"
            current_line = word + " "
    wrapped_text += current_line.strip()

    return wrapped_text

# 각 슬라이드 유형에 따른 함수 정의
def add_blank_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)

def add_black_slide(prs, text=''):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 0, 0)

def add_hymn_slide(prs, hymn_title, box_color = "203864"):
    hymn_text  = load_hymn(f'{folder_path}/Hymn/hymn.txt', hymn_title)
    lines = hymn_text.split('\n')
    hymn_lines = [line.strip() for line in hymn_text.split('\n') if line.strip() != '']
    hymn_list = []
    for i in range(0, len(hymn_lines), 1):
      hymn_line = ['\n'.join(hymn_lines[i:i+1])]
      hymn_list.append(hymn_line)

    slide = None
    textbox = None
    frame = None
    page = 1
    for hymn in hymn_list:

        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)
        # 텍스트 박스의 너비와 높이
        textbox_width = Cm(30.4)
        textbox_height = Cm(3.3)
        # 텍스트 박스를 수평 중앙에 맞춤
        textbox_x = (prs.slide_width - textbox_width) / 2
        textbox_y = Cm(15)  # 세로 위치는 15cm 고정
        textbox = slide.shapes.add_textbox(textbox_x, textbox_y, textbox_width, textbox_height)

        frame = textbox.text_frame
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        p = frame.paragraphs[0]
        p.text = hymn[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(35)
        p.font.name = 'Pretendard Semibold'
        p.font.color.rgb = RGBColor(255, 255, 255)
        fill = textbox.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(box_color)

        p = frame.paragraphs[0]

        if page == 1:
          ref_box = slide.shapes.add_textbox(Cm(23.63), Cm(13.5), Cm(8.5), Cm(1.5))
          ref_fill = ref_box.fill
          ref_fill.solid()
          ref_fill.fore_color.rgb = RGBColor.from_string('FFFFFF')

          ref_frame = ref_box.text_frame
          ref_p = ref_frame.paragraphs[0]
          ref_p.text = f"{hymn_title}"
          ref_p.font.size = Pt(20)
          ref_p.font.color.rgb = RGBColor(0, 0, 0)
          ref_p.font.name = 'Pretendard Black'
          ref_p.alignment = PP_ALIGN.CENTER
          ref_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
          ref_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

        page += 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)


def add_image_slide(prs, image_path, text=''):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)
    # Image 추가 로직 구현
    slide.shapes.add_picture(image_path, Cm(0), Cm(0))
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)
    # 텍스트 박스의 너비와 높이
    textbox_width = Cm(30.4)
    textbox_height = Cm(3.3)
    # 텍스트 박스를 수평 중앙에 맞춤
    textbox_x = (prs.slide_width - textbox_width) / 2
    textbox_y = Cm(1.2)  # 세로 위치는 15cm 고정
    textbox = slide.shapes.add_textbox(textbox_x, textbox_y, textbox_width, textbox_height)

    frame = textbox.text_frame
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    p = frame.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(36)
    p.font.name = '다음_SemiBold'
    p.font.color.rgb = RGBColor(255, 255, 255)



def add_subtitle_slide(prs, box_color = "203864", input_text='텍스트를 입력하세요', font_color='FFFF00'):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)  # 녹색 배경

    textbox = slide.shapes.add_textbox(Cm(0), prs.slide_height - Cm(4.2), Cm(33.87), Cm(4.2))


    frame = textbox.text_frame
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    p = frame.paragraphs[0]

    p.text = input_text
    p.font.size = Pt(36)
    p.font.name = 'Pretendard Semibold'
    p.font.color.rgb = RGBColor.from_string(font_color)
    p.alignment = PP_ALIGN.CENTER
    fill = textbox.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(box_color)  # 사용자 지정 색상


def add_card_slide(prs, box_color = "203864",background_color ='00FF00', input_text='텍스트를 입력하세요'):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(background_color)
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Cm(1.76), Cm(15.06), Cm(10.62), Cm(1.83))
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(box_color)  # 사용자 지정 색상
    frame = shape.text_frame
    frame.text = input_text
    p = frame.paragraphs[0]
    p.font.bold = True
    p.font.size = Pt(35)
    p.font.name = 'Pretendard Black'
    p.alignment = PP_ALIGN.CENTER

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)

def add_bible_slide(prs, directory, title, start_verse, end_verse='', box_color = "203864"):
    if end_verse == '':
      end_verse = start_verse
    verses_text = get_bible_verses(directory, title, start_verse, end_verse)
    verses_lines = verses_text.split('\n')  # 성경 구절을 줄바꿈으로 분리하여 리스트로 변환

    for verse in verses_lines:
        if not verse.strip():  # 빈 문자열 확인
            continue  # 빈 성경 구절은 건너뛰기

        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)  # 녹색 배경
        ref_info = verse.split()[0] if verse.split() else ""  # 첫 단어를 참조 정보로 사용, 빈 경우 "No Ref" 표시


        modified_verse = re.sub(r'<[^>]*>', '', verse.replace(ref_info+' ', "")).strip()  # <>, header 제거
        target_verse = wrap_text_by_max_length(modified_verse, 42)
        lines = target_verse.split('\n')
        num_lines = len(lines)
        textbox_height = Cm(4.2) + Cm(max(0, num_lines - 3) * 0.5)

        textbox = slide.shapes.add_textbox(Cm(0), prs.slide_height-textbox_height-Cm(0.3), Cm(33.87), textbox_height)
        frame = textbox.text_frame
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        p = frame.paragraphs[0]

        p.text = target_verse
        p.font.size = Pt(30)
        p.font.name = 'Pretendard Semibold'
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.LEFT
        fill = textbox.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(box_color)  # 사용자 지정 색상

        # 구절 참조 정보 파싱

        ref_box = slide.shapes.add_textbox(Cm(0), prs.slide_height-textbox_height-Cm(1.8), Cm(8), Cm(1.5))


        ref_fill = ref_box.fill
        ref_fill.solid()
        ref_fill.fore_color.rgb = RGBColor.from_string('FFFFFF')

        ref_frame = ref_box.text_frame
        ref_p = ref_frame.paragraphs[0]
        ref_p.text = f"{ref_info}"
        ref_p.font.size = Pt(24)
        ref_p.font.color.rgb = RGBColor(0, 0, 0)
        ref_p.font.name = 'Pretendard Black'
        ref_p.alignment = PP_ALIGN.CENTER
        ref_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        ref_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)

from pptx.util import Cm, Pt
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.enum.text import MSO_ANCHOR
from pptx.dml.color import RGBColor


def add_choir_slides_from_file(prs, title, box_color="203864"):
    """
    성가대.txt 파일을 읽어서 2줄씩 PPT 슬라이드에 출력.
    첫 슬라이드에는 hymn과 동일한 형태의 제목 박스를 추가한다.

    :param prs: python-pptx Presentation 객체
    :param title: 첫 슬라이드에 표시할 제목 텍스트
    :param box_color: 가사 박스 배경색 (RGB hex string)
    """

    # 1) 성가대.txt 읽기
    file_path = f"{folder_path}/Hymn/성가대.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 2) 줄 단위 전처리 (빈 줄 제거)
    lines = [line.strip() for line in text.split("\n") if line.strip() != ""]

    if not lines:
        return

    # 3) 2줄씩 묶기
    blocks = []
    for i in range(0, len(lines), 2):
        blocks.append("\n".join(lines[i:i+2]))

    # 4) 공통 레이아웃 값
    textbox_width = Cm(30.4)
    textbox_height = Cm(3.3)
    textbox_y = Cm(15)

    page = 1

    # 5) 슬라이드 생성
    for block in blocks:
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 배경색
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(0, 255, 0)

        # 가사 텍스트 박스
        textbox_x = (prs.slide_width - textbox_width) / 2
        textbox = slide.shapes.add_textbox(
            textbox_x, textbox_y, textbox_width, textbox_height
        )

        frame = textbox.text_frame
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

        p = frame.paragraphs[0]
        p.text = block
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(35)
        p.font.name = "Pretendard Semibold"
        p.font.color.rgb = RGBColor(255, 255, 255)

        fill = textbox.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(box_color)

        # ✅ 첫 페이지에만 제목 박스 추가 (기존 hymn과 동일)
        if page == 1:
            ref_box = slide.shapes.add_textbox(
                Cm(23.63), Cm(13.5), Cm(8.5), Cm(1.5)
            )
            ref_fill = ref_box.fill
            ref_fill.solid()
            ref_fill.fore_color.rgb = RGBColor.from_string("FFFFFF")

            ref_frame = ref_box.text_frame
            ref_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            ref_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

            ref_p = ref_frame.paragraphs[0]
            ref_p.text = title
            ref_p.font.size = Pt(20)
            ref_p.font.name = "Pretendard Black"
            ref_p.font.color.rgb = RGBColor(0, 0, 0)
            ref_p.alignment = PP_ALIGN.CENTER

        page += 1
