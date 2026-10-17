"""A working sheet: every glyph drawn straight from the sources, large, with cap height and
baseline marked. python tools/sheet.py out.png [names...]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "sources"))
sys.path.insert(0, HERE)
import glyphs  # noqa: E402
from raster import mask_from_path  # noqa: E402

out = sys.argv[1]
names = sys.argv[2:] or [n for n in glyphs.G if n not in ("space", ".notdef")]
scale = float(os.environ.get("SHEET_SCALE", "0.16"))
cell_h = int(1250 * scale)
pad = 24
label = ImageFont.load_default()
rows = []
row, row_w = [], 0
maxw = int(os.environ.get("SHEET_W", "2400"))
built = []
for n in names:
    p = glyphs.G[n]()
    b = p.bounds if p is not None else (0, 0, 300, 0)
    w = int((b[2] - min(0, b[0]) + 120) * scale) + pad
    built.append((n, p, b, w))
for item in built:
    if row_w + item[3] > maxw and row:
        rows.append(row); row, row_w = [], 0
    row.append(item); row_w += item[3]
if row:
    rows.append(row)
H = len(rows) * cell_h
img = Image.new("RGB", (maxw, H), (18, 18, 22))
d = ImageDraw.Draw(img)
y = 0
for r in rows:
    x = 0
    base = y + int(950 * scale)
    for n, p, b, w in r:
        ox = 12 - min(0, b[0]) * scale
        d.line([(x, base), (x + w - 6, base)], fill=(60, 60, 70))
        d.line([(x, base - 700 * scale), (x + w - 6, base - 700 * scale)], fill=(60, 60, 70))
        m = mask_from_path(p, w, cell_h, scale, ox, base - y)
        img.paste((245, 245, 245), (x, y), m)
        d.text((x + 6, y + 6), n, fill=(140, 140, 150), font=label)
        x += w
    y += cell_h
img.save(out)
print(out, img.size)
