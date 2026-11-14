#!/usr/bin/env python3
"""Measure numbered TTS clips and write a subtitle/page timeline based on audio."""
import argparse
import json
import shutil
import subprocess
import wave
from pathlib import Path

EXT=('.wav','.mp3','.m4a','.flac','.aac','.ogg')

def clock(ms):
    h,r=divmod(ms,3600000);m,r=divmod(r,60000);s,ms=divmod(r,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def find_clip(folder,index):
    found=[folder/f'{index:03d}{suffix}' for suffix in EXT
           if (folder/f'{index:03d}{suffix}').is_file()]
    if len(found)!=1:
        raise ValueError(f'Need exactly one clip for cue {index:03d}')
    return found[0]

def audio_ms(path):
    p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
      '-of','default=noprint_wrappers=1:nokey=1',str(path)],check=True,capture_output=True,text=True)
    return int(round(float(p.stdout.strip())*1000))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--timeline',required=True)
    p.add_argument('--cue-audio-dir',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--pause-ms',type=int,default=80)
    p.add_argument('--assemble',action='store_true',help='also build matching narration.wav')
    a=p.parse_args()
    if not shutil.which('ffprobe'):p.error('ffprobe required')
    if a.assemble and not shutil.which('ffmpeg'):p.error('ffmpeg required')
    orig=json.loads(Path(a.timeline).read_text(encoding='utf-8'))
    clips=Path(a.cue_audio_dir);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    now=0;new_cues=[];new_pages=[]
    wav=None
    if a.assemble:
        wav=wave.open(str(out/'narration.wav'),'wb')
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(48000)
    try:
        for page in orig['slides']:
            start=now
            for index in page['cue_indices']:
                old=orig['cues'][index-1]
                clip=find_clip(clips,index)
                if wav:
                    pcm=subprocess.run(['ffmpeg','-v','error','-i',str(clip),
                      '-f','s16le','-ar','48000','-ac','1','-'],capture_output=True,check=True).stdout
                    duration=round(len(pcm)/2/48000*1000)
                    wav.writeframes(pcm)
                    wav.writeframes(b'\x00\x00'*round(48000*a.pause_ms/1000))
                else:
                    duration=audio_ms(clip)
                new_cues.append({**old,'start_ms':now,'end_ms':now+duration})
                now+=duration+a.pause_ms
            new_pages.append({**page,'start_ms':start,'end_ms':now,'duration_ms':now-start})
    finally:
        if wav:wav.close()
    result={**orig,'alignment':'per_cue_measured_audio','total_ms':now,
            'slides':new_pages,'cues':new_cues}
    (out/'timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'lesson.srt').write_text('\n\n'.join(
        f"{c['index']}\n{clock(c['start_ms'])} --> {clock(c['end_ms'])}\n{c['text']}" for c in new_cues)+'\n',encoding='utf-8-sig')
    print(f"Retimed {len(new_cues)} cues, {len(new_pages)} slides, {now/1000:.2f}s")
    if not a.assemble:
        print('Audio not assembled: insert the exact configured pauses between clips.')

if __name__=='__main__':main()
