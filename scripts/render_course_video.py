#!/usr/bin/env python3
"""Render editable PPTX + aligned audio + SRT + explicit slide_map.json to MP4.

This is headless offline slide rendering, not fragile GUI screen recording.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from pptx import Presentation
from slide_map import validate_map_file


def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)


def audio_duration_ms(path):
    p=command(['ffprobe','-v','error','-show_entries','format=duration',
               '-of','default=noprint_wrappers=1:nokey=1',str(path)])
    return round(float(p.stdout.strip())*1000)


def convert_pages(pptx, folder, pages, width, height):
    if not shutil.which('libreoffice') or not shutil.which('pdftoppm'):
        raise RuntimeError('libreoffice and pdftoppm are required to render PPTX')
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    lo_profile=(folder/'lo-profile').as_uri()
    command(['libreoffice','-env:UserInstallation='+lo_profile,'--headless',
             '--convert-to','pdf','--outdir',str(folder),str(Path(pptx).resolve())])
    pdf=folder/(Path(pptx).stem+'.pdf')
    if not pdf.is_file() or pdf.stat().st_size==0:
        raise RuntimeError('PowerPoint to PDF conversion failed')
    command(['pdftoppm','-png','-r','120','-scale-to-x',str(width),
             '-scale-to-y',str(height),str(pdf),str(folder/'page')])
    found=sorted(folder.glob('page-*.png'))
    if len(found)!=len(pages):
        raise RuntimeError(f'PPTX slide count: {len(pages)}; rendered images: {len(found)}')
    for page,original in zip(pages,found):
        target=folder/page['image']
        if Path(page['image']).name!=page['image']:
            raise ValueError('Slide image may only be a basename')
        original.rename(target)
    return [folder/p['image'] for p in pages]


def create_concat(images,pages,output):
    if len(images)!=len(pages):
        raise ValueError('Images/pages count mismatch')
    result=['ffconcat version 1.0']
    for image,page in zip(images,pages):
        if not Path(image).is_file():
            raise FileNotFoundError(image)
        filename=Path(image).name
        if "'" in filename:
            raise ValueError('Slide image basename cannot contain a single quote')
        result += [f"file '{filename}'",f"duration {(page['end_ms']-page['start_ms'])/1000:.6f}"]
    result.append(f"file '{Path(images[-1]).name}'")
    Path(output).write_text('\n'.join(result)+'\n',encoding='utf-8')


def make_video(pptx,srt,audio,map_path,output,
               width=1080,height=1920,fps=25,burn=True,
               allow_estimated=False,duration_tolerance_ms=400):
    for p in (pptx,srt,audio,map_path):
        if not Path(p).is_file():
            raise FileNotFoundError(p)
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('ffmpeg/ffprobe are required')
    if not all(isinstance(v,int) and v>0 for v in (width,height,fps)):
        raise ValueError('Width, height and FPS must be positive integers')
    mapped=validate_map_file(map_path,srt)
    if mapped['alignment']!='per_cue_measured_audio' and not allow_estimated:
        raise ValueError('SRT timing is estimated. Use scripts/retime_tts.py with real audio first; '
                         'or --allow-estimated for a draft (not guaranteed sync).')
    slide_count=len(Presentation(str(pptx)).slides)
    if slide_count!=mapped['page_count']:
        raise ValueError(f'PPT has {slide_count} pages but map has {mapped["page_count"]}')
    audio_ms=audio_duration_ms(audio)
    if abs(audio_ms-mapped['total_ms'])>duration_tolerance_ms:
        raise ValueError(f'Audio duration {audio_ms}ms does not match slide map '
                         f'{mapped["total_ms"]}ms (tolerance {duration_tolerance_ms}ms). '
                         'Retiming subtitles is required, not just changing total duration.')
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='math-ppt-video-') as tmp:
        folder=Path(tmp)
        pages=mapped['pages']
        images=convert_pages(pptx,folder,pages,width,height)
        create_concat(images,pages,folder/'slides.ffconcat')
        shutil.copyfile(srt,folder/'subtitles.srt')
        filters=[f'fps={fps}']
        if burn:
            # Run in a private working directory to avoid arbitrary paths in libass filter.
            # Always apply fps BEFORE subtitles so captions change within static slides.
            filters.append("subtitles=subtitles.srt:force_style='Alignment=2,MarginV=145,FontSize=22,Outline=2'")
        filters.append('format=yuv420p')
        video_ms=mapped['total_ms']
        args=['ffmpeg','-y','-hide_banner','-loglevel','error',
              '-safe','0','-f','concat','-i','slides.ffconcat','-i',str(Path(audio).resolve()),
              '-vf',','.join(filters),'-t',f'{video_ms/1000:.3f}',
              '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',
              '-c:a','aac','-b:a','160k','-ar','48000',
              '-movflags','+faststart',str(output)]
        command(args,cwd=folder)
    sidecar=output.with_suffix('.srt')
    if sidecar.resolve()!=Path(srt).resolve():
        shutil.copyfile(srt,sidecar)
    manifest={'video':str(output),'subtitle':str(sidecar),
              'pptx_pages':slide_count,'srt_cues':mapped['cue_count'],
              'duration_ms':mapped['total_ms'],'audio_duration_ms':audio_ms,
              'caption_mode':'burned+sidecar' if burn else 'sidecar_only',
              'alignment':mapped['alignment'], 'render':'headless_libreoffice_pdf_to_png',
              'width':width,'height':height,'fps':fps}
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pptx',required=True)
    p.add_argument('--srt',required=True)
    p.add_argument('--audio',required=True)
    p.add_argument('--slide-map',required=True,help='Explicit slide-to-SRT cue mapping JSON')
    p.add_argument('--out',required=True)
    p.add_argument('--width',type=int,default=1080)
    p.add_argument('--height',type=int,default=1920)
    p.add_argument('--fps',type=int,default=25)
    p.add_argument('--no-burn-subtitles',action='store_true')
    p.add_argument('--allow-estimated',action='store_true',
                   help='Draft only: estimated timing may be wrong even if audio length matches')
    p.add_argument('--duration-tolerance-ms',type=int,default=400)
    a=p.parse_args()
    result=make_video(a.pptx,a.srt,a.audio,a.slide_map,a.out,
                      a.width,a.height,a.fps,not a.no_burn_subtitles,
                      a.allow_estimated,a.duration_tolerance_ms)
    print('PASS: created MP4, captions and manifest:',result['video'])

if __name__=='__main__':
    main()
