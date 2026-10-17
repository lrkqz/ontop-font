"""Build the typeface: python build.py [--review]

Draws every glyph from sources/glyphs.py, spaces and kerns it (sources/spacing.py), and writes
fonts/otf, fonts/ttf and fonts/webfonts (WOFF2). Needs: pip install -r requirements.txt

--review writes build/review/OnTop-Review.woff2 instead: the font with every design that is still
to be chosen as character variants (cv01, cv02, ...: value n is variant n), for the review page
build/review/index.html.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "sources"))

import pathops  # noqa: E402
from fontTools.fontBuilder import FontBuilder  # noqa: E402
from fontTools.pens.t2CharStringPen import T2CharStringPen  # noqa: E402
from fontTools.pens.ttGlyphPen import TTGlyphPen  # noqa: E402
from fontTools.pens.cu2quPen import Cu2QuPen  # noqa: E402
from fontTools.pens.roundingPen import RoundingPen  # noqa: E402
from fontTools.pens.transformPen import TransformPen  # noqa: E402
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

import glyphs as GL  # noqa: E402
import spacing as SP  # noqa: E402
from geometry import flatten  # noqa: E402

REVIEW = "--review" in sys.argv
CONFIG = json.load(open(os.path.join(HERE, "font.json"), encoding="utf-8"))
FAMILY = CONFIG["family"] + (" Review" if REVIEW else "")
STYLE = "Regular"
PS_NAME = CONFIG["psName"] + ("Review" if REVIEW else "") + "-" + STYLE
UPM = 1000
HM_BAR = 188                   # the middle bar: the strikeout is drawn at its weight and height
ASC, DESC = 950, -250          # the line box holds every glyph, and the caps sit in its middle

# --- glyphs ------------------------------------------------------------------------------------
names = [".notdef"] + [n for n in GL.G if n != ".notdef"]
paths = {}


def simplified(p):
    return None if p is None else pathops.simplify(p, fix_winding=True, clockwise=False)


for n in names:
    paths[n] = simplified(GL.G[n]())

# A letter with a mark or a stroke keeps the spacing of the letter under it (BASE_OF). In the
# review font every design still to be chosen is there in each variant, as character variants.
BASE_OF = {n: GL.base_of(n) for n in names if GL.base_of(n)}
CV = {}                        # cv tag -> (design, {glyph: [alternate per variant]})
if REVIEW:
    for design, variants in GL.VARIANTS.items():
        if len(variants) < 2:
            continue
        tag = f"cv{len(CV) + 1:02d}"
        chosen = GL.VARIANT[design]
        subs = {}
        for n, designs in GL.DEPENDS.items():
            if design not in designs:
                continue
            subs[n] = []
            for key in variants:
                GL.VARIANT[design] = key
                alt = f"{n}.{design}{key}"
                paths[alt] = simplified(GL.G[n]())
                names.append(alt)
                BASE_OF[alt] = BASE_OF[n]
                subs[n].append(alt)
            GL.VARIANT[design] = chosen
        CV[tag] = (design, subs)

# --- spacing -----------------------------------------------------------------------------------
# The image's own letters keep the image's spacing (see spacing.py); punctuation is set by hand.
FIXED = {
    "O": (68, 68), "N": (72, 72), "T": (25, 25), "P": (72, None),
    "period": (60, 60), "comma": (60, 60), "colon": (60, 60), "semicolon": (60, 60),
    "hyphen": (60, 60), "endash": (60, 60), "emdash": (60, 60), "periodcentered": (60, 60),
    "exclam": (72, 72), "question": (40, 60),
    "quotesingle": (60, 60), "quotedbl": (60, 60), "quoteright": (60, 60), "quoteleft": (60, 60),
    "quotesinglbase": (60, 60), "quotedblright": (60, 60), "quotedblleft": (60, 60), "quotedblbase": (60, 60),
    "slash": (20, 20), "parenleft": (70, 40), "parenright": (40, 70), "plus": (60, 60),
    "numbersign": (40, 40), "percent": (50, 50), "at": (60, 60), "Euro": (40, 60), "ampersand": (60, 40),
    "ellipsis": (60, 60), "bracketleft": (70, 40), "bracketright": (40, 70), "less": (60, 60), "greater": (60, 60),
    "guilsinglleft": (50, 50), "guilsinglright": (50, 50), "guillemotleft": (50, 50), "guillemotright": (50, 50),
    "asterisk": (50, 50), "underscore": (0, 0), "equal": (60, 60), "bar": (80, 80), "degree": (50, 50),
    "multiply": (60, 60),
    ".notdef": (60, 60),
}
SPACE_W = 545            # the image's word space: N's 72 + 545 + T's 25 = the 642 measured
ONE_LEFT = 120           # the 1 is narrow; it needs room on the side of its flag

metrics, shift = {}, {}
contours = {}
for n in names:
    p = paths[n]
    if p is None:
        metrics[n] = (SPACE_W, 0); shift[n] = 0; contours[n] = []
        continue
    contours[n] = flatten(p)
    if n in BASE_OF:
        continue
    xmin, ymin, xmax, ymax = p.bounds
    cs = contours[n]
    base = GL.ALT[n][0] if n in GL.ALT else n
    if base in ("Adieresis", "Odieresis", "Udieresis"):
        base = base[0]
    lsb, rsb = SP.sidebearings(cs, xmin, xmax)
    fl, fr = FIXED.get(n, FIXED.get(base, (None, None)))
    lsb = fl if fl is not None else lsb
    rsb = fr if fr is not None else rsb
    if n == "one":
        lsb = ONE_LEFT
    lsb, rsb = int(round(lsb)), int(round(rsb))
    metrics[n] = (int(round(lsb + (xmax - xmin) + rsb)), lsb)
    shift[n] = lsb - xmin
for n, base in BASE_OF.items():
    # the letter stays where it stands in its base; a mark may reach into the sidebearings
    shift[n] = shift[base]
    metrics[n] = (metrics[base][0], int(round(paths[n].bounds[0] + shift[n])))

# --- kerning -----------------------------------------------------------------------------------
from shapely.geometry import Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely import affinity  # noqa: E402

KERNABLE = [n for n in names if n not in (".notdef", "space")]
FIGURES = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}
prof, shapes = {}, {}
for n in KERNABLE:
    p = paths[n]
    xmin, _, xmax, _ = p.bounds
    dl, dr = SP.depths(contours[n], xmin, xmax)
    prof[n] = (dl, dr, metrics[n][1], metrics[n][0] - metrics[n][1] - (xmax - xmin))
    # the glyph as placed (its origin at 0), every contour's shell, for the distance check
    polys = [Polygon([(x + shift[n], y) for x, y in c]).buffer(0) for c in contours[n] if len(c) > 2]
    shapes[n] = unary_union(polys)


def distance(a, b, kern):
    return shapes[a].distance(affinity.translate(shapes[b], metrics[a][0] + kern, 0))


# Pairs fixed by the image: its O to P is 15 tighter than the even spacing gives.
KERN_FIXED = {("O", "P"): -15, ("Odieresis", "P"): -15}
LETTERS = [n for n in KERNABLE if n not in BASE_OF]
kerns = {}
for a in LETTERS:
    for b in LETTERS:
        punct = a in SP.PUNCT or b in SP.PUNCT
        figs = a in FIGURES and b in FIGURES
        k = SP.profile_kern(prof[a][1], prof[a][3], prof[b][0], prof[b][2], punct, punct or figs)
        k = max(k, SP.cap_for(a, b))
        if not punct and not figs:
            opened = SP.bar_open(prof[a][1], prof[a][3], prof[b][0], prof[b][2])
            if opened > 0:
                k = max(k, opened)
        k = SP.round5(k)
        if k < 0:
            need = SP.MIN_DIST_PUNCT if punct else SP.MIN_DIST
            while k < 0 and distance(a, b, k) < need:
                k += 5
            k = SP.round5(k)
        if k == 0 and not punct:
            d0 = distance(a, b, 0)
            if d0 < SP.POINT_BELOW:
                k = SP.round5(SP.POINT_DIST - d0) or 10
        if (a, b) in KERN_FIXED:
            k = KERN_FIXED[(a, b)]
        if k:
            kerns[(a, b)] = k
# A letter with a mark kerns as its base; only where its mark comes nearer the neighbour than the
# letters themselves do, the pair opens: to the same 70 (100 with punctuation) where the letters
# are kerned closer, else to the point distance of 60.
for a in KERNABLE:
    for b in KERNABLE:
        if a not in BASE_OF and b not in BASE_OF:
            continue
        ba, bb = BASE_OF.get(a, a), BASE_OF.get(b, b)
        k = kerns.get((ba, bb), 0)
        punct = a in SP.PUNCT or b in SP.PUNCT
        need = SP.MIN_DIST_PUNCT if punct else (SP.MIN_DIST if k < 0 else SP.POINT_DIST)
        if distance(a, b, k) < min(need, distance(ba, bb, k) - 0.5):
            while distance(a, b, k) < need:
                k += 5
        if k:
            kerns[(a, b)] = k
# Every pair as set must keep the outlines apart (also those not kerned).
touching = [(a, b, round(distance(a, b, kerns.get((a, b), 0)), 1)) for a in KERNABLE for b in KERNABLE
            if distance(a, b, kerns.get((a, b), 0)) < 20]

# --- features ----------------------------------------------------------------------------------
fea = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", ""]
by_tag = {}
for alt, (base, tag, label) in GL.ALT.items():
    by_tag.setdefault(tag, []).append((base, alt, label))
for tag in sorted(by_tag):
    items = by_tag[tag]
    fea.append(f"feature {tag} {{")
    fea.append(f'  featureNames {{ name "{items[0][2]}"; }};')
    for base, alt, _ in items:
        fea.append(f"  sub {base} by {alt};")
    fea.append(f"}} {tag};")
for tag, (design, subs) in CV.items():
    fea.append(f"feature {tag} {{")
    for n, alts in subs.items():
        fea.append(f"  sub {n} from [{' '.join(alts)}];")
    fea.append(f"}} {tag};")
fea.append("feature kern {")
for (a, b), k in sorted(kerns.items()):
    fea.append(f"  pos {a} {b} {k};")
fea.append("} kern;")
FEA = "\n".join(fea) + "\n"

# --- character map -----------------------------------------------------------------------------
# Lower case is set on the capitals; the dotless i and j too.
EXTRA = {0x131: "I", 0x237: "J"}
cmap = {}
for n, codes in GL.UNI.items():
    for c in codes:
        cmap[c] = n
        ch = chr(c)
        if ch.isalpha() and ch.upper() == ch and ch.lower() != ch and len(ch.lower()) == 1:
            cmap[ord(ch.lower())] = n          # lower case set on the capitals
cmap.update(EXTRA)

# --- name table --------------------------------------------------------------------------------
NAMES = {
    "familyName": FAMILY,
    "styleName": STYLE,
    "uniqueFontIdentifier": f"{CONFIG['version']};{CONFIG.get('vendor', 'NONE')};{PS_NAME}",
    "fullName": f"{FAMILY} {STYLE}",
    "psName": PS_NAME,
    "version": f"Version {CONFIG['version']}",
    "copyright": CONFIG["copyright"],
    "manufacturer": CONFIG.get("manufacturer", ""),
    "designer": CONFIG.get("designer", ""),
    "vendorURL": CONFIG.get("vendorURL", ""),
    "designerURL": CONFIG.get("designerURL", ""),
    "description": CONFIG.get("description", ""),
    "licenseDescription": CONFIG.get("license", ""),
    "licenseInfoURL": CONFIG.get("licenseURL", ""),
}
NAMES = {k: v for k, v in NAMES.items() if v}


def common(fb):
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC, lineGap=0)
    fb.setupNameTable(NAMES)
    ymax = max((paths[n].bounds[3] for n in names if paths[n] is not None))
    ymin = min((paths[n].bounds[1] for n in names if paths[n] is not None))
    fb.setupOS2(
        version=4, usWeightClass=400, usWidthClass=9, achVendID=CONFIG.get("vendor", "NONE")[:4].ljust(4),
        sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=0,
        usWinAscent=int(max(ASC, ymax + 10)), usWinDescent=int(max(-DESC, -ymin + 10)),
        sxHeight=700, sCapHeight=700, fsSelection=0x40 | 0x80, fsType=CONFIG.get("fsType", 0),
        ySubscriptXSize=650, ySubscriptYSize=600, ySubscriptYOffset=75, ySubscriptXOffset=0,
        ySuperscriptXSize=650, ySuperscriptYSize=600, ySuperscriptYOffset=350, ySuperscriptXOffset=0,
        yStrikeoutSize=HM_BAR, yStrikeoutPosition=int(350 + HM_BAR / 2),
    )
    fb.font["OS/2"].recalcUnicodeRanges(fb.font)
    fb.font["OS/2"].recalcCodePageRanges(fb.font)
    fb.setupPost(isFixedPitch=0, underlinePosition=-120, underlineThickness=80)
    fb.font["head"].fontRevision = float(CONFIG["version"])


def build_otf(out):
    fb = FontBuilder(UPM, isTTF=False)
    common(fb)
    cs = {}
    for n in names:
        pen = T2CharStringPen(metrics[n][0], None)
        if paths[n] is not None:
            paths[n].draw(TransformPen(RoundingPen(pen), (1, 0, 0, 1, shift[n], 0)))
        cs[n] = pen.getCharString()
    fb.setupCFF(PS_NAME, {"FullName": f"{FAMILY} {STYLE}", "FamilyName": FAMILY, "Weight": STYLE,
                          "Notice": CONFIG["copyright"]}, cs, {})
    addOpenTypeFeaturesFromString(fb.font, FEA)
    fb.save(out)


def build_ttf(out):
    fb = FontBuilder(UPM, isTTF=True)
    common(fb)
    gl = {}
    for n in names:
        pen = TTGlyphPen(None)
        if paths[n] is not None:
            paths[n].draw(TransformPen(Cu2QuPen(RoundingPen(pen), max_err=0.6, reverse_direction=True),
                                       (1, 0, 0, 1, shift[n], 0)))
        gl[n] = pen.glyph()
    fb.setupGlyf(gl)
    from fontTools.ttLib import newTable
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 0x000F}       # smooth and grid-fit at every size
    fb.font["gasp"] = gasp
    addOpenTypeFeaturesFromString(fb.font, FEA)
    fb.font["maxp"].maxZones = 1
    fb.save(out)


def main():
    base = CONFIG["fileName"]
    if REVIEW:
        out_dir = os.path.join(HERE, "build", "review")
        os.makedirs(out_dir, exist_ok=True)
        ttf = os.path.join(out_dir, base + "-Review.ttf")
        woff2 = os.path.join(out_dir, base + "-Review.woff2")
        build_ttf(ttf)
        f = TTFont(ttf)
        f.flavor = "woff2"
        f.save(woff2)
        designs = {tag: {"design": d, "name": GL.DESIGN_NAMES.get(d, d),
                         "variants": [[k, label] for k, (label, _) in GL.VARIANTS[d].items()],
                         "chosen": GL.VARIANT[d],
                         "glyphs": "".join(chr(GL.UNI[n][0]) for n in subs if GL.UNI.get(n))}
                   for tag, (d, subs) in CV.items()}
        with open(os.path.join(out_dir, "variants.json"), "w", encoding="utf-8") as fh:
            json.dump(designs, fh, ensure_ascii=False, indent=1)
        print("review font: glyphs", len(names), "kern pairs", len(kerns), "designs", len(CV))
        for p in (ttf, woff2):
            print(os.path.relpath(p, HERE), os.path.getsize(p))
        return
    for d in ("fonts/otf", "fonts/ttf", "fonts/webfonts"):
        os.makedirs(os.path.join(HERE, d), exist_ok=True)
    otf = os.path.join(HERE, "fonts/otf", base + "-Regular.otf")
    ttf = os.path.join(HERE, "fonts/ttf", base + "-Regular.ttf")
    woff2 = os.path.join(HERE, "fonts/webfonts", base + "-Regular.woff2")
    build_otf(otf)
    build_ttf(ttf)
    f = TTFont(ttf)
    f.flavor = "woff2"
    f.save(woff2)
    with open(os.path.join(HERE, "build", "features.fea"), "w", encoding="utf-8") as fh:
        fh.write(FEA)
    with open(os.path.join(HERE, "build", "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump({"advance_lsb": metrics, "kern": {f"{a} {b}": k for (a, b), k in sorted(kerns.items())}}, fh, indent=1)
    print("glyphs", len(names), "kern pairs", len(kerns))
    if touching:
        print("pairs closer than 20 units:", touching[:20], "..." if len(touching) > 20 else "")
    for p in (otf, ttf, woff2):
        print(os.path.relpath(p, HERE), os.path.getsize(p))


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    main()
