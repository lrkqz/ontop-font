"""Print the automatic sidebearings for some glyphs (calibration against the image)."""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "sources"))
import pathops  # noqa: E402
import glyphs as GL  # noqa: E402
import spacing as SP  # noqa: E402
from geometry import flatten  # noqa: E402

for n in (sys.argv[1:] or ["O", "N", "T", "P", "H", "A", "V", "L", "E", "C", "D", "S", "K", "R", "zero"]):
    p = pathops.simplify(GL.G[n](), fix_winding=True, clockwise=False)
    b = p.bounds
    l, r = SP.sidebearings(flatten(p), b[0], b[2])
    print(f"{n:10s} width {b[2]-b[0]:7.1f}  lsb {l:6.1f}  rsb {r:6.1f}")
