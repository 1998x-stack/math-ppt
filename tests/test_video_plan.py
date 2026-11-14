import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from assemble_video import make_concat

def test_concat_strict_page_continuity(tmp_path):
    slide=tmp_path/'slide-01.png';slide.write_bytes(b'png')
    t={'slides':[{'slide':1,'start_ms':0,'end_ms':800,'image':'slide-01.png'}], 'total_ms':800}
    target=tmp_path/'video.ffconcat'
    assert make_concat(t,tmp_path,target)==1
    assert target.read_text().count('file ')==2
    t['total_ms']=799
    with pytest.raises(ValueError,match='duration'):
        make_concat(t,tmp_path,target)

def test_concat_rejects_missing_images(tmp_path):
    t={'slides':[{'slide':1,'start_ms':0,'end_ms':800,'image':'slide-01.png'}], 'total_ms':800}
    with pytest.raises(FileNotFoundError):
        make_concat(t,tmp_path,tmp_path/'concat.txt')
