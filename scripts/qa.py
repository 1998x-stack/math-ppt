#!/usr/bin/env python3
"""Strict QA for generated PowerPoint, subtitles, time map and narration."""
import argparse
import json
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from build import BANNED, validate, clock

TIME_RE=r'\d{2}:\d{2}:\d{2},\d{3}'
SRT_RE=re.compile(rf'(?s)^(\d+)\r?\n({TIME_RE}) --> ({TIME_RE})\r?\n(.+)$')

def parse_srt(raw):
    blocks=re.split(r'\r?\n[ \t]*\r?\n',raw.lstrip('\ufeff').strip())
    results=[]
    for n,block in enumerate(blocks,1):
        block=block.replace('\r\n','\n')
        match=SRT_RE.fullmatch(block)
        if not match:
            raise ValueError(f'Invalid SRT block {n}')
        index,start,end,caption=match.groups()
        results.append((int(index),start,end,caption))
    return results

def check(source, folder):
    source=Path(source);folder=Path(folder)
    errors=[]
    doc=json.loads(source.read_text(encoding='utf-8'))
    try:validate(doc)
    except ValueError as e:errors.append(f'Invalid lesson: {e}')
    t=json.loads((folder/'timeline.json').read_text(encoding='utf-8'))
    voice=(folder/'voiceover.txt').read_text(encoding='utf-8')
    prs=Presentation(str(folder/'lesson.pptx'))
    cues=t.get('cues',[]);pages=t.get('slides',[])
    if t.get('alignment') not in ('estimated_from_text_not_audio','per_cue_measured_audio'):
        errors.append('Unknown audio alignment status')
    if len(prs.slides)!=len(doc['slides']) or len(pages)!=len(doc['slides']):
        errors.append('Page counts differ across PPT/lesson/timeline')
    if abs(prs.slide_width/prs.slide_height-9/16)>.0004:
        errors.append('PPT aspect ratio differs from 9:16')
    expected_voice='\n\n'.join(sl['notes'] for sl in doc['slides'])+'\n'
    if voice!=expected_voice:errors.append('Voiceover mismatch')
    for i,sl in enumerate(prs.slides):
        if i>=len(doc['slides']):break
        d=doc['slides'][i]
        if not sl.has_notes_slide or sl.notes_slide.notes_text_frame.text.strip()!=d['notes'].strip():
            errors.append(f'Page {i+1} notes mismatch')
        visible=[sh.text_frame.text for sh in sl.shapes if sh.has_text_frame]
        visible_set=set(visible)
        expected=[d.get('title'),d.get('kicker'),d.get('formula'),
                  d.get('secondary'),d.get('highlight') or d.get('prompt') or d.get('foot')]
        expected+=(d.get('lines') or d.get('steps') or [])
        expected+=[f"{choice['key']}  {choice['value']}" for choice in d.get('choices',[])]
        if d.get('angle_label'):expected.append(d['angle_label'])
        for token in expected:
            if token is not None and str(token) not in visible_set:
                errors.append(f'Page {i+1} missing visible content: {str(token)[:60]}')
        for sh in sl.shapes:
            if sh.has_text_frame and any(re.search(p,sh.text_frame.text,re.I) for p in BANNED):
                errors.append(f'Page {i+1} has leaked production text')
            if sh.left<0 or sh.top<0 or sh.left+sh.width>prs.slide_width+Inches(.05) or sh.top+sh.height>prs.slide_height+Inches(.05):
                errors.append(f'Page {i+1} shape outside slide')
    if len(cues)==0 or len(pages)==0:
        errors.append('Missing cues or pages')
    if t.get('total_ms')!=(pages[-1]['end_ms'] if pages else None):
        errors.append('Total duration mismatch')
    for j,c in enumerate(cues):
        if c.get('index')!=j+1 or c.get('start_ms',-1)<0 or c.get('end_ms',0)<=c.get('start_ms',0):
            errors.append(f'Invalid cue index/time {j+1}')
        if j and c['start_ms']<cues[j-1]['end_ms']:
            errors.append(f'Overlapping cues at {j+1}')
        if any(re.search(p,c.get('text',''),re.I) for p in BANNED):
            errors.append(f'Cue {j+1} leaked production text')
    used=[]
    for i,page in enumerate(pages):
        if i>=len(doc['slides']):break
        prev=pages[i-1]['end_ms'] if i else 0
        if page['start_ms']!=prev or page['start_ms']>=page['end_ms']:
            errors.append(f'Invalid page boundary {i+1}')
        if page.get('duration_ms')!=page['end_ms']-page['start_ms']:
            errors.append(f'Invalid page duration {i+1}')
        if page.get('slide')!=i+1: errors.append(f'Invalid page number {i+1}')
        indices=page.get('cue_indices',[])
        used.extend(indices)
        selected=[cues[k-1] for k in indices if isinstance(k,int) and 1<=k<=len(cues)]
        for c in selected:
            if c.get('slide')!=i+1 or not (page['start_ms']<=c['start_ms']<c['end_ms']<=page['end_ms']):
                errors.append(f'Cue {c["index"]} outside assigned page')
        actual=''.join(c['text'] for c in selected).replace(' ','')
        desired=doc['slides'][i]['notes'].replace(' ','')
        if actual!=desired:
            errors.append(f'Page {i+1} subtitles differ from lesson narration')
    if used!=list(range(1,len(cues)+1)):
        errors.append('Cue indices are duplicated, missing or reordered')
    try:srt=parse_srt((folder/'lesson.srt').read_text(encoding='utf-8-sig'))
    except ValueError as e:
        errors.append(str(e));srt=[]
    if len(srt)!=len(cues):
        errors.append('SRT cue count differs from timeline')
    for j, (block,c) in enumerate(zip(srt,cues),1):
        if block!=(c['index'],clock(c['start_ms']),clock(c['end_ms']),c['text']):
            errors.append(f'SRT block {j} does not exactly match the time map')
    from slide_map import validate_map_file
    try:
        mapping=validate_map_file(folder/'slide_map.json',folder/'lesson.srt')
        if mapping['page_count']!=len(doc['slides']) or mapping['cue_count']!=len(cues):
            errors.append('PPT page/SRT cue count disagrees with slide_map')
        if mapping['alignment']!=t['alignment']:
            errors.append('Slide map audio timing status disagrees with timeline')
    except (ValueError,FileNotFoundError,KeyError) as e:
        errors.append(f'Invalid/missing slide map: {e}')
    return errors

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='examples/tangent-integer-triangle/lesson.json')
    ap.add_argument('--out',default='examples/tangent-integer-triangle/generated')
    args=ap.parse_args()
    faults=check(args.input,Path(args.out))
    for fault in faults: print('ERROR:',fault)
    if faults:raise SystemExit(1)
    print('PASS: source, editable PPT, all visible steps, narration, exact SRT timestamps and slide alignment')
