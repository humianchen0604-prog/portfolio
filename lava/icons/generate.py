#!/usr/bin/env python3
"""Lava memory icons: 20 liquid, acid-feeling marks.

Each icon is a recipe of circles, rings, stars, sparkles and strokes, joined
with smooth unions (the gooey necks between blobs) and smooth cuts (the holes
the acid eats). The recipe is a signed distance field; its edge is traced and
fitted with cubic Béziers, so every SVG comes out as one plain, editable path
(fill-rule evenodd, fill currentColor): no filters, masks or strokes.

    python3 lava/icons/generate.py      # writes svg/*.svg and refreshes index.html

To tweak an icon, change its recipe below and run the script again.
"""
import math
import pathlib
import re

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SIZE = 100.0
STEP = 0.125
_axis = np.linspace(0, SIZE, int(SIZE / STEP) + 1)
X, Y = np.meshgrid(_axis, _axis)

W = 2.4  # outline weight
J = 5.0  # how far outlines melt into each other where they meet
DOT = 0.0  # smallest radius for loose dots and pin-holes
GROW = 0.0  # how much filled icons swell

# Bold is drawn for 32px and below: heavier lines, no dot or hole too small to see.
WEIGHTS = {
    "regular": dict(W=2.4, J=5.0, DOT=0.0, GROW=0.0),
    "bold": dict(W=4.2, J=6.5, DOT=2.8, GROW=0.7),
}


# ---------------------------------------------------------------- shapes
# Signed distance in viewBox units: negative inside, positive outside.

def circle(cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def _seg_dist(pts, closed):
    pts = np.asarray(pts, float)
    a = pts if closed else pts[:-1]
    b = np.roll(pts, -1, axis=0) if closed else pts[1:]
    lo, hi = pts.min(axis=0) - 25, pts.max(axis=0) + 25
    j0, j1 = (np.clip([lo[0], hi[0]], 0, SIZE) / STEP).astype(int)
    i0, i1 = (np.clip([lo[1], hi[1]], 0, SIZE) / STEP).astype(int)
    xs, ys = X[i0:i1 + 1, j0:j1 + 1], Y[i0:i1 + 1, j0:j1 + 1]
    d2 = np.full(xs.shape, np.inf)
    for (ax, ay), (bx, by) in zip(a, b):
        ex, ey = bx - ax, by - ay
        wx, wy = xs - ax, ys - ay
        ll = ex * ex + ey * ey
        t = np.clip((wx * ex + wy * ey) / ll, 0, 1) if ll > 0 else 0.0
        dx, dy = wx - ex * t, wy - ey * t
        np.minimum(d2, dx * dx + dy * dy, out=d2)
    # Far from the shape only a lower bound is needed: distance to its box.
    far = np.hypot(np.maximum(np.maximum(lo[0] - X, X - hi[0]), 0),
                   np.maximum(np.maximum(lo[1] - Y, Y - hi[1]), 0)) + 25
    far[i0:i1 + 1, j0:j1 + 1] = np.sqrt(d2)
    return far


def polygon(pts):
    pts = np.asarray(pts, float)
    d = _seg_dist(pts, closed=True)
    inside = np.zeros(X.shape, bool)
    with np.errstate(divide="ignore", invalid="ignore"):
        for (ax, ay), (bx, by) in zip(pts, np.roll(pts, -1, axis=0)):
            if ay == by:
                continue
            crosses = (ay > Y) != (by > Y)
            inside ^= crosses & (X < (bx - ax) * (Y - ay) / (by - ay) + ax)
    return np.where(inside, -d, d)


def stroke(pts, w=None):
    return _seg_dist(pts, closed=False) - (W if w is None else w) / 2


def capsule(a, b, r):
    return _seg_dist([a, b], closed=False) - r


def ring(d, w=None):
    return np.abs(d) - (W if w is None else w) / 2


def dot(cx, cy, r):
    """A loose droplet or pin-hole, never smaller than the weight allows."""
    return circle(cx, cy, max(r, DOT))


def _fillet(pts, radii, seg=12):
    """Round every corner of a polygon with an arc of the given radius."""
    out, n = [], len(pts)
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        u = (a - p) / np.linalg.norm(a - p)
        v = (b - p) / np.linalg.norm(b - p)
        ang = math.acos(np.clip(u @ v, -1, 1))
        # Keep neighbouring arcs from overlapping on short edges.
        t = min(radii[i] / math.tan(ang / 2), 0.45 * min(np.linalg.norm(a - p), np.linalg.norm(b - p)))
        r = t * math.tan(ang / 2)
        bis = (u + v) / np.linalg.norm(u + v)
        c = p + bis * r / math.sin(ang / 2)
        p1, p2 = p + u * t, p + v * t
        a1 = math.atan2(*(p1 - c)[::-1])
        da = (math.atan2(*(p2 - c)[::-1]) - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            out.append(c + r * np.array([math.cos(a1 + da * k / seg), math.sin(a1 + da * k / seg)]))
    return np.array(out)


def star(cx, cy, R, n=5, inner=0.5, rot=-90, tip=1.6, notch=2.2):
    """Rounded n-point star; rot is the angle of the first point (-90 = up)."""
    pts, radii = [], []
    for k in range(2 * n):
        r = R if k % 2 == 0 else R * inner
        a = math.radians(rot + 180 * k / n)
        pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
        radii.append(tip if k % 2 == 0 else notch)
    return polygon(_fillet(np.array(pts), radii))


def sparkle(cx, cy, R, rot=0, pinch=3.4, tip=1.0):
    """Four-point sparkle with curved, pinched sides."""
    t = np.linspace(0, 2 * math.pi, 280, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    r = R - tip
    x = r * np.sign(c) * np.abs(c) ** pinch
    y = r * np.sign(s) * np.abs(s) ** pinch
    a = math.radians(rot)
    pts = np.c_[cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)]
    return polygon(pts) - tip


def ellipse(cx, cy, a, b):
    t = np.linspace(0, 2 * math.pi, 240, endpoint=False)
    return polygon(np.c_[cx + a * np.cos(t), cy + b * np.sin(t)])


def teardrop(cx, cy, R, m=1.5, tip=1.5):
    """Drop with its point up; R is half its height."""
    t = np.linspace(0, 2 * math.pi, 280, endpoint=False)
    r = R - tip
    return polygon(np.c_[cx + r * np.sin(t) * np.abs(np.sin(t / 2)) ** m, cy - r * np.cos(t)]) - tip


def drip(x, y0, y1, w, bulb):
    """A run of liquid from (x, y0) down to a round bead at y1."""
    return union(capsule((x, y0), (x, y1), w), circle(x, y1, bulb), k=3)


def curve(pts, per=24):
    """Smooth Catmull-Rom curve through the points, as a polyline."""
    p = np.asarray(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2])
    return np.array(out)


# ---------------------------------------------------------------- melting

def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def union(*ds, k=0.0):
    out = ds[0]
    for d in ds[1:]:
        out = smin(out, d, k)
    return out


def cut(a, b, k=0.0):
    """a with b eaten out of it."""
    return -smin(-a, b, k)


def keep(a, b, k=0.0):
    """Only where a and b overlap."""
    return -smin(-a, -b, k)


# ---------------------------------------------------------------- icons

ICONS = []


def icon(name, kind, note):
    def register(fn):
        ICONS.append(dict(name=name, kind=kind, note=note, fn=fn))
        return fn
    return register


@icon("Kept Spark", "fill", "A memory held inside the drop, one bead slipping away.")
def kept_spark():
    d = union(circle(50, 54, 36), circle(81, 19, 6), k=11)
    return cut(d, sparkle(41, 45, 17), k=1.5)


@icon("Bubble Foam", "line", "Memories as foam: cells that share walls and melt where they meet.")
def bubble_foam():
    d = union(ring(circle(63, 39, 27)), ring(circle(30, 36, 18)), ring(circle(38, 69, 24)),
              ring(circle(76, 72, 6)), k=J)
    return np.minimum(d, sparkle(68, 33, 10))


@icon("Memory Chain", "fill", "Small moments gather and swell into one that keeps a star.")
def memory_chain():
    dots = np.minimum(circle(15, 84, 3.5), circle(28, 77, 5.5))
    chain = union(circle(42, 67, 7.5), circle(54, 50, 9.5), circle(69, 27, 13.5), k=12)
    return cut(np.minimum(dots, chain), star(69, 27.5, 7.5, inner=0.48, tip=1, notch=1), k=0.8)


@icon("Star Cell", "line", "A sparkle grown into the walls of its vessel.")
def star_cell():
    d = union(ring(circle(50, 50, 38)), ring(sparkle(50, 50, 38, tip=1.5)), k=J + 1)
    return np.minimum(d, circle(50, 50, 4))


@icon("Cell Orb", "fill", "A sealed orb divided into chambers; one keeps a spark.")
def cell_orb():
    walls = union(capsule((45, 40), (6, 31), 2.4), capsule((45, 40), (94, 22), 2.4),
                  capsule((45, 40), (48, 96), 2.4), k=3)
    chambers = keep(circle(50, 50, 32.5), -walls, k=7)
    d = cut(circle(50, 50, 38), chambers)
    return np.minimum(d, sparkle(68, 63, 9))


@icon("Lava Lamp", "line", "The lamp itself: a pool that lets go of a blob, a star rising.")
def lava_lamp():
    vessel = ring(capsule((50, 28), (50, 72), 20))
    lava = union(circle(50, 80, 10), circle(45, 57, 7), k=14)
    return np.minimum(union(vessel, lava, k=4), star(55, 30, 8.5, inner=0.5, tip=1.2, notch=1.4))


@icon("Acid Drip", "fill", "The orb runs: what it keeps leaks out in beads.")
def acid_drip():
    d = union(circle(50, 38, 29), drip(36, 50, 74, 2.6, 4.6), drip(55, 55, 85, 3.2, 5.8),
              drip(69, 52, 66, 2.2, 3.6), k=7)
    d = cut(d, star(45, 33, 10.5, inner=0.48, tip=1.2, notch=1.4), k=1)
    return np.minimum(d, dot(69, 77, 2.6))


@icon("Venn Memory", "line", "Three overlapping memories; the spark lives where all of them meet.")
def venn_memory():
    d = union(ring(circle(50, 37, 23)), ring(circle(36, 61, 23)), ring(circle(64, 61, 23)), k=J)
    return np.minimum(d, sparkle(50, 53, 5.5))


@icon("Split Memory", "fill", "A memory breaking into pieces that are still held by threads.")
def split_memory():
    d = union(circle(44, 62, 21), circle(55, 25, 13), circle(79, 50, 11), circle(19, 44, 5), k=12)
    return cut(d, sparkle(45, 63, 10), k=1)


@icon("Mitosis", "line", "A memory copying itself: the new cell carries a smaller star.")
def mitosis():
    d = ring(union(circle(34, 50, 22), circle(71, 50, 17), k=14))
    return np.minimum(d, np.minimum(star(34, 50, 10, inner=0.48, tip=1.2, notch=1.5),
                                    star(71, 50, 6, inner=0.48, tip=0.8, notch=1)))


@icon("Melting Star", "fill", "The star itself turning liquid, with a hollow core.")
def melting_star():
    d = union(star(50, 38, 32, inner=0.52, tip=3, notch=4),
              drip(70.5, 60, 77, 2.8, 4.4), drip(30, 60, 71, 2.3, 3.4), drip(50, 54, 66, 2, 3), k=5)
    d = cut(d, circle(50, 40, 5.5), k=1)
    return np.minimum(d, dot(70.5, 87, 2.4))


@icon("Star Orbit", "line", "A spark at the core, beads of memory clinging to its orbit.")
def star_orbit():
    d = union(ring(circle(50, 50, 35)), circle(74.7, 25.3, 6), circle(25.3, 74.7, 3.4), k=J)
    return np.minimum(d, ring(sparkle(50, 50, 17)))


@icon("Eroded Orb", "fill", "Acid eats at the edge; the star in the middle stays.")
def eroded_orb():
    bites = union(circle(70, 70, 9), circle(84, 53, 5), circle(62, 86, 5.5), circle(83, 70, 4.2),
                  circle(55, 65, 3.6), circle(74, 82, 3.4), dot(47, 77, 2.6), dot(64, 55, 2.4),
                  dot(80, 40, 2.2), k=3)
    d = cut(circle(50, 50, 37), bites, k=2.5)
    d = cut(d, star(38, 37, 12, inner=0.48, tip=1.4, notch=1.8), k=1)
    return np.minimum(d, dot(91, 61, 1.8))


@icon("Spark Loop", "line", "A thought looping back to the spark it came from.")
def spark_loop():
    path = curve([(32, 32), (40, 44), (54, 50), (70, 56), (80, 70), (72, 84), (56, 86), (48, 74), (56, 62),
                  (72, 63), (88, 69)])
    d = union(stroke(path, W * 1.25), sparkle(32, 32, 15), k=4)
    return np.minimum(d, np.minimum(sparkle(15, 58, 6), dot(24, 72, 1.8)))


@icon("Droplet Vault", "fill", "A single drop sealed around a spark and a few bubbles.")
def droplet_vault():
    d = teardrop(50, 52, 40)
    return cut(d, union(sparkle(50, 64, 15), circle(40, 45, 3), dot(57, 38, 2), k=1), k=1)


@icon("Rising Bubbles", "line", "Bubbles rising and joining; the biggest carries the spark.")
def rising_bubbles():
    d = union(ring(circle(48, 86, 5)), ring(circle(56, 71, 8)), ring(circle(45, 51, 11.5)),
              ring(circle(60, 25, 15.5)), k=J)
    return np.minimum(d, np.minimum(sparkle(60, 25, 8.5),
                                    np.minimum(dot(33, 72, 2), dot(66, 90, 1.8))))


@icon("Seed Cluster", "fill", "Memories budding off a core; some cells still empty.")
def seed_cluster():
    blobs, holes = [circle(50, 50, 14)], [sparkle(50, 50, 8.5)]
    for ang, r in [(-90, 9), (-30, 10), (30, 8.5), (90, 10), (150, 9), (210, 7.5)]:
        dist = 14 + r + 5
        cx, cy = 50 + dist * math.cos(math.radians(ang)), 50 + dist * math.sin(math.radians(ang))
        blobs.append(circle(cx, cy, r))
        if ang in (-30, 150):
            holes.append(circle(cx, cy, 3.5))
    return cut(union(*blobs, k=12), union(*holes), k=1)


@icon("Puddle Ripples", "line", "A memory drop falling back into the pool it came from.")
def puddle_ripples():
    ball = cut(circle(50, 36, 13), star(50, 36.5, 6.5, inner=0.48, tip=1, notch=1), k=0.8)
    drop = union(ball, capsule((50, 44), (50, 76), 1.6), k=6)
    d = union(ring(ellipse(50, 80, 38, 10)), ring(ellipse(50, 80, 20, 4.6)), drop, k=4)
    return np.minimum(d, np.minimum(dot(30, 62, 2.4), np.minimum(dot(69, 58, 2),
                                                                   dot(76, 66, 1.4))))


@icon("Spark Emerging", "fill", "Recall: a spark pulling itself out of the orb.")
def spark_emerging():
    d = union(circle(41, 61, 27), sparkle(69, 31, 17), k=13)
    d = cut(d, union(circle(32, 70, 4.5), dot(46, 78, 2.6)), k=1)
    return np.minimum(d, np.minimum(dot(86, 54, 2.4), dot(88, 12, 1.8)))


@icon("Acid Spiral", "line", "A memory winding out from its spark and pooling at the end.")
def acid_spiral():
    turns = np.linspace(0, 3.25 * math.pi, 420)
    r = 7 + 29 * turns / turns[-1]
    a = turns - math.pi / 2
    path = np.c_[50 + r * np.cos(a), 50 + r * np.sin(a)]
    return union(stroke(path, W * 1.1), sparkle(50, 50, 6.5), circle(*path[-1], 5), k=4)


# ---------------------------------------------------------------- tracing

def trace(F):
    """Marching squares: closed loops of points where F crosses zero."""
    inside = F < 0
    case = (inside[:-1, :-1] * 8 | inside[:-1, 1:] * 4 | inside[1:, 1:] * 2 | inside[1:, :-1] * 1)
    T, R, B, L = "T", "R", "B", "L"
    table = {1: [(L, B)], 2: [(B, R)], 3: [(L, R)], 4: [(T, R)], 6: [(T, B)], 7: [(L, T)],
             8: [(L, T)], 9: [(T, B)], 11: [(T, R)], 12: [(L, R)], 13: [(B, R)], 14: [(L, B)]}

    def key(side, i, j):
        return {"T": ("h", i, j), "B": ("h", i + 1, j), "L": ("v", i, j), "R": ("v", i, j + 1)}[side]

    nbrs = {}
    for i, j in np.argwhere((case > 0) & (case < 15)):
        c = int(case[i, j])
        if c in (5, 10):
            centre = (F[i, j] + F[i, j + 1] + F[i + 1, j] + F[i + 1, j + 1]) < 0
            if c == 5:
                segs = [(L, T), (B, R)] if centre else [(L, B), (T, R)]
            else:
                segs = [(T, R), (L, B)] if centre else [(L, T), (B, R)]
        else:
            segs = table[c]
        for s1, s2 in segs:
            k1, k2 = key(s1, i, j), key(s2, i, j)
            nbrs.setdefault(k1, []).append(k2)
            nbrs.setdefault(k2, []).append(k1)

    def point(k):
        kind, i, j = k
        if kind == "h":
            t = F[i, j] / (F[i, j] - F[i, j + 1])
            return ((j + t) * STEP, i * STEP)
        t = F[i, j] / (F[i, j] - F[i + 1, j])
        return (j * STEP, (i + t) * STEP)

    loops, seen = [], set()
    for start in nbrs:
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while cur not in seen:
            seen.add(cur)
            loop.append(point(cur))
            nxt = [n for n in nbrs[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
        pts = np.array(loop)
        keep_ = np.r_[True, np.hypot(*np.diff(pts, axis=0).T) > 1e-3]
        pts = pts[keep_]
        area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], 1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], 1)))
        if len(pts) > 8 and area > 0.4:
            loops.append(pts)
    return loops


# ---------------------------------------------------------------- Bézier fitting (Schneider)

def _bez(c, t):
    t = t[:, None]
    mt = 1 - t
    return mt ** 3 * c[0] + 3 * mt * mt * t * c[1] + 3 * mt * t * t * c[2] + t ** 3 * c[3]


def _bez1(c, t):
    t = t[:, None]
    mt = 1 - t
    return 3 * (mt * mt * (c[1] - c[0]) + 2 * mt * t * (c[2] - c[1]) + t * t * (c[3] - c[2]))


def _bez2(c, t):
    t = t[:, None]
    return 6 * ((1 - t) * (c[2] - 2 * c[1] + c[0]) + t * (c[3] - 2 * c[2] + c[1]))


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def _generate(d, u, t1, t2):
    p0, p3 = d[0], d[-1]
    uu = u[:, None]
    b0, b1, b2, b3 = (1 - uu) ** 3, 3 * uu * (1 - uu) ** 2, 3 * uu * uu * (1 - uu), uu ** 3
    a1, a2 = t1 * b1, t2 * b2
    c = np.array([[np.sum(a1 * a1), np.sum(a1 * a2)], [np.sum(a1 * a2), np.sum(a2 * a2)]])
    tmp = d - (b0 + b1) * p0 - (b2 + b3) * p3
    x = np.array([np.sum(a1 * tmp), np.sum(a2 * tmp)])
    seg = np.linalg.norm(p3 - p0)
    det = c[0, 0] * c[1, 1] - c[0, 1] * c[1, 0]
    al = ar = seg / 3
    if abs(det) > 1e-12:
        l_ = (x[0] * c[1, 1] - x[1] * c[0, 1]) / det
        r_ = (c[0, 0] * x[1] - c[1, 0] * x[0]) / det
        if l_ > 1e-6 * seg and r_ > 1e-6 * seg:
            al, ar = l_, r_
    return np.array([p0, p0 + t1 * al, p3 + t2 * ar, p3])


TAN_SPAN = 6  # points either side used to estimate a tangent (~0.75 units)


def _fit(d, t1, t2, err, out):
    if len(d) == 2:
        dist = np.linalg.norm(d[1] - d[0]) / 3
        out.append(np.array([d[0], d[0] + t1 * dist, d[1] + t2 * dist, d[1]]))
        return
    u = np.r_[0, np.cumsum(np.hypot(*np.diff(d, axis=0).T))]
    u /= u[-1]
    bez = _generate(d, u, t1, t2)
    for attempt in range(21):
        e = np.sum((_bez(bez, u) - d) ** 2, axis=1)
        split = int(np.argmax(e[1:-1])) + 1
        if e[split] < err:
            out.append(bez)
            return
        if e[split] > err * 4 or attempt == 20:
            break
        q, q1, q2 = _bez(bez, u) - d, _bez1(bez, u), _bez2(bez, u)
        den = np.sum(q1 * q1, axis=1) + np.sum(q * q2, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            u = np.clip(np.where(den != 0, u - np.sum(q * q1, axis=1) / den, u), 0, 1)
        u = np.maximum.accumulate(u)
        bez = _generate(d, u, t1, t2)
    s = min(TAN_SPAN, split, len(d) - 1 - split)
    tc = _unit(d[split - s] - d[split + s])
    _fit(d[:split + 1], t1, tc, err, out)
    _fit(d[split:], -tc, t2, err, out)


def _corners(pts, span=3, limit=65):
    a = pts - np.roll(pts, span, axis=0)
    b = np.roll(pts, -span, axis=0) - pts
    cos = np.sum(a * b, axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    turn = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    found = []
    for i in np.argsort(-turn):
        if turn[i] < limit:
            break
        if all(min(abs(i - j), len(pts) - abs(i - j)) > span * 3 for j in found):
            found.append(int(i))
    return sorted(found)


def fit_loop(pts, err=0.02):
    # The traced points carry a little grid noise; smooth it so tangents stay true.
    for _ in range(3):
        pts = (np.roll(pts, 1, axis=0) + 2 * pts + np.roll(pts, -1, axis=0)) / 4
    corners = _corners(pts)
    out = []
    if not corners:
        d = np.vstack([pts, pts[:1]])
        t1 = _unit(pts[TAN_SPAN] - pts[-TAN_SPAN])
        _fit(d, t1, -t1, err, out)
        return out
    pts = np.roll(pts, -corners[0], axis=0)
    cuts = [c - corners[0] for c in corners] + [len(pts)]
    ring_ = np.vstack([pts, pts[:1]])
    for s, e in zip(cuts[:-1], cuts[1:]):
        d = ring_[s:e + 1]
        k = min(TAN_SPAN, len(d) - 1)
        _fit(d, _unit(d[k] - d[0]), _unit(d[-1 - k] - d[-1]), err, out)
    return out


def to_path(loops, scale=1.0):
    def f(v):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return "0" if s == "-0" else s

    parts = []
    for beziers in loops:
        beziers = [b * scale for b in beziers]
        p0 = beziers[0][0]
        cmd = [f"M{f(p0[0])} {f(p0[1])}"]
        for b in beziers:
            cmd.append("C" + " ".join(f"{f(x)} {f(y)}" for x, y in b[1:]))
        parts.append("".join(cmd) + "Z")
    return "".join(parts)


# ---------------------------------------------------------------- output

def slug(n, name):
    return f"{n:02d}-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build(entry, weight="regular"):
    globals().update(WEIGHTS[weight])
    field = entry["fn"]()
    if entry["kind"] == "fill":
        field = field - GROW
    loops = trace(field)
    allpts = np.vstack(loops)
    shift = 50 - (allpts.min(axis=0) + allpts.max(axis=0)) / 2  # centre in the viewBox
    return [fit_loop(p + shift) for p in loops]


def write_svg(path, n, entry, d, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        f'  <title>Lava {n:02d} · {entry["name"]}</title>\n'
        f'  <path fill="currentColor" fill-rule="evenodd" d="{d}"/>\n'
        "</svg>\n")


def main():
    """svg/ holds the 100-unit masters (svg/bold/ for Bold); svg/32/ the same icons drawn at 32x32."""
    sprite, cards = [], []
    for n, entry in enumerate(ICONS, 1):
        name = slug(n, entry["name"])
        for weight, folder, sym in (("regular", "", "i"), ("bold", "bold/", "b")):
            loops = build(entry, weight)
            d = to_path(loops)
            write_svg(HERE / "svg" / f"{folder}{name}.svg", n, entry, d, 100)
            write_svg(HERE / "svg" / "32" / weight / f"{name}.svg", n, entry, to_path(loops, 0.32), 32)
            sprite.append(f'<symbol id="{sym}{n:02d}" viewBox="0 0 100 100"><path fill-rule="evenodd" d="{d}"/></symbol>')
            print(f"{name} {weight}: {d.count('C')} curves")
        use = f'<svg viewBox="0 0 100 100" aria-hidden="true"><use href="#i{n:02d}"/></svg>'
        cards.append(
            f'<figure class="card" data-kind="{entry["kind"]}">\n'
            f'  <div class="stage">{use}</div>\n'
            f'  <div class="sizes"><span class="tile">{use}</span><span class="s32">{use}</span>'
            f'<span class="s16">{use}</span></div>\n'
            f'  <figcaption><div class="title"><span class="num">{n:02d}</span> <b>{entry["name"]}</b>'
            f' <span class="tag">{"Filled" if entry["kind"] == "fill" else "Outline"}</span></div>'
            f'<p>{entry["note"]}</p><a href="svg/{name}.svg" download>{name}.svg</a></figcaption>\n'
            "</figure>")

    html_path = HERE / "index.html"
    html = html_path.read_text()
    block = ('<svg class="sprite" aria-hidden="true">\n' + "\n".join(sprite) + "\n</svg>\n"
             '<main class="grid">\n' + "\n".join(cards) + "\n</main>")
    html = re.sub(r"(<!-- icons:start -->\n).*?(<!-- icons:end -->)",
                  lambda m: m.group(1) + block + "\n" + m.group(2), html, flags=re.S)
    html_path.write_text(html)


if __name__ == "__main__":
    main()
