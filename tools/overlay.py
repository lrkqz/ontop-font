"""Lay "ON TOP" set in the built font over his image at the same cap height and measure.

python tools/overlay.py fonts/ttf/OnTop-Regular.ttf reference/on-top.png build/overlay

Writes overlay.png (image red, font green: where both are, yellow), diff.png (what differs,
magnified), and prints the deviation: pixels that differ, the share of the letters' area, and per
letter where its edges lie in the image and in the font.
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from raster import FontRaster  # noqa: E402

font_path, img_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)

# Where the image's letters stand (measured; tools/measure.py): baseline, cap top, the O's left edge.
BASE_Y, TOP_Y, LEFT_X = 170.69, 7.12, 6.56
img = Image.open(img_path).convert("RGBA")
W, H = img.size
alpha = np.array(img)[..., 3].astype(float) / 255

fr = FontRaster(font_path)
scale = (BASE_Y - TOP_Y) / 700
items, _ = fr.layout("ON TOP")
lsb_O = fr.hmtx["O"][1]
ox = LEFT_X - lsb_O * scale
m = fr.mask("ON TOP", W, H, scale, ox, BASE_Y)
f = np.array(m).astype(float) / 255

diff = np.abs(alpha - f)
both = np.minimum(alpha, f).sum()
either = np.maximum(alpha, f).sum()
print(f"image ink {alpha.sum():.0f} px, font ink {f.sum():.0f} px, ratio {f.sum() / alpha.sum():.4f}")
print(f"overlap (IoU) {both / either:.4f}; differing area {diff.sum():.0f} px = {diff.sum() / alpha.sum() * 100:.2f}% of the letters")
print(f"pixels differing by more than half: {(diff > 0.5).sum()}")


def runs(a):
    on = a.max(axis=0) > 0.5
    rs, s = [], None
    for x, v in enumerate(on):
        if v and s is None:
            s = x
        if not v and s is not None:
            rs.append((s, x)); s = None
    if s is not None:
        rs.append((s, len(on)))
    return rs


def edge(a, x0, x1, side):
    # sub-pixel ink edge along the middle third of the cap height, from coverage sums
    band = a[int(TOP_Y + 55):int(BASE_Y - 55), x0:x1]
    cov = band.sum(axis=0) / band.shape[0]
    return x0 + cov.sum() if side == "w" else None


ri, rf = runs(alpha), runs(f)
print("letter  image x0..x1      font x0..x1       dx0    dx1")
for name, a, b in zip("ONTOP", ri, rf):
    def ext(arr, r):
        col = arr[:, r[0]:r[1]].max(axis=0)
        # sub-pixel: count partial coverage at the ends
        x0 = r[0] + (1 - col[0]); x1 = r[1] - (1 - col[-1])
        return x0, x1
    ia, fa = ext(alpha, a), ext(f, b)
    print(f"  {name}     {ia[0]:7.2f}..{ia[1]:7.2f}   {fa[0]:7.2f}..{fa[1]:7.2f}   {fa[0]-ia[0]:+5.2f}  {fa[1]-ia[1]:+5.2f}")

rgb = np.zeros((H, W, 3), np.uint8)
rgb[..., 0] = (alpha * 255).astype(np.uint8)
rgb[..., 1] = (f * 255).astype(np.uint8)
Image.fromarray(rgb).save(os.path.join(out, "overlay.png"))
d = (np.clip(diff * 3, 0, 1) * 255).astype(np.uint8)
Image.fromarray(d).save(os.path.join(out, "diff.png"))
Image.fromarray(rgb).resize((W * 3, H * 3), Image.NEAREST).crop((0, 0, 1400, H * 3)).save(os.path.join(out, "overlay-zoom-left.png"))
Image.fromarray(rgb).resize((W * 3, H * 3), Image.NEAREST).crop((W * 3 - 1400, 0, W * 3, H * 3)).save(os.path.join(out, "overlay-zoom-right.png"))
