import json
import math
import os
import struct
import sys
import wave
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Inches

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from slide_map import generate_map, validate_map_file, create_map_file, read_srt
from render_course_video import make_video


def sample(tmp_path):
    prs=Presentation();prs.slide_width=Inches(7.5);prs.slide_height=Inches(13.333333)
    for i in range(2):
        slide=prs.slides.add_slide(prs.slide_layouts[6])
        box=slide.shapes.add_textbox(Inches(1),Inches(2),Inches(5),Inches(1))
        box.text=f'数学第{i+1}页 tan A = 1'
    ppt=tmp_path/'test.pptx';prs.save(str(ppt))
    srt=tmp_path/'test.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:01,200\n第一个数学结论。\n\n2\n00:00:01,500 --> 00:00:02,900\n第二个数学结论。\n',encoding='utf-8-sig')
    timeline={'alignment':'per_cue_measured_audio','total_ms':3000,
             'slides':[{'slide':1,'title':'第一页','start_ms':0,'end_ms':1500,'duration_ms':1500,'cue_indices':[1],'image':'slide-01.png'},
                       {'slide':2,'title':'第二页','start_ms':1500,'end_ms':3000,'duration_ms':1500,'cue_indices':[2],'image':'slide-02.png'}],
             'cues':[{'index':1,'slide':1,'start_ms':0,'end_ms':1200,'text':'第一个数学结论。'},
                     {'index':2,'slide':2,'start_ms':1500,'end_ms':2900,'text':'第二个数学结论。'}]}
    t=tmp_path/'timeline.json';t.write_text(json.dumps(timeline,ensure_ascii=False),encoding='utf-8')
    mapping=tmp_path/'slide_map.json';create_map_file(t,srt,mapping)
    audio=tmp_path/'narration.wav'
    with wave.open(str(audio),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
        f.writeframes(b'\x00\x00'*144000)
    return ppt,srt,mapping,audio


def test_srt_to_slide_mapping(tmp_path):
    p,s,m,a=sample(tmp_path)
    data=validate_map_file(m,s)
    assert data['page_count']==2
    assert data['cue_to_page']=={'1':1,'2':2}
    assert data['pages'][0]['captions'][0]['text']=='第一个数学结论。'


def test_srt_mutation_rejected(tmp_path):
    p,s,m,a=sample(tmp_path)
    s.write_text(s.read_text('utf-8-sig').replace('第一个','不一样的'),encoding='utf-8')
    with pytest.raises(ValueError,match='SRT differs'):
        validate_map_file(m,s)


def test_unaligned_rejected(tmp_path):
    p,s,m,a=sample(tmp_path)
    data=json.loads(m.read_text('utf-8'))
    data['alignment']='estimated_from_text_not_audio'
    m.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError,match='estimated'):
        make_video(p,s,a,m,tmp_path/'test.mp4')


def test_video_automated_render_and_burn(tmp_path):
    p,s,m,a=sample(tmp_path)
    result=make_video(p,s,a,m,tmp_path/'video.mp4',width=360,height=640,fps=8,burn=True)
    out=tmp_path/'video.mp4'
    assert out.exists() and out.stat().st_size>1500
    assert (tmp_path/'video.srt').exists()
    assert result['pptx_pages']==2
    assert result['caption_mode']=='burned+sidecar'
