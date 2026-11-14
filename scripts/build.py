#!/usr/bin/env python3
"""Editable Chinese mathematics PPT + narration/SRT/timeline generator."""
import argparse
import json
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

W,H=7.5,13.333333
GREEN='0D2422'; PANEL='1D403B'; LIME='DAFB81'
WHITE='F8F8EA'; MUTED='B8D5C7'; CYAN='71DDCE'; ORANGE='FFBC78'
BANNED=[r'9\s*[:：]\s*16',r'竖屏教学',r'开头\s*\d+\s*秒',
        r'\d+\s*秒钩子',r'抓住数学矛盾',r'原题重排',r'新增推导',
        r'答案揭晓',r'互动挑战',r'用于剪映',r'口播脚本']
FONT='Noto Sans CJK SC'

def rgb(s): return RGBColor.from_string(s)
def textbox(slide,value,x,y,w,h,size=22,color=WHITE,bold=False,center=False):
    sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=sh.text_frame
    tf.clear()
    tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(.03)
    tf.margin_top=tf.margin_bottom=Inches(.02)
    tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    p=tf.paragraphs[0]
    p.alignment=PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    r=p.add_run()
    r.text=str(value)
    r.font.name=FONT
    r.font.size=Pt(size)
    r.font.bold=bold
    r.font.color.rgb=rgb(color)
    return sh

def box(slide,x,y,w,h,color,rounding=True):
    typ=MSO_SHAPE.ROUNDED_RECTANGLE if rounding else MSO_SHAPE.RECTANGLE
    sh=slide.shapes.add_shape(typ,Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(color)
    sh.line.fill.background()
    return sh

def line(slide,x1,y1,x2,y2,color=CYAN,width=3):
    sh=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    sh.line.color.rgb=rgb(color);sh.line.width=Pt(width)

def draw_slide(slide,d,index,total,series):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb=rgb(GREEN)
    box(slide,0,0,.09,H,LIME,False)
    bar_width=5.84/total
    for j in range(total):
        box(slide,.53+j*bar_width,.32,max(.03,bar_width-.04),.044,LIME if j<=index else PANEL,False)
    box(slide,.54,.73,4.2,.48,PANEL)
    textbox(slide,d.get('kicker') or '数学思维 · 一题一方法',.70,.78,3.95,.37,14,LIME,True)
    textbox(slide,f'{index+1:02d} / {total:02d}',5.75,.80,.7,.29,11,MUTED,True,True)
    textbox(slide,d.get('title',''),.53,1.91,6.1,1.05,34,WHITE,True)
    typ=d.get('type','concept')
    formula=d.get('formula','')
    if formula:
        box(slide,.53,3.42,5.95,1.63,WHITE)
        textbox(slide,formula,.77,3.69,5.47,1.07,26,GREEN,True,True)
    else:
        box(slide,.53,3.42,5.95,.1,PANEL)
    lines=d.get('lines') or d.get('steps') or []
    if typ=='quiz' and d.get('choices'):
        lines=list(lines)+[f"{q['key']}  {q['value']}" for q in d['choices']]
    if d.get('secondary'):lines=[d['secondary']]+list(lines)
    if typ=='triangle':
        box(slide,.53,5.17,5.95,2.3,PANEL)
        line(slide,1.17,7.07,5.71,7.07,LIME)
        line(slide,1.17,7.07,4.20,5.34,ORANGE)
        line(slide,4.20,5.34,5.71,7.07,CYAN)
        textbox(slide,'A',.83,7.04,.4,.36,17,ORANGE,True)
        textbox(slide,'B',5.75,7.04,.4,.36,17,CYAN,True)
        textbox(slide,'C',4.22,5.10,.4,.36,17,LIME,True)
        if d.get('angle_label'):
            textbox(slide,d['angle_label'],1.43,6.49,1,.35,16,ORANGE,True)
        y=7.67
    else:
        y=5.55 if formula else 3.77
    limit=2 if typ=='triangle' else 4
    for j,item in enumerate(lines[:limit]):
        box(slide,.53,y+j*.87,5.95,.73,PANEL)
        textbox(slide,item,.76,y+j*.87+.10,5.51,.55,18,WHITE,j==0)
    highlight=d.get('highlight') or d.get('prompt') or d.get('foot')
    if highlight:
        cy=min(10.42,max(8.60,y+len(lines[:limit])*.87+.35))
        box(slide,.53,cy,5.95,.91,PANEL)
        box(slide,.53,cy,.09,.91,LIME,False)
        sz=57 if typ=='result' and len(str(highlight))<=3 else 19
        textbox(slide,highlight,.74,cy+.09,5.47,.70,sz,LIME,True,True)
    line(slide,.53,11.81,6.43,11.81,'34564E',1)
    textbox(slide,series,.56,11.90,5.35,.38,12,MUTED)

def segments(text,max_chars=26):
    # Split first at natural punctuation, then hard-wrap overlong clauses.
    text=re.sub(r'\s+',' ',text).strip()
    parts=[]; current=''
    for ch in text:
        current+=ch
        if ch in '，。；：！？,;?!':
            parts.append(current.strip());current=''
    if current.strip():parts.append(current.strip())
    cues=[]
    for part in parts:
        while len(part)>max_chars:
            cues.append(part[:max_chars]);part=part[max_chars:]
        if part:cues.append(part)
    if ''.join(cues).replace(' ','')!=text.replace(' ',''):
        raise ValueError('SRT segmentation dropped narration content')
    return cues

def clock(ms):
    h,r=divmod(ms,3600000);m,r=divmod(r,60000);s,ms=divmod(r,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def validate(doc):
    """Reject unsafe/incomplete content before any user-facing artifact is emitted."""
    slides=doc.get('slides')
    if not isinstance(slides,list) or not slides:
        raise ValueError('slides must be a nonempty list')
    if not isinstance(doc.get('series',''),str):
        raise ValueError('series must be text')
    if any(re.search(p,doc.get('series',''),re.I) for p in BANNED):
        raise ValueError('Production instructions leaked into visible series/footer')
    allowed={'hook','question','concept','triangle','formula','factor','steps',
             'result','warning','quiz','check','closing'}
    for i,d in enumerate(slides,1):
        if not isinstance(d,dict):
            raise ValueError(f'Slide {i} must be an object')
        for key in ('title','type','notes'):
            if not isinstance(d.get(key),str) or not d[key].strip():
                raise ValueError(f'Slide {i} missing {key}')
        if d['type'] not in allowed:
            raise ValueError(f'Slide {i} unsupported type: {d["type"]}')
        # Rendering shows only four rows (two on a triangle page).
        # Reject, never silently discard authored teaching steps.
        line_items=d.get('lines') or d.get('steps') or []
        if not isinstance(line_items,list):
            raise ValueError(f'Slide {i} lines/steps must be a list')
        choices=d.get('choices') or []
        if not isinstance(choices,list):
            raise ValueError(f'Slide {i} choices must be a list')
        rows=len(line_items)+len(choices)+(1 if d.get('secondary') else 0)
        allowed_rows=2 if d['type']=='triangle' else 4
        if rows>allowed_rows:
            raise ValueError(f'Slide {i} has {rows} text rows; only {allowed_rows} are visible')
        for key,value in d.items():
            serialized=json.dumps(value,ensure_ascii=False)
            if any(re.search(p,serialized,re.I) for p in BANNED):
                raise ValueError(f'Slide {i} contains production copy in {key}')
        if len(d['notes'])<35:
            raise ValueError(f'Slide {i} narration too short for a detailed lesson')

def build(doc,out,ms_per_char=190):
    validate(doc)
    out.mkdir(parents=True,exist_ok=True)
    prs=Presentation()
    prs.slide_width=Inches(W);prs.slide_height=Inches(H)
    captions=[];timeline=[];t=0
    for i,d in enumerate(doc['slides']):
        slide=prs.slides.add_slide(prs.slide_layouts[6])
        draw_slide(slide,d,i,len(doc['slides']),doc.get('series','数学一题一方法'))
        slide.notes_slide.notes_text_frame.text=d['notes']
        start=t;indices=[]
        for txt in segments(d['notes']):
            duration=max(1600,10*round((len(txt.replace(' ',''))*ms_per_char+170)/10))
            captions.append({'index':len(captions)+1,'slide':i+1,'start_ms':t,'end_ms':t+duration,'text':txt})
            indices.append(len(captions));t+=duration
        t+=200
        timeline.append({'slide':i+1,'title':d['title'],'start_ms':start,'end_ms':t,'duration_ms':t-start,'cue_indices':indices,'image':f'slide-{i+1:02d}.png'})
    prs.save(str(out/'lesson.pptx'))
    srt='\n\n'.join(f"{c['index']}\n{clock(c['start_ms'])} --> {clock(c['end_ms'])}\n{c['text']}" for c in captions)+'\n'
    (out/'lesson.srt').write_text(srt,encoding='utf-8-sig')
    (out/'voiceover.txt').write_text('\n\n'.join(s['notes'] for s in doc['slides'])+'\n',encoding='utf-8')
    (out/'timeline.json').write_text(json.dumps({'schema_version':1,'alignment':'estimated_from_text_not_audio','total_ms':t,'slides':timeline,'cues':captions},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"PASS: {len(timeline)} editable slides, {len(captions)} SRT cues, approx {t/1000:.1f}s")

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',default='examples/tangent-integer-triangle/lesson.json')
    p.add_argument('--out',default='examples/tangent-integer-triangle/generated')
    p.add_argument('--ms-per-char',type=int,default=190)
    a=p.parse_args()
    build(json.loads(Path(a.input).read_text(encoding='utf-8')),Path(a.out),a.ms_per_char)
