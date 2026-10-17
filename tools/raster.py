"""Rasterise outlines (pathops paths or a built font's glyphs) with Pillow, anti-aliased by
supersampling. Used by the specimen, the overlay on the ON TOP image and the review sheets."""
from PIL import Image, ImageDraw, ImageChops
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sources"))
from geometry import flatten  # noqa: E402

SS = 4  # supersampling


def mask_from_contours(contours, w, h, scale, ox, oy):
    """contours in font units (y up) -> L-mode mask of size (w, h); (ox, oy) is where the font
    origin (x 0, baseline) lands in pixels, y down."""
    W, H = w * SS, h * SS
    acc = Image.new("1", (W, H), 0)
    for c in contours:
        if len(c) < 3:
            continue
        m = Image.new("1", (W, H), 0)
        pts = [((ox + x * scale) * SS, (oy - y * scale) * SS) for x, y in c]
        ImageDraw.Draw(m).polygon(pts, fill=1)
        acc = ImageChops.logical_xor(acc, m)
    return acc.convert("L").resize((w, h), Image.BOX)


def mask_from_path(path, w, h, scale, ox, oy):
    if path is None:
        return Image.new("L", (w, h), 0)
    return mask_from_contours(flatten(path), w, h, scale, ox, oy)


class FontRaster:
    """Glyph outlines of a built font file, for setting text exactly as the font says."""

    def __init__(self, font_path):
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        self.font = TTFont(font_path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]
        self.upm = self.font["head"].unitsPerEm
        self.kern = self._read_kerning()
        self._cache = {}
        self.RecordingPen = RecordingPen

    def _read_kerning(self):
        """Pair kerning from GPOS (format 1 and 2 pair adjustments), resolved per glyph pair."""
        pairs = {}
        if "GPOS" not in self.font:
            return pairs
        gpos = self.font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            for st in lookup.SubTable:
                if lookup.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "LookupType", 2) != 2 and lookup.LookupType not in (2, 9):
                    continue
                if not hasattr(st, "Format"):
                    continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for i, g1 in enumerate(cov):
                        for pvr in st.PairSet[i].PairValueRecord:
                            v = pvr.Value1.XAdvance if pvr.Value1 and hasattr(pvr.Value1, "XAdvance") else 0
                            pairs.setdefault((g1, pvr.SecondGlyph), v)
                elif st.Format == 2:
                    cd1 = st.ClassDef1.classDefs
                    cd2 = st.ClassDef2.classDefs
                    order = self.font.getGlyphOrder()
                    for g1 in cov:
                        c1 = cd1.get(g1, 0)
                        for g2 in order:
                            c2 = cd2.get(g2, 0)
                            rec = st.Class1Record[c1].Class2Record[c2]
                            v = rec.Value1.XAdvance if rec.Value1 and hasattr(rec.Value1, "XAdvance") else 0
                            if v:
                                pairs.setdefault((g1, g2), v)
        return pairs

    def glyph_name(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def contours(self, gname):
        if gname in self._cache:
            return self._cache[gname]
        pen = self.RecordingPen()
        self.gs[gname].draw(pen)
        out, cur, last = [], [], None
        for op, args in pen.value:
            if op == "moveTo":
                cur = [args[0]]; last = args[0]
            elif op == "lineTo":
                cur.append(args[0]); last = args[0]
            elif op == "curveTo":
                p0 = last
                p1, p2, p3 = args[-3], args[-2], args[-1]
                for i in range(1, 17):
                    t = i / 16; mt = 1 - t
                    cur.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                                mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
                last = p3
            elif op == "qCurveTo":
                pts = [last] + list(args)
                # implied on-curve points between consecutive off-curve points
                offs = pts[1:-1]
                on_end = pts[-1]
                seq = [pts[0]]
                for i, o in enumerate(offs):
                    seq.append(o)
                    if i < len(offs) - 1:
                        n = offs[i + 1]
                        seq.append(((o[0] + n[0]) / 2, (o[1] + n[1]) / 2))
                seq.append(on_end)
                p = seq[0]
                i = 1
                while i + 1 < len(seq):
                    c, e = seq[i], seq[i + 1]
                    for k in range(1, 9):
                        t = k / 8; mt = 1 - t
                        cur.append((mt * mt * p[0] + 2 * mt * t * c[0] + t * t * e[0], mt * mt * p[1] + 2 * mt * t * c[1] + t * t * e[1]))
                    p = e
                    i += 2
                last = on_end
            elif op in ("closePath", "endPath"):
                if cur:
                    out.append(cur)
                cur = []
        self._cache[gname] = out
        return out

    def layout(self, text, tracking=0):
        """[(glyph name, x offset in units)] and the total advance."""
        x = 0
        out = []
        prev = None
        for ch in text:
            g = self.glyph_name(ch)
            if prev is not None:
                x += self.kern.get((prev, g), 0)
            out.append((g, x))
            x += self.hmtx[g][0] + tracking
            prev = g
        return out, x

    def mask(self, text, w, h, scale, ox, oy, tracking=0):
        W, H = w * SS, h * SS
        acc = Image.new("1", (W, H), 0)
        items, _ = self.layout(text, tracking)
        for g, x in items:
            for c in self.contours(g):
                if len(c) < 3:
                    continue
                m = Image.new("1", (W, H), 0)
                pts = [((ox + (x + px) * scale) * SS, (oy - py * scale) * SS) for px, py in c]
                ImageDraw.Draw(m).polygon(pts, fill=1)
                acc = ImageChops.logical_xor(acc, m)
        return acc.convert("L").resize((w, h), Image.BOX)
