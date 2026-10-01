"""Session B (round 2): sigils (64 px) in the Session A style - tier ramps, one light, tube-shaded line art, a shaded
core, coloured outlines only where a part crosses another, and a soft glow.

Run: python tools/art/session_b.py sigils v1
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-b")
os.makedirs(OUT, exist_ok=True)
C = 32.0

# 3x3 marks for the band between the rings (both symmetric)
MARK_X = [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]
MARK_PLUS = [(0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)]


def polar(r, deg, cy=C):
    a = math.radians(deg - 90)
    return (C + r * math.cos(a), cy + r * math.sin(a))


def poly_segments(points, closed=True):
    pts = list(points) + ([points[0]] if closed else [])
    return list(zip(pts, pts[1:]))


def arc(cx, cy, r, a0, a1, steps=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def outline_over(icon, part, color):
    """A dark edge only where this part lies on top of something already painted (separates layers, no hard
    outline against the empty background - that side gets the glow instead)."""
    cells = set(part.keys())
    for (x, y) in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in cells and 0 <= q[0] < icon.w and 0 <= q[1] < icon.h and icon.img.getpixel(q)[3] == 255:
                icon.img.putpixel(q, color)


def layer(icon, part, ramp, bias=0.0, sep=None):
    if sep is not None:
        outline_over(icon, part, sep)
    icon.paint(part, ramp, outline=False, bias=bias)


def circle_band(icon, ramp, marks_ramp, n_marks=12, outer=29.8, inner=23.6, bias=-0.05):
    """The ritual circle: a thick outer ring, a thin inner ring, small marks between them."""
    icon.paint(icon.ring(C, C, outer + 1.7, outer - 1.7), ramp, outline=False, bias=bias)
    icon.paint(icon.ring(C, C, inner + 1.0, inner - 1.0), ramp, outline=False, bias=bias - 0.08)
    mid = (outer + inner) / 2 + 0.3
    for i in range(n_marks):
        x, y = polar(mid, i * 360 / n_marks)
        px, py = math.floor(x), math.floor(y)
        shape = MARK_PLUS if i % 2 == 0 else MARK_X
        icon.pixels([(px + dx, py + dy) for dx, dy in shape], marks_ramp[3])
        icon.pixels([(px, py)], marks_ramp[4])


def core(icon, ramp, r, cy=C, sep=None, bias=0.15):
    orb = icon.sphere(C, cy, r)
    if sep is not None:
        outline_over(icon, orb, sep)
    icon.paint(orb, ramp, outline=False, bias=bias)
    return orb


def star_pts(r, n, rot_deg=0.0, cy=C):
    return [polar(r, rot_deg + i * 360 / n, cy) for i in range(n)]


# ------------------------------------------------------------------ the six sigils

def pentagram():
    """Generic ritual pentagram (the look of the first sample, rebuilt with volume)."""
    icon = Icon(64)
    v = RAMPS["violet"]
    circle_band(icon, v, v)
    pts = star_pts(23.6, 5)
    star = icon.tubes(poly_segments([pts[i] for i in (0, 2, 4, 1, 3)]), 1.6)
    layer(icon, star, RAMPS["glass"], bias=0.28, sep=v[0])
    core(icon, RAMPS["spirit"], 4.4, sep=v[0])
    icon.glow(v[4], radius=2.2, strength=0.3)
    return icon


def hexagram():
    icon = Icon(64)
    g = RAMPS["gold"]
    circle_band(icon, g, g, bias=-0.32)
    up, down = star_pts(23.6, 3), star_pts(23.6, 3, 180)
    tri = icon.tubes(poly_segments(up) + poly_segments(down), 1.6)
    layer(icon, tri, g, bias=0.18, sep=g[0])
    core(icon, RAMPS["ember"], 4.4, sep=g[0])
    icon.glow(g[4], radius=2.2, strength=0.3)
    return icon


def sigil_initiate():
    """T0: a chalk circle, a diamond drawn between four lit candles, an ember at the heart."""
    icon = Icon(64)
    ch = RAMPS["chalk"]
    circle_band(icon, ch, RAMPS["bone"])
    diamond = icon.tubes(poly_segments(star_pts(21.5, 4)), 1.5)
    layer(icon, diamond, ch, bias=0.2, sep=ch[0])
    for deg in (45, 135, 225, 315):
        x, y = polar(13.5, deg)
        body = icon.box(x - 2.0, y - 0.5, x + 2.0, y + 6.0, bevel=1.2)
        icon.paint(body, RAMPS["wax"], outline_ramp=RAMPS["wax"], bias=0.05)
        icon.pixels([(math.floor(x) - 1, math.floor(y)), (math.floor(x) + 1, math.floor(y) + 1)], RAMPS["wax"][5])
        flame = icon.sphere(x, y - 3.4, 1.9) | icon.polygon([(x - 1.6, y - 3.6), (x + 1.6, y - 3.6), (x, y - 8.2)], bevel=0.5)
        icon.paint(flame, RAMPS["ember"], outline=False, bias=0.45)
        icon.pixels([(math.floor(x), math.floor(y - 3.0))], RAMPS["ember"][5])
        icon.pixels([(math.floor(x), math.floor(y - 1.0))], RAMPS["twine"][0])
    core(icon, RAMPS["ember"], 4.0, sep=ch[0], bias=0.2)
    icon.glow(RAMPS["ember"][4], radius=2.2, strength=0.3)
    return icon


def sigil_bound():
    """T1: a silver triangle clamped to the circle, binding a spirit at its centre."""
    icon = Icon(64)
    v = RAMPS["violet"]
    circle_band(icon, v, RAMPS["glass"])
    tri_pts = star_pts(23.6, 3)
    tri = icon.tubes(poly_segments(tri_pts), 1.7)
    layer(icon, tri, RAMPS["iron"], bias=0.15, sep=v[0])
    clamps = []
    for deg in (0, 120, 240):
        a = math.radians(deg)
        x, y = polar(23.6, deg)
        tx, ty = math.cos(a), math.sin(a)
        clamps.append(((x - tx * 5.0, y - ty * 5.0), (x + tx * 5.0, y + ty * 5.0)))
    layer(icon, icon.tubes(clamps, 2.0), RAMPS["iron"], bias=0.2, sep=v[0])
    # chains from the triangle's sides to the spirit
    links = []
    for deg in (0, 120, 240):
        for r0 in (7.6, 11.0, 14.4):
            links.append((polar(r0, deg), polar(r0 + 1.8, deg)))
    layer(icon, icon.tubes(links, 1.15), RAMPS["iron"], bias=0.1, sep=v[0])
    ghost = core(icon, RAMPS["spirit"], 5.6, sep=v[0], bias=0.2)
    icon.pixels([(29, 31), (34, 31)], RAMPS["spirit"][0])
    icon.pixels([(29, 32), (34, 32)], RAMPS["spirit"][1])
    icon.glow(RAMPS["spirit"][4], radius=2.2, strength=0.3)
    return icon


def sigil_abyssal():
    """T2: an eye that watches from the deep, waves rising beneath it."""
    icon = Icon(64)
    ab = RAMPS["abyss"]
    circle_band(icon, ab, RAMPS["seaglow"])
    cy = C - 3.0
    upper = arc(C, cy + 13.0, 19.0, 222, 318)
    lower = arc(C, cy - 13.0, 19.0, 42, 138)
    lids = icon.tubes(poly_segments(upper, False) + poly_segments(lower, False), 1.5)
    layer(icon, lids, RAMPS["seaglow"], bias=0.05, sep=ab[0])
    # lashes: the eye is open and watching
    lashes = []
    for deg in (-36, -18, 0, 18, 36):
        x0, y0 = polar(7.8, deg, cy + 2.0)
        x1, y1 = polar(11.6, deg, cy + 2.0)
        lashes.append(((x0, y0 - 1.0), (x1, y1 - 1.0)))
    layer(icon, icon.tubes(lashes, 1.0), RAMPS["seaglow"], bias=-0.05, sep=ab[0])
    core(icon, RAMPS["seaglow"], 5.0, cy=cy, sep=ab[0], bias=0.1)
    pupil = icon.capsule((C, cy - 2.6), (C, cy + 2.6), 1.1)
    icon.paint(pupil, RAMPS["sculk"], outline=False, flat=1)
    waves = []
    for k, y0 in enumerate((C + 9.5, C + 15.0)):
        half = 13.0 - k * 3.5
        pts = [(C + dx, y0 + 1.8 * math.cos(dx / 2.6)) for dx in [i * 0.5 - half for i in range(int(half * 4) + 1)]]
        waves += poly_segments(pts, False)
    layer(icon, icon.tubes(waves, 1.3), RAMPS["seaglow"], bias=-0.1, sep=ab[0])
    icon.glow(RAMPS["seaglow"][3], radius=2.2, strength=0.3)
    return icon


def sigil_hollow():
    """T3: the Hollow Sigil from Session A (bone star, crimson core) on a sculk circle, crowned with spikes."""
    icon = Icon(64)
    sc = RAMPS["sculk"]
    circle_band(icon, sc, RAMPS["hollowcy"], outer=26.4, inner=21.0)
    spikes = []
    for i in range(5):
        tip = polar(31.8, i * 72)
        spikes.append([tip, polar(26.8, i * 72 - 11), polar(26.8, i * 72 + 11)])
    for s in spikes:
        icon.paint(icon.polygon(s, bevel=1.2), RAMPS["hollowcy"], outline=False, bias=0.1)
    star = icon.polygon([polar(19.6 if i % 2 == 0 else 8.0, i * 36) for i in range(10)], bevel=3.2)
    outline_over(icon, star, sc[0])
    icon.paint(star, RAMPS["bone"], outline=True, outline_ramp=RAMPS["bone"], bias=0.1, outline_over=False)
    core(icon, RAMPS["crimson"], 4.6, sep=sc[0], bias=0.2)
    icon.glow(RAMPS["hollowcy"][3], radius=2.2, strength=0.3)
    return icon


SIGILS = [("Pentagram", pentagram), ("Hexagram", hexagram), ("T0 Initiate", sigil_initiate), ("T1 Bound", sigil_bound),
          ("T2 Abyssal", sigil_abyssal), ("T3 Hollow", sigil_hollow)]


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "sigils"
    version = sys.argv[2] if len(sys.argv) > 2 else "v1"
    if which == "sigils":
        made = []
        for name, make in SIGILS:
            icon = make()
            icon.save(os.path.join(OUT, "sigil_" + name.split()[-1].lower() + ".png"))
            made.append((f"{name} (asym {icon.silhouette_asymmetry()})", icon.img))
        print(review.big_sheet(made, os.path.join(OUT, f"review-sigils-{version}.png"), scale=4))


# ================================================================== pieces: finished 16 px item textures

GEM_FRAMES = 8


def gem(ramp, frame=0):
    """A cut gem with hard facet edges: light and dark facets alternate round the pavilion (that alternation is what
    reads as "faceted" and 3D), the lit seams get a bright edge line, the shadow seams a dark one. Animated in 8 frames:
    a glint sweeps across the table, then twinkles take turns round the stone. Frame 0 is the static icon."""
    icon = Icon(16)
    t, g0, g1, tip = 4.0, 7.0, 8.2, 15.6
    L, R = 2.0, 14.0
    tl, tr = 5.6, 10.4
    facets = [  # (polygon, ramp index)
        ([(tl, t), (tr, t), (9.6, 6.0), (6.4, 6.0)], 4),                    # table
        ([(L, g0), (tl, t), (6.4, 6.0), (4.6, g0)], 5),                     # crown left (faces the light)
        ([(6.4, 6.0), (9.6, 6.0), (11.4, g0), (4.6, g0)], 3),               # crown front
        ([(tr, t), (R, g0), (11.4, g0), (9.6, 6.0)], 2),                    # crown right
        ([(L, g0), (R, g0), (R, g1), (L, g1)], 3),                          # girdle
        ([(L, g1), (5.0, g1), (8.0, tip)], 4),                              # pavilion: four wide facets,
        ([(5.0, g1), (8.0, g1), (8.0, tip)], 2),                            # light and dark alternating
        ([(8.0, g1), (11.0, g1), (8.0, tip)], 3),
        ([(11.0, g1), (R, g1), (8.0, tip)], 1),
    ]
    whole = Part({})
    for pts, idx in facets:
        part = icon.facet(pts, (0, 0, 1)) - whole
        icon.paint(part, ramp, outline=False, flat=idx)
        whole = whole | part
    icon.outline(whole, ramp)
    # hard seams: the girdle line (bright on the lit half), the crown's lit edge, table rim
    icon.pixels([(x, 7) for x in range(2, 8)], ramp[5])
    icon.pixels([(x, 7) for x in range(8, 14)], ramp[2])
    icon.pixels([(x, 8) for x in range(2, 14)], ramp[1])
    icon.pixels([(3, 6), (4, 5)], ramp[5])
    icon.pixels([(x, 4) for x in range(6, 10)], ramp[5])
    # refracted light low in the stone (bottom right) and a cool reflection on the left pavilion
    icon.pixels([(9, 10), (9, 11)], ramp[4])
    icon.pixels([(4, 9)], ramp[5])
    # animation: a glint sweeping the table (frames 0-3), then twinkles take turns (frames 4-7)
    sweep = {0: [(6, 5)], 1: [(7, 5), (8, 4)], 2: [(8, 5), (9, 4)], 3: [(9, 5)]}
    icon.pixels(sweep.get(frame, [(6, 5)]), ramp[5])
    sizes_a = [3, 2, 1, 0, 0, 0, 1, 2]   # top right
    sizes_b = [0, 0, 1, 2, 3, 2, 1, 0]   # bottom left
    sizes_c = [1, 0, 0, 0, 1, 2, 3, 2]   # bottom right
    icon.twinkle(13, 2, sizes_a[frame], ramp)
    icon.twinkle(2, 13, sizes_b[frame], ramp)
    icon.twinkle(14, 13, max(0, sizes_c[frame] - 1), ramp)
    return icon


def crown():
    """A gold crown: the inside of the back band shows between three solid points (that's what makes it a crown and
    not a comb), a curved front band with set stones, ball tips."""
    icon = Icon(16)
    g = RAMPS["gold"]
    # inside of the back of the band, seen between the points: dark, flat
    back = icon.box(2.0, 6.5, 14.0, 10.5, bevel=0)
    icon.paint(back, g, outline=False, flat=1)
    points = icon.polygon([(1.2, 11.0), (2.6, 3.8), (6.6, 10.0)], bevel=1.6) |         icon.polygon([(4.6, 10.0), (8.0, 2.4), (11.4, 10.0)], bevel=1.6) |         icon.polygon([(9.4, 10.0), (13.4, 3.8), (14.8, 11.0)], bevel=1.6)
    icon.paint(points, g, bias=0.05, outline_over=False)
    band = {}
    for y in range(8, 16):
        for x in range(1, 15):
            u = (x + 0.5 - 8) / 7.4
            lift = 1.2 * (1 - u * u)  # we look down at it: the front of the band dips
            if 8.4 + lift <= y + 0.5 <= 12.6 + lift:
                n = (u * 0.95, -0.1, math.sqrt(max(0.0, 1 - u * u)))
                band[(x, y)] = tuple(c / math.sqrt(sum(k * k for k in n)) for c in n)
    band = Part(band)
    outline_over(icon, band, g[0])
    icon.paint(band, g, bias=0.12, outline_over=False)
    for (x, y) in ((2.6, 3.0), (13.4, 3.0)):
        icon.paint(icon.sphere(x, y, 1.25), g, bias=0.25, outline_over=False)
    icon.paint(icon.sphere(8.0, 1.6, 1.4), RAMPS["crimson"], bias=0.3, outline_ramp=g, outline_over=False)
    icon.paint(icon.sphere(8.0, 11.4, 1.8), RAMPS["crimson"], bias=0.25, outline_ramp=g)
    for x in (4.2, 11.8):
        icon.paint(icon.sphere(x, 11.0, 1.0), RAMPS["hollowcy"], bias=0.15, outline=False)
    return icon


def halo():
    """A glowing halo seen at an angle: a bright torus, the far side dimmer, a few motes; light, so it glows."""
    icon = Icon(16)
    gd = RAMPS["gold"]
    ring = icon.ellipse_ring(8.0, 8.0, 6.8, 3.2, 1.8)
    far = Part({p: n for p, n in ring.normals.items() if p[1] < 8})
    near = ring - far
    icon.paint(far, gd, outline=False, bias=-0.12)
    icon.paint(near, gd, outline=False, bias=0.18)
    icon.pixels([(3, 10), (4, 11)], gd[5])
    hole = {(x, y) for y in range(16) for x in range(16) if ((x + 0.5 - 8) / 5.6) ** 2 + ((y + 0.5 - 8) / 2.0) ** 2 < 1}
    icon.glow(gd[4], radius=2.0, strength=0.4)
    icon.clear([p for p in hole if icon.img.getpixel(p)[3] < 255])  # the hole stays empty: a ring, not a plate
    # two small twinkles above the ring
    icon.pixels([(12, 1), (11, 2), (12, 2), (13, 2), (12, 3)], gd[4])
    icon.pixels([(12, 2), (3, 3)], gd[5])
    return icon


PIECES = [("Gem (T0 ember)", lambda: gem(RAMPS["ember"])), ("Gem (T1 violet)", lambda: gem(RAMPS["violet"])),
          ("Gem (T2 seaglow)", lambda: gem(RAMPS["seaglow"])), ("Gem (T3 crimson)", lambda: gem(RAMPS["crimson"])),
          ("Crown", crown), ("Halo", halo)]
GEMS = [("ember", "T0"), ("violet", "T1"), ("seaglow", "T2"), ("crimson", "T3")]


# ================================================================== particles: animated, emissive (no light, no outline)

def soul_flame(ramp, frame, frames=4):
    """A soul flame with a face: a teardrop body whose tip sways, side tongues that flicker in turn, heat-coloured
    (white core low in the flame, dark tips), two hollow eyes, sparks drifting up."""
    icon = Icon(16)
    ph = frame * 2 * math.pi / frames
    heat = {}
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            t = (py - 0.6) / 14.2                       # 0 at the tip, 1 at the base
            if not 0 <= t <= 1.08:
                continue
            sway = 1.6 * math.sin(ph + t * 2.4) * (1 - t) ** 1.5
            half = 4.7 * math.sin(min(1.0, t) * math.pi * 0.6) ** 1.6 * (1 - max(0, t - 0.86) * 3.2)
            dx = px - 8.0 - sway
            if abs(dx) <= half:
                h = 1 - (abs(dx) / max(half, 0.1)) * 0.55 - abs(t - 0.78) * 0.9
                heat[(x, y)] = h
    # side tongues: one rises while the other falls
    for side, k in ((-1, 0), (1, 1)):
        rise = 0.5 + 0.5 * math.sin(ph + k * math.pi)
        tip_y = 8.0 - 3.4 * rise
        for y in range(16):
            for x in range(16):
                px, py = x + 0.5, y + 0.5
                cx = 8.0 + side * (4.2 + (py - tip_y) * -0.25)
                if tip_y <= py <= 11.5:
                    w = 1.4 * (py - tip_y) / (11.5 - tip_y) + 0.3
                    if abs(px - cx) <= w and (x, y) not in heat:
                        heat[(x, y)] = 0.25 + 0.2 * (py - tip_y) / (11.5 - tip_y)
    for (x, y), h in heat.items():
        idx = 1 if h < 0.2 else 2 if h < 0.42 else 3 if h < 0.62 else 4 if h < 0.82 else 5
        icon.pixels([(x, y)], ramp[idx])
    # the soul: two hollow eyes and a small mouth, sitting in the hot part of the flame
    # hollow, slanted eyes - eerie, not cute (no mouth)
    icon.pixels([(6, 9), (6, 10), (6, 11), (9, 9), (9, 10), (9, 11)], ramp[0])
    # sparks drifting up and fading
    for i, (sx, base) in enumerate(((4, 3), (11, 1), (8, 0))):
        y = base - frame + (4 if base - frame < 0 else 0)
        if 0 <= y < 16 and (sx, y) not in heat:
            icon.pixels([(sx + (frame + i) % 2, y)], ramp[4 if i != 1 else 3])
    icon.glow(ramp[3], radius=1.6, strength=0.35)
    return icon


def sparkle(ramp, frame):
    """A twinkle's life in five frames: a seed of light, a growing cross, the full star (long rays, short diagonals, a
    flash ring), the fade with the ring expanding, two motes left behind."""
    icon = Icon(16)
    ray = [0, 3.2, 7.4, 4.6, 0][frame]
    diag = [0, 0, 3.4, 1.6, 0][frame]
    ring_r = [0, 0, 4.6, 6.4, 0][frame]
    if ring_r:
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
                if abs(d - ring_r) < 0.55:
                    icon.img.putpixel((x, y), ramp[3][:3] + ((150 if frame == 2 else 80),))
    def put(x, y, idx, alpha=255):
        if 0 <= x < 16 and 0 <= y < 16:
            icon.img.putpixel((x, y), ramp[idx][:3] + (alpha,))
    for dist in range(1, 8):
        if dist <= ray:
            f = dist / max(ray, 1)
            idx = 5 if f < 0.3 else 4 if f < 0.6 else 3
            a = 255 if f < 0.75 else 190
            for (ux, uy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                put(7 + (ux if ux > 0 else 0) + ux * (dist - (1 if ux > 0 else 0)) if ux else 7, 7 + uy * dist if uy < 0 else (8 + uy * (dist - 1) if uy else 7), idx, a)
                put(8 + ux * dist if ux > 0 else (7 + ux * (dist - 1) if ux else 8), 8 + uy * dist if uy > 0 else (7 + uy * (dist - 1) if uy else 8), idx, a)
        if 2 <= dist <= diag:
            idx = 4 if dist < 3 else 3
            for (ux, uy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                put(7 + ux * dist + (1 if ux > 0 else 0), 7 + uy * dist + (1 if uy > 0 else 0), idx, 200)
    if frame in (1, 2, 3):
        put(7, 7, 5); put(8, 7, 5); put(7, 8, 5); put(8, 8, 5)
    if frame == 0:
        put(7, 7, 4); put(8, 8, 4); put(8, 7, 5); put(7, 8, 4, 180)
    if frame == 4:
        put(5, 6, 4); put(11, 10, 3, 200); put(8, 3, 3, 150)
    if frame == 1:
        icon.glow(ramp[4], radius=1.6, strength=0.3)
    return icon


def frame_sheet(rows, path, scale=6):
    """rows: [(name, [frames])]. Frames side by side at 1x, then big on dark and on stone."""
    from PIL import Image, ImageDraw
    n = max(len(f) for _, f in rows)
    cell = 16 * scale
    out = Image.new("RGB", (200 + 2 * n * (cell + 8) + 120, 30 + len(rows) * (cell + 16)), (34, 32, 40))
    d = ImageDraw.Draw(out)
    d.text((200, 8), "frames on dark", fill=(200, 200, 210))
    d.text((200 + n * (cell + 8), 8), "frames on stone", fill=(200, 200, 210))
    d.text((200 + 2 * n * (cell + 8), 8), "1x", fill=(200, 200, 210))
    for r, (name, frames) in enumerate(rows):
        y = 30 + r * (cell + 16)
        d.text((8, y + cell // 2 - 6), name, fill=(230, 230, 240))
        for i, im in enumerate(frames):
            out.paste(review.on((24, 22, 30), im, scale), (200 + i * (cell + 8), y))
            st = review.stone(16, 16, scale)
            big = im.resize((cell, cell), Image.NEAREST)
            st.paste(big, (0, 0), big)
            out.paste(st, (200 + (n + i) * (cell + 8), y))
            small = review.on((24, 22, 30), im, 1)
            out.paste(small, (200 + 2 * n * (cell + 8) + i * 20, y + cell // 2 - 8))
    out.save(path)
    return path


PARTICLES = [*[(f"Gem {tier} {r} (animated)", [lambda f=f, r=r: gem(RAMPS[r], f) for f in range(GEM_FRAMES)]) for r, tier in GEMS],
             ("Soul flame (spirit)", [lambda f=f: soul_flame(RAMPS["spirit"], f) for f in range(4)]),
             ("Soul flame (crimson)", [lambda f=f: soul_flame(RAMPS["crimson"], f) for f in range(4)]),
             ("Sparkle (gold)", [lambda f=f: sparkle(RAMPS["gold"], f) for f in range(5)]),
             ("Sparkle (hollow)", [lambda f=f: sparkle(RAMPS["hollowcy"], f) for f in range(5)])]


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "particles":
    version = sys.argv[2] if len(sys.argv) > 2 else "v1"
    rows = []
    for name, makers in PARTICLES:
        frames = []
        for i, make in enumerate(makers):
            icon = make()
            icon.save(os.path.join(OUT, name.lower().replace(" (", "_").replace(")", "").replace(" ", "_") + f"_{i}.png"))
            frames.append(icon.img)
        rows.append((name, frames))
    print(frame_sheet(rows, os.path.join(OUT, f"review-particles-{version}.png")))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "pieces":
    version = sys.argv[2] if len(sys.argv) > 2 else "v1"
    made = []
    for name, make in PIECES:
        icon = make()
        icon.save(os.path.join(OUT, name.lower().replace(" (", "_").replace(")", "").replace(" ", "_") + ".png"))
        made.append((name, icon.img))
    print(review.sheet(made, os.path.join(OUT, f"review-pieces-{version}.png")))
