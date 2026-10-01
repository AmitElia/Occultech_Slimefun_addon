"""Session D: tier-1 item icons (16 px). Tier 1 is *Bound*: violet, smoky glass and silver, spirit cyan as the magic
accent; the theme is binding - bands, clamps, chains, spirits held in place (see docs/art/REFERENCES.md and STYLE.md).

Run: python tools/art/session_d.py d1 [version]     (d1 materials, d2 drops, d3 gear, d4 contracts/decor, set)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part, _norm  # noqa: E402
from session_c import cut, put, flat_face, line_px  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-d")
os.makedirs(OUT, exist_ok=True)


def bar(icon, ramp, a=(1.4, 9.4), b=(10.0, 3.6), c=(13.8, 5.8), h=3.0, tones=(4, 3, 2)):
    """A metal bar lying diagonally in 3/4 view (the ingot family shape shared with Warded Silver)."""
    d = (a[0] + c[0] - b[0], a[1] + c[1] - b[1])
    top = flat_face(icon, [a, b, c, d], (0, -0.8, 0.6))
    left = flat_face(icon, [a, d, (d[0], d[1] + h), (a[0], a[1] + h)], (-0.4, 0.5, 0.75))
    right = flat_face(icon, [d, c, (c[0], c[1] + h), (d[0], d[1] + h)], (0.6, 0.4, 0.7))
    icon.paint(left, ramp, outline=False, flat=tones[1])
    icon.paint(right - left, ramp, outline=False, flat=tones[2])
    icon.paint(top, ramp, outline=False, flat=tones[0])
    icon.outline(top | left | right, ramp)
    return top, left, right, d


def pixmap(icon, rows, x0, y0, colours):
    """Hand-placed pixels: rows of letters, each letter a colour (any other character is left alone)."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colours:
                put(icon, [(x0 + x, y0 + y)], colours[ch])


def mirror_silhouette(icon):
    """Pixels whose mirror partner is empty get cleared, so the silhouette is exactly symmetric."""
    w = icon.w
    for y in range(icon.h):
        for x in range(w):
            if icon.img.getpixel((x, y))[3] and not icon.img.getpixel((w - 1 - x, y))[3]:
                icon.img.putpixel((x, y), (0, 0, 0, 0))


# ================================================================== D1: materials and the core component

def bound_steel(frame=0):
    """Dark violet steel in the ingot shape, bound by two bands of spirit light that pulse along the bar."""
    icon = Icon(16)
    st, sp = RAMPS["boundsteel"], RAMPS["spirit"]
    top, left, right, d = bar(icon, st, tones=(3, 2, 1))   # darker than Warded Silver: a different metal
    put(icon, [(2, 9), (3, 8), (4, 7), (5, 7), (6, 6), (7, 5), (8, 5), (9, 4)], st[4])
    put(icon, [(5, 12), (5, 13), (5, 14)], st[3])
    # two bands wrapping the bar: across the top face and down the long side
    for k, (x0, y0) in enumerate(((3.6, 8.0), (8.2, 4.9))):
        hot = (frame + k * 2) % 4 == 0
        band = line_px((x0, y0), (x0 + 2.6, y0 + 1.8)) + line_px((x0 + 2.6, y0 + 1.8), (x0 + 2.6, y0 + 4.6))
        put(icon, [p for p in band if p in (top.normals.keys() | left.normals.keys() | right.normals.keys())],
            sp[4] if hot else sp[3])
    return icon


def bound_chalk(frame=0):
    """Violet chalk held by a silver band, sharpened to a point at its drawing end; the stroke it leaves is the chalk's
    own violet, with a glint where it is still fresh (animated)."""
    icon = Icon(16)
    vi, ir = RAMPS["violet"], RAMPS["iron"]
    a, b = (5.4, 9.6), (11.4, 3.6)
    vx, vy = b[0] - a[0], b[1] - a[1]
    ll = vx * vx + vy * vy

    def t_of(p):
        return ((p[0] + 0.5 - a[0]) * vx + (p[1] + 0.5 - a[1]) * vy) / ll

    stick = icon.capsule(a, b, 2.6)
    stick = Part({p: n for p, n in stick.normals.items() if 0.0 <= t_of(p) < 1.12})
    icon.paint(stick, vi, bias=0.18)
    put(icon, [p for p in stick.keys() if t_of(p) > 1.02], vi[3])
    # the sharpened tip: a cone from the stick's end to a point, its lit and shadowed halves
    n = (0.7071 * 2.6, 0.7071 * 2.6)
    base_l, base_r, tip = (a[0] - n[0], a[1] - n[1]), (a[0] + n[0], a[1] + n[1]), (2.4, 12.6)
    lit = icon.facet([base_l, a, tip], (0, 0, 1)) - stick
    dark = icon.facet([a, base_r, tip], (0, 0, 1)) - stick - lit
    icon.paint(lit, vi, outline=False, flat=4)
    icon.paint(dark, vi, outline=False, flat=2)
    icon.outline(stick | lit | dark, vi, over=False)
    put(icon, [(2, 12), (3, 12)], vi[5])
    band = [p for p in stick.keys() if 0.55 < t_of(p) < 0.72]
    put(icon, band, ir[4])
    put(icon, [p for p in band if p[0] + p[1] < 15], ir[5])
    put(icon, [(7, 6), (6, 8)], vi[4])
    # the stroke: from the tip, the chalk's own violet; a fresh glint travels along it
    stroke = [(2, 13), (1, 14), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15), (7, 14), (8, 14), (9, 14), (10, 13)]
    put(icon, stroke, vi[4])
    put(icon, [stroke[(frame * 3 + 2) % len(stroke)]], vi[5])
    put(icon, [(0, 12), (1, 11)], vi[3])
    return icon

def resonant_crystal(frame=0):
    """One double-pointed crystal floating upright (exactly symmetric outline): three faces - lit, front, shadow - with
    hard ridges, a spirit core humming inside; ripples of resonance spread from it on both sides (animated)."""
    icon = Icon(16)
    vi, sp = RAMPS["violet"], RAMPS["spirit"]
    top, bot = (8.0, 0.6), (8.0, 15.4)
    L, R, y0, y1 = 3.8, 12.2, 4.6, 11.4
    faces = [
        ([top, (L, y0), (L, y1), bot, (6.4, y1), (6.4, y0)], 4),      # left face, lit
        ([top, (6.4, y0), (6.4, y1), bot, (9.6, y1), (9.6, y0)], 3),  # front face
        ([top, (9.6, y0), (9.6, y1), bot, (R, y1), (R, y0)], 2),      # right face, in shadow
    ]
    whole = Part({})
    for pts, idx in faces:
        part = icon.facet(pts, (0, 0, 1)) - whole
        icon.paint(part, vi, outline=False, flat=idx)
        whole = whole | part
    icon.outline(whole, vi)
    for x in (6, 9):   # ridges
        put(icon, [(x, y) for y in range(5, 11)], vi[5] if x == 6 else vi[3])
    put(icon, [(7, 2), (6, 3)], vi[5])
    hum = frame % 4
    put(icon, [(7, 7), (8, 7), (7, 8), (8, 8)], sp[4] if hum % 2 else sp[3])
    put(icon, [(7, 6), (8, 9)] if hum in (1, 2) else [], sp[5])
    if hum:   # ripples on both sides, mirrored exactly
        r = 5.0 + hum * 1.0
        for deg in (-30, -10, 10, 30):
            x = math.floor(8 + r * math.cos(math.radians(deg)))
            y = math.floor(8 + r * math.sin(math.radians(deg)))
            for p in ((x, y), (15 - x, y)):
                if p not in whole.normals and 0 <= p[0] < 16:
                    put(icon, [p], sp[4], 250 - hum * 50)
    return icon

def bound_sigil(frame=0):
    """The tier-1 core component: a silver medallion carrying the Bound sigil (Session B) - a violet ring, a triangle
    clamped to it at its three corners, a bound spirit glowing at its heart. Exactly symmetric. Animated: the spirit
    pulses, a twinkle."""
    icon = Icon(16)
    ir, vi, sp, st = RAMPS["iron"], RAMPS["violet"], RAMPS["spirit"], RAMPS["boundsteel"]
    rim = icon.ring(8.0, 8.0, 7.4, 5.6)
    icon.paint(rim, ir, bias=0.1)
    face = icon.sphere(8.0, 8.0, 5.7)
    face = Part({p: _norm((n[0] * 0.3, n[1] * 0.3, n[2])) for p, n in face.normals.items()})
    icon.paint(face, RAMPS["ink"], outline=False, flat=1)
    put(icon, [p for p in face.keys() if p[0] + p[1] < 10], RAMPS["ink"][2])   # a little light on the upper left
    # the triangle as crisp 1 px lines (thick lines filled the small triangle in), mirrored for exact symmetry
    left = line_px((7, 3), (3, 11)) + [(x, 11) for x in range(3, 8)]
    tri = left + [(15 - x, y) for (x, y) in left]
    put(icon, tri, vi[5] if frame % 4 in (1, 2) else vi[4])
    put(icon, [(7, 2), (8, 2), (2, 11), (13, 11)], ir[5])   # the clamps at the corners
    spirit = icon.sphere(8.0, 8.4, 1.6)
    icon.paint(spirit, sp, bias=[0.1, 0.35, 0.25, 0.0][frame % 4], outline=False)
    mirror_silhouette(icon)
    icon.twinkle(14, 1, [0, 1, 2, 1][frame % 4], sp)
    return icon

D1 = [("Bound Steel", bound_steel, 4), ("Bound Chalk", bound_chalk, 4), ("Resonant Crystal", resonant_crystal, 4),
      ("Bound Sigil", bound_sigil, 4)]


# ================================================================== D2: boss drops and the gate catalyst

def frenzied_edge(frame=0):
    """A broken blade shard: a straight back, a serrated cutting edge glowing crimson with the berserker's frenzy (it
    pulses like a heartbeat), a jagged break at the base."""
    icon = Icon(16)
    ir, cr = RAMPS["iron"], RAMPS["crimson"]
    # deep serrations on the cutting edge (lower right), a jagged break at the base (lower left)
    edge_pts = [(15.0, 0.8), (13.6, 5.6), (11.6, 5.0), (11.6, 8.2), (9.4, 7.6), (9.4, 10.8), (7.2, 10.2), (7.0, 13.4)]
    outline_pts = edge_pts + [(5.4, 14.6), (4.8, 12.6), (3.0, 14.2), (2.6, 11.8), (0.8, 12.0), (2.0, 9.6), (10.8, 1.6)]
    blade = icon.polygon(outline_pts, bevel=0.8)
    ridge = ((15.0, 0.8), (3.8, 12.0))
    # two bevels either side of the central ridge
    for (x, y) in blade.keys():
        side = (x + 0.5 - ridge[0][0]) * (ridge[1][1] - ridge[0][1]) - (y + 0.5 - ridge[0][1]) * (ridge[1][0] - ridge[0][0])
        put(icon, [(x, y)], ir[4] if side > 0 else ir[2])
    put(icon, [p for p in line_px(*ridge) if p in blade.normals], ir[5])
    icon.outline(blade, ir)
    # the cutting edge glows with frenzy
    beat = [4, 5, 3, 3][frame % 4]
    for (x, y) in blade.keys():
        if any((x + dx, y + dy) not in blade.normals for dx, dy in ((1, 0), (0, 1), (1, 1))) and x + y > 15:
            put(icon, [(x, y)], cr[beat])
    return icon


def dusk_membrane(frame=0):
    """A bat-like wing: the arm arches up from the wrist to the wing tip, three fingers fan down from the wrist and end
    in claws past the skin, the skin between them is scalloped; dusk-coloured - violet near the arm, a sunset glow at
    the trailing edge. A small thumb claw hooks up at the wrist."""
    icon = Icon(16)
    du, bone = RAMPS["dusk"], RAMPS["bone"]
    wrist = (2.0, 9.4)
    ctrl, tip = (5.6, 0.6), (15.2, 1.6)
    arm = [((1 - t) ** 2 * wrist[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0],
            (1 - t) ** 2 * wrist[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]) for t in [k / 10 for k in range(11)]]
    fingers = [(15.4, 9.4), (11.0, 15.2), (4.6, 15.4)]
    mem = icon.facet(arm + fingers, (0, 0, 1))
    edge = [tip] + fingers
    for (t0, t1) in zip(edge, edge[1:]):   # scallops between the fingers
        mx, my = (t0[0] + t1[0]) / 2, (t0[1] + t1[1]) / 2
        cx, cy = mx + (mx - wrist[0]) * 0.22, my + (my - wrist[1]) * 0.22
        r = math.hypot(t1[0] - t0[0], t1[1] - t0[1]) * 0.5
        mem = Part({p: n for p, n in mem.normals.items() if math.hypot(p[0] + 0.5 - cx, p[1] + 0.5 - cy) > r})
    for (x, y) in mem.keys():   # dusk: dark violet under the arm, glowing toward the trailing edge
        d = min(math.hypot(x + 0.5 - ax, y + 0.5 - ay) for ax, ay in arm)
        put(icon, [(x, y)], du[1] if d < 1.6 else du[2] if d < 3.6 else du[3] if d < 6.0 else du[4])
    icon.outline(mem, [du[0], du[0]])
    put(icon, [p for a, b in zip(arm, arm[1:]) for p in line_px(a, b)], bone[4])
    for f in fingers:
        pts = line_px(wrist, f)
        put(icon, pts, bone[3])
        put(icon, pts[-1:], bone[5])
    put(icon, [(0, 7), (1, 8), (0, 6)], bone[4])   # the thumb claw
    put(icon, [(1, 9), (2, 9), (2, 10)], bone[5])
    return icon


def mirror_dust(frame=0):
    """A small heap of silver glitter with mirror flakes standing in it; the flakes reflect violet and cyan, and
    twinkles move across the heap."""
    icon = Icon(16)
    ir, vi, sp = RAMPS["iron"], RAMPS["violet"], RAMPS["spirit"]
    heap = cut(icon.sphere(8.0, 15.0, 6.6, squash=0.8), lambda x, y: y <= 14)
    icon.paint(heap, ir, bias=0.12, outline_ramp=[RAMPS["boundsteel"][0], RAMPS["boundsteel"][1]])
    put(icon, [(x, 15) for x in range(2, 14)], RAMPS["boundsteel"][1])
    for (x, y) in heap.keys():   # glitter grain
        if (x * 7 + y * 3) % 5 == 0:
            put(icon, [(x, y)], ir[5] if (x + y) % 2 else ir[2])
    flakes = [([(4.0, 10.4), (6.6, 5.6), (7.6, 9.6)], vi), ([(8.6, 9.8), (11.6, 4.0), (12.4, 9.0)], sp)]
    for pts, ramp in flakes:
        f = icon.facet(pts, (0, 0, 1))
        for (x, y) in f.keys():
            put(icon, [(x, y)], ramp[4] if (x + y) % 3 else ramp[5])
        icon.outline(f, [ir[0], ir[1]], over=False)
    spots = [(3, 3), (14, 2), (13, 12), (2, 12)]
    icon.twinkle(*spots[frame % 4], 2, sp)
    icon.twinkle(*spots[(frame + 2) % 4], 1, vi)
    return icon


def evokers_sigil(frame=0):
    """Gold fangs - the evoker's jaws - clamped shut on a cut emerald; green magic curls round it (animated)."""
    icon = Icon(16)
    gd, em = RAMPS["gold"], RAMPS["emerald"]
    gem = [([(8.0, 4.6), (12.4, 8.6), (8.0, 8.6)], 3), ([(8.0, 4.6), (8.0, 8.6), (3.6, 8.6)], 4),
           ([(3.6, 8.6), (8.0, 8.6), (8.0, 12.6)], 3), ([(8.0, 8.6), (12.4, 8.6), (8.0, 12.6)], 1)]
    whole = Part({})
    for pts, idx in gem:
        part = icon.facet(pts, (0, 0, 1)) - whole
        icon.paint(part, em, outline=False, flat=idx)
        whole = whole | part
    icon.outline(whole, em)
    put(icon, [(6, 7), (7, 6)], em[5])
    # the jaws: an upper and a lower gold band, fangs biting toward the gem
    upper = icon.tubes([((1.4, 6.0), (4.0, 3.0)), ((4.0, 3.0), (12.0, 3.0)), ((12.0, 3.0), (14.6, 6.0))], 1.1)
    lower = icon.tubes([((1.4, 11.0), (4.0, 14.0)), ((4.0, 14.0), (12.0, 14.0)), ((12.0, 14.0), (14.6, 11.0))], 1.1)
    icon.paint(upper, gd, bias=0.15, outline_over=False)
    icon.paint(lower, gd, bias=-0.05, outline_over=False)
    for x in (4, 7, 10):   # big fangs: down from the upper jaw, up from the lower, interlocking
        put(icon, [(x, 4), (x + 1, 4), (x, 5), (x + 1, 5)], gd[4])
        put(icon, [(x, 6)], gd[5])
    for x in (5, 8, 11):
        put(icon, [(x, 13), (x + 1, 13), (x, 12), (x + 1, 12)], gd[3])
        put(icon, [(x + 1, 11)], gd[4])
    # green magic curling round (a few motes orbiting)
    orbit = [(1, 2), (14, 1), (15, 13), (0, 14)]
    put(icon, [orbit[frame % 4]], em[4])
    put(icon, [orbit[(frame + 2) % 4]], em[3], 180)
    return icon


TOTEM = [  # the totem's outline (a big head, arms out, a body narrowing to a point) - our own pixels, its shape
    "................",
    ".....######.....",
    "....########....",
    "....########....",
    "....########....",
    "....########....",
    "....########....",
    "....########....",
    ".##############.",
    ".##############.",
    "..############..",
    "....########....",
    "....########....",
    ".....######.....",
    ".....######.....",
    "......####......",
]


def archevokers_effigy(frame=0):
    """A reskin of the totem's familiar shape as the Archevoker: a grey-green illager face with the heavy brow and long
    nose, eyes glowing emerald, a dark robe with outstretched sleeves and gold trim. Animated: the eyes flare."""
    icon = Icon(16)
    skin, robe, gd, em = RAMPS["ash"], RAMPS["ink"], RAMPS["gold"], RAMPS["emerald"]
    mask = {(x, y) for y, row in enumerate(TOTEM) for x, c in enumerate(row) if c == "#"}
    head = Part({p: n for p, n in icon.box(4.0, 1.0, 12.0, 8.0, bevel=1.6).normals.items() if p in mask})
    body = Part({p: n for p, n in icon.polygon([(1, 8), (15, 8), (15, 10), (12, 11), (11, 16), (5, 16), (4, 11), (1, 10)],
                                               bevel=1.6).normals.items() if p in mask and p[1] >= 8})
    icon.paint(body, robe, bias=0.3, outline=False)
    icon.paint(head, skin + [skin[-1]], bias=0.42, outline=False)
    icon.outline(head | body, [robe[0], robe[1]])
    # face: hair line, the heavy brow, glowing eyes, the long nose
    put(icon, [(x, 1) for x in range(5, 11)], robe[2])
    put(icon, [(x, 3) for x in range(5, 11)], robe[1])
    eye = em[5] if frame % 4 in (1, 2) else em[4]
    put(icon, [(6, 4), (9, 4)], eye)
    put(icon, [(7, 4), (8, 4)], skin[2])
    put(icon, [(7, 5), (8, 5), (7, 6), (8, 6), (7, 7), (8, 7)], skin[2])
    put(icon, [(7, 5), (7, 6)], skin[3])
    # gold collar and trim down the robe, cuffs at the sleeve ends
    put(icon, [(x, 8) for x in range(4, 12)], gd[3])
    put(icon, [(7, y) for y in range(9, 15)] + [(8, y) for y in range(9, 15)], gd[2])
    put(icon, [(7, 9), (8, 9)], gd[4])
    put(icon, [(1, 8), (1, 9), (14, 8), (14, 9)], gd[3])
    if frame % 4 == 2:
        put(icon, [(0, 7), (15, 7)], em[4])
    return icon

D2 = [("Frenzied Edge", frenzied_edge, 4), ("Dusk Membrane", dusk_membrane, 1), ("Mirror Dust", mirror_dust, 4),
      ("Evoker's Sigil", evokers_sigil, 4), ("Archevoker's Effigy", archevokers_effigy, 4)]


# ================================================================== D3: gear

def frenzy_cleaver(frame=0):
    """A heavy cleaver in the vanilla axe's layout (handle from the lower left, head at the top): a broad square blade
    with the cleaver's hanging hole, a wrapped handle, the cutting edge glowing crimson with frenzy (pulses)."""
    icon = Icon(16)
    ir, cr, lea, wood = RAMPS["iron"], RAMPS["crimson"], RAMPS["leather"], RAMPS["wood"]
    handle = icon.tubes([((1.6, 14.4), (12.6, 3.4))], 1.05)
    icon.paint(handle, wood, bias=0.0)
    for (x, y) in handle.keys():   # leather wrap on the grip
        if x + y > 12 and (x - y) % 3 == 0 and x < 7:
            put(icon, [(x, y)], lea[3])
    # the blade: its spine runs along the top of the handle, it reaches up and to the left
    a, b = (7.4, 8.6), (13.4, 2.6)
    px, py = -0.7071 * 5.4, -0.7071 * 5.4
    c, d = (b[0] + px, b[1] + py), (a[0] + px, a[1] + py)
    blade = icon.facet([a, b, c, d], (0, 0, 1))
    for (x, y) in blade.keys():
        t = ((x + 0.5 - a[0]) * px + (y + 0.5 - a[1]) * py) / (px * px + py * py)   # 0 at the spine, 1 at the edge
        put(icon, [(x, y)], ir[3] if t < 0.3 else ir[4] if t < 0.75 else ir[2])
    icon.outline(blade | handle, ir, over=False)
    beat = [4, 5, 3, 3][frame % 4]
    put(icon, [p for p in line_px(c, d) if p in blade.normals or 0 <= p[0] < 16 and 0 <= p[1] < 16], cr[beat])
    hx, hy = (a[0] + b[0]) / 2 + px * 0.3 + 1.2, (a[1] + b[1]) / 2 + py * 0.3 - 1.2   # the hanging hole
    put(icon, [(math.floor(hx), math.floor(hy))], RAMPS["boundsteel"][0])
    put(icon, [(math.floor(hx) + 1, math.floor(hy) + 1)], ir[5])
    put(icon, [(13, 2), (14, 1)], ir[4])   # the pommel spike above the head
    return icon


SKULL = [
    "..###..",
    ".#####.",
    "#######",
    "#KK#KK#",
    "#Kc#cK#",
    ".##K##.",
    ".#.#.#.",
]


def bone_scepter(frame=0):
    """A necromancer's scepter: a jointed bone rod, a bone collar, and on top a hand-drawn skull, sockets dark with a
    spirit-cyan spark burning in each; a wisp rises (animated)."""
    icon = Icon(16)
    bone, sp, ink = RAMPS["bone"], RAMPS["spirit"], RAMPS["ink"]
    rod = icon.tubes([((1.4, 14.6), (9.6, 6.4))], 0.95)
    icon.paint(rod, bone, bias=-0.05)
    for (x, y) in rod.keys():
        if (x + (15 - y)) % 4 == 0:
            put(icon, [(x, y)], bone[1])
    collar = icon.sphere(10.0, 7.6, 1.7, squash=0.7)
    icon.paint(collar, bone, bias=0.0, outline_over=False)
    x0, y0 = 8, 0
    mask = {(x0 + x, y0 + y) for y, row in enumerate(SKULL) for x, c in enumerate(row) if c != "."}
    for (x, y) in mask:   # light from the top left: lighter left half, darker right
        put(icon, [(x, y)], bone[4] if x < x0 + 3 else bone[3] if x == x0 + 3 else bone[2])
    put(icon, [(x0 + 2, y0), (x0 + 1, y0 + 1)], bone[5])
    glow = sp[5] if frame % 4 in (1, 2) else sp[4]
    pixmap(icon, SKULL, x0, y0, {"K": ink[0], "c": glow})
    put(icon, [(x0 + 3, y0 + 5)], ink[1])
    icon.outline(Part({p: (0, 0, 1) for p in mask}), [bone[0], bone[1]], over=False)
    wisp = [[(15, 2)], [(15, 1), (14, 0)], [(15, 0)], []][frame % 4]
    put(icon, wisp, sp[4], 200)
    return icon

def duskwing_charm(frame=0):
    """A violet gem hung on a small loop, two dusk wings spread from it; the wings beat (animated)."""
    icon = Icon(16)
    du, vi, bone, ir = RAMPS["dusk"], RAMPS["violet"], RAMPS["bone"], RAMPS["iron"]
    lift = [0, -2, -3, -1][frame % 4]
    for side in (-1, 1):
        root = (8 + side * 2.0, 8.4)
        tip = (8 + side * 7.4, 4.6 + lift)
        low = (8 + side * 6.0, 10.6 + lift * 0.4)
        wing = icon.facet([root, tip, (8 + side * 5.8, 8.0 + lift * 0.6), low], (0, 0, 1))
        for (x, y) in wing.keys():
            d = abs(x + 0.5 - root[0])
            put(icon, [(x, y)], du[2] if d < 2 else du[3] if d < 4 else du[4])
        icon.outline(wing, [du[0], du[0]], over=False)
        put(icon, [p for p in line_px(root, tip)], bone[4])
    gem = icon.sphere(8.0, 9.0, 2.6)
    icon.paint(gem, vi, bias=0.2, outline_ramp=[ir[1], ir[2]])
    put(icon, [(7, 8)], vi[5])
    return icon


GHOST = [".####.", "######", "#K##K#", "######", "######", "#.##.#"]


def mirror_ward(frame=0):
    """An exactly symmetric heater shield of mirror glass in a silver rim; the decoy it conjures shows in the glass as a
    small violet ghost; a band of shine slides down the glass (animated)."""
    icon = Icon(16)
    ir, gl, vi = RAMPS["iron"], RAMPS["glass"], RAMPS["violet"]
    rim = icon.polygon([(1.5, 1.5), (14.5, 1.5), (14.5, 7.2), (8.0, 15.2), (1.5, 7.2)], bevel=1.4)
    icon.paint(rim, ir, bias=0.1)
    glass = icon.facet([(3.2, 3.2), (12.8, 3.2), (12.8, 6.8), (8.0, 12.8), (3.2, 6.8)], (0, 0, 1))
    for (x, y) in glass.keys():
        put(icon, [(x, y)], gl[4] if x < 8 else gl[3])
    shine = 3 + frame * 2
    put(icon, [p for p in glass.keys() if p[1] in (shine, shine + 1)], gl[5])
    pixmap(icon, GHOST, 5, 4, {"#": vi[3], "K": vi[0]})
    put(icon, [(7, 1), (8, 1)], RAMPS["spirit"][4])
    mirror_silhouette(icon)
    return icon

def scrying_mirror(frame=0):
    """A scrying orb: a glass ball dark with turning violet mist, an eye opening in its depths, a bright highlight on
    the glass; it rests in a silver claw stand. Animated: the mist turns, the eye opens and closes."""
    icon = Icon(16)
    ir, vi, sp, ink = RAMPS["iron"], RAMPS["violet"], RAMPS["spirit"], RAMPS["ink"]
    base = icon.box(4.4, 13.2, 11.6, 15.6, bevel=0.9)
    icon.paint(base, ir, bias=0.0)
    orb = icon.sphere(8.0, 7.0, 5.9)
    icon.paint(orb, ink, bias=0.1, outline_ramp=[vi[0], vi[1]])
    for (x, y) in orb.keys():   # mist turning inside
        a = math.atan2(y + 0.5 - 7.0, x + 0.5 - 8.0) + frame * math.pi / 2
        d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 7.0)
        if 2.0 < d < 5.0 and math.sin(a * 2 + d) > 0.55:
            put(icon, [(x, y)], vi[3])
    for (x0, y0, x1, y1) in ((3.6, 10.6, 5.0, 13.4), (12.4, 10.6, 11.0, 13.4), (8.0, 12.2, 8.0, 13.4)):   # the claws
        put(icon, line_px((x0, y0), (x1, y1)), ir[4])
    put(icon, [(4, 4), (5, 3), (4, 5), (6, 3)], gl := RAMPS["glass"][5])
    put(icon, [(11, 10), (12, 9)], vi[4])
    open_ = [1, 2, 2, 0][frame % 4]
    if open_ == 0:
        put(icon, [(6, 7), (7, 7), (8, 7), (9, 7)], vi[4])
    else:
        put(icon, [(6, 7), (9, 7), (7, 6), (8, 6), (7, 8), (8, 8)], vi[4])
        put(icon, [(7, 7), (8, 7)], sp[5] if open_ == 2 else sp[4])
    return icon

D3 = [("Frenzy Cleaver", frenzy_cleaver, 4), ("Bone Scepter", bone_scepter, 4), ("Duskwing Charm", duskwing_charm, 4),
      ("Mirror Ward", mirror_ward, 4), ("Scrying Mirror", scrying_mirror, 4)]


# ================================================================== D4: contracts (one family) and decorations

def _c(ramp, i):
    return RAMPS[ramp][i]


# 5x5 emblems drawn on the parchment (letters -> colours); every contract shares the scroll, the emblem and seal differ
EMBLEMS = {
    "harvest": (["..y..", ".y.y.", "..y..", ".y.y.", "..s.."], {"y": _c("gold", 2), "s": _c("emerald", 2)}),
    "gather": (["wwwww", "wwgww", "kkkkk", "wwwww", "wwwww"], {"w": _c("wood", 3), "g": _c("gold", 4), "k": _c("wood", 1)}),
    "brewer": (["..k..", ".kmk.", "mmmmm", "mMmmm", ".mmm."], {"k": _c("glass", 3), "m": _c("blossom", 2), "M": _c("blossom", 4)}),
    "shepherd": (["k...k", ".k.k.", "..k..", ".r.r.", "r...r"], {"k": _c("iron", 4), "r": _c("crimson", 3)}),  # shears
    "beekeeper": ([".hhh.", "h.h.h", "hhhhh", "h.h.h", ".hhh."], {"h": _c("pollen", 1)}),
    "acolyte": (["..e..", "..c..", "bbbbb", ".bbb.", "....."], {"e": _c("ember", 4), "c": _c("bone", 4), "b": _c("ash", 2)}),
    "ward": (["sssss", "sckcs", "scccs", ".scs.", "..s.."], {"s": _c("iron", 3), "c": _c("spirit", 3), "k": _c("ink", 0)}),
}
SEALS = {"harvest": "gold", "gather": "wood", "brewer": "blossom", "shepherd": "chalk", "beekeeper": "pollen",
         "acolyte": "ember", "ward": "spirit"}


def contract(kind):
    """A spirit contract: a parchment sheet between two rolls, lines of writing, the duty's emblem, and a wax seal in
    the duty's colour with two ribbon tails."""
    def make(frame=0):
        icon = Icon(16)
        pa = RAMPS["parchment"]
        # a sheet tilted on the diagonal (a square sheet filling the slot read as a door)
        c = (8.0, 8.0)
        ux, uy = math.cos(math.radians(-20)), math.sin(math.radians(-20))
        vx, vy = -uy, ux

        def at(u, v):
            return (c[0] + u * ux + v * vx, c[1] + u * uy + v * vy)

        sheet = icon.facet([at(-4.5, -5), at(4.5, -5), at(4.5, 5), at(-4.5, 5)], (0, 0, 1))
        icon.paint(sheet, pa, outline=False, flat=4)
        for (x, y) in sheet.keys():   # the sheet curls a little toward its rolls
            u = (x + 0.5 - c[0]) * ux + (y + 0.5 - c[1]) * uy
            v = (x + 0.5 - c[0]) * vx + (y + 0.5 - c[1]) * vy
            if abs(v) > 3.8:
                put(icon, [(x, y)], pa[3])
            elif u > 3.4:
                put(icon, [(x, y)], pa[3])
        icon.outline(sheet, pa, over=False)
        for v0, bias in ((-5.0, 0.05), (5.0, -0.1)):
            roll = icon.capsule(at(-5.2, v0), at(5.2, v0), 1.5)
            icon.paint(roll, pa, bias=bias, outline_over=False)
        rows, colours = EMBLEMS[kind]
        ex, ey = at(-0.4, -1.4)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in colours:
                    put(icon, [(round(ex - 2.5) + x, round(ey - 2.5) + y)], colours[ch])
        for v in (2.0, 3.2):
            put(icon, [p for p in line_px(at(-3.4, v), at(1.6 if v > 2.5 else 2.6, v)) if p in sheet.normals], pa[2])
        seal_ramp = RAMPS[SEALS[kind]]
        sx, sy = at(3.0, 4.6)
        put(icon, [(round(sx) - 1, round(sy) + 2), (round(sx) + 1, round(sy) + 3)], seal_ramp[2])
        seal = icon.sphere(sx, sy, 2.1)
        icon.paint(seal, seal_ramp, bias=0.05, outline_ramp=[seal_ramp[0], seal_ramp[1]])
        put(icon, [(math.floor(sx), math.floor(sy))], seal_ramp[1])
        return icon
    return make


def moonlit_lily(frame=0):
    """A sprig of lily of the valley: white bells hanging from an arching stem, broad leaves at its foot, a little
    crescent moon above; the stars around it twinkle in turn (animated)."""
    icon = Icon(16)
    leaf, sp, bone = RAMPS["emerald"], RAMPS["spirit"], RAMPS["bone"]
    for (cx, cy, ang) in ((4.6, 11.6, 250), (9.6, 12.2, 300)):
        part = Part({})
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for x, y, px, py in icon._cells():
            u, v = (px - cx) * ca + (py - cy) * sa, -(px - cx) * sa + (py - cy) * ca
            if (u / 4.2) ** 2 + (v / 1.6) ** 2 <= 1:
                part.normals[(x, y)] = _norm((-sa * v * 0.4, ca * v * 0.4, 1))
        icon.paint(part, leaf, bias=-0.15)
    stem = [(7.0, 15.0), (7.0, 11.0), (7.6, 7.0), (9.2, 4.4), (11.6, 3.6), (13.4, 5.0)]
    put(icon, [p for a, b in zip(stem, stem[1:]) for p in line_px(a, b)], leaf[3])
    for (x, y) in ((8, 7), (10, 5), (12, 5), (14, 7)):   # bells hanging from the stem
        bell = icon.sphere(x + 0.5, y + 1.6, 1.25)
        icon.paint(bell, bone, bias=0.3, outline_ramp=[leaf[0], leaf[1]], outline_over=False)
        put(icon, [(x, y + 2)], sp[4])
    moon = Part({(x, y): (0, 0, 1) for x, y, px, py in icon._cells()
                 if math.hypot(px - 3.0, py - 3.0) < 2.3 and math.hypot(px - 4.2, py - 2.2) >= 2.0})
    icon.paint(moon, RAMPS["gold"], outline=False, flat=4)
    stars = [(1, 8), (6, 1), (15, 1), (14, 12)]
    for k, (x, y) in enumerate(stars):
        size = [2, 1, 0, 1][(k + frame) % 4]
        icon.twinkle(x, y, min(size, 1) if x in (1, 15) or y in (1,) else size, sp)
    return icon


def witchcap(frame=0):
    """A crimson fungus whose cap bubbles like a witch's brew - green bubbles rise from it and pop (animated)."""
    icon = Icon(16)
    cr, br, bone = RAMPS["crimson"], RAMPS["brew"], RAMPS["bone"]
    stem = icon.box(6.4, 8.6, 9.6, 15.6, bevel=1.2)
    icon.paint(stem, bone, bias=-0.05)
    put(icon, [(7, 10), (8, 12), (7, 13)], cr[2])
    cap = cut(icon.sphere(8.0, 9.4, 6.8, squash=0.82), lambda x, y: y <= 9)
    icon.paint(cap, cr, bias=0.05, outline_over=False)
    put(icon, [(x, 9) for x in range(2, 14)], cr[1])   # the gills' shadow under the rim
    for (x, y) in ((5, 5), (9, 4), (11, 7), (4, 7)):   # brew spots on the cap
        put(icon, [(x, y), (x + 1, y)], br[3])
    put(icon, [(5, 4)], br[4])
    for (x, start) in ((6, 0), (10, 2), (8, 1)):      # bubbles rising and popping
        stage = (frame + start) % 4
        y = 3 - stage
        if stage < 3 and y >= 0:
            put(icon, [(x, y)], br[4] if stage else br[5])
        elif y >= 0:
            put(icon, [(x - 1, y), (x + 1, y)], br[4], 150)
    put(icon, [(12, 10), (12, 11)], br[3])   # a drip off the rim
    return icon


D4 = [(f"Contract: {n.title()}" if n != "brewer" else "Contract: Brewer's Aid", contract(n), 1) for n in EMBLEMS] + \
     [("Moonlit Lily", moonlit_lily, 4), ("Witchcap", witchcap, 4)]
GROUPS = {"d1": D1, "d2": D2, "d3": D3, "d4": D4}


def tier1_set():
    """Every tier-1 icon (Session A's Spirit Essence included), first frame."""
    from PIL import Image
    essence = Image.open(os.path.join(OUT, "..", "session-a", "spirit_essence.png")).convert("RGBA")
    icons = [("Spirit Essence", essence)]
    for group in (D1, D2, D3, D4):
        icons += [(name, make(0).img) for name, make, _ in group]
    return icons


def slug(name):
    return name.lower().replace("'", "").replace(":", "").replace(" ", "_")


def render(which, version):
    suffix = "" if version == "final" else "-" + version
    statics, animated = [], []
    for name, make, frames in GROUPS[which]:
        icons = [make(f) for f in range(frames)]
        if frames == 1:
            icons[0].save(os.path.join(OUT, slug(name) + ".png"))
        else:
            for f, icon in enumerate(icons):
                icon.save(os.path.join(OUT, f"{slug(name)}_{f}.png"))
            animated.append((name, [i.img for i in icons]))
        statics.append((name, icons[0].img))
    print(review.sheet(statics, os.path.join(OUT, f"review-{which}{suffix}.png")))
    if animated:
        from session_b import frame_sheet
        print(frame_sheet(animated, os.path.join(OUT, f"review-{which}-anim{suffix}.png")))


if __name__ == "__main__" and sys.argv[1:2] == ["set"]:
    icons = tier1_set()
    print(review.inventory(icons, os.path.join(OUT, "review-tier1-inventory.png"), cols=8))
    print(review.inventory(icons, os.path.join(OUT, "review-tier1-inventory-1x.png"), cols=8, scale=2))
    anim = [(name, make, n) for group in (D1, D2, D3, D4) for name, make, n in group if n > 1]
    review.gif([[make(f % n).img for f in range(4)] for _, make, n in anim], os.path.join(OUT, "preview-tier1-animated.gif"),
               ms=170, scale=5)
    sys.exit()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "d1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    render(which, version)
