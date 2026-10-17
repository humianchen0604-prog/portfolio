/* Lava Voice: 20 liquid listening icons.
 *
 * Each icon is a recipe make(t, a) that returns a signed distance field
 * f(x, y) over a 100-unit square (negative inside). t is time in seconds and
 * a is how much the icon is listening, from 0 (idle) to 1 (listening). Shapes
 * are joined with smooth unions, so blobs melt into each other as they move.
 *
 * The gallery traces the field every frame (contour); export.py traces it once
 * at each icon's pose and fits Béziers for the static SVGs.
 */
(function (root) {
  'use strict';
  const { abs, min, max, hypot, sin, cos, PI, pow, floor, atan2 } = Math;
  const TAU = PI * 2;
  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
  const lerp = (p, q, t) => p + (q - p) * t;
  const frac = v => v - floor(v);

  // ------------------------------------------------------------ shapes

  function smin(p, q, k) {
    if (k <= 0) return p < q ? p : q;
    const h = clamp(0.5 + 0.5 * (q - p) / k, 0, 1);
    return q + (p - q) * h - k * h * (1 - h);
  }

  const circle = (cx, cy, r) => (x, y) => hypot(x - cx, y - cy) - r;

  function ellipse(cx, cy, rx, ry, rot = 0) {
    const c = cos(rot), s = sin(rot);
    return (x, y) => {
      const dx = x - cx, dy = y - cy;
      const u = (dx * c + dy * s) / rx, v = (-dx * s + dy * c) / ry;
      const k0 = hypot(u, v), k1 = hypot(u / rx, v / ry);
      return k1 > 1e-9 ? k0 * (k0 - 1) / k1 : -min(rx, ry);
    };
  }

  function capsule(ax, ay, bx, by, r) {
    const ex = bx - ax, ey = by - ay, ll = ex * ex + ey * ey || 1e-9;
    return (x, y) => {
      const wx = x - ax, wy = y - ay;
      const t = clamp((wx * ex + wy * ey) / ll, 0, 1);
      return hypot(wx - ex * t, wy - ey * t) - r;
    };
  }

  /** A round-ended stroke of width w along a polyline [[x, y], ...]. */
  function stroke(pts, w) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [x, y] of pts) { x0 = min(x0, x); y0 = min(y0, y); x1 = max(x1, x); y1 = max(y1, y); }
    const n = pts.length - 1;
    return (x, y) => {
      const box = hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1));
      if (box > 14) return box - w / 2;
      let d2 = Infinity;
      for (let i = 0; i < n; i++) {
        const ax = pts[i][0], ay = pts[i][1];
        const ex = pts[i + 1][0] - ax, ey = pts[i + 1][1] - ay;
        const wx = x - ax, wy = y - ay, ll = ex * ex + ey * ey || 1e-9;
        const t = clamp((wx * ex + wy * ey) / ll, 0, 1);
        const dx = wx - ex * t, dy = wy - ey * t, dd = dx * dx + dy * dy;
        if (dd < d2) d2 = dd;
      }
      return Math.sqrt(d2) - w / 2;
    };
  }

  /** Four-point sparkle with pinched sides (an Lq ball with q < 1). */
  function sparkle(cx, cy, R, rot = 0, q = 0.62, round = 0.9) {
    const c = cos(rot), s = sin(rot), Rr = R - round, iq = 1 / q, e = 0.3;
    const F = (x, y) => {
      const dx = x - cx, dy = y - cy;
      const u = abs(dx * c + dy * s), v = abs(-dx * s + dy * c);
      return pow(pow(u, q) + pow(v, q), iq) - Rr;
    };
    return (x, y) => {
      const f = F(x, y);
      if (f > 14) return f - round;
      const g = hypot(F(x + e, y) - F(x - e, y), F(x, y + e) - F(x, y - e)) / (2 * e);
      return f / max(g, 0.5) - round;
    };
  }

  /** A blob whose radius follows r(theta); keep the wobble gentle. */
  const radial = (cx, cy, r) => (x, y) => (hypot(x - cx, y - cy) - r(atan2(y - cy, x - cx))) * 0.8;

  /** A filled band of width w along the edge of another shape. */
  const band = (f, w) => (x, y) => abs(f(x, y)) - w / 2;

  function union(fs, k = 0) {
    return (x, y) => {
      let d = fs[0](x, y);
      for (let i = 1; i < fs.length; i++) d = smin(d, fs[i](x, y), k);
      return d;
    };
  }
  const cut = (f, g, k = 0) => (x, y) => -smin(-f(x, y), g(x, y), k);

  /** A run of liquid from (x, y0) down to a round bead at y1. */
  const drip = (x, y0, y1, w, bead) => union([capsule(x, y0, x, y1, w), circle(x, y1, bead)], 3);

  // ------------------------------------------------------------ voice

  /** A made-up voice: syllable-like swells between 0 and 1. */
  function speech(t, s) {
    return clamp(0.5 + 0.32 * sin(3.1 * t + s) * sin(1.27 * t + 0.7 * s + 1)
      + 0.22 * sin(7.3 * t + 2.3 * s) + 0.1 * sin(11.9 * t + 4.1 * s), 0, 1);
  }

  /** How loud part s of an icon is: a slow breath when idle, speech when listening. */
  const level = (t, a, s) => lerp(0.32 + 0.12 * sin(1.7 * t + 1.3 * s), speech(t, s), a);

  const wave = (n, f) => Array.from({ length: n + 1 }, (_, i) => f(i / n));

  /** Smooth Catmull-Rom curve through the points, as a polyline. */
  function spline(pts, per = 6) {
    const p = [pts[0], ...pts, pts[pts.length - 1]], out = [];
    for (let i = 1; i < p.length - 2; i++) {
      const [p0, p1, p2, p3] = [p[i - 1], p[i], p[i + 1], p[i + 2]];
      for (let k = 0; k < per; k++) {
        const t = k / per, t2 = t * t, t3 = t2 * t;
        out.push([0, 1].map(d => 0.5 * (2 * p1[d] + (p2[d] - p0[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2
          + (3 * p1[d] - p0[d] - 3 * p2[d] + p3[d]) * t3)));
      }
    }
    out.push(pts[pts.length - 1]);
    return out;
  }

  // ------------------------------------------------------------ icons

  const ICONS = [
    {
      name: 'Blob Choir', note: 'Seven voices melting into one chord.',
      make(t, a) {
        const fs = [];
        for (let i = -3; i <= 3; i++) {
          const L = level(t, a, i * 0.9 + (i < 0 ? 0.4 : 0)), k = abs(i);
          if (k === 0) { fs.push(ellipse(50, 50, 12 + 2 * L, 13 + 11 * L)); continue; }
          const x = 50 + Math.sign(i) * [0, 15, 26, 35][k];
          fs.push(ellipse(x, 50, [0, 6, 4.5, 3][k], [0, 22, 15, 9][k] * (0.5 + 0.7 * L)));
        }
        return union(fs, 4.5);
      },
    },
    {
      name: 'Gooey Ridge', note: 'A waveform pulled up out of a thin line of liquid.',
      make(t, a) {
        const up1 = 10 + 26 * level(t, a, 0.3), dn1 = 10 + 30 * level(t, a, 1.1);
        const up2 = 6 + 16 * level(t, a, 2.1), dn2 = 6 + 18 * level(t, a, 4.0);
        return union([
          capsule(10, 50, 90, 50, 1.4),
          ellipse(40, 50 + (dn1 - up1) / 2, 10, (up1 + dn1) / 2),
          ellipse(65, 50 + (dn2 - up2) / 2, 7, (up2 + dn2) / 2),
        ], 7);
      },
    },
    {
      name: 'Noodle Speaker', note: 'A wobbling noodle of sound beside its speaker.',
      make(t, a) {
        const ph = t * (1.2 + 3 * a), A = 10 + 9 * level(t, a, 0.5), L = level(t, a, 2);
        const pts = wave(40, s => [14 + 50 * s, 50 + A * sin(TAU * 1.75 * s - ph) * (0.4 + 0.6 * sin(PI * s))]);
        return (x, y) => min(stroke(pts, 7.5)(x, y), ellipse(80, 50, 8 + 1.5 * L, 11 + 4 * L)(x, y));
      },
    },
    {
      name: 'Fading Pills', note: 'Pills that swell in turn and melt together when you speak.',
      make(t, a) {
        const xs = [17, 30, 45, 61, 78], rx = [2.2, 3.6, 5, 5.8, 8.5], ry = [9, 17, 23, 17, 9.5];
        const fs = xs.map((x, i) => {
          const L = level(t - i * 0.12, a, i * 0.8);
          return i === 4 ? ellipse(x, 50, rx[i], ry[i] + 2 * L) : ellipse(x, 50, rx[i], ry[i] * (0.55 + 0.75 * L));
        });
        return union(fs, 7 * a);
      },
    },
    {
      name: 'Melting Mic', note: 'A microphone dripping its words into a puddle.',
      make(t, a) {
        const head = cut(capsule(50, 21, 50, 45, 15),
          union([22, 30, 38].map(y => capsule(43, y, 57, y, 1.6))), 1);
        const drips = [[-7, 0], [0, 1.3], [7, 2.4]].map(([dx, s]) => drip(50 + dx, 52, 62 + 18 * level(t, a, s), 2.3, 3.4));
        return union([head, ...drips, ellipse(50, 87, 22, 4)], 4);
      },
    },
    {
      name: 'Lava Mic', note: 'A microphone with lava rising inside it.',
      make(t, a) {
        const sp = 0.12 + 0.45 * a;
        const blobs = [0, 1, 2].map(i => {
          const p = frac(t * sp + i / 3);
          return circle(50 + 5 * sin(t * 1.3 + i * 2), 60 - 46 * p, 4 + 2.5 * sin(PI * p) + 1.5 * level(t, a, i));
        });
        const head = cut(capsule(50, 22, 50, 46, 15), union(blobs, 6), 1.5);
        const arc = stroke(wave(24, s => [50 + 22 * cos(PI * s), 46 + 22 * sin(PI * s)]), 5);
        return (x, y) => min(head(x, y), union([arc, capsule(50, 68, 50, 80, 2.6), capsule(38, 82, 62, 82, 3)], 3)(x, y));
      },
    },
    {
      name: 'Orbit Choir', note: 'Moons of sound that touch the core and pull away.',
      make(t, a) {
        const fs = [circle(50, 50, 13 + 5 * level(t, a, 0))];
        for (let i = 0; i < 3; i++) {
          const ang = t * (0.5 + 1.6 * a) + i * TAU / 3, R = 30 + 5 * level(t, a, i + 1);
          fs.push(circle(50 + R * cos(ang), 50 + R * 0.75 * sin(ang), 6 + 2 * level(t, a, i * 2)));
        }
        return union(fs, 9);
      },
    },
    {
      name: 'Talking Drop', note: 'A drop with a face, mouthing along as you talk.',
      make(t, a) {
        const L = level(t, a, 0.4), blink = frac(t * 0.27) > 0.96 ? 0.25 : 1;
        const body = union([circle(50, 60, 24), capsule(50, 58, 50, 21, 3)], 14);
        const face = union([ellipse(50, 67, 10 - 2 * L, 1.2 + 8 * L), ellipse(41, 53, 2.6, 2.8 * blink), ellipse(59, 53, 2.6, 2.8 * blink)]);
        return cut(body, face, 1);
      },
    },
    {
      name: 'Drip EQ', note: 'An equaliser that drips instead of bouncing.',
      make(t, a) {
        const drips = [0, 1, 2, 3, 4, 5].map(i => drip(22 + i * 11.2, 24, 36 + 40 * level(t, a, i * 0.9), 2.8, 4.2));
        return union([capsule(16, 24, 84, 24, 5), ...drips], 5);
      },
    },
    {
      name: 'Splash Rings', note: 'Each word lands like a drop and ripples out.',
      make(t, a) {
        const fs = [circle(50, 50, 9 + 3 * level(t, a, 0))];
        for (let i = 0; i < 3; i++) {
          const p = frac(t * (0.25 + 0.55 * a) + i / 3);
          const w = 6 * pow(1 - p, 1.2) * (0.4 + 0.6 * max(a, 0.35));
          if (w > 1.4) fs.push(band(circle(50, 50, 14 + 28 * p), w));
        }
        return union(fs, 4);
      },
    },
    {
      name: 'Wave Ring', note: 'A ring whose rim ripples with your voice.',
      make(t, a) {
        const L = level(t, a, 0);
        const outer = radial(50, 50, th => 30 + (1.5 + 4.5 * L) * sin(5 * th + 2 * t) + (1 + 3 * a) * sin(8 * th - 3.1 * t) + 1.2 * sin(3 * th + 0.7 * t));
        const inner = radial(50, 50, th => 13 + (0.6 + 2 * a) * sin(4 * th - 2 * t));
        const ring = cut(outer, inner, 1.5);
        return (x, y) => min(ring(x, y), circle(50, 50, 4 + 2 * L)(x, y));
      },
    },
    {
      name: 'Spark Speaker', note: 'The memory spark singing out on both sides.',
      make(t, a) {
        const fs = [sparkle(50, 50, 15 + 4 * level(t, a, 0), 0.25 * sin(t * 0.8))];
        for (const side of [-1, 1]) {
          for (let j = 0; j < 3; j++) {
            const x = 50 + side * (23 + j * 9), h = (14 - j * 3) * (0.4 + 0.8 * level(t, a, j * 1.1 + (side > 0 ? 0.5 : 0)));
            fs.push(capsule(x, 50 - h, x, 50 + h, 3 - j * 0.4));
          }
        }
        return union(fs, 5);
      },
    },
    {
      name: 'Chatter Bubble', note: 'A speech bubble with three dots bouncing inside.',
      make(t, a) {
        const bubble = union([circle(50, 46, 30), circle(30, 72, 7)], 10);
        const dots = union([0, 1, 2].map(i => circle(37 + i * 13, 46 - 7 * abs(sin(t * (2 + 4 * a) + i * 0.9)) * (0.3 + 0.7 * a), 4.6)));
        const body = cut(bubble, dots, 1);
        return (x, y) => min(body(x, y), circle(21, 83, 3.2)(x, y));
      },
    },
    {
      name: 'Sound Bloom', note: 'Petals that open wider the louder you speak.',
      make(t, a) {
        const rot = t * 0.15 * (1 + 2 * a), fs = [circle(50, 50, 9)];
        for (let i = 0; i < 6; i++) {
          const ang = rot + i * TAU / 6, len = 12 + 16 * level(t, a, i * 1.05), c = 7 + len / 2;
          fs.push(ellipse(50 + c * cos(ang), 50 + c * sin(ang), len / 2 + 3, 5.5, ang));
        }
        return cut(union(fs, 6), circle(50, 50, 4), 1);
      },
    },
    {
      name: 'Helix Voice', note: 'Two strands of sound twisting around each other.',
      make(t, a) {
        const ph = t * (1 + 3 * a), A = 7 + 11 * level(t, a, 0.7);
        const strand = s => stroke(wave(36, u => [12 + 76 * u, 50 + s * A * pow(sin(PI * u), 0.8) * sin(TAU * 1.25 * u - ph)]), 7);
        return union([strand(1), strand(-1)], 3);
      },
    },
    {
      name: 'Puddle Bars', note: 'Bars rising out of a puddle and sinking back in.',
      make(t, a) {
        const bars = [0, 1, 2, 3].map(i => capsule(29 + i * 14, 70 - (10 + 40 * level(t, a, i * 1.2)), 29 + i * 14, 80, 5));
        return union([ellipse(50, 80, 36, 6.5), ...bars], 7);
      },
    },
    {
      name: 'Listening Ear', note: 'An ear drinking in drops of sound.',
      make(t, a) {
        const curl = stroke(spline([[40, 76], [47, 83], [56, 82], [61, 74], [62, 64], [69, 56], [75, 44], [73, 30],
          [64, 20], [51, 17], [40, 23], [36, 33]]), 10);
        const fold = union([circle(55, 43, 5.5 + 1.5 * level(t, a, 3)), capsule(55, 43, 50, 57, 2.6)], 3);
        const sp = 0.3 + 0.6 * a;
        const drops = [0, 1, 2].map(i => {
          const p = frac(t * sp + i / 3);
          return circle(8 + 24 * p, 38 + 3 * sin(TAU * p + i), 2.5 + 2 * level(t, a, i) * sin(PI * p));
        });
        return union([curl, fold, ...drops], 6);
      },
    },
    {
      name: 'Bounce Trio', note: 'Three drops bouncing off a liquid floor.',
      make(t, a) {
        const fs = [capsule(14, 82, 86, 82, 4)];
        [28, 50, 72].forEach((x, i) => {
          const top = 6 + 34 * level(t, a, i * 1.4), p = frac(t * (0.8 + 1.2 * a) + i * 0.33);
          const h = top * 4 * p * (1 - p), r = 8.5, sq = 0.28 * (1 - min(1, h / 4));
          fs.push(ellipse(x, 82 - 4 - r * (1 - sq) - h, r * (1 + sq), r * (1 - sq)));
        });
        return union(fs, 7);
      },
    },
    {
      name: 'Melting Wave', note: 'A sound wave so loud it starts to drip.',
      make(t, a) {
        const ph = t * (0.8 + 2.5 * a), A = 4 + 7 * level(t, a, 0.3);
        const y = x => 38 + A * sin(TAU * 1.2 * (x - 12) / 76 - ph);
        const drips = [26, 44, 62, 78].map((x, i) => drip(x, y(x), y(x) + 10 + 22 * level(t, a, i * 0.9 + 0.4), 2.4, 3.8));
        return union([stroke(wave(36, u => [12 + 76 * u, y(12 + 76 * u)]), 11), ...drips], 5);
      },
    },
    {
      name: 'Spark Amoeba', note: 'A restless blob holding the spark it heard.',
      make(t, a) {
        const L = level(t, a, 0);
        const blob = radial(50, 50, th => 27 + 1.5 * sin(3 * th + 0.9 * t)
          + L * (3.5 * sin(3 * th + 1.3 * t) + 2.5 * sin(5 * th - 2.1 * t) + 1.8 * sin(7 * th + 3.1 * t)));
        const moon = circle(50 + 36 * cos(t * 0.7), 50 + 36 * sin(t * 0.7), 3.5 + a);
        return union([cut(blob, sparkle(50, 50, 11 + 2 * L, t * 0.4), 1), moon], 8);
      },
    },
  ];

  // ------------------------------------------------------------ 04, linked

  /** The five pills of 04 Fading Pills at time t: centre x, radii and loudness. */
  function pills(t, a, dy = () => 0, thin = 1) {
    const xs = [17, 30, 45, 61, 78], rx = [2.2, 3.6, 5, 5.8, 8.5].map(r => r * thin), ry = [11, 20, 27, 20, 9.5];
    return xs.map((x, i) => {
      const L = level(t - i * 0.12, a, i * 0.8);
      return { x, y: 50 + dy(i), rx: rx[i], ry: i === 4 ? ry[i] + 2 * L : ry[i] * (0.55 + 0.75 * L), L };
    });
  }
  const pillShapes = ps => ps.map(p => ellipse(p.x, p.y, p.rx, p.ry));

  /** Variations on 04 where the pills are joined to each other. */
  const VARIANTS = [
    {
      id: '04a', name: 'Acid Thread', note: 'Pills strung on a thread of acid that flares where it meets them.',
      make(t, a) {
        const ps = pills(t, a, () => 0, 0.75);
        const threads = ps.slice(1).map((p, i) => capsule(ps[i].x, 50, p.x, 50, 0.7 + 0.6 * (ps[i].L + p.L) / 2));
        return union([...pillShapes(ps), ...threads], 2.5);
      },
    },
    {
      id: '04b', name: 'Taffy', note: 'Stretchy necks between pills that thin, snap and join again.',
      make(t, a) {
        const ps = pills(t, a, () => 0, 0.9), sp = 0.7 + 1.4 * a;
        const necks = ps.slice(1).flatMap((p, i) => {
          const pull = abs(sin(t * sp + i * 1.7));
          const w = 1.2 + 2.6 * (1 - pull), sag = 4 + 14 * pull;
          if (w < 1.5) return [];
          const q = ps[i], y0 = 50 + q.ry * 0.35;
          return [stroke(wave(10, u => [lerp(q.x, p.x, u), y0 + sag * sin(PI * u)]), w)];
        });
        return union([...pillShapes(ps), ...necks], 4);
      },
    },
    {
      id: '04c', name: 'Bead Chain', note: 'Droplets bob in the gaps and link the pills like a chain.',
      make(t, a) {
        const ps = pills(t, a, () => 0, 0.7);
        const beads = ps.slice(1).map((p, i) => circle((ps[i].x + p.x) / 2,
          50 + (i % 2 ? 1 : -1) * (7 + 3 * sin(t * (1.6 + 3 * a) + i)), 2.8 + 1.4 * level(t, a, i * 1.7)));
        return union([...pillShapes(ps), ...beads], 3);
      },
    },
    {
      id: '04d', name: 'Melt Bridge', note: 'The pills fuse into one slab that drips between them.',
      make(t, a) {
        const ps = pills(t, a);
        const drips = ps.slice(1).map((p, i) => {
          const x = (ps[i].x + p.x) / 2;
          return drip(x, 52, 62 + 22 * level(t, a, i * 1.3 + 0.5), 2, 3.2);
        });
        const slab = union([...pillShapes(ps), capsule(17, 50, 78, 50, 4), ...drips], 8);
        const pits = union([0, 1, 2, 3].map(i => {
          const p = frac(t * (0.1 + 0.3 * a) + i / 4);
          return circle(24 + i * 15 + 3 * sin(t + i), 56 - 14 * p, 1.2 + 1.2 * sin(PI * p));
        }));
        return cut(slab, pits, 1);
      },
    },
    {
      id: '04e', name: 'Acid Membrane', note: 'The pills live inside a liquid skin and push at it when you speak.',
      make(t, a) {
        const ps = pills(t, a), inner = union(pillShapes(ps), 10);
        const skin = band((x, y) => inner(x, y) - 5.5, 2.6);
        return union([...pillShapes(ps), skin], 2.5);
      },
    },
    {
      id: '04f', name: 'Zigzag Ladder', note: 'Pills step up and down, joined by diagonal rungs.',
      make(t, a) {
        const off = i => (i % 2 ? 1 : -1) * (9 + 4 * sin(t * (0.9 + 2 * a) + i));
        const ps = pills(t, a, off);
        const rungs = ps.slice(1).map((p, i) => {
          const q = ps[i], up = q.y < p.y;
          return capsule(q.x, q.y + (up ? 1 : -1) * q.ry * 0.55, p.x, p.y + (up ? -1 : 1) * p.ry * 0.55, 1.6 + 0.9 * q.L);
        });
        return union([...pillShapes(ps), ...rungs], 3.5);
      },
    },
  ];

  /** The frame used for the static SVGs and the still preview. */
  const POSE = { t: 1, a: 0.65 };

  // ------------------------------------------------------------ tracing

  /**
   * The field on an (n+1)^2 grid. Unless exact, it is read first on a grid four
   * times coarser, and points whose coarse neighbour is far from any edge take
   * that value: a distance field cannot change sign within that reach.
   */
  function sample(f, n, exact) {
    const m = n + 1, step = 100 / n, F = new Float64Array(m * m), c = 4;
    if (exact || n % c) {
      for (let j = 0; j < m; j++) for (let i = 0; i < m; i++) F[j * m + i] = f(i * step, j * step);
      return F;
    }
    const cm = n / c + 1, C = new Float64Array(cm * cm), reach = c * step * 1.5;
    for (let J = 0; J < cm; J++) for (let I = 0; I < cm; I++) C[J * cm + I] = f(I * c * step, J * c * step);
    for (let j = 0; j < m; j++) {
      const J = Math.round(j / c);
      for (let i = 0; i < m; i++) {
        const v = C[J * cm + Math.round(i / c)];
        F[j * m + i] = abs(v) > reach ? v : f(i * step, j * step);
      }
    }
    return F;
  }

  /**
   * Marching squares over an n x n grid of cells covering the 100-unit square.
   * Returns closed loops as flat [x0, y0, x1, y1, ...] arrays.
   */
  function contour(f, n, exact = false) {
    const m = n + 1, step = 100 / n, F = sample(f, n, exact);
    const adj = new Int32Array(m * m * 4).fill(-1);
    const link = (e1, e2) => {
      adj[e1 * 2 + (adj[e1 * 2] < 0 ? 0 : 1)] = e2;
      adj[e2 * 2 + (adj[e2 * 2] < 0 ? 0 : 1)] = e1;
    };
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const o = j * m + i;
        const tl = F[o], tr = F[o + 1], br = F[o + m + 1], bl = F[o + m];
        const c = (tl < 0) << 3 | (tr < 0) << 2 | (br < 0) << 1 | (bl < 0);
        if (c === 0 || c === 15) continue;
        const T = o * 2, B = (o + m) * 2, L = o * 2 + 1, R = (o + 1) * 2 + 1;
        switch (c) {
          case 1: case 14: link(L, B); break;
          case 2: case 13: link(B, R); break;
          case 3: case 12: link(L, R); break;
          case 4: case 11: link(T, R); break;
          case 6: case 9: link(T, B); break;
          case 7: case 8: link(L, T); break;
          case 5: if (tl + tr + br + bl < 0) { link(L, T); link(B, R); } else { link(L, B); link(T, R); } break;
          case 10: if (tl + tr + br + bl < 0) { link(T, R); link(L, B); } else { link(L, T); link(B, R); } break;
        }
      }
    }
    const point = (e, out) => {
      const o = e >> 1;
      if ((e & 1) === 0) { const t = F[o] / (F[o] - F[o + 1]); out.push(((o % m) + t) * step, floor(o / m) * step); }
      else { const t = F[o] / (F[o] - F[o + m]); out.push((o % m) * step, (floor(o / m) + t) * step); }
    };
    const seen = new Uint8Array(m * m * 2), loops = [];
    for (let e = 0; e < m * m * 2; e++) {
      if (adj[e * 2] < 0 || seen[e]) continue;
      const pts = [];
      let prev = -1, cur = e;
      while (cur >= 0 && !seen[cur]) {
        seen[cur] = 1;
        point(cur, pts);
        const n0 = adj[cur * 2], n1 = adj[cur * 2 + 1];
        const next = n0 !== prev && !seen[n0] ? n0 : n1 !== prev && n1 >= 0 && !seen[n1] ? n1 : -1;
        prev = cur;
        cur = next;
      }
      if (pts.length >= 6) loops.push(pts);
    }
    return loops;
  }

  /** Fill traced loops on a 2D canvas, smoothing corners with quadratic curves. */
  function fillLoops(ctx, loops, scale) {
    ctx.beginPath();
    for (const p of loops) {
      const k = p.length / 2;
      const mx = (i, j) => ((p[2 * (i % k)] + p[2 * (j % k)]) / 2) * scale;
      const my = (i, j) => ((p[2 * (i % k) + 1] + p[2 * (j % k) + 1]) / 2) * scale;
      ctx.moveTo(mx(k - 1, 0), my(k - 1, 0));
      for (let i = 0; i < k; i++) ctx.quadraticCurveTo(p[2 * i] * scale, p[2 * i + 1] * scale, mx(i, i + 1), my(i, i + 1));
      ctx.closePath();
    }
    ctx.fill('evenodd');
  }

  const api = { ICONS, VARIANTS, POSE, contour, sample, fillLoops, level, speech };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LavaVoice = api;
})(typeof window !== 'undefined' ? window : globalThis);
