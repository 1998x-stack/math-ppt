import json
import sys
from pathlib import Path
from math import atan, pi
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import segments, validate

def read_example():
    return json.loads((ROOT/'examples/tangent-integer-triangle/lesson.json').read_text(encoding='utf-8'))

def test_math_answer():
    triples=[(a,b,c) for a in range(1,35) for b in range(a,35) for c in range(b,35)
             if a+b+c == a*b*c]
    assert triples==[(1,2,3)]
    assert abs(atan(1)+atan(2)+atan(3)-pi)<1e-12

def test_all_twenty_slides_are_valid():
    d=read_example()
    assert len(d['slides'])==20
    validate(d)

def test_forbidden_production_phrases():
    d=read_example()
    d['slides'][0]['kicker']='开头 3 秒抓住数学矛盾'
    try:
        validate(d)
    except ValueError: pass
    else: raise AssertionError('production text not rejected')

def test_srt_segmentation_preserves_words():
    for slide in read_example()['slides']:
        original=''.join(slide['notes'].split())
        obtained=''.join(''.join(segments(slide['notes'])).split())
        assert obtained == original

def test_slide_notes_are_meaningful():
    assert all(len(s['notes'])>=35 for s in read_example()['slides'])
