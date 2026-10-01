"""Session F: tier-3 item icons (16 px). Tier 3 is *Hollow*: sculk black-teal and old bone, hollow cyan as the magic,
crimson as the accent; boss drops keep their boss's colours (Heartwood amber, storm cyan, corrupted crimson, Gallus
gold). Held items are drawn as views of their future 3D models (Session E's lesson). Blocks go to Session G.

Run: python tools/art/session_f.py f1 [version]   (f1 materials, f2 drops, f3 weapons, f4 armor, f5 charms, set)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part, _norm  # noqa: E402
from session_c import cut, put, flat_face, line_px  # noqa: E402
from session_d import bar, pixmap, mirror_silhouette  # noqa: E402
from session_e import mask_part, dome_normals  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-f")
os.makedirs(OUT, exist_ok=True)


# ================================================================== F1: materials and the final catalyst

def hollow_essence(frame=0):
    """Spirit Essence's family shape (a round flask, a spirit escaping round the cork) gone Hollow: smoky sculk glass,
    hollow-cyan essence swirling inside, and the spirit that escapes is a dark shade with cyan eyes (animated)."""
    icon = Icon(16)
    sc, hc, wood = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["wood"]
    body = icon.sphere(7.4, 10.8, 4.8)
    liquid = Part({p: n for p, n in body.normals.items() if p[1] >= 8})
    icon.paint(body - liquid, sc, outline=False, bias=0.05)
    icon.paint(liquid, sc, outline=False, bias=-0.45)
    icon.outline(body, sc)
    neck = icon.box(5.9, 3.8, 8.9, 6.9, bevel=1.0)
    icon.paint(neck, sc, bias=0.15)
    cork = icon.box(5.4, 2.2, 9.4, 4.1, bevel=1.0)
    icon.paint(cork, wood, bias=-0.1)
    swirl = [(6, 10), (7, 9), (8, 9), (9, 10), (9, 11), (8, 12), (7, 12), (6, 11)]
    for i, p in enumerate(swirl):
        put(icon, [p], hc[5] if (i - frame * 2) % 8 in (0, 1) else hc[3])
    put(icon, [(4, 8), (4, 9), (5, 7)], sc[5])
    put(icon, [(9, 3), (10, 3), (10, 2), (11, 2)], sc[3])
    bob = [0, -1, 0, 1][frame % 4] * 0 + (1 if frame % 4 == 2 else 0)
    shade = icon.sphere(13.3, 2.6 + bob, 2.4)
    icon.paint(shade, sc, bias=-0.35, outline_ramp=[sc[0], sc[0]])
    put(icon, [(12, 2 + bob), (14, 2 + bob)], hc[4])
    return icon


def hollow_ingot(frame=0):
    """The ingot family's fourth and last metal: sculk-black, split by hollow-cyan veins that pulse through it."""
    icon = Icon(16)
    sc, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    top, left, right, d = bar(icon, sc, tones=(3, 2, 1))
    put(icon, [(2, 9), (3, 8), (4, 7), (5, 7), (6, 6), (7, 5), (8, 5), (9, 4)], sc[4])
    veins = [(4, 8), (5, 8), (6, 9), (7, 8), (8, 7), (9, 6), (10, 6), (11, 5), (6, 10), (6, 11), (9, 11), (10, 10)]
    for i, p in enumerate(veins):
        if p in top.normals or p in left.normals or p in right.normals:
            put(icon, [p], hc[5] if (i + frame * 3) % 6 < 2 else hc[3])
    return icon


def hollow_crystal(frame=0):
    """A jagged shard broken from the Hollow, dark and translucent, hollow-cyan light trapped in it; echoes ring out
    from it (animated)."""
    icon = Icon(16)
    sc, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    pts = [(9.6, 0.6), (11.4, 3.4), (13.6, 3.6), (12.2, 7.0), (13.4, 10.6), (10.4, 11.6), (7.6, 15.4), (5.6, 12.6),
           (2.6, 12.0), (4.2, 8.4), (2.6, 5.6), (6.0, 4.6)]
    shard = icon.polygon(pts, bevel=1.4)
    icon.paint(shard, sc, bias=-0.1)
    for (x, y) in shard.keys():   # a lit fracture plane on the upper left
        if x + y * 0.4 < 9.0:
            put(icon, [(x, y)], sc[3])
    put(icon, line_px((9.6, 1.6), (7.4, 14.0)), sc[4])
    glow = icon.sphere(7.8, 8.6, 2.6, squash=1.4)
    for (x, y) in glow.keys():
        d = math.hypot(x + 0.5 - 7.8, (y + 0.5 - 8.6) / 1.4)
        put(icon, [(x, y)], hc[5] if d < 0.9 else hc[4] if d < 1.8 and frame % 2 else hc[3] if d < 1.8 else hc[2])
    k = frame % 4
    if k:
        r = 5.0 + k * 1.2
        for deg in (150, 170, 190, 210, -30, -10, 10, 30):
            x = math.floor(8 + r * math.cos(math.radians(deg)))
            y = math.floor(9 + r * math.sin(math.radians(deg)))
            if 0 <= x < 16 and 0 <= y < 16 and icon.img.getpixel((x, y))[3] == 0:
                put(icon, [(x, y)], hc[4], 250 - k * 55)
    return icon


def hollow_effigy(frame=0):
    """The catalyst that summons Gallus: a carved pumpkin gone dark with sculk, its carved face lit hollow cyan from
    inside, a crimson rooster's comb on top - the Hollow Jockey's mark. The light flickers (animated)."""
    icon = Icon(16)
    sc, hc, cr, gel = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["crimson"], RAMPS["gel"]
    for (cx, r) in ((4.6, 4.4), (11.4, 4.4), (8.0, 5.2)):   # the pumpkin's lobes
        lobe = icon.sphere(cx, 9.8, r, squash=1.0)
        icon.paint(lobe, sc, bias=-0.15, outline_ramp=[sc[0], sc[0]], outline_over=False)
    put(icon, [(6, y) for y in range(6, 15)] + [(10, y) for y in range(6, 15)], sc[1])   # grooves between lobes
    comb = icon.polygon([(5.6, 5.0), (6.4, 1.4), (7.6, 3.6), (8.6, 0.8), (9.6, 3.4), (10.8, 1.8), (10.6, 5.0)], bevel=0.8)
    icon.paint(comb, cr, bias=0.2, outline_over=False)
    glow = hc[5] if frame % 4 in (1, 2) else hc[4]
    put(icon, [(4, 8), (5, 8), (5, 9), (11, 8), (10, 8), (10, 9)], glow)          # eyes
    put(icon, [(7, 11), (8, 11)], glow)                                           # nose
    put(icon, [(4, 12), (5, 13), (6, 13), (7, 12), (8, 13), (9, 13), (10, 12), (11, 12)], hc[3])   # a jagged grin
    return icon


F1 = [("Hollow Essence", hollow_essence, 4), ("Hollow Ingot", hollow_ingot, 4), ("Hollow Crystal", hollow_crystal, 4),
      ("Hollow Effigy", hollow_effigy, 4)]


# ================================================================== F2: boss drops

def warlords_brand(frame=0):
    """The Hollow Warlord's branding iron: a bone-gripped iron rod ending in a round brand - an iron disc whose rim
    glows red-hot and whose face carries the Hollow star, white-hot at the centre; heat shimmer and smoke (animated)."""
    icon = Icon(16)
    ir, cr, em, bone = RAMPS["boundsteel"], RAMPS["crimson"], RAMPS["ember"], RAMPS["bone"]
    rod = icon.tubes([((1.4, 14.6), (7.6, 8.4))], 0.8)
    icon.paint(rod, ir, bias=0.1)
    grip = icon.tubes([((1.4, 14.6), (4.0, 12.0))], 1.15)
    icon.paint(grip, bone, bias=0.0, outline_over=False)
    disc = icon.sphere(10.4, 5.6, 4.8)
    icon.paint(disc, ir, bias=-0.1, outline_ramp=[cr[0], cr[1]], outline_over=False)
    heat = frame % 4
    rim = [p for p in disc.keys() if math.hypot(p[0] + 0.5 - 10.4, p[1] + 0.5 - 5.6) > 3.6]
    put(icon, rim, cr[3] if heat in (0, 3) else cr[4])
    star = [(10.4 + (3.2 if i % 2 == 0 else 1.3) * math.cos(math.radians(-90 + i * 36)),
             5.6 + (3.2 if i % 2 == 0 else 1.3) * math.sin(math.radians(-90 + i * 36))) for i in range(10)]
    st = icon.facet(star, (0, 0, 1))
    for (x, y) in st.keys():
        d = math.hypot(x + 0.5 - 10.4, y + 0.5 - 5.6)
        put(icon, [(x, y)], em[5] if d < 1.2 + (heat % 2) * 0.6 else em[4])
    smoke = [[(14, 0)], [(15, 0), (13, 0)], [(15, 1)], []][heat]
    put(icon, smoke, RAMPS["ash"][4], 170)
    return icon


def heartwood_resin(frame=0):
    """A drop of Heartwood amber, glossy and clear, with an eye trapped inside it - the Heartwood Horror's - that opens
    and closes (animated)."""
    icon = Icon(16)
    am, wood, gel = RAMPS["amber"], RAMPS["wood"], RAMPS["gel"]
    drop = icon.sphere(8.0, 9.6, 5.6) | icon.polygon([(3.4, 8.0), (12.6, 8.0), (8.6, 0.8)], bevel=1.6)
    icon.paint(drop, am, bias=0.15, outline_ramp=[am[0], am[1]])
    inner = icon.sphere(8.4, 10.2, 3.4)
    for p in inner.keys():   # deeper, darker amber inside (it's thick)
        put(icon, [p], am[2])
    open_ = [1, 2, 2, 0][frame % 4]
    if open_:
        put(icon, [(6, 10), (7, 9), (8, 9), (9, 9), (10, 10), (7, 11), (8, 11), (9, 11)], wood[1])
        put(icon, [(8, 10)] if open_ == 1 else [(7, 10), (8, 10), (9, 10)], gel[4])
    else:
        put(icon, [(6, 10), (7, 10), (8, 10), (9, 10), (10, 10)], wood[1])
    put(icon, [(5, 6), (5, 7), (6, 5)], am[5])   # gloss
    put(icon, [(11, 13), (10, 14)], am[4])       # light through the resin
    return icon


def lancers_pennant(frame=0):
    """The Vanguard's pennant: a swallow-tailed black and crimson flag bearing a bone Hollow star, on a short iron lance
    tip; it waves (animated)."""
    icon = Icon(16)
    ir, cr, ink, bone = RAMPS["iron"], RAMPS["crimson"], RAMPS["ink"], RAMPS["bone"]
    put(icon, [(1, y) for y in range(1, 16)], ir[3])
    put(icon, [(2, y) for y in range(1, 16)], ir[2])
    put(icon, [(1, 0), (2, 0)], ir[5])
    wave = [0, 1, 0, -1][frame % 4]
    for x in range(3, 15):
        t = (x - 3) / 11
        top = 2 + round(math.sin(t * 3.2 + frame * 1.5) * 0.9)
        bottom = 11 - round(t * 3.0) + round(math.sin(t * 3.2 + frame * 1.5) * 0.9)
        notch = x > 11 and abs((top + bottom) / 2 - 0) >= 0
        for y in range(top, bottom + 1):
            if x > 11 and abs(y - (top + bottom) / 2) < (x - 11) * 0.9:
                continue   # the swallow tail
            put(icon, [(x, y)], cr[3] if y < (top + bottom) / 2 else cr[2])
    put(icon, [(x, 3 + round(math.sin((x - 3) / 11 * 3.2 + frame * 1.5) * 0.9)) for x in range(3, 15)], ink[1])
    put(icon, [(6, 5), (5, 6), (6, 6), (7, 6), (6, 7), (5, 8), (7, 8)], bone[4])
    return icon


def outriders_fletching(frame=0):
    """The Outrider's fletching: three broad storm-grey feathers fanned out, their tips white as lightning, bound at the
    quill with a crimson band; lightning crackles between the tips (animated)."""
    icon = Icon(16)
    ash, wd, cr = RAMPS["ash"], RAMPS["wind"], RAMPS["crimson"]
    base = (8.0, 13.4)
    for tip in ((2.4, 3.0), (13.6, 3.0), (8.0, 0.6)):   # outer feathers first, the middle one on top
        dx, dy = tip[0] - base[0], tip[1] - base[1]
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        mid = (base[0] + dx * 0.55, base[1] + dy * 0.55)
        vane = icon.polygon([base, (mid[0] + nx * 1.7, mid[1] + ny * 1.7), tip, (mid[0] - nx * 1.7, mid[1] - ny * 1.7)], bevel=1.0)
        icon.paint(vane, ash, bias=0.35, outline_ramp=[ash[0], ash[0]], outline_over=True)
        tipzone = [p for p in vane.keys() if math.hypot(p[0] + 0.5 - tip[0], p[1] + 0.5 - tip[1]) < 2.4]
        put(icon, tipzone, wd[4])
        put(icon, line_px(base, tip)[1:-2], ash[4])
    band = icon.box(6.0, 11.0, 10.0, 13.0, bevel=0.8)
    icon.paint(band, cr, bias=0.1, outline_over=False)
    put(icon, [(8, 14), (8, 15)], ash[3])
    k = frame % 4
    bolts = [[(5, 1), (6, 2)], [(10, 2), (11, 1)], [(5, 1), (6, 0), (10, 0), (11, 1)], []][k]
    put(icon, bolts, wd[5])
    return icon


def corrupted_circuit(frame=0):
    """A circuit chip from the Corrupted Colossus: a dark board with pins down both sides, hollow-cyan traces, and a
    crimson corruption that glitches across it (animated)."""
    icon = Icon(16)
    sc, hc, cr, ir = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["crimson"], RAMPS["iron"]
    for y in (4, 7, 10, 13):   # pins
        put(icon, [(1, y), (2, y), (13, y), (14, y)], ir[4])
        put(icon, [(1, y + 1) if y < 15 else (1, y), (14, y + 1)], ir[2])
    chip = icon.box(3.0, 2.4, 13.0, 15.0, bevel=1.2)
    icon.paint(chip, sc, bias=0.0)
    traces = [(5, 4), (6, 4), (7, 4), (7, 5), (7, 6), (8, 6), (9, 6), (10, 6), (5, 9), (6, 9), (6, 10), (6, 11), (7, 11),
              (8, 11), (9, 11), (9, 12), (10, 9), (11, 9), (11, 8), (5, 13), (6, 13)]
    put(icon, traces, hc[3])
    core = icon.box(7.6, 7.6, 10.4, 10.4, bevel=0.6)
    icon.paint(core, hc, bias=0.1, outline=False)
    k = frame % 4
    glitch = [[(4, 5), (5, 5), (11, 12)], [(9, 3), (10, 3), (4, 12), (5, 12), (6, 12)], [(11, 5), (8, 13), (9, 13)],
              [(5, 7), (6, 7), (7, 7), (10, 13)]][k]
    put(icon, glitch, cr[4])
    put(icon, [(8, 8)], cr[5] if k == 1 else hc[5])
    return icon


def mirror_visage(frame=0):
    """The Doppelganger's face: a mask of mirror glass with empty eye holes, framed in dark silver; a reflection slides
    over it (animated)."""
    icon = Icon(16)
    ir, wd, sc = RAMPS["boundsteel"], RAMPS["wind"], RAMPS["sculk"]
    mask = icon.sphere(8.0, 7.8, 6.4, squash=1.15)
    mask = Part({p: n for p, n in mask.normals.items() if p[1] <= 14})
    icon.paint(mask, wd, bias=0.0, outline_ramp=[ir[0], ir[1]])
    for (x, y) in mask.keys():   # mirror: cool reflections in bands
        if (x - y) % 7 == 0:
            put(icon, [(x, y)], wd[2])
    put(icon, [(4, 7), (5, 7), (6, 7), (9, 7), (10, 7), (11, 7), (5, 8), (6, 8), (9, 8), (10, 8)], sc[0])   # eye holes
    put(icon, [(8, 9), (8, 10), (7, 11)], wd[3])          # nose
    put(icon, [(6, 12), (7, 12), (8, 12), (9, 12)], wd[2])  # mouth line
    k = frame % 4
    put(icon, [p for p in line_px((2 + k * 3, 13), (6 + k * 3, 2)) if p in mask.normals], wd[5])
    mirror_silhouette(icon)
    return icon


def hollow_heart(frame=0):
    """A heart of dark heartwood: two lobes with a clear dip between them, vessel stubs on top, hollow-cyan light
    pulsing through its cracks - it beats (animated)."""
    icon = Icon(16)
    sc, hc, cr = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["crimson"]
    beat = [0.0, 0.5, 0.0, 0.2][frame % 4]
    heart = icon.sphere(5.0, 7.0, 3.9 + beat * 0.4) | icon.sphere(11.0, 7.0, 3.9 + beat * 0.4) | \
        icon.polygon([(1.2, 7.8), (14.8, 7.8), (8.0, 15.2 + beat)], bevel=1.6)
    heart = Part({p: n for p, n in heart.normals.items() if not (p[0] in (7, 8) and p[1] < 5)})   # the dip
    icon.paint(heart, sc, bias=0.05, outline_ramp=[sc[0], sc[0]])
    for (x0, y0) in ((5, 3), (10, 3)):   # vessel stubs
        put(icon, [(x0, y0 - 1), (x0 + 1, y0 - 1), (x0, y0 - 2), (x0 + 1, y0 - 2)], sc[3])
        put(icon, [(x0, y0 - 2)], sc[4])
    cracks = [(8, 6), (7, 7), (8, 8), (9, 9), (8, 10), (8, 11), (5, 7), (4, 8), (11, 6), (12, 7)]
    put(icon, cracks, hc[5] if beat > 0.3 else hc[4] if beat else hc[3])
    put(icon, [(3, 5), (4, 4)], sc[5])
    return icon


def gallus_wishbone(frame=0):
    """Gallus's wishbone: a bone Y with knobbed ends, a gold glint running along it; a twinkle (animated)."""
    icon = Icon(16)
    bone, gd = RAMPS["bone"], RAMPS["gold"]
    arms = icon.tubes([((8.0, 13.0), (4.0, 7.0)), ((4.0, 7.0), (3.2, 2.6)), ((8.0, 13.0), (12.0, 7.0)),
                       ((12.0, 7.0), (12.8, 2.6))], 1.05)
    icon.paint(arms, bone, bias=0.1)
    for (x, y) in ((3.2, 2.2), (12.8, 2.2)):
        icon.paint(icon.sphere(x, y, 1.6), bone, bias=0.2, outline_over=False)
    icon.paint(icon.sphere(8.0, 13.6, 1.8), bone, bias=0.0, outline_over=False)
    glint = [(4, 7), (5, 9), (11, 9), (12, 7)][frame % 4]
    put(icon, [glint], gd[5])
    mirror_silhouette(icon)
    icon.twinkle(8, 3, [0, 1, 2, 1][frame % 4], gd)
    return icon


F2 = [("Warlord's Brand", warlords_brand, 4), ("Heartwood Resin", heartwood_resin, 4), ("Lancer's Pennant", lancers_pennant, 4),
      ("Outrider's Fletching", outriders_fletching, 4), ("Corrupted Circuit", corrupted_circuit, 4),
      ("Mirror Visage", mirror_visage, 4), ("Hollow Heart", hollow_heart, 4), ("Gallus Wishbone", gallus_wishbone, 4)]


# ================================================================== F3: weapons

def dreadlance(frame=0):
    """The Dreadlance, drawn as its 3D model would look: a dark shaft on the diagonal, a wide bone vamplate (the cone
    hand-guard, ringed) over the grip, a big leaf-shaped head of hollow steel whose edges run crimson - it drinks
    blood; a drop gathers and falls from it (animated)."""
    icon = Icon(16)
    sc, bone, cr, ir = RAMPS["sculk"], RAMPS["bone"], RAMPS["crimson"], RAMPS["boundsteel"]
    shaft = icon.tubes([((0.6, 15.4), (9.4, 6.6))], 0.75)
    icon.paint(shaft, sc, bias=0.15)
    d, pp = (0.7071, -0.7071), (0.7071, 0.7071)

    def at(u, v):   # u along the lance from the vamplate's narrow end, v across it
        return (3.6 + d[0] * u + pp[0] * v, 12.4 + d[1] * u + pp[1] * v)

    vamp = icon.polygon([at(0, -1.0), at(0, 1.0), at(3.8, 3.4), at(3.8, -3.4)], bevel=1.2)
    icon.paint(vamp, bone, bias=0.1, outline_over=True)
    put(icon, [p for p in line_px(at(2.4, -2.4), at(2.4, 2.4)) if p in vamp.normals], bone[2])   # a ring on the cone
    head = icon.polygon([at(6.0, 0), at(8.6, -2.3), at(14.6, 0), at(8.6, 2.3)], bevel=1.4)
    icon.paint(head, ir, bias=0.45, outline_ramp=[cr[0], cr[1]], outline_over=True)
    edge = [p for p in head.keys() if any((p[0] + dx, p[1] + dy) not in head.normals for dx, dy in ((1, 0), (0, 1), (1, 1)))]
    put(icon, edge, cr[3] if frame % 4 != 1 else cr[4])
    put(icon, line_px(at(6.8, 0), at(13.4, 0)), ir[5])
    drip = [[], [(14, 5)], [(14, 6)], [(14, 8)]][frame % 4]
    put(icon, drip, cr[4])
    return icon


def soulfire_censer(frame=0):
    """The Soulfire Censer (the Wyrmbreath's successor): a pierced silver orb with a gold band, hung by three short
    chains from a cap and one chain to a ring handle; hollow-cyan soul fire glows through two rows of piercings and
    wisps out of them; it swings (animated)."""
    icon = Icon(16)
    ir, hc, gd = RAMPS["iron"], RAMPS["hollowcy"], RAMPS["gold"]
    swing = [0, 1, 0, -1][frame % 4]
    ring = icon.ring(2.6, 2.6, 2.2, 1.1)
    icon.paint(ring, ir, bias=0.1)
    cx, cy = 9.6 + swing * 0.6, 10.4
    hook = (cx, cy - 6.4)
    chain = line_px((4.0, 4.0), hook)
    put(icon, [p for i, p in enumerate(chain) if i % 2 == 0], ir[4])
    put(icon, [p for i, p in enumerate(chain) if i % 2 == 1], ir[2])
    for dx in (-2.6, 0, 2.6):   # three short chains from the hook to the orb's rim
        put(icon, line_px(hook, (cx + dx, cy - 3.4)), ir[3])
    orb = icon.sphere(cx, cy, 4.2)
    icon.paint(orb, ir, bias=0.0)
    put(icon, [(x, math.floor(cy)) for x in range(math.floor(cx - 4), math.floor(cx + 4) + 1)
               if (x, math.floor(cy)) in orb.normals], gd[4])
    holes = [(-2, -2), (0, -2), (2, -2), (-3, 2), (-1, 2), (1, 2), (3, 2)]
    for i, (dx, dy) in enumerate(holes):
        put(icon, [(math.floor(cx + dx), math.floor(cy + dy))], hc[5] if (i + frame) % 3 == 0 else hc[4])
    wisps = [[(12, 7), (13, 6)], [(13, 6), (14, 5)], [(5, 8), (4, 7)], [(14, 5), (15, 4)]][frame % 4]
    put(icon, wisps, hc[4], 200)
    return icon


def lichs_phylactery(frame=0):
    """The Lich's Phylactery: a skull for a stopper, a narrow neck bound in gold, a round glass bulb with a crimson soul
    turning inside it and glowing through the glass, a pointed bone finial below (animated)."""
    icon = Icon(16)
    bone, gd, cr, sc, hc, gl = RAMPS["bone"], RAMPS["gold"], RAMPS["crimson"], RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["glass"]
    bulb = icon.sphere(8.0, 10.0, 4.6)
    icon.paint(bulb, sc, bias=0.2, outline_ramp=[sc[0], sc[0]])
    k = frame % 4
    soul = icon.sphere(8.0 + [0, 1, 0, -1][k] * 0.5, 10.2, 2.4)
    for (x, y) in soul.keys():
        d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 10.2)
        put(icon, [(x, y)], cr[5] if d < 0.9 else cr[4] if d < 1.7 else cr[2])
    put(icon, [(5, 8), (5, 9), (6, 7)], gl[4])                 # the glass catches the light
    neck = icon.box(6.4, 3.8, 9.6, 6.4, bevel=0.6)
    icon.paint(neck, sc, bias=0.3, outline_over=False)
    put(icon, [(x, 5) for x in range(6, 10)], gd[4])
    skull = icon.sphere(8.0, 2.4, 2.5)
    icon.paint(skull, bone, bias=0.2, outline_over=False)
    put(icon, [(7, 2), (9, 2)], sc[0])
    if k in (1, 2):
        put(icon, [(7, 2), (9, 2)], hc[4])
    finial = icon.polygon([(6.4, 14.0), (9.6, 14.0), (8.0, 15.9)], bevel=0.6)
    icon.paint(finial, bone, bias=0.0, outline_over=False)
    mirror_silhouette(icon)
    return icon


def stormstring_bow(state=0):
    """The Stormstring Bow in its four textures, laid out like the vanilla bow: sculk-dark limbs with bone tips, a
    string of hollow-cyan lightning; drawn, the arrow's head crackles, and at full draw lightning arcs off it."""
    icon = Icon(16)
    sc, bone, hc, wd = RAMPS["sculk"], RAMPS["bone"], RAMPS["hollowcy"], RAMPS["wind"]
    a, c, b = (14.4, 1.4), (0.8, 0.8), (1.4, 14.4)
    pts = [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
            (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in [i / 16 for i in range(17)]]
    limb = icon.tubes(list(zip(pts, pts[1:])), 1.15)
    icon.paint(limb, sc, bias=0.2)
    for (x, y) in limb.keys():
        if x + y >= 14 and (x >= 12 or y >= 12):
            put(icon, [(x, y)], bone[4] if (x < 14 and y < 2) or (x < 2 and y < 14) else bone[3])
    put(icon, [(15, 2), (2, 15)], bone[5])
    put(icon, [(3, 4), (4, 3), (3, 5), (5, 3)], RAMPS["crimson"][3])
    put(icon, [(4, 4)], hc[5])
    pull = [0.0, 2.6, 4.2, 5.6][state]
    apex = (7.6 + pull, 7.6 + pull)
    from session_c import line_px as lp
    string = lp((14, 2), apex) + lp(apex, (2, 14)) if pull else lp((14, 2), (2, 14))
    put(icon, [p for p in string if p not in limb.normals], hc[4] if state else hc[3])
    if state:
        length = 9.6 + pull * 0.4
        head = (apex[0] - 0.7071 * length, apex[1] - 0.7071 * length)
        shaft = lp(apex, head)
        put(icon, shaft[1:-2], sc[4])
        put(icon, shaft[-2:], hc[5])
        put(icon, shaft[1:3], wd[4])
        if state == 3:
            hx, hy = shaft[-1]
            put(icon, [(hx - 1, hy - 2), (hx, hy - 3), (hx - 2, hy), (hx - 3, hy + 1)], hc[4])
    return icon


F3 = [("Dreadlance", dreadlance, 4), ("Soulfire Censer", soulfire_censer, 4), ("Lich's Phylactery", lichs_phylactery, 4)]
BOW_STATES = ["standby", "pulling_0", "pulling_1", "pulling_2"]


# ================================================================== F4: Hollow armor (vanilla armor-icon silhouettes + bone)

from session_e import CHEST, LEGS, BOOTS  # noqa: E402

CROWN_HELM = [   # the crown's spikes are drawn separately (an outline would fill the gaps between them)
    "................",
    "................",
    "...##########...",
    "....########....",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "...##########...",
    "....##....##....",
]


def hollow_base(icon, rows, cx, cy, rx, ry):
    sc = RAMPS["sculk"]
    part = mask_part(icon, rows, dome_normals(cx, cy, rx, ry))
    part = Part({p: n for p, n in part.normals.items() if rows[p[1]][p[0]] == "#"})
    icon.paint(part, sc, bias=0.05, outline=False)
    icon.outline(part, [sc[0], sc[0]], over=False)
    mirror_silhouette(icon)
    return part


def glow(frame):
    hc = RAMPS["hollowcy"]
    return hc[[3, 4, 5, 4][frame % 4]]


def hollow_helmet(frame=0):
    """The Hollow Crown: a sculk helm crowned with bone spikes, a crimson gem at the brow, a visor of hollow light."""
    icon = Icon(16)
    bone, cr, sc = RAMPS["bone"], RAMPS["crimson"], RAMPS["sculk"]
    hollow_base(icon, CROWN_HELM, 7.0, 4.0, 6.0, 7.0)
    for x in (3, 6, 9, 12):   # the crown: four bone spikes on a band, a crimson gem in the band
        put(icon, [(x, 0), (x, 1)], bone[4] if x < 8 else bone[3])
    put(icon, [(x, 2) for x in range(3, 13)], bone[3])
    put(icon, [(3, 2), (4, 2), (5, 2), (6, 2)], bone[5])
    put(icon, [(7, 2), (8, 2)], cr[4])
    put(icon, [(x, 5) for x in range(4, 12)], sc[0])
    put(icon, [(x, 5) for x in range(5, 11)], glow(frame))   # the visor at eye level
    return icon


def hollow_chestplate(frame=0):
    """The Hollow Cuirass: sculk plates with a ribcage of bone across the chest, a crimson gem at the heart, hollow
    light at the collar."""
    icon = Icon(16)
    bone, cr = RAMPS["bone"], RAMPS["crimson"]
    hollow_base(icon, CHEST, 7.0, 6.0, 7.0, 7.0)
    put(icon, [(0, 1), (15, 1)], RAMPS["sculk"][1])   # (the chest mask's fin tips: keep them dark, no fins here)
    for y in (8, 10, 12):   # ribs
        put(icon, [(x, y) for x in range(4, 7)] + [(x, y) for x in range(9, 12)], bone[3])
        put(icon, [(4, y), (11, y)], bone[4])
    put(icon, [(7, y) for y in range(7, 14)] + [(8, y) for y in range(7, 14)], bone[2])   # the sternum
    put(icon, [(7, 9), (8, 9)], cr[4])
    put(icon, [(6, 5), (7, 6), (8, 6), (9, 5)], glow(frame))
    return icon


def hollow_leggings(frame=0):
    """The Hollow Greaves: sculk plates, bone knee guards, a crimson gem at the belt, hollow light down the sides."""
    icon = Icon(16)
    bone, cr = RAMPS["bone"], RAMPS["crimson"]
    hollow_base(icon, LEGS, 7.0, 5.0, 7.0, 8.0)
    put(icon, [(2, 7), (2, 9), (13, 7), (13, 9)], RAMPS["sculk"][2])
    put(icon, [(x, 3) for x in range(3, 13)], bone[2])
    put(icon, [(7, 3), (8, 3)], cr[4])
    for x0 in (3, 9):   # knee guards
        put(icon, [(x0, 8), (x0 + 1, 8), (x0 + 2, 8), (x0 + 1, 9)], bone[4] if x0 == 3 else bone[3])
    put(icon, [(3, 11), (3, 12), (12, 11), (12, 12)], glow(frame))
    return icon


def hollow_boots(frame=0):
    """The Hollow Sabatons: sculk plates with bone toe caps and cuffs of hollow light."""
    icon = Icon(16)
    bone = RAMPS["bone"]
    hollow_base(icon, BOOTS, 7.0, 7.0, 7.0, 6.0)
    put(icon, [(2, 4), (13, 4)], RAMPS["sculk"][2])
    put(icon, [(1, 10), (2, 10), (1, 11), (2, 11), (13, 10), (14, 10), (13, 11), (14, 11)], bone[4])
    put(icon, [(3, 5), (4, 5), (5, 5), (10, 5), (11, 5), (12, 5)], glow(frame))
    put(icon, [(x, 12) for x in (1, 2, 3, 4, 11, 12, 13, 14)], RAMPS["sculk"][0])
    return icon


F4 = [("Hollow Crown", hollow_helmet, 4), ("Hollow Cuirass", hollow_chestplate, 4),
      ("Hollow Greaves", hollow_leggings, 4), ("Hollow Sabatons", hollow_boots, 4)]


# ================================================================== F5: talismans, the egg, the shield, the flower

def hollow_halo(frame=0):
    """The Hollow Halo: Session B's glowing gold ring seen at an angle (the far side dimmer, the hole empty), twinkles
    travelling round it (animated)."""
    icon = Icon(16)
    gd = RAMPS["gold"]
    ring = icon.ellipse_ring(8.0, 8.0, 6.8, 3.2, 1.8)
    far = Part({p: n for p, n in ring.normals.items() if p[1] < 8})
    icon.paint(far, gd, outline=False, bias=-0.12)
    icon.paint(ring - far, gd, outline=False, bias=0.18)
    put(icon, [(3, 10), (4, 11)], gd[5])
    hole = {(x, y) for y in range(16) for x in range(16) if ((x + 0.5 - 8) / 5.6) ** 2 + ((y + 0.5 - 8) / 2.0) ** 2 < 1}
    icon.glow(gd[4], radius=2.0, strength=0.4)
    icon.clear([p for p in hole if icon.img.getpixel(p)[3] < 255])
    spots = [(12, 2), (14, 6), (4, 3), (1, 6)]
    icon.twinkle(*spots[frame % 4], 2, gd)
    icon.twinkle(*spots[(frame + 2) % 4], 1, gd)
    return icon


def wishbone_talisman(frame=0):
    """The Wishbone Talisman: Gallus's wishbone hung upright on a cord that runs through both knobs to a loop, its joint
    wrapped in gold wire round a crimson gem; a twinkle (animated)."""
    icon = Icon(16)
    bone, gd, cr, tw = RAMPS["bone"], RAMPS["gold"], RAMPS["crimson"], RAMPS["twine"]
    arms = icon.tubes([((8.0, 13.2), (4.8, 8.6)), ((4.8, 8.6), (4.0, 5.4)), ((8.0, 13.2), (11.2, 8.6)),
                       ((11.2, 8.6), (12.0, 5.4))], 0.95)
    icon.paint(arms, bone, bias=0.1)
    for x in (4.0, 12.0):
        icon.paint(icon.sphere(x, 5.0, 1.4), bone, bias=0.2, outline_over=False)
    wrap = icon.sphere(8.0, 12.8, 2.0)
    icon.paint(wrap, gd, bias=0.2, outline_over=False)
    put(icon, [(7, 12), (8, 12)], cr[4] if frame % 4 != 2 else cr[5])
    mirror_silhouette(icon)
    cord = line_px((4, 3), (7, 0))   # drawn after the symmetry pass, mirrored exactly
    put(icon, cord + [(15 - x, y) for (x, y) in cord], tw[3])
    icon.twinkle(13, 11, [0, 1, 2, 1][frame % 4], gd)
    return icon


def aura_talisman(frame=0):
    """The Aura Talisman: a long pointed crystal hung from a cord by a silver loop; its four facets cycle through the
    colours and sparkles trail off it (animated)."""
    icon = Icon(16)
    ir, tw = RAMPS["iron"], RAMPS["twine"]
    hues = [RAMPS["crimson"], RAMPS["ember"], RAMPS["gold"], RAMPS["gel"], RAMPS["seaglow"], RAMPS["violet"]]
    put(icon, line_px((5, 0), (7, 2)) + line_px((10, 0), (8, 2)), tw[3])
    loop = icon.ring(8.0, 2.8, 1.3, 0.5)
    icon.paint(loop, ir, bias=0.2, outline=False)
    top, l, r, bot = (8.0, 4.0), (4.6, 8.0), (11.4, 8.0), (8.0, 15.6)
    facets = [([top, l, (8.0, 8.0)], 4), ([top, (8.0, 8.0), r], 3), ([l, (8.0, 8.0), bot], 3), ([(8.0, 8.0), r, bot], 2)]
    whole = Part({})
    for i, (pts, tone) in enumerate(facets):
        part = icon.facet(pts, (0, 0, 1)) - whole
        icon.paint(part, hues[(i + frame) % 6], outline=False, flat=tone)
        whole = whole | part
    icon.outline(whole, [ir[0], ir[1]], over=False)
    put(icon, [(6, 6), (6, 7)], RAMPS["wind"][5])
    trail = [(13, 12), (14, 9), (2, 13), (1, 10)]
    icon.twinkle(*trail[frame % 4], 2, hues[frame % 6])
    put(icon, [trail[(frame + 1) % 4]], hues[(frame + 3) % 6][4])
    return icon


def gallus_egg(frame=0):
    """The Gallus Egg: a big cream egg speckled crimson and gold, a crack across it glowing hollow cyan; it rocks and
    the crack pulses - something is about to hatch (animated)."""
    icon = Icon(16)
    bone, cr, gd, hc = RAMPS["bone"], RAMPS["crimson"], RAMPS["gold"], RAMPS["hollowcy"]
    rock = [0, 1, 0, -1][frame % 4] * 0.5
    egg = icon.sphere(8.0 + rock, 9.0, 5.4, squash=1.28)
    egg = Part({p: n for p, n in egg.normals.items() if p[1] < 16})
    icon.paint(egg, bone, bias=0.15)
    for (x, y, c) in ((5, 6, cr[3]), (9, 4, gd[3]), (11, 8, cr[2]), (6, 11, gd[2]), (10, 12, cr[3]), (8, 7, gd[4])):
        put(icon, [(x + round(rock), y)], c)
    crack = [(4, 10), (5, 9), (6, 10), (7, 9), (8, 10), (9, 9), (10, 10), (11, 9), (12, 10)]
    put(icon, [(x + round(rock), y) for (x, y) in crack], hc[[3, 4, 5, 4][frame % 4]])
    put(icon, [(5 + round(rock), 4), (6 + round(rock), 3)], bone[5])
    return icon


def heartwood_aegis(frame=0):
    """The Heartwood Aegis: a heater shield of dark heartwood in a bone rim, amber resin running in its grain, a green
    rune of regrowth at its heart that pulses (animated). (Held as a shield, it needs a 3D model - Session G.)"""
    icon = Icon(16)
    wood, bone, am, gel = RAMPS["wood"], RAMPS["bone"], RAMPS["amber"], RAMPS["gel"]
    rim = icon.polygon([(1.5, 1.5), (14.5, 1.5), (14.5, 7.2), (8.0, 15.2), (1.5, 7.2)], bevel=1.4)
    icon.paint(rim, bone, bias=0.0)
    face = icon.polygon([(3.0, 3.0), (13.0, 3.0), (13.0, 6.8), (8.0, 13.2), (3.0, 6.8)], bevel=1.2)
    icon.paint(face, wood, bias=-0.15, outline=False)
    for (x, y) in face.keys():   # the grain, with resin in it
        if (x + y * 2) % 5 == 0:
            put(icon, [(x, y)], am[3] if y % 3 else am[4])
    rune = [(8, 4), (7, 5), (9, 5), (8, 6), (8, 7), (6, 7), (10, 7), (8, 8), (8, 9)]
    put(icon, rune, gel[[3, 4, 5, 4][frame % 4]])
    mirror_silhouette(icon)
    return icon


def watchful_eyeblossom(frame=0):
    """The Watchful Eyeblossom: six pale petals tipped with amber in a lobed ring round an eye, on a dark stem with two
    leaves; the eye opens when you come near (animated: closed, opening, open and looking, closing), a mote drifting."""
    icon = Icon(16)
    sc, bone, am = RAMPS["sculk"], RAMPS["bone"], RAMPS["amber"]
    put(icon, [(8, y) for y in range(10, 16)], sc[3])
    for pts in ([(8, 14), (6, 13), (4, 13), (3, 12)], [(8, 13), (10, 12), (12, 12), (13, 11)]):
        put(icon, pts, sc[4])
    petals = Part({})
    for k in range(6):
        a = math.radians(-90 + k * 60)
        petals = petals | icon.sphere(8.0 + 3.9 * math.cos(a), 6.0 + 3.9 * math.sin(a), 2.2)
    icon.paint(petals, bone, bias=0.1, outline_ramp=[bone[0], bone[1]])
    for k in range(6):   # amber tips
        a = math.radians(-90 + k * 60)
        put(icon, [(math.floor(8.0 + 5.0 * math.cos(a)), math.floor(6.0 + 5.0 * math.sin(a)))], am[3])
    centre = icon.sphere(8.0, 6.0, 2.6)
    icon.paint(centre, sc, bias=0.2, outline=False)
    state = [0, 1, 2, 1][frame % 4]
    if state == 0:
        put(icon, [(6, 6), (7, 6), (8, 6), (9, 6)], am[2])
    else:
        put(icon, [(7, 5), (8, 5), (7, 6), (8, 6), (7, 7), (8, 7)] if state == 2 else [(7, 6), (8, 6)], am[4])
        if state == 2:
            put(icon, [(8, 6)], sc[0])
            put(icon, [(7, 5)], am[5])
    put(icon, [[(14, 3)], [(15, 2)], [(14, 1)], [(13, 0)]][frame % 4], am[4], 200)
    return icon


F5 = [("Hollow Halo", hollow_halo, 4), ("Wishbone Talisman", wishbone_talisman, 4), ("Aura Talisman", aura_talisman, 4),
      ("Gallus Egg", gallus_egg, 4), ("Heartwood Aegis", heartwood_aegis, 4), ("Watchful Eyeblossom", watchful_eyeblossom, 4)]
GROUPS = {"f1": F1, "f2": F2, "f3": F3, "f4": F4, "f5": F5}


def tier3_set():
    """Every tier-3 icon (Session A's Hollow Sigil included), first frame."""
    from PIL import Image
    sigil = Image.open(os.path.join(OUT, "..", "session-a", "hollow_sigil.png")).convert("RGBA")
    icons = [("Hollow Sigil", sigil)]
    for group in (F1, F2, F3, F4, F5):
        icons += [(name, make(0).img) for name, make, _ in group]
    icons.append(("Stormstring Bow", stormstring_bow(0).img))
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
    if which == "f3":
        bows = [stormstring_bow(i) for i in range(4)]
        for st, icon in zip(BOW_STATES, bows):
            icon.save(os.path.join(OUT, f"stormstring_bow_{st}.png"))
            statics.append((f"Stormstring Bow ({st})", icon.img))
        animated.append(("Stormstring Bow (draw)", [i.img for i in bows]))
    print(review.sheet(statics, os.path.join(OUT, f"review-{which}{suffix}.png")))
    if animated:
        from session_b import frame_sheet
        print(frame_sheet(animated, os.path.join(OUT, f"review-{which}-anim{suffix}.png")))


if __name__ == "__main__" and sys.argv[1:2] == ["set"]:
    icons = tier3_set()
    print(review.inventory(icons, os.path.join(OUT, "review-tier3-inventory.png"), cols=9))
    print(review.inventory(icons, os.path.join(OUT, "review-tier3-inventory-1x.png"), cols=9, scale=2))
    anim = [(name, make, n) for group in (F1, F2, F3, F4, F5) for name, make, n in group if n > 1]
    review.gif([[make(f % n).img for f in range(4)] for _, make, n in anim], os.path.join(OUT, "preview-tier3-animated.gif"),
               ms=170, scale=4)
    review.gif([[stormstring_bow(i).img for i in range(4)]], os.path.join(OUT, "preview-stormstring-draw.gif"), ms=260)
    sys.exit()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "f1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    render(which, version)
