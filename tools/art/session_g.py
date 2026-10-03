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
    """The Arcane Altar (vanilla: enchanting table, 12 px tall): a low block of dark stone the table's height, so the
    table's floating book shows above it - banded in gold, its corners capped in gold, its sides set with ember-glowing
    arcane eyes; the top a slab with an arcane circle and an infusion star that turn and glow (animated)."""
    m = Model("arcane_altar")
    ash, gd, em, vi = RAMPS["ash"], RAMPS["gold"], RAMPS["ember"], RAMPS["violet"]
    side = bricks(ash, 21, row_h=5, brick_w=8, tones=(2, 2, 3))
    for x in range(16):   # rows 4..15 show (the block is 12 tall): gold bands at its top and foot
        side.putpixel((x, 4), gd[4]); side.putpixel((x, 5), gd[2]); side.putpixel((x, 15), gd[2]); side.putpixel((x, 14), gd[3])
    for y in range(4, 16):
        for x in (0, 15):
            side.putpixel((x, y), gd[3] if x == 0 else gd[2])
    eye = [(6, 9), (7, 8), (8, 8), (9, 9), (6, 10), (7, 11), (8, 11), (9, 10)]
    put(side, eye, gd[4])
    put(side, [(7, 9), (8, 9), (7, 10), (8, 10)], em[4])
    put(side, [(7, 9)], em[5])
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
    m.box((0, 0, 0), (16, 12, 16), {"north": t_side, "south": t_side, "west": t_side, "east": t_side,
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
    """The Brood Egg (vanilla: sniffer egg): blocky like the sniffer egg it covers - a squarish egg sac 14 wide, 12
    deep and a block tall - of spider silk wound with bands of thread, dark eggs pressing against it from inside,
    crimson veins pulsing through it (animated); a low cap of silk on top."""
    m = Model("brood_egg")
    bone, cr, ink = RAMPS["bone"], RAMPS["crimson"], RAMPS["ink"]
    frames = []
    for f in range(4):
        silk = blank()
        for y in range(16):
            for x in range(16):
                band = (x + y) % 5 == 0          # wound thread
                silk.putpixel((x, y), bone[2] if band else bone[4] if y < 4 else bone[3])
        for (cx, cy) in ((3, 6), (10, 4), (7, 10), (12, 12)):   # eggs pressing from inside
            put(silk, [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)], ink[3])
            put(silk, [(cx, cy)], ink[4])
        glow = cr[[2, 3, 4, 3][f]]
        put(silk, [(1, 2), (2, 3), (2, 4), (3, 6), (4, 7), (5, 8), (5, 9), (6, 11), (13, 2), (13, 3), (12, 5), (12, 6),
                   (13, 8), (14, 9)], glow)
        rim(silk, bone[5], bone[1])
        frames.append(silk)
    t = m.texture("silk", frames)
    top = rim(fill(bone, 4), bone[5], bone[2])
    for y in range(16):
        for x in range(16):
            if (x * 2 + y) % 7 == 0:
                top.putpixel((x, y), bone[3])
    t_top = m.texture("top", top)
    m.cube((0.8, 0, 1.8), (15.2, 16, 14.2), t, top=t_top, bottom=t_top)
    m.cube((3, 16, 4), (13, 17.2, 12), (t, [3, 0, 13, 1]), top=t_top)
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


LILAC_STONE = hexes("#262130", "#423b4f", "#625a72", "#857c96", "#a69eb6", "#c9c2d6")   # muted, a hint of lilac
AMETHYST = hexes("#2f2244", "#4e3a72", "#7a5ea6", "#a689d0", "#d2bff0", "#f4ecff")
NOTE = ["..#.", "..##", "..#.", "###.", "##.."]   # a quaver: stem, flag, head


def polished_bricks(stone, seed):
    """Polished stone bricks that tile: 8x4 bricks in running bond across exactly one block, so neighbours join with
    no seam. Each brick is a smooth face shaded as a gentle slope (lit top-left, darker bottom-right) with a crisp lit
    bevel, a faint polish streak and a little speckle; the mortar is a thin dark line."""
    rnd = random.Random(seed)
    img = blank()
    tone = {}
    for y in range(16):
        row, off = y // 4, ((y // 4) % 2) * 4
        for x in range(16):
            bx, by = (x + off) % 8, y % 4
            key = (row, ((x + off) // 8) % 2)
            if key not in tone:
                tone[key] = rnd.choice((3, 3, 4))
            if by == 3 or bx == 7:
                img.putpixel((x, y), stone[0] if (x + y) % 4 else stone[1])
                continue
            t = tone[key]
            if by == 0 or bx == 0:
                t += 1                       # the lit bevel
            elif by == 2 and bx >= 4 or bx == 6 and by >= 1:
                t -= 1                       # falling away to the bottom-right
            img.putpixel((x, y), stone[max(1, min(len(stone) - 1, t))])
    for _ in range(8):                       # speckle
        x, y = rnd.randrange(16), rnd.randrange(16)
        if img.getpixel((x, y)) not in (stone[0], stone[1]):
            img.putpixel((x, y), stone[2])
    for (x, y) in ((2, 1), (3, 1), (13, 9), (14, 9)):   # polish streaks
        img.putpixel((x, y), stone[4])
    return img


def chiming_tile():
    """The Chiming Amethyst Tile (vanilla: amethyst block): polished stone bricks in a muted lilac grey, the same on
    every side so a floor (or wall) of tiles joins seamlessly, two amethyst musical notes inlaid in its bricks; on its
    top the notes catch the light in turn (animated)."""
    m = Model("chiming_tile")
    base = polished_bricks(LILAC_STONE, 51)
    notes = [(1, 5), (10, 13)]   # inlaid at (x, y) of each note's top-left; inside one brick face each

    def inlay(img, glow):
        for n, (nx, ny) in enumerate(notes):
            for y, row in enumerate(NOTE):
                for x, c in enumerate(row):
                    if c == "#":
                        lit = glow == n
                        img.putpixel(((nx + x) % 16, (ny + y) % 16), AMETHYST[4] if lit else AMETHYST[3] if (x + y) % 3 else AMETHYST[2])
            if glow == n:
                put(img, [((nx + 2) % 16, ny % 16)], AMETHYST[5])
        return img

    side = inlay(base.copy(), -1)
    frames = [inlay(base.copy(), g) for g in (-1, 0, -1, 1)]
    t_side, t_top = m.texture("side", side), m.texture("top", frames)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    return m


def tier_glyph(key, chalk_ramp, base_ramp, glow_ramp, variant, glow=False, base_img=None):
    """A circle glyph tile over a carpet: dark slate, a rune drawn in the tier's chalk, dust, a faint glow in the rune's
    heart. glow: the rune also burns with its own light - a second, emissive layer over the tile (light_emission 15, so
    it shines in the dark) with a soft halo round the strokes, pulsing (animated)."""
    m = Model(key + ("" if variant == 0 else f"_v{variant}"))
    rnd = random.Random(170 + variant)
    if base_img is not None:   # the tier's own surface (Hollow: living sculk)
        top = base_img.copy()
    else:
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


def _soften(ramp, amount=0.18):
    """Pulls a ramp a little toward grey (keeping its brightness)."""
    out = []
    for (r, g, b, a) in ramp:
        lum = 0.3 * r + 0.59 * g + 0.11 * b
        out.append((round(r + (lum - r) * amount), round(g + (lum - g) * amount), round(b + (lum - b) * amount), a))
    return out


CORALS = {k: _soften(v) for k, v in CORALS.items()}


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


VANILLA_FIRE = os.path.join(os.path.dirname(__file__), "vanilla_fire")   # fire_0/1.png + mcmeta from the 1.21.5 client


def prismatic_fire(palette=0):
    """Prismatic fire (shown by the plugin over a lit Prismatic Netherrack, in place of vanilla fire): vanilla's own
    fire - its two flame textures, in the classic fire shape (a box of flame walls round an X) - recoloured so its hue runs
    through the palette, rolling upward and through time like the first version's sparks; the brightness of every
    pixel is vanilla's, so it flickers exactly like fire. Glows (light_emission). Animated like vanilla (32 frames)."""
    import colorsys
    name, start, span = FIRE_PALETTES[palette]
    m = Model("prismatic_fire" + ("" if palette == 0 else f"_v{palette}"))
    m.part = True
    refs = []
    for t_name in ("fire_0", "fire_1"):
        meta = json.load(open(os.path.join(VANILLA_FIRE, t_name + ".png.mcmeta")))
        strip = Image.open(os.path.join(VANILLA_FIRE, t_name + ".png")).convert("RGBA")
        count = strip.size[1] // 16
        order = meta["animation"].get("frames", list(range(count)))
        position = {k: i for i, k in enumerate(order)}   # when each frame plays
        frames = []
        for k in range(count):
            img = strip.crop((0, k * 16, 16, k * 16 + 16))
            out = blank()
            for y in range(16):
                for x in range(16):
                    r, g, b, a = img.getpixel((x, y))
                    if a == 0:
                        continue
                    h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                    phase = (position.get(k, k) / count + (15 - y) / 40 + x / 120) % 1.0
                    if span >= 1.0:
                        hue = phase                                  # rainbow: round the whole wheel
                    else:
                        hue = start + span * (1 - abs(2 * phase - 1))  # back and forth within the palette
                    rr, gg, bb = colorsys.hls_to_rgb(hue % 1.0, l, min(1.0, sat * 0.95))
                    out.putpixel((x, y), (round(rr * 255), round(gg * 255), round(bb * 255), a))
            frames.append(out)
        refs.append(m.texture(t_name.replace("fire", "flame"), frames))
        m.mcmeta[t_name.replace("fire", "flame")] = meta   # vanilla's timing
    f0, f1 = refs
    # the classic fire shape: a box of four flame walls just inside the block's sides and an X of two flames through
    # its middle; every plane drawn from both sides so the item display shows it all round
    for (frm, to, faces, ref) in (((0, 0, 0.3), (16, 16, 0.3), ("north", "south"), f0),
                                  ((0, 0, 15.7), (16, 16, 15.7), ("south", "north"), f1),
                                  ((0.3, 0, 0), (0.3, 16, 16), ("west", "east"), f1),
                                  ((15.7, 0, 0), (15.7, 16, 16), ("east", "west"), f0)):
        m.box(frm, to, {faces[0]: (ref, [0, 0, 16, 16]), faces[1]: (ref, [16, 0, 0, 16])}, shade=False, light=15)
    for angle, ref in ((45, f0), (-45, f1)):
        el = m.box((0, 0, 8), (16, 16, 8), {"north": (ref, [0, 0, 16, 16]), "south": (ref, [16, 0, 0, 16])}, shade=False, light=15)
        el["rotation"] = {"origin": [8, 8, 8], "axis": "y", "angle": angle, "rescale": True}
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


# ================================================================== G4: tier-3 blocks (Hollow: sculk black-teal, old
# bone, hollow cyan, crimson). Built for their final Nexo look (see SESSIONS.md, Session H); glowing parts emit light.

def hollow_star(img, cx, cy, r_out, r_in, c_out, c_in, core=None):
    """The Hollow Sigil's bold eight-pointed star (filled), centred at (cx, cy)."""
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * math.pi / 8
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for y in range(16):
        for x in range(16):
            # point-in-polygon (even-odd)
            inside = False
            px, py = x + 0.5, y + 0.5
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
                    inside = not inside
            if inside:
                d = math.hypot(px - cx, py - cy)
                img.putpixel((x, y), c_in if d < r_in * 0.9 else c_out)
    if core:
        put(img, [(int(cx) - 1, int(cy) - 1), (int(cx), int(cy) - 1), (int(cx) - 1, int(cy)), (int(cx), int(cy))], core)
    return img


def sculk_stone(seed, tone=2):
    """Dark sculk-black stone, softly mottled, with a few faint cyan flecks (sculk's own spark)."""
    sk, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        for x in range(16):
            t = tone + (1 if rnd.random() < 0.2 else -1 if rnd.random() < 0.15 else 0)
            img.putpixel((x, y), sk[max(0, min(5, t))])
    for _ in range(5):
        img.putpixel((rnd.randrange(16), rnd.randrange(16)), hc[1])
    return img


DEEPSLATE = hexes("#141418", "#24242b", "#35353e", "#4a4a54", "#62626c", "#7e7e88")   # ancient-city stone


def sculk(seed, frames=4, glow=True, spots=5):
    """Sculk, tileable: irregular cells (a torus Voronoi) of dark teal, lighter at their hearts, split by near-black
    crevices; a few cells hold soul spots that pulse in turn (animated). Returns frames (or one image)."""
    sk, hc = RAMPS["sculk"], RAMPS["hollowcy"]
    rnd = random.Random(seed)
    cells = [(rnd.uniform(0, 16), rnd.uniform(0, 16)) for _ in range(11)]
    soul = rnd.sample(range(len(cells)), spots)
    base = blank()
    owner = {}
    for y in range(16):
        for x in range(16):
            ds = []
            for i, (cx, cy) in enumerate(cells):
                dx, dy = abs(x + 0.5 - cx), abs(y + 0.5 - cy)
                dx, dy = min(dx, 16 - dx), min(dy, 16 - dy)
                ds.append((math.hypot(dx, dy), i))
            ds.sort()
            (d1, i1), (d2, _) = ds[0], ds[1]
            owner[(x, y)] = (i1, d1)
            if d2 - d1 < 0.9:
                c = sk[0] if (x + y) % 3 else sk[1]
            else:
                c = sk[4] if d1 < 1.2 else sk[3] if d1 < 2.4 else sk[2]
            base.putpixel((x, y), c)
    if not glow:
        return base
    out = []
    for f in range(frames):
        img = base.copy()
        for n, i in enumerate(soul):
            level = [2, 3, 4, 5, 4, 3][(f + n * 2) % 6] if frames > 1 else 3
            for (x, y), (o, d) in owner.items():
                if o == i and d < 1.1:
                    img.putpixel((x, y), hc[level])
                elif o == i and d < 1.8 and level >= 4:
                    img.putpixel((x, y), hc[2])
        out.append(img)
    return out if frames > 1 else out[0]


def soul_glow(frames_imgs):
    """Just the glowing soul pixels of sculk frames (for an emissive layer over the face)."""
    hc = RAMPS["hollowcy"]
    out = []
    for img in frames_imgs:
        g = blank()
        for y in range(16):
            for x in range(16):
                c = img.getpixel((x, y))
                if c in hc[3:]:
                    g.putpixel((x, y), c)
        out.append(g)
    return out


def bone_tex(seed, tone=3):
    """Old bone: pale, with a lit edge, grain along its length and a few pits - not a flat fill."""
    bone = RAMPS["bone"]
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        for x in range(16):
            t = tone + (1 if x < 3 else -1 if x > 12 else 0)
            if (y * 3 + x) % 7 == 0:
                t -= 1
            img.putpixel((x, y), bone[max(1, min(5, t))])
    for _ in range(6):
        img.putpixel((rnd.randrange(16), rnd.randrange(16)), bone[1])
    return img


def deepslate_tiles(seed, overgrown=0, frames=1):
    """Ancient-city deepslate tiles (4x4 tiles with dark seams), with sculk creeping down from the top over `overgrown`
    rows in a ragged edge. Returns frames (or one image)."""
    ds = DEEPSLATE
    rnd = random.Random(seed)
    tile = blank()
    for y in range(16):
        for x in range(16):
            if y % 4 == 3 or x % 4 == 3:
                tile.putpixel((x, y), ds[0])
            else:
                t = 2 + (1 if (x % 4 == 0 or y % 4 == 0) else 0) - (1 if rnd.random() < 0.12 else 0)
                tile.putpixel((x, y), ds[t])
    if not overgrown:
        return tile
    edge = [overgrown + rnd.choice((-2, -1, 0, 0, 1, 2)) for _ in range(16)]
    sk_frames = sculk(seed + 7, frames=frames) if frames > 1 else [sculk(seed + 7, frames=1)]
    out = []
    for skf in sk_frames:
        img = tile.copy()
        for x in range(16):
            for y in range(max(0, edge[x])):
                img.putpixel((x, y), skf.getpixel((x, y)))
            if 0 <= edge[x] < 16:
                img.putpixel((x, edge[x]), RAMPS["sculk"][0])
        out.append(img)
    return out if frames > 1 else out[0]


def hollow_assembler():
    """The Hollow Assembler (vanilla: crafter): a forge of the ancient cities - a block of deepslate tiles in a frame of
    reinforced deepslate, sculk creeping over its upper half and pulsing; on each side a bone-ribbed arch with soul fire
    burning behind it (animated, glowing); on top nine bone sockets (its nine inputs) cut into sculk, a faint soul
    light in each."""
    m = Model("hollow_assembler")
    sk, hc, bone, ds = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["bone"], DEEPSLATE
    sides = deepslate_tiles(501, overgrown=6, frames=4)
    flames = []
    rnd = random.Random(503)
    for f in range(8):
        fl = blank()
        for x in range(5, 11):   # soul fire in the arch
            h = 3 + rnd.randrange(4) + (1 if 7 <= x <= 8 else 0)
            for k in range(h):
                fl.putpixel((x, 14 - k), hc[5] if k == 0 else hc[4] if k < 2 else hc[3] if k < h - 1 else hc[2])
        flames.append(fl)
    arch = []
    for img in sides:
        a = img.copy()
        for y in range(7, 15):   # the dark of the arch
            for x in range(5, 11):
                if not (y == 7 and x in (5, 10)):
                    a.putpixel((x, y), sk[0])
        for y in range(8, 15):   # bone bars across it
            for x in (6, 9):
                a.putpixel((x, y), bone[3] if y % 2 else bone[2])
        put(a, [(x, 6) for x in range(5, 11)] + [(4, y) for y in range(7, 15)] + [(11, y) for y in range(7, 15)], bone[4])
        put(a, [(x, 15) for x in range(4, 12)], bone[2])
        arch.append(a)
    t_side, t_fire = m.texture("side", arch), m.texture("fire", flames)
    t_glow = m.texture("souls", soul_glow(arch))
    top_frames = sculk(505, frames=4, spots=3)
    tops = []
    for f, img in enumerate(top_frames):
        top = img.copy()
        for i in range(3):
            for j in range(3):
                x0, y0 = 2 + i * 4, 2 + j * 4
                for (x, y) in ((x0, y0), (x0 + 1, y0), (x0 + 2, y0), (x0, y0 + 1), (x0 + 2, y0 + 1), (x0, y0 + 2), (x0 + 1, y0 + 2), (x0 + 2, y0 + 2)):
                    top.putpixel((x, y), bone[4] if (x == x0 or y == y0) else bone[2])
                top.putpixel((x0 + 1, y0 + 1), hc[4] if (i + j * 3 + f) % 4 == 0 else hc[2])
        tops.append(top)
    t_top = m.texture("top", tops)
    frame_img = blank()
    for y in range(16):
        for x in range(16):
            frame_img.putpixel((x, y), ds[3] if (x + y) % 5 else ds[2])
    rim(frame_img, ds[5], ds[1])
    t_frame = m.texture("frame", frame_img)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_frame)
    for (d, frm, to) in (("north", (0, 0, -0.05), (16, 16, -0.05)), ("south", (0, 0, 16.05), (16, 16, 16.05)),
                         ("west", (-0.05, 0, 0), (-0.05, 16, 16)), ("east", (16.05, 0, 0), (16.05, 16, 16))):
        m.box(frm, to, {d: t_fire}, shade=False, light=13)
        m.box(frm, to, {d: t_glow}, shade=False, light=15)
    for (x, z) in ((-0.4, -0.4), (14.4, -0.4), (-0.4, 14.4), (14.4, 14.4)):   # reinforced corners
        m.cube((x, 0, z), (x + 2, 16.2, z + 2), (t_frame, [0, 0, 2, 16]), top=(t_frame, [0, 0, 2, 2]))
    m.cube((-0.4, 0, -0.4), (16.4, 1.5, 16.4), (t_frame, [0, 0, 16, 2]), top=(t_frame, [0, 0, 16, 16]))   # foot
    return m


def hollow_glyph(variant=0):
    """A Hollow Glyph (vanilla: gray carpet): a thin slab of living sculk with a hollow-cyan rune burning in it."""
    return tier_glyph("hollow_glyph", RAMPS["hollowcy"], RAMPS["sculk"], RAMPS["hollowcy"], variant, glow=True,
                      base_img=sculk(520 + variant, frames=1, spots=2))


def hollow_altar():
    """The Hollow Altar (vanilla: crying obsidian; the Abyssal Altar upgrades into it): the summit of the altars - an
    ancient-city altar of deepslate tiles on a reinforced plinth, half swallowed by sculk that pulses with souls (its
    soul spots glow); on top a sculk catalyst's crown - a bone-rimmed dais with the Hollow star burning in cyan round a
    beating crimson heart; at its corners great bone fangs like a shrieker's curve up and inward, and between them
    sculk-sensor tendrils of cyan light sway (animated, glowing)."""
    m = Model("hollow_altar")
    sk, hc, bone, cr, ds = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["bone"], RAMPS["crimson"], DEEPSLATE
    sides = deepslate_tiles(551, overgrown=9, frames=6)
    t_side = m.texture("side", sides)
    t_souls = m.texture("souls", soul_glow(sides))
    plinth = blank()
    for y in range(16):
        for x in range(16):
            plinth.putpixel((x, y), ds[3] if (x // 2 + y) % 3 else ds[4])
    rim(plinth, ds[5], ds[0])
    t_plinth = m.texture("plinth", plinth)
    dais = sculk(553, frames=1, spots=0)
    rim(dais, bone[4], bone[2])
    for i in range(16):   # the catalyst's bone rim, two pixels deep
        dais.putpixel((i, 1), bone[3]); dais.putpixel((1, i), bone[3]); dais.putpixel((i, 14), bone[2]); dais.putpixel((14, i), bone[2])
    t_dais = m.texture("dais", dais)
    stars = [hollow_star(blank(), 8, 8, 6.2, 2.8, hc[3], hc[4], core=cr[[3, 4, 5, 5, 4, 3][f]]) for f in range(6)]
    t_star = m.texture("star", stars)
    t_bone = m.texture("bone", bone_tex(555, tone=3))
    t_fang = m.texture("fang", bone_tex(557, tone=4))
    tendrils = []
    for f in range(6):
        t = blank()
        sway = [0, 1, 1, 0, -1, -1][f]
        for y in range(16):
            x = 7 + (sway if y < 6 else 0)
            t.putpixel((x, y), hc[5] if y < 3 else hc[4] if y < 8 else hc[3])
            t.putpixel((x + 1, y), hc[3] if y < 8 else hc[2])
        tendrils.append(t)
    t_tendril = m.texture("tendril", tendrils)
    # the block, its glowing souls, the plinth
    m.cube((0, 1.5, 0), (16, 16, 16), (t_side, [0, 0, 16, 14.5]), top=t_dais, bottom=t_plinth)
    for (d, frm, to) in (("north", (0, 1.5, -0.05), (16, 16, -0.05)), ("south", (0, 1.5, 16.05), (16, 16, 16.05)),
                         ("west", (-0.05, 1.5, 0), (-0.05, 16, 16)), ("east", (16.05, 1.5, 0), (16.05, 16, 16))):
        m.box(frm, to, {d: (t_souls, [0, 0, 16, 14.5])}, shade=False, light=15)
    m.cube((-0.6, 0, -0.6), (16.6, 1.5, 16.6), (t_plinth, [0, 0, 16, 2]), top=t_plinth, bottom=t_plinth)
    # the dais and the star
    m.cube((3, 16, 3), (13, 17.2, 13), (t_dais, [3, 0, 13, 1]), top=(t_dais, [3, 3, 13, 13]))
    m.box((3.2, 17.25, 3.2), (12.8, 17.25, 12.8), {"up": (t_star, [1, 1, 15, 15])}, shade=False, light=15)
    # fangs: from each corner a slim bone tooth rising and hooking inward, like a shrieker's, in narrowing steps
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cz = (1.4 if sx < 0 else 14.6), (1.4 if sz < 0 else 14.6)   # the fang's root at the corner
        steps = ((2.4, 13.5, 17.0, 0.0), (2.0, 17.0, 19.5, 0.5), (1.6, 19.5, 21.5, 1.2), (1.1, 21.5, 23.0, 2.0), (0.7, 23.0, 24.2, 2.8))
        for (w, y0, y1, lean) in steps:
            x, z = cx - sx * lean, cz - sz * lean   # leaning in toward the middle as it rises
            m.cube((x - w / 2, y0, z - w / 2), (x + w / 2, y1, z + w / 2), (t_fang, [0, 0, max(1, round(w)), round(y1 - y0)]),
                   top=(t_fang, [0, 0, max(1, round(w)), max(1, round(w))]))
    # sensor tendrils between the fangs, mid-edge
    for (x, z, faces) in ((7.5, 0.6, ("north", "south")), (7.5, 15.4, ("north", "south")),
                          (0.6, 7.5, ("west", "east")), (15.4, 7.5, ("west", "east"))):
        if faces[0] == "north":
            m.box((x - 1, 16, z), (x + 1, 21, z), {faces[0]: (t_tendril, [6, 0, 9, 16]), faces[1]: (t_tendril, [9, 0, 6, 16])},
                  shade=False, light=15)
        else:
            m.box((x, 16, z - 1), (x, 21, z + 1), {faces[0]: (t_tendril, [6, 0, 9, 16]), faces[1]: (t_tendril, [9, 0, 6, 16])},
                  shade=False, light=15)
    return m


def servitor_nexus():
    """The Servitor Nexus (vanilla: conduit, a small cube in the middle of its block): a heart of hollow-cyan light
    held in a ribcage - curved bone ribs round it from a spine at its back, open at the front where the ribs fall
    short of meeting - the whole cage rooted in a mound of sculk; the heart churns, the linked spirits circling in it
    (animated, glowing)."""
    m = Model("servitor_nexus")
    sk, hc, bone = RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["bone"]
    hearts = []
    for f in range(8):
        h = fill(hc, 3)
        for y in range(16):
            for x in range(16):
                swirl = math.sin((x + y) * 0.6 + f * 0.8) + math.cos((x - y) * 0.5 - f * 0.6)
                h.putpixel((x, y), hc[5] if swirl > 1.3 else hc[4] if swirl > 0.3 else hc[3] if swirl > -0.8 else hc[2])
        a = f * math.pi / 4
        for k in range(3):   # spirits circling
            sx, sy = 7.5 + 5 * math.cos(a + k * 2.1), 7.5 + 5 * math.sin(a + k * 2.1)
            put(h, [(int(sx), int(sy))], (255, 255, 255, 255))
        hearts.append(h)
    t_heart = m.texture("heart", hearts)
    t_rib = m.texture("rib", bone_tex(571, tone=3))
    t_spine = m.texture("spine", bone_tex(573, tone=2))
    mound = sculk(575, frames=4, spots=3)
    t_mound = m.texture("mound", mound)
    t_mound_glow = m.texture("mound_glow", soul_glow(mound))
    # the sculk mound it grows from
    m.cube((1, 0, 1), (15, 2, 15), (t_mound, [1, 0, 15, 2]), top=t_mound, bottom=t_mound)
    m.cube((3, 2, 3), (13, 3.5, 13), (t_mound, [3, 0, 13, 2]), top=(t_mound, [3, 3, 13, 13]))
    m.box((1, 2.05, 1), (15, 2.05, 15), {"up": (t_mound_glow, [1, 1, 15, 15])}, shade=False, light=15)
    # the heart
    m.box((4.6, 4.6, 4.6), (11.4, 11.4, 11.4), {d: (t_heart, [2, 2, 14, 14]) for d in FACES_ALL}, shade=False, light=15)
    # the spine at the back (south, +z), vertebrae stepping
    for y in range(3, 16, 2):
        m.cube((7, y, 13.2), (9, y + 1.6, 15), (t_spine, [0, 0, 2, 2]), top=(t_spine, [0, 0, 2, 2]))
    # ribs: four, each curving from the spine round one side toward the front and sloping down as real ribs do,
    # stopping short of meeting; longest in the middle of the cage
    for y, reach in ((6.0, 0.8), (8.8, 1.0), (11.6, 0.9), (14.0, 0.55)):
        h, r = 0.9, 3.2 + 3.2 * reach
        for side in (-1, 1):
            segs = [((8 + side * 1, 13.4), (8 + side * 4.0, 14.3), 0.0),          # leaving the spine
                    ((8 + side * 4.0, 11.4), (8 + side * (r - 0.4), 13.4), -0.4),  # bending round the back
                    ((8 + side * (r - 0.4), 6.0), (8 + side * (r + 0.6), 11.4), -0.9),  # down the side
                    ((8 + side * (r - 1.6), 4.0), (8 + side * (r - 0.4), 6.0), -1.5),   # turning to the front
                    ((8 + side * (r - 3.2), 3.2), (8 + side * (r - 1.6), 4.2), -2.0)]   # the tip
            for (ax, az), (bx, bz), dy in segs:
                x0, x1 = sorted((ax, bx))
                z0, z1 = sorted((az, bz))
                m.cube((x0, y + dy, z0), (x1, y + dy + h, z1), (t_rib, [0, 0, max(1, round(x1 - x0)), 1]),
                       top=(t_rib, [0, 0, max(1, round(x1 - x0)), max(1, round(z1 - z0))]))
    return m


RESIN = hexes("#2a1206", "#5a2a0c", "#8a4816", "#b46a26", "#d89144", "#f2bf72")   # amber resin, warm but not loud


def resin_tile():
    """The Resin Tile (vanilla: resin bricks): polished bricks of amber resin from the Heartwood - warm, a little
    translucent-looking (a lit inner glow in each brick), joined by dark heartwood seams; the same on every side and
    running bond across exactly one block, so floors join seamlessly; a tiny insect caught in one brick, and a glint
    that slides across the top (animated)."""
    m = Model("resin_tile")
    base = polished_bricks(RESIN, 491)
    for (x, y) in ((4, 9), (5, 9), (4, 10), (6, 10), (5, 8), (3, 8)):   # a little fly caught in the amber
        base.putpixel((x, y), RESIN[0])
    put(base, [(13, 5), (14, 5), (12, 6)], RESIN[1])   # and a speck of heartwood
    for y in range(16):   # amber is translucent: light pools in the middle of each brick
        row, off = y // 4, ((y // 4) % 2) * 4
        for x in range(16):
            if (x + off) % 8 in (3, 4) and y % 4 == 1 and base.getpixel((x, y)) in (RESIN[2], RESIN[3]):
                base.putpixel((x, y), RESIN[4])
    put(base, [(10, 1), (11, 1), (2, 13)], RESIN[5])
    frames = []
    for f in range(8):
        top = base.copy()
        for k in range(16):   # a glint sliding along a diagonal
            x, y = (k + f * 2) % 16, (k * 2 + f) % 16
            if k % 5 == 0 and top.getpixel((x, y)) not in (RESIN[0], RESIN[1]):
                top.putpixel((x, y), RESIN[5])
        frames.append(top)
    t_side, t_top = m.texture("side", base), m.texture("top", frames)
    m.cube((0, 0, 0), (16, 16, 16), t_side, top=t_top, bottom=t_side)
    return m


G4 = [("Hollow Assembler", hollow_assembler)] + \
     [(f"Hollow Glyph v{v}", (lambda v=v: hollow_glyph(v))) for v in range(4)] + \
     [("Hollow Altar", hollow_altar), ("Servitor Nexus", servitor_nexus), ("Resin Tile", resin_tile)]


# ================================================================== G5: held 3D models. In the inventory (and on the
# ground, in frames) these items keep their 2D icons; in the hand (and on the head) they are these models - the item
# definition selects on display_context, as vanilla's trident does. build_pack wires folders named <key>_held.

HANDHELD_DISPLAY = {   # vanilla item/handheld (with item/generated's head): how a sword sprite is held
    "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}
GENERATED_DISPLAY = {   # vanilla item/generated: how a flat item (a book) is held
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}
TRIDENT_DISPLAY = {   # vanilla item/trident_in_hand (its model points up along y, centred on x = z = 0)
    "thirdperson_righthand": {"rotation": [0, 60, 0], "translation": [11, 17, -2], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 60, 0], "translation": [3, 17, 12], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [-3, 17, 1], "scale": [1, 1, 1]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [13, 17, 1], "scale": [1, 1, 1]},
}


# The hand's frame (from vanilla's ItemInHandLayer, checked against an in-game screenshot of the censer): with no display
# rotation a model's +y points forward along the arm's front and its -z runs down the arm toward the fist. Where the
# fist grips, in display space: vanilla handheld holds a sword sprite at about pixel (3, 3) and puts it at
FIST = (0.0, -1.9, 1.5)


def grip_display(rotation, grip, scale, first_person=None):
    """Third-person display that turns a model by `rotation` and puts its grip point (model px) in the fist."""
    o = [(grip[i] - 8.0) * scale for i in range(3)]
    r = _rot_xyz(rotation, o)
    t = [round(FIST[i] - r[i], 3) for i in range(3)]
    d = {"thirdperson_righthand": {"rotation": list(rotation), "translation": t, "scale": [scale] * 3},
         "thirdperson_lefthand": {"rotation": list(rotation), "translation": t, "scale": [scale] * 3},
         "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]}}
    d.update(first_person or {
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]}})
    return d


def _rot_xyz(deg, v):
    """Minecraft's display rotation (a quaternion from Euler XYZ: Rx * Ry * Rz) applied to v."""
    rx, ry, rz = (math.radians(a) for a in deg)
    x, y, z = v
    # Rz
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    # Ry
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    # Rx
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    return x, y, z


def shifted_display(display, offset):
    """A display for a model drawn `offset` px away from the frame `display` was made for: each translation is
    corrected by the offset turned and scaled as that context turns and scales the model (T' = T - R S o)."""
    out = {}
    for ctx, d in display.items():
        o = [offset[i] * d["scale"][i] for i in range(3)]
        r = _rot_xyz(d["rotation"], o)
        t = [round(d["translation"][i] - r[i], 3) for i in range(3)]
        out[ctx] = {"rotation": d["rotation"], "translation": t, "scale": d["scale"]}
    return out


def diagonal(m, angle=-45):
    """Lays a model built upright (along y, centred on x = z = 8, from y -3 to 19) along the diagonal a sprite takes:
    -45 = a sword's (grip bottom-left, head top-right); +45 = vanilla's spear's (head top-left, butt bottom-right)."""
    for e in m.elements:
        assert "rotation" not in e
        e["rotation"] = {"origin": [8, 8, 8], "axis": "z", "angle": angle}
    return m


def prism(m, w, y0, y1, faces_tex, top=None, light=0, cx=8.0, cz=8.0, d=None, shade=True):
    """A square (or w x d) upright box centred on (cx, cz)."""
    d = d or w
    tex, uv = faces_tex if isinstance(faces_tex, tuple) else (faces_tex, None)
    def f(width):
        return (tex, uv or [0, 0, max(1, round(width)), max(1, round(y1 - y0))])
    faces = {"north": f(w), "south": f(w), "west": f(d), "east": f(d)}
    cap = top or (tex, [0, 0, max(1, round(w)), max(1, round(d))])
    faces["up"] = cap
    faces["down"] = cap
    return m.box((cx - w / 2, y0, cz - d / 2), (cx + w / 2, y1, cz + d / 2), faces, shade=shade, light=light)


def metal(ramp, seed, tone=3):
    """Shaded metal: a lit stripe down the left, darker to the right, a little wear."""
    rnd = random.Random(seed)
    img = blank()
    for y in range(16):
        for x in range(16):
            t = tone + (1 if x % 4 == 0 else -1 if x % 4 == 3 else 0) - (1 if rnd.random() < 0.08 else 0)
            img.putpixel((x, y), ramp[max(0, min(len(ramp) - 1, t))])
    return img


def orb_frames(ramp, n=8, swirl=0.7):
    """A glowing orb's surface: a hot heart, a slow swirl of brighter and darker light (animated)."""
    out = []
    for f in range(n):
        img = blank()
        for y in range(16):
            for x in range(16):
                v = math.sin((x + y) * swirl + f * 0.8) + math.cos((x - y) * 0.5 - f * 0.5)
                img.putpixel((x, y), ramp[5] if v > 1.3 else ramp[4] if v > 0.2 else ramp[3] if v > -0.9 else ramp[2])
        out.append(img)
    return out


def eyeball_faces(m, gaze_path, prefix="eye"):
    """A guardian's eyeball as six face textures per frame: each face pixel is a point on the ball, coloured iris or
    pupil by its angle to where the eye looks - so the one pupil slides across faces as the gaze moves round."""
    sg, bone, ab, cr = RAMPS["seaglow"], RAMPS["bone"], RAMPS["abyss"], RAMPS["crimson"]
    def point(face, u, v):
        a, b = -1 + 2 * (u + 0.5) / 16, 1 - 2 * (v + 0.5) / 16   # a: right as seen from outside, b: up
        return {"up": (a, 1, -b), "down": (a, -1, b), "north": (-a, b, -1), "south": (a, b, 1),
                "west": (-1, b, a), "east": (1, b, -a)}[face]
    refs = {}
    for face in FACES_ALL:
        frames = []
        for g in gaze_path:
            gl = math.sqrt(sum(c * c for c in g))
            g = [c / gl for c in g]
            img = fill(bone, 4)
            for v in range(16):
                for u in range(16):
                    pnt = point(face, u, v)
                    pl = math.sqrt(sum(c * c for c in pnt))
                    ang = math.degrees(math.acos(max(-1, min(1, sum(pnt[i] * g[i] for i in range(3)) / pl))))
                    if ang < 15:
                        img.putpixel((u, v), ab[0])
                    elif ang < 30:
                        img.putpixel((u, v), sg[4] if ang < 25 else sg[2])
                    elif ang > 120 and (u * 3 + v * 5) % 23 == 0:
                        img.putpixel((u, v), cr[3])   # veins at the back
            frames.append(img)
        refs[face] = m.texture(f"{prefix}_{face}", frames)
    return refs


# where the eye looks, frame by frame (in the scepter's frame: +y out of its tip): holds and darts, all round
GAZE_PATH = [(0, 1, 0), (0, 1, 0), (0, 1, 0), (0.9, 0.5, 0.2), (0.9, 0.5, 0.2), (0.4, 0.4, 0.9), (0.4, 0.4, 0.9),
             (0, 1, 0), (-0.9, 0.5, -0.1), (-0.9, 0.5, -0.1), (-0.3, 0.3, -0.95), (-0.3, 0.3, -0.95), (0, 1, 0),
             (0.2, 0.6, 0.8), (0.95, 0.2, -0.3), (0, 1, 0)]


def scepter(key, metal_ramp, orb_ramp, eye=False, using=False):
    """A scepter (Wyrmbreath, Guardian's Gaze): a pommel, a wrapped grip, a ringed collar, a cup from which four claw
    prongs rise at the orb's corners and just hook over its top edges - the orb (or the guardian's eye) stays in full
    view. The eye is a ball: one pupil that darts round to look every way, sliding across its faces (16 frames).
    using: the model while right-click is held - upright and posed straight out along the raised arm."""
    m = Model(key + ("_held_using" if using else "_held"))
    m.part = True
    t_metal = m.texture("metal", metal(metal_ramp, 601))
    grip = metal(metal_ramp, 603, tone=2)
    for y in range(0, 16, 3):
        for x in range(16):
            grip.putpixel((x, y), metal_ramp[1])
    t_grip = m.texture("grip", grip)
    prism(m, 2.4, -3, -1.6, t_metal)                       # pommel
    prism(m, 1.6, -1.6, 8, t_grip)                          # grip
    prism(m, 3.0, 8, 9.4, t_metal)                          # collar
    prism(m, 1.8, 9.4, 10, t_metal)
    prism(m, 4.2, 10, 11.2, t_metal)                        # the cup
    if eye:
        faces = eyeball_faces(m, GAZE_PATH)
        m.box((5.8, 11.2, 5.8), (10.2, 15.6, 10.2), {d: faces[d] for d in FACES_ALL}, light=12)
    else:
        t_orb = m.texture("orb", orb_frames(orb_ramp))
        prism(m, 4.4, 11.2, 15.6, (t_orb, [3, 3, 13, 13]), light=15, shade=False)   # the orb
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):   # four claws at the orb's corners
        px, pz = 8 + sx * 2.7, 8 + sz * 2.7
        prism(m, 1.0, 10.4, 15.2, t_metal, cx=px, cz=pz)
        prism(m, 0.9, 15.2, 16.2, t_metal, cx=8 + sx * 2.05, cz=8 + sz * 2.05)   # hooking just over the corner
    if using:
        # the raised arm (the SPEAR use pose) points forward, so the model's -z (down the arm) is forward: turn the
        # scepter's tip (+y) onto -z, grip in the fist
        m.display = grip_display((-90, 0, 0), (8, 3.2, 8), 0.85, first_person={
            "firstperson_righthand": {"rotation": [-60, -10, 0], "translation": [1.5, 1.5, -2], "scale": [0.68] * 3},
            "firstperson_lefthand": {"rotation": [-60, 10, 0], "translation": [1.5, 1.5, -2], "scale": [0.68] * 3}})
    else:
        m.display = HANDHELD_DISPLAY
    return m


def wyrmbreath_held(using=False):
    """Wyrmbreath in the hand: a gold scepter, its claws round an orb of dragon fire (pointed ahead while in use)."""
    m = scepter("wyrmbreath", RAMPS["gold"], RAMPS["ember"], using=using)
    return m if using else diagonal(m)


def guardians_gaze_held(using=False):
    """Guardian's Gaze in the hand: a teal-steel scepter, its claws round a guardian's eye that looks all about."""
    m = scepter("guardians_gaze", RAMPS["abyss"], RAMPS["seaglow"], eye=True, using=using)
    return m if using else diagonal(m)


def abyssal_anchor_held():
    """The Abyssal Anchor in the hand, held by its ring like a war hammer: a round ring in the fist, a stock across just
    above it with ball ends, the shank rising with sea-glow runes (glowing), and at the top the crown with the two arms
    curving out and down in a smooth arc to broad arrowhead flukes - an anchor's true silhouette, upside down as it is
    swung; a spectral chain trails from the ring (glowing)."""
    m = Model("abyssal_anchor_held")
    m.part = True
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    t_iron = m.texture("iron", metal(ab, 611, tone=3))
    t_dark = m.texture("dark", metal(ab, 612, tone=2))
    runes = []
    for f in range(6):
        img = metal(ab, 613, tone=3)
        for i, y in enumerate((2, 6, 10, 14)):
            put(img, [(7, y), (8, y)], sg[[3, 4, 5, 4, 3, 2][(f + i) % 6]])
        runes.append(img)
    t_rune = m.texture("rune", runes)
    t_chain = m.texture("chain", fill(sg, 4))
    # the ring: an octagon of bars in the x-y plane, centred at y -0.6
    cy = -0.6
    for (w, h, dx, dy) in ((2.6, 0.9, 0, 2.2), (2.6, 0.9, 0, -2.2), (0.9, 2.6, 2.2, 0), (0.9, 2.6, -2.2, 0)):
        m.cube((8 + dx - w / 2, cy + dy - h / 2, 7.55), (8 + dx + w / 2, cy + dy + h / 2, 8.45), (t_iron, [0, 0, 2, 2]))
    for (dx, dy) in ((1.5, 1.5), (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5)):
        m.cube((8 + dx - 0.6, cy + dy - 0.6, 7.55), (8 + dx + 0.6, cy + dy + 0.6, 8.45), (t_iron, [0, 0, 1, 1]))
    # the stock, across (z), ball-ended
    prism(m, 1.2, 2.2, 3.4, t_dark, d=8.4)
    for z in (3.4, 12.6):
        prism(m, 1.8, 1.9, 3.7, t_dark, cz=z)
    prism(m, 2.0, 3.4, 13.6, (t_rune, [0, 0, 2, 10]))       # the shank
    m.box((7.2, 4, 6.95), (8.8, 13.2, 6.95), {"north": (t_rune, [6, 1, 10, 15])}, shade=False, light=15)
    m.box((7.2, 4, 9.05), (8.8, 13.2, 9.05), {"south": (t_rune, [6, 1, 10, 15])}, shade=False, light=15)
    prism(m, 3.2, 13.6, 15.4, t_iron)                       # the crown
    prism(m, 1.6, 15.4, 16.8, t_iron)
    # the arms: an arc whose centre is on the shank below the crown (radius 5), from the crown out and down
    for side in (-1, 1):
        for k in range(7):
            phi = math.radians(20 + k * 13)
            ax, ay = 8 + side * 5.0 * math.sin(phi), 10.4 + 5.0 * math.cos(phi)
            prism(m, 1.6, ay - 0.8, ay + 0.8, t_iron, cx=ax, d=1.8)
        # the fluke: a broad arrowhead pointing down (toward the ring), at the arm's end
        fx = 8 + side * 4.9
        for (w, y0, y1) in ((3.4, 9.6, 10.6), (2.6, 8.6, 9.6), (1.6, 7.8, 8.6), (0.7, 7.2, 7.8)):
            prism(m, w, y0, y1, t_iron, cx=fx, d=1.4)
    for i in range(4):                                      # the spectral chain trailing from the ring
        prism(m, 1.6 if i % 2 == 0 else 0.6, -4.6 - i * 1.6, -3.0 - i * 1.6, (t_chain, [0, 0, 2, 2]),
              d=0.6 if i % 2 == 0 else 1.6, light=15, shade=False)
    m.display = HANDHELD_DISPLAY
    return diagonal(m)


CENSER_GRIP = (8, 6.5, 8)   # the middle of the grip


def soulfire_censer_held(using=False):
    """The Soulfire Censer in the hand: a gold grip in the fist and a gold handle sticking straight out ahead of it; from
    a ring at the handle's tip a chain drops, and the censer hangs from it by its own weight - a gold cap, a dark caged
    orb with soul fire behind cyan glass (glowing, animated), a gold band, a finial hanging below.
    Built in the hand's own frame (from vanilla's ItemInHandLayer, confirmed by an in-game screenshot): +y points out
    ahead of the fist, -z down the arm. Arm hanging (no turn): the handle points ahead and the chain hangs down. Arm
    raised forward (the in-use pose) and first person: down the arm is ahead, so the model turns -90 about x - the
    handle still points ahead and the chain still hangs down."""
    m = Model("soulfire_censer_held" + ("_using" if using else ""))
    m.part = True
    gd, st, hc, ir = RAMPS["gold"], RAMPS["boundsteel"], RAMPS["hollowcy"], RAMPS["iron"]
    t_gold = m.texture("gold", metal(gd, 621))
    t_steel = m.texture("steel", metal(st, 623, tone=2))
    t_chain = m.texture("chain", metal(ir, 625, tone=3))
    fires = []
    for f in range(8):
        img = fill(st, 1)
        rnd = random.Random(627 + f)
        for x in range(3, 13):
            h = 4 + rnd.randrange(5)
            for k in range(h):
                img.putpixel((x, 13 - k), hc[5] if k < 2 else hc[4] if k < 4 else hc[3])
        for x in (5, 10):
            for y in range(16):
                img.putpixel((x, y), st[2])
        fires.append(img)
    t_fire = m.texture("fire", fires)
    G = lambda w, h: (t_gold, [0, 0, max(1, round(w)), max(1, round(h))])  # noqa: E731
    m.cube((6.8, 3.0, 6.8), (9.2, 4.0, 9.2), G(2, 1))                     # pommel cap
    m.cube((7.2, 4.0, 7.2), (8.8, 9.0, 8.8), G(2, 5))                     # the grip, in the fist
    m.cube((7.4, 9.0, 7.4), (8.6, 17.0, 8.6), G(1, 8))                    # the handle, straight out ahead
    m.cube((7.0, 17.0, 7.0), (9.0, 18.4, 9.0), G(2, 1))                   # the ring at its tip
    m.cube((7.6, 17.2, 6.0), (8.4, 18.2, 7.0), G(1, 1))                   # a hook under it
    # the chain, dropping straight down (-z) from the hook
    for i in range(4):
        z1 = 6.0 - i * 1.5
        w, d = (1.2, 0.5) if i % 2 == 0 else (0.5, 1.2)
        m.cube((8 - w / 2, 17.7 - d / 2, z1 - 1.6), (8 + w / 2, 17.7 + d / 2, z1), (t_chain, [0, 0, 1, 2]))
    # the censer, hanging by its weight: its top is +z, its bottom -z
    m.cube((6.7, 16.4, 0.0), (9.3, 19.0, 1.0), G(3, 1))                   # cap
    m.cube((5.7, 15.4, -0.8), (10.3, 20.0, 0.0), (t_steel, [0, 0, 5, 1]))
    m.box((5.0, 14.7, -4.8), (11.0, 20.7, -0.8), {d: (t_fire, [2, 2, 14, 14]) for d in FACES_ALL}, shade=False, light=15)
    m.cube((4.8, 14.5, -3.2), (11.2, 20.9, -2.4), G(6, 1))                # its band
    m.cube((5.7, 15.4, -5.8), (10.3, 20.0, -4.8), (t_steel, [0, 0, 5, 1]))
    m.cube((7.0, 16.7, -6.8), (9.0, 18.7, -5.8), G(2, 1))                 # finial
    m.cube((7.6, 17.3, -8.4), (8.4, 18.1, -6.8), G(1, 2))
    fp = {"firstperson_righthand": {"rotation": [-90, -10, 0], "translation": [1.5, 2.0, -1.0], "scale": [0.68] * 3},
          "firstperson_lefthand": {"rotation": [-90, 10, 0], "translation": [1.5, 2.0, -1.0], "scale": [0.68] * 3}}
    m.display = grip_display((-90, 0, 0) if using else (0, 0, 0), CENSER_GRIP, 0.7, first_person=fp)
    return m


SPEAR_DISPLAY = {   # vanilla 26.2 item/spear_in_hand: how a spear is held (its sprite runs head top-left to butt bottom-right)
    "firstperson_righthand": {"rotation": [-20, 90, -35], "translation": [3.13, 2.0, 0.13], "scale": [1.36, 1.36, 0.68]},
    "firstperson_lefthand": {"rotation": [-20, -90, 35], "translation": [3.13, 2.0, 0.13], "scale": [1.36, 1.36, 0.68]},
    "thirdperson_righthand": {"rotation": [5, 270, -40], "translation": [0, 2, 2], "scale": [1.7, 1.7, 0.85]},
    "thirdperson_lefthand": {"rotation": [5, -270, 40], "translation": [0, 2, 2], "scale": [1.7, 1.7, 0.85]},
}


DREAD_HEAD = [   # vanilla's spear head, upright (tip at the top), one pixel = half a unit, as in vanilla's 32 px sprite
    "...#...",
    "...#...",
    "..###..",
    "..###..",
    ".#####.",
    ".#####.",
    "#######",
    "#######",
    "#.....#",    # the barbs at its back corners
]


def dreadlance_head():
    """The head's texture, shaded like vanilla's spear head in blackened steel: a bright ridge down the middle catching
    the light, the lit half lighter than the shadowed one, its edges darker - no accent colour."""
    ds = [(16, 16, 20, 255), (30, 30, 37, 255), (46, 46, 56, 255), (66, 66, 78, 255), (92, 92, 106, 255), (132, 132, 146, 255)]
    img = blank()
    for r, row in enumerate(DREAD_HEAD):
        cols = [c for c, ch in enumerate(row) if ch == "#"]
        for c in cols:
            edge = c in (min(cols), max(cols)) or r == len(DREAD_HEAD) - 2
            if r == len(DREAD_HEAD) - 1:
                col = ds[3] if c < 3 else ds[2]                       # barbs
            elif c == 3:
                col = ds[5]                                           # the ridge
            elif c < 3:
                col = ds[3] if edge else ds[4]                        # lit half
            else:
                col = ds[2] if edge else ds[3]                        # shadowed half
            img.putpixel((c, r), col)
    return img


def dreadlance_head_boxes(m, tex, y0, px=0.5, depth=1.0):
    """Builds DREAD_HEAD as voxels one pixel thick: one box per run of pixels in a row, every face textured with the
    pixels it shows (like vanilla's generated item models)."""
    rows = len(DREAD_HEAD)
    for r, row in enumerate(DREAD_HEAD):
        yb = y0 + (rows - 1 - r) * px
        c = 0
        while c < len(row):
            if row[c] != "#":
                c += 1
                continue
            c1 = c
            while c1 + 1 < len(row) and row[c1 + 1] == "#":
                c1 += 1
            x0 = 8 - len(row) * px / 2 + c * px
            x1 = x0 + (c1 - c + 1) * px
            run = [c, r, c1 + 1, r + 1]
            m.box((x0, yb, 8 - depth / 2), (x1, yb + px, 8 + depth / 2),
                  {"south": (tex, run), "north": (tex, [c1 + 1, r, c, r + 1]), "up": (tex, run), "down": (tex, run),
                   "west": (tex, [c, r, c + 1, r + 1]), "east": (tex, [c1, r, c1 + 1, r + 1])})
            c = c1 + 1


def dreadlance_held():
    """The Dreadlance in the hand, held exactly as vanilla holds a spear (vanilla's own spear_in_hand transforms, read
    from the 26.2 client; built upright, laid on the spear's +45 diagonal; vanilla stretches a spear 1.7x in its plane
    and 0.85x in depth, so the staff's parts are drawn twice as deep as wide to come out round).
    A detailed 3D staff in the Hollow armour's scheme - a steel butt spike with a soul gem, a ferrule, a violet-black
    wrapped grip between steel collars, a dark sculk shaft with raised steel rings inlaid with soul light, a socket with
    glowing purple gems and swept-back lugs - and a head of blackened steel with exactly vanilla's spear-head shape
    and size, built as voxels one pixel thick (depth 1 unit, which vanilla's 0.85x depth stretch makes as deep as a
    pixel is wide), shaded like vanilla's: a bright ridge, a lit half and a shadowed half."""
    m = Model("dreadlance_held")
    m.part = True
    sk, vi, hc, ink = RAMPS["sculk"], RAMPS["violet"], RAMPS["hollowcy"], RAMPS["ink"]
    st = STEEL
    t_steel = m.texture("steel", metal(st, 651, tone=3))
    t_dark = m.texture("steel_dark", metal(st, 652, tone=2))
    shaft = blank()
    for y in range(16):
        for x in range(16):
            shaft.putpixel((x, y), sk[3] if x % 4 == 0 else sk[2] if (x + y) % 5 else sk[1])   # dark sculk grain
    t_shaft = m.texture("shaft", shaft)
    grip = blank()
    for y in range(16):
        for x in range(16):
            band = (y + x // 3) % 4
            grip.putpixel((x, y), vi[2] if band == 0 else ink[3] if band in (1, 2) else ink[2])   # violet-black wrap
    t_grip = m.texture("grip", grip)
    t_soul = m.texture("soul", [fill(hc, [3, 4, 5, 4][f]) for f in range(4)])
    t_gem = m.texture("gem", [fill(vi, [3, 4, 5, 4][f]) for f in range(4)])
    t_head = m.texture("head", dreadlance_head())
    def p(w, y0, y1, tex, d=None, light=0, cx=8.0):
        """A round part: an octagonal section (two crossed boxes, corners cut), drawn twice as deep as wide so vanilla's
        0.85x depth against 1.7x in-plane makes it come out round; the inner box is a hair shorter so the caps don't
        fight."""
        d = d if d else w * 2
        prism(m, w, y0, y1, tex, cx=cx, d=d * 0.58, light=light)
        prism(m, w * 0.58, y0 + 0.02, y1 - 0.02, tex, cx=cx, d=d, light=light)
    p(0.5, -3.0, -2.2, t_steel)                            # butt spike
    p(0.9, -2.2, -1.4, t_steel)
    p(1.0, -1.4, -0.6, t_soul, light=15)                   # soul gem
    p(1.15, -0.6, 0.0, t_steel)                            # ferrule
    p(1.0, 0.0, 0.5, t_dark)
    p(0.8, 0.5, 5.0, (t_grip, [0, 0, 2, 5]))               # wrapped grip
    p(1.05, 5.0, 5.6, t_steel)                             # collar
    p(0.7, 5.6, 12.0, (t_shaft, [6, 0, 8, 16]))            # the shaft
    for y in (7.2, 9.6):                                    # raised steel rings, soul light inlaid
        p(0.95, y, y + 0.5, t_steel)
        p(0.97, y + 0.15, y + 0.35, t_soul, light=15)
    p(1.05, 12.0, 12.6, t_steel)                           # socket
    p(1.4, 12.6, 13.4, t_dark)
    for sx in (-1, 1):
        m.box((8 + sx * 0.82 - 0.25, 12.7, 7.4), (8 + sx * 0.82 + 0.25, 13.3, 8.6), {d: (t_gem, [0, 0, 1, 1]) for d in FACES_ALL},
              light=15)                                    # a purple gem each side
        p(0.4, 11.8, 13.2, t_steel, cx=8 + sx * 1.25, d=0.7)   # lugs swept back from the socket
        p(0.3, 11.0, 12.0, t_steel, cx=8 + sx * 1.55, d=0.5)
    p(0.9, 13.4, 13.9, t_dark)                             # neck, between the barbs
    dreadlance_head_boxes(m, t_head, 13.4)                  # the head: vanilla's spear head, one pixel thick
    m.display = SPEAR_DISPLAY
    return diagonal(m, angle=45)


CLEAVER_STEEL = hexes("#1b1c20", "#34363c", "#555860", "#7e818a", "#aeb1b9", "#e2e4e9")   # plain forged steel, no tint
# Blood on the blade's flat (8 wide: u 0 = the cutting edge, u 7 = against the haft; v 0 = the far end): dried (B),
# fresh (b), a wet highlight (r) - heaviest along the edge, a few runs inward and spatter on the flat.
CLEAVER_BLOOD = [
    "........",
    "........",
    "b.......",
    "Bb....B.",
    "BBb.....",
    "rBBb....",
    "BBBBb...",
    "BrB.Bb..",
    "BB....B.",
    "Bb......",
    "BBb..b..",
    "b..B....",
    "........",
]
CLEAVER_EDGE_BLOOD = "..bBBrBBBbB."   # the honed edge, far end first


def cleaver_flat():
    """The blade's flat, like forged steel: a bright honed bevel along the edge and the dark grind line behind it, the
    flat itself in a smooth gradient - lighter toward the edge, darker toward the haft - crossed by one soft diagonal
    reflection; then the blood over it."""
    st, cr = CLEAVER_STEEL, RAMPS["crimson"]
    img = blank()
    for v in range(13):
        for u in range(8):
            if u == 0:
                col = st[5] if v % 5 else st[4]                      # honed bevel
            elif u == 1:
                col = st[4]
            elif u == 2:
                col = st[2]                                          # grind line
            else:
                t = 3 if u < 5 else 2                                # gradient across the flat
                streak = (u + v) % 13
                if streak in (6, 7):
                    t += 1                                           # a soft reflection
                elif streak == 8:
                    t -= 0 if t == 2 else 1
                col = st[t]
            img.putpixel((u, v), col)
            ch = CLEAVER_BLOOD[v][u]
            if ch != ".":
                img.putpixel((u, v), {"B": cr[1], "b": cr[2], "r": cr[3]}[ch])
    for v, ch in enumerate(CLEAVER_EDGE_BLOOD):                       # the edge strip's texture, column 15
        img.putpixel((15, v), {"B": cr[1], "b": cr[2], "r": cr[3]}.get(ch, CLEAVER_STEEL[5] if v % 3 else CLEAVER_STEEL[4]))
    return img


def frenzy_cleaver_held():
    """The Frenzy Cleaver in the hand: a short wrapped grip with a pommel cap, and a big butcher's blade of plain forged
    steel - long and broad, a thick spine along its top, a bright honed bevel and grind line along the edge, a smooth
    gradient and a soft reflection across the flat - streaked with dried and fresh blood along the edge, running inward,
    spattered over the flat (no glow); the haft runs up through it; rivets."""
    m = Model("frenzy_cleaver_held")
    m.part = True
    wood, le = RAMPS["wood"], RAMPS["leather"]
    st = CLEAVER_STEEL
    haft = blank()
    for y in range(16):
        for x in range(16):
            haft.putpixel((x, y), wood[3] if x % 4 == 0 else wood[2] if (x + y) % 5 else wood[1])
    t_haft = m.texture("haft", haft)
    wrap = blank()
    for y in range(16):
        for x in range(16):
            wrap.putpixel((x, y), le[3] if (y + x // 2) % 3 else le[1])
    t_wrap = m.texture("wrap", wrap)
    t_flat = m.texture("flat", cleaver_flat())
    t_spine = m.texture("spine", metal(st, 661, tone=2))
    t_rivet = m.texture("rivet", fill(st, 4))
    prism(m, 2.0, -3.0, -2.0, t_spine)                      # pommel cap
    prism(m, 1.6, -2.0, 2.6, (t_wrap, [0, 0, 2, 5]))        # a short wrapped grip
    prism(m, 1.6, 2.6, 18.6, (t_haft, [6, 0, 8, 16]))       # the haft, up through the blade
    prism(m, 2.0, 18.6, 19.4, t_spine)
    # the blade, to the -x side (up-left once laid on the diagonal): 13 long, 8 broad
    m.box((-0.8, 5.4, 7.5), (7.2, 18.4, 8.5), {"south": (t_flat, [0, 0, 8, 13]), "north": (t_flat, [8, 0, 0, 13]),
          "up": (t_spine, [0, 0, 8, 1]), "down": (t_spine, [0, 0, 8, 1])})                       # the flat, both sides
    m.cube((6.6, 5.0, 7.3), (7.4, 18.8, 8.7), (t_spine, [0, 0, 1, 14]))           # bound to the haft
    m.cube((-0.8, 17.4, 7.2), (7.2, 18.8, 8.8), (t_spine, [0, 0, 8, 1]))          # the thick spine along the top
    m.cube((-0.8, 5.0, 7.3), (7.2, 5.6, 8.7), (t_spine, [0, 0, 8, 1]))            # the heel
    m.box((-1.8, 5.6, 7.7), (-0.8, 17.4, 8.3), {d: (t_flat, [15, 0, 16, 12]) for d in ("west", "north", "south")} |
          {"up": (t_flat, [15, 0, 16, 1]), "down": (t_flat, [15, 11, 16, 12])})  # the honed edge, bloodied
    for (x, y) in ((3.2, 14.6), (3.2, 8.4)):                                       # rivets
        m.cube((x, y, 7.3), (x + 1.0, y + 1.0, 8.7), (t_rivet, [0, 0, 1, 1]))
    m.display = HANDHELD_DISPLAY
    return diagonal(m)


GRIMOIRE_RUNE = ["..#..", ".#.#.", "#.#.#", ".#.#.", "..#.."]


def grimoire_pages():
    """Both pages, 1 texel a unit (left page u 0-6, right page u 8-14, 12 rows, far end at the top): bone-white
    parchment, darker toward the gutter, lines of dark script, the rune printed faintly (its glow is the overlay)."""
    bone, ink = RAMPS["bone"], RAMPS["ink"]
    img = blank()
    for u0, gutter in ((0, 6), (8, 8)):
        for v in range(12):
            for k in range(7):
                u = u0 + k
                outer = (u == u0) if gutter != u0 else (u == u0 + 6)
                col = bone[3] if u == gutter else bone[4] if outer or v in (0, 11) else bone[5]
                if v in (1, 9, 10) and u != gutter and not outer and (u * 3 + v * 5) % 4:
                    col = bone[2] if (u + v) % 3 else ink[3]           # script, faded
                img.putpixel((u, v), col)
        rx = u0 + 1
        for r, row in enumerate(GRIMOIRE_RUNE):
            for c, ch in enumerate(row):
                if ch == "#":
                    img.putpixel((rx + c, 3 + r), bone[3])             # the rune, printed
    for v in range(16):                                                # page edges (u 15)
        img.putpixel((15, v), bone[4] if v % 2 else bone[3])
    return img


def grimoire_glow(f):
    """The glowing overlay (8 frames): each rune pulses in soul blue, and a line of script writes itself in faint
    soul light, one letter a frame (left page's last line, right page's first)."""
    hc = RAMPS["hollowcy"]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pulse = hc[[3, 4, 5, 4, 3, 4, 5, 4][f]]
    for rx in (1, 9):
        for r, row in enumerate(GRIMOIRE_RUNE):
            for c, ch in enumerate(row):
                if ch == "#":
                    img.putpixel((rx + c, 3 + r), pulse)
    for (u0, v) in ((1, 10), (9, 1)):
        for k in range(min(f, 5)):
            u = u0 + k
            if (u * 3 + v * 5) % 4:
                img.putpixel((u, v), hc[3] if k < f - 1 else hc[5])
    return img


def lichs_grimoire_held():
    """The Lich's Grimoire in the hand, held open on the palm: two halves of sculk-black leather tipped up 22.5 degrees
    into a V, each carrying a block of bone-white pages with dark script and a soul rune that pulses while a line writes
    itself (glowing overlay); bone corner guards, a ridged spine with bone bands, a small skull capping the spine's far
    end, a crimson ribbon trailing from the near end, and souls - two blue, two crimson - rising from the gutter
    (glowing, flickering out of step). Built lying in the x-y plane, pages facing +z, spine along y: in the hand +y
    points ahead and +z up, so the book lies open on the palm; first person tips it up toward the eye."""
    m = Model("lichs_phylactery_held")
    m.part = True
    sk, bone, cr, hc = RAMPS["sculk"], RAMPS["bone"], RAMPS["crimson"], RAMPS["hollowcy"]
    leather = blank()
    for y in range(16):
        for x in range(16):
            leather.putpixel((x, y), sk[2] if x in (0, 15) or y in (0, 15) else sk[1] if (x * 2 + y) % 7 else sk[0])
    t_leather = m.texture("leather", leather)
    t_pages = m.texture("pages", grimoire_pages())
    t_glow = m.texture("glow", [grimoire_glow(f) for f in range(8)])
    t_bone = m.texture("bone", fill(bone, 4))
    t_bone_dark = m.texture("bone_dark", fill(bone, 3))
    t_ribbon = m.texture("ribbon", fill(cr, 2))
    skull = blank()
    for y in range(16):
        for x in range(16):
            skull.putpixel((x, y), bone[4] if y < 9 else bone[3])
    for (x, y) in ((3, 6), (4, 6), (3, 7), (4, 7), (11, 6), (12, 6), (11, 7), (12, 7), (7, 10), (8, 10)):
        skull.putpixel((x, y), sk[0])                                  # sockets, nose
    for x in range(4, 12, 2):
        skull.putpixel((x, 13), sk[0])                                 # teeth
    t_skull = m.texture("skull", skull)
    motes = [m.texture(f"soul{i}", [fill(ramp, [2, 3, 4, 5, 5, 4, 3, 2][(f + 2 * i) % 8]) for f in range(8)])
             for i, ramp in enumerate((hc, cr, hc, cr))]
    pivot = [8.0, 8.0, 6.3]

    def half(sign):
        """One half of the open book; sign -1 the left (x < 8), +1 the right."""
        lo = (lambda a, b: (8 - b, 8 - a)) if sign < 0 else (lambda a, b: (8 + a, 8 + b))  # noqa: E731
        uv0 = 0 if sign < 0 else 8
        els = []
        x0, x1 = lo(0.0, 7.5)
        els.append(m.box((x0, 1.5, 5.8), (x1, 14.5, 6.3), {d: (t_leather, [0, 0, 8, 13] if d in ("north", "south") else [0, 0, 1, 13])
                                                            for d in ("north", "south", "east", "west")} |
                         {"up": (t_leather, [0, 0, 8, 1]), "down": (t_leather, [0, 0, 8, 1])}))          # the cover
        x0, x1 = lo(0.0, 7.0)
        els.append(m.box((x0, 2.0, 6.3), (x1, 14.0, 7.7), {"south": (t_pages, [uv0, 0, uv0 + 7, 12]),
                         "east": (t_pages, [15, 0, 16, 12]), "west": (t_pages, [15, 0, 16, 12]),
                         "up": (t_pages, [15, 0, 16, 7]), "down": (t_pages, [15, 0, 16, 7])}))         # the pages
        els.append(m.box((x0, 2.0, 7.72), (x1, 14.0, 7.72), {"south": (t_glow, [uv0, 0, uv0 + 7, 12])}, shade=False,
                         light=15))                                                                  # runes and script
        for y in (1.3, 13.5):                                                                         # corner guards
            cx0, cx1 = lo(6.3, 7.7)
            els.append(m.box((cx0, y, 5.6), (cx1, y + 1.2, 6.5), {d: (t_bone, [0, 0, 1, 1]) for d in FACES_ALL}))
        for e in els:
            e["rotation"] = {"origin": pivot, "axis": "y", "angle": 22.5 if sign < 0 else -22.5}

    half(-1)
    half(+1)
    m.box((7.1, 1.5, 5.5), (8.9, 14.5, 6.3), {d: (t_leather, [0, 0, 2, 13]) for d in FACES_ALL})  # the spine
    for y in (3.5, 7.4, 11.3):                                                                       # bone bands
        m.box((6.9, y, 5.3), (9.1, y + 0.8, 6.2), {d: (t_bone_dark, [0, 0, 1, 1]) for d in FACES_ALL})
    m.box((6.9, 14.5, 5.0), (9.1, 16.3, 7.0), {"up": (t_skull, [2, 2, 14, 14]), "north": (t_bone, [0, 0, 2, 2]),
          "south": (t_bone, [0, 0, 2, 2]), "east": (t_bone, [0, 0, 2, 2]), "west": (t_bone, [0, 0, 2, 2]),
          "down": (t_bone, [0, 0, 2, 2])})                                                          # skull on the spine
    m.box((7.7, -1.8, 5.9), (8.3, 1.5, 6.1), {d: (t_ribbon, [0, 0, 1, 3]) for d in FACES_ALL})       # the ribbon
    for (x, y, z), t in zip(((7.4, 6.0, 8.6), (8.7, 9.2, 9.6), (7.7, 11.0, 10.9), (8.4, 7.6, 12.0)), motes):
        m.box((x - 0.35, y - 0.35, z - 0.35), (x + 0.35, y + 0.35, z + 0.35), {d: (t, [0, 0, 1, 1]) for d in FACES_ALL},
              shade=False, light=15)                                                                # rising souls
    fp = {"firstperson_righthand": {"rotation": [-50, -10, 0], "translation": [0.0, 3.5, -1.5], "scale": [0.55] * 3},
          "firstperson_lefthand": {"rotation": [-50, 10, 0], "translation": [0.0, 3.5, -1.5], "scale": [0.55] * 3}}
    # third person: lying flat on the palm, pages up (tipped, its cover faced whoever stood in front), smaller, and
    # held by its inner half so it sits out beside the hip instead of in it (+x is outward from the body)
    m.display = grip_display((0, 0, 0), (4.5, 8, 5.5), 0.55, first_person=fp)
    return m


def bone_scepter_held():
    """The Bone Scepter in the hand: a staff of stacked vertebrae - knobbed discs with little spurs - topped by a
    skull whose sockets burn with soul-green fire (glowing, animated), a wisp curling up from its crown. The skull
    looks where the scepter points."""
    m = Model("bone_scepter_held")
    m.part = True
    bone, gel, ink = RAMPS["bone"], RAMPS["gel"], RAMPS["ink"]
    t_bone = m.texture("bone", bone_tex(671, tone=4))
    t_dark = m.texture("bone_dark", bone_tex(673, tone=3))
    face_frames = []
    for f in range(6):
        face = bone_tex(675, tone=4)
        glow = gel[[3, 4, 5, 4, 3, 4][f]]
        for (x0, x1) in ((3, 7), (9, 13)):                  # sockets
            for y in range(4, 9):
                for x in range(x0, x1):
                    face.putpixel((x, y), ink[0])
            put(face, [(x0 + 1, 6), (x0 + 2, 6), (x0 + 1, 7), (x0 + 2, 7)], glow)
        put(face, [(7, 10), (8, 10), (7, 11), (8, 11)], ink[1])   # the nose
        for x in range(3, 13):                              # teeth
            face.putpixel((x, 13), bone[5] if x % 2 else ink[1])
        face_frames.append(face)
    t_face = m.texture("face", face_frames)
    t_wisp = m.texture("wisp", fill(gel, 4))
    prism(m, 2.2, -3, -1.6, t_dark)                         # a knob at the foot
    y = -1.6
    while y < 11.5:                                         # the vertebrae
        prism(m, 2.2, y, y + 1.0, t_bone)
        prism(m, 1.4, y + 1.0, y + 1.6, t_dark)
        y += 1.6
    for yy in (2.0, 6.8):                                    # spurs
        prism(m, 3.6, yy, yy + 0.6, t_dark, d=0.8)
    # the skull, looking where the scepter points. Held in vanilla's sword pose the model's +y (its tip) points
    # ahead and its +x points up (worked out from the 26.2 client's hand transforms), so the face goes on the skull's
    # +y side, turned so its brow is toward +x; the cranium's crown is toward +x too.
    face_up = [f.rotate(-90) for f in face_frames]                # brow toward +x on an up face
    t_face_up = m.texture("face_up", face_up)
    m.box((5.4, 12.0, 5.4), (10.6, 17.2, 10.6), {"up": (t_face_up, [2, 2, 14, 14]), "west": (t_bone, [0, 0, 5, 5]),
          "north": (t_bone, [0, 0, 5, 5]), "south": (t_bone, [0, 0, 5, 5]), "east": (t_bone, [0, 0, 5, 5]),
          "down": (t_bone, [0, 0, 5, 5])})
    m.box((6.2, 17.22, 5.8), (9.8, 17.22, 10.2), {"up": (t_face_up, [4, 3, 12, 13])}, shade=False, light=13)   # sockets glow
    prism(m, 4.0, 11.2, 12.0, t_dark, cx=7.4)               # where the skull meets the staff
    for k in range(4):                                      # a wisp curling up from the crown (+x is up)
        m.box((10.6 + k * 0.8, 14.0 + [0.4, 0.9, 0.5, 0.0][k], 7.6), (11.4 + k * 0.8, 14.8 + [0.4, 0.9, 0.5, 0.0][k], 8.4),
              {d: (t_wisp, [0, 0, 1, 1]) for d in FACES_ALL}, light=15, shade=False)
    m.display = HANDHELD_DISPLAY
    return diagonal(m)


def occult_codex_held():
    """The Occult Codex in the hand, after Iron's Spells' books: two thick leather covers overhanging a block of bone
    pages, a rounded spine, iron corner guards, an iron clasp across the fore-edge, and the ember jewel on the cover
    (glowing, pulsing). Lies in the x-y plane like a flat item, so it is held as vanilla holds a book."""
    m = Model("occult_codex_held")
    m.part = True
    le, ir, bone, em = RAMPS["leather"], RAMPS["iron"], RAMPS["bone"], RAMPS["ember"]
    cover = blank()
    for y in range(16):
        for x in range(16):
            cover.putpixel((x, y), le[3] if (x * 3 + y * 5) % 11 else le[2])
    rim(cover, le[4], le[1])
    for i in range(2, 14):   # a tooled border
        cover.putpixel((i, 2), le[1]); cover.putpixel((i, 13), le[1]); cover.putpixel((2, i), le[1]); cover.putpixel((13, i), le[1])
    t_cover = m.texture("cover", cover)
    pages = blank()
    for y in range(16):
        for x in range(16):
            pages.putpixel((x, y), bone[4] if y % 2 else bone[3])
    t_pages = m.texture("pages", pages)
    t_iron = m.texture("iron", metal(ir, 641, tone=3))
    jewels = [fill(em, [3, 4, 5, 4, 3, 2][f]) for f in range(6)]
    t_jewel = m.texture("jewel", jewels)
    # covers (front +z, back -z), pages between, the spine on the left
    m.cube((3, 1, 9.4), (13.6, 15, 10.6), t_cover)
    m.cube((3, 1, 5.4), (13.6, 15, 6.6), t_cover)
    m.box((3.6, 1.6, 6.6), (13.0, 14.4, 9.4), {"east": (t_pages, [0, 0, 3, 13]), "up": (t_pages, [0, 0, 9, 3]),
                                                "down": (t_pages, [0, 0, 9, 3])})
    m.cube((2.2, 1, 6.0), (3.4, 15, 10.0), (t_cover, [0, 0, 4, 14]))   # the spine
    m.cube((1.8, 2.5, 6.6), (2.4, 13.5, 9.4), (t_cover, [0, 0, 3, 11]))
    for (y0, y1) in ((1, 2.6), (13.4, 15)):                  # corner guards on the fore-edge corners
        for z0, z1 in ((10.4, 10.9), (5.1, 5.6)):
            m.cube((11.8, y0, z0), (13.9, y1, z1), (t_iron, [0, 0, 2, 2]))
    m.cube((12.8, 7, 5.2), (14.2, 9, 10.8), (t_iron, [0, 0, 2, 2]))   # the clasp across the fore-edge
    m.box((7.0, 6.6, 10.6), (9.6, 9.4, 11.3), {d: (t_jewel, [0, 0, 3, 3]) for d in FACES_ALL}, light=15, shade=False)
    m.cube((6.6, 6.2, 10.6), (10.0, 9.8, 10.9), (t_iron, [0, 0, 3, 3]))   # its setting
    m.display = GENERATED_DISPLAY
    return m


SHIELD_DISPLAY = {   # vanilla item/shield
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
    "fixed": {"rotation": [0, 180, 0], "translation": [-4.5, 4.5, -5], "scale": [0.55, 0.55, 0.55]},
    "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25, 0.25, 0.25]},
}
SHIELD_BLOCKING_DISPLAY = {   # vanilla item/shield_blocking
    "thirdperson_righthand": {"rotation": [45, 155, 0], "translation": [-3.49, 11, -2], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [45, 155, 0], "translation": [11.51, 7, 2.5], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
}


def heartwood_aegis(blocking=False):
    """The Heartwood Aegis (vanilla: shield): vanilla's shield rebuilt as a plain model - the entity shield's plate
    (12x22x1) and handle (2x6x6) in the same place its renderer puts them - so the Session F texture (vanilla shield
    UV layout, 64x64, its regrowth rune animated) maps on unchanged, with vanilla's display (held and blocking)."""
    m = Model("heartwood_aegis_shield" + ("_blocking" if blocking else ""))
    m.part = True
    m.extra = {"gui_light": "front"}
    frames = []
    i = 0
    while os.path.exists(os.path.join(OUT, "..", "session-f", f"heartwood_aegis_shield_{i}.png")):
        frames.append(Image.open(os.path.join(OUT, "..", "session-f", f"heartwood_aegis_shield_{i}.png")).convert("RGBA"))
        i += 1
    wood = RAMPS["wood"]
    calm = []
    for fr in frames:   # the back (x 14..25, y 1..22) repainted calmer: dark vertical boards, soft grain, two bands
        fr = fr.copy()
        for y in range(1, 23):
            for x in range(14, 26):
                board = (x - 14) // 3
                t_ = 2 if board % 2 else 1
                if (x - 14) % 3 == 2:
                    t_ = 0
                elif (y * 2 + x) % 9 == 0:
                    t_ += 1
                if y in (6, 17):
                    t_ = 0
                fr.putpixel((x, y), wood[max(0, min(3, t_))])
        calm.append(fr)
    frames = calm
    t = m.texture("shield", frames)
    q = lambda x0, y0, x1, y1: (t, [x0 / 4, y0 / 4, x1 / 4, y1 / 4])  # noqa: E731  (64 px texture -> 16 uv units)
    # the plate: entity box (-6,-11,-2) size 12x22x1 at uv (0,0); its renderer flips y and z, so it sits at z 1..2
    m.box((-6, -11, 1), (6, 11, 2), {"south": q(1, 1, 13, 23), "north": q(14, 1, 26, 23), "up": q(1, 0, 13, 1),
                                      "down": q(13, 0, 25, 1), "west": q(0, 1, 1, 23), "east": q(13, 1, 14, 23)})
    # the handle: entity box (-1,-3,-1) size 2x6x6 at uv (26,0) -> z -5..1
    m.box((-1, -3, -5), (1, 3, 1), {"south": q(32, 6, 34, 12), "north": q(40, 6, 42, 12), "up": q(32, 0, 34, 6),
                                     "down": q(34, 0, 36, 6), "west": q(26, 6, 32, 12), "east": q(34, 6, 40, 12)})
    m.display = SHIELD_BLOCKING_DISPLAY if blocking else SHIELD_DISPLAY
    return m


G5 = [("Occult Codex (held)", occult_codex_held), ("Wyrmbreath (held)", wyrmbreath_held),
      ("Wyrmbreath (in use)", lambda: wyrmbreath_held(True)),
      ("Guardian's Gaze (held)", guardians_gaze_held), ("Guardian's Gaze (in use)", lambda: guardians_gaze_held(True)),
      ("Abyssal Anchor (held)", abyssal_anchor_held), 
      ("Lich's Grimoire (held)", lichs_grimoire_held), ("Dreadlance (held)", dreadlance_held), ("Soulfire Censer (held)", soulfire_censer_held), ("Soulfire Censer (in use)", lambda: soulfire_censer_held(True)),
      ("Frenzy Cleaver (held)", frenzy_cleaver_held), ("Bone Scepter (held)", bone_scepter_held),
      ("Heartwood Aegis", heartwood_aegis), ("Heartwood Aegis (blocking)", lambda: heartwood_aegis(True))]


# ================================================================== G6: worn armor. An equipment asset per set
# (assets/occultech/equipment/<set>.json) with a humanoid layer (helmet, chestplate, boots) and a humanoid_leggings
# layer, 64x32 each in vanilla's armor layout; the plugin points the armor items' `equippable` at it. Armor textures
# are entity textures: no animation, no glow. Written to docs/art/session-g/equipment/<set>/.

ARMOR_BOXES = {   # part: (u, v, w, h, d) - the player model's boxes in the armor texture
    "head": (0, 0, 8, 8, 8), "body": (16, 16, 8, 12, 4), "arm": (40, 16, 4, 12, 4), "leg": (0, 16, 4, 12, 4)}


def armor_faces():
    """Every face of every box: (part, face, x0, y0, w, h)."""
    out = []
    for part, (u, v, w, h, d) in ARMOR_BOXES.items():
        out += [(part, "top", u + d, v, w, d), (part, "bottom", u + d + w, v, w, d), (part, "right", u, v + d, d, h),
                (part, "front", u + d, v + d, w, h), (part, "left", u + d + w, v + d, d, h), (part, "back", u + 2 * d + w, v + d, w, h)]
    return out


# which piece covers what: layer, part, faces, rows of the side faces (0 = top of the box)
ARMOR_COVER = {
    "helmet":   ("humanoid", "head", ("top", "right", "front", "left", "back"), range(0, 8)),
    "chest":    ("humanoid", "body", ("top", "right", "front", "left", "back"), range(0, 12)),
    "arms":     ("humanoid", "arm", ("top", "right", "front", "left", "back"), range(0, 6)),
    "boots":    ("humanoid", "leg", ("bottom", "right", "front", "left", "back"), range(7, 12)),
    "waist":    ("humanoid_leggings", "body", ("right", "front", "left", "back"), range(8, 12)),
    "legs":     ("humanoid_leggings", "leg", ("top", "right", "front", "left", "back"), range(0, 9)),
}


def paint_armor(painter):
    """Both layers: painter(piece, part, face, u, v, w, h) -> colour or None, for every covered pixel."""
    layers = {"humanoid": Image.new("RGBA", (64, 32), (0, 0, 0, 0)), "humanoid_leggings": Image.new("RGBA", (64, 32), (0, 0, 0, 0))}
    faces = armor_faces()
    for piece, (layer, part, face_names, rows) in ARMOR_COVER.items():
        for (p_, face, x0, y0, w, h) in faces:
            if p_ != part or face not in face_names:
                continue
            for v in range(h):
                if face not in ("top", "bottom") and v not in rows:
                    continue
                for u in range(w):
                    c = painter(piece, part, face, u, v, w, h)
                    if c is not None:
                        layers[layer].putpixel((x0 + u, y0 + v), c)
    return layers


# ================================================================== G6 v3: worn armor.
# Helmets are worn as 3D item models (an equippable with no asset makes the game draw the head item's model, context
# "head", as it draws a carved pumpkin); chestplates add 3D back pieces on the equipment asset's "wings" layer (the
# elytra's wings); bodies, legs and boots are equipment textures (64x32, vanilla layout). Vanilla packs can't add
# geometry anywhere else (shoulder plates and the like need a client mod).

HEAD_DISPLAY = {"head": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}


ELYTRA_FRONT, ELYTRA_BACK = (24, 2), (36, 2)   # a wing's two broad faces (10 x 20) in the elytra texture


def wings_tex(shape):
    """A wings texture (64x32, the elytra layout): shape(u, v) -> colour or None for a 10x20 wing face, drawn on both
    broad faces (mirrored on the back) and on the edges and top where the shape reaches them."""
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    for v in range(20):
        for u in range(10):
            c = shape(u, v)
            if c is None:
                continue
            img.putpixel((ELYTRA_FRONT[0] + u, ELYTRA_FRONT[1] + v), c)
            img.putpixel((ELYTRA_BACK[0] + 9 - u, ELYTRA_BACK[1] + v), c)
    for v in range(20):   # the thin edges
        if shape(0, v) is not None:
            img.putpixel((34, 2 + v), shape(0, v)); img.putpixel((35, 2 + v), shape(0, v))
        if shape(9, v) is not None:
            img.putpixel((22, 2 + v), shape(9, v)); img.putpixel((23, 2 + v), shape(9, v))
    for u in range(10):
        if shape(u, 0) is not None:
            img.putpixel((24 + u, 0), shape(u, 0)); img.putpixel((24 + u, 1), shape(u, 0))
    return img


# ---------------------------------------------------------------- G6 v3: clean, art-directed armor textures
# Lessons (Sessions A/B, STYLE.md): bold shapes; one light from the top-left - every plate a bevel (lit top-left edge,
# shadowed bottom-right), 3-5 ramp steps, no noise; dark gaps between plates in the material's own darkest tones;
# dark vessel, living light - the bodies are dark and calm, the accent (sea glow / hollow cyan) only on gems and
# glowing inlay; hard facets on gems. References studied: clean-plated sea armor (layered plates, crisp highlights),
# crystal armor (spikes), a shaman set (carved mask, crystals, cloth panels).

class ArmorCanvas:
    """The two worn layers, drawn face by face in face-local coordinates (u right, v down)."""

    def __init__(self):
        self.layers = {"humanoid": Image.new("RGBA", (64, 32), (0, 0, 0, 0)),
                       "humanoid_leggings": Image.new("RGBA", (64, 32), (0, 0, 0, 0))}
        self.rects = {(p, f): (x0, y0, w, h) for (p, f, x0, y0, w, h) in armor_faces()}

    def face(self, layer, part, face):
        x0, y0, w, h = self.rects[(part, face)]
        return (self.layers[layer], x0, y0, w, h)

    @staticmethod
    def px(F, u, v, c):
        img, x0, y0, w, h = F
        if 0 <= u < w and 0 <= v < h and c is not None:
            img.putpixel((x0 + u, y0 + v), c)

    def rect(self, F, u0, v0, u1, v1, c):
        for v in range(v0, v1 + 1):
            for u in range(u0, u1 + 1):
                self.px(F, u, v, c)

    def plate(self, F, u0, v0, u1, v1, ramp, tone=3):
        """A bevelled plate: lit top and left edges (the top-left corner brightest), shadowed bottom and right."""
        for v in range(v0, v1 + 1):
            for u in range(u0, u1 + 1):
                t = tone
                if v == v0 or u == u0:
                    t = tone + 1
                if v == v1 or u == u1:
                    t = tone - 1
                if (u, v) == (u0, v0):
                    t = tone + 2
                self.px(F, u, v, ramp[max(0, min(len(ramp) - 1, t))])

    def gem(self, F, u0, v0, u1, v1, ramp):
        """A cut gem with hard facets: a lit left face, a dark right face, a bright seam at the top-left."""
        mid = (u0 + u1) / 2
        for v in range(v0, v1 + 1):
            for u in range(u0, u1 + 1):
                t = 4 if u < mid else 2
                if v == v1:
                    t -= 1
                self.px(F, u, v, ramp[t])
        self.px(F, u0, v0, ramp[5])

    def inlay(self, F, pts, glow):
        """Glowing inlay: a raised tube of light - bright core, its ends dimmer, one hot pixel."""
        for i, (u, v) in enumerate(pts):
            self.px(F, u, v, glow[3] if i in (0, len(pts) - 1) else glow[4])
        if pts:
            self.px(F, *pts[len(pts) // 2], glow[5])

    def scales(self, F, u0, v0, u1, v1, ramp):
        """Small overlapping scales, cleanly: each a 2 px arc lit on its top, dark beneath (no noise)."""
        for v in range(v0, v1 + 1):
            for u in range(u0, u1 + 1):
                row = (v - v0) // 2
                lit = (v - v0) % 2 == 0 and (u + row) % 2 == 0
                self.px(F, u, v, ramp[3] if lit else ramp[2] if (v - v0) % 2 == 0 else ramp[1])


def abyssal_armor():
    """Abyssal, worn - plated like a deep-sea predator: layered teal plates over dark scales. Breastplate of two lit
    pectoral plates over banded abdominal plates, a sea-glow orb set at the heart; a spine of stacked plates behind;
    layered pauldrons and bracers; segmented thigh plates and knee cops with sea-glow studs; plated boots with a
    glowing toe line and a heel fin. Back fins on the wings layer."""
    ab0, sg, ir = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["iron"]
    ab = ab0
    dark = [ab0[0], ab0[1], ab0[2], ab0[2], ab0[3], ab0[3]]   # the scales between plates stay dark: the plates read
    c = ArmorCanvas()
    H, L = "humanoid", "humanoid_leggings"
    # ---- chestplate: body
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "body", face)
        c.scales(F, 0, 0, F[3] - 1, 11, dark)
    F = c.face(H, "body", "front")
    c.plate(F, 0, 0, 3, 4, ab, 4); c.plate(F, 4, 0, 7, 4, ab, 4)          # pectorals
    for i, v in enumerate((5, 7, 9)):                                     # abdominal bands, narrowing
        c.plate(F, 1 + i // 2, v, 6 - i // 2, v + 1, ab, 4)
    c.rect(F, 0, 11, 7, 11, ab[0])                                        # under the belt line
    c.gem(F, 3, 2, 4, 3, sg)                                               # the sea-glow heart
    c.inlay(F, [(1, 4), (2, 4)], sg); c.inlay(F, [(5, 4), (6, 4)], sg)    # glow under the pectorals
    F = c.face(H, "body", "back")
    for v in range(0, 11, 2):                                             # the spine of stacked plates
        c.plate(F, 3, v, 4, v + 1, ab, 4)
    c.plate(F, 0, 0, 2, 3, ab, 4); c.plate(F, 5, 0, 7, 3, ab, 4)          # shoulder blades
    for face in ("right", "left"):
        F = c.face(H, "body", face)
        c.plate(F, 0, 0, 3, 3, ab, 4); c.plate(F, 0, 5, 3, 6, ab, 3)
    F = c.face(H, "body", "top")
    c.plate(F, 0, 0, 7, 3, ab, 4)
    # ---- chestplate: arms - pauldron (layered), scales, bracer
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        c.scales(F, 0, 0, 3, 11, dark)
        c.plate(F, 0, 0, 3, 2, ab, 4); c.plate(F, 0, 3, 3, 4, ab, 4)      # pauldron, two layers
        c.plate(F, 0, 8, 3, 10, ab, 4)                                    # bracer
        c.rect(F, 0, 11, 3, 11, ab[1])
    c.inlay(c.face(H, "arm", "front"), [(1, 9), (2, 9)], sg)
    c.plate(c.face(H, "arm", "top"), 0, 0, 3, 3, ab, 4)
    # ---- boots
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "leg", face)
        c.plate(F, 0, 7, 3, 9, ab, 4)
        c.plate(F, 0, 10, 3, 11, ab, 3)
    c.inlay(c.face(H, "leg", "front"), [(0, 10), (1, 10), (2, 10), (3, 10)], sg)   # glowing toe line
    F = c.face(H, "leg", "back")
    c.rect(F, 1, 7, 2, 9, ab[4]); c.px(F, 1, 7, ab[5])                   # heel fin
    c.rect(c.face(H, "leg", "bottom"), 0, 0, 3, 3, ab[1])
    # ---- leggings: belt and tassets, thigh plates, knee cops, shin scales
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        c.rect(F, 0, 8, F[3] - 1, 8, ir[2]); c.px(F, 0, 8, ir[4])           # belt
        c.plate(F, 0, 9, F[3] - 1, 11, ab, 4)                              # tassets
        G = c.face(L, "leg", face)
        c.scales(G, 0, 0, 3, 8, dark)
        c.plate(G, 0, 0, 3, 2, ab, 4); c.plate(G, 0, 3, 3, 3, ab, 3)        # thigh plates, layered
        c.plate(G, 0, 7, 3, 8, ab, 3)
    c.gem(c.face(L, "body", "front"), 3, 9, 4, 10, sg)                     # belt buckle gem
    F = c.face(L, "leg", "front")
    c.plate(F, 0, 4, 3, 6, ab, 4); c.gem(F, 1, 5, 2, 5, sg)               # knee cop with its stud
    c.plate(c.face(L, "leg", "top"), 0, 0, 3, 3, ab, 3)
    layers = c.layers
    layers["wings"] = abyssal_wings()
    return layers


def hollow_armor():
    """Hollow, worn - a shaman of the sculk, half sorcery, half machine: robes of dark violet cloth marked with
    glowing hollow-cyan runes; carved old-bone plaques over the chest, round a cut cyan crystal heart; aged gold
    clasps and trim; bone pauldrons with crystal facets, cloth-wrapped sleeves and bone bracers; a skirt of cloth panels
    with rune marks and a gold-trimmed hem, a sash with a crimson gem; wrapped boots with bone toe caps. Crystal vanes
    on the wings layer."""
    ink, vi, bone, gd, hc, cr = RAMPS["ink"], RAMPS["violet"], RAMPS["bone"], RAMPS["gold"], RAMPS["hollowcy"], RAMPS["crimson"]
    cloth = [ink[1], ink[2], ink[3], vi[2], vi[3], vi[4]]                 # dark violet cloth
    c = ArmorCanvas()
    H, L = "humanoid", "humanoid_leggings"

    def robe(F, v0, v1):
        """Cloth: soft vertical folds (a lit fold every 3 px), a little darker at the bottom."""
        for v in range(v0, v1 + 1):
            for u in range(F[3]):
                t = 3 if u % 3 == 0 else 2 if u % 3 == 1 else 1
                if v == v1:
                    t -= 1
                c.px(F, u, v, cloth[max(0, t)])

    # ---- chestplate: body
    for face in ("front", "back", "right", "left"):
        robe(c.face(H, "body", face), 0, 11)
    F = c.face(H, "body", "front")
    c.plate(F, 0, 0, 2, 2, bone, 3); c.plate(F, 5, 0, 7, 2, bone, 3)      # carved bone plaques at the collar
    c.plate(F, 1, 7, 2, 8, bone, 3); c.plate(F, 5, 7, 6, 8, bone, 3)
    c.rect(F, 2, 3, 5, 6, gd[2])                                          # the crystal's gold setting
    c.px(F, 2, 3, gd[4]); c.px(F, 5, 6, gd[1])
    c.gem(F, 3, 3, 4, 5, hc)                                               # cut cyan crystal heart
    c.inlay(F, [(3, 9), (4, 10), (3, 11)], hc)                             # a rune below it
    c.rect(F, 0, 11, 7, 11, gd[2]); c.px(F, 0, 11, gd[4])
    F = c.face(H, "body", "back")
    for v in (1, 4, 7):
        c.plate(F, 3, v, 4, v + 1, bone, 3)                                # bone spine plaques
    c.inlay(F, [(1, 2), (1, 3), (2, 4), (1, 5)], hc); c.inlay(F, [(6, 2), (6, 3), (5, 4), (6, 5)], hc)   # runes
    c.rect(F, 0, 11, 7, 11, gd[2])
    for face in ("right", "left"):
        F = c.face(H, "body", face)
        c.plate(F, 0, 0, 3, 1, bone, 3)
        c.rect(F, 0, 11, 3, 11, gd[2])
    c.plate(c.face(H, "body", "top"), 0, 0, 7, 3, cloth, 3)
    # ---- arms: bone pauldron with a crystal facet, wrapped sleeve, gold band, bone bracer
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        robe(F, 0, 11)
        c.plate(F, 0, 0, 3, 2, bone, 4)
        c.rect(F, 0, 3, 3, 3, gd[3]); c.px(F, 0, 3, gd[4])
        for v in (5, 7):
            c.rect(F, 0, v, 3, v, cloth[1])                                # wraps
        c.plate(F, 0, 9, 3, 11, bone, 3)
    c.gem(c.face(H, "arm", "right"), 1, 0, 2, 1, hc); c.gem(c.face(H, "arm", "left"), 1, 0, 2, 1, hc)
    F = c.face(H, "arm", "top")
    c.plate(F, 0, 0, 3, 3, bone, 4); c.gem(F, 1, 1, 2, 2, hc)
    # ---- boots: wrapped, gold ankle band, bone toe caps
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "leg", face)
        robe(F, 7, 11)
        c.rect(F, 0, 7, 3, 7, gd[3]); c.px(F, 0, 7, gd[4])
    F = c.face(H, "leg", "front")
    c.plate(F, 0, 10, 3, 11, bone, 3)
    c.rect(c.face(H, "leg", "bottom"), 0, 0, 3, 3, ink[1])
    # ---- leggings: sash with a crimson gem, a skirt of rune-marked cloth panels, gold hem
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        c.rect(F, 0, 8, F[3] - 1, 9, gd[2]); c.rect(F, 0, 8, F[3] - 1, 8, gd[3])
        robe(F, 10, 11)
        G = c.face(L, "leg", face)
        robe(G, 0, 8)
        c.rect(G, 0, 8, 3, 8, gd[2])                                       # gold hem
    c.gem(c.face(L, "body", "front"), 3, 8, 4, 9, cr)                      # crimson gem on the sash
    for face in ("front", "back"):
        c.inlay(c.face(L, "leg", face), [(1, 2), (2, 3), (1, 4), (2, 5)], hc)   # rune marks down the panels
    for face in ("right", "left"):
        c.inlay(c.face(L, "leg", face), [(1, 3), (1, 4)], hc)
    c.plate(c.face(L, "leg", "top"), 0, 0, 3, 3, cloth, 3)
    layers = c.layers
    layers["wings"] = hollow_wings()
    return layers


def abyssal_wings():
    """The Abyssal back fins: each a fan of spines with membrane between them, swept out from the shoulder blade -
    the membrane a clean gradient (lit at the top), each spine a darker raised ray, the rim lit with sea glow."""
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]

    def shape(u, v):
        half = 5.2 * (1 - v / 21) ** 0.6
        d = abs(u + 0.5 - 5)
        if d > half + (0.8 if v % 5 == 0 else 0):
            return None
        if d > half - 0.6:
            return sg[3] if v % 5 == 0 else sg[2]                  # glowing rim, spine tips poke past it
        if (u - 5) * 5 == 0 or abs(u + 0.5 - 5) < 0.6:
            return ab[1]                                           # the central ray
        if v % 5 == 0:
            return ab[1]                                           # spines
        return ab[4] if v < 5 else ab[3] if v < 12 else ab[2]      # membrane, lit at the top
    return wings_tex(shape)


def hollow_wings():
    """The Hollow back vanes: a gold mount at the shoulder blade holding a cluster of long crystals - hard facets, the
    left face lit, the right dark, a bright seam - cyan in the middle, violet beside."""
    hc, vi, gd = RAMPS["hollowcy"], RAMPS["violet"], RAMPS["gold"]

    def shape(u, v):
        if v <= 1:
            return gd[4] if (v == 0 and u < 9) else gd[2]
        for (cx, top, length, ramp) in ((5.0, 2, 18, hc), (2.4, 2, 11, vi), (7.6, 3, 12, vi)):
            half = 1.7 * (1 - (v - top) / length)
            off = u + 0.5 - cx
            if top <= v < top + length and abs(off) <= half:
                if abs(off) < 0.5:
                    return ramp[5]                                 # the bright seam
                return ramp[4] if off < 0 else ramp[2]             # lit left face, dark right face
        return None
    return wings_tex(shape)


# ---------------------------------------------------------------- G6 v3 helms: clean 16 px textures
# The head spans model units 1.6..14.4 (1 head pixel = 1.6 units); the player's eyes sit at y 6.4..8.0 (row 4 of the
# face), the mouth at y 3.2..4.8 (row 6). Face toward -z (north).

def tex_plates(ramp, band=4, tone=3):
    """Clean horizontal plates, `band` px tall: each lit along its top edge and left end, shadowed at its bottom."""
    img = blank()
    for y in range(16):
        b = y % band
        for x in range(16):
            t = tone + 1 if b == 0 else tone - 1 if b == band - 1 else tone
            if x == 0 and b != band - 1:
                t += 1
            img.putpixel((x, y), ramp[max(0, min(len(ramp) - 1, t))])
    return img


def tex_smooth(ramp, tone=3):
    """A smooth sculpted surface: lit from the top-left, falling to shadow at the bottom-right (no noise)."""
    img = blank()
    for y in range(16):
        for x in range(16):
            s = (x + y) / 30
            t = tone + 1 if s < 0.22 else tone if s < 0.7 else tone - 1
            img.putpixel((x, y), ramp[t])
    return img


def tex_fin(ramp, rim):
    """A fin: membrane lit at the top fading down, darker rays between, a glowing rim along the top."""
    img = blank()
    for y in range(16):
        for x in range(16):
            ray = x % 4 == 0
            t = 4 if y < 4 else 3 if y < 10 else 2
            img.putpixel((x, y), ramp[1] if ray else ramp[t])
    for x in range(16):
        img.putpixel((x, 0), rim[3] if x % 4 else rim[4])
    return img


def tex_crystal(ramp, frames=8):
    """A crystal's faces: the left half lit, the right dark, a bright seam down the middle, a glint travelling up."""
    out = []
    for f in range(frames):
        img = blank()
        for y in range(16):
            for x in range(16):
                img.putpixel((x, y), ramp[5] if x in (7, 8) else ramp[4] if x < 7 else ramp[2])
        gy = 15 - (f * 2) % 16
        for x in range(16):
            if x not in (7, 8):
                img.putpixel((x, gy), ramp[5] if x < 7 else ramp[3])
        out.append(img)
    return out


def tex_cloth(ramp):
    """Cloth: soft vertical folds, a lit fold every 4 px."""
    img = blank()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), ramp[3] if x % 4 == 0 else ramp[2] if x % 4 in (1, 3) else ramp[1])
    return img


def tex_glow_lines(glow, lines, frames=6):
    """Emissive inlay lines (glowing tubes) on transparency, pulsing."""
    out = []
    for f in range(frames):
        img = blank()
        for i, line in enumerate(lines):
            for k, (x, y) in enumerate(line):
                lvl = [3, 4, 5, 4, 3, 2][(f + i) % 6]
                img.putpixel((x, y), glow[max(2, lvl - (1 if k in (0, len(line) - 1) else 0))])
        out.append(img)
    return out


def tex_fin_shape(ramp, rim, flip=False):
    """A fin's silhouette on transparency, drawn as a clean shape: three spines fanning from the root (bottom-left),
    each ending in a point; between them the edge curves in smoothly. Two membrane tones (darker toward the root),
    each spine a continuous darker line, a glowing rim along the edge."""
    spines = [math.radians(a) for a in (16, 50, 84)]
    gap = (spines[1] - spines[0]) / 2
    img = blank()
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5, 15.5 - y
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            if th < spines[0] - 0.15 or th > spines[-1] + 0.15:
                continue
            d = min(abs(th - a) for a in spines) / gap
            edge = 15.4 - 5.0 * min(1.0, d) ** 1.3
            if r > edge:
                continue
            on_spine = min(abs(r * math.sin(th - a)) for a in spines) < 0.55   # distance to the ray, in px
            if r > edge - 1.0:
                c = rim[4] if on_spine else rim[3]
            elif on_spine:
                c = ramp[1]
            else:
                c = ramp[3] if r > 7 else ramp[2]
            img.putpixel((x, 15 - y if flip else y), c)
    return img


def fin_plane(m, tex, x, y0, y1, z0, z1, light=0):
    """A fin as a two-sided plane in the y-z plane at x (its silhouette from the texture's transparency)."""
    m.box((x, y0, z0), (x, y1, z1), {"west": (tex, [0, 0, 16, 16]), "east": (tex, [16, 0, 0, 16])}, shade=True, light=light)


def abyssal_helm_worn():
    """The Abyssal Helm worn: a sea-monster mask - a sculpted teal helm whose face is a mask with a T-shaped visor (the
    wearer's eyes and mouth show through the T), bone fangs lining the mouth slit like a predator's jaw, a heavy brow
    with two small glowing eyes at its corners, glowing gill marks on the cheeks; layered fan fins sweeping back from
    the temples and a tall dorsal crest from brow to nape."""
    m = Model("abyssal_helmet_head")
    m.part = True
    ab, sg, bone = RAMPS["abyss"], RAMPS["seaglow"], RAMPS["bone"]
    t_shell = m.texture("shell", tex_plates(ab, band=4, tone=3))
    t_mask = m.texture("mask", tex_smooth(ab, tone=3))
    t_brow = m.texture("brow", tex_smooth(ab, tone=4))
    t_fin = m.texture("fin", tex_fin_shape(ab, sg))
    t_fin_down = m.texture("fin_down", tex_fin_shape(ab, sg, flip=True))
    t_tooth = m.texture("tooth", tex_smooth(bone, tone=3))
    t_gill = m.texture("gills", tex_glow_lines(sg, [[(2, y), (3, y), (4, y), (5, y), (6, y)] for y in (4, 7, 10)]))
    t_eye = m.texture("eye", [fill(sg, [3, 4, 5, 5, 4, 3][f]) for f in range(6)])
    T = lambda t, w, h: (t, [0, 0, max(1, min(16, round(w))), max(1, min(16, round(h)))])  # noqa: E731
    # the helm: crown, back, sides
    m.cube((0.6, 14.6, 0.6), (15.4, 16.0, 15.6), T(t_shell, 15, 2), top=T(t_mask, 15, 15))
    m.cube((2.2, 16.0, 2.2), (13.8, 16.8, 14.4), T(t_mask, 12, 1), top=T(t_mask, 12, 12))
    m.cube((0.6, 0.8, 14.6), (15.4, 14.6, 16.0), T(t_shell, 15, 14))
    for x0 in (0.0, 14.6):
        m.cube((x0, 0.8, 0.6), (x0 + 1.4, 14.6, 14.6), T(t_shell, 14, 14))
    # the mask, round a T: eye slit y 6.2..8.2 across x 2.6..13.4, mouth slit x 7.0..9.0 from y 2.0
    for (a, b) in (((0.6, 8.2, -0.2), (15.4, 14.6, 1.2)),          # forehead
                   ((0.6, 6.2, -0.2), (2.6, 8.2, 1.2)), ((13.4, 6.2, -0.2), (15.4, 8.2, 1.2)),   # beside the eye slit
                   ((0.6, 0.8, -0.2), (7.0, 6.2, 1.2)), ((9.0, 0.8, -0.2), (15.4, 6.2, 1.2)),     # cheeks
                   ((7.0, 0.8, -0.2), (9.0, 2.0, 1.2))):                                           # chin
        m.cube(a, b, T(t_mask, b[0] - a[0], b[1] - a[1]))
    m.cube((0.4, 8.2, -1.0), (15.6, 9.6, -0.2), T(t_brow, 15, 2), top=T(t_brow, 15, 2))            # heavy brow
    m.cube((5.6, 9.6, -0.8), (10.4, 11.4, -0.2), T(t_brow, 5, 2), top=T(t_brow, 5, 2))             # its central ridge
    for x in (0.6, 14.2):                                                                           # small glowing eyes
        m.box((x, 9.0, -1.2), (x + 1.2, 10.0, -0.9), {d: (t_eye, [0, 0, 1, 1]) for d in FACES_ALL}, light=15, shade=False)
    for (x, y, ln) in ((6.2, 5.0, 1.0), (6.2, 3.2, 1.2), (6.2, 2.0, 0.8)):                         # fangs lining the mouth slit
        m.cube((x, y, -0.6), (x + 0.8, y + ln, 0.2), T(t_tooth, 1, 2))
        m.cube((16 - x - 0.8, y + 0.4, -0.6), (16 - x, y + ln + 0.4, 0.2), T(t_tooth, 1, 2))
    m.box((1.0, 1.4, -0.25), (6.6, 6.0, -0.25), {"north": (t_gill, [0, 2, 8, 12])}, shade=False, light=15)   # gill marks
    m.box((9.4, 1.4, -0.25), (15.0, 6.0, -0.25), {"north": (t_gill, [8, 2, 0, 12])}, shade=False, light=15)
    # layered fan fins sweeping back and up from each temple (three, each larger and further back)
    for side in (0, 1):
        for (y0, y1, z0, z1, xo) in ((6.0, 15.0, 2.0, 11.0, 0.3), (8.0, 19.0, 5.0, 16.0, 0.9), (10.0, 23.0, 8.0, 21.0, 1.5)):
            fin_plane(m, t_fin, -xo if side == 0 else 16 + xo, y0, y1, z0, z1)
        fin_plane(m, t_fin_down, -0.4 if side == 0 else 16.4, -3.0, 4.0, 1.0, 8.0)                    # a cheek fin, hanging
    # the dorsal crest, rising from the brow and sweeping back over the crown
    fin_plane(m, t_fin, 8.0, 15.8, 30.0, -1.0, 19.0)
    m.cube((7.4, 15.8, -1.0), (8.6, 17.0, 16.0), T(t_brow, 1, 16), top=T(t_brow, 1, 16))           # the crest's root
    m.display = HEAD_DISPLAY
    return m


def hollow_helm_worn():
    """The Hollow Crown worn - a sculk shaman's mask: a hood of dark violet cloth bound by an aged-gold circlet; over
    the face a mask of carved old bone - heavy brow, nose ridge, cheekbones, eye holes (the wearer's eyes show), glowing
    hollow-cyan markings running from the eyes - with a faceted crimson gem on the brow; bone horns sweeping out, up and
    back, ringed in gold; a cluster of hollow-cyan crystals rising from the crown with lightning crackling between them
    and the horn tips (animated, glowing); a tassel of rune beads hanging behind."""
    m = Model("hollow_helmet_head")
    m.part = True
    ink, vi, bone, gd, hc, cr = RAMPS["ink"], RAMPS["violet"], RAMPS["bone"], RAMPS["gold"], RAMPS["hollowcy"], RAMPS["crimson"]
    cloth = [ink[1], ink[2], ink[3], vi[2], vi[3], vi[4]]
    t_cloth = m.texture("cloth", tex_cloth(cloth))
    t_bone = m.texture("bone", tex_smooth(bone, tone=3))
    t_bone_lit = m.texture("bone_lit", tex_smooth(bone, tone=4))
    t_horn = m.texture("horn", tex_plates(bone, band=3, tone=3))
    t_gold = m.texture("gold", tex_smooth(gd, tone=3))
    t_crystal = m.texture("crystal", tex_crystal(hc))
    gem = blank()
    for y in range(16):
        for x in range(16):
            gem.putpixel((x, y), cr[5] if x < 3 and y < 3 else cr[4] if x < 8 else cr[2])
    t_gem = m.texture("gem", gem)
    marks = [[(4, y) for y in range(6, 14)], [(11, y) for y in range(6, 14)], [(3, 13), (5, 13)], [(10, 13), (12, 13)]]
    t_marks = m.texture("marks", tex_glow_lines(hc, marks))
    bolts = []
    for f in range(6):
        b = blank()
        rnd = random.Random(741 + f)
        y = 8
        for x in range(16):
            y = max(2, min(13, y + rnd.choice((-2, -1, 0, 1, 2))))
            b.putpixel((x, y), (255, 255, 255, 255)); b.putpixel((x, y + 1), hc[4])
            if rnd.random() < 0.2:
                b.putpixel((x, max(0, y - 2)), hc[3])
        bolts.append(b)
    t_bolt = m.texture("bolt", bolts)
    beads = blank()
    for y in range(16):
        for x in range(6, 10):
            beads.putpixel((x, y), hc[4] if y % 4 == 0 else cloth[2])
    t_beads = m.texture("beads", beads)
    T = lambda t, w, h: (t, [0, 0, max(1, min(16, round(w))), max(1, min(16, round(h)))])  # noqa: E731
    # the hood
    m.cube((0.6, 14.6, 0.6), (15.4, 16.2, 15.6), T(t_cloth, 15, 2), top=T(t_cloth, 15, 15))
    m.cube((0.6, 0.4, 14.6), (15.4, 14.6, 16.2), T(t_cloth, 15, 14))
    for x0 in (-0.2, 14.8):
        m.cube((x0, 0.4, 1.0), (x0 + 1.4, 14.6, 14.6), T(t_cloth, 14, 14))
    m.cube((-0.4, 12.4, 0.8), (16.4, 13.8, 15.8), T(t_gold, 16, 2))                                 # gold circlet
    # the bone mask: eye holes at x 3.2..6.4 and 9.6..12.8, y 6.4..8.0
    for (a, b) in (((0.6, 8.0, -0.4), (15.4, 12.4, 1.2)),
                   ((0.6, 6.4, -0.4), (3.2, 8.0, 1.2)), ((6.4, 6.4, -0.4), (9.6, 8.0, 1.2)), ((12.8, 6.4, -0.4), (15.4, 8.0, 1.2)),
                   ((0.6, 0.6, -0.4), (15.4, 6.4, 1.2))):
        m.cube(a, b, T(t_bone, b[0] - a[0], b[1] - a[1]))
    m.cube((1.0, 8.0, -1.2), (15.0, 9.4, -0.4), T(t_bone_lit, 14, 2), top=T(t_bone_lit, 14, 2))     # brow
    m.cube((7.0, 3.4, -1.4), (9.0, 6.8, -0.4), T(t_bone_lit, 2, 4), top=T(t_bone_lit, 2, 2))       # nose ridge
    for x in (1.4, 11.0):
        m.cube((x, 4.6, -1.0), (x + 3.6, 5.8, -0.4), T(t_bone_lit, 4, 1), top=T(t_bone_lit, 4, 1))  # cheekbones
    for x in range(3, 13, 2):                                                                        # carved teeth
        m.cube((x + 0.1, 1.2, -0.7), (x + 1.0, 2.6, -0.4), T(t_bone_lit, 1, 2))
    m.box((0.8, 0.8, -0.45), (15.2, 8.0, -0.45), {"north": (t_marks, [1, 4, 15, 15])}, shade=False, light=15)   # markings
    m.box((7.0, 9.6, -1.2), (9.0, 11.6, -0.4), {d: (t_gem, [0, 0, 16, 16]) for d in FACES_ALL}, light=8)        # brow gem
    # bone horns, gold-ringed, out from the temples, up and back
    horn = ((-1.0, 12.2, 4.0, 2.8), (-2.6, 14.6, 5.0, 2.5), (-3.8, 17.2, 6.4, 2.2), (-4.4, 20.0, 8.2, 1.9),
            (-4.4, 22.6, 10.4, 1.6), (-3.8, 24.8, 12.8, 1.3), (-2.8, 26.4, 15.2, 1.0), (-1.8, 27.4, 17.4, 0.7))
    pts = []
    for (a, b) in zip(horn, horn[1:]):
        for k in range(4):
            pts.append(tuple(a[i] + (b[i] - a[i]) * k / 4 for i in range(4)))
    pts.append(horn[-1])
    for side in (0, 1):
        for i, (cx, cy, cz, w) in enumerate(pts):
            x = cx if side == 0 else 16 - cx
            ring = i in (6, 14)
            tex = T(t_gold, 2, 2) if ring else T(t_horn, 2, 2)
            w2 = w + (0.4 if ring else 0)
            m.cube((x - w2 / 2, cy - w2 / 2, cz - w2 / 2), (x + w2 / 2, cy + w2 / 2, cz + w2 / 2), tex)
    # the crystal cluster on the crown (glowing), lightning between the crystals and the horn tips
    for (x0, z0, w, h) in ((7.0, 8.0, 2.2, 8.0), (4.8, 9.6, 1.6, 5.2), (9.6, 9.6, 1.6, 5.6), (6.0, 11.4, 1.4, 4.0), (8.8, 11.4, 1.4, 4.4)):
        m.box((x0, 16.2, z0), (x0 + w, 16.2 + h, z0 + w), {d: (t_crystal, [4, 0, 12, 16]) for d in ("north", "south", "west", "east")} |
              {"up": (t_crystal, [6, 0, 10, 4])}, light=13)
        m.box((x0 + w * 0.25, 16.2 + h, z0 + w * 0.25), (x0 + w * 0.75, 17.4 + h, z0 + w * 0.75),
              {d: (t_crystal, [6, 0, 10, 4]) for d in ("north", "south", "west", "east", "up")}, light=13)   # its point
    m.box((-1.8, 20.0, 15.2), (17.8, 27.0, 15.2), {"north": (t_bolt, [0, 0, 16, 16]), "south": (t_bolt, [16, 0, 0, 16])},
          shade=False, light=15)
    m.box((2.0, 19.0, 10.6), (14.0, 24.0, 10.6), {"north": (t_bolt, [16, 0, 0, 16]), "south": (t_bolt, [0, 0, 16, 16])},
          shade=False, light=15)
    m.box((6.6, 3.0, 16.4), (9.4, 13.0, 16.4), {"south": (t_beads, [5, 0, 11, 16]), "north": (t_beads, [5, 0, 11, 16])})   # tassel
    m.display = HEAD_DISPLAY
    return m


def mannequin(name):
    """A preview body wearing a set's equipment textures (boxes laid out as the player's, front facing south)."""
    m = Model("mannequin_" + name)
    edir = os.path.join(OUT, "equipment", name)
    hum = Image.open(os.path.join(edir, "humanoid.png")).convert("RGBA")
    leg = Image.open(os.path.join(edir, "humanoid_leggings.png")).convert("RGBA")
    skin = Image.new("RGBA", (64, 32), (150, 110, 85, 255))
    t_h, t_l, t_s = m.texture("hum", hum), m.texture("leg", leg), m.texture("skin", skin)
    def uv(part, face):
        for (p, f, x0, y0, w, h) in armor_faces():
            if p == part and f == face:
                return [x0 / 4, y0 / 2, (x0 + w) / 4, (y0 + h) / 2]
    def box(part, frm, to, t, inflate):
        a = [frm[i] - inflate for i in range(3)]
        b = [to[i] + inflate for i in range(3)]
        m.box(a, b, {"south": (t, uv(part, "front")), "north": (t, uv(part, "back")), "east": (t, uv(part, "left")),
                     "west": (t, uv(part, "right")), "up": (t, uv(part, "top")), "down": (t, uv(part, "bottom"))})
    for t, inf in ((t_s, 0), (t_l, 0.25), (t_h, 0.5)):
        box("body", (4, 12, 6), (12, 24, 10), t, inf)
        box("arm", (0, 12, 6), (4, 24, 10), t, inf)
        box("arm", (12, 12, 6), (16, 24, 10), t, inf)
        box("leg", (4, 0, 6), (8, 12, 10), t, inf)
        box("leg", (8, 0, 6), (12, 12, 10), t, inf)
    box("head", (4, 24, 4), (12, 32, 12), t_s, 0)
    return m


# ---------------------------------------------------------------- G6 v4
# Coverage is vanilla netherite's (tools/art/vanilla_armor): vanilla armor reads as 3D armor because of *where* it
# covers - a chest piece with a shaped edge, pauldrons on the upper arms (hands bare), boots, leggings with a waist -
# with the body showing between. We paint only inside that coverage.
# The back detail rides the elytra's wings (the only geometry a pack can add on the body) but is painted as a raised
# layer of the chestplate: each wing hinges at a shoulder (h = 0), crosses the back ~2 px behind it and flares out
# toward the hip lower down; we paint only the wing's own half (hinge to spine), so the two halves meet at the spine
# and nothing hangs like wings.

VANILLA_ARMOR = os.path.join(os.path.dirname(__file__), "vanilla_armor")


class CoveredCanvas(ArmorCanvas):
    """An ArmorCanvas that only paints where vanilla netherite armor covers (and never the head - helms are models)."""

    def __init__(self):
        super().__init__()
        self.mask = {"humanoid": Image.open(os.path.join(VANILLA_ARMOR, "humanoid_netherite.png")).convert("RGBA"),
                     "humanoid_leggings": Image.open(os.path.join(VANILLA_ARMOR, "humanoid_leggings_netherite.png")).convert("RGBA")}

    def _px(self, F, u, v, c):
        img, x0, y0, w, h = F
        if not (0 <= u < w and 0 <= v < h) or c is None:
            return
        layer = "humanoid" if img is self.layers["humanoid"] else "humanoid_leggings"
        x, y = x0 + u, y0 + v
        if y < 16 and x < 32:
            return                  # the head: the helm is a 3D model
        if self.mask[layer].getpixel((x, y))[3] == 0:
            return
        img.putpixel((x, y), c)


def covered_canvas():
    c = CoveredCanvas()
    c.px = c._px
    return c


SCALE_CELL = [[2, 4, 4, 3], [2, 3, 3, 2], [1, 2, 2, 1]]   # one fish scale (4 x 3): lit crown, body, the shadow under it


def scale_px(ramp, u, v, offset=0):
    """Real overlapping scales: rows of rounded scales, each lit at its crown (top-left light) and casting a shadow on
    the row below; alternate rows offset by half a scale."""
    row = v // 3
    cu = (u + offset + (2 if row % 2 else 0)) % 4
    return ramp[SCALE_CELL[v % 3][cu]]


def abyssal_armor():
    """Abyssal, worn - armour of real scales: deep-teal fish scales in overlapping rows over the whole piece, a keel
    plate down the breastbone with a sea-glow gem, pectoral rims; pauldrons of three big layered scales; scale
    leggings with big knee plates and spined fins flaring at the hips; plated boots with a glowing toe line. On the
    back (wings layer): a raised back plate of scales with a spined dorsal ridge and fins flaring at the hips."""
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    c = covered_canvas()
    H, L = "humanoid", "humanoid_leggings"
    for layer in (H, L):
        for part in ("body", "arm", "leg"):
            for face in ("front", "back", "right", "left", "top", "bottom"):
                F = c.face(layer, part, face)
                for v in range(F[4]):
                    for u in range(F[3]):
                        c.px(F, u, v, scale_px(ab, u, v))
    # chest: keel plate, gem, pectoral rims
    F = c.face(H, "body", "front")
    for v in range(0, 12):
        c.px(F, 3, v, ab[4] if v % 3 == 0 else ab[3]); c.px(F, 4, v, ab[2])
    c.gem(F, 3, 3, 4, 4, sg)
    for u in range(8):
        if u not in (3, 4):
            c.px(F, u, 5, ab[5] if u < 3 else ab[4])                      # the pectoral rim
    F = c.face(H, "body", "back")
    for v in range(0, 12, 2):
        c.px(F, 3, v, ab[4]); c.px(F, 4, v, ab[3])
    # pauldrons: three big layered scales
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        for (v0, tone) in ((0, 4), (2, 4), (4, 3)):
            c.rect(F, 0, v0, 3, v0 + 1, ab[tone]); c.px(F, 0, v0, ab[tone + 1])
            c.rect(F, 0, v0 + 2, 3, v0 + 2, ab[1])
        c.px(F, 1, 5, sg[3]); c.px(F, 2, 5, sg[2])
    c.plate(c.face(H, "arm", "top"), 0, 0, 3, 3, ab, 4)
    # boots: plated, glowing toe line, heel fin
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "leg", face)
        c.plate(F, 0, 9, 3, 11, ab, 3)
    c.inlay(c.face(H, "leg", "front"), [(0, 10), (1, 10), (2, 10), (3, 10)], sg)
    F = c.face(H, "leg", "back")
    c.px(F, 1, 9, ab[5]); c.px(F, 2, 9, ab[4])
    # leggings: knee plates, hip fins, belt
    F = c.face(L, "leg", "front")
    c.plate(F, 0, 4, 3, 6, ab, 4); c.gem(F, 1, 5, 2, 5, sg)
    for face in ("right", "left"):
        F = c.face(L, "leg", face)
        for (u, v) in ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (2, 2), (3, 2), (3, 3)):   # a hip fin
            c.px(F, u if face == "left" else 3 - u, v, sg[3] if v == 0 else ab[4] if (u + v) % 2 else ab[2])
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        for u in range(F[3]):
            c.px(F, u, 8, ab[1]); c.px(F, u, 9, ab[4] if u % 2 else ab[3])
    c.gem(c.face(L, "body", "front"), 3, 9, 4, 10, sg)
    return c.layers   # no back piece: capes and elytras stay free


def hollow_armor():
    """Hollow, worn - a sculk shaman's harness: carved old-bone plaques (lit edges, dark carved grooves) over dark violet
    cloth that falls in soft folds; a cut cyan crystal heart set in aged gold; bone pauldrons ridged like vertebrae
    with a crystal on each; a gold sash with a crimson gem over a skirt of cloth panels marked with glowing runes;
    wrapped boots with bone toe caps. On the back (wings layer): a bone back plate with crystals growing from the
    spine, static sparks of electricity round them."""
    ink, vi, bone, gd, hc, cr = RAMPS["ink"], RAMPS["violet"], RAMPS["bone"], RAMPS["gold"], RAMPS["hollowcy"], RAMPS["crimson"]
    cloth = [ink[1], ink[2], ink[3], vi[2], vi[3], vi[4]]
    c = covered_canvas()
    H, L = "humanoid", "humanoid_leggings"

    def fold(u, v, h):
        t = 3 if u % 4 == 0 else 2 if u % 4 in (1, 3) else 1
        return cloth[max(0, t - (1 if v >= h - 1 else 0))]

    def carved(F, u0, v0, u1, v1):
        """A carved bone plaque: lit top-left edge, shadowed bottom-right, a dark groove carved across its middle."""
        c.plate(F, u0, v0, u1, v1, bone, 3)
        mid = (v0 + v1) // 2
        for u in range(u0 + 1, u1):
            c.px(F, u, mid, RAMPS["sculk"][2])

    for layer in (H, L):
        for part in ("body", "arm", "leg"):
            for face in ("front", "back", "right", "left", "top", "bottom"):
                F = c.face(layer, part, face)
                for v in range(F[4]):
                    for u in range(F[3]):
                        c.px(F, u, v, fold(u, v, F[4]))
    F = c.face(H, "body", "front")
    carved(F, 0, 0, 2, 3); carved(F, 5, 0, 7, 3)                           # collar plaques
    c.rect(F, 2, 1, 5, 4, gd[2]); c.px(F, 2, 1, gd[4]); c.px(F, 5, 4, gd[1])
    c.gem(F, 3, 1, 4, 3, hc)                                               # the crystal heart
    carved(F, 1, 5, 6, 7)                                                  # a breast plaque
    for u in range(8):
        c.px(F, u, 8, gd[3] if u % 2 else gd[4])
    F = c.face(H, "body", "back")
    for v in (0, 3, 6):
        carved(F, 2, v, 5, v + 1)
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        for (v0, v1) in ((0, 1), (2, 3), (4, 5)):
            c.plate(F, 0, v0, 3, v1, bone, 4 if v0 == 0 else 3)             # pauldron ridged like vertebrae
        c.px(F, 1, 1, hc[4]); c.px(F, 2, 1, hc[3])
    F = c.face(H, "arm", "top")
    c.plate(F, 0, 0, 3, 3, bone, 4); c.gem(F, 1, 1, 2, 2, hc)
    F = c.face(H, "leg", "front")
    c.plate(F, 0, 10, 3, 11, bone, 3)
    for face in ("front", "back", "right", "left"):
        c.rect(c.face(H, "leg", face), 0, 8, 3, 8, gd[3])
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        for u in range(F[3]):
            c.px(F, u, 8, gd[4] if u % 2 else gd[3]); c.px(F, u, 9, gd[2])
        G = c.face(L, "leg", face)
        for u in range(4):
            c.px(G, u, 8, gd[3] if u % 2 else gd[2])
    c.gem(c.face(L, "body", "front"), 3, 8, 4, 9, cr)
    for face in ("front", "back"):
        c.inlay(c.face(L, "leg", face), [(1, 2), (2, 3), (1, 4), (2, 5)], hc)
    layers = c.layers
    layers["wings"] = hollow_back()
    return layers


def back_tex(shape):
    """The back detail on the elytra's wings: shape(h, v) -> colour or None, h = 0 at the wing's hinge (a shoulder)
    to 9 at its far end, v = 0 at the top. Painted on the face seen from behind (u = 36 + h) and mirrored on the inner
    face, plus the hinge-side edge. Only the wing's own half is painted (h up to the spine, where x = 0)."""
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    for v in range(20):
        spine = (5 + 0.25 * v) / 0.966           # where this wing crosses the spine
        for h in range(10):
            if h > spine:
                continue
            col = shape(h, v, spine)
            if col is None:
                continue
            img.putpixel((36 + h, 2 + v), col)
            img.putpixel((24 + 9 - h, 2 + v), col)
            if h == 0:
                img.putpixel((34, 2 + v), col); img.putpixel((35, 2 + v), col)
    return img


def abyssal_back():
    """The back detail: a pair of spined fins fanning up and out from the spine across the shoulder blades - rays
    radiating from low on the spine, membrane between them lit toward the top, a glowing rim along the outer edge -
    and a ridge of spines down the spine itself."""
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]

    def shape(h, v, spine):
        d = spine - h                                    # px from the spine, outward
        if v > 9:
            return None
        if d < 1.1:
            return sg[3] if v % 3 == 0 else ab[1]        # the spine ridge, its tips glowing
        reach = 1.2 + (9 - v) * 0.62                     # the fan widens toward the shoulders
        if d > reach:
            return None
        ang = math.atan2(9.5 - v, d)                     # rays from low on the spine
        on_ray = abs((ang / (math.pi / 2)) * 4 - round((ang / (math.pi / 2)) * 4)) < 0.16
        if d > reach - 1.0:
            return sg[3] if on_ray else sg[2]            # glowing rim
        if on_ray:
            return ab[1]
        return ab[4] if v < 4 else ab[3]
    return back_tex(shape)


def hollow_back():
    """The back detail: a carved bone plate across the shoulder blades (gold-edged), and from the spine a fan of cut
    crystals - each a shard with a lit face, a dark face and a bright seam - with a few sparks of electricity."""
    bone, hc, gd, sk = RAMPS["bone"], RAMPS["hollowcy"], RAMPS["gold"], RAMPS["sculk"]

    def shape(h, v, spine):
        d = spine - h
        for (base_v, slope, length) in ((7.5, 1.6, 4.2), (4.5, 1.1, 4.6), (2.0, 0.6, 3.6)):   # shards from the spine
            along = d
            centre = base_v - along * slope / 1.6
            if 0.6 < along < length and abs(v + 0.5 - centre) < 0.9 - along * 0.12:
                return hc[5] if abs(v + 0.5 - centre) < 0.3 else hc[4] if v + 0.5 < centre else hc[2]
        if (round(d), v) in {(3, 1), (5, 3), (2, 8)}:
            return (255, 255, 255, 255)                 # sparks
        if v == 0 and d < 5:
            return gd[4] if h % 2 else gd[3]
        if v <= 4 and d < 5:
            return bone[4] if v == 1 else sk[2] if v == 3 else bone[3]   # the carved bone plate
        return None
    return back_tex(shape)


def abyssal_helm_worn():
    """The Abyssal Helm worn - an open-faced sea-creature helm (the whole face shows): a crown of clean teal plates, a
    heavy brow band with a sea-glow gem, cheek guards along the sides of the face; fins tilted out like wings - two
    layered fan fins on each side, angled up and out - and a dorsal crest from the brow back over the crown. Textures
    in a clean, vanilla-like style so it sits well beside vanilla blocks."""
    m = Model("abyssal_helmet_head")
    m.part = True
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    top_i, side_i, back_i = tex_helm(ab, tone=3)
    t_top, t_side, t_back = m.texture("helm_top", top_i), m.texture("helm_side", side_i), m.texture("helm_back", back_i)
    t_brow = m.texture("brow", tex_smooth(ab, tone=4))
    t_fin = m.texture("fin", tex_fin_shape(ab, sg))
    t_gem = m.texture("gem", [fill(sg, [3, 4, 5, 4][f]) for f in range(4)])
    T = lambda t, w, h: (t, [0, 0, max(1, min(16, round(w))), max(1, min(16, round(h)))])  # noqa: E731
    m.cube((0.6, 14.6, 0.6), (15.4, 16.0, 15.6), (t_side, [0, 0, 16, 2]), top=(t_top, [0, 0, 16, 16]))   # crown
    m.cube((2.2, 16.0, 2.2), (13.8, 16.8, 14.4), (t_side, [0, 0, 16, 1]), top=(t_top, [2, 2, 14, 14]))
    m.box((0.6, 2.0, 14.6), (15.4, 14.6, 16.0), {"south": (t_back, [0, 2, 16, 16]), "north": (t_side, [0, 2, 16, 16]),
          "west": (t_side, [0, 2, 2, 16]), "east": (t_side, [0, 2, 2, 16]), "down": (t_side, [0, 14, 16, 16])})   # back
    for x0 in (0.0, 14.6):
        m.cube((x0, 3.0, 0.6), (x0 + 1.4, 14.6, 14.6), (t_side, [0, 3, 16, 16]))              # sides
    m.cube((0.2, 11.2, -0.4), (15.8, 14.6, 1.2), T(t_brow, 16, 3))                            # brow band (forehead only)
    m.box((7.0, 12.0, -0.7), (9.0, 13.8, -0.4), {d: (t_gem, [0, 0, 2, 2]) for d in FACES_ALL}, light=15)
    for x0 in (0.2, 14.0):
        m.cube((x0, 3.0, -0.2), (x0 + 1.8, 11.2, 1.2), T(t_brow, 2, 8))                       # cheek guards
    for side in (0, 1):                                                                        # fins, angled up and out
        sgn = -1 if side == 0 else 1
        for (y0, y1, z0, z1, ang, x) in ((7.0, 17.0, 3.0, 13.0, 22.5, 0.2), (10.0, 21.0, 7.0, 18.0, 45.0, 0.6)):
            px = -x if side == 0 else 16 + x
            el = m.box((px, y0, z0), (px, y1, z1), {"west": (t_fin, [0, 0, 16, 16]), "east": (t_fin, [16, 0, 0, 16])})
            el["rotation"] = {"origin": [px, y0, (z0 + z1) / 2], "axis": "z", "angle": -sgn * ang}
    fin_plane(m, t_fin, 8.0, 16.0, 27.0, 0.0, 17.0)                                            # dorsal crest
    m.cube((7.4, 16.0, 0.0), (8.6, 17.2, 15.0), T(t_brow, 1, 15), top=T(t_brow, 1, 15))
    m.display = HEAD_DISPLAY
    return m


def hollow_helm_worn():
    """The Hollow Crown worn - a sculk shaman's mask after the Psi shaman: a tall carved mask of old bone over a dark
    head-wrap - flat frontal plane, a heavy brow, a long nose ridge, carved horizontal bands, a carved mouth with teeth,
    eye holes (the wearer's eyes show) - its top rising above the head in a stepped crest; glowing hollow-cyan marks in
    its grooves; blocky bone horns thrusting forward from the temples, banded in gold; the crystal cluster on the crown
    with lightning crackling between the crystals and the horns (animated, glowing)."""
    m = Model("hollow_helmet_head")
    m.part = True
    ink, vi, bone, gd, hc, cr, sk = (RAMPS["ink"], RAMPS["violet"], RAMPS["bone"], RAMPS["gold"], RAMPS["hollowcy"],
                                     RAMPS["crimson"], RAMPS["sculk"])
    cloth = [ink[1], ink[2], ink[3], vi[2], vi[3], vi[4]]
    t_cloth = m.texture("cloth", tex_cloth(cloth))
    mask = blank()
    for y in range(16):
        for x in range(16):
            mask.putpixel((x, y), bone[4] if x < 2 or y < 1 else bone[2] if x > 13 else bone[3])
        if y % 4 == 3:
            for x in range(1, 15):
                mask.putpixel((x, y), sk[2])          # carved bands
    t_mask = m.texture("mask", mask)
    t_lit = m.texture("bone_lit", tex_smooth(bone, tone=4))
    t_horn = m.texture("horn", tex_plates(bone, band=4, tone=3))
    t_gold = m.texture("gold", tex_smooth(gd, tone=3))
    t_crystal = m.texture("crystal", tex_crystal(hc))
    teeth = blank()
    for x in range(16):
        for y in range(16):
            teeth.putpixel((x, y), bone[5] if x % 3 else sk[1])
    t_teeth = m.texture("teeth", teeth)
    t_marks = m.texture("marks", tex_glow_lines(hc, [[(x, 3) for x in range(2, 14)], [(x, 11) for x in range(2, 14)]]))
    bolts = []
    for f in range(6):
        b = blank()
        rnd = random.Random(761 + f)
        y = 8
        for x in range(16):
            y = max(2, min(13, y + rnd.choice((-2, -1, 0, 1, 2))))
            b.putpixel((x, y), (255, 255, 255, 255)); b.putpixel((x, y + 1), hc[4])
            if rnd.random() < 0.2:
                b.putpixel((x, max(0, y - 2)), hc[3])
        bolts.append(b)
    t_bolt = m.texture("bolt", bolts)
    T = lambda t, w, h: (t, [0, 0, max(1, min(16, round(w))), max(1, min(16, round(h)))])  # noqa: E731
    # the head-wrap
    m.cube((0.6, 14.6, 0.6), (15.4, 16.0, 15.6), T(t_cloth, 15, 2), top=T(t_cloth, 15, 15))
    m.cube((0.6, 0.6, 14.6), (15.4, 14.6, 16.0), T(t_cloth, 15, 14))
    for x0 in (0.0, 14.6):
        m.cube((x0, 0.6, 1.2), (x0 + 1.4, 14.6, 14.6), T(t_cloth, 14, 14))
    # the mask: eye holes at x 3.2..6.4 and 9.6..12.8, y 6.4..8.0
    for (a, b) in (((0.4, 8.0, -0.6), (15.6, 19.0, 1.2)),
                   ((0.4, 6.4, -0.6), (3.2, 8.0, 1.2)), ((6.4, 6.4, -0.6), (9.6, 8.0, 1.2)), ((12.8, 6.4, -0.6), (15.6, 8.0, 1.2)),
                   ((0.4, -0.6, -0.6), (15.6, 6.4, 1.2))):
        m.cube(a, b, T(t_mask, b[0] - a[0], b[1] - a[1]))
    m.cube((2.4, 19.0, -0.4), (13.6, 21.4, 1.0), T(t_mask, 11, 2), top=T(t_lit, 11, 1))        # stepped crest
    m.cube((5.0, 21.4, -0.2), (11.0, 23.2, 0.8), T(t_mask, 6, 2), top=T(t_lit, 6, 1))
    m.cube((0.8, 8.0, -1.6), (15.2, 9.6, -0.6), T(t_lit, 14, 2), top=T(t_lit, 14, 1))          # heavy brow
    m.cube((6.8, 1.8, -2.0), (9.2, 8.0, -0.6), T(t_lit, 2, 6), top=T(t_lit, 2, 2))             # long nose ridge
    m.cube((3.0, 0.2, -1.0), (13.0, 1.8, -0.6), T(t_teeth, 10, 2))                             # carved teeth
    m.box((0.6, 9.8, -0.65), (15.4, 18.8, -0.65), {"north": (t_marks, [0, 0, 16, 16])}, shade=False, light=15)
    m.box((7.0, 15.0, -1.4), (9.0, 17.0, -0.6), {d: (T(t_gold, 2, 2)[0], [0, 0, 4, 4]) for d in FACES_ALL})
    # blocky horns, thrusting forward from the temples
    for side in (0, 1):
        for (x0, x1, y0, y1, z0, z1, tex) in ((-2.6, 0.4, 10.6, 14.2, 4.0, 8.0, t_horn), (-4.2, -1.0, 11.6, 15.0, 0.6, 4.6, t_gold),
                                               (-4.6, -1.8, 12.8, 16.0, -3.0, 1.0, t_horn), (-4.0, -2.4, 14.4, 17.6, -5.6, -2.6, t_horn),
                                               (-3.4, -2.4, 16.4, 18.8, -7.0, -5.0, t_horn)):
            a, b = (x0, x1) if side == 0 else (16 - x1, 16 - x0)
            m.cube((a, y0, z0), (b, y1, z1), T(tex, 3, 3))
    # crystals on the crown, lightning between them and the horns
    for (x0, z0, w, h) in ((7.0, 8.0, 2.2, 8.0), (4.8, 9.6, 1.6, 5.2), (9.6, 9.6, 1.6, 5.6), (6.0, 11.4, 1.4, 4.0), (8.8, 11.4, 1.4, 4.4)):
        m.box((x0, 16.0, z0), (x0 + w, 16.0 + h, z0 + w), {d: (t_crystal, [4, 0, 12, 16]) for d in ("north", "south", "west", "east")} |
              {"up": (t_crystal, [6, 0, 10, 4])}, light=13)
        m.box((x0 + w * 0.25, 16.0 + h, z0 + w * 0.25), (x0 + w * 0.75, 17.2 + h, z0 + w * 0.75),
              {d: (t_crystal, [6, 0, 10, 4]) for d in ("north", "south", "west", "east", "up")}, light=13)
    m.box((-3.0, 17.0, 6.0), (19.0, 25.0, 6.0), {"north": (t_bolt, [0, 0, 16, 16]), "south": (t_bolt, [16, 0, 0, 16])},
          shade=False, light=15)
    m.box((1.0, 18.0, 11.0), (15.0, 24.0, 11.0), {"north": (t_bolt, [16, 0, 0, 16]), "south": (t_bolt, [0, 0, 16, 16])},
          shade=False, light=15)
    m.display = HEAD_DISPLAY
    return m


# ---------------------------------------------------------------- G6 v5: Hollow as a sculk soul machine
SOUL = RAMPS["hollowcy"]      # the light-blue soul power
STEEL = DEEPSLATE             # black and greys, reinforced-deepslate style


# ---------------------------------------------------------------- G6 v6: helmet shells that look like helmets; the
# Hollow horns are the warden's tendrils (vanilla's own shape, recoloured purple), mounted at the helmet's sides

def tex_helm(ramp, tone=3):
    """A helmet's shell, three textures: a domed top with a raised crest down its middle and rivets at the corners; the
    sides with a raised ear plate, a rim band along the bottom edge and rivets on it; the back with the crest running
    down to a flared neck rim. Shaded from one light at the top-left - no stripes."""
    def base(img):
        for y in range(16):
            for x in range(16):
                s = (x * 0.6 + y) / 24
                img.putpixel((x, y), ramp[tone + 1] if s < 0.18 else ramp[tone] if s < 0.62 else ramp[tone - 1])
        return img
    top = base(blank())
    for y in range(16):                                  # the crest, front to back
        top.putpixel((6, y), ramp[tone - 1]); top.putpixel((7, y), ramp[tone + 2]); top.putpixel((8, y), ramp[tone + 1])
        top.putpixel((9, y), ramp[tone - 2])
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        top.putpixel((x, y), ramp[tone + 2]); top.putpixel((x + 1, y + 1), ramp[tone - 2])
    side = base(blank())
    for y in range(4, 11):                               # the raised ear plate (a rounded rectangle)
        for x in range(4, 12):
            if (x, y) in ((4, 4), (11, 4), (4, 10), (11, 10)):
                continue
            edge_lit = y == 4 or x == 4
            edge_dark = y == 10 or x == 11
            side.putpixel((x, y), ramp[tone + 1] if edge_lit else ramp[tone - 1] if edge_dark else ramp[tone])
    for x in range(16):                                  # the rim band
        side.putpixel((x, 13), ramp[tone + 1]); side.putpixel((x, 14), ramp[tone]); side.putpixel((x, 15), ramp[tone - 2])
    for x in (2, 8, 13):
        side.putpixel((x, 14), ramp[tone + 2])            # rivets on the rim
    back = base(blank())
    for y in range(13):
        back.putpixel((7, y), ramp[tone + 2]); back.putpixel((8, y), ramp[tone + 1]); back.putpixel((9, y), ramp[tone - 2])
    for x in range(16):
        back.putpixel((x, 12), ramp[tone + 1]); back.putpixel((x, 13), ramp[tone + 2])
        back.putpixel((x, 14), ramp[tone]); back.putpixel((x, 15), ramp[tone - 2])
    return top, side, back


VANILLA_WARDEN = os.path.join(os.path.dirname(__file__), "vanilla_warden", "warden.png")


def warden_tendrils(ramp):
    """The warden's two tendrils (its 'horns', vanilla's own 16x16 artwork from warden.png), recoloured into `ramp` by
    brightness: (right one, left one)."""
    w = Image.open(VANILLA_WARDEN).convert("RGBA")
    crops = [w.crop((52, 32, 68, 48)), w.crop((58, 0, 74, 16))]
    lums = sorted({round(0.3 * r + 0.59 * g + 0.11 * b) for crop in crops for (r, g, b, a) in crop.getdata() if a})
    out = []
    for crop in crops:
        img = blank()
        for y in range(16):
            for x in range(16):
                r, g, b, a = crop.getpixel((x, y))
                if not a:
                    continue
                l = round(0.3 * r + 0.59 * g + 0.11 * b)
                k = lums.index(l) / max(1, len(lums) - 1)        # 0 = darkest .. 1 = brightest
                img.putpixel((x, y), ramp[1 + round(k * (len(ramp) - 2))])
        out.append(img)
    return out


def tendril_lightning(shape, frames=6):
    """Soul lightning crackling over a tendril: random bolts kept inside its shape, a new pattern each frame."""
    out = []
    for f in range(frames):
        img = blank()
        rnd = random.Random(811 + f)
        pts = [(x, y) for y in range(16) for x in range(16) if shape.getpixel((x, y))[3]]
        for _ in range(3):
            x, y = rnd.choice(pts)
            for _ in range(6):
                if shape.getpixel((x, y))[3]:
                    img.putpixel((x, y), (255, 255, 255, 255) if rnd.random() < 0.4 else SOUL[4])
                x = max(0, min(15, x + rnd.choice((-1, 0, 1))))
                y = max(0, min(15, y + rnd.choice((-1, 0, 1))))
        out.append(img)
    return out


def infection(c, F, cx, cy, r, veins=()):
    """Sculk infection growing on the steel, read by its gradient: a glowing soul heart, bright sculk round it, darker
    sculk toward the edge, veins of it reaching out over the plates at the given angles (degrees, 0 = right, 90 =
    down), and a shadow under its raised lower edge."""
    sk = RAMPS["sculk"]
    w, h = F[3], F[4]
    for v in range(h):
        for u in range(w):
            d = math.hypot(u - cx, v - cy)
            if d <= r * 0.3:
                col = SOUL[4] if d < 0.6 else SOUL[3]          # its glowing heart
            elif d <= r * 0.6:
                col = sk[4]
            elif d <= r - 0.5:
                col = sk[3]
            elif d <= r:
                col = sk[2]
            elif d <= r + 0.8 and v > cy:
                col = sk[0]                                   # the shadow under its raised edge
            else:
                continue
            c.px(F, u, v, col)
    for ang in veins:                                         # veins reaching out over the plates
        a = math.radians(ang)
        for k in range(int(r * 10), int((r + 2.6) * 10)):
            t = k / 10
            c.px(F, int(round(cx + math.cos(a) * t)), int(round(cy + math.sin(a) * t)), sk[2] if t < r + 1.4 else sk[1])


def crack(c, F, pts):
    """A crack of soul lightning through the steel along a fixed jagged path: light blue, white-hot at its middle."""
    for k, (u, v) in enumerate(pts):
        c.px(F, u, v, SOUL[5] if k == len(pts) // 2 else SOUL[4])


def hollow_armor():
    """Hollow, worn - a sculk soul machine, endgame armour, laid out on purpose: heavy plates of black-grey reinforced
    steel over a dark sculk underlayer; the soul reactor in the chest, infected - sculk spreading round it in a clear
    gradient, two cracks of soul lightning running from it in a mirrored pair; the infection climbing the spine behind;
    a matching patch on each pauldron and each thigh, each with its crack; purple trim; light-blue soles. No back piece."""
    sk, vi = RAMPS["sculk"], RAMPS["violet"]
    c = covered_canvas()
    H, L = "humanoid", "humanoid_leggings"
    for layer in (H, L):                                     # the calm underlayer: dark sculk, darker toward the bottom
        for part in ("body", "arm", "leg"):
            for face in ("front", "back", "right", "left", "top", "bottom"):
                F = c.face(layer, part, face)
                for v in range(F[4]):
                    for u in range(F[3]):
                        c.px(F, u, v, sk[1] if v < F[4] - 2 else sk[0])
    # chest: pectorals, abdominal plates, the infected reactor and its two cracks
    F = c.face(H, "body", "front")
    c.plate(F, 0, 0, 2, 4, STEEL, 3); c.plate(F, 5, 0, 7, 4, STEEL, 3)
    for v in (6, 8):
        c.plate(F, 1, v, 6, v + 1, STEEL, 3)
    infection(c, F, 3.5, 3.0, 2.6, veins=(150, 30))
    c.rect(F, 2, 2, 5, 4, STEEL[1]); c.px(F, 2, 2, STEEL[4])
    c.gem(F, 3, 2, 4, 3, SOUL)                                # the soul reactor core
    crack(c, F, [(2, 5), (2, 6), (1, 7), (1, 8), (2, 9), (1, 10)])
    crack(c, F, [(5, 5), (5, 6), (6, 7), (6, 8), (5, 9), (6, 10)])
    for u in range(8):
        c.px(F, u, 11, vi[3] if u % 2 else vi[2])
    F = c.face(H, "body", "back")
    c.plate(F, 0, 0, 2, 5, STEEL, 3); c.plate(F, 5, 0, 7, 5, STEEL, 3); c.plate(F, 1, 7, 6, 9, STEEL, 2)
    infection(c, F, 3.5, 5.0, 2.2, veins=(-90,))             # climbing the spine
    crack(c, F, [(3, 8), (4, 9), (3, 10)])
    for u in range(8):
        c.px(F, u, 11, vi[2])
    for face in ("right", "left"):
        F = c.face(H, "body", face)
        c.plate(F, 0, 0, 3, 4, STEEL, 2); c.plate(F, 0, 6, 3, 9, STEEL, 2)
    c.plate(c.face(H, "body", "top"), 0, 0, 7, 3, STEEL, 3)
    # pauldrons: two plates, purple rim, a soul core; the same small infection on each
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        c.plate(F, 0, 0, 3, 2, STEEL, 4); c.plate(F, 0, 3, 3, 5, STEEL, 3)
        c.rect(F, 0, 6, 3, 6, vi[3])
    for face in ("right", "left"):
        F = c.face(H, "arm", face)
        c.gem(F, 1, 1, 2, 1, SOUL)
        infection(c, F, 1.5, 4.0, 1.4)
    F = c.face(H, "arm", "top")
    c.plate(F, 0, 0, 3, 3, STEEL, 4); c.gem(F, 1, 1, 2, 2, SOUL)
    # boots: clean - heavy plates, purple toe trim, light-blue sole
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "leg", face)
        c.plate(F, 0, 7, 3, 10, STEEL, 3)
        c.rect(F, 0, 11, 3, 11, SOUL[3] if face == "front" else STEEL[1])
    c.rect(c.face(H, "leg", "front"), 0, 10, 3, 10, vi[3])
    c.rect(c.face(H, "leg", "bottom"), 0, 0, 3, 3, STEEL[1])
    # leggings: belt with a core, thigh plates, knee guards; the same infection on each thigh's outer side
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        for u in range(F[3]):
            c.px(F, u, 8, STEEL[4] if u == 0 else STEEL[3]); c.px(F, u, 9, STEEL[2])
        G = c.face(L, "leg", face)
        c.plate(G, 0, 0, 3, 3, STEEL, 3); c.plate(G, 0, 7, 3, 8, STEEL, 2)
    c.gem(c.face(L, "body", "front"), 3, 8, 4, 9, SOUL)
    for face in ("right", "left"):
        F = c.face(L, "leg", face)
        infection(c, F, 1.5, 2.5, 1.6, veins=(90,))
        crack(c, F, [(1, 5), (2, 6), (1, 7)])
    F = c.face(L, "leg", "front")
    c.plate(F, 0, 4, 3, 6, STEEL, 4); c.px(F, 0, 4, vi[4]); c.px(F, 3, 4, vi[3]); c.gem(F, 1, 5, 2, 5, SOUL)
    c.plate(c.face(L, "leg", "top"), 0, 0, 3, 3, STEEL, 3)
    return c.layers


def hollow_helm_worn():
    """The Hollow Crown worn - the head of a sculk soul machine, open-faced (the whole face shows): a helmet of
    black-grey reinforced steel (a domed top with a crest; ear plates and a rim band on the sides; a crest down the back
    to a flared neck rim), sculk creeping over it from the rim and along the brow, a brow band with a soul conduit and core, cheek guards; and
    at the helmet's sides the warden's two tendrils - vanilla's own shape, recoloured purple - set exactly as on the
    warden's head (flat, reaching out and up from the sides), conducting soul lightning: it crackles over each tendril
    and little cracks of plasma flicker in the air all round them (animated, glowing)."""
    m = Model("hollow_helmet_head")
    m.part = True
    vi = RAMPS["violet"]
    top_i, side_i, back_i = tex_helm(STEEL, tone=3)
    growth = sculk(781, frames=1, spots=3)
    rnd = random.Random(783)
    edge = [11 + rnd.choice((-2, -1, 0, 0, 1)) for _ in range(16)]

    def creep(img, rows_from_bottom=True, ragged=edge):
        """Sculk creeping over the steel from an edge, in a ragged line, a few soul spots in it."""
        img = img.copy()
        for x in range(16):
            for y in range(16):
                if (y >= ragged[x]) if rows_from_bottom else (y <= 15 - ragged[x]):
                    img.putpixel((x, y), growth.getpixel((x, y)))
            y0 = ragged[x] if rows_from_bottom else 15 - ragged[x]
            if 0 <= y0 < 16:
                img.putpixel((x, y0), RAMPS["sculk"][0])
        return img
    t_top = m.texture("helm_top", top_i)
    t_side = m.texture("helm_side", creep(side_i))
    t_back = m.texture("helm_back", creep(back_i))
    t_brow = m.texture("brow", creep(tex_smooth(STEEL, tone=3), ragged=[14 + rnd.choice((-1, 0, 0, 1)) for _ in range(16)]))
    t_core = m.texture("core", [fill(SOUL, [3, 4, 5, 5, 4, 3][f]) for f in range(6)])
    t_conduit = m.texture("conduit", tex_glow_lines(SOUL, [[(x, 7) for x in range(1, 15)], [(x, 8) for x in range(1, 15)]]))
    right_t, left_t = warden_tendrils(vi)
    t_tr, t_tl = m.texture("tendril_r", right_t), m.texture("tendril_l", left_t)
    t_zr, t_zl = m.texture("zap_r", tendril_lightning(right_t)), m.texture("zap_l", tendril_lightning(left_t))
    sparks = []
    fire = {0: (0, 1), 1: (5, 6, 7), 2: (10, 11), 3: (13, 14)}   # when each quadrant's bolt is alive (of 16 frames)
    for f in range(16):   # bolts of plasma: in each quadrant, a jagged downward stroke with a fork - or nothing
        b = blank()
        for q, (qx, qy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            if f not in fire[q]:
                continue
            rnd = random.Random(831 + q * 13 + f)
            x = qx + 3 + rnd.choice((-1, 0, 1))
            fork_at = rnd.randrange(2, 5)
            for y in range(qy, qy + 8):
                b.putpixel((x, y), (255, 255, 255, 255) if (y - qy) % 3 else SOUL[5])
                if 0 <= x + 1 - qx < 8:
                    b.putpixel((x + 1, y), SOUL[3])            # a glow beside the stroke
                if y - qy == fork_at:                          # the fork
                    fx = x
                    for k in range(1, 4):
                        fx = fx - 1 if 0 < fx - qx else fx
                        if y + k < qy + 8:
                            b.putpixel((fx, y + k), RAMPS["violet"][5] if k == 3 else SOUL[4])
                x = max(qx, min(qx + 6, x + rnd.choice((-1, 0, 1))))
        sparks.append(b)
    t_spark = m.texture("spark", sparks)
    # the helmet: a sculk-grown dome, sides with ear plates and a rim, a back with a crest and neck rim
    m.cube((0.6, 14.6, 0.6), (15.4, 16.0, 15.6), (t_side, [0, 0, 16, 2]), top=(t_top, [0, 0, 16, 16]))
    m.cube((2.2, 16.0, 2.2), (13.8, 16.8, 14.4), (t_side, [0, 0, 16, 1]), top=(t_top, [2, 2, 14, 14]))
    m.box((0.6, 1.4, 14.6), (15.4, 14.6, 16.0), {"south": (t_back, [0, 2, 16, 16]), "north": (t_side, [0, 2, 16, 16]),
          "west": (t_side, [0, 2, 2, 16]), "east": (t_side, [0, 2, 2, 16]), "down": (t_side, [0, 14, 16, 16])})
    for x0 in (0.0, 14.6):
        m.cube((x0, 2.0, 0.6), (x0 + 1.4, 14.6, 14.6), (t_side, [0, 3, 16, 16]))
    # brow band with a soul conduit and core; cheek guards (the face stays open)
    m.cube((0.2, 10.6, -0.4), (15.8, 14.6, 1.2), (t_brow, [0, 12, 16, 16]))   # its lower edge grown with sculk
    m.box((0.4, 10.6, -0.45), (15.6, 12.2, -0.45), {"north": (t_conduit, [0, 6, 16, 9])}, shade=False, light=15)
    m.box((6.8, 11.6, -1.0), (9.2, 13.8, -0.4), {d: (t_core, [0, 0, 2, 2]) for d in FACES_ALL}, light=15)
    for x0 in (0.2, 14.0):
        m.cube((x0, 2.0, -0.2), (x0 + 1.8, 10.6, 1.2), (t_side, [0, 8, 2, 16]))   # cheek guards, sculk at their foot
    # the warden's tendrils, flat at the helmet's sides as on the warden (16 px out, from 7 below the top to 9 above):
    # each drawn on both faces with its base at the helmet; lightning crackling over it
    for (x0, x1, tex, zap, flip) in ((-16.0, 0.0, t_tr, t_zr, False), (16.0, 32.0, t_tl, t_zl, False)):
        m.box((x0, 9.0, 8.0), (x1, 25.0, 8.0), {"south": (tex, [0, 0, 16, 16]), "north": (tex, [16, 0, 0, 16])}, light=6)
        m.box((x0, 9.0, 7.9), (x1, 25.0, 7.9), {"north": (zap, [16, 0, 0, 16])}, shade=False, light=15)
        m.box((x0, 9.0, 8.1), (x1, 25.0, 8.1), {"south": (zap, [0, 0, 16, 16])}, shade=False, light=15)
    # little cracks of plasma in the air round each tendril: small planes facing every way, each showing one quadrant
    # of the flickering spark texture (so neighbours never flicker together)
    spots = ((-11.0, 20.0, 5.6, "z"), (-7.0, 23.0, 10.4, "x"), (-13.0, 14.0, 9.8, "y45"), (-4.0, 17.0, 5.8, "x"))
    for side in (0, 1):
        for k, (x, y, z, orient) in enumerate(spots):
            px = x if side == 0 else 16 - x
            q = [(0, 0), (8, 0), (0, 8), (8, 8)][(k + side) % 4]
            uv = [q[0], q[1], q[0] + 8, q[1] + 8]
            sz = 6.0
            if orient == "x":
                el = m.box((px, y, z - sz / 2), (px, y + sz, z + sz / 2), {"west": (t_spark, uv), "east": (t_spark, uv)},
                           shade=False, light=15)
            else:
                el = m.box((px - sz / 2, y, z), (px + sz / 2, y + sz, z), {"north": (t_spark, uv), "south": (t_spark, uv)},
                           shade=False, light=15)
                if orient == "y45":
                    el["rotation"] = {"origin": [px, y, z], "axis": "y", "angle": 45}
    m.display = HEAD_DISPLAY
    return m


def save_armor(name, layers):
    d = os.path.join(OUT, "equipment", name)
    os.makedirs(d, exist_ok=True)
    for old in os.listdir(d):
        if old.endswith(".png") and old[:-4] not in layers:
            os.remove(os.path.join(d, old))   # a layer the set no longer has (the old back pieces)
    for layer, img in layers.items():
        img.save(os.path.join(d, f"{layer}.png"))


def armor_preview(layers, scale=6):
    """A flat front/back preview: the player's boxes unfolded as they're worn (head, body, arms, legs, both views)."""
    hum, leg = layers["humanoid"], layers["humanoid_leggings"]
    out = Image.new("RGBA", (2 * 16 * scale + 3 * 10, 32 * scale + 20), (60, 58, 66, 255))
    def blit(img, src, dst, flip=False):
        crop = img.crop(src)
        if flip:
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
        crop = crop.resize((crop.size[0] * scale, crop.size[1] * scale), Image.NEAREST)
        out.alpha_composite(crop, dst)
    for view, ox in (("front", 10), ("back", 16 * scale + 20)):
        hx = (8, 8, 16, 16) if view == "front" else (24, 8, 32, 16)
        bx = (20, 20, 28, 32) if view == "front" else (32, 20, 40, 32)
        ax = (44, 20, 48, 32) if view == "front" else (52, 20, 56, 32)
        lx = (4, 20, 8, 32) if view == "front" else (12, 20, 16, 32)
        for img in (hum, leg):
            blit(img, hx, (ox + 4 * scale, 10))
            blit(img, bx, (ox + 4 * scale, 10 + 8 * scale))
            blit(img, ax, (ox, 10 + 8 * scale))
            blit(img, ax, (ox + 12 * scale, 10 + 8 * scale), flip=True)
            blit(img, lx, (ox + 4 * scale, 10 + 20 * scale))
            blit(img, lx, (ox + 8 * scale, 10 + 20 * scale), flip=True)
    return out


G6_SETS = {"abyssal": abyssal_armor, "hollow": hollow_armor}


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
GROUPS = {"g1": G1, "g2": G2, "g3": G3, "g4": G4, "g5": G5}


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
    for name, meta in model.mcmeta.items():
        with open(os.path.join(d, f"{name}.mcmeta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
    if model.part:
        open(os.path.join(d, "part.txt"), "w", encoding="utf-8").write("shown by the plugin, not a block skin")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "g1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    if which == "g6":   # worn armor: textures, not models
        sheet = Image.new("RGBA", (420, 230 * len(G6_SETS)), (60, 58, 66, 255))
        for helm in (abyssal_helm_worn(), hollow_helm_worn()):
            save(helm)
        for i, (name, make) in enumerate(G6_SETS.items()):
            layers = make()
            save_armor(name, layers)
            sheet.alpha_composite(armor_preview(layers), (0, i * 230))
        sheet.save(os.path.join(OUT, "review-g6.png"))
        print(os.path.join(OUT, "review-g6.png"))
        sys.exit(0)
    suffix = "" if version == "final" else "-" + version
    models = []
    for name, make in GROUPS[which]:
        m = make()
        if not name.endswith("(front)"):   # preview-only views
            save(m)
        models.append((name, m))
    print(review(models, os.path.join(OUT, f"review-{which}{suffix}.png"), frames=4, s=5))
