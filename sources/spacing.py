"""Spacing and kerning, computed from the outlines and calibrated on the ON TOP image.

Sidebearings: a side's white is its sidebearing plus a share of the space its profile leaves
(its depth, capped). Every side gets the same white:

    sidebearing = BASE - SHARE * mean(min(depth(y), CAP))   over the cap height

BASE, SHARE and CAP are chosen so the four letters of the image space as they do there: a stem
side 72, the O's side 68, the T's 25 (the gaps O-N 140, T-O 93 and the word space measured in
the image).

Kerning, per pair:
- The horizontal gap between the two profiles is taken row by row over the cap height; the
  nearest share of the rows (NEAR) is what the eye reads as the gap. A pair whose near gap is
  wider than two stems' sidebearings closes CLOSE of the difference.
- A pair whose ink faces itself over a long stretch at less than the normal gap (a bar meeting a
  bar, the L's foot meeting a period) opens up towards the normal gap.
- Punctuation may tuck under an overhang only so far (PUNCT_CAP): a period under the F's arm
  reads as an E's foot, a hyphen over the L's foot as an L with a stroke.
- Whatever the profiles say, the two outlines, over their full height, never come nearer than
  MIN_DIST in two dimensions (a quote over the J's stub, the Q's tail under a parenthesis).
Only kerns of at least MIN_KERN are kept.
"""
import math

BASE, SHARE, CAP = 72, 0.18, 362
REF = 2 * BASE
NEAR, CLOSE, MIN_KERN = 0.4, 0.55, 16
OPEN_SHARE, OPEN_BELOW, KEEP_SHARE = 0.25, 20, 0.2
STEP = 5
ZONE = (0, 700)
MIN_DIST, MIN_DIST_PUNCT = 70, 100

LOW = {"period", "comma", "quotesinglbase", "quotedblbase", "ellipsis"}
MIDDLE = {"hyphen", "endash", "emdash", "periodcentered", "bullet"}
HIGH = {"quoteright", "quoteleft", "quotedblright", "quotedblleft", "quotesingle", "quotedbl", "degree",
        "ordfeminine", "ordmasculine", "trademark"}
DOTS = {"colon", "semicolon"}
PUNCT_CAP = [(LOW, -130), (MIDDLE, -60), (HIGH, -250), (DOTS, -60)]
PUNCT = LOW | MIDDLE | HIGH | DOTS


def _crossings(contours, y):
    xs = []
    for c in contours:
        n = len(c)
        for i in range(n):
            (x0, y0), (x1, y1) = c[i], c[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return xs


def profile(contours, zone=ZONE, step=STEP):
    """Per row: (leftmost ink x, rightmost ink x) or None."""
    rows = []
    y = zone[0] + step / 2
    while y < zone[1]:
        xs = _crossings(contours, y)
        rows.append((min(xs), max(xs)) if xs else None)
        y += step
    return rows


def sidebearings(contours, xmin, xmax):
    rows = profile(contours)
    dl = [CAP if r is None else min(CAP, r[0] - xmin) for r in rows]
    dr = [CAP if r is None else min(CAP, xmax - r[1]) for r in rows]
    return BASE - SHARE * sum(dl) / len(dl), BASE - SHARE * sum(dr) / len(dr)


def depths(contours, xmin, xmax):
    rows = profile(contours)
    return ([math.inf if r is None else r[0] - xmin for r in rows],
            [math.inf if r is None else xmax - r[1] for r in rows])


def profile_kern(right_depth_l, rsb_l, left_depth_r, lsb_r, punct=False, may_open=False):
    """The kern the profiles ask for (before the punctuation caps and the 2-D check). Only pairs
    whose ink ends face each other (punctuation, figures: may_open) are ever opened; a letter's
    foot facing the next letter's stem is not."""
    gaps = [rsb_l + a + lsb_r + b for a, b in zip(right_depth_l, left_depth_r)]
    finite = sorted(g for g in gaps if g != math.inf)
    if not finite:
        return 0
    tight = [g for g in finite if g < REF - OPEN_BELOW]
    if may_open and len(tight) >= OPEN_SHARE * len(finite):
        # bars facing bars: open towards the normal gap (fully for punctuation)
        k = (REF - sum(tight) / len(tight)) * (1.0 if punct else 0.6)
        return k
    # Where a long stretch already stands at the normal gap (two bars at one height, as in 7 1),
    # closing up would run them into one bar.
    if sum(1 for g in finite if g <= REF + 10) >= KEEP_SHARE * len(finite):
        return 0
    k = max(1, int(len(finite) * NEAR))
    near = finite[:k]
    near_gap = sum(near) / len(near)
    if near_gap <= REF:
        return 0
    return CLOSE * (REF - near_gap)


# A mark over the J's stub reads as part of the J: quotes may come only so near it.
J_CAP = -120


def cap_for(a, b):
    lo = -10_000
    for group, cap in PUNCT_CAP:
        if a in group or b in group:
            lo = max(lo, cap)
    if ("J" in (a, b)) and (a in HIGH or b in HIGH):
        lo = max(lo, J_CAP)
    return lo


# Two letters whose bars face each other at one height over a long stretch (T T, F T) run into
# one bar at small sizes: open them to BAR_GAP. Letters whose corners only touch at a point
# (Y Y at the cap height) are opened until they stand POINT_DIST apart.
BAR_GAP, BAR_SHARE, BAR_BELOW = 95, 0.2, 75
POINT_DIST, POINT_BELOW = 60, 50


def bar_open(right_depth_l, rsb_l, left_depth_r, lsb_r):
    gaps = [rsb_l + a + lsb_r + b for a, b in zip(right_depth_l, left_depth_r)]
    finite = [g for g in gaps if g != math.inf]
    tight = [g for g in finite if g < BAR_BELOW]
    if finite and len(tight) >= BAR_SHARE * len(finite):
        return BAR_GAP - sum(tight) / len(tight)
    return 0


def round5(k):
    k = int(round(k / 5.0) * 5)
    return k if abs(k) >= MIN_KERN else 0
