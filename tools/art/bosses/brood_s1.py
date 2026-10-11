"""Brood Mother redesign, session 1: three directions as Blockbench cuboid blockouts.

The brief: a scary, mutated Minecraft spider, enchanted and cursed. It wears a wooden mask carved like a villager's
face, as a lure, with two large glowing eyes showing through its eye holes. On its back, a pile of breathing, glowing
egg cocoons; the fight's egg sacs are laid from it.

  A  Masked matriarch  high-arched legs, knees above the body; the classic looming spider
  B  Weaver crone      low and wide, a swollen abdomen near the ground under a hill of cocoons
  C  The lure          the front body reared up so the mask sits at a villager's head height, front legs raised

Tier 0 (initiate): dark chitin, pale silk, old wood and twine; the accent is ember, in the eyes and inside the eggs.

Run from the repository root: python tools/art/bosses/brood_s1.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, leg  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s1_concepts"
PALETTE = {
    "chitin": RAMPS["ash"][2], "chitin_lit": RAMPS["ash"][3], "marrow": RAMPS["ash"][1],
    "silk": RAMPS["chalk"][3], "wood": RAMPS["wood"][2], "wood_dark": RAMPS["wood"][1], "twine": RAMPS["twine"][2],
    "iron": RAMPS["iron"][2], "glow": RAMPS["ember"][3], "eye": RAMPS["ember"][4],
}
DIRECTIONS = {
    "A": {"title": "Masked matriarch", "body_y": 24, "rear": 0, "legs": "arched", "pile": 8, "abdomen": (15, 13, 19)},
    "B": {"title": "Weaver crone", "body_y": 15, "rear": 0, "legs": "splayed", "pile": 13, "abdomen": (20, 14, 24)},
    "C": {"title": "The lure", "body_y": 20, "rear": 38, "legs": "rearing", "pile": 9, "abdomen": (15, 12, 18)},
}


def mask(head, cx, cy, z, w, h):
    """The villager mask: a carved board with a brow ridge, the long villager nose and two eye holes; behind each hole,
    a large glowing eye. Built around the holes, so they are real openings."""
    hole_w, hole_h, hole_y = 6, 5, cy + h * 0.12
    left, right = cx - w / 2, cx + w / 2
    top, bottom = cy + h / 2, cy - h / 2
    eye_x = w * 0.22
    head.box("mask_top", (cx, (top + hole_y + hole_h / 2) / 2, z), (w, top - hole_y - hole_h / 2, 2), "wood")
    head.box("mask_bottom", (cx, (bottom + hole_y - hole_h / 2) / 2, z), (w, hole_y - hole_h / 2 - bottom, 2), "wood")
    head.box("mask_bridge", (cx, hole_y, z), (2 * (eye_x - hole_w / 2), hole_h, 2), "wood")
    for s in (-1, 1):
        edge = cx + s * (eye_x + hole_w / 2)
        outer = right if s > 0 else left
        head.box(f"mask_cheek_{s}", ((edge + outer) / 2, hole_y, z), (abs(outer - edge), hole_h, 2), "wood")
        # the eye fills the hole, a little sunk, so it reads as a glowing eye in the mask, not a shadow behind it
        head.box(f"eye_{s}", (cx + s * eye_x, hole_y, z + 0.5), (hole_w, hole_h, 2), "eye")
    head.box("mask_brow", (cx, hole_y + hole_h / 2 + 1.2, z - 1.4), (w * 0.8, 2, 2), "wood_dark")
    head.box("mask_nose", (cx, hole_y - hole_h / 2 - 4.5, z - 3), (5, 10, 5), "wood")
    head.box("mask_mouth", (cx, bottom + h * 0.16, z - 1.1), (w * 0.4, 1, 1), "wood_dark")
    head.box("mask_crack", (cx + w * 0.25, cy + h * 0.32, z - 1.1), (1, h * 0.3, 1), "wood_dark", rotation=(0, 0, 20))
    for s in (-1, 1):
        head.box(f"mask_strap_{s}", (cx + s * (w / 2 + 0.5), cy + h * 0.1, z + 5), (1, 2, 10), "twine")


def cocoons(abdomen, centre, radii, count):
    """The brood: a heap of egg cocoons on the abdomen, each with an ember glow through a split in its silk."""
    cx, cy, cz = centre
    rx, ry, rz = radii
    golden = math.pi * (3 - math.sqrt(5))
    pile = abdomen.group("cocoon_pile", (cx, cy + ry * 0.7, cz))
    glow = pile.group("glow_brood", (cx, cy + ry * 0.7, cz))
    for i in range(count):
        a = i * golden
        r = math.sqrt((i + 0.5) / count)
        x, z = cx + math.cos(a) * r * rx * 0.75, cz + math.sin(a) * r * rz * 0.75
        top = cy + ry * math.sqrt(max(0.05, 1 - (r * 0.75) ** 2))
        size = 11 - 3.5 * r + (i % 3) * 1.2
        y = top + size * 0.3 + (size * 0.6 if i % 3 == 0 and r < 0.7 else 0)   # a second layer: the pile heaps up
        pile.blob(f"cocoon_{i}", (x, y, z), (size * 0.5, size * 0.62, size * 0.5), "silk", layers=4)
        # the ember light of the brood inside, showing through a split in the silk
        glow.box(f"brood_glow_{i}", (x, y + size * 0.05, z), (size * 0.24, size * 0.85, size * 1.08), "glow",
                 rotation=(0, 20 + i * 47, 6))   # a seam right through the silk: it shows on both sides
    for i in range(count // 2):
        a, b = i * golden * 2, (i * golden * 2 + 2.1)
        v1.beam(pile, f"strand_{i}", (cx + math.cos(a) * rx * 0.5, cy + ry * 0.95, cz + math.sin(a) * rz * 0.5),
                (cx + math.cos(b) * rx * 0.6, cy + ry * 0.8, cz + math.sin(b) * rz * 0.6), 0.8, "silk")


def legs(thorax, d, y):
    """Eight legs from the thorax sides, front to back. A leg is laid along +X and yawed round Y (positive yaw turns it
    to the front, -Z); femur up, tibia down to the floor."""
    style = d["legs"]
    yaws = (64, 24, -18, -58) if style == "arched" else (52, 20, -14, -46)
    for side in (1, -1):
        for i, yaw in enumerate(yaws):
            hip = (side * 7, y, -8 + i * 4)
            ang = yaw if side > 0 else 180 - yaw
            if style == "arched":
                segs = [(21, 64, 4.4), (None, -76, 3.4)]   # knees high over the body
            elif style == "splayed":
                segs = [(20, 26, 4.6), (None, -50, 3.6)]
            else:   # rearing: the front pair lifted high in threat, the rest braced wide
                segs = [(16, 78, 4.4), (15, 40, 3.4)] if i == 0 else [(17, 44, 4.4), (None, -66, 3.4)]
            leg(thorax, f"leg_{'r' if side > 0 else 'l'}{i}", hip, ang, segs, ground=0.0, mat="chitin",
                knuckle_mat="chitin_lit", joint_scale=1.35, bristles=3, bristle_mat="chitin_lit")


def build(key):
    d = DIRECTIONS[key]
    y = d["body_y"]
    model = Model(f"occultech_brood_mother_{key.lower()}")
    body = model.group("root_body", (0, y, 0))
    ax, ay, az = d["abdomen"]
    abdomen = body.group("abdomen", (0, y + 2, 4))
    abdomen.blob("abdomen", (0, y + ay * 0.55, 6 + az), (ax, ay, az), "chitin", layers=6)
    for i in range(5):   # a ridge of mutated spines down the back of the abdomen
        abdomen.box(f"spine_{i}", (0, y + ay * 1.5 - i * 1.5, 6 + az * 1.15 + i * 4), (2, 5, 2), "chitin_lit", rotation=(-35, 0, 0))
    abdomen.box("spinnerets", (0, y + 2, 6 + az * 2 - 1), (5, 4, 4), "chitin_lit")
    cocoons(abdomen, (0, y + ay * 0.55, 6 + az), (ax, ay, az), d["pile"])
    # the front body: thorax and head, reared up for the lure
    fore = body.group("thorax", (0, y, 2), (d["rear"], 0, 0))
    fore.box("thorax", (0, y, -4), (17, 12, 16), "chitin")
    fore.box("thorax_plate", (0, y + 6, -4), (11, 2, 12), "chitin_lit")
    legs(fore, d, y)
    head = fore.group("h_head", (0, y + 1, -11))
    head.box("head", (0, y + 2, -16), (16, 14, 10), "chitin")
    for s in (-1, 1):
        head.box(f"fang_{s}", (s * 3, y - 5, -21), (2.5, 6, 2.5), "chitin_lit", rotation=(-20, 0, s * 10))
    mask(head, 0, y + 3, -22, 24, 28)
    # the spider's own eyes, too many of them, peeking out round the mask's edge
    for i, (ex, ey) in enumerate(((-12.5, 12), (12.5, 12), (-13.5, 7), (13.5, 7), (-10, 17), (10, 17))):
        head.box(f"spider_eye_{i}", (ex, y + ey, -19), (2, 2, 2), "eye")
    return model


VIEWS = v1.VIEWS


def main():
    for key in DIRECTIONS:
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = build(key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        sheet.direction_sheet(out, f"Brood Mother - {key} {DIRECTIONS[key]['title']}", stats, out / "sheet.png")
        print(key, stats["size_blocks"], stats["cubes"])
    items = [(k, v["title"]) for k, v in DIRECTIONS.items()]
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Brood Mother - three directions (session 1)")
    sheet.compare_sheet(OUT, items, OUT / "compare_material.png", heading="Brood Mother - material zones",
                        views=("flat_side", "flat_34", "flat_back"))


if __name__ == "__main__":
    main()
