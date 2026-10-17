"""Every glyph of the typeface, drawn from the rules measured in the ON TOP image.

O, N, T and P are the image's own letters, taken from its measurements. Everything else is
designed in their logic; no outline comes from another font. The rules (docs/MEASUREMENTS.md):

- The letters behave like a monoline geometric face stretched 1.32 times in width: vertical
  strokes 264, horizontal bars 196 (the stretch of a 200 stroke is 264).
- Round letters have big superelliptic outer corners (234 wide, 177 tall); their counters
  small ones (54 x 48). Straight letters and every stroke end are square.
- Diagonals keep the N's weight: the stroke is 214 thick before the stretch at the N's angle,
  and between a vertical and a horizontal stroke at other angles (diag_h).
- Letters with three horizontal storeys (B E S 2 3 5 6 8 9 ẞ & $) have three equal bars of 172 so
  their counters (92) stay open at small sizes.
- Every rounding is the O's own corner (@lrkqz, 2026-10-17); only the P's and R's bowl keep the
  corner measured on the logo's P.

Units: 1000 to the em, cap height 700, baseline 0. Each builder returns a pathops.Path with its
ink starting at x = 0 (spacing is added in spacing.py).
"""
import math
from geometry import (rect, poly, band, union, minus, clip, mirror_x, mirror_y, rotate180, rotate90, translate,
                      line_through, scale)

CH = 700

# --- measured in his image (px x 700 / 163.57) ------------------------------------------------
V = 264        # straight vertical stem (N 262/269, T 266, P 260)
VR = 254       # vertical side of a round (O 256, P's bowl 250)
OT = 195       # top bar (T 195, O 195, P 196)
OB = 197       # bottom bar (O 197)
HM = 188       # middle bar (P's bowl 188)
BIG = (234, 177, 0.605)   # outer corner of a full-height round (O, fitted rms 0.1 px)
BOWL = (212, 172, 0.63)   # outer corner of a bowl (P)
CNT = (54, 48, 0.55)      # counter corner (O)
CNTB = (67, 59, 0.66)     # counter corner in a bowl (P)
STRETCH = 1.32

# --- derived -----------------------------------------------------------------------------------
H3 = M3 = 172                          # the three equal bars of three-storey letters
Y_B1, Y_M0, Y_M1, Y_T0 = 172, 264, 436, 528   # their storeys: counters 92 each
MID = BIG                              # half-height bowls round with the O's own corner
CNT3 = (54, 46, 0.55)                  # the O's counter corner, as tall as a 92 counter allows: its two curves meet


def round_corner(x, y, sx, sy, corner=None):
    """The sliver to subtract from a square corner at (x, y) to round it with `corner` (default the
    O's). sx/sy point from the corner into the shape (+1 right/up, -1 left/down)."""
    corner = corner or BIG
    rx, ry = corner[0], corner[1]
    big = 4000
    x0, x1 = sorted((x, x + sx * big))
    y0, y1 = sorted((y, y + sy * big))
    tl = corner if (sx > 0 and sy < 0) else None
    tr = corner if (sx < 0 and sy < 0) else None
    br = corner if (sx < 0 and sy > 0) else None
    bl = corner if (sx > 0 and sy > 0) else None
    shape = rect(x0, y0, x1, y1, tl, tr, br, bl)
    bx0, bx1 = sorted((x, x + sx * rx))
    by0, by1 = sorted((y, y + sy * ry))
    return minus(rect(bx0, by0, bx1, by1), shape)


def diag_h(m):
    """Horizontal thickness of a diagonal stroke of slope m (dx/dy, either sign).

    Undo the stretch, give the stroke its weight at that angle, stretch again. The weight is 200
    upright, 195 flat, and 214 at the N's angle (42.9 deg before the stretch), as measured."""
    mu = abs(m) / STRETCH
    th = math.atan(mu)
    t = 200 * math.cos(th) ** 2 + 195 * math.sin(th) ** 2 + 16.24 * math.sin(2 * th)
    return STRETCH * t * math.sqrt(1 + mu * mu)


def solve_slope(f, lo=0.05, hi=6.0):
    """Root of f(m) = 0 by bisection (f increasing or decreasing, one root in range)."""
    flo = f(lo)
    for _ in range(80):
        mid = (lo + hi) / 2
        if (f(mid) > 0) == (flo > 0):
            lo, flo = mid, f(mid)
        else:
            hi = mid
    return (lo + hi) / 2


G = {}          # name -> builder
UNI = {}        # name -> list of code points
ALT = {}        # name -> (base name, feature tag, label)


def glyph(name, *codes):
    def deco(fn):
        G[name] = fn
        UNI[name] = list(codes)
        return fn
    return deco


def alt(name, base, tag, label):
    def deco(fn):
        G[name] = fn
        ALT[name] = (base, tag, label)
        return fn
    return deco


# =============================================================================================
# The image's own letters
# =============================================================================================

@glyph("O", ord("O"))
def O(W=1333):
    return minus(rect(0, 0, W, CH, BIG, BIG, BIG, BIG),
                 rect(256, OB, W - 256, CH - OT, CNT, CNT, CNT, CNT))


@glyph("N", ord("N"))
def N():
    # As measured, including its small asymmetries: left stem 262, right 268, the diagonal's top
    # end at 404, its foot at 876, the crotches 193 below the top and 183 above the base.
    return union(rect(0, 0, 262, CH), rect(1042, 0, 1310, CH),
                 poly((27, CH), (404, CH), (1267, 0), (876, 0)))


@glyph("T", ord("T"))
def T():
    return union(rect(0, CH - OT, 1276, CH), rect(508, 0, 774, CH - OT + 1))


def p_bowl(W=1206, stem=260, side=250):
    return union(rect(0, 0, stem, CH), rect(0, 157, W, CH, None, BOWL, BOWL, None))


def p_counter(W=1206, stem=260, side=250):
    return rect(stem, 345, W - side, CH - OT, None, CNTB, CNTB, None)


@glyph("P", ord("P"))
def P():
    return minus(p_bowl(), p_counter())


# =============================================================================================
# Capitals
# =============================================================================================

def a_shape(W=1420, f=340, bar=(112, 300)):
    a = (W - f) / 2
    m = a / CH
    h = diag_h(m)
    outer = poly((0, 0), (W, 0), (W - a, CH), (a, CH))
    y_apex = (W - 2 * h) / (2 * m)
    inner = poly((h, 0), (W - h, 0), (W / 2, y_apex))
    if bar:
        inner = minus(inner, rect(-10, bar[0], W + 10, bar[1]))
    return minus(outer, inner)


@glyph("A", ord("A"))
def A():
    # The pointed A (@lrkqz, 2026-10-17: "spitzes A rein, kein rundes A als standard").
    return a_shape()


@alt("A.ss01", "A", "ss01", "A rund")
def A_round(W=1333):
    # The O's upper half on two legs, its crossbar and counter those of the P's bowl.
    return minus(rect(0, 0, W, CH, BIG, BIG, None, None),
                 rect(V, 345, W - V, CH - OT, CNTB, CNTB, None, None),
                 rect(V, -10, W - V, 157))


@glyph("B", ord("B"))
def B(W=1180, overlap=120):
    # Two equal bowls, each with the O's corners on the right, curving in at the waist as in his
    # proposal of 2026-10-17, but neither bowl wider than the other ("bauch sollte nicht glatt sein,
    # sollte genau so gecurved sein, wie im beispiel ... beide gleich"). The bowls overlap over
    # `overlap` around the middle; where their corners cross they make the waist.
    upper = rect(0, CH / 2 - overlap / 2, W, CH, None, BIG, BIG, None)
    lower = rect(0, 0, W, CH / 2 + overlap / 2, None, BIG, BIG, None)
    return minus(union(upper, lower, rect(0, Y_M0, W - 300, Y_M1)),
                 rect(V, Y_M1, W - VR, Y_T0, None, CNT3, CNT3, None),
                 rect(V, Y_B1, W - VR, Y_M0, None, CNT3, CNT3, None))


def c_ring(W, side=256, br=True, tr_in=True):
    return minus(rect(0, 0, W, CH, BIG, BIG, BIG if br else None, BIG),
                 rect(side, OB, W - side, CH - OT, CNT, CNT if tr_in else None, CNT if br else None, CNT))


C_STUB = 90     # how far the C's ends turn in past the counter's edge (his sketch, 2026-10-17)


@glyph("C", ord("C"))
def C(W=1270):
    # The O opened on the right; its ends turn in and stop square.
    return minus(c_ring(W), rect(W - 257, OB + C_STUB, W + 10, CH - OT - C_STUB))


@glyph("D", ord("D"))
def D(W=1300):
    return minus(rect(0, 0, W, CH, None, BIG, BIG, None),
                 rect(V, OB, W - VR, CH - OT, None, CNT, CNT, None))


@glyph("E", ord("E"))
def E(W=1120):
    # Round on the left like the C (@lrkqz, 2026-10-17: "rundes E, aber mit dem spacing zwischen
    # den strichen wie beim eckigen"): the square E's three bars and counters.
    return minus(rect(0, 0, W, CH, BIG, None, None, BIG),
                 rect(VR, Y_M1, W + 10, Y_T0, CNT3, None, None, None),
                 rect(VR, Y_B1, W + 10, Y_M0, None, None, None, CNT3))


@alt("E.ss04", "E", "ss04", "E eckig")
def E_square(W=1120):
    return union(rect(0, 0, V, CH), rect(0, 0, W, Y_B1), rect(0, Y_M0, W, Y_M1), rect(0, Y_T0, W, CH))


@glyph("F", ord("F"))
def F(W=1100):
    # The round A without its right side (@lrkqz, 2026-10-17): its corner, its top bar, its
    # crossbar at the P's height; both bars as thick as the A's and as long as each other.
    return minus(rect(0, 0, W, CH, BIG, None, None, None),
                 rect(V, 345, W + 10, CH - OT, CNTB, None, None, None),
                 rect(V, -10, W + 10, 157))


def g_shape(W=1310, rise=360, spur=200, spur_t=100):
    """The O opened at the upper right: the top ends square after its round corner without turning
    down; the foot rises from the round lower corner at the stroke's own width, and a short spur
    points in from it. @lrkqz, 2026-10-17: first "oben ... straight, wie beim C, nur, dass es nicht
    runter geht ... unten ist dafür rund, aber kein komisches element", then a foot as short as the
    J's; shown that both read as a C at 16 to 24 px ("ERLEDICT"), he chose the spur."""
    out = minus(c_ring(W, tr_in=False), rect(W - 257, rise, W + 10, CH - OT))
    return union(out, rect(W - 256 - spur, rise - spur_t, W - 255, rise))


@glyph("G", ord("G"))
def G_():
    return g_shape()


@glyph("H", ord("H"))
def H(W=1300):
    y0 = (CH - HM) / 2
    return union(rect(0, 0, V, CH), rect(W - V, 0, W, CH), rect(0, y0, W, y0 + HM))


@glyph("I", ord("I"))
def I():
    return rect(0, 0, V, CH)


@glyph("J", ord("J"))
def J(W=1150, stub=315):
    return minus(union(rect(0, 0, W, stub, None, None, BIG, BIG), rect(W - V, 0, W, CH, None, None, BIG, None)),
                 rect(VR, OB, W - V, stub + 10, None, None, CNT, CNT))


@glyph("K", ord("K"))
def K(W=1250, junction=150):
    # Arm and leg meet the stem itself at its middle (no bar: "Das erst K war gut, nur der quere
    # balken in der mitte war schlecht"), stretched until the K is as wide as O, N and P ("gleiche
    # breite durch das arme strecken, wie O, N, P"). The point where they meet sits in the stem, so
    # they join it over `junction`; their ends are cut level, as the N's diagonal ends.
    def width(m):
        return V - junction * m / 2 + m * CH / 2 + diag_h(m)
    m = solve_slope(lambda m: width(m) - W, 0.5, 4)
    h = diag_h(m)
    x_tip = V - junction * m / 2
    a_l = x_tip - m * CH / 2
    arm = clip(band(m, a_l, a_l + h, CH / 2, CH), rect(0, CH / 2, 5000, CH))
    return union(rect(0, 0, V, CH), arm, mirror_y(arm, CH / 2))


@glyph("L", ord("L"))
def L(W=1120):
    return union(rect(0, 0, V, CH), rect(0, 0, W, OB))


@glyph("M", ord("M"))
def M(W=1500, foot=200, crotch=188):
    # The N's diagonal twice, meeting in a flat foot on the baseline.
    m = (W / 2 - foot / 2 - V) / (CH - crotch)
    h = diag_h(m)
    x_t = h + V - crotch * m
    left = band(-m, line_through(V, CH - crotch, -m), line_through(x_t, CH, -m), 0, CH)
    left = clip(left, rect(0, 0, W / 2, CH))
    half = union(rect(0, 0, V, CH), left)
    return union(half, mirror_x(half, W / 2))


@glyph("Q", ord("Q"))
def Q(W=1333):
    # The O with a tail across its lower right corner, at the N's angle.
    m = -1.2246
    h = diag_h(m) * 0.8
    x_c, y_c = W - 210, 70           # a point on the tail's centre line
    a = line_through(x_c, y_c, m)
    tail = band(m, a - h / 2, a + h / 2, -60, 290)
    ring = minus(rect(0, 0, W, CH, BIG, BIG, BIG, BIG), rect(256, OB, W - 256, CH - OT, CNT, CNT, None, CNT))
    return union(ring, tail)


@glyph("R", ord("R"))
def R(W=1250):
    m = -1.2246
    h = diag_h(m)
    leg = band(m, W - h, W, 0, 345)
    return union(minus(p_bowl(), p_counter()), clip(leg, rect(0, 0, W, CH)))


@alt("R.ss02", "R", "ss02", "R langes Bein")
def R_long(W=1250):
    # The leg leaves the bowl beside the stem and runs to the bottom right corner.
    y = 345
    m = -solve_slope(lambda m: (W - diag_h(m) - m * y) - (260 + 40))
    h = diag_h(m)
    leg = band(m, W - h, W, 0, y)
    return union(minus(p_bowl(), p_counter()), clip(leg, rect(260, 0, W, CH)))


def s_shape(W=1260, round_ends=False):
    c = CNT3
    out = poly((0, 0), (W, 0, MID), (W, Y_M1, MID), (VR, Y_M1, c), (VR, Y_T0, c), (W, Y_T0),
               (W, CH), (0, CH, MID), (0, Y_M0, MID), (W - VR, Y_M0, c), (W - VR, Y_B1, c), (0, Y_B1))
    if round_ends:
        # The O's own corner at both ends, cut where the 172 bar ends (it reaches 177).
        out = minus(out, round_corner(W, CH, -1, -1), round_corner(0, 0, 1, 1))
    return out


@glyph("S", ord("S"))
def S():
    # Round ends (@lrkqz, 2026-10-17: "S runde Ecken!").
    return s_shape(round_ends=True)


@alt("S.ss03", "S", "ss03", "S gerade Enden")
def S_square():
    return s_shape()


@glyph("U", ord("U"))
def U(W=1300):
    return minus(rect(0, 0, W, CH, None, None, BIG, BIG),
                 rect(256, OB, W - 256, CH + 10, None, None, CNT, CNT))


def v_shape(W=1420, f=300):
    a = (W - f) / 2
    m = a / CH
    h = diag_h(m)
    outer = poly((a, 0), (W - a, 0), (W, CH), (0, CH))
    y_apex = CH - (W - 2 * h) / (2 * m)
    inner = poly((h, CH), (W - h, CH), (W / 2, y_apex))
    return minus(outer, inner)


@glyph("V", ord("V"))
def V_():
    return v_shape()


@glyph("W", ord("W"))
def W_(W=1880):
    # Feet and middle apex as wide as the stroke itself: then the strokes' edges meet them
    # without a step (W = 4 c + h with c = 700 m).
    m = solve_slope(lambda m: 2800 * m + diag_h(m) - W, 0.1, 2)
    h = diag_h(m)
    f = h
    c = CH * m
    s1 = band(-m, line_through(0, CH, -m), line_through(h, CH, -m), 0, CH)
    s2 = band(m, line_through(c + f - h, 0, m), line_through(c + f, 0, m), 0, CH)
    left = union(s1, s2)
    shape = union(left, mirror_x(left, W / 2))
    sil = poly((0, CH), (c, 0), (c + f, 0), (W / 2, 0.01), (W - c - f, 0), (W - c, 0), (W, CH))
    return clip(shape, union(sil, rect(c, 0, W - c, CH)))


@glyph("X", ord("X"))
def X(W=1360):
    m = solve_slope(lambda m: W - diag_h(m) - m * CH)
    h = diag_h(m)
    s = band(-m, line_through(0, CH, -m), line_through(h, CH, -m), 0, CH)
    return clip(union(s, mirror_x(s, W / 2)), rect(0, 0, W, CH))


@glyph("Y", ord("Y"))
def Y(W=1340, join=300):
    m = (W / 2 - V / 2) / (CH - join)
    h = diag_h(m)
    arm = band(-m, line_through(0, CH, -m), line_through(h, CH, -m), join - 200, CH)
    arm = clip(arm, rect(0, 0, W / 2, CH))
    stem = rect(W / 2 - V / 2, 0, W / 2 + V / 2, join + 10)
    half = union(arm, stem)
    return union(half, mirror_x(half, W / 2))


@glyph("Z", ord("Z"))
def Z(W=1220):
    # The diagonal runs from the top bar's lower right corner to the bottom bar's upper left one.
    m = solve_slope(lambda m: (W - (CH - OT - OB) * m) - diag_h(m), 0.3, 5)
    a_r = line_through(W, CH - OT, m)
    a_l = line_through(0, OB, m)
    diag = band(m, a_l, a_r, 0, CH)
    return union(rect(0, CH - OT, W, CH), rect(0, 0, W, OB), clip(diag, rect(0, 0, W, CH)))


# =============================================================================================
# Umlauts
# =============================================================================================

DOT_W, DOT_H, DOT_GAP, DOT_SPREAD = 190, 150, 100, 340


def dots(cx, W=None):
    y0 = CH + DOT_GAP
    return union(rect(cx - DOT_SPREAD / 2 - DOT_W / 2, y0, cx - DOT_SPREAD / 2 + DOT_W / 2, y0 + DOT_H),
                 rect(cx + DOT_SPREAD / 2 - DOT_W / 2, y0, cx + DOT_SPREAD / 2 + DOT_W / 2, y0 + DOT_H))


@glyph("Adieresis", 0xC4)
def Adieresis():
    return union(A(), dots(1420 / 2))


@alt("Adieresis.ss01", "Adieresis", "ss01", "A rund")
def Adieresis_round():
    return union(A_round(), dots(1333 / 2))


@glyph("Odieresis", 0xD6)
def Odieresis():
    return union(O(), dots(1333 / 2))


@glyph("Udieresis", 0xDC)
def Udieresis():
    return union(U(), dots(1300 / 2))


# =============================================================================================
# Figures
# =============================================================================================

@glyph("zero", ord("0"))
def zero(W=1000):
    # The O's corners on a narrower body, so 0 and O stay apart.
    return minus(rect(0, 0, W, CH, MID, MID, MID, MID), rect(256, OB, W - 256, CH - OT, CNT, CNT, CNT, CNT))


@glyph("one", ord("1"))
def one(W=564):
    return union(rect(W - V, 0, W, CH), rect(0, CH - OT, W, CH))


@glyph("two", ord("2"))
def two(W=1180):
    return poly((0, 0), (W, 0), (W, Y_B1), (VR, Y_B1, CNT3), (VR, Y_M0, CNT3), (W, Y_M0, MID), (W, CH, MID),
                (0, CH), (0, Y_T0), (W - VR, Y_T0, CNT3), (W - VR, Y_M1, CNT3), (0, Y_M1, MID))


@glyph("three", ord("3"))
def three(W=1180, x_m=250):
    return poly((0, 0), (W, 0, MID), (W, CH, MID), (0, CH), (0, Y_T0), (W - VR, Y_T0, CNT3),
                (W - VR, Y_M1, CNT3), (x_m, Y_M1), (x_m, Y_M0), (W - VR, Y_M0, CNT3), (W - VR, Y_B1, CNT3), (0, Y_B1))


@glyph("four", ord("4"))
def four(W=1200, stem_in=150, bar=(170, 358)):
    xs = W - stem_in - V
    return union(rect(0, bar[0], V, CH), rect(0, bar[0], W, bar[1]), rect(xs, 0, xs + V, CH))


@glyph("five", ord("5"))
def five(W=1180, flag=1030):
    # The S's storeys, but square at the top left and its flag stopping short of the bowl below,
    # so 5 and S stay apart.
    return poly((0, 0), (W, 0, MID), (W, Y_M1, MID), (VR, Y_M1, CNT3), (VR, Y_T0, CNT3), (flag, Y_T0),
                (flag, CH), (0, CH), (0, Y_M0), (W - VR, Y_M0, CNT3), (W - VR, Y_B1, CNT3), (0, Y_B1))


@glyph("six", ord("6"))
def six(W=1180):
    return minus(poly((0, 0, MID), (W, 0, MID), (W, Y_M1, MID), (VR, Y_M1, CNT3), (VR, Y_T0, CNT3), (W, Y_T0),
                      (W, CH), (0, CH, MID)),
                 rect(VR, Y_B1, W - VR, Y_M0, CNT3, CNT3, CNT3, CNT3))


@glyph("seven", ord("7"))
def seven(W=1150, m=0.75):
    # The diagonal leaves the bar's lower right corner, as the Z's does: no overhang (2026-10-17).
    h = diag_h(m)
    a_r = line_through(W, CH - OT, m)
    diag = band(m, a_r - h, a_r, 0, CH - OT + 1)
    return union(rect(0, CH - OT, W, CH), clip(diag, rect(0, 0, W, CH)))


@glyph("eight", ord("8"))
def eight(W=1180, overlap=120):
    # Two bowls with the O's corners on both sides; they overlap as the B's do, so the waist is
    # the B's on both sides.
    up_bot, lo_top = CH / 2 - overlap / 2, CH / 2 + overlap / 2
    return minus(union(rect(0, up_bot, W, CH, BIG, BIG, BIG, BIG), rect(0, 0, W, lo_top, BIG, BIG, BIG, BIG),
                       rect(300, Y_M0, W - 300, Y_M1)),
                 rect(VR, Y_M1, W - VR, Y_T0, CNT3, CNT3, CNT3, CNT3),
                 rect(VR, Y_B1, W - VR, Y_M0, CNT3, CNT3, CNT3, CNT3))


@glyph("nine", ord("9"))
def nine(W=1180):
    return rotate180(six(W), W / 2, CH / 2)


# =============================================================================================
# Punctuation and signs
# =============================================================================================

PD_W, PD_H = 264, 196          # the period: a square before the stretch


@glyph("space", 0x20, 0xA0)
def space():
    return None


@glyph("period", ord("."))
def period():
    return rect(0, 0, PD_W, PD_H)


COMMA_TAIL = 190


def comma_shape(y=0):
    # The period run on below the line, its right side cut back towards the left.
    return poly((0, y + PD_H), (PD_W, y + PD_H), (PD_W, y), (110, y - COMMA_TAIL), (0, y - COMMA_TAIL))


@glyph("comma", ord(","))
def comma():
    return comma_shape()


@glyph("colon", ord(":"))
def colon():
    # The dots stand where the O's bars are: on the baseline and under the cap height.
    return union(rect(0, 0, PD_W, PD_H), rect(0, CH - PD_H, PD_W, CH))


@glyph("semicolon", ord(";"))
def semicolon():
    return union(comma_shape(), rect(0, CH - PD_H, PD_W, CH))


@glyph("hyphen", ord("-"), 0x2010, 0x2011)
def hyphen():
    return rect(0, 350 - HM / 2, 560, 350 + HM / 2)


@glyph("endash", 0x2013)
def endash():
    return rect(0, 350 - HM / 2, 1000, 350 + HM / 2)


@glyph("emdash", 0x2014)
def emdash():
    return rect(0, 350 - HM / 2, 1640, 350 + HM / 2)


@glyph("periodcentered", 0xB7)
def periodcentered():
    return rect(0, 350 - PD_H / 2, PD_W, 350 + PD_H / 2)


@glyph("question", ord("?"))
def question(W=960, neck=330, low=Y_M1 - 150, bar=150):
    # The top of the 2 turned back on itself above the period: its counter that of the
    # three-storey letters (92), its hook bar 150 so 90 stay clear above the period.
    hook = poly((0, Y_T0), (0, CH), (W, CH, MID), (W, low, MID), (neck, low), (neck, low + bar),
                (W - VR, low + bar, CNT3), (W - VR, Y_T0, CNT3))
    return union(hook, rect(neck, 0, neck + PD_W, PD_H))


@glyph("exclam", ord("!"))
def exclam():
    # 90 clear above the period, as in the ?.
    return union(rect(0, PD_H + 90, V, CH), rect(0, 0, V, PD_H))


@glyph("quotesingle", ord("'"))
def quotesingle():
    return rect(0, 440, PD_W, CH)


@glyph("quotedbl", ord('"'))
def quotedbl():
    return union(rect(0, 440, PD_W, CH), rect(PD_W + 120, 440, 2 * PD_W + 120, CH))


def quote_shape():
    """The comma raised so its head sits on the cap height."""
    return comma_shape(CH - PD_H)


@glyph("quoteright", 0x2019)
def quoteright():
    return quote_shape()


@glyph("quoteleft", 0x2018)
def quoteleft():
    # The closing quote turned over: the head below, the tail rising up to the cap height.
    q = quote_shape()
    y0, y1 = CH - PD_H - COMMA_TAIL, CH
    return rotate180(q, PD_W / 2, (y0 + y1) / 2)


@glyph("quotesinglbase", 0x201A)
def quotesinglbase():
    return comma_shape()


@glyph("quotedblright", 0x201D)
def quotedblright():
    return union(quote_shape(), translate(quote_shape(), PD_W + 120))


@glyph("quotedblleft", 0x201C)
def quotedblleft():
    q = quoteleft()
    return union(q, translate(q, PD_W + 120))


@glyph("quotedblbase", 0x201E)
def quotedblbase():
    return union(comma_shape(), translate(comma_shape(), PD_W + 120))


@glyph("slash", ord("/"))
def slash(m=0.8):
    h = diag_h(m)
    s = band(m, 0, h, 0, CH)
    return s


def corner_inset_at(v, corner=None):
    """How far in from the corner's vertical side the curve of a round corner lies at height v
    (measured from the corner's horizontal edge)."""
    rx, ry, k = corner or BIG
    lo, hi = 0.0, 1.0
    for _ in range(60):
        t = (lo + hi) / 2
        y = 3 * (1 - t) * t * t * (ry - ry * k) + t ** 3 * ry
        lo, hi = (t, hi) if y < v else (lo, t)
    t = (lo + hi) / 2
    return (1 - t) ** 3 * rx + 3 * (1 - t) ** 2 * t * (rx - rx * k)


@glyph("ampersand", 0x26)
def ampersand(top_w=720):
    # The first & he saw, as he chose it again (2026-10-17: "Nimm das erste, aber ohne den
    # dreieckigen überhang auf der rechten schräge"): the 8's storeys, the upper loop smaller and
    # set in on a round shoulder, the lower bowl open on the right, and a leg at 0.9 of the N's
    # weight, one band of even width, whose right edge runs straight on from the loop's side.
    # The bowl's foot rounds with the O's corner and ends exactly on the leg's left edge, in a
    # point where the counter's floor meets it ("der untere balken sollte von der krümmung her
    # auf den queren balken mit der spitze enden"); below that point a notch parts foot and leg.
    m = -1.2246
    h = diag_h(m) * 0.9
    W = top_w - m * Y_M1                      # the leg's right edge leaves the loop's side at Y_M1
    leg_left_at = lambda y: W - h + m * y     # noqa: E731
    bowl_w = leg_left_at(Y_B1) + corner_inset_at(Y_B1)
    upper = minus(rect(80, Y_M0, top_w, CH, MID, MID, None, None),
                  rect(80 + VR, Y_M1, top_w - VR, Y_T0, CNT3, CNT3, CNT3, CNT3))
    lower = minus(rect(0, 0, bowl_w, Y_M1, MID, None, None, MID),
                  rect(VR, Y_B1, bowl_w + 10, Y_M0, CNT3, None, None, CNT3),
                  round_corner(bowl_w, 0, -1, 1))
    leg = clip(band(m, W - h, W, 0, Y_M1), rect(0, 0, W, Y_M1))
    return union(upper, lower, leg)


@glyph("numbersign", ord("#"))
def numbersign(W=1180):
    sv, bh = 230, 172
    return union(rect(240, 0, 240 + sv, CH), rect(W - 240 - sv, 0, W - 240, CH),
                 rect(0, 120, W, 120 + bh), rect(0, CH - 120 - bh, W, CH - 120))


@glyph("plus", ord("+"))
def plus(W=800):
    bar = HM
    st = 250
    return union(rect(0, 350 - bar / 2, W, 350 + bar / 2), rect(W / 2 - st / 2, 350 - W / 2 / STRETCH, W / 2 + st / 2, 350 + W / 2 / STRETCH))


PAREN = (300, 230, 0.6)
PAREN_IN = (90, 70, 0.6)


@glyph("parenleft", ord("("))
def parenleft(W=440, y0=-80, y1=780):
    # The O's left side, cut off: its corners are what make it a parenthesis and not a bracket.
    return minus(rect(0, y0, W, y1, PAREN, None, None, PAREN),
                 rect(220, y0 + 165, W + 10, y1 - 165, PAREN_IN, None, None, PAREN_IN))


@glyph("parenright", ord(")"))
def parenright():
    return mirror_x(parenleft(), 220)


SMALL_O = (110, 84, 0.62)
SMALL_C = (28, 24, 0.6)


def small_o(x0, y0, w=400, h=290, side=140, bar=100):
    return minus(rect(x0, y0, x0 + w, y0 + h, SMALL_O, SMALL_O, SMALL_O, SMALL_O),
                 rect(x0 + side, y0 + bar, x0 + w - side, y0 + h - bar, SMALL_C, SMALL_C, SMALL_C, SMALL_C))


@glyph("percent", ord("%"))
def percent(W=1300):
    # Two small zeros and the slash between them.
    m = (W - 300) / CH
    h = 240
    a = (W - h) / 2 - m * CH / 2
    sl = clip(band(m, a, a + h, 0, CH), rect(0, 0, W, CH))
    return union(small_o(0, CH - 290), small_o(W - 400, 0), sl)


@glyph("Euro", 0x20AC)
def Euro(W=1240, inset=180, bar=110, reach=200):
    # The C with two lighter bars through its back ("einfach kleinere striche"), each starting
    # where the C's round corner ends, so back, corner and bar run on without a neck; inside the
    # counter they reach in a little.
    c = translate(C(W - inset), inset)
    back = inset + 256
    lo, hi = BIG[1], CH - BIG[1]              # where the outer corners end on the C's back
    return union(c, rect(0, lo, back + reach, lo + bar), rect(0, hi - bar, back + reach, hi))


@glyph("at", ord("@"))
def at(W=1420, y0=-150):
    # A lighter O for the ring; inside it an a, square like the P's bowl, whose side runs down
    # into the ring's foot where the ring opens.
    side, bar = 160, 120
    ring = minus(rect(0, y0, W, CH, BIG, BIG, BIG, BIG),
                 rect(side, y0 + bar, W - side, CH - bar, CNT, CNT, CNT, CNT))
    a_l, a_r, a_t = 380, W - 330, 470
    stem_l = a_r - 200
    ring = minus(ring, rect(stem_l, y0 - 10, W + 10, y0 + bar + 1), rect(a_r, y0 - 10, W + 10, 120))
    bowl = minus(rect(a_l, 90, a_r, a_t, (120, 92, 0.62), None, None, (120, 92, 0.62)),
                 rect(a_l + 170, 90 + 115, stem_l, a_t - 115, SMALL_C, None, None, SMALL_C))
    foot = rect(stem_l, y0, a_r, a_t)
    return union(ring, bowl, foot)


# =============================================================================================
# More signs (counter-review 1: what a German interface will meet)
# =============================================================================================

@glyph("ellipsis", 0x2026)
def ellipsis(gap=144):
    return union(*(rect(i * (PD_W + gap), 0, i * (PD_W + gap) + PD_W, PD_H) for i in range(3)))


@glyph("bracketleft", ord("["))
def bracketleft(W=440, y0=-80, y1=780):
    # The parenthesis with square corners.
    return minus(rect(0, y0, W, y1), rect(220, y0 + 165, W + 10, y1 - 165))


@glyph("bracketright", ord("]"))
def bracketright():
    return mirror_x(bracketleft(), 220)


def chevron(half, weight=0.75, cy=CH / 2, m=1.2246):
    """A < pointing left: two arms at the N's angle, like the K's arm and leg, meeting in a point
    on the left; their ends cut level, as the N's diagonal ends on the cap height."""
    h = diag_h(m) * weight
    a = -m * cy                       # the outer edge x = a + m y runs through the point (0, cy)
    arm = clip(band(m, a, a + h, cy, cy + half), rect(0, cy, 5000, cy + half))
    return union(arm, mirror_y(arm, cy))


def chevron_w(half, weight=0.75, m=1.2246):
    return m * half + diag_h(m) * weight


LT_HALF, GUIL_HALF, GUIL_WEIGHT = 250, 190, 0.75


@glyph("less", ord("<"))
def less():
    return chevron(LT_HALF)


@glyph("greater", ord(">"))
def greater():
    return mirror_x(chevron(LT_HALF), chevron_w(LT_HALF) / 2)


@glyph("guilsinglleft", 0x2039)
def guilsinglleft():
    return chevron(GUIL_HALF, GUIL_WEIGHT)


@glyph("guilsinglright", 0x203A)
def guilsinglright():
    return mirror_x(chevron(GUIL_HALF, GUIL_WEIGHT), chevron_w(GUIL_HALF, GUIL_WEIGHT) / 2)


@glyph("guillemotleft", 0xAB)
def guillemotleft():
    c = chevron(GUIL_HALF, GUIL_WEIGHT)
    return union(c, translate(c, diag_h(1.2246) * GUIL_WEIGHT + 130))


@glyph("guillemotright", 0xBB)
def guillemotright():
    c = guilsinglright()
    return union(c, translate(c, diag_h(1.2246) * GUIL_WEIGHT + 130))


@glyph("asterisk", ord("*"))
def asterisk(w=580, h=460, t=110):
    # An upright bar and two diagonals crossing, raised to the cap height, at the weight of the
    # Euro's bars (2026-10-17: "viel zu unkenntlich (dick), nimm da die strichstärke von den
    # € querstrichen"): the diagonals 110 across, the upright 110 stretched as every upright is.
    cy = CH - h / 2
    m = w / h
    up_w = t * STRETCH
    up = rect(w / 2 - up_w / 2, cy - h / 2, w / 2 + up_w / 2, cy + h / 2)
    d = t * math.sqrt(1 + m * m)              # 110 across the stroke
    a1 = line_through(w / 2, cy, m)
    a2 = line_through(w / 2, cy, -m)
    box = rect(0, cy - h / 2, w, cy + h / 2)
    return union(up, clip(band(m, a1 - d / 2, a1 + d / 2, cy - h, cy + h), box),
                 clip(band(-m, a2 - d / 2, a2 + d / 2, cy - h, cy + h), box))


@glyph("underscore", ord("_"))
def underscore(W=1000):
    return rect(0, -230, W, -230 + 172)


@glyph("equal", ord("="))
def equal(W=800, bar=172, gap=110):
    return union(rect(0, CH / 2 - gap / 2 - bar, W, CH / 2 - gap / 2), rect(0, CH / 2 + gap / 2, W, CH / 2 + gap / 2 + bar))


@glyph("bar", ord("|"))
def bar_(W=220):
    return rect(0, -80, W, 780)


@glyph("dollar", ord("$"))
def dollar(W=1180, t=230):
    # The S with its stroke standing out above and below.
    cx = W / 2
    return union(s_shape(W, round_ends=True), rect(cx - t / 2, -120, cx + t / 2, 1), rect(cx - t / 2, CH - 1, cx + t / 2, CH + 120))


@glyph("degree", 0xB0)
def degree():
    return small_o(0, CH - 290)


@glyph("multiply", 0xD7)
def multiply(w=520, h=440, t=110):
    # Two diagonals crossing in the middle of the box, from corner to corner, at the asterisk's
    # weight (2026-10-17: "das kleine sternchen (2 balken) ... auch auf die strichstärke vom
    # größeren sternchen bringen"): 110 across the stroke.
    cy = CH / 2
    m = solve_slope(lambda m: m * h + t * math.sqrt(1 + m * m) - w, 0.05, 4)
    hh = t * math.sqrt(1 + m * m)
    a = line_through(w / 2, cy, -m)
    s = band(-m, a - hh / 2, a + hh / 2, cy - h, cy + h)
    return clip(union(s, mirror_x(s, w / 2)), rect(0, cy - h / 2, w, cy + h / 2))


@glyph("uni1E9E", 0x1E9E)
def germandbls_cap(W=1180, top=980, gap=130):
    # The capital sharp s: a stem, a flat top, and from its end a diagonal dropping to the left
    # into the waist of the 3's lower bowl, whose foot stops short of the stem. The upper half is
    # no bowl, so it is never a B.
    m = 1.0
    h = diag_h(m) * 0.85
    a_r = line_through(top, Y_T0, m)          # the diagonal leaves the top bar's lower right corner
    diag = clip(band(m, a_r - h, a_r, Y_M0, Y_T0 + 1), rect(V, Y_M0, top, CH))
    lower = poly((V + gap, 0), (W, 0, MID), (W, Y_M1, MID), (a_r - h + m * Y_M1, Y_M1), (a_r - h + m * Y_M0, Y_M0),
                 (W - VR, Y_M0, CNT3), (W - VR, Y_B1, CNT3), (V + gap, Y_B1))
    return union(rect(0, 0, V, CH), rect(0, Y_T0, top, CH), diag, lower)


@glyph(".notdef")
def notdef(W=600):
    return minus(rect(0, 0, W, CH), rect(60, 60, W - 60, CH - 60))


# =============================================================================================
# Accents (GF Latin Core)
# =============================================================================================
# Every accent is drawn once, in the place and the weight of the approved dieresis: its foot 100
# above the cap height (y 800), its strokes as heavy as the dots (190 upright, 150 flat: a dot is
# 0.72 of the letters' weight). The accents with two strokes and a counter (^ ˇ ˘ ˚ ~) rise to
# 200, so the counter stays open. The marks below hang from the baseline to the descender (-250).
# Small marks round with corners scaled to their size, as the small signs ( ) % ° do.
#
# The new designs are shown to @lrkqz as variants; VARIANTS holds them, VARIANT the one in the
# font (until he chooses, the first).

ACC_Y, ACC_H, ACC_TALL = CH + DOT_GAP, DOT_H, 200
ACC_WEIGHT = DOT_W / V                 # 0.72: the dot against the stem
ACC_GAP = DOT_SPREAD - DOT_W           # 150: the white between the two dots

VARIANTS = {}       # design -> {key: (label, builder)}
VARIANT = {}        # design -> key of the variant in the font
DESIGN_NAMES = {}   # design -> its German name on the review page


def variant(design, key, label):
    def deco(fn):
        VARIANTS.setdefault(design, {})[key] = (label, fn)
        VARIANT.setdefault(design, key)
        return fn
    return deco


def drawn(design):
    return VARIANTS[design][VARIANT[design]][1]()


def mid_x(p):
    b = p.bounds
    return (b[0] + b[2]) / 2


def centred(p, cx):
    return translate(p, cx - mid_x(p))


# --- acute, grave, double acute ------------------------------------------------------------

ACUTE_SLOPE = {"1": ("wie die Schräge des N", 1.2246), "2": ("steil", 0.7), "3": ("flach", 2.0)}
DESIGN_NAMES["acute"] = "Akut, Gravis, Doppelakut"


def acute_at(m):
    """A stroke leaning right at slope m, its ends cut level as the N's diagonal ends."""
    th = diag_h(m) * ACC_WEIGHT
    return translate(band(m, 0, th, ACC_Y, ACC_Y + ACC_H), -m * ACC_Y)


for _k, (_label, _m) in ACUTE_SLOPE.items():
    variant("acute", _k, _label)(lambda m=_m: acute_at(m))


def acute_mark():
    return drawn("acute")


def grave_mark():
    a = drawn("acute")
    return mirror_x(a, mid_x(a))


def hungarumlaut_mark():
    m = ACUTE_SLOPE[VARIANT["acute"]][1]
    a = acute_at(m)
    return union(a, translate(a, diag_h(m) * ACC_WEIGHT + ACC_GAP))


# --- circumflex and caron ----------------------------------------------------------------------

DESIGN_NAMES["circumflex"] = "Zirkumflex und Hatschek"


def roof(W, H, vt, f=0, y0=ACC_Y):
    """A ^: two strokes vt thick measured upright, meeting in a point (f = 0) or a flat top f wide;
    the counter below them a triangle."""
    m = (W / 2 - f / 2) / H
    th = vt * m
    outer = poly((0, y0), (W, y0), (W / 2 + f / 2, y0 + H), (W / 2 - f / 2, y0 + H))
    y_in = (W / 2 - th) / m
    return minus(outer, poly((th, y0 - 1), (W - th, y0 - 1), (W / 2, y0 + y_in)))


@variant("circumflex", "1", "spitz")
def circumflex_point():
    return roof(700, ACC_TALL, 125)


@variant("circumflex", "2", "oben flach wie das A")
def circumflex_flat():
    return roof(720, ACC_TALL, 125, 200)


@variant("circumflex", "3", "flacher und breiter")
def circumflex_wide():
    return roof(820, 180, 115)


def circumflex_mark():
    return drawn("circumflex")


def caron_mark():
    c = drawn("circumflex")
    b = c.bounds
    return mirror_y(c, (b[1] + b[3]) / 2)


# --- tilde ---------------------------------------------------------------------------------------

DESIGN_NAMES["tilde"] = "Tilde"


def wave(W, H, tw, vt, k=0.6, corner=130, y0=ACC_Y):
    """An arch and then a cup sharing their middle stroke: a square wave with round corners
    (corner None: square). tw: the upright strokes, vt: the flat ones."""
    xm = W / 2 - tw / 2
    cr = (min(corner, (xm + tw) / 2), min(H, 110), k) if corner else None
    ci = (max(10, cr[0] - tw), max(10, cr[1] - vt), 0.55) if corner else None
    arch = minus(rect(0, y0, xm + tw, y0 + H, cr, cr, None, None), rect(tw, y0 - 10, xm, y0 + H - vt, ci, ci, None, None))
    cup = minus(rect(xm, y0, W, y0 + H, None, None, cr, cr), rect(xm + tw, y0 + vt, W - tw, y0 + H + 10, None, None, ci, ci))
    return union(arch, cup)


@variant("tilde", "1", "Welle, runde Ecken")
def tilde_round():
    return wave(620, 180, 180, 85)


@variant("tilde", "2", "Welle, weicher")
def tilde_soft():
    return wave(660, 170, 170, 80, k=0.5, corner=160)


@variant("tilde", "3", "Welle, eckig")
def tilde_square():
    return wave(620, 170, 170, 80, corner=None)


def tilde_mark():
    return drawn("tilde")


# --- macron, dot ---------------------------------------------------------------------------------

DESIGN_NAMES["macron"] = "Makron (Strich)"
MACRON_W = 2 * DOT_W / 2 + DOT_SPREAD   # 530: as wide as the dieresis


@variant("macron", "1", "so hoch wie die Punkte")
def macron_dot():
    return rect(0, ACC_Y, MACRON_W, ACC_Y + ACC_H)


@variant("macron", "2", "leichter")
def macron_light():
    return rect(0, ACC_Y, MACRON_W, ACC_Y + 120)


def macron_mark():
    return drawn("macron")


def dot_mark():
    return rect(0, ACC_Y, DOT_W, ACC_Y + DOT_H)


def dieresis_mark():
    return dots(DOT_SPREAD / 2 + DOT_W / 2)


# --- breve ---------------------------------------------------------------------------------------

DESIGN_NAMES["breve"] = "Breve (Bogen)"


def cup_mark(W, H, side, bar, y0=ACC_Y):
    """The O's lower half, open at the top; its corners the O's, scaled to the height."""
    s = H / 300
    c = (234 * s, 177 * s, 0.605)
    ci = (max(10, c[0] - side), max(10, c[1] - bar), 0.55)
    return minus(rect(0, y0, W, y0 + H, None, None, c, c), rect(side, y0 + bar, W - side, y0 + H + 10, None, None, ci, ci))


@variant("breve", "1", "tief")
def breve_deep():
    return cup_mark(560, 180, 170, 80)


@variant("breve", "2", "flach")
def breve_flat():
    return cup_mark(560, 150, 160, 70)


def breve_mark():
    return drawn("breve")


# --- ring ----------------------------------------------------------------------------------------

DESIGN_NAMES["ring"] = "Ring"


def degree_scaled(s, y0=ACC_Y):
    """The approved degree sign, scaled: its corners and proportions kept."""
    w, h, side, bar = 400 * s, 290 * s, 140 * s, 100 * s
    co = (SMALL_O[0] * s, SMALL_O[1] * s, SMALL_O[2])
    ci = (max(6, SMALL_C[0] * s), max(6, SMALL_C[1] * s), SMALL_C[2])
    return minus(rect(0, y0, w, y0 + h, co, co, co, co), rect(side, y0 + bar, w - side, y0 + h - bar, ci, ci, ci, ci))


@variant("ring", "1", "das Gradzeichen, kleiner")
def ring_degree():
    return degree_scaled(ACC_WEIGHT)


@variant("ring", "2", "das Gradzeichen, größer")
def ring_large():
    return degree_scaled(0.86)


def ring_mark():
    return drawn("ring")


# --- marks below ---------------------------------------------------------------------------------

DESIGN_NAMES["cedilla"] = "Cedille (Ç Ş)"
DESC = -250


def hook_left(W=300, depth=-DESC, stem=170, bar=110):
    """A stem down from the letter, its foot turning left with the O's corner (scaled): the
    cedilla as a small J."""
    c = (min(W - 20, 234 * 0.7), min(depth, 177 * 0.7), 0.605)
    ci = (40, 34, 0.55)
    out = rect(-W + stem / 2, -depth, stem / 2, 0, None, None, c, None)
    return minus(out, rect(-W + stem / 2 - 10, -depth + bar, -stem / 2, 10, None, None, ci, None))


@variant("cedilla", "1", "Haken nach links")
def cedilla_hook():
    return hook_left()


@variant("cedilla", "2", "kleiner Bogen, offen nach links")
def cedilla_bowl(W=300, depth=-DESC, neck=50, neck_w=130, side=130, bar=72):
    # A short neck down from the letter, then a small bowl open on the left, its right corners
    # the O's scaled to the bowl's height.
    h = depth - neck
    s = h / CH
    c = (234 * s * 2, 177 * s * 2 * 0.5, 0.605)
    ci = (36, 28, 0.55)                      # its two curves meet in the 56 counter
    x0 = -W / 2 + 20
    bowl = minus(rect(x0, -depth, x0 + W, -neck, None, c, c, None),
                 rect(x0 - 10, -depth + bar, x0 + W - side, -neck - bar, None, ci, ci, None))
    return union(bowl, rect(-neck_w / 2, -neck - 1, neck_w / 2, 0))


def comma_mark(s=ACC_WEIGHT, gap=60):
    """The approved comma at the size of the dots, below the line."""
    c = scale(comma_shape(), s)
    b = c.bounds
    return translate(c, -mid_x(c), -gap - b[3])


@variant("cedilla", "3", "Komma (wie bei Ș Ț)")
def cedilla_comma():
    return comma_mark()


def cedilla_mark():
    return drawn("cedilla")


DESIGN_NAMES["commaaccent"] = "Komma unten (Ș Ț Ģ Ķ Ļ Ņ)"


@variant("commaaccent", "1", "so groß wie die Punkte")
def commaaccent_dot():
    return comma_mark()


@variant("commaaccent", "2", "kleiner")
def commaaccent_small():
    return comma_mark(0.6, 50)


def commaaccent_mark():
    return drawn("commaaccent")


DESIGN_NAMES["ogonek"] = "Ogonek (Ą Ę Į Ų)"


@variant("ogonek", "1", "Haken nach rechts")
def ogonek_hook(W=310, depth=-DESC, stem=170, bar=110):
    # The cedilla's hook turned round: down from the letter's foot, turning right.
    return mirror_x(hook_left(W, depth, stem, bar), 0)


@variant("ogonek", "2", "Haken nach rechts, Ende hoch")
def ogonek_j(W=330, depth=-DESC, stem=160, bar=100, stub=80):
    out = mirror_x(hook_left(W, depth, stem, bar), 0)
    end = W - stem / 2
    return union(out, rect(end - 100, -depth + bar - 1, end, -depth + bar + stub))


def ogonek_mark():
    return drawn("ogonek")


def caronvertical_mark():
    """The caron beside a stem (Ľ): the approved closing quote at the size of the dots."""
    q = scale(quote_shape(), ACC_WEIGHT, ACC_WEIGHT, 0, CH)
    return translate(q, -q.bounds[0])


MARKS = {"grave": grave_mark, "acute": acute_mark, "circumflex": circumflex_mark, "tilde": tilde_mark,
         "macron": macron_mark, "breve": breve_mark, "dotaccent": dot_mark, "dieresis": dieresis_mark,
         "ring": ring_mark, "hungarumlaut": hungarumlaut_mark, "caron": caron_mark,
         "commaaccent": commaaccent_mark, "cedilla": cedilla_mark, "ogonek": ogonek_mark,
         "caronvertical": caronvertical_mark}
MARK_DESIGN = {"grave": "acute", "acute": "acute", "hungarumlaut": "acute", "circumflex": "circumflex",
               "caron": "circumflex", "tilde": "tilde", "macron": "macron", "breve": "breve", "ring": "ring",
               "cedilla": "cedilla", "commaaccent": "commaaccent", "ogonek": "ogonek"}
BELOW = {"cedilla", "commaaccent", "ogonek"}


# =============================================================================================
# The accented capitals (GF Latin Core)
# =============================================================================================
# A letter and its marks, from Unicode's decompositions. An accent stands over the middle of the
# letter's ink unless TOP_X says otherwise; a mark below hangs from the middle of its foot, the
# ogonek from the last stroke on the right (OGONEK_X: where its stem stands). As in Latvian, G K
# L N take a comma below for their cedilla; L takes the caron beside its stem. The letter keeps
# its spacing (build.py), so an accent wider than an I reaches into its sidebearings.

import unicodedata                   # noqa: E402
from fontTools import agl            # noqa: E402

COMBINING = {0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde", 0x304: "macron",
             0x306: "breve", 0x307: "dotaccent", 0x308: "dieresis", 0x30A: "ring", 0x30B: "hungarumlaut",
             0x30C: "caron", 0x326: "commaaccent", 0x327: "cedilla", 0x328: "ogonek"}
LATIN_CORE_ACCENTED = [
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC7, 0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xD1, 0xD2, 0xD3,
    0xD4, 0xD5, 0xD9, 0xDA, 0xDB, 0xDD, 0x100, 0x102, 0x104, 0x106, 0x10A, 0x10C, 0x10E, 0x112, 0x116, 0x118,
    0x11A, 0x11E, 0x120, 0x122, 0x12A, 0x12E, 0x130, 0x136, 0x139, 0x13B, 0x13D, 0x143, 0x145, 0x147, 0x150,
    0x154, 0x158, 0x15A, 0x15E, 0x160, 0x164, 0x16A, 0x16E, 0x170, 0x172, 0x174, 0x176, 0x178, 0x179, 0x17B,
    0x17D, 0x218, 0x21A, 0x1E80, 0x1E82, 0x1E84, 0x1EF2]
COMMA_FOR_CEDILLA = {"G", "K", "L", "N"}
TOP_X = {"L": V / 2 + 60}            # over the L's stem, not over the white beside it
OGONEK_X = {"A": 1420 - diag_h(540 / 700) / 2, "E": 1120 - 200, "I": V / 2, "U": 1300 - 128}
COMPOSITE = {}                        # name -> (base, [marks])
DEPENDS = {}                          # name -> the designs it shows


def glyph_name(code):
    return agl.UV2AGL.get(code) or f"uni{code:04X}"


def base_of(name):
    return COMPOSITE[name][0] if name in COMPOSITE else None


def compose(base, marks):
    p = G[base]()
    b = p.bounds
    out = [p]
    for mk in marks:
        m = MARKS[mk]()
        if mk == "caronvertical":
            out.append(translate(m, V + 70))
        elif mk == "ogonek":
            out.append(translate(m, OGONEK_X[base]))
        elif mk in BELOW:
            out.append(centred(m, mid_x(p)))
        else:
            out.append(centred(m, TOP_X.get(base, (b[0] + b[2]) / 2)))
    return union(*out)


def _register(code):
    ch = chr(code)
    parts = unicodedata.decomposition(ch).split()
    base = chr(int(parts[0], 16))
    marks = [COMBINING[int(x, 16)] for x in parts[1:]]
    if base in COMMA_FOR_CEDILLA and marks == ["cedilla"]:
        marks = ["commaaccent"]
    if base == "L" and marks == ["caron"]:
        marks = ["caronvertical"]
    name = glyph_name(code)
    COMPOSITE[name] = (base, marks)
    DEPENDS[name] = sorted({MARK_DESIGN[m] for m in marks if m in MARK_DESIGN})
    glyph(name, code)(lambda base=base, marks=marks: compose(base, marks))


for _code in LATIN_CORE_ACCENTED:
    _register(_code)


# =============================================================================================
# Letters with a stroke (Ø Đ Ð Ħ Ł)
# =============================================================================================
# The stroke is either the Euro's light bar (110) or the three-storey bar (172); the letter under
# it is the approved one and keeps its spacing.

DESIGN_NAMES["slashO"] = "Ø"
DESIGN_NAMES["barD"] = "Đ Ð"
DESIGN_NAMES["barH"] = "Ħ"
DESIGN_NAMES["slashL"] = "Ł"
LIGHT_BAR = 110


def slash_through(m, th, cx, cy, y0, y1):
    a = line_through(cx, cy, m)
    return band(m, a - th / 2, a + th / 2, y0, y1)


def o_outer(W=1333):
    return rect(0, 0, W, CH, BIG, BIG, BIG, BIG)


@variant("slashO", "1", "leichter Strich von Ecke zu Ecke")
def oslash_light(W=1333):
    m = (W - 2 * 120) / CH
    th = LIGHT_BAR * STRETCH * math.sqrt(1 + (m / STRETCH) ** 2)
    s = clip(slash_through(m, th, W / 2, CH / 2, -10, CH + 10), o_outer(W))
    return union(O(W), s)


@variant("slashO", "2", "wie der Schrägstrich, über das O hinaus")
def oslash_through(W=1333, over=70):
    m = 0.8
    th = diag_h(m) * 0.6
    s = slash_through(m, th, W / 2, CH / 2, -over, CH + over)
    return union(O(W), s)


@variant("slashO", "3", "Schräge des N, im O")
def oslash_n(W=1333):
    m = 1.2246
    th = diag_h(m) * 0.7
    s = clip(slash_through(m, th, W / 2, CH / 2, -10, CH + 10), o_outer(W))
    return union(O(W), s)


def d_bar(t, out=130, reach=200):
    return rect(-out, CH / 2 - t / 2, V + reach, CH / 2 + t / 2)


@variant("barD", "1", "leichter Balken wie beim €")
def dcroat_light():
    return union(D(), d_bar(LIGHT_BAR))


@variant("barD", "2", "Balken der dreistöckigen Buchstaben (172)")
def dcroat_bar():
    return union(D(), d_bar(H3))


@glyph("Dcroat", 0x110)
def Dcroat():
    return drawn("barD")


@glyph("Eth", 0xD0)
def Eth():
    return drawn("barD")


def h_bar(t, W=1300, out=100):
    y = (CH + (CH + HM) / 2) / 2           # midway between the crossbar's top and the cap height
    return rect(-out, y - t / 2, W + out, y + t / 2)


@variant("barH", "1", "leichter Balken wie beim €")
def hbar_light():
    return union(H(), h_bar(LIGHT_BAR))


@variant("barH", "2", "Balken der dreistöckigen Buchstaben (172)")
def hbar_bar():
    return union(H(), h_bar(H3))


@glyph("Hbar", 0x126)
def Hbar():
    return drawn("barH")


def l_slash(t_upright, m=0.8, cy=420, hy=190):
    # A stroke rising through the stem, its ends cut level as every diagonal's are.
    th = t_upright * math.sqrt(1 + (m / STRETCH) ** 2)
    return slash_through(m, th, V / 2, cy, cy - hy, cy + hy)


@variant("slashL", "1", "leichter Strich wie beim €")
def lslash_light():
    return union(L(), l_slash(LIGHT_BAR * STRETCH))


@variant("slashL", "2", "kräftiger Strich (172)")
def lslash_bar():
    return union(L(), l_slash(H3 * STRETCH))


@glyph("Lslash", 0x141)
def Lslash():
    return drawn("slashL")


@glyph("Oslash", 0xD8)
def Oslash():
    return drawn("slashO")


for _n, _d, _b in (("Dcroat", "barD", "D"), ("Eth", "barD", "D"), ("Hbar", "barH", "H"), ("Lslash", "slashL", "L"),
                   ("Oslash", "slashO", "O")):
    COMPOSITE[_n] = (_b, [])
    DEPENDS[_n] = [_d]



# =============================================================================================
# Æ Œ Þ (GF Latin Core)
# =============================================================================================
# Æ and Œ carry the E's three storeys (bars 172, counters 92); the A's and O's part keep their
# own construction. Þ is the P's bowl on a stem that runs through.

DESIGN_NAMES["AE"] = "Æ"
DESIGN_NAMES["OE"] = "Œ"
DESIGN_NAMES["Thorn"] = "Þ"
A_SLOPE = 540 / 700                    # the pointed A's legs: (1420 - 340) / 2 across the cap height


def ae_shape(W=1760, xs=900, round_a=False):
    """The A's left leg (or the round A's side), the E's stem at xs and its three bars to W. The
    round A of ss01 leaves the Æ pointed: a round Æ reads as FE, the F being the round A without
    its right side."""
    # on the round side the bars start where the O's corner ends, so it stays the O's
    x_top, x_mid = (BIG[0], V / 2) if round_a else (0, 0)
    bars = union(rect(x_top, Y_T0, W, CH), rect(x_mid, Y_M0, W, Y_M1), rect(xs, 0, W, Y_B1), rect(xs, 0, xs + V, CH))
    if round_a:
        out = union(minus(rect(0, 0, xs + 1, CH, BIG, None, None, None), rect(V, -10, xs + 2, Y_M0, None, None, None, None),
                          rect(V, Y_M1, xs + 2, Y_T0, CNT3, None, None, None)), bars)
        return out
    h = diag_h(A_SLOPE)
    leg = band(A_SLOPE, 0, h, 0, CH)
    left = clip(bars, poly((0, 0), (W + 10, 0), (W + 10, CH), (A_SLOPE * CH, CH)))
    return union(leg, left)


@variant("AE", "1", "E-Teil breit")
def AE_wide():
    return ae_shape()


@variant("AE", "2", "E-Teil schmaler")
def AE_narrow():
    return ae_shape(1640, 880)


@glyph("AE", 0xC6)
def AE():
    return drawn("AE")


def oe_shape(W=1820, xs=860, o_bars=True):
    """The O's left half and its counter, closed by the E's stem at xs; the E's storeys after."""
    out = rect(0, 0, W, CH, BIG, None, None, BIG)
    if o_bars:
        counter = rect(256, OB, xs, CH - OT, CNT, None, None, CNT)
    else:
        counter = rect(256, Y_B1, xs, Y_T0, CNT, None, None, CNT)
    return minus(out, counter, rect(xs + V, Y_M1, W + 10, Y_T0), rect(xs + V, Y_B1, W + 10, Y_M0))


@variant("OE", "1", "O-Teil mit den Balken des O")
def OE_obars():
    return oe_shape()


@variant("OE", "2", "dreistöckig durchgehend")
def OE_three():
    return oe_shape(o_bars=False)


@glyph("OE", 0x152)
def OE():
    return drawn("OE")


def thorn_shape(dy=79, W=1206):
    return minus(union(rect(0, 0, 260, CH), translate(rect(0, 157, W, CH, None, BOWL, BOWL, None), 0, -dy)),
                 translate(p_counter(W), 0, -dy))


@variant("Thorn", "1", "Bauch des P, mittig")
def thorn_mid():
    return thorn_shape()


@variant("Thorn", "2", "Bauch des P, tiefer")
def thorn_low():
    return thorn_shape(120)


@glyph("Thorn", 0xDE)
def Thorn():
    return drawn("Thorn")


for _n, _d in (("AE", "AE"), ("OE", "OE"), ("Thorn", "Thorn")):
    DEPENDS[_n] = [_d]


# =============================================================================================
# Signs (GF Latin Core)
# =============================================================================================

DESIGN_NAMES["cent"] = "¢"
DESIGN_NAMES["sterling"] = "£"
DESIGN_NAMES["yen"] = "¥"
DESIGN_NAMES["copyright"] = "© und ®"
DESIGN_NAMES["trademark"] = "™"
DESIGN_NAMES["section"] = "§"
DESIGN_NAMES["paragraph"] = "¶"
DESIGN_NAMES["brace"] = "{ }"
DESIGN_NAMES["inverted"] = "¡ ¿"
DESIGN_NAMES["bullet"] = "•"
DESIGN_NAMES["ordinal"] = "ª º"
DESIGN_NAMES["asciicircum"] = "^"
SIGN_T = 230                           # the $'s and #'s upright


def cent_shape(through, W=1060):
    c = C(W)
    cx = W / 2
    if through:
        return union(c, rect(cx - SIGN_T / 2, -120, cx + SIGN_T / 2, CH + 120))
    return union(c, rect(cx - SIGN_T / 2, -120, cx + SIGN_T / 2, 1), rect(cx - SIGN_T / 2, CH - 1, cx + SIGN_T / 2, CH + 120))


@variant("cent", "1", "Strich oben und unten, wie beim $")
def cent_outside():
    return cent_shape(False)


@variant("cent", "2", "Strich durch das C")
def cent_through():
    return cent_shape(True)


@glyph("cent", 0xA2)
def cent():
    return drawn("cent")


def sterling_shape(bar, W=1100, xs=240):
    # The F's top (its round corner and top bar, shorter), a stem, the L's foot, a crossbar.
    top = minus(rect(xs, OB, W - 120, CH, BIG, None, None, None), rect(xs + V, OB - 10, W, CH - OT, CNT, None, None, None))
    foot = rect(60, 0, W, OB)
    cross = rect(60, 330 - bar / 2, xs + V + 220, 330 + bar / 2)
    return union(top, foot, cross)


@variant("sterling", "1", "leichter Querbalken wie beim €")
def sterling_light():
    return sterling_shape(110)


@variant("sterling", "2", "Querbalken 172")
def sterling_bar():
    return sterling_shape(H3)


@glyph("sterling", 0xA3)
def sterling():
    return drawn("sterling")


def yen_shape(bars, W=1340):
    y = Y()
    half = 330
    if bars == 2:
        b = union(rect(W / 2 - half, 120, W / 2 + half, 230), rect(W / 2 - half, 290, W / 2 + half, 400))
    else:
        b = rect(W / 2 - half, 190, W / 2 + half, 190 + H3)
    return union(y, b)


@variant("yen", "1", "zwei leichte Balken wie beim €")
def yen_two():
    return yen_shape(2)


@variant("yen", "2", "ein Balken 172")
def yen_one():
    return yen_shape(1)


@glyph("yen", 0xA5)
def yen():
    return drawn("yen")


def light_ring(W, y0, y1, side=160, bar=120):
    """The @'s ring: a lighter O."""
    return minus(rect(0, y0, W, y1, BIG, BIG, BIG, BIG), rect(side, y0 + bar, W - side, y1 - bar, CNT, CNT, CNT, CNT))


SMALL_BOWL = (120, 92, 0.62)           # the corner of the a inside the @


def small_c(x0, y0, w, h, side=170, bar=115):
    inner = (SMALL_C[0], SMALL_C[1], SMALL_C[2])
    ring = minus(rect(x0, y0, x0 + w, y0 + h, SMALL_BOWL, SMALL_BOWL, SMALL_BOWL, SMALL_BOWL),
                 rect(x0 + side, y0 + bar, x0 + w - side, y0 + h - bar, inner, inner, inner, inner))
    return minus(ring, rect(x0 + w - side - 1, y0 + bar + 40, x0 + w + 10, y0 + h - bar - 40))


def small_r(x0, y0, w, h, side=170, bar=80):
    bowl_y = y0 + h * 0.42
    inner = (SMALL_C[0], SMALL_C[1], SMALL_C[2])
    c = (SMALL_BOWL[0], 75, SMALL_BOWL[2])         # the bowl is half as tall as the C: its corner lower
    bowl = minus(rect(x0, bowl_y, x0 + w, y0 + h, None, c, c, None),
                 rect(x0 + side, bowl_y + bar, x0 + w - side, y0 + h - bar, None, inner, inner, None))
    m = -1.2246
    t = diag_h(m) * 0.42
    leg = clip(band(m, x0 + w - t - m * y0, x0 + w - m * y0, y0, bowl_y + 1), rect(x0, y0, x0 + w, bowl_y + 1))
    return union(rect(x0, y0, x0 + side, y0 + h), bowl, leg)


def circled(inner, big):
    if big:
        W, y0, y1 = 1420, -150, CH
    else:
        W, y0, y1 = 1333, 0, CH
    ring = light_ring(W, y0, y1)
    iw, ih = 560, (y1 - y0) * 0.55
    return union(ring, inner(W / 2 - iw / 2 + 10, (y0 + y1) / 2 - ih / 2, iw, ih))


@variant("copyright", "1", "Ring wie beim @, auf Versalhöhe")
def copyright_cap():
    return circled(small_c, False)


@variant("copyright", "2", "Ring so groß wie das @")
def copyright_big():
    return circled(small_c, True)


@glyph("copyright", 0xA9)
def copyright():
    return drawn("copyright")


@glyph("registered", 0xAE)
def registered():
    return circled(small_r, VARIANT["copyright"] == "2")


def trademark_shape(s, gap=70):
    # The face's own T and M, small, their tops on the cap height.
    t = scale(T(), s)
    m = scale(M(), s)
    tw = t.bounds[2]
    return translate(union(t, translate(m, tw + gap)), 0, CH - CH * s)


@variant("trademark", "1", "T und M der Schrift, klein (330 hoch)")
def trademark_47():
    return trademark_shape(330 / CH)


@variant("trademark", "2", "noch kleiner (280 hoch)")
def trademark_40():
    return trademark_shape(280 / CH)


@glyph("trademark", 0x2122)
def trademark():
    return drawn("trademark")


def section_shape(round_ends, W=900, b=150, c=107, s=200, y0=-110):
    """Two S's run into one: four bars; the left side joins the upper three, the right the lower
    three, so the middle counter is closed. Its corners the O's, its counters the S's."""
    ys = [y0]
    for step in (b, c, b, c, b, c, b):
        ys.append(ys[-1] + step)
    y1, y2, y3, y4, y5, y6, y7 = ys[1:]
    k = CNT3
    out = poly((0, y0), (W, y0, BIG), (W, y5, BIG), (s, y5, k), (s, y6, k), (W, y6), (W, y7),
               (0, y7, BIG), (0, y2, BIG), (W - s, y2, k), (W - s, y1, k), (0, y1))
    out = minus(out, rect(s, y3, W - s, y4, k, k, k, k))
    if round_ends:
        out = minus(out, round_corner(W, y7, -1, -1), round_corner(0, y0, 1, 1))
    return out


@variant("section", "1", "runde Enden wie beim S")
def section_round():
    return section_shape(True)


@variant("section", "2", "gerade Enden")
def section_square():
    return section_shape(False)


@glyph("section", 0xA7)
def section():
    return drawn("section")


def pilcrow_shape(filled, W=940, st=190, gap=110):
    x2 = W - st                         # the second stem
    x1 = x2 - gap - st                  # the first stem, the bowl's side
    bowl = rect(0, 250, x1 + st, CH, BIG, None, None, BIG)
    if not filled:
        bowl = minus(bowl, rect(220, 250 + 140, x1 + 1, CH - OT, CNT, None, None, CNT))
    return union(bowl, rect(x1, 0, x1 + st, CH), rect(x2, 0, W, CH), rect(x1, CH - OT, W, CH))


@variant("paragraph", "1", "Bauch gefüllt")
def pilcrow_filled():
    return pilcrow_shape(True)


@variant("paragraph", "2", "Bauch offen")
def pilcrow_open():
    return pilcrow_shape(False)


@glyph("paragraph", 0xB6)
def paragraph():
    return drawn("paragraph")


def brace_shape(round_, W=440, y0=-80, y1=780, x=110, t=200, arm=165, tab=150):
    """The bracket's arms on a stem set in, and a tab pointing out at the middle."""
    cy = (y0 + y1) / 2
    c = PAREN if round_ else None
    ci = PAREN_IN if round_ else None
    upper = minus(rect(x, cy, W, y1, c, None, None, None), rect(x + t, cy - 10, W + 10, y1 - arm, ci, None, None, None))
    lower = minus(rect(x, y0, W, cy, None, None, None, c), rect(x + t, y0 + arm, W + 10, cy + 10, None, None, None, ci))
    return union(upper, lower, rect(0, cy - tab / 2, x + t, cy + tab / 2))


@variant("brace", "1", "eckig wie die [ ]")
def brace_square():
    return brace_shape(False)


@variant("brace", "2", "rund wie die ( )")
def brace_round():
    return brace_shape(True)


@glyph("braceleft", ord("{"))
def braceleft():
    return drawn("brace")


@glyph("braceright", ord("}"))
def braceright():
    b = drawn("brace")
    return mirror_x(b, 220)


@variant("inverted", "1", "gedreht, auf der Grundlinie")
def inverted_base():
    return None


@variant("inverted", "2", "gedreht, unter die Grundlinie gesenkt")
def inverted_low():
    return None


def inverted(sign):
    p = sign()
    b = p.bounds
    r = rotate180(p, (b[0] + b[2]) / 2, CH / 2)
    return translate(r, 0, -250) if VARIANT["inverted"] == "2" else r


@glyph("exclamdown", 0xA1)
def exclamdown():
    return inverted(exclam)


@glyph("questiondown", 0xBF)
def questiondown():
    return inverted(question)


@variant("bullet", "1", "eckig, größer als der Punkt")
def bullet_square():
    return rect(0, 350 - 140, 370, 350 + 140)


@variant("bullet", "2", "rund")
def bullet_round():
    c = (150, 114, 0.605)
    return rect(0, 350 - 140, 370, 350 + 140, c, c, c, c)


@glyph("bullet", 0x2022)
def bullet():
    return drawn("bullet")


def small_a_shape(W=560, H=290, f=150, h=130, bar=(45, 105)):
    """The pointed A, small: its legs h across, its crossbar low."""
    a = (W - f) / 2
    m = a / H
    outer = poly((0, 0), (W, 0), (W - a, H), (a, H))
    y_apex = (W - 2 * h) / (2 * m)
    inner = minus(poly((h, 0), (W - h, 0), (W / 2, y_apex)), rect(-10, bar[0], W + 10, bar[1]))
    return minus(outer, inner)


def ordinal(letter, underline, W):
    y = CH - 290
    p = translate(letter(), 0, y)
    if underline:
        p = union(p, rect(0, y - 100 - 90, W, y - 100))
    return p


@variant("ordinal", "1", "mit Strich darunter")
def ordinal_bar():
    return None


@variant("ordinal", "2", "ohne Strich")
def ordinal_plain():
    return None


@glyph("ordfeminine", 0xAA)
def ordfeminine():
    return ordinal(small_a_shape, VARIANT["ordinal"] == "1", 560)


@glyph("ordmasculine", 0xBA)
def ordmasculine():
    return ordinal(lambda: small_o(0, 0), VARIANT["ordinal"] == "1", 400)


@glyph("divide", 0xF7)
def divide(W=800):
    # The minus with a dieresis dot above and below, as far from it as the dots stand from the caps.
    bar = rect(0, 350 - HM / 2, W, 350 + HM / 2)
    gap = DOT_GAP * 0.7
    d = lambda y: rect(W / 2 - DOT_W / 2, y, W / 2 + DOT_W / 2, y + DOT_H)  # noqa: E731
    return union(bar, d(350 + HM / 2 + gap), d(350 - HM / 2 - gap - DOT_H))


@glyph("minus", 0x2212)
def minus_sign(W=800):
    # The plus's bar.
    return rect(0, 350 - HM / 2, W, 350 + HM / 2)


@glyph("backslash", ord("\\"))
def backslash():
    s = slash()
    return mirror_x(s, mid_x(s))


@variant("asciicircum", "1", "der Zirkumflex, groß")
def asciicircum_roof():
    return roof(720, 330, 160, 0, CH - 330)


@variant("asciicircum", "2", "der Pfeil < gedreht")
def asciicircum_arrow():
    c = rotate90(chevron(LT_HALF), 0, 0)
    c = rotate90(rotate90(c, 0, 0), 0, 0)            # pointing up
    b = c.bounds
    return translate(c, -b[0], CH - b[3])


@glyph("asciicircum", ord("^"))
def asciicircum():
    return drawn("asciicircum")


@glyph("asciitilde", ord("~"))
def asciitilde():
    # The tilde as chosen, larger, in the middle of the caps.
    t = scale(tilde_mark(), 1.45)
    b = t.bounds
    return translate(t, -b[0], 350 - (b[1] + b[3]) / 2)


for _n, _d in (("cent", "cent"), ("sterling", "sterling"), ("yen", "yen"), ("copyright", "copyright"),
               ("registered", "copyright"), ("trademark", "trademark"), ("section", "section"),
               ("paragraph", "paragraph"), ("braceleft", "brace"), ("braceright", "brace"),
               ("exclamdown", "inverted"), ("questiondown", "inverted"), ("bullet", "bullet"),
               ("ordfeminine", "ordinal"), ("ordmasculine", "ordinal"), ("asciicircum", "asciicircum")):
    DEPENDS[_n] = [_d]


# =============================================================================================
# The accents on their own
# =============================================================================================
# Spacing accents stand where they stand over the caps; combining marks have no width and stand
# over the letter before them (centred on COMBINING_X when nothing positions them; the mark
# feature in build.py places them on each letter's anchor).

SPACING_ACCENTS = {"grave": 0x60, "dieresis": 0xA8, "macron": 0xAF, "acute": 0xB4, "cedilla": 0xB8,
                   "circumflex": 0x2C6, "caron": 0x2C7, "breve": 0x2D8, "dotaccent": 0x2D9, "ring": 0x2DA,
                   "ogonek": 0x2DB, "tilde": 0x2DC, "hungarumlaut": 0x2DD}
COMBINING_X = -660
COMBINING_MARKS = {}                   # glyph name -> mark


def _spacing(mark):
    return lambda: MARKS[mark]()


def _combining(mark):
    def draw():
        m = MARKS[mark]()
        if mark == "ogonek":
            return translate(m, COMBINING_X)
        return centred(m, COMBINING_X)
    return draw


for _mark, _code in SPACING_ACCENTS.items():
    glyph(_mark, _code)(_spacing(_mark))
    DEPENDS[_mark] = [MARK_DESIGN[_mark]] if _mark in MARK_DESIGN else []
for _code, _mark in COMBINING.items():
    _name = _mark + "comb"
    glyph(_name, _code)(_combining(_mark))
    COMBINING_MARKS[_name] = _mark


# =============================================================================================
# His choices
# =============================================================================================
# Review round 1 (2026-10-17), accents and strokes, as @lrkqz picked them from the variants:
# "1:1 · 2:1 · 3:2 · 4:2 · 5:2 · 6:2 · 7:2 · 8:2 · 9:2 · 10:2 · 11:1 · 12:1 · 13:1".
CHOSEN = {"acute": "1", "circumflex": "1", "tilde": "2", "macron": "2", "breve": "2", "ring": "2",
          "cedilla": "2", "commaaccent": "2", "ogonek": "2", "slashO": "2", "barD": "1", "barH": "1",
          "slashL": "1"}
# Review round 2 (2026-10-17), Æ Œ Þ and the signs:
# "1:2 · 2:2 · 3:1 · 4:1 · 5:1 · 6:1 · 7:1 · 8:2 · 9:1 · 10:2 · 11:2 · 12:2 · 13:1 · 14:1 · 15:1".
CHOSEN.update({"AE": "2", "OE": "2", "Thorn": "1", "cent": "1", "sterling": "1", "yen": "1", "copyright": "1",
               "trademark": "2", "section": "1", "paragraph": "2", "brace": "2", "inverted": "2", "bullet": "1",
               "ordinal": "1", "asciicircum": "1"})
VARIANT.update(CHOSEN)
