"""Gelatinous Sovereign redesign, session 1: three directions as Blockbench cuboid blockouts.

The fight is set (GelatinousSovereign.java): a huge slime (a size-7 slime, about 3.6 blocks) that marks a player and
leaps onto them with a shockwave (jump it); at 66% it splits off three shards that crawl back to heal it; at 33% it
shrinks, speeds up and leaves acid puddles. The name is set: the Gelatinous Sovereign. The look is open.

All three keep the vanilla slime's idea: a see-through jelly with something solid inside it. Each has to show the
split (a tear) and the shrink (the jelly burning off what is inside):

  A  Drowned Regent  a low, wide mound of murky jelly; inside, a dead king seated on his sunken throne, treasure and
                     helmets drifting round him; the crown sits on the outside, sunk halfway into the top. At 33% the
                     jelly burns off and the king stands up.
  B  Crowned Core    the vanilla slime made huge: a sagging cube of jelly around a great dark core with the vanilla
                     slime face, crowned; swallowed treasure orbits the core. At 33% the outer jelly is gone and the
                     crowned core is left, small and fast.
  C  The Pretender   the jelly has taken the shape of the king it ate: a seated, crowned figure on a throne of slime,
                     the real king's skeleton inside in the same pose. At 33% the shape slumps and the skeleton walks.

Run from the repository root: python tools/art/bosses/sovereign_s1.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s1 as b1, volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/gelatinous_sovereign/overhaul/s1_concepts"
PALETTE = {
    # the jelly is see-through in the colour views (alpha), solid in silhouette and clay
    "jelly": (108, 196, 60, 70), "jelly_murky": (64, 132, 52, 95), "jelly_skin": (128, 210, 80, 150),
    "core": RAMPS["gel"][1], "face": RAMPS["gel"][0], "bone": RAMPS["bone"][3], "bone_dark": RAMPS["bone"][2],
    "gold": RAMPS["gold"][3], "gold_dark": RAMPS["gold"][2], "gem": RAMPS["crimson"][4], "iron": RAMPS["iron"][3],
    "iron_dark": RAMPS["iron"][2], "wood": RAMPS["wood"][2], "stone": RAMPS["ash"][3], "rags": RAMPS["ink"][3],
}
DIRECTIONS = {"A": "Drowned Regent", "B": "Crowned Core", "C": "The Pretender"}


# ---- props --------------------------------------------------------------------------------------------------------

def crown(g, name, centre, r, sunk=False):
    """A king's crown: a band of four sides, a point on each corner and the middle of each side, a red stone at the
    front."""
    x, y, z = centre
    h = r * 0.5
    for s in (-1, 1):
        g.box(f"{name}_band_x{s}", (x + s * (r - 0.5), y, z), (1, h, 2 * r), "gold")
        g.box(f"{name}_band_z{s}", (x, y, z + s * (r - 0.5)), (2 * r - 2, h, 1), "gold")
    for i, (dx, dz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0))):
        tall = 3 if dx and dz else 2
        g.box(f"{name}_point_{i}", (x + dx * (r - 0.5), y + h / 2 + tall / 2, z + dz * (r - 0.5)), (1, tall, 1), "gold")
    g.box(f"{name}_stone", (x, y, z - r - 0.3), (2, 2, 1), "gem")


def throne(g, name, base, w, seat_h, back_h, mat="stone"):
    x, y, z = base
    g.box(f"{name}_seat", (x, y + seat_h - 2, z), (w, 4, w * 0.8), mat)
    g.box(f"{name}_base", (x, y + (seat_h - 4) / 2, z + 1), (w - 4, seat_h - 4, w * 0.7), mat)
    g.box(f"{name}_back", (x, y + seat_h + back_h / 2, z + w * 0.4 - 1.5), (w, back_h, 3), mat)
    g.box(f"{name}_back_top", (x, y + seat_h + back_h + 1.5, z + w * 0.4 - 1.5), (w * 0.6, 3, 3), mat)
    for s in (-1, 1):
        g.box(f"{name}_arm_{s}", (x + s * (w / 2 - 1.5), y + seat_h + 4, z - 1), (3, 2, w * 0.7), mat)
        g.box(f"{name}_arm_post_{s}", (x + s * (w / 2 - 1.5), y + seat_h + 1.5, z - w * 0.32), (2, 3, 2), mat)


def skeleton(g, name, hip, k, seated=True, crowned=False):
    """A king's skeleton in vanilla skeleton proportions (head 8, body 8x12x4, limbs 2 thick), scaled by k. Seated:
    thighs forward on the seat, shins down, forearms on the armrests."""
    x, y, z = hip
    u = k
    g.box(f"{name}_pelvis", (x, y + u, z), (8 * u, 2 * u, 3 * u), "bone")
    g.box(f"{name}_spine", (x, y + 6 * u, z + u), (2 * u, 10 * u, 2 * u), "bone_dark")
    for i in range(4):
        g.box(f"{name}_rib_{i}", (x, y + (5 + 2 * i) * u, z), (8 * u, u, 4 * u), "bone")
    skull_y = y + 16 * u
    g.box(f"{name}_skull", (x, skull_y, z), (8 * u, 7 * u, 8 * u), "bone")
    g.box(f"{name}_jaw", (x, skull_y - 4 * u, z - u), (6 * u, 2 * u, 6 * u), "bone_dark")
    for s in (-1, 1):
        g.box(f"{name}_eye_{s}", (x + s * 2 * u, skull_y + 0.5 * u, z - 4 * u - 0.2), (2 * u, 1.5 * u, 0.6), "face")
        g.box(f"{name}_shoulder_{s}", (x + s * 5 * u, y + 12 * u, z), (2 * u, 2 * u, 2 * u), "bone")
        g.box(f"{name}_rag_{s}", (x + s * 4 * u, y + 11 * u, z + 0.5 * u), (4 * u, 4 * u, 5 * u), "rags")
        if seated:
            g.box(f"{name}_thigh_{s}", (x + s * 2.5 * u, y, z - 5 * u), (2 * u, 2 * u, 10 * u), "bone")
            g.box(f"{name}_shin_{s}", (x + s * 2.5 * u, y - 5 * u, z - 10 * u), (2 * u, 10 * u, 2 * u), "bone")
            g.box(f"{name}_upper_arm_{s}", (x + s * 5 * u, y + 8 * u, z), (2 * u, 8 * u, 2 * u), "bone")
            g.box(f"{name}_forearm_{s}", (x + s * 5 * u, y + 4 * u, z - 4 * u), (2 * u, 2 * u, 8 * u), "bone")
        else:
            g.box(f"{name}_leg_{s}", (x + s * 2.5 * u, y - 6 * u, z), (2 * u, 12 * u, 2 * u), "bone")
            g.box(f"{name}_arm_{s}", (x + s * 5 * u, y + 6 * u, z), (2 * u, 12 * u, 2 * u), "bone")
    if crowned:
        crown(g, f"{name}_crown", (x, skull_y + 5 * u, z), 4.5 * u)
    return skull_y


def treasure(g, name, centre, spread, n, rnd, helmets=2, sword=True):
    """Swallowed treasure drifting in the jelly: coins turned at odd angles, a couple of adventurers' helmets, a sword."""
    cx, cy, cz = centre
    sx, sy, sz = spread
    for i in range(n):
        p = (cx + rnd.uniform(-sx, sx), cy + rnd.uniform(-sy, sy), cz + rnd.uniform(-sz, sz))
        g.box(f"{name}_coin_{i}", p, (3, 1, 3), "gold", rotation=(rnd.choice((0, 22.5, 45, -22.5)), 0, 0))
    for i in range(helmets):
        p = (cx + rnd.uniform(-sx, sx), cy + rnd.uniform(-sy, sy), cz + rnd.uniform(-sz, sz))
        mat = ("iron", "gold_dark")[i % 2]
        g.box(f"{name}_helm_{i}", p, (8, 6, 8), mat, rotation=(0, 0, rnd.choice((22.5, -22.5, 45))))
        g.box(f"{name}_helm_{i}_slit", (p[0], p[1] + 0.5, p[2] - 4.2), (6, 1, 0.6), "face", rotation=(0, 0, 0))
    if sword:
        p = (cx + sx * 0.5, cy, cz - sz * 0.3)
        g.box(f"{name}_sword_blade", p, (1, 16, 3), "iron", rotation=(0, 0, 45))
        g.box(f"{name}_sword_guard", (p[0] - 6, p[1] - 6, p[2]), (2, 2, 7), "iron_dark", rotation=(0, 0, 45))


def puddle(g, name, centre, w, d):
    """The jelly spreads where it sits: a thin skirt on the floor, a little wider than the body."""
    x, _, z = centre
    g.box(f"{name}_puddle", (x, 0.5, z), (w, 1, d), "jelly")
    g.box(f"{name}_puddle_edge", (x, 0.25, z), (w + 6, 0.5, d + 6), "jelly")


# ---- the three directions -----------------------------------------------------------------------------------------

def goo(g, name, centre, radii, mat="jelly", layers=6):
    """A rounded lump of jelly (stepped both ways, so it reads round from the side too, not as a stack of slabs)."""
    return g.blob(name, centre, radii, mat, layers=layers, axes=("y", "z"))


def drowned_regent(model):
    rnd = random.Random(1)
    body = model.group("root_body", (0, 0, 0))
    inside = body.group("inside", (0, 0, 0))
    throne(inside, "throne", (0, 0, 8), 24, 14, 40)          # the tall back breaks out of the top of the jelly
    skeleton(inside, "king", (0, 16, 6), 1.25)
    treasure(inside, "treasure", (0, 20, 0), (26, 10, 22), 16, rnd)
    jelly = body.group("jelly", (0, 24, 0))
    goo(jelly, "jelly_dome", (0, 20, 2), (36, 22, 32), "jelly_murky", 8)
    goo(jelly, "jelly_sag_l", (-26, 9, -12), (18, 10, 18), "jelly_murky")     # it sags and spreads where it sits
    goo(jelly, "jelly_sag_r", (27, 10, 10), (15, 11, 16), "jelly_murky")
    goo(jelly, "jelly_rear", (-6, 22, 24), (20, 16, 14), "jelly_murky")
    # a pseudopod reaching forward, a swallowed gauntlet in its tip
    for i, (x, y, z, r) in enumerate(((14, 12, -26, 11), (19, 9, -37, 8), (23, 7, -45, 6))):
        goo(jelly, f"jelly_reach_{i}", (x, y, z), (r, r * 0.8, r), "jelly_murky", 4)
    inside.box("gauntlet", (23, 7, -45), (4, 4, 6), "iron", rotation=(0, 22.5, 0))
    puddle(jelly, "jelly", (0, 0, -4), 84, 84)
    crown(body, "crown", (0, 41, -2), 8)                # sunk halfway into the top of the dome


def crowned_core(model):
    rnd = random.Random(2)
    body = model.group("root_body", (0, 0, 0))
    core = body.group("core", (0, 26, 0))
    b1.rounded_box(core, "core", (0, 26, 0), (30, 30, 30), "core", 2)
    for s in (-1, 1):   # the vanilla slime face, made huge: two dark square eyes and a small mouth
        core.box(f"face_eye_{s}", (s * 7, 31, -15.3), (6, 6, 1), "face")
    core.box("face_mouth", (3, 20, -15.3), (4, 3, 1), "face")
    crown(core, "crown", (0, 44, 0), 10)
    treasure(body, "treasure", (0, 26, 0), (24, 20, 24), 18, rnd)
    jelly = body.group("jelly", (0, 28, 0))
    # one vanilla slime cube, bevelled, sagging under its own weight: the bottom bulges out, the top is domed
    b1.rounded_box(jelly, "jelly_cube", (0, 30, 0), (58, 52, 56), "jelly", 4)
    b1.rounded_box(jelly, "jelly_bulge", (0, 9, 0), (68, 16, 66), "jelly", 5)
    b1.rounded_box(jelly, "jelly_dome", (0, 57, 0), (44, 6, 42), "jelly", 2)
    goo(jelly, "jelly_lip", (-8, 11, -32), (18, 9, 8), "jelly", 4)          # a drooping lip at the front
    for i in range(12):                                                    # goo running down from the top edges
        a = i * 2 * math.pi / 12 + 0.3
        x, z = math.cos(a) * 29.5, math.sin(a) * 28.5
        jelly.box(f"jelly_run_{i}", (x, 46 - (i % 4) * 3, z), (3, 8 + (i % 3) * 5, 3), "jelly_skin")
    puddle(jelly, "jelly", (0, 0, 0), 78, 76)


def pretender(model):
    rnd = random.Random(3)
    body = model.group("root_body", (0, 0, 0))
    inside = body.group("inside", (0, 0, 0))
    throne(inside, "throne", (0, 0, 10), 40, 20, 52, mat="wood")   # its tall back rises behind the head
    skull_y = skeleton(inside, "king", (0, 24, 8), 2.0)
    treasure(inside, "treasure", (0, 14, -10), (20, 8, 10), 8, rnd, helmets=1, sword=False)
    jelly = body.group("jelly", (0, 30, 8))
    # the jelly takes the king's shape: a robe spreading to the floor, a lap, torso, shoulders, a head, arms on the rests
    goo(jelly, "jelly_robe", (0, 9, 4), (32, 10, 30))
    goo(jelly, "jelly_lap", (0, 22, -4), (22, 9, 18))
    goo(jelly, "jelly_torso", (0, 40, 8), (17, 15, 12))
    goo(jelly, "jelly_shoulders", (0, 54, 8), (27, 6, 12), layers=4)
    goo(jelly, "jelly_head", (0, skull_y + 1, 6), (10, 10, 10))
    for s in (-1, 1):
        jelly.box(f"jelly_upper_arm_{s}", (s * 25, 45, 8), (9, 16, 9), "jelly", rotation=(0, 0, s * 22.5))
        jelly.box(f"jelly_forearm_{s}", (s * 23, 36, -2), (9, 8, 22), "jelly")
        for f in range(3):                                         # fingers of slime dripping off the armrest
            jelly.box(f"jelly_finger_{s}_{f}", (s * (20 + f * 3), 29, -11), (2, 6 + f * 2, 2), "jelly_skin")
    jelly.box("jelly_beard", (0, skull_y - 11, 0), (10, 10, 6), "jelly_skin")
    crown(body, "crown", (0, skull_y + 12, 6), 8)
    puddle(jelly, "jelly", (0, 0, 2), 78, 72)


BUILD = {"A": drowned_regent, "B": crowned_core, "C": pretender}


def build(key):
    model = Model(f"occultech_gelatinous_sovereign_{key.lower()}")
    BUILD[key](model)
    return model


VIEWS = b1.VIEWS


def main():
    for old in OUT.glob("*"):
        if old.is_dir():
            shutil.rmtree(old)
    for key, title in DIRECTIONS.items():
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = build(key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        sheet.direction_sheet(out, f"Gelatinous Sovereign - {key} {title}", stats, out / "sheet.png")
        print(key, stats["size_blocks"], stats["cubes"])
    items = list(DIRECTIONS.items())
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Gelatinous Sovereign - three directions (session 1)")
    sheet.compare_sheet(OUT, items, OUT / "compare_material.png", heading="Gelatinous Sovereign - see-through jelly",
                        views=("flat_front", "flat_34", "flat_side"))


if __name__ == "__main__":
    main()
