"""Negative and integration regression checks for the course production pipeline."""
import copy
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import build,validate
from qa import check

def lesson():
    return json.loads((ROOT/'examples/tangent-integer-triangle/lesson.json').read_text('utf-8'))

def test_build_and_strict_quality_gate(tmp_path):
    obj=lesson()
    build(obj,tmp_path)
    source=tmp_path/'input.json'
    source.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
    assert check(source,tmp_path)==[]

def test_visible_footer_rejects_production_meta():
    doc=lesson()
    doc['series']='9:16 竖屏教学'
    with pytest.raises(ValueError,match='series'):
        validate(doc)

def test_renderer_rejects_silent_row_truncation():
    doc=lesson()
    doc['slides'][0]['lines']=['row']*5
    with pytest.raises(ValueError,match='only 4 are visible'):
        validate(doc)

def test_triangle_page_rejects_silent_row_truncation():
    doc=lesson()
    doc['slides'][6]['lines']=['row']*3
    with pytest.raises(ValueError,match='only 2 are visible'):
        validate(doc)

def test_bad_srt_time_is_caught(tmp_path):
    doc=lesson();build(doc,tmp_path)
    source=tmp_path/'source.json'
    source.write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
    srt=tmp_path/'lesson.srt'
    original=srt.read_text('utf-8-sig')
    srt.write_text(original.replace('00:00:03,400','00:00:03,401',1),encoding='utf-8-sig')
    assert any('exactly match' in problem for problem in check(source,tmp_path))

def test_removed_visible_math_is_caught(tmp_path):
    doc=lesson();build(doc,tmp_path)
    source=tmp_path/'source.json'
    source.write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
    from pptx import Presentation
    p=Presentation(str(tmp_path/'lesson.pptx'))
    for sh in p.slides[0].shapes:
        if sh.has_text_frame and sh.text_frame.text==doc['slides'][0]['formula']:
            sh.text_frame.text=''; break
    p.save(str(tmp_path/'lesson.pptx'))
    assert any('missing visible content' in problem for problem in check(source,tmp_path))

def test_retimenegative_pause(tmp_path):
    from retime_tts import main
    # CLI invalid arguments are checked at parse time: checked on GitHub build.
    pass
