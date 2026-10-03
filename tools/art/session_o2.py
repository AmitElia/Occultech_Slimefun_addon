"""Session O2: the sigils (Session B) retouched as crisp, finished pixel art - every pixel fully solid or clear (no soft
bloom), rings and lines shaded as bevelled tubes from the top-left light, a 1 px outline in each sigil's own darkest
tone, faceted gem cores, glowing rune marks in the ring band, exactly mirror-symmetric shapes.

Run: python tools/art/session_o2.py sigils
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS, hexes  # noqa: E402
from PIL import Image  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-b")
N = 64
C = 32.0                                   # the centre lies between pixels 31 and 32: mirror x <-> 63 - x
LIGHT = (-0.55, -0.62, 0.56)               # from the top-left, a little in front
_l = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _l for v in LIGHT)


def lit(n):
    """Brightness 0..1 of a surface normal (nx, ny, nz) under the light."""
    return max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])


def pick(ramp, t, lo=0, hi=None):
    hi = len(ramp) - 1 if hi is None else hi
    return ramp[max(lo, min(hi, round(lo + t * (hi - lo))))]


class Canvas:
    """A 64 px sigil: colours per pixel, plus which pixels belong to which layer (for outlines)."""

    def __init__(self):
        self.px = {}
        self.solid = set()          # pixels that get an outline round them

    def put(self, x, y, c, solid=True):
        if 0 <= x < N and 0 <= y < N:
            self.px[(x, y)] = c
            if solid:
                self.solid.add((x, y))

    def outline(self, color):
        """A 1 px outline on the empty pixels round everything solid (4-neighbours)."""
        edge = set()
        for (x, y) in self.solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in self.px and 0 <= q[0] < N and 0 <= q[1] < N:
                    edge.add(q)
        for q in edge:
            self.px[q] = color

    def image(self):
        img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for (x, y), c in self.px.items():
            img.putpixel((x, y), c[:3] + (255,))
        return img


def centre(x, y):
    return x + 0.5, y + 0.5


def ring(cv, r_in, r_out, ramp, lo=1):
    """A ring shaded as a round tube: across the band the surface turns from the inner edge over the top to the outer
    edge, so the light picks out the top-left of its crest and the inner rim of its bottom-right."""
    for y in range(N):
        for x in range(N):
            px, py = centre(x, y)
            dx, dy = px - C, py - C
            d = math.hypot(dx, dy)
            if r_in <= d <= r_out:
                u = (d - r_in) / (r_out - r_in) * 2 - 1          # -1 inner edge .. 1 outer edge
                rx, ry = dx / d, dy / d
                n = (rx * u, ry * u, math.sqrt(max(0.0, 1 - u * u)) + 0.15)
                cv.put(x, y, pick(ramp, lit(n) ** 0.9, lo=lo))


def segment(cv, a, b, w, ramp, lo=1):
    """A straight bar of width w from a to b, shaded as a tube (lit along its top-left side)."""
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    ln = math.hypot(vx, vy)
    ux, uy = vx / ln, vy / ln
    nx, ny = -uy, ux                                             # across the bar
    for y in range(N):
        for x in range(N):
            px, py = centre(x, y)
            t = (px - ax) * ux + (py - ay) * uy
            if t < -w / 2 or t > ln + w / 2:
                continue
            s = (px - ax) * nx + (py - ay) * ny
            tc = min(max(t, 0), ln)
            ex, ey = ax + ux * tc - px, ay + uy * tc - py
            if math.hypot(ex, ey) > w / 2 + 1e-6 and not (0 <= t <= ln and abs(s) <= w / 2):
                continue
            u = max(-1.0, min(1.0, s / (w / 2)))
            n = (nx * u, ny * u, math.sqrt(max(0.0, 1 - u * u)) + 0.25)
            cv.put(x, y, pick(ramp, lit(n), lo=lo))


def polyline(cv, pts, w, ramp, closed=True, lo=1):
    pairs = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    for a, b in pairs:
        segment(cv, a, b, w, ramp, lo=lo)


def polar(r, deg, cy=C):
    a = math.radians(deg - 90)
    return (C + r * math.cos(a), cy + r * math.sin(a))


def star_pts(r, n, rot=0.0, cy=C):
    return [polar(r, rot + i * 360 / n, cy) for i in range(n)]


def gem(cv, cx, cy, r, ramp):
    """A cut gem seen from above: a bright square table, eight crown facets round it - lit ones toward the top-left,
    dark ones away, light and dark alternating - a bright seam on the lit side, a white glint."""
    for y in range(N):
        for x in range(N):
            px, py = centre(x, y)
            dx, dy = px - cx, py - cy
            d = max(abs(dx), abs(dy)) * 0.7 + math.hypot(dx, dy) * 0.42      # an octagon
            if d > r:
                continue
            if max(abs(dx), abs(dy)) < r * 0.42:
                c = ramp[4] if dx + dy < 0 else ramp[3]                        # the table
            else:
                ang = math.degrees(math.atan2(dy, dx)) % 360
                k = int(((ang + 22.5) % 360) // 45)
                face = lit((math.cos(math.radians(k * 45)) * 0.8, math.sin(math.radians(k * 45)) * 0.8, 0.6))
                c = pick(ramp, face * (1.0 if k % 2 == 0 else 0.7), lo=1)
                if d > r - 1.0:
                    c = ramp[5] if dx + dy < -r * 0.5 else ramp[1]               # the girdle seam
            cv.put(x, y, c)
    gx, gy = math.floor(cx - r * 0.3), math.floor(cy - r * 0.3)
    cv.put(gx, gy, (255, 255, 255, 255))


def mark(cv, x, y, ramp, shape):
    """A small glowing rune mark: bright heart, its arms a step darker (emissive: no outline, no light)."""
    for (dx, dy) in shape:
        cv.put(x + dx, y + dy, ramp[5] if (dx, dy) == (0, 0) else ramp[4], solid=False)


MARK_PLUS = [(0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)]
MARK_X = [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]


def band_marks(cv, r, ramp, n=12):
    """Marks round the band, placed in mirrored pairs (exactly symmetric)."""
    for i in range(n):
        x, y = polar(r, i * 360 / n)
        mark(cv, math.floor(x), math.floor(y), ramp, MARK_PLUS if i % 2 == 0 else MARK_X)


def frame(cv, ramp, marks):
    """The ritual circle: a heavy outer ring, a thin inner ring, marks in the band between."""
    ring(cv, 26.5, 30.6, ramp)
    ring(cv, 21.6, 23.2, ramp)
    band_marks(cv, 24.9, marks)


def filled_star(cv, pts, ramp, bevel=3.0):
    """A solid star (polygon) bevelled along its edges: each edge's bevel faces out, the top a flat lit plateau."""
    def inside(px, py):
        c = False
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                c = not c
        return c
    for y in range(N):
        for x in range(N):
            px, py = centre(x, y)
            if not inside(px, py):
                continue
            best, bn = 1e9, None
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
                vx, vy = x2 - x1, y2 - y1
                ln = math.hypot(vx, vy)
                t = max(0, min(ln, ((px - x1) * vx + (py - y1) * vy) / ln))
                d = math.hypot(x1 + vx * t / ln - px, y1 + vy * t / ln - py)
                if d < best:
                    best, bn = d, (vy / ln, -vx / ln)
            # make the normal point outward (away from the centre)
            if bn[0] * (px - C) + bn[1] * (py - C) < 0:
                bn = (-bn[0], -bn[1])
            if best < bevel:
                k = 1 - best / bevel
                n = (bn[0] * k, bn[1] * k, 1 - k * 0.6)
                cv.put(x, y, pick(ramp, lit(n), lo=1))
            else:
                cv.put(x, y, pick(ramp, 0.78 - (px - C + py - C) * 0.006, lo=1))


# ------------------------------------------------------------------ the six sigils

def pentagram():
    """The ritual pentagram: a violet circle, a pale star of bevelled glass-silver bars, a spirit gem at its heart."""
    cv = Canvas()
    v = RAMPS["violet"]
    frame(cv, v, RAMPS["spirit"])
    pts = star_pts(21.6, 5)
    polyline(cv, [pts[i] for i in (0, 2, 4, 1, 3)], 3.2, RAMPS["glass"])
    gem(cv, C, C, 4.6, RAMPS["spirit"])
    cv.outline(v[0])
    return cv.image()


def hexagram():
    cv = Canvas()
    g = RAMPS["gold"]
    frame(cv, g, RAMPS["ember"])
    polyline(cv, star_pts(21.6, 3), 3.2, g)
    polyline(cv, star_pts(21.6, 3, 180), 3.2, g)
    gem(cv, C, C, 4.6, RAMPS["ember"])
    cv.outline(g[0])
    return cv.image()


def candle(cv, cx, cy):
    """A short wax candle (bevelled cylinder, lit left) with an ember flame (emissive)."""
    wax, em = RAMPS["wax"], RAMPS["ember"]
    for y in range(int(cy), int(cy) + 6):
        for x in range(int(cx) - 2, int(cx) + 2):
            k = x - (int(cx) - 2)
            c = [wax[4], wax[5], wax[3], wax[2]][k]
            cv.put(x, y, wax[5] if y == int(cy) and k in (1, 2) else c)
    cv.put(int(cx) - 1, int(cy) - 1, RAMPS["twine"][0])                   # the wick
    for (dx, dy, t) in ((-1, -2, 4), (0, -2, 5), (-1, -3, 5), (0, -3, 4), (-1, -4, 4), (0, -4, 3), (0, -5, 3)):
        cv.put(int(cx) + dx, int(cy) + dy, em[t], solid=False)


def sigil_initiate():
    """T0: a chalk circle, a diamond drawn between four lit candles, an ember gem at the heart."""
    cv = Canvas()
    ch = RAMPS["chalk"]
    frame(cv, ch, RAMPS["ember"])
    polyline(cv, star_pts(21.0, 4), 3.0, ch)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        candle(cv, C + sx * 9.0, C + sy * 9.0 - 3)
    gem(cv, C, C, 4.4, RAMPS["ember"])
    cv.outline(RAMPS["bone"][0])
    return cv.image()


def sigil_bound():
    """T1: a silver triangle clamped to the violet circle, chains binding a spirit gem at its centre."""
    cv = Canvas()
    v, ir = RAMPS["violet"], RAMPS["iron"]
    frame(cv, v, RAMPS["spirit"])
    tri = star_pts(21.6, 3)
    polyline(cv, tri, 3.2, ir)
    for deg in (0, 120, 240):                                  # clamps across the inner ring at the corners
        a = math.radians(deg)
        x, y = polar(22.4, deg)
        tx, ty = math.cos(a), math.sin(a)
        segment(cv, (x - tx * 4.2, y - ty * 4.2), (x + tx * 4.2, y + ty * 4.2), 3.6, ir)
    for deg in (60, 180, 300):                                 # chains from each side's middle to the spirit
        for r0 in (6.6, 9.4):
            a, b = polar(r0, deg), polar(r0 + 1.8, deg)
            segment(cv, a, b, 2.6, ir)
    gem(cv, C, C, 5.0, RAMPS["spirit"])
    cv.outline(v[0])
    return cv.image()


def sigil_abyssal():
    """T2: an eye watching from the deep - lids, lashes, a sea-glow iris gem and a slit pupil - and waves beneath."""
    cv = Canvas()
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    frame(cv, ab, sg)
    cy = C - 3.0
    # the lids: two arcs meeting at the corners - the upper from a circle centred below the eye, the lower from above
    upper = [(C + 19.0 * math.cos(math.radians(a)), cy + 12.0 + 19.0 * math.sin(math.radians(a))) for a in range(222, 319, 4)]
    lower = [(x, cy - (y - cy)) for (x, y) in upper]
    polyline(cv, upper, 2.6, sg, closed=False)
    polyline(cv, lower, 2.6, sg, closed=False)
    for deg in (-36, -18, 0, 18, 36):                          # lashes
        a, b = polar(9.4, deg, cy), polar(12.6, deg, cy)
        segment(cv, a, b, 1.8, sg)
    gem(cv, C, cy, 5.2, sg)
    for y in range(int(cy) - 3, int(cy) + 3):                  # the slit pupil
        cv.put(31, y, RAMPS["sculk"][0])
        cv.put(32, y, RAMPS["sculk"][1])
    for k, y0 in enumerate((C + 9.0, C + 14.0)):               # waves
        half = 11.0 - k * 3.0
        pts = [(C + dx, y0 + 1.6 * math.cos(dx / 2.4)) for dx in [i * 0.5 - half for i in range(int(half * 4) + 1)]]
        polyline(cv, pts, 2.4, sg, closed=False)
    cv.outline(ab[0])
    return cv.image()


def sigil_hollow():
    """T3: the Hollow star - solid, bevelled old bone - on a sculk circle crowned with five hollow-cyan spikes, a
    crimson gem at its heart."""
    cv = Canvas()
    sc, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    for i in range(5):                                          # the crown of spikes, outside the ring
        tip, l, r = polar(31.6, i * 72), polar(27.0, i * 72 - 9), polar(27.0, i * 72 + 9)
        filled_star(cv, [tip, r, l], hc, bevel=1.6)
    ring(cv, 24.0, 28.0, sc)
    ring(cv, 19.6, 21.0, sc)
    band_marks(cv, 22.4, hc, n=10)
    filled_star(cv, [polar(18.6 if i % 2 == 0 else 7.6, i * 36) for i in range(10)], RAMPS["bone"], bevel=3.0)
    gem(cv, C, C, 4.4, RAMPS["crimson"])
    cv.outline(sc[0])
    return cv.image()


SIGILS = [("pentagram", pentagram), ("hexagram", hexagram), ("initiate", sigil_initiate), ("bound", sigil_bound),
          ("abyssal", sigil_abyssal), ("hollow", sigil_hollow)]


def asymmetry(img):
    a = img.getchannel("A")
    return sum(1 for y in range(N) for x in range(N // 2) if (a.getpixel((x, y)) > 0) != (a.getpixel((N - 1 - x, y)) > 0))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "sigils"
    if which == "sigils":
        made = []
        for name, make in SIGILS:
            img = make()
            img.save(os.path.join(OUT, f"sigil_{name}.png"))
            made.append((f"{name} (asym {asymmetry(img)})", img))
        print(review.big_sheet(made, os.path.join(OUT, "review-sigils.png"), scale=4))
