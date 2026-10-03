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
from PIL import Image  # noqa: E402

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
    """A Hollow crystal split in two: the halves float apart and hollow light pours out of the break between them;
    two fragments orbit at its sides. Dark translucent faces (lit, front, shadow) with hard ridges. Exactly symmetric.
    Animated: the halves breathe apart, the light pulses, the fragments bob."""
    icon = Icon(16)
    sc, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    k = frame % 4
    lift = [0, 0, 1, 0][k]
    # the light in the break, behind the halves
    for y in range(6 - lift, 10):
        for x in range(4, 12):
            d = abs(x + 0.5 - 8.0)
            put(icon, [(x, y)], hc[5] if d < 1.5 else hc[4] if d < 3.0 else hc[3])
    halves = [  # (polygon, ridge)
        ([(8.0, 0.4 - lift), (12.6, 5.4 - lift), (11.0, 6.6 - lift), (9.6, 6.0 - lift), (8.0, 7.0 - lift), (6.4, 6.0 - lift),
          (5.0, 6.6 - lift), (3.4, 5.4 - lift)], ((8.0, 1.0 - lift), (8.0, 6.4 - lift))),
        ([(3.6, 10.4), (5.0, 9.2), (6.6, 9.8), (8.0, 9.0), (9.4, 9.8), (11.0, 9.2), (12.4, 10.4), (8.0, 15.6)],
         ((8.0, 9.6), (8.0, 15.0))),
    ]
    for pts, ridge in halves:
        part = icon.facet(pts, (0, 0, 1))
        for (x, y) in part.keys():
            put(icon, [(x, y)], sc[3] if x < 6 else sc[2] if x < 8 else sc[1])
        icon.outline(part, [sc[0], sc[0]], over=False)
        put(icon, [p for p in line_px(*ridge) if p in part.normals], sc[4])
    put(icon, [(6, 2 - lift), (5, 3 - lift)], hc[4])   # light catching the upper edges
    put(icon, [(x, 6 - lift) for x in (5, 6, 9, 10)] + [(x, 9) for x in (5, 6, 9, 10)], hc[4])   # the glowing break edges
    bob = [0, -1, 0, 1][k]
    for x in (1, 14):   # orbiting fragments
        put(icon, [(x, 7 + bob), (x, 8 + bob)], sc[4] if x == 1 else sc[3])
        put(icon, [(x, 6 + bob)], hc[4])
    return icon


ROOSTER_SKULL = [  # side view, beak to the right, open: R comb/wattle, B bone, b shade, K hollow, C socket fire, G beak
    "....RR.RR......",
    "...RRRRRRR.....",
    "..BBBBKBBBB....",
    ".BBBBBBKBBBBG..",
    ".BKKKKBBBBBGGGG",
    ".BKKCKBBKBGG...",
    ".BKKKKBBBb..GGG",
    "..bBBBBBbbGGG..",
    "...bbbbbbRR....",
]


def hollow_effigy(frame=0):
    """The catalyst that summons Gallus, the Hollow Jockey: a ritual totem - a rooster's skull with its crimson comb and
    wattle, the eye socket burning hollow cyan, set on a sculk stake bound with twine and hung with black feathers.
    Animated: the socket flares and a wisp rises from it."""
    icon = Icon(16)
    bone, cr, gd, sc, hc, tw, ink = (RAMPS["bone"], RAMPS["crimson"], RAMPS["gold"], RAMPS["sculk"], RAMPS["hollowcy"],
                                     RAMPS["twine"], RAMPS["ink"])
    stake = icon.box(6.0, 9.0, 8.0, 16.0, bevel=0.6)
    icon.paint(stake, sc, bias=0.25)
    put(icon, line_px((6, 11), (3, 14)) + [(3, 15)], ink[2])         # black feathers hanging off the binding
    put(icon, line_px((7, 11), (10, 14)) + [(10, 15)], ink[3])
    put(icon, [(6, 11), (7, 11), (6, 12), (7, 12)], tw[4])
    glow = hc[5] if frame % 4 in (1, 2) else hc[4]
    cols = {"R": cr[3], "B": bone[3], "b": bone[1], "K": sc[0], "C": glow, "G": gd[3]}
    pixmap(icon, ROOSTER_SKULL, 0, 0, cols)
    put(icon, [(2, 2), (3, 2), (4, 2), (5, 2)], bone[4])    # aged bone: only the crown of the skull catches light
    put(icon, [(x, 3) for x in range(8, 12)], bone[2])
    put(icon, [(13, 5), (12, 6)], gd[2])
    put(icon, [(5, 0), (4, 1)], cr[5])
    mask = {(x, y) for y, row in enumerate(ROOSTER_SKULL) for x, c in enumerate(row) if c != "."}
    icon.outline(Part({p: (0, 0, 1) for p in mask}), [sc[0], sc[0]], over=False)
    wisp = [[], [(4, 3)], [(5, 2)], [(4, 1)]][frame % 4]
    put(icon, wisp, hc[4], 200)
    return icon


F1 = [("Hollow Essence", hollow_essence, 4), ("Hollow Ingot", hollow_ingot, 4), ("Hollow Crystal", hollow_crystal, 4),
      ("Hollow Effigy", hollow_effigy, 4)]


# ================================================================== F2: boss drops

def warlords_brand(frame=0):
    """The Hollow Warlord's brand, forged like a weapon: a thick hexagonal iron head seen at three quarters (its side
    shows its depth), spiked at the corners, the Hollow star raised on its face and glowing white-hot to crimson; a
    gold-collared rod, a leather grip, a bone pommel. Heat glows round it, embers fall (animated)."""
    icon = Icon(16)
    ir, cr, em, bone, gd, lea = (RAMPS["boundsteel"], RAMPS["crimson"], RAMPS["ember"], RAMPS["bone"], RAMPS["gold"],
                                 RAMPS["leather"])
    rod = icon.tubes([((2.0, 14.0), (8.0, 8.0))], 0.85)
    icon.paint(rod, ir, bias=0.15)
    grip = icon.tubes([((2.0, 14.0), (4.6, 11.4))], 1.1)
    icon.paint(grip, lea, bias=0.1, outline_over=False)
    icon.paint(icon.sphere(1.6, 14.4, 1.4), bone, bias=0.2, outline_over=False)
    icon.paint(icon.sphere(7.6, 8.4, 1.5), gd, bias=0.2, outline_over=False)
    cx, cy = 10.4, 5.4
    hexa = [(cx + 4.4 * math.cos(math.radians(a)), cy + 4.4 * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    back = icon.facet([(x + 1.2, y + 1.2) for x, y in hexa], (0, 0, 1))
    icon.paint(back, ir, outline=False, flat=1)
    front = icon.polygon(hexa, bevel=1.2)
    icon.paint(front, ir, bias=0.05, outline_over=False)
    icon.outline(front | back, [ir[0], ir[0]], over=False)
    for (x, y) in hexa:   # spikes at the corners
        sx, sy = cx + (x - cx) * 1.3, cy + (y - cy) * 1.3
        p = (math.floor(sx), math.floor(sy))
        if 0 <= p[0] < 16 and 0 <= p[1] < 16:
            put(icon, [p], ir[4])
    heat = frame % 4
    star = [(cx + (3.2 if i % 2 == 0 else 1.3) * math.cos(math.radians(-90 + i * 36)),
             cy + (3.2 if i % 2 == 0 else 1.3) * math.sin(math.radians(-90 + i * 36))) for i in range(10)]
    st = icon.facet(star, (0, 0, 1))
    for (x, y) in st.keys():
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        put(icon, [(x, y)], em[5] if d < 1.0 + (heat % 2) * 0.5 else em[4] if d < 2.0 else cr[4])
    icon.glow(cr[3], radius=1.3, strength=0.25)
    embers = [[(13, 12)], [(14, 13), (12, 11)], [(13, 14)], [(12, 12)]][heat]
    put(icon, embers, em[4])
    return icon


def heartwood_resin(frame=0):
    """A drop of Heartwood amber with real volume: lit from the top left, light glowing through its lower side, a
    sharp specular streak, bubbles caught inside, a drip hanging from it - and deep in it, blurred by the resin, the
    Heartwood Horror's eye, which opens and closes (animated)."""
    icon = Icon(16)
    am, wood, gel = RAMPS["amber"], RAMPS["wood"], RAMPS["gel"]
    drop = icon.sphere(7.6, 9.0, 5.4) | icon.polygon([(3.0, 7.6), (12.2, 7.6), (8.2, 0.6)], bevel=2.2)
    icon.paint(drop, am, bias=0.05, outline_ramp=[am[0], am[1]])
    for (x, y) in drop.keys():   # subsurface glow: light passing through the lower right
        if math.hypot(x + 0.5 - 9.6, y + 0.5 - 11.4) < 2.6:
            put(icon, [(x, y)], am[4])
    halo = icon.sphere(7.4, 9.4, 2.6)
    for p in halo.keys():         # the dark depth round the trapped eye
        put(icon, [p], am[1] if math.hypot(p[0] + 0.5 - 7.4, p[1] + 0.5 - 9.4) < 1.8 else am[2])
    open_ = [1, 2, 2, 0][frame % 4]
    if open_:
        put(icon, [(7, 9)] if open_ == 1 else [(6, 9), (7, 9), (8, 9)], gel[3])
        if open_ == 2:
            put(icon, [(7, 9)], wood[0])
    else:
        put(icon, [(6, 9), (7, 9), (8, 9)], wood[0])
    put(icon, [(4, 6), (4, 7), (5, 5), (5, 4)], am[5])   # the specular streak
    put(icon, [(10, 6), (11, 9)], am[5])                # bubbles
    put(icon, [(10, 7), (11, 10)], am[3])
    drip = [[(8, 15)], [(8, 15)], [(8, 15), (8, 14)], []][frame % 4]
    put(icon, [(8, 14)], am[3])
    put(icon, drip, am[3])
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
    """A Hollow heart, anatomical: chambers of dark heartwood, the aortic arch and the great vessels rising from it
    (their cut ends crimson), hollow-cyan veins running over it - it beats (animated)."""
    icon = Icon(16)
    sc, hc, cr = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["crimson"]
    beat = [0.0, 0.45, 0.0, 0.2][frame % 4]
    vessels = icon.tubes([((7.6, 6.4), (7.4, 2.6)), ((7.4, 2.6), (5.8, 1.6)), ((5.8, 1.6), (4.2, 2.4)),
                          ((4.2, 2.4), (3.6, 4.2))], 1.2) | icon.tubes([((9.6, 6.6), (11.4, 2.4))], 1.0) |         icon.tubes([((12.0, 7.0), (14.0, 4.8))], 0.9)
    icon.paint(vessels, sc, bias=0.5)
    for p in ((3, 4), (11, 1), (14, 4)):   # the cut vessel ends
        put(icon, [p], cr[3])
    body = icon.sphere(8.2, 10.0, 4.2 + beat * 0.5) | icon.sphere(11.0, 7.6, 2.3 + beat * 0.3) |         icon.sphere(5.4, 7.8, 2.1 + beat * 0.3) | icon.polygon([(4.2, 10.4), (12.2, 11.0), (7.0, 15.8)], bevel=1.0)
    icon.paint(body, sc, bias=0.0, outline_ramp=[sc[0], sc[0]], outline_over=True)
    put(icon, [(9, 8), (10, 7)], sc[1])     # the groove between the chambers
    veins = [(9, 9), (8, 10), (8, 11), (7, 12), (7, 13), (10, 10), (11, 11), (6, 9), (5, 10)]
    put(icon, veins, hc[4] if beat > 0.3 else hc[3])
    put(icon, [(4, 7), (5, 6), (6, 9)], sc[5])
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

DREAD_STEEL = [(16, 16, 20, 255), (30, 30, 37, 255), (46, 46, 56, 255), (66, 66, 78, 255), (92, 92, 106, 255),
               (126, 126, 140, 255)]   # blackened steel, black to grey


def spear_sprite(size, frame, head_at_left):
    """The Dreadlance drawn like vanilla's spears, upgraded - a pixel sprite along the diagonal. size 32: the in-hand
    sprite (vanilla's layout: head top-left, butt bottom-right); size 16: the icon (head top-right, butt bottom-left).
    Parts along the spear, from the tip: a leaf blade of blackened steel with honed soul-blue edges and a purple ridge
    that pulses (animated); a steel socket with swept lugs and a purple gem; a dark sculk shaft banded in soul blue; a
    grip wrapped in violet-black leather; a steel pommel with a soul gem. Coloured outline in the steel's own black."""
    st, sk, vi, hc = DREAD_STEEL, RAMPS["sculk"], RAMPS["violet"], RAMPS["hollowcy"]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    big = size == 32
    span = 2 * (size - 1)                                # s runs 0 (tip) .. span (butt)
    sc = span / 62.0                                     # the 32 px layout, scaled
    pulse = [vi[3], vi[4], vi[5], vi[4]][frame % 4]
    edge_lit = [hc[3], hc[4], hc[3], hc[2]][frame % 4]
    blade_end, socket_end, shaft_end, grip_end = 18 * sc, 23 * sc, 44 * sc, 56 * sc

    def half(sv):                                         # the leaf's half-width along the blade
        prof = [(0, 0), (2, 1), (5, 2), (8, 3), (11, 4), (14, 3), (16, 2), (18, 1)]
        sv = sv / sc
        for (a, ha), (b, hb) in zip(prof, prof[1:]):
            if a <= sv <= b:
                return (ha + (hb - ha) * (sv - a) / (b - a)) * (1 if big else 0.85)
        return 0
    for y in range(size):
        for x in range(size):
            if head_at_left:
                sv, k = x + y, x - y                     # s from the tip at (0, 0); k across (+ = upper right)
            else:
                xx = size - 1 - x
                sv, k = xx + y, y - xx                   # mirrored: tip at (size-1, 0)
            col = None
            if sv <= blade_end:
                h = half(sv)
                if abs(k) <= h + 0.01:
                    if k == 0:
                        col = pulse                      # the glowing ridge
                    elif abs(k) >= h - 0.5:
                        col = edge_lit if k > 0 else st[1]   # the honed edge catches the light on the upper side only
                    elif k == 1:
                        col = st[4]                      # a sheen beside the ridge
                    else:
                        col = st[3] if k > 0 else st[2]
            elif sv <= socket_end:
                mid = (blade_end + socket_end) / 2
                if abs(k) <= (2 if big else 1):
                    col = vi[4] if (k == 0 and abs(sv - mid) < 1) else st[4] if k > 0 else st[3]
                elif big and abs(k) == 3 and sv > mid:
                    col = st[4]                          # the lugs, swept back
            elif sv <= shaft_end:
                if k in (0, 1):
                    band = big and int(sv) % 7 == 0
                    col = hc[2] if band else (sk[3] if k == 1 else sk[2])
            elif sv <= grip_end:
                if k in (0, 1) or (big and k == -1):
                    col = vi[2] if int(sv) % 3 == 0 else (RAMPS["ink"][3] if k == 1 else RAMPS["ink"][2])
            elif sv <= span:
                if abs(k) <= (1 if big else 0) or k == 1:
                    col = hc[4] if (big and abs(sv - (grip_end + span) / 2) < 1 and k == 0) else st[4] if k > 0 else st[3]
            if col is not None:
                img.putpixel((x, y), col)
    filled = {(x, y) for y in range(size) for x in range(size) if img.getpixel((x, y))[3]}
    for (x, y) in list(filled):                          # a coloured outline in the steel's own black
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < size and 0 <= q[1] < size and q not in filled:
                img.putpixel(q, st[0])
    return img


def dreadlance(frame=0):
    """The Dreadlance's icon - a spear like vanilla's, upgraded and dark (see spear_sprite)."""
    icon = Icon(16)
    icon.img = spear_sprite(16, frame, head_at_left=False)
    return icon


def dreadlance_in_hand(frame=0):
    """The Dreadlance in the hand: a 32 px sprite in vanilla's spear_in_hand layout (head top-left)."""
    return spear_sprite(32, frame, head_at_left=True)


def soulfire_censer(frame=0):
    """The Soulfire Censer, the Wyrmbreath's successor: a gothic censer - a caged orb of dark iron bound with gold
    filigree, a domed spire on top and a finial below, soul fire blazing inside the bars and venting from it, a trail
    of hollow smoke curling away; it hangs on a chain from a gold ring and swings (animated)."""
    icon = Icon(16)
    ir, hc, gd, ink = RAMPS["boundsteel"], RAMPS["hollowcy"], RAMPS["gold"], RAMPS["ink"]
    k = frame % 4
    swing = [0, 1, 0, -1][k] * 0.5
    cx, cy = 9.8 + swing, 9.6
    ring = icon.ring(2.4, 2.4, 2.0, 1.0)
    icon.paint(ring, gd, bias=0.1)
    chain = line_px((3.6, 3.6), (cx, cy - 6.4))
    put(icon, [p for i, p in enumerate(chain) if i % 2 == 0], ir[4])
    put(icon, [p for i, p in enumerate(chain) if i % 2 == 1], ir[2])
    cage = icon.sphere(cx, cy, 4.0)
    for (x, y) in cage.keys():   # the fire inside, brightest at its heart
        dd = math.hypot(x + 0.5 - cx, y + 0.5 - cy - 0.6)
        put(icon, [(x, y)], hc[5] if dd < 1.4 + (k % 2) * 0.4 else hc[4] if dd < 2.6 else hc[3])
    for (x, y) in cage.keys():   # the iron bars and rims over it
        dx = x + 0.5 - cx
        rim = math.hypot(dx, y + 0.5 - cy) > 3.2
        if rim or abs(dx) < 0.5 or abs(abs(dx) - 2.0) < 0.5:
            put(icon, [(x, y)], ir[3] if dx < 0 else ir[1])
    put(icon, [(x, math.floor(cy)) for x in range(math.floor(cx - 4), math.floor(cx + 4) + 1)
               if (x, math.floor(cy)) in cage.normals], gd[4])                                # the gold band
    icon.outline(cage, [ink[0], ink[0]], over=False)
    dome = icon.polygon([(cx - 2.8, cy - 3.2), (cx + 2.8, cy - 3.2), (cx, cy - 6.6)], bevel=1.0)
    icon.paint(dome, gd, bias=0.1, outline_over=False)
    fin = icon.polygon([(cx - 1.6, cy + 3.6), (cx + 1.6, cy + 3.6), (cx, cy + 6.2)], bevel=0.6)
    icon.paint(fin, gd, bias=-0.05, outline_over=False)
    for i, (fx, h) in enumerate(((-2, 2), (2, 3))):   # soul fire venting at the shoulders
        hh = h + [0, 1, 0, -1][(k + i) % 4]
        put(icon, [(math.floor(cx + fx), math.floor(cy - 3.6 - j)) for j in range(max(1, hh))], hc[4])
    trail = [(13, 3), (14, 2), (15, 1), (14, 0)]
    put(icon, [trail[(k + j) % 4] for j in range(2)], hc[3], 170)
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


# ================================================================== F4: Hollow armor, hand-drawn plate by plate
# A richer scheme than the first try: blackened violet steel plates (each lit on its own, so they read as separate
# pieces of metal), aged gold trim, bone, a hollow-cyan glow in the seams and crimson gems. Silhouettes follow the
# vanilla armor icons. Letters: H highlight, L light plate, M mid, D dark, K seam/shadow, G gold, g dark gold,
# B bone, b bone shade, C hollow glow (animated), R crimson.

# The Hollow set, redrawn to match the worn armour (G6, locked in): a sculk soul machine - black-grey reinforced plates
# (H L M D K), sculk infection (T bright, S, s dark), soul power in light blue (C, animated; W white-hot; c a crack),
# purple trim (P, p) - and on the helm the purple warden tendrils.
HOLLOW_HELM = [
    "................",
    ".P............P.",
    ".PP..........PP.",
    "..Pp.LLLLLL.pP..",
    "..pPLHHHHHHMPp..",
    "...LHMMMMMMMDD..",
    "...LCCCWCCCCDD..",
    "...LMKKKKKKMDD..",
    "...LMKKKKKKMDD..",
    "...SMKKKKKKMsD..",
    "...TSMKKKKMssD..",
    "...SsMM..MMssD..",
    "....sDD..DDs....",
    "................",
    "................",
    "................",
]
HOLLOW_CHEST = [
    "................",
    "................",
    ".HLLL......LLMD.",
    ".LMMDL....LMMDD.",
    ".LMCDLLLLLLMCDD.",
    ".pMMDLHSSSHLMDp.",
    "..ppDLSTCTSLDp..",
    "....LHSCWCSMD...",
    "....LMSTCTSMD...",
    "....LMcSSSMMD...",
    "....LMMcMcMMD...",
    "....LMMMMMMMD...",
    "....pppppppp....",
    "................",
    "................",
    "................",
]
HOLLOW_LEGS = [
    "................",
    "................",
    "...LLLLLLLLLD...",
    "...LMMMCMMMMD...",
    "....LHMD.LHMD...",
    "....LTSD.LTSD...",
    "....LSCD.LSCD...",
    "....LscD.LscD...",
    "....LHPD.LHPD...",
    "....LMCD.LMCD...",
    "....LMMD.LMMD...",
    "....LMMD.LMMD...",
    "....KKKK.KKKK...",
    "................",
    "................",
    "................",
]
HOLLOW_BOOTS = [
    "................",
    "................",
    "................",
    "................",
    "...LLD....LLD...",
    "...PPp....PPp...",
    "...LMD....LMD...",
    "...LSD....LSD...",
    "..LHMD....LHMD..",
    "..LMMDD..LMMDD..",
    ".LMMMMD..LMMMMD.",
    ".CCCCCC..CCCCCC.",
    "................",
    "................",
    "................",
    "................",
]


def hollow_armor(rows, frame):
    icon = Icon(16)
    ds = [(20, 20, 24, 255), (36, 36, 43, 255), (53, 53, 62, 255), (74, 74, 84, 255), (98, 98, 108, 255), (126, 126, 136, 255)]
    sk, hc, vi = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["violet"]
    for row in rows:
        assert len(row) == 16, row
    pulse = hc[[3, 4, 5, 4][frame % 4]]
    cols = {"H": ds[5], "L": ds[4], "M": ds[3], "D": ds[2], "K": ds[0], "T": sk[4], "S": sk[3], "s": sk[1],
            "C": pulse, "W": (255, 255, 255, 255), "c": hc[4], "P": vi[4], "p": vi[2]}
    pixmap(icon, rows, 0, 0, cols)
    mask = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != "."}
    icon.outline(Part({p: (0, 0, 1) for p in mask}), [ds[1], ds[0]], over=False)
    return icon


def hollow_helmet(frame=0):
    """The Hollow Crown: an open-faced helm of black-grey reinforced steel, a soul conduit burning across its brow,
    sculk creeping up its cheek guards, and the warden's tendrils in purple rising from its sides."""
    return hollow_armor(HOLLOW_HELM, frame)


def hollow_chestplate(frame=0):
    """The Hollow Cuirass: heavy steel pauldrons with soul cores, the soul reactor in the chest infected with sculk,
    cracks of soul light running down from it, a purple hem."""
    return hollow_armor(HOLLOW_CHEST, frame)


def hollow_leggings(frame=0):
    """The Hollow Greaves: a steel belt with a soul core, plated legs with sculk infection on the thighs, purple-trimmed
    knee guards with soul cores."""
    return hollow_armor(HOLLOW_LEGS, frame)


def hollow_boots(frame=0):
    """The Hollow Sabatons: heavy steel boots with purple cuffs, a touch of sculk, glowing soul soles."""
    return hollow_armor(HOLLOW_BOOTS, frame)


F4 = [("Hollow Crown", hollow_helmet, 4), ("Hollow Cuirass", hollow_chestplate, 4),
      ("Hollow Greaves", hollow_leggings, 4), ("Hollow Sabatons", hollow_boots, 4)]
GROUPS = {"f1": F1, "f2": F2, "f3": F3, "f4": F4}


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


# ------------------------------------------------------------------ the Heartwood Aegis is a real shield: a 3D texture

SHIELD_UV = {  # the vanilla shield model's box unwrap on a 64 x 64 sheet (plate 12x22x1 at 0,0; handle 2x6x6 at 26,0)
    "front": (1, 1, 12, 22), "back": (14, 1, 12, 22), "left": (0, 1, 1, 22), "right": (13, 1, 1, 22),
    "top": (1, 0, 12, 1), "bottom": (13, 0, 12, 1), "handle": (26, 0, 16, 12),
}


def heartwood_shield_texture(frame=0):
    """The Heartwood Aegis as a shield texture in the vanilla shield's layout: the front is dark heartwood with its
    grain running down it, two veins of amber resin flowing through the grain, a bone rim with gold corner caps, an
    amber boss and a green rune of regrowth that pulses (animated); the back is lighter planks with leather straps and
    iron studs; the edges are bone; the handle is leather."""
    from PIL import Image
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    wood, am, bone, gd, gel, lea, ir = (RAMPS["wood"], RAMPS["amber"], RAMPS["bone"], RAMPS["gold"], RAMPS["gel"],
                                        RAMPS["leather"], RAMPS["iron"])
    fx, fy, fw, fh = SHIELD_UV["front"]
    for v in range(fh):
        for u in range(fw):
            c = wood[2] if (u + round(1.4 * math.sin(v * 0.45))) % 3 else wood[1]
            if u in (1, 2) and v > 1:
                c = wood[3] if c == wood[2] else c    # the lit side of the curve
            for (x0, ph) in ((2.6, 0.0), (9.4, 2.2)):   # resin veins: thin, running down the grain
                if abs(u + 0.5 - (x0 + 1.0 * math.sin(v * 0.33 + ph))) < 0.5:
                    c = am[4] if (v + int(ph * 3)) % 9 == 0 else am[2]
            if u == 0 or v == 0:
                c = bone[4]
            elif u == fw - 1 or v == fh - 1:
                c = bone[2]
            if (u < 2 or u > fw - 3) and (v < 2 or v > fh - 3):
                c = gd[4] if u < 6 and v < 11 else gd[3]
            img.putpixel((fx + u, fy + v), c)
    pulse = [3, 4, 5, 4][frame % 4]
    rune = [  # a tree of regrowth: a trunk, branches reaching out, roots
        ".....gg.....",
        "...g.GG.g...",
        "....gGGg....",
        "..g..GG..g..",
        "...g.GG.g...",
        "....gGGg....",
        ".....GG.....",
        ".....GG.....",
        "....gGGg....",
        "...g....g...",
    ]
    for dv, row in enumerate(rune):
        for u, ch in enumerate(row):
            if ch != ".":
                img.putpixel((fx + u, fy + 8 + dv), gel[pulse] if ch == "G" else gel[pulse - 1])
    for (u, v, c) in ((5, 4, am[4]), (6, 4, am[3]), (5, 5, am[3]), (6, 5, am[2]), (5, 3, gd[4]), (6, 3, gd[3]),
                      (4, 4, gd[4]), (7, 4, gd[3]), (4, 5, gd[3]), (7, 5, gd[2]), (5, 6, gd[2]), (6, 6, gd[2])):
        img.putpixel((fx + u, fy + v), c)   # the boss: an amber gem in a gold setting
    img.putpixel((fx + 5, fy + 4), am[5])
    bx, by, bw, bh = SHIELD_UV["back"]
    for v in range(bh):
        for u in range(bw):
            c = wood[3] if v % 5 else wood[2]
            if u in (3, 8):
                c = lea[3] if u == 3 else lea[2]
            if u in (3, 8) and v % 7 == 3:
                c = ir[4]
            img.putpixel((bx + u, by + v), c)
    for key, col in (("left", bone[3]), ("right", bone[2]), ("top", bone[4]), ("bottom", bone[2])):
        x0, y0, w, h = SHIELD_UV[key]
        for v in range(h):
            for u in range(w):
                img.putpixel((x0 + u, y0 + v), col)
    hx, hy, hw, hh = SHIELD_UV["handle"]
    for v in range(hh):
        for u in range(hw):
            if (u < 6 and v >= 6) or (u >= 6 and v < 6) or (u >= 6 and v >= 6):
                img.putpixel((hx + u, hy + v), lea[3] if (u + v) % 4 else lea[2])
    return img


def shield_preview(tex, scale=6):
    """How the shield looks as a 3D object: the front face, its right edge and top edge in an oblique view, and the
    flat front and back faces for reference."""
    from PIL import Image, ImageDraw
    fx, fy, fw, fh = SHIELD_UV["front"]
    out = Image.new("RGBA", ((fw + 4) * scale * 3 + 40, (fh + 8) * scale + 30), (34, 32, 40, 255))
    d = ImageDraw.Draw(out)
    # oblique 3D view: shear the front up toward the right, then add the side (right edge) and top edge in depth
    ox, oy = 10, 40
    depth = 2
    for v in range(fh):
        for u in range(fw):
            c = tex.getpixel((fx + u, fy + v))
            x, y = ox + u * scale, oy + (v - u * 0.25) * scale
            d.rectangle((x, y, x + scale - 1, y + scale - 1), fill=c)
    rx, ry, _, _ = SHIELD_UV["right"]
    for v in range(fh):
        for k in range(depth):
            c = tex.getpixel((rx, ry + v))
            c = (c[0] * 7 // 10, c[1] * 7 // 10, c[2] * 7 // 10, 255)
            x, y = ox + (fw + k) * scale, oy + (v - fw * 0.25 - k * 0.5) * scale
            d.rectangle((x, y, x + scale - 1, y + scale - 1), fill=c)
    tx, ty, _, _ = SHIELD_UV["top"]
    for u in range(fw):
        for k in range(depth):
            c = tex.getpixel((tx + u, ty))
            x, y = ox + (u + k) * scale, oy + (-1 - u * 0.25 - k * 0.5) * scale
            d.rectangle((x, y, x + scale - 1, y + scale - 1), fill=c)
    d.text((ox, 8), "3D view", fill=(220, 220, 230))
    for n, key in enumerate(("front", "back")):
        x0, y0, w, h = SHIELD_UV[key]
        face = tex.crop((x0, y0, x0 + w, y0 + h)).resize((w * scale, h * scale), Image.NEAREST)
        px = 10 + (fw + 4) * scale * (n + 1)
        out.alpha_composite(face, (px, 40))
        d.text((px, 8), key, fill=(220, 220, 230))
    return out


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
      ("Gallus Egg", gallus_egg, 4), ("Watchful Eyeblossom", watchful_eyeblossom, 4)]
GROUPS = {"f1": F1, "f2": F2, "f3": F3, "f4": F4, "f5": F5}


def tier3_set():
    """Every tier-3 icon (Session A's Hollow Sigil included), first frame."""
    from PIL import Image
    sigil = Image.open(os.path.join(OUT, "..", "session-a", "hollow_sigil.png")).convert("RGBA")
    icons = [("Hollow Sigil", sigil)]
    for group in (F1, F2, F3, F4, F5):
        icons += [(name, make(0).img) for name, make, _ in group]
    icons.append(("Stormstring Bow", stormstring_bow(0).img))
    from PIL import Image
    tex = heartwood_shield_texture(0)
    x0, y0, w, h = SHIELD_UV["front"]
    front = tex.crop((x0, y0, x0 + w, y0 + h)).resize((8, 15), Image.NEAREST)
    stand_in = Image.new("RGBA", (16, 16))
    stand_in.paste(front, (4, 0))
    icons.append(("Heartwood Aegis (3D model)", stand_in))
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
    if which == "f5":   # the Heartwood Aegis is a shield: a 64x64 texture in the vanilla layout (4 frames), a preview
        texes = [heartwood_shield_texture(f) for f in range(4)]
        for f, tex in enumerate(texes):
            tex.save(os.path.join(OUT, f"heartwood_aegis_shield_{f}.png"))
        shield_preview(texes[0], scale=10).save(os.path.join(OUT, f"review-heartwood-aegis{suffix}.png"))
        review.gif([[shield_preview(t, scale=4) for t in texes]], os.path.join(OUT, "preview-heartwood-aegis.gif"), ms=220, scale=1)
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
