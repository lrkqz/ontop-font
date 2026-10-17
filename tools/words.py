"""Set lines of text from a built font, white on the site's ground, for looking at spacing.

python tools/words.py font.ttf out.png cap_px "LINE ONE" "LINE TWO" ...
Features: prefix a line with ss01,ss04: to apply those stylistic sets (by glyph substitution)."""
import os, sys
from PIL import Image

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from raster import FontRaster  # noqa: E402

font, out, cap = sys.argv[1], sys.argv[2], float(sys.argv[3])
lines = sys.argv[4:]
fr = FontRaster(font)
scale = cap / 700
pad = int(cap * 0.6)
line_h = int(cap * 1.9)
import re
FEAT = re.compile(r"^((?:ss\d\d,?)+):")
widths = []
for ln in lines:
    widths.append(fr.layout(FEAT.sub("", ln))[1] * scale)
W = int(max(widths) + 2 * pad)
H = int(line_h * len(lines) + pad)
img = Image.new("RGB", (W, H), (11, 11, 13))
for i, ln in enumerate(lines):
    text = ln
    subs = {}
    if FEAT.match(ln):
        tags, text = ln.split(":", 1)
        gsub = fr.font["GSUB"].table if "GSUB" in fr.font else None
        if gsub:
            for fe in gsub.FeatureList.FeatureRecord:
                if fe.FeatureTag in tags.split(","):
                    for li in fe.Feature.LookupListIndex:
                        for st in gsub.LookupList.Lookup[li].SubTable:
                            subs.update(st.mapping)
    base = pad + line_h * i + cap * 1.2
    if subs:
        orig = fr.glyph_name
        fr.glyph_name = lambda ch, o=orig: subs.get(o(ch), o(ch))
    m = fr.mask(text, W, H, scale, pad, base)
    if subs:
        fr.glyph_name = orig
    img.paste((242, 242, 242), (0, 0), m)
img.save(out)
print(out, img.size)
