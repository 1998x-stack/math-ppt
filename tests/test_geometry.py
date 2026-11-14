"""The editable diagram must not contradict its own angle labels."""
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import TRIANGLE_VERTICES

def test_exact_triangle_geometry_for_featured_problem():
    ax,ay=TRIANGLE_VERTICES['A']
    bx,by=TRIANGLE_VERTICES['B']
    cx,cy=TRIANGLE_VERTICES['C']
    assert ay==by
    assert ax<cx<bx and cy<ay
    tan_a=(ay-cy)/(cx-ax)
    tan_b=(by-cy)/(bx-cx)
    assert abs(tan_a-1)<1e-12
    assert abs(tan_b-2)<1e-12
    A=math.atan(tan_a)
    B=math.atan(tan_b)
    C=math.pi-A-B
    assert abs(A-math.pi/4)<1e-12
    assert abs(math.tan(C)-3)<1e-12
    assert 0<C<math.pi/2
