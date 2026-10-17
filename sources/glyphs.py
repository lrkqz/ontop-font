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
from geometry import rect, poly, band, union, minus, clip, mirror_x, mirror_y, rotate180, translate, line_through

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
