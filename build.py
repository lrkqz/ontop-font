"""Build the typeface: python build.py [--review | --direct]

Draws every glyph from sources/glyphs.py, spaces and kerns it (sources/spacing.py), writes the
UFO sources/OnTop-Regular.ufo and builds fonts/otf, fonts/ttf and fonts/webfonts (WOFF2) from it with
Google's builder (gftools builder sources/config.yaml), as Google's toolchain does.
Needs: pip install -r requirements.txt

--direct writes the fonts straight from fontTools into build/direct instead (no gftools).

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
        if len(variants) < 2 or design in GL.CHOSEN:
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
                if n in BASE_OF:
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
    # GF Latin Core: the signs take the spacing of the signs they are drawn from
    "braceleft": (70, 40), "braceright": (40, 70), "exclamdown": (72, 72), "questiondown": (60, 40),
    "bullet": (60, 60), "ordfeminine": (50, 50), "ordmasculine": (50, 50), "divide": (60, 60), "minus": (60, 60),
    "backslash": (20, 20), "asciicircum": (60, 60), "asciitilde": (60, 60), "copyright": (60, 60),
    "registered": (60, 60), "trademark": (50, 50), "section": (60, 60), "paragraph": (60, 60),
    **{n: (60, 60) for n in GL.SPACING_ACCENTS}, "uni25CC": (60, 60),
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
    if n in GL.COMBINING_MARKS:
        # no width: the mark stands over the letter before it
        metrics[n] = (0, int(round(p.bounds[0]))); shift[n] = 0
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

KERNABLE = [n for n in names if n not in (".notdef", "space", "uni25CC") and n not in GL.COMBINING_MARKS
            and n not in GL.SPACING_ACCENTS]
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
FEA_UFO = "\n".join(fea) + "\n"          # the UFO's features.fea: ufo2ft adds GDEF, mark and kern
for tag, (design, subs) in CV.items():
    fea.append(f"feature {tag} {{")
    for n, alts in subs.items():
        fea.append(f"  sub {n} from [{' '.join(alts)}];")
    fea.append(f"}} {tag};")
# Marks: every letter has an anchor over its middle (TOP_X where it differs), under the middle of
# its foot, and where the ogonek stands; the combining marks attach there. On a letter that carries
# a mark already, and on a mark, the next mark stands MARK_GAP above (or below) it.
MARK_GAP = 60
LETTERS_FOR_MARKS = [n for n in names if paths.get(n) is not None and n not in GL.COMBINING_MARKS
                     and (n in BASE_OF or len(n.split(".")[0]) == 1 and n[0].isalpha()
                          or n.split(".")[0] in ("AE", "OE", "Thorn", "uni1E9E", "uni25CC"))]


def anchors_of(n):
    base = BASE_OF.get(n, n)
    letter = base.split(".")[0]
    b, bb = paths[n].bounds, paths[base].bounds
    mid = (bb[0] + bb[2]) / 2
    top = GL.TOP_X.get(letter, mid)
    og = GL.OGONEK_X.get(letter, bb[2] - 150)
    top_y = b[3] + MARK_GAP - GL.DOT_GAP if b[3] > max(bb[3], GL.CH) + 1 else GL.CH
    bottom_y = b[1] - MARK_GAP if b[1] < min(bb[1], 0) - 1 else 0
    return {"top": (top + shift[n], top_y), "bottom": (mid + shift[n], bottom_y), "ogonek": (og + shift[n], 0)}


MARK_ANCHOR = {"cedilla": "bottom", "commaaccent": "bottom", "ogonek": "ogonek"}


def mark_anchors(n):
    """A combining mark's own anchor (_top, _bottom, _ogonek) and the one the next mark takes."""
    kind = MARK_ANCHOR.get(GL.COMBINING_MARKS[n], "top")
    b = paths[n].bounds
    own = ("_" + kind, (GL.COMBINING_X, GL.CH if kind == "top" else 0))
    if kind == "top":
        return [own, ("top", (GL.COMBINING_X, b[3] + MARK_GAP - GL.DOT_GAP))]
    if kind == "bottom":
        return [own, ("bottom", (GL.COMBINING_X, b[1] - MARK_GAP))]
    return [own]


fea.append("table GDEF {")
fea.append("  GlyphClassDef [{}], , [{}], ;".format(
    " ".join(n for n in names if n not in GL.COMBINING_MARKS and paths.get(n) is not None),
    " ".join(GL.COMBINING_MARKS)))
fea.append("} GDEF;")
for n in GL.COMBINING_MARKS:
    (own, (x, y)) = mark_anchors(n)[0]
    fea.append(f"markClass {n} <anchor {x} {y}> @MC_{own[1:]};")
fea.append("feature mark {")
for kind in ("top", "bottom", "ogonek"):
    fea.append(f"  lookup mark_{kind} {{")
    for n in LETTERS_FOR_MARKS:
        x, y = anchors_of(n)[kind]
        fea.append(f"    pos base {n} <anchor {int(round(x))} {int(round(y))}> mark @MC_{kind};")
    fea.append(f"  }} mark_{kind};")
fea.append("} mark;")
fea.append("feature mkmk {")
for kind in ("top", "bottom"):
    fea.append(f"  lookup mkmk_{kind} {{")
    for n in GL.COMBINING_MARKS:
        for name, (x, y) in mark_anchors(n)[1:]:
            if name == kind:
                fea.append(f"    pos mark {n} <anchor {int(round(x))} {int(round(y))}> mark @MC_{kind};")
    fea.append(f"  }} mkmk_{kind};")
fea.append("} mkmk;")
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


def write_ufo(path):
    """The UFO that Google's toolchain builds from (gftools builder sources/config.yaml): every glyph
    as placed and rounded, its anchors, the kerning and the stylistic sets."""
    import ufoLib2
    from fontTools.pens.pointPen import SegmentToPointPen
    major, minor = CONFIG["version"].split(".")
    ufo = ufoLib2.Font()
    i = ufo.info
    i.familyName, i.styleName = FAMILY, STYLE
    i.styleMapFamilyName, i.styleMapStyleName = FAMILY, "regular"
    i.versionMajor, i.versionMinor = int(major), int(minor)
    i.copyright = CONFIG["copyright"]
    i.openTypeNameDesigner = CONFIG.get("designer")
    i.openTypeNameDesignerURL = CONFIG.get("designerURL")
    i.openTypeNameManufacturer = CONFIG.get("manufacturer")
    i.openTypeNameManufacturerURL = CONFIG.get("vendorURL")
    i.openTypeNameLicense = CONFIG.get("license")
    i.openTypeNameLicenseURL = CONFIG.get("licenseURL")
    i.openTypeNameDescription = CONFIG.get("description")
    i.postscriptFontName = PS_NAME
    i.unitsPerEm = UPM
    i.ascender, i.descender, i.capHeight, i.xHeight = ASC, DESC, 700, 700
    i.openTypeHheaAscender, i.openTypeHheaDescender, i.openTypeHheaLineGap = ASC, DESC, 0
    i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender, i.openTypeOS2TypoLineGap = ASC, DESC, 0
    ymax = max(paths[n].bounds[3] for n in names if paths[n] is not None)
    ymin = min(paths[n].bounds[1] for n in names if paths[n] is not None)
    i.openTypeOS2WinAscent = int(max(ASC, ymax + 10))
    i.openTypeOS2WinDescent = int(max(-DESC, -ymin + 10))
    i.openTypeOS2Selection = [7]               # USE_TYPO_METRICS
    i.openTypeOS2Type = []                     # installable: fsType 0
    i.openTypeOS2VendorID = CONFIG.get("vendor", "NONE")[:4].ljust(4)
    i.openTypeOS2WeightClass, i.openTypeOS2WidthClass = 400, 9
    i.openTypeOS2SubscriptXSize, i.openTypeOS2SubscriptYSize = 650, 600
    i.openTypeOS2SubscriptXOffset, i.openTypeOS2SubscriptYOffset = 0, 75
    i.openTypeOS2SuperscriptXSize, i.openTypeOS2SuperscriptYSize = 650, 600
    i.openTypeOS2SuperscriptXOffset, i.openTypeOS2SuperscriptYOffset = 0, 350
    i.openTypeOS2StrikeoutSize, i.openTypeOS2StrikeoutPosition = HM_BAR, int(350 + HM_BAR / 2)
    i.postscriptUnderlinePosition, i.postscriptUnderlineThickness = -120, 80
    i.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]
    i.openTypeHeadCreated = "2026/10/16 00:00:00"
    codes = {}
    for c, n in cmap.items():
        codes.setdefault(n, []).append(c)
    for n in names:
        g = ufo.newGlyph(n)
        g.width = metrics[n][0]
        g.unicodes = sorted(codes.get(n, []))
        if paths[n] is not None:
            paths[n].draw(TransformPen(RoundingPen(SegmentToPointPen(g.getPointPen())), (1, 0, 0, 1, shift[n], 0)))
        if n in LETTERS_FOR_MARKS:
            for kind, (x, y) in anchors_of(n).items():
                g.appendAnchor({"name": kind, "x": int(round(x)), "y": int(round(y))})
        if n in GL.COMBINING_MARKS:
            for name, (x, y) in mark_anchors(n):
                g.appendAnchor({"name": name, "x": int(round(x)), "y": int(round(y))})
    ufo.lib["public.glyphOrder"] = names
    ufo.lib["public.openTypeMeta"] = {"dlng": ["Latn"], "slng": ["Latn"]}
    ufo.lib["public.openTypeCategories"] = {n: ("mark" if n in GL.COMBINING_MARKS else "base")
                                            for n in names if paths[n] is not None}
    ufo.kerning = {(a, b): k for (a, b), k in sorted(kerns.items())}
    ufo.features.text = FEA_UFO
    ufo.save(path, overwrite=True)


def gftools_build():
    """Build fonts/ from the UFO with Google's own builder, as their toolchain will."""
    import shutil, subprocess
    exe = shutil.which("gftools", path=os.path.dirname(sys.executable)) or shutil.which("gftools")
    if not exe:
        sys.exit("gftools not found: pip install -r requirements.txt (or build.py --direct)")
    env = dict(os.environ, PATH=os.path.dirname(exe) + os.pathsep + os.environ.get("PATH", ""))   # fontmake beside it
    subprocess.run([exe, "builder", os.path.join(HERE, "sources", "config.yaml")], check=True, cwd=HERE, env=env)


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
    write_ufo(os.path.join(HERE, "sources", base + "-Regular.ufo"))
    direct = "--direct" in sys.argv
    out = os.path.join(HERE, "build", "direct") if direct else os.path.join(HERE, "fonts")
    otf = os.path.join(out, "otf", base + "-Regular.otf")
    ttf = os.path.join(out, "ttf", base + "-Regular.ttf")
    woff2 = os.path.join(out, "webfonts", base + "-Regular.woff2")
    if direct:
        # straight from fontTools, without Google's builder (quick, for comparison)
        for d in ("otf", "ttf", "webfonts"):
            os.makedirs(os.path.join(out, d), exist_ok=True)
        build_otf(otf)
        build_ttf(ttf)
        f = TTFont(ttf)
        f.flavor = "woff2"
        f.save(woff2)
    else:
        gftools_build()
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
