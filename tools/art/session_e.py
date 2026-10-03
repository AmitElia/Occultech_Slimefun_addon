"""Session E: tier-2 item icons (16 px). Tier 2 is *Abyssal*: deep teal and prismarine, sea glow as the magic, iron and
gold fittings; boss drops keep their boss's colours (Blaze Choir ember and gold, Tempest wind, Guardian prismarine).
Full-cube blocks go to Session G; decorations that are objects (jars, chimes, braziers...) get icons here.

Run: python tools/art/session_e.py e1 [version]   (e1 materials, e2 drops, e3 weapons, e4 armor, e5 decor, set)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part, _norm  # noqa: E402
from session_c import cut, put, flat_face, line_px  # noqa: E402
from session_d import bar, pixmap, mirror_silhouette  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-e")
os.makedirs(OUT, exist_ok=True)


def mask_part(icon, rows, normal_fn=None):
    """A Part from a hand-drawn mask (rows of '#'); normals from normal_fn(x, y) or facing the viewer."""
    out = {}
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                out[(x, y)] = normal_fn(x, y) if normal_fn else (0.0, 0.0, 1.0)
    return Part(out)


def dome_normals(cx, cy, rx, ry):
    """Normals of a soft dome over a mask: lit top-left, shadowed bottom-right, by distance from (cx, cy)."""
    def fn(x, y):
        dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        return _norm((dx * 0.8, dy * 0.8, max(0.2, 1 - (dx * dx + dy * dy) * 0.5)))
    return fn


# ================================================================== E1: materials, component, catalyst, tether

def abyssal_alloy(frame=0):
    """The ingot family's third metal: deep abyssal teal, a sea-glow wave inlaid along the bar that ripples (animated)."""
    icon = Icon(16)
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    top, left, right, d = bar(icon, ab, tones=(4, 3, 2))
    put(icon, [(2, 9), (3, 8), (4, 7), (5, 7), (6, 6), (7, 5), (8, 5), (9, 4)], ab[5])
    put(icon, [(5, 12), (5, 13), (5, 14)], ab[4])
    wave = [(4, 8), (5, 8), (6, 7), (7, 7), (8, 6), (9, 6), (10, 5)]
    for i, p in enumerate(wave):   # a crest of light travels along the inlay
        put(icon, [p], sg[5] if (i - frame * 2) % 7 in (0, 1) else sg[3])
    return icon


def tide_glass(frame=0):
    """A thick hexagonal tile of sea glass: bright bevelled edges, a clear inside where caustic light lines wander
    (animated)."""
    icon = Icon(16)
    sg, wd = RAMPS["seaglow"], RAMPS["wind"]
    hexa = [(8.0 + 7.2 * math.cos(math.radians(a)), 8.0 + 6.6 * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    tile = icon.polygon(hexa, bevel=2.2)
    icon.paint(tile, sg, bias=0.0)
    inner = icon.polygon([(8.0 + 4.6 * math.cos(math.radians(a)), 8.0 + 4.2 * math.sin(math.radians(a)))
                          for a in range(-90, 270, 60)], bevel=0.5)
    for p in inner.keys():   # see-through: the middle of the tile is darker than its bevelled rim
        put(icon, [p], sg[1])
    k = frame % 4
    for y0 in (6, 9):   # caustic lines drifting through the glass
        for x in range(4, 12):
            y = y0 + round(math.sin((x + k * 1.6) * 0.9))
            if (x, y) in inner.normals:
                put(icon, [(x, y)], sg[3])
    put(icon, [(5, 3), (4, 4), (3, 5)], wd[5])
    mirror_silhouette(icon)
    return icon


def abyssal_sigil(frame=0):
    """The tier-2 core component: a medallion carrying the Abyssal sigil (Session B) - an abyssal ring round a dark
    face, a sea-glow eye watching from it, waves below. Exactly symmetric. Animated: the eye blinks, a twinkle."""
    icon = Icon(16)
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    rim = icon.ring(8.0, 8.0, 7.4, 5.6)
    icon.paint(rim, ab, bias=0.25)
    face = icon.sphere(8.0, 8.0, 5.7)
    icon.paint(face, ab, outline=False, flat=0)
    put(icon, [p for p in face.keys() if p[0] + p[1] < 10], ab[1])
    blink = frame % 4 == 3
    if blink:
        put(icon, [(x, 7) for x in range(4, 12)], sg[3])
    else:
        lids = [(4, 7), (5, 6), (6, 5), (7, 5), (8, 5), (9, 5), (10, 6), (11, 7),
                (5, 8), (6, 9), (7, 9), (8, 9), (9, 9), (10, 8)]
        put(icon, lids, sg[3])
        put(icon, [(6, 7), (7, 6), (8, 6), (9, 7), (7, 8), (8, 8), (6, 6), (9, 6)], sg[1])
        put(icon, [(7, 7), (8, 7)], sg[5] if frame % 4 == 1 else sg[4])
    put(icon, [(5, 11), (6, 12), (7, 11), (8, 11), (9, 12), (10, 11)], sg[2])   # the waves, gentle and low
    mirror_silhouette(icon)
    icon.twinkle(14, 1, [0, 1, 2, 1][frame % 4], sg)
    return icon


def tide_relic(frame=0):
    """The Drowned Elder's summoning relic: an octagonal cage of carved prismarine bound with gold, holding a glowing
    sea eye that looks about (animated)."""
    icon = Icon(16)
    ab, sg, gd = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["gold"]
    octa = [(8.0 + 7.4 * math.cos(math.radians(a)), 8.0 + 7.4 * math.sin(math.radians(a))) for a in range(-112, 248, 45)]
    cage = icon.polygon(octa, bevel=2.0)
    icon.paint(cage, ab, bias=0.15)
    hole = icon.sphere(8.0, 8.0, 4.6)
    orb = icon.sphere(8.0, 8.0, 4.0)
    for p in hole.keys():
        put(icon, [p], ab[0])
    icon.paint(orb, sg, bias=0.05, outline=False)
    look = [(0, 0), (1, 0), (0, 0), (-1, 0)][frame % 4]
    put(icon, [(7 + look[0], 7), (8 + look[0], 7), (7 + look[0], 8), (8 + look[0], 8)], ab[0])
    put(icon, [(8 + look[0], 7)], sg[5])
    for (x, y) in ((8, 1), (14, 8), (8, 14), (1, 8)):   # gold bindings at the four sides
        put(icon, [(x, y), (15 - x if x != 8 else 7, y) if x != 8 else (7, y)], gd[4])
    put(icon, [(1, 7), (14, 7)], gd[3])
    mirror_silhouette(icon)
    return icon


def abyssal_tether(frame=0):
    """A spectral chain lying on the diagonal: a handle ring at one end, links alternating face-on (hollow) and edge-on
    (a bar), a hook at the other end; a glimmer runs down the links (animated)."""
    icon = Icon(16)
    ab, sg, ir = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["iron"]
    handle = icon.ring(3.0, 3.0, 2.6, 1.3)
    icon.paint(handle, ir, bias=0.15)
    centres = [(5.6, 5.6), (7.4, 7.4), (9.2, 9.2), (11.0, 11.0)]
    for i, (x, y) in enumerate(centres):
        if i % 2 == 0:   # face-on: a hollow oval link
            link = icon.ring(x, y, 1.9, 0.9)
            icon.paint(link, ab, bias=0.3, outline_ramp=[ab[0], ab[1]], outline_over=False)
        else:            # edge-on: a short bar across the chain
            put(icon, line_px((x - 1.0, y + 1.0), (x + 1.0, y - 1.0)), ab[4])
    k = frame % 4
    gx, gy = centres[k]
    put(icon, [(math.floor(gx) - 1, math.floor(gy)), (math.floor(gx), math.floor(gy) - 1)], sg[5])
    # the hook
    put(icon, [(12, 12), (13, 13), (13, 14), (12, 15), (11, 15), (10, 14)], ir[4])
    put(icon, [(14, 13), (14, 12)], ir[3])
    put(icon, [(10, 13)], ir[5])
    return icon


E1 = [("Abyssal Alloy", abyssal_alloy, 4), ("Tide Glass", tide_glass, 4), ("Abyssal Sigil", abyssal_sigil, 4),
      ("Tide Relic", tide_relic, 4), ("Abyssal Tether", abyssal_tether, 4)]


# ================================================================== E2: boss drops

def abyssal_lens(frame=0):
    """A lens for beam weapons, made like a magnifying glass (a shape no other icon has): a gold rim round clear sea
    glass with a fresnel ring, a short handle, the beam's hot point gathering and flaring at the centre (animated)."""
    icon = Icon(16)
    gd, sg, wd = RAMPS["gold"], RAMPS["seaglow"], RAMPS["wind"]
    handle = icon.tubes([((10.6, 10.6), (14.6, 14.6))], 1.2)
    icon.paint(handle, RAMPS["wood"], bias=0.05)
    put(icon, [(11, 11), (12, 12)], gd[4])
    rim = icon.ring(6.6, 6.6, 6.2, 4.6)
    icon.paint(rim, gd, bias=0.05, outline_over=False)
    glass = icon.sphere(6.6, 6.6, 4.7)
    icon.paint(glass, wd, bias=-0.15, outline=False)
    for (x, y) in glass.keys():
        if abs(math.hypot(x + 0.5 - 6.6, y + 0.5 - 6.6) - 3.0) < 0.45:
            put(icon, [(x, y)], sg[3])
    put(icon, [(4, 3), (3, 4), (4, 4)], wd[5])
    hot = [sg[3], sg[4], sg[5], sg[4]][frame % 4]
    put(icon, [(6, 6), (7, 6), (6, 7), (7, 7)], hot)
    if frame % 4 == 2:
        put(icon, [(6, 4), (6, 9), (4, 6), (9, 6)], sg[5])
    return icon


def nautilus_core(frame=0):
    """A nautilus shell drawn as nested whorls (a line spiral turns to mush at 16 px; nested rims read as a coil): a big
    outer whorl with curved stripes, a smaller one inside it, a tiny one at the core; on the right a lipped opening
    where a sea-glow light pulses (animated)."""
    icon = Icon(16)
    bone, wood, sg = RAMPS["bone"], RAMPS["wood"], RAMPS["seaglow"]
    outer = icon.sphere(7.0, 8.2, 6.6)
    icon.paint(outer, bone, bias=0.15, outline_ramp=[wood[0], wood[1]])
    for a0 in (200, 240, 280, 320):   # stripes on the outer whorl, curving with it
        seg = [(7.0 + r * math.cos(math.radians(a0 + r * 8)), 8.2 + r * math.sin(math.radians(a0 + r * 8))) for r in (4.6, 5.4, 6.2)]
        put(icon, [p for a, b in zip(seg, seg[1:]) for p in line_px(a, b) if p in outer.normals], wood[3])
    for (cx, cy, r, bias) in ((5.8, 9.0, 3.8, 0.05), (5.0, 9.6, 1.9, -0.05)):
        whorl = icon.sphere(cx, cy, r)
        rim = [p for p in whorl.keys() if any((p[0] + dx, p[1] + dy) not in whorl.normals
                                              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        icon.paint(whorl, bone, bias=bias, outline=False)
        put(icon, rim, wood[1])
    mouth = icon.sphere(12.6, 9.4, 2.8, squash=1.2)
    icon.paint(mouth, bone, bias=0.35, outline_ramp=[wood[0], wood[1]], outline_over=False)
    glow = [2, 3, 4, 3][frame % 4]
    hollow = icon.sphere(13.0, 9.6, 1.7, squash=1.2)
    for p in hollow.keys():
        put(icon, [p], sg[glow])
    put(icon, [(13, 9)], sg[glow + 1])
    return icon


def choir_ember(frame=0):
    """A flame crystallised mid-flicker, with real volume: a bevelled crystal shaded by the light (lit left, shadowed
    right), a gold ridge down its spine, a white-hot core showing through, a soft glow and sparks (animated)."""
    icon = Icon(16)
    em, gd = RAMPS["ember"], RAMPS["gold"]
    outline_pts = [(8.0, 0.6), (11.0, 5.2), (12.8, 3.8), (13.4, 9.6), (11.2, 14.6), (4.8, 14.6), (2.6, 9.6), (3.4, 5.0),
                   (5.2, 6.4)]
    flame = icon.polygon(outline_pts, bevel=3.2)
    icon.paint(flame, em, bias=-0.05, outline_ramp=[em[0], em[1]])
    pulse = [0.0, 0.2, 0.35, 0.15][frame % 4]
    core = icon.sphere(7.6, 10.2, 2.6, squash=1.3)
    for (x, y) in core.keys():
        d = math.hypot(x + 0.5 - 7.6, (y + 0.5 - 10.2) / 1.3)
        put(icon, [(x, y)], em[5] if d < 1.0 + pulse * 2 else em[4])
    put(icon, line_px((8.0, 1.6), (7.6, 7.4)), gd[5])           # the spine ridge
    put(icon, line_px((11.6, 5.6), (11.0, 10.0)), gd[4])         # a side ridge
    put(icon, [(5, 7), (4, 8), (5, 6)], em[5])                    # light on the lit facet
    icon.glow(em[3], radius=1.4, strength=0.28)
    sparks = [[(14, 2)], [(14, 1), (1, 4)], [(1, 3)], [(15, 6)]][frame % 4]
    put(icon, sparks, gd[4])
    return icon


def tempest_core(frame=0):
    """A pale wind orb at the heart of a whirlwind: ribbons of air spiral round it and turn (animated)."""
    icon = Icon(16)
    wd = RAMPS["wind"]
    orb = icon.sphere(8.0, 8.0, 3.0)
    icon.paint(orb, wd, bias=0.15, outline_ramp=[wd[0], wd[1]])
    for k in range(3):   # three ribbons, rotating a quarter of their spacing each frame
        a0 = k * 2 * math.pi / 3 + frame * math.pi / 6
        pts = [(8.0 + r * math.cos(a0 + r * 0.55), 8.0 + r * math.sin(a0 + r * 0.55) * 0.8) for r in [3.6 + i * 0.4 for i in range(10)]]
        put(icon, [p for a, b in zip(pts, pts[1:]) for p in line_px(a, b) if 0 <= p[0] < 16 and 0 <= p[1] < 16],
            wd[4] if k == 0 else wd[3])
        put(icon, [(math.floor(pts[-1][0]), math.floor(pts[-1][1]))], wd[5])
    return icon


def elder_scale(frame=0):
    """A great scale shed by the Elder: a rounded shield of old prismarine; growth lines follow its outline like a real
    scale's, a little weed clings to it, a sea-glow glint slides over it (animated)."""
    icon = Icon(16)
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]

    def shape(k):   # the outline, shrunk by k toward the scale's base point
        ox, oy = 8.0, 15.0
        circ = [(8.0 + 6.6 * math.cos(math.radians(a)), 6.6 + 6.4 * math.sin(math.radians(a))) for a in range(150, 391, 15)]
        pts = circ + [(8.0, 15.4)]
        return [(ox + (x - ox) * k, oy + (y - oy) * k) for (x, y) in pts]

    scale = icon.polygon(shape(1.0), bevel=2.0)
    icon.paint(scale, ab, bias=0.15)
    for k in (0.72, 0.46):   # growth lines
        inner = icon.facet(shape(k), (0, 0, 1))
        edge = [p for p in inner.keys() if any((p[0] + dx, p[1] + dy) not in inner.normals
                                               for dx, dy in ((1, 0), (-1, 0), (0, -1)))]
        put(icon, edge, ab[2])
    put(icon, [(3, 9), (3, 10), (12, 11)], RAMPS["gel"][2])
    g = [(4, 3), (6, 2), (9, 2), (11, 3)][frame % 4]
    put(icon, [g, (g[0], g[1] + 1)], sg[5])
    mirror_silhouette(icon)
    return icon


E2 = [("Abyssal Lens", abyssal_lens, 4), ("Nautilus Core", nautilus_core, 4), ("Choir Ember", choir_ember, 4),
      ("Tempest Core", tempest_core, 4), ("Elder Scale", elder_scale, 4)]


# ================================================================== E3: weapons and the Choir Bell

def scepter(icon, rod_ramp, band_ramp, prong_ramp, tip_colour):
    """The shared scepter build, drawn as its future 3D model would look: a shaded rod with bands and a collar, three
    claw prongs from the collar - one behind the head, two in front - cradling whatever sits at (10.6, 5.2).
    Returns a function that paints the front prongs (call it after the head)."""
    rod = icon.tubes([((1.4, 14.6), (8.2, 7.8))], 0.95)
    icon.paint(rod, rod_ramp, bias=0.05)
    for (x, y) in rod.keys():
        if (x + (15 - y)) in (6, 7, 12):
            put(icon, [(x, y)], band_ramp[4] if x + y < 15 else band_ramp[3])
    collar = icon.sphere(8.6, 7.4, 1.8)
    icon.paint(collar, band_ramp, bias=0.15, outline_over=False)

    def prong(points, over=False):
        part = icon.tubes(list(zip(points, points[1:])), 0.75)
        icon.paint(part, prong_ramp, bias=0.15, outline_over=over)
        tip = points[-1]
        put(icon, [(math.floor(tip[0]), math.floor(tip[1]))], tip_colour)

    prong([(8.6, 7.4), (11.0, 3.4), (12.6, 1.2)])              # the back prong, behind the head

    def front():
        prong([(8.6, 7.4), (7.2, 5.2), (7.0, 2.8), (7.8, 1.4)], over=True)    # in front: a dark edge separates
        prong([(8.6, 7.4), (11.2, 8.4), (13.4, 7.8), (14.6, 6.4)], over=True)  # them from the head behind
    return front


def wyrmbreath(frame=0):
    """A fire scepter: a gold rod with ember bands and a collar, three gold dragon-claw prongs cradling a blazing ember
    orb; flames rise from it and flicker (animated)."""
    icon = Icon(16)
    gd, em = RAMPS["gold"], RAMPS["ember"]
    front = scepter(icon, gd, em, gd, gd[5])
    cr = RAMPS["crimson"]
    pulse = [0.15, 0.3, 0.2, 0.35][frame % 4]
    orb = icon.sphere(10.6, 5.2, 2.9)
    icon.paint(orb, cr, bias=pulse, outline_ramp=[cr[0], cr[0]], outline_over=False)   # a blazing red orb in gold claws
    put(icon, [(10, 5), (11, 5), (10, 6)], em[4])
    put(icon, [(9, 4)], em[5])
    front()
    # flames licking up off the orb
    k = frame % 4
    for (x, h, ph) in ((9, 2, 0), (11, 3, 1), (12, 2, 2)):
        hh = h + [0, 1, 0, 1][(k + ph) % 4]
        for i in range(hh):
            put(icon, [(x + (1 if i == hh - 1 and (k + ph) % 2 else 0), 2 - i)], em[4] if i < hh - 1 else em[3])
    icon.glow(em[3], radius=1.3, strength=0.22)
    return icon


def guardians_gaze(frame=0):
    """The guardian's scepter: a prismarine rod with gold bands, the guardian's spikes become three orange-tipped claw
    prongs cradling a glossy eyeball whose orange iris looks about (animated)."""
    icon = Icon(16)
    ab, gd, em, wd = RAMPS["abyss"], RAMPS["gold"], RAMPS["ember"], RAMPS["wind"]
    front = scepter(icon, ab, gd, ab, em[4])
    eye = icon.sphere(10.6, 5.2, 3.0)
    icon.paint(eye, wd, bias=0.1, outline_ramp=[ab[0], ab[1]], outline_over=False)
    lx, ly = [(0, 0), (1, 0), (0, 1), (-1, 0)][frame % 4]
    iris = [(x + lx, y + ly) for x in (10, 11) for y in (4, 5, 6)] + [(9 + lx, 5 + ly), (12 + lx, 5 + ly)]
    put(icon, iris, em[4])
    put(icon, [(10 + lx, 4 + ly)], em[5])
    put(icon, [(11 + lx, 5 + ly)], RAMPS["ink"][0])
    put(icon, [(9, 3)], wd[5])
    front()
    return icon


LANTERN = [  # a lantern: handle arch, wide lid and brim, cage, base (a narrow cap read as a bottle neck)
    "......####......",
    ".....#....#.....",
    ".....######.....",
    "....########....",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    "....########....",
]


def grave_lantern(frame=0):
    """A black iron lantern - handle arch, wide lid, cage, base - with a ghostly flame inside and a little skull in it,
    flickering (animated)."""
    icon = Icon(16)
    ir, sp, bone = RAMPS["boundsteel"], RAMPS["spirit"], RAMPS["bone"]
    y0 = 2
    mask = {(x, y + y0) for y, row in enumerate(LANTERN) for x, c in enumerate(row) if c == "#"}
    for (x, y) in mask:
        put(icon, [(x, y)], ir[2] if x < 8 else ir[1])
    put(icon, [(6, 2), (7, 2), (5, 3)], ir[4])                     # the arch catches the light
    put(icon, [(x, 4) for x in range(5, 9)] + [(4, 5), (5, 5)], ir[5])
    flick = frame % 4
    for y in range(7, 13):   # the flame inside the cage
        for x in range(6, 10):
            h = (y - 6) / 7 + (0.15 if x in (7, 8) else 0)
            put(icon, [(x, y)], sp[5] if h > 0.75 else sp[4] if h > 0.45 else sp[3])
    put(icon, [(6, 7 + (flick % 2)), (9, 8 - (flick % 2))], sp[2])
    put(icon, [(7, 10), (8, 10), (7, 11), (8, 11)], bone[4])   # the skull in the flame
    put(icon, [(7, 10), (8, 10)], RAMPS["ink"][0])
    put(icon, [(x, 13) for x in range(4, 12)], ir[3])
    icon.outline(Part({p: (0, 0, 1) for p in mask}), [ir[0], ir[0]], over=False)
    mirror_silhouette(icon)
    return icon


def abyssal_anchor(frame=0):
    """A heavy anchor, upright (an anchor only reads upright): ring, a stock with ball ends, the shank, U-curved arms
    ending in arrowhead flukes; abyssal iron, sea-glow runes that pulse, and the spectral chain it is hurled on trailing
    from the ring. (Its look in the hand is a held-model job for Session G.)"""
    icon = Icon(16)
    ab, sg, ir = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["iron"]
    shank = icon.tubes([((8.0, 4.0), (8.0, 14.0))], 1.0)
    arc = [(8.0 + 4.9 * math.cos(math.radians(a)), 9.4 + 4.9 * math.sin(math.radians(a))) for a in range(20, 161, 14)]
    arms = icon.tubes(list(zip(arc, arc[1:])), 0.95)
    icon.paint(shank | arms, ab, bias=0.2)
    for sgn in (-1, 1):   # arrowhead flukes at the arm tips
        tx = 8.0 + sgn * 4.7
        fl = icon.polygon([(tx - 1.6, 11.4), (tx + 1.6, 11.4), (tx + sgn * 0.5, 8.4)], bevel=0.6)
        icon.paint(fl, ab, bias=0.3, outline_over=False)
    stock = icon.tubes([((4.8, 5.0), (11.2, 5.0))], 0.7)
    icon.paint(stock, ab, bias=0.05, outline_over=False)
    for x in (4.4, 11.6):
        icon.paint(icon.sphere(x, 5.0, 1.1), ab, bias=0.25, outline=False)
    ring = icon.ring(8.0, 2.2, 2.0, 1.0)
    icon.paint(ring, ir, bias=0.1, outline_over=False)
    mirror_silhouette(icon)
    for i, y in enumerate((7, 9, 11)):   # runes down the shank
        put(icon, [(8, y)], sg[5] if (i + frame) % 3 == 0 else sg[3])
    put(icon, [(10, 1), (11, 1), (12, 0), (13, 0), (14, 1)], sg[3], 200)   # the spectral chain trailing off
    put(icon, [(15, 1)], sg[4], 150)
    return icon


def choir_bell(frame=0):
    """A small gold hand bell glowing ember inside; when rung it sends out a burning shockwave (animated rings)."""
    icon = Icon(16)
    gd, em, wood = RAMPS["gold"], RAMPS["ember"], RAMPS["wood"]
    handle = icon.box(6.8, 0.6, 9.2, 4.6, bevel=0.8)
    icon.paint(handle, wood, bias=0.1)
    body = icon.sphere(8.0, 6.6, 3.2) | icon.polygon([(4.8, 6.6), (11.2, 6.6), (13.4, 12.6), (2.6, 12.6)], bevel=1.4)
    icon.paint(body, gd, bias=0.1, outline_over=False)
    lip = icon.box(2.0, 11.6, 14.0, 13.4, bevel=0.8)
    icon.paint(lip, gd, bias=0.25, outline_over=False)
    put(icon, [(x, 13) for x in range(4, 12)], em[3])   # the glow inside the mouth
    put(icon, [(7, 14), (8, 14)], em[4])                 # the clapper
    k = frame % 4
    if k:
        r = 4.5 + k * 1.6
        for deg in range(20, 161, 20):
            x = math.floor(8 + r * math.cos(math.radians(deg)))
            y = math.floor(9 + r * math.sin(math.radians(deg)) * 0.6)
            for pt in ((x, y), (15 - x, y)):
                if 0 <= pt[0] < 16 and 0 <= pt[1] < 16 and icon.img.getpixel(pt)[3] == 0:
                    put(icon, [pt], em[4], 250 - k * 55)
    return icon


E3 = [("Wyrmbreath", wyrmbreath, 4), ("Guardian's Gaze", guardians_gaze, 4), ("Grave Lantern", grave_lantern, 4),
      ("Abyssal Anchor", abyssal_anchor, 4), ("Choir Bell", choir_bell, 4)]


# ================================================================== E4: Abyssal armor (vanilla armor-icon silhouettes + fins)

HELM = [
    ".......##.......",
    "......###.......",
    "......###.......",
    ".....######.....",
    "....########....",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "....##....##....",
]
CHEST = [
    "................",
    "#...........#...",
    ".#####....#####.",
    ".#####....#####.",
    ".######..######.",
    ".##############.",
    ".##############.",
    ".##############.",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "....########....",
    ".....######.....",
]
LEGS = [
    "................",
    "................",
    "....########....",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "..#####..#####..",
    "...####..####...",
    "..#####..#####..",
    "...####..####...",
    "...####..####...",
    "...####..####...",
    "...####..####...",
]
BOOTS = [
    "................",
    "................",
    "................",
    "...##......##...",
    "..###......###..",
    "...###....###...",
    "...####..####...",
    "...####..####...",
    "..#####..#####..",
    "..#####..#####..",
    ".######..######.",
    ".######..######.",
    ".####......####.",
]


def armor_base(icon, rows, cx, cy, rx, ry):
    """Paint an armor piece's plates over its mask: a soft dome of abyssal metal, outlined in its own darks."""
    ab = RAMPS["abyss"]
    part = mask_part(icon, rows, dome_normals(cx, cy, rx, ry))
    part = Part({p: n for p, n in part.normals.items() if rows[p[1]][p[0]] == "#"})
    icon.paint(part, ab, bias=0.18, outline=False)
    icon.outline(part, [ab[0], ab[1]], over=False)
    mirror_silhouette(icon)
    return part


def trim(frame):
    sg = RAMPS["seaglow"]
    return sg[[3, 4, 4, 3][frame % 4]], sg[2]


ABYSSAL_HELM_ICON = [   # redrawn to match the worn helm (G6): open-faced, fins tilted up and out, a crest, a brow gem
    "................",
    ".......F........",
    "......FFF.......",
    "f....LFFFL....f.",
    "FF..LHHHHHML..FF",
    ".FFLHHMMMMMMDFF.",
    "..FLGGGgGGGGDF..",
    "...LMKKKKKKMD...",
    "...LMKKKKKKMD...",
    "...LMKKKKKKMD...",
    "...LMMK..KMMD...",
    "...DDD....DDD...",
    "................",
    "................",
    "................",
    "................",
]


def abyssal_helmet(frame=0):
    """The Abyssal Helm: an open-faced helm of abyssal plate - a brow band with a sea-glow gem (pulsing), cheek guards,
    fan fins tilted up and out from its sides and a crest along its top."""
    from session_d import pixmap
    icon = Icon(16)
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    cols = {"H": ab[5], "L": ab[4], "M": ab[3], "D": ab[2], "K": ab[0], "F": ab[4], "f": sg[3], "G": ab[5],
            "g": sg[[3, 4, 5, 4][frame % 4]]}
    pixmap(icon, ABYSSAL_HELM_ICON, 0, 0, cols)
    mask = {(x, y) for y, row in enumerate(ABYSSAL_HELM_ICON) for x, c in enumerate(row) if c != "."}
    icon.outline(Part({p: (0, 0, 1) for p in mask}), [ab[1], ab[0]], over=False)
    return icon


def abyssal_chestplate(frame=0):
    """The Abyssal Chestplate: shoulder plates with fins, a sea-glow seam down the middle, gill-like glowing lines on the
    chest (Thorns), a belt (the glow pulses)."""
    icon = Icon(16)
    ab = RAMPS["abyss"]
    armor_base(icon, CHEST, 7.0, 6.0, 7.0, 7.0)
    hi, lo = trim(frame)
    put(icon, [(0, 1), (1, 2), (15, 1), (14, 2)], ab[4])   # shoulder fins
    put(icon, [(7, y) for y in range(5, 14)], ab[1])
    put(icon, [(8, y) for y in range(5, 14)], lo)
    put(icon, [(8, 5), (8, 6)], hi)
    for y in (8, 10):   # gills
        put(icon, [(4, y), (5, y), (10, y), (11, y)], lo)
    put(icon, [(x, 12) for x in range(3, 13)], ab[2])
    put(icon, [(2, 3), (3, 3), (12, 3), (13, 3)], ab[5])
    return icon


def abyssal_leggings(frame=0):
    """The Abyssal Greaves: a belt with a glowing buckle, fins down the outer sides of the legs, knee plates."""
    icon = Icon(16)
    ab = RAMPS["abyss"]
    armor_base(icon, LEGS, 7.0, 5.0, 7.0, 8.0)
    hi, lo = trim(frame)
    put(icon, [(x, 3) for x in range(3, 13)], ab[4])
    put(icon, [(7, 3), (8, 3)], hi)
    put(icon, [(2, 7), (2, 9), (13, 7), (13, 9)], ab[5])   # fins on the outer sides
    put(icon, [(4, 9), (5, 9), (10, 9), (11, 9)], lo)       # knee plates' glow
    put(icon, [(x, 13) for x in (3, 4, 5, 6, 9, 10, 11, 12)], ab[1])
    return icon


def abyssal_boots(frame=0):
    """The Abyssal Boots: cuffs with sea-glow trim, fins at the heels, dark soles."""
    icon = Icon(16)
    ab = RAMPS["abyss"]
    armor_base(icon, BOOTS, 7.0, 7.0, 7.0, 6.0)
    hi, lo = trim(frame)
    put(icon, [(2, 4), (13, 4)], ab[5])                      # heel fins
    put(icon, [(3, 5), (4, 5), (5, 5), (10, 5), (11, 5), (12, 5)], hi)
    put(icon, [(x, 12) for x in (1, 2, 3, 4, 11, 12, 13, 14)], ab[0])
    put(icon, [(4, 9), (11, 9)], lo)
    return icon


E4 = [("Abyssal Helm", abyssal_helmet, 4), ("Abyssal Chestplate", abyssal_chestplate, 4),
      ("Abyssal Greaves", abyssal_leggings, 4), ("Abyssal Boots", abyssal_boots, 4)]


# ================================================================== E5: decorations that are objects

def bottled_gale(frame=0):
    """A tall corked bottle of dark sea-green glass with a white tornado funnel spinning inside it: wide at the top,
    a point at the bottom, bands of wind turning round it (animated)."""
    icon = Icon(16)
    gl, wd, wood = RAMPS["glass"], RAMPS["wind"], RAMPS["wood"]
    body = icon.capsule((8.0, 9.4), (8.0, 12.0), 3.7)
    icon.paint(body, wd, bias=-0.45, outline_ramp=[gl[0], gl[1]])
    neck = icon.box(6.4, 2.8, 9.6, 6.4, bevel=0.8)
    icon.paint(neck, wd, bias=-0.45, outline_ramp=[gl[0], gl[1]], outline_over=False)
    cork = icon.box(6.0, 0.8, 10.0, 3.2, bevel=0.8)
    icon.paint(cork, wood, bias=0.15, outline_over=False)
    k = frame % 4
    for i, y in enumerate(range(7, 15)):   # the funnel, row by row: narrowing, each row pushed sideways (it twists)
        half = 3.2 - i * 0.4
        shift = [0, 1, 1, 0, -1, -1, 0, 1][(i + k) % 8] * (0.4 + i * 0.12)
        xs = range(math.floor(8 - half + shift), math.ceil(8 + half + shift))
        band = (i + k) % 2 == 0
        for x in xs:
            put(icon, [(x, y)], wd[5] if band and x < 8 + shift else wd[4] if band else wd[2])
    put(icon, [(5, 9), (5, 10)], gl[5])
    return icon


def wisp_jar(frame=0):
    """A round jar of dark tinted glass, a short neck and an iron lid; three wisps drift inside it, blinking in turn
    (animated)."""
    icon = Icon(16)
    ink, gl, ir, po = RAMPS["ink"], RAMPS["glass"], RAMPS["iron"], RAMPS["pollen"]
    body = icon.sphere(8.0, 10.0, 5.8, squash=0.95)
    icon.paint(body, ink, bias=0.1, outline_ramp=[gl[0], gl[1]])
    neck = icon.box(5.4, 3.4, 10.6, 5.4, bevel=0.6)
    icon.paint(neck, ink, bias=0.0, outline_ramp=[gl[0], gl[1]], outline_over=False)
    lid = icon.box(4.8, 1.2, 11.2, 3.6, bevel=0.9)
    icon.paint(lid, ir, bias=0.1, outline_over=False)
    put(icon, [(4, 8), (4, 9), (5, 7)], gl[3])
    wisps = [(6, 10), (10, 8), (9, 13)]
    for i, (x, y) in enumerate(wisps):
        on = (i + frame) % 3
        dy = (frame + i) % 2
        if on == 0:
            put(icon, [(x, y - dy)], po[4])
            put(icon, [(x - 1, y - dy), (x + 1, y - dy), (x, y - 1 - dy), (x, y + 1 - dy)], po[3], 160)
        elif on == 1:
            put(icon, [(x, y - dy)], po[3])
        else:
            put(icon, [(x, y - dy)], po[2], 160)
    return icon


def wind_chime(frame=0):
    """A wind chime: a wooden ring, four metal tubes of different lengths on threads, a sail below; the tubes sway
    (animated)."""
    icon = Icon(16)
    wood, ir, gd, chalk = RAMPS["wood"], RAMPS["iron"], RAMPS["gold"], RAMPS["chalk"]
    put(icon, [(8, 0)], chalk[3])
    ring = icon.sphere(8.0, 2.6, 6.0, squash=0.28)
    icon.paint(ring, wood, bias=0.1)
    sway = [0, 1, 0, -1][frame % 4]
    for i, (x, length) in enumerate(((3, 8), (6, 10), (10, 9), (13, 7))):
        off = sway if i % 2 == 0 else -sway
        put(icon, [(x, 4)], chalk[2])
        tube = [(x + (off if y > 7 else 0), y) for y in range(5, 5 + length)]
        put(icon, tube, ir[4] if i % 2 == 0 else gd[4])
        put(icon, [(tube[0][0] + 1, yy) for (_, yy) in tube[1:-1]], ir[2] if i % 2 == 0 else gd[2])
    put(icon, [(8, y) for y in range(4, 11)], chalk[2])
    sail = icon.box(6.6 + sway * 0.5, 11.0, 9.4 + sway * 0.5, 15.0, bevel=0.6)
    icon.paint(sail, wood, bias=0.15, outline_over=False)
    return icon


def occult_orrery(frame=0):
    """A brass orrery: a big glowing sun on a slim rod above a small stand, two tilted orbits drawn as dotted paths,
    little worlds of sea, fire and void moving round them (animated)."""
    icon = Icon(16)
    gd, em, sg, vi = RAMPS["gold"], RAMPS["ember"], RAMPS["seaglow"], RAMPS["violet"]
    base = icon.box(5.4, 13.6, 10.6, 15.6, bevel=0.9)
    icon.paint(base, gd, bias=0.0)
    put(icon, [(8, y) for y in range(10, 14)], gd[3])
    orbits = ((6.6, 4.0, -18), (4.0, 2.4, 22))
    for (rx, ry, tilt) in orbits:   # dotted, tilted orbit paths
        for a in range(0, 360, 20):
            u, v = rx * math.cos(math.radians(a)), ry * math.sin(math.radians(a))
            t = math.radians(tilt)
            put(icon, [(math.floor(8 + u * math.cos(t) - v * math.sin(t)), math.floor(6.4 + u * math.sin(t) + v * math.cos(t)))], gd[3], 200)
    sun = icon.sphere(8.0, 6.4, 2.6)
    icon.paint(sun, em, bias=0.35, outline=False)
    for (orb, ramp, start) in ((0, sg, 0), (0, em, 180), (1, vi, 90)):
        rx, ry, tilt = orbits[orb]
        a = math.radians(start + frame * 90)
        u, v = rx * math.cos(a), ry * math.sin(a)
        t = math.radians(tilt)
        x, y = 8 + u * math.cos(t) - v * math.sin(t), 6.4 + u * math.sin(t) + v * math.cos(t)
        icon.paint(icon.sphere(x, y, 1.2), ramp if ramp is not em else RAMPS["crimson"], bias=0.2, outline=False)
    return icon


def soulfire_brazier(frame=0):
    """An iron bowl on three legs full of crackling soul-fire flames and drifting embers; never burns anything
    (animated)."""
    icon = Icon(16)
    ir, sp = RAMPS["boundsteel"], RAMPS["spirit"]
    for (a, b) in (((4.0, 11.0), (2.6, 15.4)), ((12.0, 11.0), (13.4, 15.4)), ((8.0, 12.0), (8.0, 15.4))):
        put(icon, line_px(a, b), ir[3])
    bowl = cut(icon.sphere(8.0, 8.0, 6.2, squash=0.7), lambda x, y: y >= 8)
    icon.paint(bowl, ir, bias=0.2)
    put(icon, [(x, 8) for x in range(2, 14)], ir[4])
    flick = frame % 4
    for (x, h, ph) in ((5, 4, 0), (8, 6, 1), (11, 4, 2), (7, 3, 3), (10, 3, 1)):
        hh = h + [0, 1, 0, -1][(flick + ph) % 4]
        for i in range(hh):
            y = 7 - i
            put(icon, [(x, y)], sp[5] if i < hh * 0.35 else sp[4] if i < hh * 0.7 else sp[3])
    put(icon, [[(4, 1)], [(12, 0)], [(6, 0)], [(11, 2)]][flick], sp[4])
    return icon


def everliving_coral(frame=0):
    """Branching tube coral that never dries out: blue tubes with open tips, a thin stream of bubbles rising from it
    (animated)."""
    icon = Icon(16)
    fr = RAMPS["frost"]
    branches = [((8.0, 15.4), (8.0, 4.6), 1.3), ((7.6, 11.0), (3.6, 6.6), 1.1), ((8.4, 10.0), (12.6, 5.6), 1.1),
                ((5.2, 8.6), (3.0, 3.2), 0.9), ((11.4, 7.0), (13.2, 2.6), 0.9)]
    whole = Part({})
    for a, b, r in branches:
        part = icon.capsule(a, b, r)
        icon.paint(part, fr, bias=0.05, outline=False)
        whole = whole | part
        put(icon, [(math.floor(b[0]), math.floor(b[1]))], fr[1])   # the open tip
    icon.outline(whole, [fr[0], fr[0]], over=False)
    k = frame % 4
    for (x, base) in ((9, 3), (13, 1)):
        y = base - k
        if 0 <= y:
            put(icon, [(x, y)], RAMPS["wind"][5])
            put(icon, [(x + 1, y)], RAMPS["wind"][3], 160)
    return icon


def rune_obelisk(frame=0):
    """A small obelisk of blackstone on a plinth, a rune glowing on its face; three runes orbit it (animated)."""
    icon = Icon(16)
    ink, ash, sg = RAMPS["ink"], RAMPS["ash"], RAMPS["seaglow"]
    plinth = icon.box(3.6, 13.0, 12.4, 15.6, bevel=1.0)
    icon.paint(plinth, ash, bias=0.1)
    shaft = icon.polygon([(5.6, 13.2), (10.4, 13.2), (9.6, 3.6), (6.4, 3.6)], bevel=1.2)
    icon.paint(shaft, ash, bias=0.05, outline_over=False)
    tip = icon.polygon([(6.4, 3.8), (9.6, 3.8), (8.0, 0.6)], bevel=0.8)
    icon.paint(tip, ash, bias=0.2, outline_over=False)
    put(icon, [(8, 6), (7, 7), (9, 7), (6, 8), (10, 8), (7, 9), (9, 9), (8, 10)], sg[4])   # an eye rune (a cross read as a grave)
    put(icon, [(8, 8)], sg[5])
    for i in range(3):   # orbiting runes: in front when low on the ellipse, behind (hidden) when high
        a = math.radians(i * 120 + frame * 30)
        x, y = 8 + 6.6 * math.cos(a), 8 + 2.0 * math.sin(a)
        p = (math.floor(x), math.floor(y))
        if math.sin(a) > -0.2 or icon.img.getpixel(p)[3] == 0:
            put(icon, [p, (p[0], p[1] - 1)], sg[5] if math.sin(a) > 0 else sg[3])
    return icon


E5 = [("Bottled Gale", bottled_gale, 4), ("Wisp Jar", wisp_jar, 4), ("Wind Chime", wind_chime, 4),
      ("Occult Orrery", occult_orrery, 4), ("Soulfire Brazier", soulfire_brazier, 4), ("Everliving Coral", everliving_coral, 4),
      ("Rune Obelisk", rune_obelisk, 4)]
GROUPS = {"e1": E1, "e2": E2, "e3": E3, "e4": E4, "e5": E5}


def tier2_set():
    icons = []
    for group in (E1, E2, E3, E4, E5):
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
    icons = tier2_set()
    print(review.inventory(icons, os.path.join(OUT, "review-tier2-inventory.png"), cols=9))
    print(review.inventory(icons, os.path.join(OUT, "review-tier2-inventory-1x.png"), cols=9, scale=2))
    anim = [(name, make, n) for group in (E1, E2, E3, E4, E5) for name, make, n in group if n > 1]
    review.gif([[make(f % n).img for f in range(4)] for _, make, n in anim], os.path.join(OUT, "preview-tier2-animated.gif"),
               ms=170, scale=4)
    sys.exit()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "e1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    render(which, version)
