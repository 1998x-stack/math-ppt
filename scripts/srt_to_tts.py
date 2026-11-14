#!/usr/bin/env python3
"""Generate per-cue audio from SRT with optional edge-tts, preserving slide identity.

`--dry-run` requires no external service and writes a TTS job manifest.
After audio generation, run retime_tts.py to regenerate accurate captions and page map.
"""
import argparse
import asyncio
import json
from pathlib import Path

from slide_map import validate_map_file


def jobs_from_map(map_path,srt_path,output_dir):
    m=validate_map_file(map_path,srt_path)
    jobs=[]
    for page in m['pages']:
        for cue in page['captions']:
            jobs.append({'cue_index':cue['index'], 'page':page['page'],
                         'text':cue['text'], 'file':f"{cue['index']:03d}.mp3",
                         'estimated_start_ms':cue['start_ms'],
                         'estimated_end_ms':cue['end_ms']})
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    (out/'tts_jobs.json').write_text(json.dumps({'alignment':'requires_measured_audio',
                            'provider':'edge-tts-unofficial',
                            'total':len(jobs),'jobs':jobs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return jobs


async def synthesize(jobs,folder,voice,rate,overwrite=False):
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError('pip install edge-tts (optional; requires network)') from e
    for job in jobs:
        path=Path(folder)/job['file']
        if path.exists() and path.stat().st_size>0 and not overwrite:
            continue
        # Provider is unofficial and rate limited; sequential requests are intentional.
        tts=edge_tts.Communicate(job['text'],voice=voice,rate=rate)
        await tts.save(str(path))
        if not path.exists() or path.stat().st_size==0:
            raise RuntimeError(f'Empty TTS output at subtitle {job["cue_index"]}')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--srt',required=True)
    ap.add_argument('--slide-map',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--voice',default='zh-CN-YunxiNeural')
    ap.add_argument('--rate',default='-5%')
    ap.add_argument('--dry-run',action='store_true')
    ap.add_argument('--overwrite',action='store_true')
    args=ap.parse_args()
    jobs=jobs_from_map(args.slide_map,args.srt,args.out)
    if args.dry_run:
        print(f'PASS: {len(jobs)} TTS jobs exported; no speech generated')
        return
    asyncio.run(synthesize(jobs,args.out,args.voice,args.rate,args.overwrite))
    print(f'PASS: {len(jobs)} per-cue audio clips ready; now run retime_tts.py --assemble')

if __name__=='__main__':main()
