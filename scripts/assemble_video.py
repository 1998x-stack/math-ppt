#!/usr/bin/env python3
"""Assemble a narrated slide video from audio-calibrated timeline and PNG pages.

SRT is deliberately kept external: import the aligned SRT into the editor.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

def make_concat(timeline, slides_dir, path):
    pages=timeline.get('slides') or []
    if not pages:
        raise ValueError('Timeline must contain slide pages')
    if pages[0]['start_ms'] != 0:
        raise ValueError('Timeline must start at zero')
    lines=['ffconcat version 1.0']
    prev=0; last=None
    for i,page in enumerate(pages,1):
        start,end=page['start_ms'],page['end_ms']
        if start!=prev or end<=start:
            raise ValueError(f'Invalid page timing at {i}')
        image=page.get('image') or f'slide-{i:02d}.png'
        if Path(image).name!=image:
            raise ValueError('Image basename cannot contain a directory path')
        file=(Path(slides_dir)/image).resolve()
        if not file.is_file():
            raise FileNotFoundError(f'Missing PNG: {file}')
        quoted=str(file).replace("'", "'\''")
        lines.append(f"file '{quoted}'")
        lines.append(f"duration {(end-start)/1000:.6f}")
        last=f"file '{quoted}'";prev=end
    if timeline.get('total_ms')!=prev:
        raise ValueError('Timeline duration does not match its final slide')
    # FFmpeg concat demuxer needs the final frame repeated to honor its duration.
    lines.append(last)
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return len(pages)

def get_audio_ms(audio):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
        '-of','default=noprint_wrappers=1:nokey=1',str(audio)],
        text=True,capture_output=True,check=True)
    return round(float(r.stdout.strip())*1000)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--timeline',required=True)
    ap.add_argument('--slides-dir',required=True)
    ap.add_argument('--audio',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--allow-estimated',action='store_true',
        help='Draft only: permit text-estimated timing instead of audio alignment')
    ap.add_argument('--dry-run',action='store_true',
        help='Validate assets and save ffconcat without encoding an MP4')
    args=ap.parse_args()
    if not shutil.which('ffprobe'):
        ap.error('ffprobe is required')
    if not args.dry_run and not shutil.which('ffmpeg'):
        ap.error('ffmpeg is required')
    t=json.loads(Path(args.timeline).read_text(encoding='utf-8'))
    if t.get('alignment')!='per_cue_measured_audio' and not args.allow_estimated:
        ap.error('Refusing unaligned timeline. Align real TTS clips first, or use --allow-estimated for a draft')
    duration=get_audio_ms(args.audio)
    if abs(duration-t.get('total_ms',0))>300:
        ap.error(f'Audio ({duration}ms) and slide plan ({t.get("total_ms")}ms) differ by more than 300ms')
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    ffconcat=target.with_suffix('.ffconcat')
    n=make_concat(t,args.slides_dir,ffconcat)
    if args.dry_run:
        print(f'PASS: {n} slides, timing matches audio, ffconcat={ffconcat}')
        return
    command=['ffmpeg','-y','-hide_banner','-loglevel','error',
      '-safe','0','-f','concat','-i',str(ffconcat),'-i',str(args.audio),
      '-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p',
      '-fps_mode','vfr','-c:a','aac','-b:a','192k','-shortest',
      '-movflags','+faststart',str(target)]
    subprocess.run(command,check=True)
    print(f'PASS: {target} ({n} slide pages); import aligned lesson.srt separately')

if __name__=='__main__':main()
