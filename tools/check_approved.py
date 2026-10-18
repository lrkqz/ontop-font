"""Check that the approved glyphs are untouched: every glyph of a reference font must have the same
outline, advance and side bearing in the new build, and every kerning pair between them the same
value.

python tools/check_approved.py reference.otf fonts/otf/OnTop-Regular.otf

The reference is the approved 1.000 build (git show 196429b:fonts/otf/ONTOP-Regular.otf, or the
.ttf). Outlines are compared point for point, ignoring only how a contour is written down (an
explicit closing line, where it starts); where they still differ, the largest distance between the
two outlines is measured, and a TrueType build passes within one unit (its curves are converted to
quadratics with that tolerance).
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import LineString

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from raster import FontRaster  # noqa: E402

TOLERANCE = 1.0


def contours(glyphset, name):
    """Each contour as a list of segments [(op, points)], closing line dropped, starting at its
    smallest on-curve point."""
    pen = RecordingPen()
    glyphset[name].draw(pen)
    out, cur, start = [], [], None
    for op, args in pen.value:
        if op == "moveTo":
            cur, start = [], args[0]
        elif op in ("closePath", "endPath"):
            if cur and cur[-1][0] == "lineTo" and cur[-1][1][-1] == start:
                cur.pop()
            segs, pts = [], start
            for o, a in cur:
                segs.append((o, (pts,) + tuple(a)))
                pts = a[-1]
            if segs:
                i = min(range(len(segs)), key=lambda j: segs[j][1][0])
                segs = segs[i:] + segs[:i]
            out.append(tuple(segs))
        else:
            cur.append((op, args))
    return sorted(out)


def polyline(fr, name):
    return [LineString(c + c[:1]) for c in fr.contours(name) if len(c) > 1]


def deviation(fa, fb, name):
    a, b = polyline(fa, name), polyline(fb, name)
    if len(a) != len(b):
        return float("inf")
    # every contour against its nearest counterpart, both ways
    there = max(min(x.hausdorff_distance(y) for y in b) for x in a)
    back = max(min(y.hausdorff_distance(x) for x in a) for y in b)
    return max(there, back)


ref, new = TTFont(sys.argv[1]), TTFont(sys.argv[2])
rg, ng = ref.getGlyphSet(), new.getGlyphSet()
fa, fb = FontRaster(sys.argv[1]), FontRaster(sys.argv[2])
problems, within = 0, []
for name in ref.getGlyphOrder():
    if name not in ng:
        print("missing:", name)
        problems += 1
        continue
    if contours(rg, name) != contours(ng, name):
        d = deviation(fa, fb, name)
        if d <= TOLERANCE:
            within.append((name, round(d, 2)))
        else:
            print(f"outline changed: {name} (up to {d:.1f} units)")
            problems += 1
    if ref["hmtx"][name] != new["hmtx"][name]:
        print("metrics changed:", name, ref["hmtx"][name], "->", new["hmtx"][name])
        problems += 1
old = set(ref.getGlyphOrder())
for pair in set(fa.kern) | {p for p in fb.kern if p[0] in old and p[1] in old}:
    if fa.kern.get(pair, 0) != fb.kern.get(pair, 0):
        print("kern changed:", pair, fa.kern.get(pair, 0), "->", fb.kern.get(pair, 0))
        problems += 1
if within:
    print(f"written differently, same within {TOLERANCE:g} unit: {len(within)} glyphs, at most "
          f"{max(d for _, d in within)} units")
print("approved glyphs:", len(old), "problems:", problems)
