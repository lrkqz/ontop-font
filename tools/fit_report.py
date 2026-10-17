"""Edge-by-edge deviation of "ON TOP" in the font from his image, in image pixels.

python tools/fit_report.py fonts/ttf/OnTop-Regular.ttf reference/on-top.png

Every row and every column of the image is scanned for the sub-pixel places where the ink edge
crosses half coverage, in the image and in the font set over it (same cap height, same left
edge, same baseline). Where a row has the same number of crossings in both, they are paired and
their distance is the deviation there. Reported per letter: mean, 95th percentile and maximum.
"""
import sys, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from raster import FontRaster  # noqa: E402

BASE_Y, TOP_Y, LEFT_X = 170.69, 7.12, 6.56
font_path, img_path = sys.argv[1], sys.argv[2]
img = Image.open(img_path).convert("RGBA")
W, H = img.size
A = np.array(img)[..., 3].astype(float) / 255
fr = FontRaster(font_path)
scale = (BASE_Y - TOP_Y) / 700
ox = LEFT_X - fr.hmtx["O"][1] * scale
F = np.array(fr.mask("ON TOP", W, H, scale, ox, BASE_Y)).astype(float) / 255


def cross(line):
    out = []
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]
        if (a - 0.5) * (b - 0.5) < 0:
            out.append(i + (0.5 - a) / (b - a) + 0.5)
    return out


LETTERS = {"O": (0, 335), "N": (335, 700), "T": (790, 1116), "O2": (1116, 1452), "P": (1452, W)}
rows_all = []
skipped = [0, 0]
print("letter   mean   p95    max   (px; the cap height is 163.6 px)")
for k, (x0, x1) in LETTERS.items():
    ds = []
    for y in range(H):
        a, f = cross(A[y, x0:x1]), cross(F[y, x0:x1])
        if a and len(a) == len(f):
            ds += [abs(p - q) for p, q in zip(a, f)]
        elif a or f:
            skipped[0] += 1
    for x in range(x0, x1):
        a, f = cross(A[:, x]), cross(F[:, x])
        if a and len(a) == len(f):
            ds += [abs(p - q) for p, q in zip(a, f)]
        elif a or f:
            skipped[0] += 1
    ds = np.array(ds)
    # a pair further apart than 20 px is two different edges paired by count, not a deviation
    skipped[1] += int((ds > 20).sum())
    ds = ds[ds <= 20]
    rows_all.append(ds)
    print(f"  {k:4s}  {ds.mean():5.2f}  {np.percentile(ds, 95):5.2f}  {ds.max():5.2f}")
allds = np.concatenate(rows_all)
print(f"  all   {allds.mean():5.2f}  {np.percentile(allds, 95):5.2f}  {allds.max():5.2f}   ({len(allds)} edge points)")
print(f"  rows/columns with a different number of edges: {skipped[0]}; pairs set aside as mismatched: {skipped[1]}")
