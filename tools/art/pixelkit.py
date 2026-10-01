"""A small pixel-art kit: shapes with real surface normals, ramp shading under one light, selective outlines.

Workflow for an icon:
    icon = Icon(16)
    part = icon.capsule((4, 12), (11, 5), 2.2)           # a mask with normals
    icon.paint(part, RAMPS["chalk"], outline=True)       # shaded with the ramp, outlined in its own dark tones
    icon.pixels([(5, 4)], RAMPS["chalk"][5])             # hand-placed accents
Parts are painted in order (later parts sit on top; their outline separates them from what's below).
"""
import math

from PIL import Image

from palettes import LIGHT


def _norm(v):
    length = math.sqrt(sum(c * c for c in v)) or 1
    return tuple(c / length for c in v)


L = _norm(LIGHT)


class Part:
    """Pixels of one shape: {(x, y): normal}."""

    def __init__(self, normals):
        self.normals = normals

    def __or__(self, other):
        merged = dict(self.normals)
        merged.update(other.normals)
        return Part(merged)

    def __sub__(self, other):
        return Part({p: n for p, n in self.normals.items() if p not in other.normals})

    def __and__(self, other):
        return Part({p: n for p, n in self.normals.items() if p in other.normals})

    def keys(self):
        return self.normals.keys()


class Icon:
    def __init__(self, size=16, height=None):
        self.size = self.w = size
        self.h = height or size
        self.img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))

    # ------------------------------------------------------------------ shapes (pixel centers at +0.5)

    def _cells(self):
        for y in range(self.h):
            for x in range(self.w):
                yield x, y, x + 0.5, y + 0.5

    def sphere(self, cx, cy, r, squash=1.0):
        out = {}
        for x, y, px, py in self._cells():
            dx, dy = (px - cx) / r, (py - cy) / (r * squash)
            d = dx * dx + dy * dy
            if d <= 1.0:
                out[(x, y)] = _norm((dx, dy, math.sqrt(max(0.0, 1 - d))))
        return Part(out)

    def capsule(self, a, b, r):
        out = {}
        ax, ay = a
        bx, by = b
        vx, vy = bx - ax, by - ay
        ll = vx * vx + vy * vy or 1
        for x, y, px, py in self._cells():
            t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ll))
            dx, dy = px - (ax + t * vx), py - (ay + t * vy)
            d = math.hypot(dx, dy)
            if d <= r:
                out[(x, y)] = _norm((dx / r, dy / r, math.sqrt(max(0.0, 1 - (d / r) ** 2))))
        return Part(out)

    def box(self, x0, y0, x1, y1, bevel=1.0):
        """An axis-aligned block; edges within `bevel` pixels tilt outward."""
        out = {}
        for x, y, px, py in self._cells():
            if x0 <= px <= x1 and y0 <= py <= y1:
                nx = -1 if px - x0 < bevel else (1 if x1 - px < bevel else 0)
                ny = -1 if py - y0 < bevel else (1 if y1 - py < bevel else 0)
                out[(x, y)] = _norm((nx * 0.7, ny * 0.7, 1))
        return Part(out)

    def polygon(self, points, bevel=1.4):
        """A filled polygon whose edges are bevelled (lit edges catch the light, far edges fall into shadow)."""
        out = {}
        n = len(points)
        for x, y, px, py in self._cells():
            if not _inside(points, px, py):
                continue
            best, normal2d = 1e9, (0.0, 0.0)
            for i in range(n):
                (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
                d, nrm = _edge(px, py, x0, y0, x1, y1, points)
                if d < best:
                    best, normal2d = d, nrm
            if best < bevel:
                tilt = 1 - best / bevel
                out[(x, y)] = _norm((normal2d[0] * tilt, normal2d[1] * tilt, 1))
            else:
                out[(x, y)] = (0.0, 0.0, 1.0)
        return Part(out)

    def tubes(self, segments, r):
        """Line art as rounded tubes: each pixel takes the normal of its nearest segment (a raised, glowing inlay)."""
        out = {}
        for x, y, px, py in self._cells():
            best = None
            for (ax, ay), (bx, by) in segments:
                vx, vy = bx - ax, by - ay
                ll = vx * vx + vy * vy or 1
                t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ll))
                dx, dy = px - (ax + t * vx), py - (ay + t * vy)
                d = math.hypot(dx, dy)
                if best is None or d < best[0]:
                    best = (d, dx, dy)
            d, dx, dy = best
            if d <= r:
                out[(x, y)] = _norm((dx / r, dy / r, math.sqrt(max(0.0, 1 - (d / r) ** 2))))
        return Part(out)

    def facet(self, points, normal):
        """A flat face of a cut gem: one normal for the whole polygon."""
        n = _norm(normal)
        return Part({(x, y): n for x, y, px, py in self._cells() if _inside(points, px, py)})

    def ellipse_ring(self, cx, cy, rx, ry, width, tilt=0.55):
        """A torus seen at an angle (a halo): the band curves across its width, the far side tilts away."""
        out = {}
        for x, y, px, py in self._cells():
            dx, dy = (px - cx) / rx, (py - cy) / ry
            d = math.hypot(dx, dy)
            band = (d - 1.0) * min(rx, ry) / (width / 2)
            if abs(band) <= 1 and d:
                ux, uy = dx / d, dy / d
                out[(x, y)] = _norm((ux * band, uy * band * tilt - (1 - tilt) * 0.3, math.sqrt(max(0.0, 1 - band * band))))
        return Part(out)

    def ring(self, cx, cy, r_out, r_in):
        """A torus seen from above: normals curve across the band."""
        out = {}
        mid, half = (r_out + r_in) / 2, (r_out - r_in) / 2
        for x, y, px, py in self._cells():
            dx, dy = px - cx, py - cy
            d = math.hypot(dx, dy)
            if r_in <= d <= r_out:
                t = (d - mid) / half
                ux, uy = (dx / d, dy / d) if d else (0, 0)
                out[(x, y)] = _norm((ux * t, uy * t, math.sqrt(max(0.0, 1 - t * t))))
        return Part(out)

    # ------------------------------------------------------------------ painting

    def paint(self, part, ramp, outline=True, bias=0.0, flat=None, ambient=0.18, spec=True, outline_ramp=None, outline_over=True):
        """Shades the part with a ramp (index from lighting), then draws a selective outline around it."""
        top = len(ramp) - 1
        for (x, y), n in part.normals.items():
            lit = max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2])
            value = ambient + (1 - ambient) * lit + bias
            idx = max(1, min(top - (0 if spec else 1), round(value * (top - 1)) + (1 if spec and lit > 0.93 else 0)))
            if flat is not None:
                idx = flat
            self.img.putpixel((x, y), ramp[idx])
        if outline:
            self.outline(part, outline_ramp or ramp, over=outline_over)

    def outline(self, part, ramp, over=True):
        """over=False: only outline onto empty pixels (never across parts already painted)."""
        """Selective outline: around the shape, in the ramp's own darks (lighter on the lit top-left side)."""
        cells = set(part.keys())
        edge = set()
        for (x, y) in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in cells and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                    edge.add((q, (dx, dy)))
        for (q, (dx, dy)) in edge:
            lit_side = dx < 0 or dy < 0
            current = self.img.getpixel(q)
            if current[3] == 0 or (over and q not in cells):
                self.img.putpixel(q, ramp[1] if lit_side else ramp[0])

    def pixels(self, coords, color):
        for (x, y) in coords:
            if 0 <= x < self.w and 0 <= y < self.h:
                self.img.putpixel((x, y), color)

    def glow(self, color, radius=3.0, strength=0.5):
        """Soft bloom on empty pixels around everything painted so far (alpha falls off with distance)."""
        solid = [(x, y) for y in range(self.h) for x in range(self.w) if self.img.getpixel((x, y))[3] == 255]
        rr = int(math.ceil(radius))
        best = {}
        for (sx, sy) in solid:
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    q = (sx + dx, sy + dy)
                    if 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                        d = math.hypot(dx, dy)
                        if d <= radius and d < best.get(q, 99):
                            best[q] = d
        for q, d in best.items():
            if self.img.getpixel(q)[3] == 0:
                a = int(255 * strength * (1 - (d - 1) / radius) ** 1.5) if d > 1 else int(255 * strength)
                if a > 6:
                    self.img.putpixel(q, color[:3] + (min(255, a),))

    def twinkle(self, x, y, size, ramp):
        """The Occultech twinkle (signature motif): size 1 = a dot, 2 = a 3 px cross, 3 = a 5 px star with a white core,
        4 = a 7 px star. Colours come from the top of a ramp (chromatic, never plain white)."""
        if size <= 0:
            return
        if size == 1:
            self.pixels([(x, y)], ramp[4])
            return
        arm = {2: 1, 3: 2, 4: 3}[size]
        for d in range(1, arm + 1):
            c = ramp[4] if d < arm or size == 2 else ramp[3]
            self.pixels([(x + d, y), (x - d, y), (x, y + d), (x, y - d)], c)
        self.pixels([(x, y)], ramp[5])

    def clear(self, coords):
        for (x, y) in coords:
            self.img.putpixel((x, y), (0, 0, 0, 0))

    def mirror_check(self):
        """Pixels that differ from the horizontal mirror image (0 = perfectly symmetric)."""
        w = self.w
        return sum(1 for y in range(self.h) for x in range(w // 2) if self.img.getpixel((x, y)) != self.img.getpixel((w - 1 - x, y)))

    def silhouette_asymmetry(self):
        """Like mirror_check but only compares coverage (shading follows the top-left light, so it is never mirrored)."""
        w = self.w
        return sum(1 for y in range(self.h) for x in range(w // 2)
                   if (self.img.getpixel((x, y))[3] > 0) != (self.img.getpixel((w - 1 - x, y))[3] > 0))

    def save(self, path):
        self.img.save(path)


def _inside(poly, px, py):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _edge(px, py, x0, y0, x1, y1, poly):
    vx, vy = x1 - x0, y1 - y0
    ll = vx * vx + vy * vy or 1
    t = max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / ll))
    cx, cy = x0 + t * vx, y0 + t * vy
    d = math.hypot(px - cx, py - cy)
    # outward normal of the edge
    nx, ny = vy, -vx
    length = math.hypot(nx, ny) or 1
    nx, ny = nx / length, ny / length
    mx, my = (x0 + x1) / 2 + nx * 0.01, (y0 + y1) / 2 + ny * 0.01
    if _inside(poly, mx, my):
        nx, ny = -nx, -ny
    return d, (nx, ny)
