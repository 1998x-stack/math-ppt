#!/usr/bin/env python3
"""Verify generated PPTX, captions, and slide timeline against the lesson source."""
import argparse
import json
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches

BANNED=r'9\s*[:：]\s*16|竖屏教学|开头\s*\d+\s*秒|\d+\s*秒钩子|抓住数学矛盾|原题重排|新增推导|答案揭晓|互动挑战'

def check(source,folder):
    doc=json.loads(Path(source).read_text(encoding='utf-8'))
    timeline=json.loads((folder/'timeline.json').read_text(encoding='utf-8'))
    srt=(folder/'lesson.srt').read_text(encoding='utf-8-sig')
    voice=(folder/'voiceover.txt').read_text(encoding='utf-8')
    prs=Presentation(str(folder/'lesson.pptx'))
    errors=[]
    if len(prs.slides)!=len(doc['slides']) or len(timeline['slides'])!=len(doc['slides']):
        errors.append('PPT/JSON/timeline page counts differ')
    if abs(prs.slide_width / prs.slide_height - 9/16)>0.0004:
        errors.append('Presentation ratio is not 9:16')
    expected='\n\n'.join(s['notes'] for s in doc['slides'])+'\n'
    if voice!=expected:errors.append('Voiceover differs from notes')
    for i,sl in enumerate(prs.slides):
        if not sl.has_notes_slide:errors.append(f'slide {i+1} has no notes')
        else:
            got=sl.notes_slide.notes_text_frame.text.strip()
            if got!=doc['slides'][i]['notes'].strip():
                errors.append(f'slide {i+1} notes differ')
        for sh in sl.shapes:
            if sh.has_text_frame and re.search(BANNED,sh.text_frame.text,re.I):
                errors.append(f'slide {i+1} visible directing text leaked')
            if sh.left<0 or sh.top<0 or sh.left+sh.width>prs.slide_width+Inches(.05) or sh.top+sh.height>prs.slide_height+Inches(.05):
                errors.append(f'slide {i+1} shape outside canvas')
    cues=timeline['cues']
    for j,c in enumerate(cues):
        if c['index']!=j+1 or c['start_ms']>=c['end_ms']:
            errors.append(f'Invalid cue {j+1}')
        if j and c['start_ms']<cues[j-1]['end_ms']:
            errors.append(f'Overlapping cue {j+1}')
        if re.search(BANNED,c['text'],re.I):errors.append(f'cue {j+1} directing text leaked')
    for i,slide in enumerate(timeline['slides']):
        prev=timeline['slides'][i-1]['end_ms'] if i else 0
        if slide['start_ms']!=prev:errors.append(f'slide {i+1} timeline discontinuity')
        got=''.join(c['text'] for c in cues if c['slide']==i+1).replace(' ','')
        want=doc['slides'][i]['notes'].replace(' ','')
        if got!=want:errors.append(f'slide {i+1} subtitle text mismatch')
    if timeline['slides'] and timeline['slides'][-1]['end_ms']!=timeline['total_ms']:
        errors.append('Invalid total duration')
    blocks=re.findall(r'(?m)^(\d+)\r?\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\r?\n([^\r\n]+)',srt.lstrip('\ufeff'))
    if len(blocks)!=len(cues):errors.append('SRT cue count differs from timeline')
    if blocks:
        for b,c in zip(blocks,cues):
            if b[3]!=c['text']:errors.append('SRT text differs from timeline');break
    return errors

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',default='examples/tangent-integer-triangle/lesson.json')
    p.add_argument('--out',default='examples/tangent-integer-triangle/generated')
    a=p.parse_args()
    problems=check(a.input,Path(a.out))
    for problem in problems:print('ERROR:',problem)
    if problems:raise SystemExit(1)
    print('PASS: presentation, speaker notes, SRT, narration and page timing verified')
