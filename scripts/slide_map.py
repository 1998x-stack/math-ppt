#!/usr/bin/env python3
"""Strict SRT <-> cue <-> PowerPoint page mapping.

An SRT has no page information. An existing, verified timeline is required.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

STAMP = re.compile(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$')


def millis(text):
    m = STAMP.fullmatch(text)
    if not m:
        raise ValueError(f'Invalid SRT timestamp: {text!r}')
    h, minute, s, ms = map(int, m.groups())
    if minute > 59 or s > 59:
        raise ValueError(f'Out-of-range SRT timestamp: {text!r}')
    return ((h*60 + minute)*60 + s)*1000 + ms


def read_srt(path):
    text = Path(path).read_text(encoding='utf-8-sig').replace('\r\n', '\n').strip()
    if not text:
        raise ValueError('Empty SRT')
    chunks = re.split(r'\n\s*\n', text)
    cues = []
    for number, chunk in enumerate(chunks, 1):
        lines = chunk.split('\n')
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError(f'Malformed SRT cue {number}')
        index = int(lines[0].strip())
        if index != number:
            raise ValueError(f'SRT cue index {index}, expected {number}')
        if ' --> ' not in lines[1]:
            raise ValueError(f'Missing SRT timestamp arrow, cue {index}')
        first, last = lines[1].split(' --> ', 1)
        start, end = millis(first.strip()), millis(last.strip())
        if end <= start:
            raise ValueError(f'Non-positive SRT cue {index}')
        caption = '\n'.join(lines[2:]).strip()
        if not caption:
            raise ValueError(f'Empty subtitle for cue {index}')
        if cues and start < cues[-1]['end_ms']:
            raise ValueError(f'Overlapping SRT cues {index-1} and {index}')
        cues.append({'index': index, 'start_ms':start,'end_ms':end,'text':caption})
    return cues


def generate_map(timeline, srt_path):
    srt_path = Path(srt_path)
    captions = read_srt(srt_path)
    indexed = timeline.get('cues', [])
    pages = timeline.get('slides', [])
    if len(indexed) != len(captions) or not pages:
        raise ValueError('SRT/timeline count mismatch')
    for a, b in zip(indexed, captions):
        for k in ('index','start_ms','end_ms','text'):
            if a[k] != b[k]:
                raise ValueError(f'SRT/timeline mismatch at cue {b["index"]}: {k}')
    mapped = []
    seen = []
    prev = 0
    for num, page in enumerate(pages, 1):
        ids = page.get('cue_indices', [])
        if not ids or page['slide'] != num or page['start_ms'] != prev or page['end_ms'] <= prev:
            raise ValueError(f'Invalid slide/page mapping at page {num}')
        selected = []
        for idx in ids:
            if not isinstance(idx, int) or idx < 1 or idx > len(captions):
                raise ValueError(f'Invalid cue reference {idx} on page {num}')
            cue = dict(captions[idx-1])
            if indexed[idx-1]['slide'] != num:
                raise ValueError(f'Cue {idx} belongs to another slide')
            if cue['start_ms'] < page['start_ms'] or cue['end_ms'] > page['end_ms']:
                raise ValueError(f'Cue {idx} exceeds page {num} time range')
            selected.append(cue)
            seen.append(idx)
        mapped.append({'page':num, 'title':page.get('title',''),
                       'start_ms':page['start_ms'],'end_ms':page['end_ms'],
                       'duration_ms':page['end_ms']-page['start_ms'],
                       'image':page.get('image',f'slide-{num:02d}.png'),
                       'cue_indices':ids,'captions':selected})
        prev = page['end_ms']
    if seen != list(range(1,len(captions)+1)) or timeline.get('total_ms') != prev:
        raise ValueError('Missing/duplicated cues or wrong total duration')
    return {'schema_version':2,
            'alignment':timeline.get('alignment','unknown'),
            'total_ms':prev,
            'srt_sha256':hashlib.sha256(srt_path.read_bytes()).hexdigest(),
            'page_count':len(mapped),
            'cue_count':len(captions),
            'pages':mapped,
            'cue_to_page':{str(c['index']):p['page'] for p in mapped for c in p['captions']}}


def create_map_file(timeline_path,srt_path,output):
    data = generate_map(json.loads(Path(timeline_path).read_text('utf-8')),srt_path)
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data


def validate_map_file(map_path,srt_path):
    result=json.loads(Path(map_path).read_text('utf-8'))
    rawhash=hashlib.sha256(Path(srt_path).read_bytes()).hexdigest()
    if result.get('srt_sha256')!=rawhash:
        raise ValueError('SRT differs from the subtitle source used for mapping')
    cues=read_srt(srt_path)
    pages=result.get('pages') or []
    got=[(c['index'],c['start_ms'],c['end_ms'],c['text'],p['page']) for p in pages for c in p['captions']]
    if len(pages)!=result.get('page_count') or len(got)!=len(cues):
        raise ValueError('Map counts do not match page/cue data')
    for cue, item in zip(cues,got):
        if (cue['index'],cue['start_ms'],cue['end_ms'],cue['text'])!=item[:4]:
            raise ValueError(f'Mapping mismatch at subtitle {cue["index"]}')
        if result.get('cue_to_page',{}).get(str(cue['index']))!=item[4]:
            raise ValueError(f'Subtitle {cue["index"]} has incorrect page mapping')
    seen=[];prev=0
    for i,page in enumerate(pages,1):
        if page['page']!=i or page['start_ms']!=prev or page['end_ms']<=prev:
            raise ValueError(f'Map slide order/boundaries invalid at {i}')
        if page['duration_ms']!=page['end_ms']-page['start_ms']:
            raise ValueError(f'Invalid duration at page {i}')
        for c in page['captions']:
            if not (page['start_ms']<=c['start_ms']<c['end_ms']<=page['end_ms']):
                raise ValueError('Subtitle outside its slide')
            seen.append(c['index'])
        prev=page['end_ms']
    if seen!=list(range(1,len(cues)+1)) or prev!=result.get('total_ms'):
        raise ValueError('Map omitted/duplicated a subtitle or wrong duration')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--timeline',required=True)
    ap.add_argument('--srt',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    m=create_map_file(a.timeline,a.srt,a.out)
    print(f'PASS: {m["page_count"]} PPT pages mapped to {m["cue_count"]} SRT cues')

if __name__=='__main__':
    main()
