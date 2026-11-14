"""Exercise actual per-cue audio measurement, WAV concatenation and retimed subtitles."""
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import build
from qa import parse_srt
from assemble_video import make_concat

def tiny_lesson():
    doc=json.loads((ROOT/'examples/tangent-integer-triangle/lesson.json').read_text('utf-8'))
    doc['slides']=doc['slides'][:1]
    return doc

def test_tts_alignment_and_audio_assembly(tmp_path):
    if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg is unavailable')
    source=tmp_path/'original'
    build(tiny_lesson(),source)
    original=json.loads((source/'timeline.json').read_text('utf-8'))
    audio=tmp_path/'cues'
    audio.mkdir()
    for cue in original['cues']:
        with wave.open(str(audio/f"{cue['index']:03d}.wav"),'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b'\x00\x00'*8000)
    result=tmp_path/'aligned'
    p=subprocess.run([sys.executable,str(ROOT/'scripts/retime_tts.py'),
       '--timeline',str(source/'timeline.json'),'--cue-audio-dir',str(audio),
       '--out',str(result),'--pause-ms','100','--assemble'],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    aligned=json.loads((result/'timeline.json').read_text('utf-8'))
    cues=aligned['cues']
    assert aligned['alignment']=='per_cue_measured_audio'
    assert all(c['end_ms']-c['start_ms']==500 for c in cues)
    assert all(cues[i]['start_ms']-cues[i-1]['end_ms']==100 for i in range(1,len(cues)))
    assert len(parse_srt((result/'lesson.srt').read_text('utf-8-sig')))==len(cues)
    with wave.open(str(result/'narration.wav'),'rb') as wav:
        actual=wav.getnframes()/wav.getframerate()*1000
    assert abs(actual-aligned['total_ms'])<1
    png=tmp_path/'pages';png.mkdir()
    (png/'slide-01.png').write_bytes(b'placeholder: plan validation checks existence only')
    concat=tmp_path/'sample.ffconcat'
    assert make_concat(aligned,png,concat)==1
    assert 'duration' in concat.read_text()
