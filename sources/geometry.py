"""Drawing primitives: contours with rounded corners, diagonal bands, and boolean operations.

Every glyph of the typeface is built from these. A contour is a list of vertices; a vertex is
(x, y) for a sharp corner or (x, y, corner) for a rounded one, where corner = (rx, ry, k):
rx is how far the curve reaches along the horizontal edge next to the corner, ry along the
vertical edge, and k the length of the Bezier handles as a fraction of that reach (0.5523 is
an ellipse; more is squarer). This is exactly the model fitted to the corners of the ON TOP
image (see docs/MEASUREMENTS.md).

Coordinates are font units, y up, the baseline at 0.
"""
import math
import pathops


def _unit(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    return dx / d, dy / d, d


def _reach(corner, ux, uy):
    """How far a rounded corner reaches along an edge with direction (ux, uy)."""
    rx, ry, _ = corner
    return rx if abs(ux) >= abs(uy) else ry


def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i][0], pts[i][1]
        x1, y1 = pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][1]
        a += x0 * y1 - x1 * y0
    return a / 2


def contour(vertices):
    """A closed pathops.Path through the vertices, counter-clockwise (outer contour)."""
    vs = [v if len(v) == 3 else (v[0], v[1], None) for v in vertices]
    if signed_area(vs) < 0:
        vs = vs[::-1]
    n = len(vs)
    entry, exit_, ctrl = [], [], []
    for i, (x, y, c) in enumerate(vs):
        px, py, _ = vs[i - 1]
        nx, ny, _ = vs[(i + 1) % n]
        if c is None:
            entry.append((x, y)); exit_.append((x, y)); ctrl.append(None)
            continue
        k = c[2]
        ux, uy, din = _unit(x, y, px, py)
        vx, vy, dout = _unit(x, y, nx, ny)
        rin = min(_reach(c, ux, uy), din)
        rout = min(_reach(c, vx, vy), dout)
        p0 = (x + ux * rin, y + uy * rin)
        p3 = (x + vx * rout, y + vy * rout)
        c1 = (p0[0] - ux * rin * k, p0[1] - uy * rin * k)
        c2 = (p3[0] - vx * rout * k, p3[1] - vy * rout * k)
        entry.append(p0); exit_.append(p3); ctrl.append((c1, c2))
    p = pathops.Path()
    p.moveTo(*exit_[0])
    last = exit_[0]
    for j in list(range(1, n)) + [0]:
        if entry[j] != last:
            p.lineTo(*entry[j])
        if ctrl[j] is not None:
            (c1, c2) = ctrl[j]
            p.cubicTo(c1[0], c1[1], c2[0], c2[1], exit_[j][0], exit_[j][1])
        last = exit_[j]
    p.close()
    return p


def rect(x0, y0, x1, y1, tl=None, tr=None, br=None, bl=None):
    """An axis-aligned rectangle; each corner sharp or rounded."""
    return contour([(x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl)])


def poly(*pts):
    return contour(list(pts))


def band(m, a_left, a_right, y0, y1):
    """The region between the parallel lines x = a_left + m*y and x = a_right + m*y, from y0 to y1.
    m is dx/dy: positive leans right going up."""
    return poly((a_left + m * y0, y0), (a_right + m * y0, y0), (a_right + m * y1, y1), (a_left + m * y1, y1))


def line_through(x, y, m):
    """The a of the line x = a + m*y through (x, y)."""
    return x - m * y


def union(*paths):
    paths = [p for p in paths if p is not None]
    out = paths[0]
    for p in paths[1:]:
        out = pathops.op(out, p, pathops.PathOp.UNION)
    return out


def minus(a, *holes):
    for h in holes:
        a = pathops.op(a, h, pathops.PathOp.DIFFERENCE)
    return a


def clip(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def translate(path, dx, dy=0):
    out = pathops.Path()
    for verb, pts in path:
        moved = [(x + dx, y + dy) for x, y in pts]
        if verb == pathops.PathVerb.MOVE:
            out.moveTo(*moved[0])
        elif verb == pathops.PathVerb.LINE:
            out.lineTo(*moved[0])
        elif verb == pathops.PathVerb.CUBIC:
            out.cubicTo(*moved[0], *moved[1], *moved[2])
        elif verb == pathops.PathVerb.QUAD:
            out.quadTo(*moved[0], *moved[1])
        elif verb == pathops.PathVerb.CLOSE:
            out.close()
    return out


def mirror_x(path, axis):
    """Mirror left-right about x = axis (contour direction is fixed by the next union)."""
    out = pathops.Path()
    for verb, pts in path:
        moved = [(2 * axis - x, y) for x, y in pts]
        if verb == pathops.PathVerb.MOVE:
            out.moveTo(*moved[0])
        elif verb == pathops.PathVerb.LINE:
            out.lineTo(*moved[0])
        elif verb == pathops.PathVerb.CUBIC:
            out.cubicTo(*moved[0], *moved[1], *moved[2])
        elif verb == pathops.PathVerb.CLOSE:
            out.close()
    return pathops.op(out, out, pathops.PathOp.UNION)


def mirror_y(path, axis):
    out = pathops.Path()
    for verb, pts in path:
        moved = [(x, 2 * axis - y) for x, y in pts]
        if verb == pathops.PathVerb.MOVE:
            out.moveTo(*moved[0])
        elif verb == pathops.PathVerb.LINE:
            out.lineTo(*moved[0])
        elif verb == pathops.PathVerb.CUBIC:
            out.cubicTo(*moved[0], *moved[1], *moved[2])
        elif verb == pathops.PathVerb.CLOSE:
            out.close()
    return pathops.op(out, out, pathops.PathOp.UNION)


def rotate180(path, cx, cy):
    return mirror_y(mirror_x(path, cx), cy)


def bounds(path):
    if path is None:
        return None
    b = path.bounds
    return b  # (xmin, ymin, xmax, ymax)


def flatten(path, steps=24):
    """Contours as lists of points (cubics sampled), for rasterising and measuring."""
    out, cur = [], []
    last = None
    for verb, pts in path:
        if verb == pathops.PathVerb.MOVE:
            if cur:
                out.append(cur)
            cur = [pts[0]]; last = pts[0]
        elif verb == pathops.PathVerb.LINE:
            cur.append(pts[0]); last = pts[0]
        elif verb == pathops.PathVerb.CUBIC:
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = last, pts[0], pts[1], pts[2]
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                cur.append((mt ** 3 * x0 + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t ** 3 * x3,
                            mt ** 3 * y0 + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t ** 3 * y3))
            last = pts[2]
        elif verb == pathops.PathVerb.QUAD:
            (x0, y0), (x1, y1), (x2, y2) = last, pts[0], pts[1]
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                cur.append((mt * mt * x0 + 2 * mt * t * x1 + t * t * x2, mt * mt * y0 + 2 * mt * t * y1 + t * t * y2))
            last = pts[1]
        elif verb == pathops.PathVerb.CLOSE:
            if cur:
                out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out
