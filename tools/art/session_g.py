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
from palettes import RAMPS, hexes  # noqa: E402
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
    """The Brood Egg (vanilla: sniffer egg, 14x16x12 - the skin encloses it): a great egg sac of spider silk, wider
    than its foot, bulging round its middle and rising to a rounded crown above the block; wound with bands of thread,
    dark eggs pressing against it from inside, crimson veins pulsing through it (animated), a strand at its tip."""
    m = Model("brood_egg")
    bone, cr, ink = RAMPS["bone"], RAMPS["crimson"], RAMPS["ink"]
    frames = []
    for f in range(4):
        silk = blank()
        for y in range(16):
            for x in range(16):
                band = (x + y) % 5 == 0          # wound thread
                silk.putpixel((x, y), bone[2] if band else bone[4] if y < 5 else bone[3])
        for (cx, cy) in ((3, 6), (10, 4), (7, 10), (12, 12)):   # eggs pressing from inside
            put(silk, [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)], ink[3])
            put(silk, [(cx, cy)], ink[4])
        glow = cr[[2, 3, 4, 3][f]]
        put(silk, [(1, 2), (2, 3), (2, 4), (3, 6), (4, 7), (5, 8), (5, 9), (6, 11), (13, 2), (13, 3), (12, 5), (12, 6),
                   (13, 8), (14, 9)], glow)
        frames.append(silk)
    t = m.texture("silk", frames)
    top = m.texture("top", rim(fill(bone, 4), bone[5], bone[3]))
    # (y0, y1, half-width): the egg's layers from the foot up; every layer up to y16 encloses the sniffer egg
    layers = ((0, 2, 7.2), (2, 5, 7.8), (5, 11, 8.3), (11, 14, 7.8), (14, 16, 7.2), (16, 18, 6.0), (18, 20, 4.6),
              (20, 21.5, 3.0), (21.5, 22.5, 1.6))
    for i, (y0, y1, r) in enumerate(layers):
        v0 = (i * 3) % 12
        m.cube((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), (t, [0, v0, 16, v0 + min(4, y1 - y0)]), top=top, bottom=top)
    m.box((7.5, 22.5, 7.5), (8.5, 25, 8.5), {d: (t, [0, 0, 1, 3]) for d in ("north", "south", "west", "east")})
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


def tier_glyph(key, chalk_ramp, base_ramp, glow_ramp, variant, glow=False):
    """A circle glyph tile over a carpet: dark slate, a rune drawn in the tier's chalk, dust, a faint glow in the rune's
    heart. glow: the rune also burns with its own light - a second, emissive layer over the tile (light_emission 15, so
    it shines in the dark) with a soft halo round the strokes, pulsing (animated)."""
    m = Model(key + ("" if variant == 0 else f"_v{variant}"))
    rnd = random.Random(170 + variant)
    top = slab_top(base_ramp, 160 + variant, tone=2)
    for _ in range(18):
        top.putpixel((rnd.randrange(16), rnd.randrange(16)), base_ramp[3])
    rune = GLYPH_RUNES[(variant + 1) % 4]
    strokes = [(4 + x, 4 + y) for y, row in enumerate(rune) for x, c in enumerate(row) if c == "#"]
    for (x, y) in strokes:
        top.putpixel((x, y), chalk_ramp[4] if (x + y) % 4 else chalk_ramp[3])
    put(top, [(7, 7), (8, 8)], glow_ramp[4])
    side = fill(base_ramp, 1)
    t_top, t_side = m.texture("top", top), m.texture("side", side)
    m.box((0, 0, 0), (16, 1.2, 16), {"up": t_top, "north": (t_side, [0, 0, 16, 1]), "south": (t_side, [0, 0, 16, 1]),
                                      "west": (t_side, [0, 0, 16, 1]), "east": (t_side, [0, 0, 16, 1]), "down": t_top})
    if glow:
        halo = {(x + dx, y + dy) for (x, y) in strokes for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(strokes)
        frames = []
        for f in range(8):
            layer = blank()
            a = [110, 140, 170, 200, 220, 200, 170, 140][f]
            for (x, y) in halo:
                if 0 <= x < 16 and 0 <= y < 16:
                    layer.putpixel((x, y), glow_ramp[3][:3] + (a,))
            for (x, y) in strokes:
                layer.putpixel((x, y), glow_ramp[5] if (x + y + f) % 4 == 0 else glow_ramp[4])
            frames.append(layer)
        t_glow = m.texture("glow", frames)
        m.box((0, 1.3, 0), (16, 1.3, 16), {"up": t_glow}, shade=False, light=15)
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
    """The Phantom Roost (vanilla: bone block): a little tower of dark slate where phantoms sleep - silver-capped
    corners, and on each side an arched roosting hole in the dark of which a phantom's pale green eyes glow and now and
    then blink (animated; the eyes have their own light). On top a silver perch bar on two posts, rags of dusk membrane
    hanging from it."""
    m = Model("phantom_roost")
    st, ir, du, ink, emd = RAMPS["boundsteel"], RAMPS["iron"], RAMPS["dusk"], RAMPS["ink"], RAMPS["emerald"]
    side = bricks(st, 71, row_h=4, brick_w=8, tones=(1, 2, 2))
    arch = set()
    for y in range(4, 15):
        for x in range(4, 12):
            if y == 4 and x in (4, 5, 10, 11) or y == 5 and x in (4, 11):
                continue
            arch.add((x, y))
    for (x, y) in arch:
        side.putpixel((x, y), ink[0] if y > 6 else ink[1])
    put(side, [(3, y) for y in range(6, 15)] + [(x, 3) for x in range(6, 10)] + [(4, 5), (5, 4), (11, 5), (10, 4)], st[4])
    put(side, [(12, y) for y in range(6, 15)], st[1])
    put(side, [(x, 15) for x in range(3, 13)], st[3])   # the sill
    for x in range(16):
        side.putpixel((x, 0), ir[4])
    t_side = m.texture("side", side)
    # the eyes: their own emissive layer just outside each face
    blink = [0] * 12 + [1, 2, 1, 0]
    eyes = []
    for f, b in enumerate(blink):
        layer = blank()
        if b < 2:
            for ex in (5, 9):
                pts = [(ex, 9), (ex + 1, 9)] if b == 0 else []
                pts += [(ex, 10), (ex + 1, 10)]
                put(layer, pts, emd[5] if b == 0 else emd[4])
                put(layer, [(ex + 1, 10)], emd[4])
        eyes.append(layer)
    t_eyes = m.texture("eyes", eyes)
    top = rim(slab_top(st, 73, tone=2), ir[4], st[1])
    t_top = m.texture("top", top)
    t_silver = m.texture("silver", rim(fill(ir, 3), ir[5], ir[1]))
    rag = blank()
    for y in range(16):
        for x in range(16):
            if y < 12 - (x * 7 % 5):   # ragged hem
                rag.putpixel((x, y), du[2] if (x + y) % 5 else du[1])
    t_rag = m.texture("rag", rag)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_top)
    for (x, z) in ((-0.3, -0.3), (14.3, -0.3), (-0.3, 14.3), (14.3, 14.3)):   # silver corner caps
        m.cube((x, 14, z), (x + 2, 16.5, z + 2), (t_silver, [0, 0, 2, 2]), top=(t_silver, [0, 0, 2, 2]))
    m.box((0, 0, -0.05), (16, 16, -0.05), {"north": t_eyes}, shade=False, light=15)
    m.box((0, 0, 16.05), (16, 16, 16.05), {"south": t_eyes}, shade=False, light=15)
    m.box((-0.05, 0, 0), (-0.05, 16, 16), {"west": t_eyes}, shade=False, light=15)
    m.box((16.05, 0, 0), (16.05, 16, 16), {"east": t_eyes}, shade=False, light=15)
    for x in (3, 12):   # the perch: two posts and a bar
        m.cube((x, 16, 7), (x + 1, 21, 8.5), (t_silver, [0, 0, 1, 5]), top=(t_silver, [0, 0, 1, 1]))
    m.cube((2, 21, 6.8), (14, 22.2, 8.7), (t_silver, [0, 0, 12, 1]), top=(t_silver, [0, 0, 12, 2]))
    for (x0, x1, drop) in ((4.5, 7, 4.5), (8, 10.5, 3)):   # rags of membrane hanging from the bar
        m.box((x0, 21 - drop, 7.75), (x1, 21, 7.75), {"north": (t_rag, [0, 0, x1 - x0, drop]), "south": (t_rag, [0, 0, x1 - x0, drop])},
              shade=False)
    return m


RAM_FACE = [  # B brow, E eye glow, e eye edge, S muzzle, s muzzle shade, h muzzle highlight, N nostril, G sun, g rays
    ".......gg.......",
    "......gGGg......",
    ".......GG.......",
    ".BBB...gg...BBB.",
    "..BBBBSSSSBBBB..",
    "..eEEeShhSeEEe..",
    "...eEeShSSeEe...",
    "......ShSS......",
    "......ShSs......",
    ".....SSSSss.....",
    "....SShSSSss....",
    "....SSSSSSss....",
    "....SNNSSNNs....",
    ".....sssssss....",
    "................",
    "................",
]


def frenzy_idol():
    """The Frenzy Idol (vanilla: chiseled resin bricks): a ram guardian of the Bound tier - benevolent but stern.
    Dusk-violet stone warmed toward rose and orange; a long silver ram's muzzle down its face with flared nostrils; a
    heavy brow bearing down toward the centre over calm almond eyes glowing ember orange; an ember sun on its brow;
    silver horns ridged like a ram's, spiralling down each side of its head. Animated: the eyes and the sun breathe
    light."""
    m = Model("frenzy_idol")
    du, em, st, vi = RAMPS["dusk"], RAMPS["ember"], RAMPS["boundsteel"], RAMPS["violet"]
    stone = [em[0], du[0], du[1], st[2], du[2]]   # dark violet slate, its seams and shadows ember-brown
    frames = []
    for f in range(4):
        face = bricks(stone, 81, row_h=8, brick_w=16, tones=(2, 3))
        cols = {"B": du[0], "E": [em[3], em[4], em[5], em[4]][f], "e": em[2], "S": st[4], "s": st[3], "h": du[5],
                "N": du[0], "G": [em[3], em[4], em[5], em[4]][f], "g": em[2]}
        for y, row in enumerate(RAM_FACE):
            for x, c in enumerate(row):
                if c in cols:
                    face.putpixel((x, y), cols[c])
        frames.append(face)
    plain = bricks(stone, 83, row_h=8, brick_w=16, tones=(2, 3))
    t_face, t_plain = m.texture("face", frames), m.texture("plain", plain)
    top = rim(slab_top(stone, 85, tone=3), stone[4], stone[0])
    put(top, circle_pts(7.5, 7.5, 3.2), em[2])
    put(top, [(7, 7), (8, 7), (7, 8), (8, 8)], em[4])
    t_top = m.texture("top", top)
    horn = blank()
    for y in range(16):
        for x in range(16):
            horn.putpixel((x, y), st[2] if (x + y) % 3 == 0 else st[3])   # ridged silver
    t_horn = m.texture("horn", rim(horn, st[4], st[1]))
    m.box((0, 0, 0), (16, 16, 16), {"north": t_face, "south": t_face, "west": t_plain, "east": t_plain,
                                     "up": t_top, "down": t_plain})
    for side in (-1, 1):   # a spiral on the side of the head: up from the crown, back, down, and forward to the tip
        x0, x1 = (-2.5, 0.5) if side < 0 else (15.5, 18.5)
        for (y0, z0, y1, z1) in ((14, 5, 18, 9), (15, 9, 18, 13), (11, 11, 15, 14), (8, 8, 11, 13), (8, 4.5, 10.5, 8)):
            m.cube((x0, y0, z0), (x1, y1, z1), (t_horn, [0, 0, 3, 3]))
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


# ================================================================== G3: tier-2 blocks (Abyssal: deep teal, prismarine,
# iron and gold fittings, sea glow)

def plate(ramp, seed, tone=2, rivets=None):
    """A riveted metal plate: brushed rows, a lit top-left bevel, rivets at the corners."""
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        for x in range(16):
            t = tone + (1 if (y * 7 + rnd.randrange(3)) % 9 == 0 else 0)
            img.putpixel((x, y), ramp[t])
    rim(img, ramp[tone + 2], ramp[max(0, tone - 1)])
    for (x, y) in rivets or ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(img, [(x, y)], ramp[min(len(ramp) - 1, tone + 3)])
        put(img, [(x + 1, y + 1)], ramp[max(0, tone - 1)])
    return img


def abyss_bricks(seed, row_h=4, brick_w=8):
    """Prismarine-like masonry in the abyss ramp: teal bricks with a cold, dark mortar."""
    return bricks(RAMPS["abyss"], seed, row_h=row_h, brick_w=brick_w, tones=(2, 3, 3, 4))


def turned(model):
    """The model turned half a turn (for previewing a block's front, which faces north, in the iso renderer)."""
    m = Model(model.key)
    m.textures = model.textures
    swap = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "up", "down": "down"}
    for e in model.elements:
        (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
        m.elements.append({"from": [16 - x1, y0, 16 - z1], "to": [16 - x0, y1, 16 - z0], "shade": e["shade"],
                           "faces": {swap[d]: f for d, f in e["faces"].items()}})
    return m


def occult_forge():
    """The Occult Forge (vanilla: blast furnace; its front faces whoever placed it): a squat furnace of abyss stone
    bound in riveted iron, gold corner fittings; its front an arched furnace mouth roaring with ember fire (animated);
    sea-glow runes on its iron flanks; on top an iron grate glowing from below and a short stone chimney."""
    m = Model("occult_forge")
    ab, ir, gd, em, sg = RAMPS["abyss"], RAMPS["iron"], RAMPS["gold"], RAMPS["ember"], RAMPS["seaglow"]
    mouths, flanks = [], []
    for f in range(4):
        front = abyss_bricks(201)
        for y in range(0, 4):   # an iron lintel band
            for x in range(16):
                front.putpixel((x, y), ir[2] if y else ir[4])
        for (x, y) in ((2, 1), (13, 1)):
            put(front, [(x, y)], ir[5])
        # the arched mouth: x 3..12, y 6..14, rounded top
        for y in range(6, 15):
            for x in range(3, 13):
                if y == 6 and x in (3, 4, 11, 12) or y == 7 and x in (3, 12):
                    continue
                front.putpixel((x, y), ab[0])
        rnd = random.Random(210 + f)
        for x in range(4, 12):   # flames: tall in the middle, licking up and down by frame
            h = 3 + (2 if 6 <= x <= 9 else 0) + rnd.randrange(3)
            for k in range(h):
                y = 14 - k
                c = em[5] if k == 0 else em[4] if k < 2 else em[3] if k < h - 1 else em[2]
                front.putpixel((x, y), c)
        for y in range(6, 15):   # the iron arch frame
            for x in (2, 13):
                front.putpixel((x, y), ir[3] if x == 2 else ir[1])
        put(front, [(x, 5) for x in range(4, 12)] + [(3, 6), (12, 6)], ir[3])
        put(front, [(7, 4), (8, 4)], gd[4])   # gold keystone
        put(front, [(x, 15) for x in range(2, 14)], ir[1])
        mouths.append(front)
        side = plate(ir, 220, tone=1)
        rune = [(7, 3), (8, 3), (7, 4), (8, 4), (5, 5), (10, 5), (5, 6), (10, 6), (6, 7), (9, 7), (7, 8), (8, 8),
                (7, 9), (8, 9), (7, 10), (8, 10), (5, 9), (10, 9)]   # a trident-like Abyssal rune
        put(side, rune, sg[[2, 3, 4, 3][f]])
        put(side, [(7, 6), (8, 6)], sg[[3, 4, 5, 4][f]])
        put(side, [(x, 12) for x in range(16)] + [(x, 13) for x in range(16)], ab[2])
        put(side, [(x, 14) for x in range(16)] + [(x, 15) for x in range(16)], ab[1])
        flanks.append(side)
    t_front, t_side = m.texture("front", mouths), m.texture("side", flanks)
    grate = []
    for f in range(4):
        top = rim(fill(ir, 1), ir[3], ir[0])
        for y in range(3, 13):
            for x in range(3, 13):
                glow = em[[2, 3, 3, 2][(x + y + f) % 4]]
                top.putpixel((x, y), ir[2] if x % 3 == 0 else glow)
        grate.append(top)
    t_top = m.texture("top", grate)
    t_bottom = m.texture("bottom", fill(ab, 1))
    corner = rim(fill(gd, 3), gd[5], gd[1])
    t_corner = m.texture("corner", corner)
    chimney = bricks(ab, 230, row_h=3, brick_w=4, tones=(1, 2, 2))
    t_chim = m.texture("chimney", chimney)
    chim_top = rim(fill(ab, 0), ab[3], ab[1])
    put(chim_top, [(x, y) for x in range(5, 11) for y in range(5, 11)], em[2])
    t_chim_top = m.texture("chimney_top", chim_top)
    m.box((0, 0, 0), (16, 16, 16), {"north": t_front, "south": t_side, "west": t_side, "east": t_side,
                                     "up": t_top, "down": t_bottom})
    for (x, z) in ((-0.3, -0.3), (14.3, -0.3), (-0.3, 14.3), (14.3, 14.3)):   # gold corner fittings top and bottom
        for y in (0, 13):
            m.cube((x, y, z), (x + 2, y + 3, z + 2), (t_corner, [0, 0, 2, 3]), top=(t_corner, [0, 0, 2, 2]))
    m.cube((9, 16, 9), (14, 21, 14), (t_chim, [0, 0, 5, 5]), top=(t_chim_top, [4, 4, 12, 12]))
    return m


def soul_condenser():
    """The Soul Condenser (vanilla: respawn anchor): an iron cage with gold-capped corner posts, smoky glass panes on
    every side behind which a captured soul - a glowing wisp trailing a tail - circles (animated); a condenser coil on
    top round a glowing core."""
    m = Model("soul_condenser")
    ab, ir, gd, sg, gl = RAMPS["abyss"], RAMPS["iron"], RAMPS["gold"], RAMPS["seaglow"], RAMPS["glass"]
    panes = []
    for f in range(8):
        side = blank()
        for y in range(16):
            for x in range(16):
                side.putpixel((x, y), ab[2] if (x + y) % 7 else ab[3])   # smoky glass, lit from within
        a = f * math.pi / 4
        hx, hy = int(7.5 + 3.6 * math.cos(a)), int(7.5 + 2.8 * math.sin(a))
        put(side, [(hx + dx, hy + dy) for dx in range(-1, 3) for dy in range(-1, 3)], sg[2])   # the wisp's halo
        for k in range(7, -1, -1):   # the wisp: its tail fades behind it round the circle
            a = (f - k * 0.35) * math.pi / 4
            x, y = 7.5 + 3.6 * math.cos(a), 7.5 + 2.8 * math.sin(a)
            c = sg[5] if k == 0 else sg[4] if k < 2 else sg[3] if k < 4 else sg[2]
            pts = [(int(x), int(y))]
            if k < 2:
                pts += [(int(x) + 1, int(y)), (int(x), int(y) + 1), (int(x) + 1, int(y) + 1)]
            put(side, pts, c)
        for i in range(16):   # the iron frame round the pane
            for (x, y) in ((i, 0), (i, 1), (i, 14), (i, 15), (0, i), (1, i), (14, i), (15, i)):
                side.putpixel((x, y), ir[3] if (x < 1 or y < 1) else ir[2] if (x < 2 or y < 2) else ir[1])
        put(side, [(2, 2), (3, 2), (2, 3)], gl[4])   # a glint on the glass
        panes.append(side)
    t_side = m.texture("side", panes)
    tops = []
    for f in range(8):
        top = rim(plate(ir, 240, tone=1, rivets=()), ir[3], ir[0])
        put(top, circle_pts(7.5, 7.5, 5.2), gd[3])
        put(top, circle_pts(7.5, 7.5, 3.6), ir[4])
        put(top, [(x, y) for x in range(6, 10) for y in range(6, 10)], sg[[3, 4, 5, 4, 3, 4, 5, 4][f]])
        tops.append(top)
    t_top = m.texture("top", tops)
    post = rim(fill(ir, 2), ir[4], ir[0])
    t_post = m.texture("post", post)
    cap = rim(fill(gd, 3), gd[5], gd[1])
    t_cap = m.texture("cap", cap)
    coil = blank()
    for y in range(16):
        for x in range(16):
            coil.putpixel((x, y), gd[4] if y % 2 == 0 else gd[2])
    t_coil = m.texture("coil", coil)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_post)
    for (x, z) in ((-0.4, -0.4), (13.4, -0.4), (-0.4, 13.4), (13.4, 13.4)):
        m.cube((x, 0, z), (x + 3, 16, z + 3), (t_post, [0, 0, 3, 16]), top=(t_post, [0, 0, 3, 3]))
        m.cube((x - 0.3, 16, z - 0.3), (x + 3.3, 17.5, z + 3.3), (t_cap, [0, 0, 3, 2]), top=(t_cap, [0, 0, 3, 3]))
    m.cube((4.5, 16, 4.5), (11.5, 18, 11.5), (t_coil, [0, 0, 7, 2]), top=(t_top, [4.5, 4.5, 11.5, 11.5]))
    return m


def abyssal_glyph(variant=0):
    return tier_glyph("abyssal_glyph", RAMPS["seaglow"], RAMPS["abyss"], RAMPS["seaglow"], variant)


def abyssal_altar():
    """The Abyssal Altar (vanilla: prismarine bricks; the Bound Altar upgrades into it): deep-teal masonry banded in
    gold at top and foot, a sea-glow tide rolling round its middle (animated), prismarine crystal spires at its four
    corners, and on top the Abyssal sigil - an eye in a ring - its pupil glowing and its gaze drifting."""
    m = Model("abyssal_altar")
    ab, gd, sg, ir = RAMPS["abyss"], RAMPS["gold"], RAMPS["seaglow"], RAMPS["iron"]
    sides, tops = [], []
    for f in range(4):
        side = abyss_bricks(251, row_h=6, brick_w=8)
        for x in range(16):   # the tide band: a wave that rolls along the side
            crest = 7 + (1 if (x + f * 2) % 8 < 4 else 0)
            for y in range(6, 11):
                side.putpixel((x, y), ab[0])
            side.putpixel((x, 6), gd[2]); side.putpixel((x, 10), gd[2])
            side.putpixel((x, crest), sg[5]); side.putpixel((x, crest + 1), sg[3])
            side.putpixel((x, 0), gd[4]); side.putpixel((x, 1), gd[2]); side.putpixel((x, 14), gd[3]); side.putpixel((x, 15), gd[1])
        sides.append(side)
        top = rim(slab_top(ab, 253, tone=2), gd[4], gd[2])
        put(top, circle_pts(7.5, 7.5, 6.0), gd[3])
        eye = [(4, 7), (5, 6), (6, 5), (7, 5), (8, 5), (9, 5), (10, 6), (11, 7), (4, 8), (5, 9), (6, 10), (7, 10), (8, 10),
               (9, 10), (10, 9), (11, 8)]
        put(top, eye, sg[3])
        put(top, [(x, y) for x in range(5, 11) for y in range(6, 10) if (x, y) not in eye], ab[0])
        px = 6 + [1, 1, 2, 1][f]   # the pupil drifts
        put(top, [(px, 7), (px + 1, 7), (px, 8), (px + 1, 8)], sg[[4, 5, 5, 4][f]])
        tops.append(top)
    t_side, t_top = m.texture("side", sides), m.texture("top", tops)
    crystal = blank()
    for y in range(16):
        for x in range(16):
            crystal.putpixel((x, y), sg[4] if (x + y) % 4 == 0 else sg[2] if x % 2 else sg[3])
    t_crys = m.texture("crystal", crystal)
    t_base = m.texture("base", rim(fill(gd, 2), gd[4], gd[1]))
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    for (x, z) in ((0.5, 0.5), (13, 0.5), (0.5, 13), (13, 13)):
        m.cube((x, 16, z), (x + 2.5, 17, z + 2.5), (t_base, [0, 0, 3, 1]), top=(t_base, [0, 0, 3, 3]))
        m.cube((x + 0.5, 17, z + 0.5), (x + 2, 20, z + 2), (t_crys, [0, 0, 2, 3]), top=(t_crys, [0, 0, 2, 2]))
        m.cube((x + 0.9, 20, z + 0.9), (x + 1.6, 21.5, z + 1.6), (t_crys, [4, 0, 5, 2]), top=(t_crys, [4, 4, 5, 5]))
    return m


GUARDIAN_EYE_Y = 22.4   # the eye's centre above the column, in px (the plugin puts its display at block y + 1.4)


def guardian_column():
    """The Guardian Eye's column (vanilla: observer): a fluted column of teal guardian stone - a stepped plinth, a
    capital ringed in amber spikes - and on top a gold cradle of four claws in which its eye sits. The eye itself is
    a separate display that turns to look at what it shoots (guardian_eye_orb)."""
    m = Model("guardian_eye")
    ab, am, gd, sg = RAMPS["abyss"], RAMPS["amber"], RAMPS["gold"], RAMPS["seaglow"]
    shaft = blank()
    for y in range(16):
        for x in range(16):
            flute = x % 4
            shaft.putpixel((x, y), ab[4] if flute == 0 else ab[3] if flute == 1 else ab[2] if flute == 2 else ab[1])
    put(shaft, [(x, y) for x in range(16) for y in (7, 8)], sg[2])   # a sea-glow ring round the shaft
    t_shaft = m.texture("shaft", shaft)
    stone = rim(fill(ab, 3), ab[5], ab[1])
    put(stone, [(x, 8) for x in range(16)], ab[2])
    t_stone = m.texture("stone", stone)
    t_top = m.texture("top", rim(slab_top(ab, 311, tone=3), ab[5], ab[1]))
    t_spike = m.texture("spike", rim(fill(am, 3), am[5], am[1]))
    t_gold = m.texture("gold", rim(fill(gd, 3), gd[5], gd[1]))
    m.cube((0, 3, 0), (16, 13, 16), (t_shaft, [0, 3, 16, 13]))
    m.cube((-0.5, 0, -0.5), (16.5, 3, 16.5), (t_stone, [0, 5, 16, 8]), top=t_top, bottom=t_top)       # plinth
    m.cube((-0.5, 13, -0.5), (16.5, 16, 16.5), (t_stone, [0, 5, 16, 8]), top=t_top, bottom=t_top)     # capital
    for (x, z) in ((-1.5, -1.5), (15.5, -1.5), (-1.5, 15.5), (15.5, 15.5)):
        m.cube((x, 13.5, z), (x + 2, 15.5, z + 2), (t_spike, [0, 0, 2, 2]))
    m.cube((5, 16, 5), (11, 17.5, 11), (t_gold, [0, 0, 6, 2]), top=(t_gold, [0, 0, 6, 6]))           # the cradle
    for (x, z) in ((4, 4), (11, 4), (4, 11), (11, 11)):
        m.cube((x, 17, z), (x + 1, 20.5, z + 1), (t_gold, [0, 0, 1, 3]), top=(t_gold, [0, 0, 1, 1]))
    return m


def guardian_orb(m=None, cy=8.0, frame_count=8):
    """The Guardian Eye's eye: a ball of pale guardian hide, an amber-ringed iris with a slit pupil on its north face
    (its front - the plugin turns it toward its target), glowing (light_emission). Drawn into `m` at height cy (the
    inventory model) or as its own model centred in its block."""
    own = m is None
    m = m or Model("guardian_eye_orb")
    ab, am, bone, sg = RAMPS["abyss"], RAMPS["amber"], RAMPS["bone"], RAMPS["seaglow"]
    hide = blank()
    for y in range(16):
        for x in range(16):
            hide.putpixel((x, y), bone[4] if (x * 3 + y) % 7 else bone[3])
    put(hide, [(2, 5), (3, 6), (4, 6), (12, 9), (11, 10)], RAMPS["crimson"][3])   # a few veins
    t_hide = m.texture("orb_hide", hide)
    irises = []
    for f in range(frame_count):
        iris = fill(bone, 4)
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                if d < 6.5:
                    iris.putpixel((x, y), am[2] if d > 5.4 else sg[3] if d > 3.6 else sg[4])
        w = [2, 2, 2, 1, 1, 2, 2, 2][f % 8]   # the slit narrows now and then
        for y in range(3, 13):
            for x in range(8 - w // 2 - (w % 2), 8 + w // 2):
                iris.putpixel((x, y), ab[0])
        put(iris, [(5, 4), (6, 4), (5, 5)], (255, 255, 255, 255))   # a catchlight
        irises.append(iris)
    t_iris = m.texture("orb_iris", irises)
    c, r = 8.0, 4.0
    def b(x0, y0, z0, x1, y1, z1):
        return (c + x0, cy + y0, c + z0), (c + x1, cy + y1, c + z1)
    m.box(*b(-r, -2, -2, r, 2, 2), {d: (t_hide, [0, 0, 8, 5]) for d in ("west", "east", "up", "down", "south")})
    m.box(*b(-2, -r, -2, 2, r, 2), {d: (t_hide, [0, 0, 5, 8]) for d in ("west", "east", "up", "down", "south")})
    m.box(*b(-3.2, -3.2, -3.2, 3.2, 3.2, 3.2), {d: (t_hide, [2, 2, 9, 9]) for d in ("west", "east", "up", "down", "south")})
    m.box(*b(-2.4, -2.4, -r, 2.4, 2.4, r), {"north": (t_iris, [3, 3, 13, 13]), "south": (t_hide, [0, 0, 5, 5]),
                                           "west": (t_hide, [0, 0, 8, 5]), "east": (t_hide, [0, 0, 8, 5]),
                                           "up": (t_hide, [0, 0, 5, 8]), "down": (t_hide, [0, 0, 5, 8])}, light=12)
    if own:
        m.part = True
    return m


def guardian_eye_inventory():
    """The Guardian Eye as the inventory shows it: the column with its eye in the cradle, looking out."""
    m = guardian_column()
    m.key = "guardian_eye_inventory"
    m.part = True
    guardian_orb(m, cy=GUARDIAN_EYE_Y)
    m.display = {"gui": {"rotation": [30, 225, 0], "translation": [0, -2.5, 0], "scale": [0.5, 0.5, 0.5]}}
    return m


def pearl_bed():
    """The Pearl Bed (vanilla: tube coral block): a block of sea-floor rock crusted with coral along its top edge, and
    on top a great scallop - a ribbed, blush-pink fan standing open behind its lower valve - round a big glowing pearl
    that shimmers (animated)."""
    m = Model("pearl_bed")
    ab, sg, bl = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["blossom"]
    rnd = random.Random(271)
    side = blank()
    for y in range(16):
        for x in range(16):
            side.putpixel((x, y), ab[2] if (x * 5 + y * 3) % 7 else ab[1])
    for x in range(16):   # a crust of coral along the top edge, hanging down unevenly
        depth = 2 + rnd.randrange(3)
        for y in range(depth):
            side.putpixel((x, y), bl[3] if y == 0 else bl[2] if y < depth - 1 else bl[1])
    for _ in range(5):
        x, y = rnd.randrange(1, 15), rnd.randrange(6, 15)
        put(side, [(x, y)], bl[2]); put(side, [(x, y - 1)], bl[3])
    t_side = m.texture("side", side)
    top = rim(slab_top(ab, 273, tone=2), bl[3], ab[1])
    t_top = m.texture("top", top)
    shell = blank()
    for y in range(16):
        for x in range(16):
            rib = round((x - 7.5) * 16 / (16 + (15 - y) * 1.2)) % 2 == 0   # ribs fanning out from the hinge
            shell.putpixel((x, y), (bl[3] if rib else bl[2]) if y > 9 else (bl[4] if rib else bl[3]))
    t_shell = m.texture("shell", shell)
    pearls = []
    for f in range(4):
        pearl = fill(sg, 4)
        put(pearl, [(x, y) for x in range(16) for y in range(16) if x < 8 and y < 8], (255, 252, 246, 255))
        put(pearl, [(x, y) for x in range(16) for y in range(16) if x > 10 or y > 10], sg[3])
        put(pearl, [(x, y) for x in range(16) for y in range(16) if (x + y + f * 4) % 16 < 2], (255, 225, 240, 255))
        pearls.append(pearl)
    t_pearl = m.texture("pearl", pearls)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    m.cube((3, 16, 3), (13, 17.5, 12), (t_shell, [0, 0, 10, 2]), top=(t_shell, [3, 3, 13, 12]))   # the lower valve
    for i, (x0, x1, y0, y1) in enumerate(((6, 10, 17.5, 19), (4.5, 11.5, 19, 21), (3, 13, 21, 23.5), (4, 12, 23.5, 25))):
        m.cube((x0, y0, 3 + i * 0.2), (x1, y1, 4.5 + i * 0.2), (t_shell, [x0, 25 - y1 - 9, x1, 25 - y0 - 9]))   # the fan, open
    m.box((6, 17.5, 6.5), (10, 21.5, 10.5), {d: (t_pearl, [4, 4, 12, 12]) for d in FACES_ALL}, shade=False)
    return m


def ember_brazier():
    """The Ember Brazier (vanilla: magma block): a squat black-iron stove - riveted plates, a barred grille on each
    side through which the coals glow (animated), a gold lip round the top - and a deep bed of coals in its top, dark
    lumps with fire breathing in the cracks between them (animated)."""
    m = Model("ember_brazier")
    ir, gd, em, ash = RAMPS["iron"], RAMPS["gold"], RAMPS["ember"], RAMPS["ash"]
    sides, tops = [], []
    for f in range(4):
        side = plate(ir, 280, tone=1)
        for y in range(5, 12):   # the grille: glow behind bars
            for x in range(3, 13):
                glow = em[[3, 4, 3, 2][(f + (y > 8) + x // 5) % 4]] if y > 6 else em[2]
                side.putpixel((x, y), ir[2] if x % 3 == 0 else glow)
        put(side, [(x, 4) for x in range(2, 14)] + [(x, 12) for x in range(2, 14)] + [(2, y) for y in range(4, 13)]
            + [(13, y) for y in range(4, 13)], ir[3])
        for x in range(16):
            side.putpixel((x, 0), gd[4]); side.putpixel((x, 1), gd[2])
        sides.append(side)
        top = blank()
        rnd = random.Random(281)
        for y in range(16):
            for x in range(16):
                top.putpixel((x, y), em[[2, 3, 4, 3][(x + y + f) % 4]])   # fire in the cracks
        for _ in range(16):   # dark coal lumps over it
            cx, cy = rnd.randrange(0, 15), rnd.randrange(0, 15)
            put(top, [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)], ash[1])
            put(top, [(cx, cy)], ash[3])
            put(top, [(cx + 1, cy + 1)], em[1])
        tops.append(top)
    t_side, t_top = m.texture("side", sides), m.texture("top", tops)
    lip = rim(fill(gd, 3), gd[5], gd[1])
    t_lip = m.texture("lip", lip)
    foot = rim(fill(ir, 1), ir[3], ir[0])
    t_foot = m.texture("foot", foot)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_foot)
    for (frm, to) in (((-0.5, 15, -0.5), (16.5, 17, 1)), ((-0.5, 15, 15), (16.5, 17, 16.5)),
                      ((-0.5, 15, 1), (1, 17, 15)), ((15, 15, 1), (16.5, 17, 15))):   # the raised gold lip
        m.cube(frm, to, (t_lip, [0, 0, 16, 2]), top=(t_lip, [0, 0, 16, 2]))
    for (x, z) in ((-0.5, -0.5), (14, -0.5), (-0.5, 14), (14, 14)):   # iron feet
        m.cube((x, 0, z), (x + 2.5, 2, z + 2.5), (t_foot, [0, 0, 3, 2]))
    return m


def abyssal_lantern():
    """The Abyssal Lantern (vanilla: lantern - light 15, small - so the skin can be smaller than a block; it encloses
    the lantern standing or hanging): a deep-sea lamp 12 wide and 14 tall - dark iron cap and foot rimmed in gold,
    iron corner posts, panes of sea glow brightest at the heart behind which bubbles rise (animated, glowing), and an
    iron ring on top over the lantern's chain."""
    m = Model("abyssal_lantern")
    ir, gd, sg = RAMPS["iron"], RAMPS["gold"], RAMPS["seaglow"]
    panes = []
    for f in range(4):
        side = blank()
        for y in range(16):
            for x in range(16):
                d = abs(x - 7.5) + abs(y - 7.5) * 0.8
                side.putpixel((x, y), sg[4] if d < 3 else sg[3] if d < 6 else sg[2])
        for (bx, phase) in ((4, 0), (8, 6), (11, 11)):   # bubbles rising
            y = 13 - (phase + f * 3) % 11
            put(side, [(bx, y), (bx + 1, y)], sg[5]); put(side, [(bx, y + 1)], sg[1])
        panes.append(side)
    t_side = m.texture("side", panes)
    top = rim(fill(ir, 1), gd[4], gd[1])
    put(top, circle_pts(7.5, 7.5, 3.5), ir[3])
    t_top = m.texture("top", top)
    band = blank()
    for y in range(16):
        for x in range(16):
            band.putpixel((x, y), gd[4] if y == 0 else ir[1] if y < 3 else ir[0])
    t_band = m.texture("band", band)
    post = rim(fill(ir, 1), ir[3], ir[0])
    t_post = m.texture("post", post)
    ring = rim(fill(ir, 2), ir[4], ir[0])
    t_ring = m.texture("ring", ring)
    m.box((2.5, 2, 2.5), (13.5, 12, 13.5), {d: (t_side, [2.5, 3, 13.5, 13]) for d in ("north", "south", "west", "east")}, light=15)
    m.cube((2, 0, 2), (14, 2, 14), (t_band, [0, 0, 12, 2]), top=t_top, bottom=t_top)       # foot
    m.cube((2, 12, 2), (14, 14, 14), (t_band, [0, 0, 12, 2]), top=t_top, bottom=t_top)     # cap
    for (x, z) in ((1.6, 1.6), (12.9, 1.6), (1.6, 12.9), (12.9, 12.9)):
        m.cube((x, 0, z), (x + 1.5, 14, z + 1.5), (t_post, [0, 0, 2, 14]), top=(t_post, [0, 0, 2, 2]))
    m.cube((6, 14, 6), (10, 15, 10), (t_ring, [0, 0, 4, 1]), top=(t_ring, [0, 0, 4, 4]))
    m.cube((6, 15, 7.4), (7, 17, 8.6), (t_ring, [0, 0, 1, 2]))
    m.cube((9, 15, 7.4), (10, 17, 8.6), (t_ring, [0, 0, 1, 2]))
    m.cube((6.5, 17, 7.4), (9.5, 18, 8.6), (t_ring, [0, 0, 3, 1]))
    return m


CORALS = {   # the Tidal Tile's looks: variant 0 is its own block (tube), the rest by name (BlockSkinService/StepTile)
    "tube":   hexes("#0f1f5a", "#1c3aa0", "#2f5fd8", "#5a8af0", "#9cc0ff"),
    "brain":  hexes("#4a1035", "#8a2258", "#c94a86", "#f08ab4", "#ffc4dc"),
    "bubble": hexes("#30104a", "#5e1f86", "#9a33b8", "#c45ee0", "#e8a6f6"),
    "fire":   hexes("#3c0a0e", "#7a1420", "#b8222c", "#e04848", "#ff9a8a"),
    "horn":   hexes("#4a3606", "#8c6a10", "#c8a020", "#e8cc48", "#fff09a"),
}
CORAL_ORDER = ["tube", "brain", "bubble", "fire", "horn"]


def tidal_tile(variant=0):
    """The Tidal Coral Tile (vanilla: a coral block, cycled by right-click): living coral with a film of sea water
    glinting over its top (animated). Seamless - no frame or edge shading - so a floor of tiles reads as one reef, not
    a grid. One variant per coral; the skin follows the block."""
    coral = CORALS[CORAL_ORDER[variant]]
    m = Model("tidal_tile" + ("" if variant == 0 else f"_v{variant}"))
    sg = RAMPS["seaglow"]

    def reef(seed):
        rnd = random.Random(seed)
        img = blank()
        for y in range(16):
            for x in range(16):
                img.putpixel((x, y), coral[2] if (x + 2 * y) % 5 else coral[1])
        for _ in range(40):   # polyps, wrapping round the edges so tiles join
            x, y = rnd.randrange(16), rnd.randrange(16)
            img.putpixel((x, y), coral[4]); img.putpixel(((x + 1) % 16, y), coral[3]); img.putpixel((x, (y + 1) % 16), coral[1])
        return img

    tops = []
    for f in range(4):
        top = reef(291 + variant)
        for k in range(3):   # glints of the water film drifting across
            gx, gy = (3 + k * 5 + f * 2) % 16, (4 + k * 6 + f) % 16
            put(top, [(gx, gy), ((gx + 1) % 16, gy)], sg[5] if k == 0 else sg[4])
        tops.append(top)
    t_top, t_side = m.texture("top", tops), m.texture("side", reef(295 + variant))
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    return m


def prismatic_netherrack():
    """Prismatic Netherrack (vanilla: netherrack; lit, its fire burns on top): dark nether rock split by crystal-filled
    cracks whose light runs through every colour of the rainbow (animated). Its top stays flat so the fire sits on it."""
    m = Model("prismatic_netherrack")
    cr, ash = RAMPS["crimson"], RAMPS["ash"]
    hues = [hexes("#ff5a5a")[0], hexes("#ffb03a")[0], hexes("#fff05a")[0], hexes("#5aff8a")[0], hexes("#5ad0ff")[0],
            hexes("#8a6aff")[0], hexes("#e05aff")[0], hexes("#ff5aa8")[0]]
    rnd = random.Random(301)
    base = blank()
    for y in range(16):
        for x in range(16):   # netherrack: dark red rock in soft clumps
            clump = ((x // 3) * 5 + (y // 2) * 3 + rnd.randrange(2)) % 5
            base.putpixel((x, y), [cr[1], cr[1], cr[2], ash[2], cr[0]][clump])
    crack = []   # two cracks that branch across the face, edge to edge
    for (x, y, dx) in ((2, 0, 1), (13, 0, -1)):
        while y < 16:
            crack.append((x, y))
            y += 1
            if rnd.random() < 0.45:
                x = max(0, min(15, x + dx * rnd.choice((1, 1, -1))))
                crack.append((x, y - 1))
    frames = []
    for f in range(8):
        img = base.copy()
        for i, (x, y) in enumerate(crack):
            img.putpixel((x, y), hues[(f + i // 4) % len(hues)])
            for (nx, ny) in ((x + 1, y), (x - 1, y)):   # the rock darkens at the crack's lips
                if 0 <= nx < 16 and (nx, ny) not in crack:
                    img.putpixel((nx, ny), cr[0])
        frames.append(img)
    t = m.texture("rock", frames)
    m.cube((0, 0, 0), (16, 16, 16), t)
    return m


FIRE_PALETTES = {   # the Prismatic Netherrack's palettes (DecorationService order): hue (start, span) per frame cycle
    0: ("rainbow", 0.0, 1.0),
    1: ("aurora", 0.30, 0.45),
    2: ("dusk", 0.78, 0.30),
}


def prismatic_fire(palette=0):
    """Prismatic fire (shown by the plugin over a lit Prismatic Netherrack, in place of vanilla fire): tongues of flame
    on four crossed planes like vanilla fire's, white-hot at the root, their colour running through the palette's hues
    as they flicker (16 frames). Glows (light_emission)."""
    name, start, span = FIRE_PALETTES[palette]
    m = Model("prismatic_fire" + ("" if palette == 0 else f"_v{palette}"))
    m.part = True
    import colorsys
    frames = []
    rnd = random.Random(320 + palette)
    phases = [rnd.random() * 6.28 for _ in range(16)]
    for f in range(16):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for x in range(16):
            edge = min(x, 15 - x)
            h = 6 + edge * 0.9 + 3 * math.sin(phases[x] + f * 0.8) + 2 * math.sin(x * 1.7 + f * 0.4)
            h = max(3, min(15, h))
            for k in range(int(h)):
                y = 15 - k
                t = k / h
                hue = (start + span * (((f / 16) + x / 40 + t * 0.15) % 1.0)) % 1.0
                light = 0.92 if t < 0.15 else 0.75 - 0.25 * t
                sat = 0.35 if t < 0.15 else 0.9
                r, g, b = colorsys.hls_to_rgb(hue, light, sat)
                img.putpixel((x, y), (int(r * 255), int(g * 255), int(b * 255), 255 if t < 0.8 else 170))
        frames.append(img)
    t = m.texture("flame", frames)
    both = lambda a, b_: {a: (t, [0, 0, 16, 16]), b_: (t, [16, 0, 0, 16])}   # noqa: E731
    m.box((0, 0, 8), (16, 16, 8), both("north", "south"), shade=False, light=15)
    m.box((8, 0, 0), (8, 16, 16), both("west", "east"), shade=False, light=15)
    m.box((0, 0, 8), (16, 16, 8), both("north", "south"), shade=False, light=15, rotation=("y", 45))
    m.box((8, 0, 0), (8, 16, 16), both("west", "east"), shade=False, light=15, rotation=("y", 45))
    return m


G3 = [("Occult Forge", occult_forge), ("Occult Forge (front)", lambda: turned(occult_forge())),
      ("Soul Condenser", soul_condenser)] + \
     [(f"Abyssal Glyph v{v}", (lambda v=v: abyssal_glyph(v))) for v in range(4)] + \
     [("Abyssal Altar", abyssal_altar), ("Guardian Eye", guardian_column), ("Guardian Eye (inventory)", guardian_eye_inventory),
      ("Guardian Eye orb", guardian_orb), ("Pearl Bed", pearl_bed),
      ("Ember Brazier", ember_brazier), ("Abyssal Lantern", abyssal_lantern)] + \
     [(f"Tidal Tile ({CORAL_ORDER[v]})", (lambda v=v: tidal_tile(v))) for v in range(5)] + \
     [("Prismatic Netherrack", prismatic_netherrack)] + \
     [(f"Prismatic fire ({FIRE_PALETTES[p][0]})", (lambda p=p: prismatic_fire(p))) for p in range(3)]


G2 = [("Arcane Pedestal", arcane_pedestal), ("Brood Egg", brood_egg), ("Trophy Board", trophy_board),
      ("Chiming Tile", chiming_tile)] + \
     [(f"Bound Glyph v{v}", (lambda v=v: tier_glyph("bound_glyph", RAMPS["violet"], RAMPS["boundsteel"], RAMPS["violet"], v,
                                                    glow=True)))
      for v in range(4)] + \
     [("Bound Altar", bound_altar), ("Phantom Roost", phantom_roost), ("Frenzy Idol", frenzy_idol),
      ("Servitor Shrine", servitor_shrine), ("Floor Sigil", floor_sigil)]


G1 = [("Initiate's Altar", initiate_altar), ("Offering Bowl", offering_bowl), ("Chalk Glyph", chalk_glyph),
      ("Chalk Glyph v1", lambda: chalk_glyph(1)), ("Chalk Glyph v2", lambda: chalk_glyph(2)),
      ("Chalk Glyph v3", lambda: chalk_glyph(3)), ("Arcane Altar", arcane_altar)]
GROUPS = {"g1": G1, "g2": G2, "g3": G3}


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
    if model.part:
        open(os.path.join(d, "part.txt"), "w", encoding="utf-8").write("shown by the plugin, not a block skin")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "g1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    suffix = "" if version == "final" else "-" + version
    models = []
    for name, make in GROUPS[which]:
        m = make()
        if not name.endswith("(front)"):   # preview-only views
            save(m)
        models.append((name, m))
    print(review(models, os.path.join(OUT, f"review-{which}{suffix}.png"), frames=4, s=5))
