from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.enum.text import MSO_AUTO_SIZE  # Correct import location for MSO_AUTO_SIZE
from pptx.enum.text import MSO_ANCHOR
import re
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')


exec(open("EvergreenSlideMaker/setting.py").read())

hymn_list = ['임재', '좋으신 하나님', '내가 매일 기쁘게', '마음 속에 근심 있는 사람', '우리 주 하나님']

def create_presentation(hymn_list=[]):
    prs = Presentation()
    prs.slide_width = Cm(33.867)
    prs.slide_height = Cm(19.05)
    directory = folder_path+"/bible"
    pic_dic = folder_path+"/image/"
    add_image_slide(prs, pic_dic+'2026.png', text='주일 1부 예배')
    add_image_slide(prs, pic_dic+'2026.png', text='주일 2부 예배')

    add_blank_slide(prs)
    add_hymn_slide(prs, hymn_list[0])

   
    # add_image_slide(prs, pic_dic+'신앙고백.png')
    add_image_slide(prs, pic_dic+'2026_신앙고백1.JPG')
    add_image_slide(prs, pic_dic+'2026_신앙고백2.JPG')
    # add_card_slide(prs, input_text= '신앙고백', background_color='000000')
    add_blank_slide(prs)
    add_hymn_slide(prs, hymn_list[1])
    add_hymn_slide(prs, hymn_list[2])
    add_hymn_slide(prs, hymn_list[3])
    add_hymn_slide(prs, hymn_list[4])

    add_card_slide(prs, input_text= '성가대 찬양')
    # add_choir_slides_from_file(prs, box_color="203864", title="주 예수 나의 산  소망")
    add_card_slide(prs, input_text= '통성기도', background_color='000000')
    add_card_slide(prs, input_text= '대표기도')

    # 제목/본문 (필수)
    add_bible_slide(prs, directory, "로마서", "8:11")
    add_subtitle_slide(prs, input_text="(4) 복음은 성령으로 나를 살게 한다 (로마서 8:11)")
    
    # RED only — 원고 순서 그대로
    add_bible_slide(prs, directory, "마가복음", "1:15")
    add_bible_slide(prs, directory, "고린도전서", "15:3", "15:4")
    
    add_bible_slide(prs, directory, "로마서", "8:11")  # 본문 재인용(확장 구절 포함 맥락)
    
    add_bible_slide(prs, directory, "요한복음", "14:16", "14:17")
    add_bible_slide(prs, directory, "고린도전서", "3:16")
    add_bible_slide(prs, directory, "로마서", "8:9")
    
    add_bible_slide(prs, directory, "갈라디아서", "2:20")
    add_bible_slide(prs, directory, "사도행전", "13:52")
    
    add_bible_slide(prs, directory, "이사야", "58:11")
    add_bible_slide(prs, directory, "에스겔", "37:9")
    add_bible_slide(prs, directory, "사도행전", "1:8")
    
    # (참고) 항목 중 RED로 표시된 절만 포함
    add_bible_slide(prs, directory, "로마서", "8:1")
    add_bible_slide(prs, directory, "로마서", "8:15")
    
    add_bible_slide(prs, directory, "요한복음", "16:14")
    add_bible_slide(prs, directory, "요한복음", "16:8")
    
    add_bible_slide(prs, directory, "요한일서", "1:9")
    add_bible_slide(prs, directory, "로마서", "12:2")
    add_bible_slide(prs, directory, "로마서", "8:13")
    
    add_bible_slide(prs, directory, "사도행전", "1:8")   # 결론부 재강조
    add_bible_slide(prs, directory, "로마서", "8:11")     # 마지막 고백
    add_hymn_slide(prs,  '주님 다시 오실 때 까지')


    # add_card_slide(prs, input_text= '성찬')
    # add_hymn_slide(prs, '보혈을 지나')
    add_card_slide(prs, input_text= '통성기도', background_color='000000')
    add_card_slide(prs, input_text= '광고')
    add_hymn_slide(prs,  '우리 오늘 눈물로')    
    add_card_slide(prs, input_text= '축도')

    prs.save(F'{today}_늘푸른교회_.pptx')

create_presentation(hymn_list)
