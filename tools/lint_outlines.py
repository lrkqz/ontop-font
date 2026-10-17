"""Find outline artifacts in a built font: segments shorter than MIN_SEG units and corners sharper
than MIN_ANGLE degrees (slivers, steps and spikes left by boolean operations).

python tools/lint_outlines.py fonts/otf/OnTop-Regular.otf
"""
import math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

MIN_SEG, MIN_ANGLE = 15.0, 25.0
# Acute corners that are part of the design (where a diagonal meets a cap line or a stem).
ACUTE_BY_DESIGN = {"A", "A.ss01", "Adieresis", "Adieresis.ss01", "N", "M", "V", "W", "X", "Y", "Z", "K", "R", "R.ss02",
                   "seven", "slash", "percent", "Q", "ampersand", "uni1E9E", "less", "greater", "guilsinglleft",
                   "guilsinglright", "guillemotleft", "guillemotright", "multiply", "asterisk", "comma", "semicolon",
                   "quoteright", "quoteleft", "quotesinglbase", "quotedblright", "quotedblleft", "quotedblbase"}

# A letter with a mark or a stroke inherits its base's acute corners.
import os  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources"))
import glyphs as GL  # noqa: E402
ACUTE_BY_DESIGN |= {n for n, (base, _) in GL.COMPOSITE.items() if base in ACUTE_BY_DESIGN}

font = TTFont(sys.argv[1])
gs = font.getGlyphSet()
problems = 0
for name in font.getGlyphOrder():
    pen = RecordingPen()
    gs[name].draw(pen)
    contours, cur = [], []
    for op, args in pen.value:
        if op == "moveTo":
            cur = [("on", args[0])]
        elif op == "lineTo":
            cur.append(("on", args[0]))
        elif op in ("curveTo", "qCurveTo"):
            for a in args[:-1]:
                cur.append(("off", a))
            cur.append(("on", args[-1]))
        elif op in ("closePath", "endPath"):
            contours.append(cur)
    for c in contours:
        on = [p for t, p in c if t == "on"]
        n = len(c)
        for i in range(n):
            t0, p0 = c[i]
            t1, p1 = c[(i + 1) % n]
            if t0 == "on" and t1 == "on":
                d = math.dist(p0, p1)
                if 0 < d < MIN_SEG:
                    print(f"{name}: short segment {d:.1f} at {p0} -> {p1}")
                    problems += 1
        # short curves: on-curve points joined by off-curve points only, nearer than MIN_SEG
        ons = [i for i in range(n) if c[i][0] == "on"]
        for j, i in enumerate(ons):
            k = ons[(j + 1) % len(ons)]
            if (k - i) % n > 1:
                d = math.dist(c[i][1], c[k][1])
                if 0 < d < MIN_SEG:
                    print(f"{name}: short curve {d:.1f} at {c[i][1]} -> {c[k][1]}")
                    problems += 1
        # angles at on-curve points between their neighbours (control or on)
        for i in range(n):
            t, p = c[i]
            if t != "on":
                continue
            a = c[i - 1][1]
            b = c[(i + 1) % n][1]
            v1 = (a[0] - p[0], a[1] - p[1])
            v2 = (b[0] - p[0], b[1] - p[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 < 1e-6 or l2 < 1e-6:
                continue
            cos = max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
            ang = math.degrees(math.acos(cos))
            if ang < MIN_ANGLE and name not in ACUTE_BY_DESIGN:
                print(f"{name}: sharp corner {ang:.1f} deg at {p}")
                problems += 1
            if ang < 12 and name in ACUTE_BY_DESIGN:
                print(f"{name}: very sharp corner {ang:.1f} deg at {p}")
                problems += 1
print("problems:", problems)
