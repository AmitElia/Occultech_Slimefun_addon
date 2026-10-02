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


G1 = [("Initiate's Altar", initiate_altar), ("Offering Bowl", offering_bowl), ("Chalk Glyph", chalk_glyph),
      ("Chalk Glyph v1", lambda: chalk_glyph(1)), ("Chalk Glyph v2", lambda: chalk_glyph(2)),
      ("Chalk Glyph v3", lambda: chalk_glyph(3)), ("Arcane Altar", arcane_altar)]
GROUPS = {"g1": G1}


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
