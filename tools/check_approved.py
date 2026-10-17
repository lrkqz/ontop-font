"""Check that the approved glyphs are untouched: every glyph of a reference font must have the same
outline, advance and side bearing in the new build, and every kerning pair between them the same
value.

python tools/check_approved.py reference.otf fonts/otf/OnTop-Regular.otf

The reference is the approved 1.000 build (git show 196429b:fonts/otf/ONTOP-Regular.otf).
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, __file__.rsplit("tools", 1)[0] + "tools")
from raster import FontRaster  # noqa: E402

ref, new = TTFont(sys.argv[1]), TTFont(sys.argv[2])
rg, ng = ref.getGlyphSet(), new.getGlyphSet()
problems = 0
for name in ref.getGlyphOrder():
    if name not in ng:
        print("missing:", name)
        problems += 1
        continue
    a, b = RecordingPen(), RecordingPen()
    rg[name].draw(a)
    ng[name].draw(b)
    if a.value != b.value:
        print("outline changed:", name)
        problems += 1
    if ref["hmtx"][name] != new["hmtx"][name]:
        print("metrics changed:", name, ref["hmtx"][name], "->", new["hmtx"][name])
        problems += 1
rk, nk = FontRaster(sys.argv[1]).kern, FontRaster(sys.argv[2]).kern
old = set(ref.getGlyphOrder())
for pair in set(rk) | {p for p in nk if p[0] in old and p[1] in old}:
    if rk.get(pair, 0) != nk.get(pair, 0):
        print("kern changed:", pair, rk.get(pair, 0), "->", nk.get(pair, 0))
        problems += 1
print("approved glyphs:", len(old), "problems:", problems)
