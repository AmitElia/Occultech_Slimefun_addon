"""Session G: blocks. Placed Occultech blocks are *skinned*: the vanilla block stays (Slimefun's block), an item display
shows our model over it, a hair larger, so the vanilla block is hidden - nothing vanilla is retextured. Each model
must enclose its vanilla block's shape. The inventory shows the same model.

Outputs per block in docs/art/session-g/<key>/: model.json + textures (<name>.png, animated ones as frames
<name>_0.png..), picked up by tools/art/build_pack.py. Review sheets are 3D renders (blockkit.render_iso).

Run: python tools/art/session_g.py g1 [version]
"""
import json
import math
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from blockkit import Model, review  # noqa: E402
from PIL import Image  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-g")
os.makedirs(OUT, exist_ok=True)


def blank():
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def put(img, pts, c):
    for (x, y) in pts:
        if 0 <= x < 16 and 0 <= y < 16:
            img.putpixel((x, y), c)


def bricks(ramp, seed, row_h=4, brick_w=8, tones=(2, 3, 3, 4)):
    """Running-bond masonry: mortar in the ramp's darkest tone, each brick its own tone, lit on its top-left edge
    and shadowed on its bottom-right (so every brick has a little volume)."""
    rnd = random.Random(seed)
    img = blank()
    shades = {}
    for y in range(16):
        row = y // row_h
        off = (row % 2) * (brick_w // 2)
        for x in range(16):
            bx = (x + off) // brick_w
            if y % row_h == row_h - 1 or (x + off) % brick_w == brick_w - 1:
                img.putpixel((x, y), ramp[0] if (x + y) % 3 else ramp[1])
                continue
            key = (row, bx)
            if key not in shades:
                shades[key] = rnd.choice(tones)
            t = shades[key]
            if y % row_h == 0 or (x + off) % brick_w == 0:
                t = min(len(ramp) - 1, t + 1)
            elif y % row_h == row_h - 2 or (x + off) % brick_w == brick_w - 2:
                t = max(1, t - 1)
            img.putpixel((x, y), ramp[t])
    for _ in range(10):   # wear: a few chips
        x, y = rnd.randrange(16), rnd.randrange(16)
        if img.getpixel((x, y)) not in (ramp[0], ramp[1]):
            img.putpixel((x, y), ramp[max(1, 2)])
    return img


def slab_top(ramp, seed, tone=3):
    """A worked stone top: one stone, softly mottled, a bevelled rim (lit top-left, dark bottom-right)."""
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        for x in range(16):
            t = tone + (1 if rnd.random() < 0.18 else -1 if rnd.random() < 0.18 else 0)
            if x == 0 or y == 0:
                t = tone + 1
            elif x == 15 or y == 15:
                t = tone - 1
            img.putpixel((x, y), ramp[max(1, min(len(ramp) - 1, t))])
    return img


def circle_pts(cx, cy, r, steps=48):
    pts = set()
    for i in range(steps):
        a = 2 * math.pi * i / steps
        pts.add((math.floor(cx + r * math.cos(a)), math.floor(cy + r * math.sin(a))))
    return sorted(pts)


# ================================================================== G1: tier-0 blocks

def initiate_altar():
    """The Initiate's Altar (vanilla: lodestone, a full cube): a block of chalk-stone masonry on a dark plinth, a band
    of ember-lit runes carved round it, a bone trim; its top a worked slab with the Initiate sigil inlaid in ember that
    breathes (animated); four tallow candles at the corners, burning."""
    m = Model("initiate_altar")
    ch, ash, em, bone, wax = RAMPS["chalk"], RAMPS["ash"], RAMPS["ember"], RAMPS["bone"], RAMPS["wax"]
    side = bricks(ch, 3)
    for x in range(16):
        side.putpixel((x, 15), ash[1]); side.putpixel((x, 14), ash[2]); side.putpixel((x, 13), ash[3])
        side.putpixel((x, 0), bone[4]); side.putpixel((x, 1), bone[2])
    for x in range(1, 15):   # the carved rune band
        side.putpixel((x, 6), ash[1]); side.putpixel((x, 9), ash[1])
        for y in (7, 8):
            side.putpixel((x, y), ash[2])
    runes = [(2, 7), (3, 8), (4, 7), (7, 7), (8, 7), (7, 8), (8, 8), (11, 8), (12, 7), (13, 8)]
    put(side, runes, em[4])
    put(side, [(3, 7), (12, 8)], em[3])
    frames = []
    for f in range(4):
        top = slab_top(ch, 11, tone=3)
        glow = [em[3], em[4], em[5], em[4]][f]
        put(top, circle_pts(7.5, 7.5, 6.2), em[2])
        diamond = [(7, 2), (8, 2), (6, 3), (9, 3), (5, 4), (10, 4), (4, 5), (11, 5), (3, 6), (12, 6), (2, 7), (13, 7),
                   (2, 8), (13, 8), (3, 9), (12, 9), (4, 10), (11, 10), (5, 11), (10, 11), (6, 12), (9, 12), (7, 13), (8, 13)]
        put(top, diamond, glow)
        put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], em[5] if f in (1, 2) else em[4])
        frames.append(top)
    t_side = m.texture("side", side)
    t_top = m.texture("top", frames)
    t_bottom = m.texture("bottom", slab_top(ash, 5, tone=2))
    m.box((0, 0, 0), (16, 16, 16), {"north": t_side, "south": t_side, "west": t_side, "east": t_side,
                                     "up": t_top, "down": t_bottom})
    candle = blank()
    for y in range(16):
        for x in range(16):
            candle.putpixel((x, y), wax[4] if x < 2 else wax[3] if x < 4 else wax[2])
    put(candle, [(1, 0), (2, 0), (1, 1)], wax[5])
    flame = blank()
    for y in range(16):
        for x in range(16):
            flame.putpixel((x, y), em[5] if y > 9 else em[4] if y > 4 else em[3])
    t_c = m.texture("candle", candle)
    t_f = m.texture("flame", flame)
    for (x, z) in ((1, 1), (13, 1), (1, 13), (13, 13)):
        m.cube((x, 16, z), (x + 2, 19, z + 2), (t_c, [0, 0, 4, 6]), top=(t_c, [0, 0, 2, 2]))
        m.box((x + 0.5, 19, z + 0.5), (x + 1.5, 21, z + 1.5),
              {d: (t_f, [0, 0, 16, 16]) for d in ("north", "south", "west", "east", "up")}, shade=False)
    return m


def offering_bowl():
    """The Offering Bowl, kept low so a ring of them never hides the altar (vanilla: black carpet, 1 px): a thin
    blackstone plate covering the carpet, carved at its edge, and on it a low, wide bowl of hammered dark iron with
    embers glowing in it (animated). About 5 px tall in all."""
    m = Model("offering_bowl")
    ash, ir, em = RAMPS["ash"], RAMPS["iron"], RAMPS["ember"]
    plate = slab_top(ash, 9, tone=2)
    for i in range(16):
        for (x, y) in ((i, 1), (i, 14), (1, i), (14, i)):
            plate.putpixel((x, y), ash[1])
    edge = blank()
    for y in range(16):
        for x in range(16):
            edge.putpixel((x, y), ash[2] if y == 0 else ash[1])
    bowl = blank()
    for y in range(16):
        for x in range(16):
            bowl.putpixel((x, y), ir[2] if (x * 3 + y * 5) % 7 else ir[1])   # hammered, dark iron
    put(bowl, [(x, 0) for x in range(16)], ir[4])
    embers = []
    for f in range(4):
        e = blank()
        rnd = random.Random(40 + f)
        for y in range(16):
            for x in range(16):
                v = rnd.random()
                e.putpixel((x, y), em[5] if v < 0.06 else em[4] if v < 0.2 else em[3] if v < 0.45 else ash[1])
        embers.append(e)
    t_plate, t_edge, t_bowl, t_emb = m.texture("plate", plate), m.texture("edge", edge), m.texture("bowl", bowl), m.texture("embers", embers)
    m.box((0, 0, 0), (16, 1.2, 16), {"up": t_plate, "down": t_plate, "north": (t_edge, [0, 0, 16, 1]),
                                      "south": (t_edge, [0, 0, 16, 1]), "west": (t_edge, [0, 0, 16, 1]),
                                      "east": (t_edge, [0, 0, 16, 1])})
    m.cube((5, 1.2, 5), (11, 2, 11), (t_bowl, [0, 0, 6, 1]))                         # the foot
    m.box((3.5, 3.6, 3.5), (12.5, 4, 12.5), {"up": t_emb}, shade=False)              # the embers inside
    for (frm, to) in (((2, 2, 2), (14, 5, 3)), ((2, 2, 13), (14, 5, 14)), ((2, 2, 3), (3, 5, 13)), ((13, 2, 3), (14, 5, 13))):
        m.cube(frm, to, (t_bowl, [0, 0, 12, 3]), top=(t_bowl, [0, 0, 12, 1]))
    m.cube((3, 2, 3), (13, 3.6, 13), (t_bowl, [0, 4, 10, 6]), top=(t_bowl, [2, 2, 12, 12]))   # the bowl's floor
    return m


GLYPH_RUNES = [  # 8x8 chalk marks at the tile's centre, one per variant (the circle shows a mix)
    ["...##...", "..#..#..", ".#.##.#.", "#.#..#.#", "#.#..#.#", ".#.##.#.", "..#..#..", "...##..."],
    ["...#....", "..###...", ".#.#.#..", "...#....", "...#....", ".#.#.#..", "..###...", "...#...."],
    ["#......#", ".#....#.", "..#..#..", "...##...", "...##...", "..#..#..", ".#....#.", "#......#"],
    ["..####..", ".#....#.", "#..##..#", "#.#..#.#", "#.#..#.#", "#..##..#", ".#....#.", "..####.."],
]


def chalk_glyph(variant=0):
    """A Chalk Glyph (vanilla: white carpet, 1 px tall): a thin tile of dark slate covering the carpet, a chalk rune
    drawn on it - four variants, so a circle of glyphs shows a mix - with chalk dust smudged round the mark."""
    m = Model("chalk_glyph" + ("" if variant == 0 else f"_v{variant}"))
    ash, ch = RAMPS["ash"], RAMPS["chalk"]
    rnd = random.Random(70 + variant)
    top = slab_top(ash, 60 + variant, tone=2)
    for _ in range(18):   # dust
        top.putpixel((rnd.randrange(16), rnd.randrange(16)), ash[3])
    for y, row in enumerate(GLYPH_RUNES[variant]):
        for x, c in enumerate(row):
            if c == "#":
                top.putpixel((4 + x, 4 + y), ch[4] if (x + y) % 4 else ch[3])
    side = blank()
    for y in range(16):
        for x in range(16):
            side.putpixel((x, y), ash[1])
    t_top, t_side = m.texture("top", top), m.texture("side", side)
    m.box((0, 0, 0), (16, 1.2, 16), {"up": t_top, "north": (t_side, [0, 0, 16, 1]), "south": (t_side, [0, 0, 16, 1]),
                                      "west": (t_side, [0, 0, 16, 1]), "east": (t_side, [0, 0, 16, 1]), "down": t_top})
    return m


def arcane_altar():
    """The Arcane Altar (vanilla: enchanting table; the skin is a full cube so the floating book is hidden): a block of
    dark stone banded in gold, its corners capped in gold, its sides set with ember-glowing arcane eyes; the top a slab
    with an arcane circle and an infusion star that turn and glow (animated)."""
    m = Model("arcane_altar")
    ash, gd, em, vi = RAMPS["ash"], RAMPS["gold"], RAMPS["ember"], RAMPS["violet"]
    side = bricks(ash, 21, row_h=5, brick_w=8, tones=(2, 2, 3))
    for x in range(16):
        side.putpixel((x, 0), gd[4]); side.putpixel((x, 1), gd[2]); side.putpixel((x, 15), gd[2]); side.putpixel((x, 14), gd[3])
    for y in range(16):
        for x in (0, 15):
            side.putpixel((x, y), gd[3] if x == 0 else gd[2])
    eye = [(6, 7), (7, 6), (8, 6), (9, 7), (6, 8), (7, 9), (8, 9), (9, 8)]
    put(side, eye, gd[4])
    put(side, [(7, 7), (8, 7), (7, 8), (8, 8)], em[4])
    put(side, [(7, 7)], em[5])
    frames = []
    for f in range(4):
        top = slab_top(ash, 23, tone=2)
        put(top, circle_pts(7.5, 7.5, 6.6), gd[3])
        put(top, circle_pts(7.5, 7.5, 4.6), gd[2])
        a0 = f * math.pi / 8
        for k in range(8):   # a turning eight-pointed star
            a = a0 + k * math.pi / 4
            for r in (1.5, 2.5, 3.5):
                put(top, [(math.floor(7.5 + r * math.cos(a)), math.floor(7.5 + r * math.sin(a)))], em[4] if r < 3 else em[3])
        put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], em[5])
        for k in range(4):
            a = a0 * 2 + k * math.pi / 2
            put(top, [(math.floor(7.5 + 6.6 * math.cos(a)), math.floor(7.5 + 6.6 * math.sin(a)))], vi[4])
        frames.append(top)
    t_side, t_top, t_bottom = m.texture("side", side), m.texture("top", frames), m.texture("bottom", slab_top(ash, 2, tone=1))
    m.box((0, 0, 0), (16, 16, 16), {"north": t_side, "south": t_side, "west": t_side, "east": t_side,
                                     "up": t_top, "down": t_bottom})
    return m


# ================================================================== G2: the rest of tier 0, tier 1

def fill(ramp, idx):
    img = blank()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), ramp[idx])
    return img


def rim(img, light, dark):
    """A bevel on a face: lit top and left edges, shadowed bottom and right."""
    for i in range(16):
        img.putpixel((i, 0), light); img.putpixel((0, i), light)
        img.putpixel((i, 15), dark); img.putpixel((15, i), dark)
    return img


def planks(ramp, seed, plank_h=4):
    """Horizontal boards: a dark seam between boards, grain streaks, a lighter top edge on each board."""
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        board = y // plank_h
        tone = 2 + (board % 2)
        for x in range(16):
            if y % plank_h == plank_h - 1:
                c = ramp[0]
            elif y % plank_h == 0:
                c = ramp[tone + 1]
            else:
                c = ramp[tone] if (x * 7 + board * 11 + rnd.randrange(3)) % 9 else ramp[tone - 1]
            img.putpixel((x, y), c)
    return img


def arcane_pedestal():
    """The Arcane Pedestal (vanilla: polished deepslate wall - the skin encloses the wall's post): a deepslate column with
    a stepped base and capital banded in gold, an arcane eye glowing on the capital's top where the offering rests
    (animated)."""
    m = Model("arcane_pedestal")
    ash, gd, em = RAMPS["ash"], RAMPS["gold"], RAMPS["ember"]
    shaft = bricks(ash, 31, row_h=4, brick_w=16, tones=(2, 3))
    for y in range(16):
        shaft.putpixel((0, y), ash[3]); shaft.putpixel((15, y), ash[1])
    band = rim(fill(ash, 2), ash[4], ash[1])
    for x in range(16):
        band.putpixel((x, 1), gd[4]); band.putpixel((x, 14), gd[2])
    frames = []
    for f in range(4):
        top = rim(slab_top(ash, 33, tone=2), gd[4], gd[2])
        put(top, circle_pts(7.5, 7.5, 4.4), gd[3])
        put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], em[[3, 4, 5, 4][f]])
        put(top, [(6, 7), (9, 8), (7, 6), (8, 9)], em[[2, 3, 4, 3][f]])
        frames.append(top)
    t_shaft, t_band, t_top = m.texture("shaft", shaft), m.texture("band", band), m.texture("top", frames)
    m.cube((2, 0, 2), (14, 3, 14), (t_band, [0, 0, 12, 3]), top=t_band, bottom=t_band)
    m.cube((3.5, 3, 3.5), (12.5, 13, 12.5), (t_shaft, [0, 3, 9, 13]))
    m.cube((2, 13, 2), (14, 16, 14), (t_band, [0, 13, 12, 16]), top=t_top, bottom=t_band)
    return m


def brood_egg():
    """The Brood Egg (vanilla: sniffer egg - the skin encloses it): a rounded sac of spider silk built up in layers,
    wound with clear bands of thread, dark eggs pressing against it from inside and crimson veins pulsing through it;
    a strand rising from its top (animated)."""
    m = Model("brood_egg")
    bone, cr, ink = RAMPS["bone"], RAMPS["crimson"], RAMPS["ink"]
    frames = []
    for f in range(4):
        silk = blank()
        for y in range(16):
            for x in range(16):
                band = (x + y) % 5 == 0          # wound thread
                silk.putpixel((x, y), bone[2] if band else bone[4] if y < 4 else bone[3])
        for (cx, cy) in ((3, 5), (10, 3), (7, 10), (12, 11)):   # eggs pressing from inside
            put(silk, [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)], ink[3])
            put(silk, [(cx, cy)], ink[4])
        glow = cr[[2, 3, 4, 3][f]]
        put(silk, [(1, 2), (2, 3), (2, 4), (3, 6), (4, 7), (5, 8), (5, 9), (6, 11), (13, 2), (13, 3), (12, 5), (12, 6),
                   (13, 8), (14, 9)], glow)
        frames.append(silk)
    t = m.texture("silk", frames)
    top = m.texture("top", rim(fill(bone, 4), bone[5], bone[2]))
    m.cube((0.8, 0, 1.8), (15.2, 16, 14.2), t, top=top, bottom=top)
    m.cube((0, 2, 1), (16, 14, 15), (t, [0, 2, 16, 14]))
    m.cube((-0.6, 4.5, 0.4), (16.6, 11.5, 15.6), (t, [0, 4, 16, 11]))
    m.cube((2.5, 16, 3.5), (13.5, 17.5, 12.5), (t, [2, 0, 13, 2]), top=top)
    m.cube((5, 17.5, 6), (11, 18.5, 10), (t, [5, 0, 11, 1]), top=top)
    m.box((7.5, 18.5, 7.5), (8.5, 22, 8.5), {d: (t, [0, 0, 1, 4]) for d in ("north", "south", "west", "east")})
    return m


def trophy_board():
    """The Trophy Board (vanilla: chiseled tuff bricks, a cube): a display pedestal - dark polished wood panels in gilded
    frames, a gold crest of crossed blades on each side, and a crimson velvet top edged in gold where the trophies
    float (the board's own displays)."""
    m = Model("trophy_board")
    wood, gd, cr = RAMPS["wood"], RAMPS["gold"], RAMPS["crimson"]
    side = blank()
    for y in range(16):
        for x in range(16):
            side.putpixel((x, y), wood[1] if (x * 3 + y) % 11 else wood[0])
    for i in range(16):   # the gilded frame
        for (x, y) in ((i, 0), (i, 1), (i, 14), (i, 15), (0, i), (1, i), (14, i), (15, i)):
            side.putpixel((x, y), gd[3] if x < 2 or y < 2 else gd[2])
    for i in range(3, 13):   # the inner panel's lit edge
        side.putpixel((i, 3), wood[2]); side.putpixel((3, i), wood[2])
    crest = [(5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (10, 5), (9, 6), (6, 9), (5, 10)]
    put(side, crest, gd[4])
    put(side, [(7, 8), (8, 7)], gd[5])
    put(side, [(4, 11), (11, 11), (4, 4), (11, 4)], gd[3])
    top = blank()
    for y in range(16):
        for x in range(16):
            top.putpixel((x, y), cr[2] if (x + y) % 6 else cr[1])
    rim(top, gd[4], gd[2])
    put(top, [(5, 4), (4, 5), (6, 4)], cr[3])   # the velvet's sheen
    t_side, t_top = m.texture("side", side), m.texture("top", top)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    return m


def chiming_tile():
    """The Chiming Amethyst Tile (vanilla: amethyst block): a pale stone tile set with a star of amethyst inlay that
    rings with light when the chime sounds (animated shimmer); amethyst veins run down its sides."""
    m = Model("chiming_tile")
    ch, vi, gl = RAMPS["chalk"], RAMPS["violet"], RAMPS["glass"]
    side = bricks(ch, 51, row_h=8, brick_w=16, tones=(2, 3))
    put(side, [(3, 2), (3, 3), (4, 4), (4, 5), (5, 6), (11, 9), (12, 10), (12, 11), (13, 12)], vi[3])
    put(side, [(3, 2), (12, 10)], vi[5])
    frames = []
    for f in range(4):
        top = rim(slab_top(ch, 53, tone=3), ch[4], ch[2])
        star = [(7, 2), (8, 2), (7, 3), (8, 3), (7, 12), (8, 12), (7, 13), (8, 13), (2, 7), (3, 7), (2, 8), (3, 8),
                (12, 7), (13, 7), (12, 8), (13, 8), (5, 5), (10, 5), (5, 10), (10, 10), (6, 6), (9, 6), (6, 9), (9, 9)]
        put(top, star, vi[3])
        ring = circle_pts(7.5, 7.5, 2.0 + f * 1.6)
        put(top, ring, gl[5] if f < 3 else gl[4])
        put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], vi[5])
        frames.append(top)
    t_side, t_top = m.texture("side", side), m.texture("top", frames)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=fill(ch, 2) and t_side)
    return m


def tier_glyph(key, chalk_ramp, base_ramp, glow_ramp, variant):
    """A circle glyph tile over a carpet: dark slate, a rune drawn in the tier's chalk, dust, a faint glow in the rune's
    heart."""
    m = Model(key + ("" if variant == 0 else f"_v{variant}"))
    rnd = random.Random(170 + variant)
    top = slab_top(base_ramp, 160 + variant, tone=2)
    for _ in range(18):
        top.putpixel((rnd.randrange(16), rnd.randrange(16)), base_ramp[3])
    for y, row in enumerate(GLYPH_RUNES[(variant + 1) % 4]):
        for x, c in enumerate(row):
            if c == "#":
                top.putpixel((4 + x, 4 + y), chalk_ramp[4] if (x + y) % 4 else chalk_ramp[3])
    put(top, [(7, 7), (8, 8)], glow_ramp[4])
    side = fill(base_ramp, 1)
    t_top, t_side = m.texture("top", top), m.texture("side", side)
    m.box((0, 0, 0), (16, 1.2, 16), {"up": t_top, "north": (t_side, [0, 0, 16, 1]), "south": (t_side, [0, 0, 16, 1]),
                                      "west": (t_side, [0, 0, 16, 1]), "east": (t_side, [0, 0, 16, 1]), "down": t_top})
    return m


def bound_altar():
    """The Bound Altar (vanilla: amethyst block; the Initiate's Altar upgrades into it): violet stone masonry gripped at
    its four corners by silver clamps, a binding band of spirit light round its middle, and on top the Bound sigil -
    ring, clamped triangle, a spirit at its heart - with the spirit itself rising from it as a small glowing orb
    (animated)."""
    m = Model("bound_altar")
    vi, ir, sp, st = RAMPS["violet"], RAMPS["iron"], RAMPS["spirit"], RAMPS["boundsteel"]
    frames_side, frames_top = [], []
    for f in range(4):
        side = bricks(st, 61, tones=(2, 3, 3))
        for x in range(16):
            side.putpixel((x, 7), sp[[2, 3, 4, 3][f]]); side.putpixel((x, 8), sp[[3, 4, 5, 4][f]])
            side.putpixel((x, 0), ir[4]); side.putpixel((x, 15), st[1])
        frames_side.append(side)
        top = rim(slab_top(st, 63, tone=2), ir[4], ir[2])
        put(top, circle_pts(7.5, 7.5, 6.2), vi[4])
        tri = [(7, 3), (8, 3), (6, 5), (9, 5), (5, 7), (10, 7), (4, 9), (11, 9), (3, 11), (12, 11)] + [(x, 11) for x in range(3, 13)]
        put(top, tri, vi[3])
        put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], sp[[3, 4, 5, 4][f]])
        frames_top.append(top)
    t_side, t_top = m.texture("side", frames_side), m.texture("top", frames_top)
    clamp = rim(fill(ir, 3), ir[5], ir[1])
    t_clamp = m.texture("clamp", clamp)
    orb = fill(sp, 5)
    put(orb, [(x, y) for x in range(16) for y in range(16) if (x + y) % 5 == 0], sp[4])
    t_orb = m.texture("orb", orb)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    for (x, z) in ((-0.5, -0.5), (13.5, -0.5), (-0.5, 13.5), (13.5, 13.5)):
        m.cube((x, 2, z), (x + 3, 14, z + 3), (t_clamp, [0, 0, 3, 12]), top=(t_clamp, [0, 0, 3, 3]))
    m.box((7, 17, 7), (9, 19, 9), {d: (t_orb, [0, 0, 2, 2]) for d in FACES_ALL}, shade=False)
    return m


FACES_ALL = ("north", "south", "west", "east", "up", "down")


def phantom_roost():
    """The Phantom Roost (vanilla: bone block): a lattice of bleached ribs bound into a block, dark gaps between them,
    dusk membrane stretched in the gaps; on top a nest of dark membrane with two crossed perch bones."""
    m = Model("phantom_roost")
    bone, du, ink = RAMPS["bone"], RAMPS["dusk"], RAMPS["ink"]
    side = blank()
    for y in range(16):
        for x in range(16):
            rib = x % 5 in (0, 1)
            side.putpixel((x, y), (bone[4] if x % 5 == 0 else bone[3]) if rib else (du[2] if (x + y) % 4 else du[1]))
    for y in (0, 15):
        for x in range(16):
            side.putpixel((x, y), bone[4] if y == 0 else bone[2])
    for x in (0, 5, 10, 15):
        put(side, [(x, 7), (x + 1, 7)], bone[5])
    top = blank()
    rnd = random.Random(71)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            top.putpixel((x, y), bone[3] if d > 6.5 else du[1] if d > 4 else ink[2] if rnd.random() < 0.7 else du[2])
    t_side, t_top = m.texture("side", side), m.texture("top", top)
    t_bone = m.texture("bone", rim(fill(bone, 4), bone[5], bone[2]))
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    m.cube((1, 16, 7), (15, 17.5, 8.5), (t_bone, [0, 0, 14, 2]))
    m.cube((7.5, 16, 1), (9, 17.5, 15), (t_bone, [0, 0, 14, 2]))
    return m


def frenzy_idol():
    """The Frenzy Idol (vanilla: chiseled resin bricks): dark crimson-stained stone carved into a snarling face - a deep
    recess, heavy brows, big eyes and a wide fanged maw glowing with frenzy (pulsing, animated) - with two bone horns
    curling up from its top."""
    m = Model("frenzy_idol")
    ash, cr, bone = RAMPS["ash"], RAMPS["crimson"], RAMPS["bone"]
    frames = []
    for f in range(4):
        face = bricks(cr, 81, row_h=8, brick_w=16, tones=(1, 2))
        for y in range(3, 14):   # the carved recess
            for x in range(2, 14):
                face.putpixel((x, y), cr[1] if (x + y) % 7 else cr[0])
        glow, hot = cr[[3, 4, 5, 4][f]], cr[[4, 5, 5, 5][f]]
        put(face, [(2, 4), (3, 4), (4, 5), (5, 5), (6, 6), (9, 6), (10, 5), (11, 5), (12, 4), (13, 4)], ash[0])   # brows
        put(face, [(4, 6), (5, 6), (4, 7), (5, 7), (10, 6), (11, 6), (10, 7), (11, 7)], glow)                   # eyes
        put(face, [(4, 6), (11, 6)], hot)
        for x in range(3, 13):   # the maw
            put(face, [(x, 10), (x, 11), (x, 12)], ash[0])
            put(face, [(x, 11)], glow if x % 2 else ash[0])
        put(face, [(3, 10), (5, 10), (7, 10), (9, 10), (11, 10), (4, 12), (6, 12), (8, 12), (10, 12), (12, 12)], bone[4])
        frames.append(face)
    plain = bricks(cr, 83, row_h=8, brick_w=16, tones=(1, 2))
    t_face, t_plain = m.texture("face", frames), m.texture("plain", plain)
    t_top = m.texture("top", rim(slab_top(cr, 85, tone=2), cr[3], cr[0]))
    t_horn = m.texture("horn", rim(fill(bone, 3), bone[5], bone[1]))
    m.box((0, 0, 0), (16, 16, 16), {"north": t_face, "south": t_face, "west": t_plain, "east": t_plain,
                                     "up": t_top, "down": t_plain})
    for x in (1, 12):
        m.cube((x, 16, 6), (x + 3, 19, 10), (t_horn, [0, 0, 3, 3]))
        tx = x - 1 if x < 8 else x + 2
        m.cube((tx, 19, 7), (tx + 2, 22, 9), (t_horn, [0, 0, 2, 3]))
    return m


def servitor_shrine():
    """The Servitor Shrine (vanilla: purpur pillar): a violet stone shrine framed in silver, an arched niche on each
    side where its bound spirit glows (animated), a stepped silver roof with a finial."""
    m = Model("servitor_shrine")
    st, ir, sp, vi = RAMPS["boundsteel"], RAMPS["iron"], RAMPS["spirit"], RAMPS["violet"]
    frames = []
    for f in range(4):
        side = bricks(st, 91, tones=(2, 3))
        for y in range(16):
            side.putpixel((0, y), ir[4]); side.putpixel((15, y), ir[2])
        for y in range(4, 14):   # the niche
            for x in range(5, 11):
                if y > 5 or 6 <= x <= 9:
                    side.putpixel((x, y), st[0])
        put(side, [(5, 5), (6, 4), (9, 4), (10, 5)], ir[4])
        sx = 7 + [0, 0, 1, 1][f]
        put(side, [(sx, 8), (sx + 1, 8), (sx, 9), (sx + 1, 9), (sx, 10)], sp[[3, 4, 5, 4][f]])
        put(side, [(sx, 8)], sp[5])
        frames.append(side)
    t_side = m.texture("side", frames)
    roof = rim(fill(ir, 3), ir[5], ir[1])
    t_roof = m.texture("roof", roof)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_roof, bottom=t_roof)
    m.cube((1, 16, 1), (15, 17.5, 15), (t_roof, [0, 0, 14, 2]))
    m.cube((4, 17.5, 4), (12, 19, 12), (t_roof, [0, 0, 8, 2]))
    m.cube((7, 19, 7), (9, 22, 9), (t_roof, [0, 0, 2, 3]))
    return m


def floor_sigil():
    """The Floor Sigil (vanilla: chiseled tuff): a block of grey stone whose top carries a five-pointed sigil in violet
    that slowly turns (animated) - the stone that projects the larger sigil onto the floor round it."""
    m = Model("floor_sigil")
    ch, vi, st = RAMPS["chalk"], RAMPS["violet"], RAMPS["boundsteel"]
    side = bricks(st, 101, row_h=8, brick_w=8, tones=(2, 3))
    put(side, [(x, 7) for x in range(16)], vi[2])
    frames = []
    for f in range(4):
        top = rim(slab_top(st, 103, tone=2), st[4], st[1])
        put(top, circle_pts(7.5, 7.5, 6.4), vi[3])
        a0 = -math.pi / 2 + f * math.pi / 10
        pts = [(7.5 + 5.4 * math.cos(a0 + k * 4 * math.pi / 5), 7.5 + 5.4 * math.sin(a0 + k * 4 * math.pi / 5)) for k in range(6)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for t in range(13):
                put(top, [(math.floor(x0 + (x1 - x0) * t / 12), math.floor(y0 + (y1 - y0) * t / 12))], vi[4])
        put(top, [(7, 7), (8, 8)], vi[5])
        frames.append(top)
    t_side, t_top = m.texture("side", side), m.texture("top", frames)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    return m


G2 = [("Arcane Pedestal", arcane_pedestal), ("Brood Egg", brood_egg), ("Trophy Board", trophy_board),
      ("Chiming Tile", chiming_tile)] + \
     [(f"Bound Glyph v{v}", (lambda v=v: tier_glyph("bound_glyph", RAMPS["violet"], RAMPS["boundsteel"], RAMPS["spirit"], v)))
      for v in range(4)] + \
     [("Bound Altar", bound_altar), ("Phantom Roost", phantom_roost), ("Frenzy Idol", frenzy_idol),
      ("Servitor Shrine", servitor_shrine), ("Floor Sigil", floor_sigil)]


G1 = [("Initiate's Altar", initiate_altar), ("Offering Bowl", offering_bowl), ("Chalk Glyph", chalk_glyph),
      ("Chalk Glyph v1", lambda: chalk_glyph(1)), ("Chalk Glyph v2", lambda: chalk_glyph(2)),
      ("Chalk Glyph v3", lambda: chalk_glyph(3)), ("Arcane Altar", arcane_altar)]
GROUPS = {"g1": G1, "g2": G2}


def save(model):
    d = os.path.join(OUT, model.key)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for name, tex in model.textures.items():
        if isinstance(tex, list):
            for i, fr in enumerate(tex):
                fr.save(os.path.join(d, f"{name}_{i}.png"))
        else:
            tex.save(os.path.join(d, f"{name}.png"))
    with open(os.path.join(d, "model.json"), "w", encoding="utf-8") as f:
        json.dump(model.to_json(), f, indent=2)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "g1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    suffix = "" if version == "final" else "-" + version
    models = []
    for name, make in GROUPS[which]:
        m = make()
        save(m)
        models.append((name, m))
    print(review(models, os.path.join(OUT, f"review-{which}{suffix}.png"), frames=4, s=5))
