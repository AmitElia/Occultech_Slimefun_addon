"""Witch Coven redesign, step 3: the three sisters as a set (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The face picked from the character study (s2_study, 2026-10-11): F1's eyes (vanilla's, at 1.45x), F2's drooping brow,
F3's long nose with the mole at its tip, under vanilla's witch hat. The body is the study's: the villager head and
robe at 1.45x, an old stoop, free cuffed sleeves (no hands), a ragged hem hanging as she hovers.

The sisters differ only by their vessels (each shown in one role colour; in the fight every sister takes every role):
  the cauldron  vanilla's cauldron grown huge, roped to her back; her sleeves cast and throw   (green, the healer)
  the bottles   a diagonal shoulder belt of large potion bottles, one more raised in her sleeve (purple, the curser)
  the pot       an iron pot held out in front of her in both sleeves                          (red, the bomber)

Run from the repository root: python tools/art/bosses/coven_set.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402
from bosses.coven_study import K, PALETTE as STUDY, hat, ragged_hem  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s3_set"
ROLE = {"green": ((120, 235, 90), (180, 240, 160)), "purple": ((176, 84, 230), (206, 160, 238)),
        "red": ((232, 76, 60), (240, 160, 140))}
PALETTE = dict(STUDY, glass=(170, 196, 196), cork=(124, 94, 62), strap=(86, 62, 42), buckle=(150, 140, 110))
for name, (g, s) in ROLE.items():
    PALETTE[f"glow_{name}"] = g
    PALETTE[f"steam_{name}"] = s
SISTERS = [("cauldron", "green", "The cauldron"), ("bottles", "purple", "The bottles"), ("pot", "red", "The pot")]
RW, RD = 8 * K + 1, 6 * K + 1          # the villager robe at 1.45x


def face(h, hc, hw, hh, f):
    """F1's eyes, F2's drooping brow, F3's long nose with the mole at its tip."""
    x, y, z = hc
    h.box("brow", (x, y + 1.3, f - 0.9), (8 * K + 0.4, 2.6, 2.2), "brow", rotation=(-14, 0, 0))
    for sd in (-1, 1):
        h.box(f"eye_{sd}", (sd * 2 * K, y - 0.6, f - 0.2), (1.6, 1.6, 0.4), "eye")
    h.box("nose", (x, y - 3.6, f - 2.2), (2 * K, 5 * K, 2 * K + 0.6), "nose", rotation=(14, 0, 0))
    h.box("mole", (x - 0.6, y - 6.6, f - 4.2), (1.2, 1.2, 1.2), "mole")
    hat(h, y + hh / 2, z)


def sleeve(torso, sd, cuff, shoulder_y=35):
    sh = (sd * (RW / 2 + 2.6), shoulder_y, -0.5)
    m1.tapered(torso, f"sleeve_{sd}", sh, cuff, 6.2, 6.8, "sleeve")
    torso.box(f"cuff_{sd}", cuff, (7.6, 7.6, 2.4), "cuff")


def bottle(g, name, c, role, size=1.0, rot=(0, 0, 0)):
    """A large potion bottle: a round body of glowing brew in glass, a neck, a cork."""
    x, y, z = c
    s = size
    g.box(name, (x, y, z), (5 * s, 5 * s, 5 * s), f"glow_{role}", rotation=rot)
    g.box(name + "_glass", (x, y + 2.2 * s, z), (5.6 * s, 1.2 * s, 5.6 * s), "glass", rotation=rot)
    g.box(name + "_neck", (x, y + 3.6 * s, z), (2.2 * s, 2.2 * s, 2.2 * s), "glass", rotation=rot)
    g.box(name + "_cork", (x, y + 5.1 * s, z), (1.8 * s, 1.4 * s, 1.8 * s), "cork", rotation=rot)


def witch(model, vessel, role):
    root = model.group("root", (0, 0, 0))
    lower = root.group("robe_lower", (0, 9, 0))
    lower.box("robe_lower_box", (0, 15.5, 0), (RW, 13, RD), "robe")
    ragged_hem(lower, 9, RW / 2, RD / 2)
    lower.box("herb", (-RW / 2 - 0.8, 15, -1), (1.6, 6, 3), "herb", rotation=(0, 0, 6))
    lower.box("charm", (-RW / 2 - 0.8, 11, 1.5), (1.6, 2.4, 1.6), "bone")
    torso = root.group("torso", (0, 21, 0), (-11, 0, 0))            # the old stoop
    m1.octo(torso, "robe_upper", (0, 29.5, 0), (RW, 17, RD), "robe", 0.22)
    torso.box("collar", (0, 37.5, -0.5), (RW - 2, 2, RD - 1), "robe_dark")
    glow, steam = f"glow_{role}", f"steam_{role}"
    if vessel == "cauldron":
        cz = RD / 2 + 12.5
        torso.box("cauldron", (0, 25, cz), (24, 20, 22), "iron")
        torso.box("cauldron_lip", (0, 35.6, cz), (26, 2.4, 24), "iron_dark")
        torso.box("cauldron_band", (0, 21, cz), (24.6, 2.4, 22.6), "iron_dark")
        torso.box("brew", (0, 36.4, cz), (21, 1.2, 19), glow)
        for i, (x, h, lean) in enumerate(((-4, 5, 10), (3, 6.5, -8), (8, 4, 12))):
            torso.box(f"steam_{i}", (x, 37 + h / 2, cz + (i - 1) * 4), (1.2, h, 1.2), steam, rotation=(0, 0, lean))
        for sx in (-1, 1):
            torso.box(f"cauldron_ear_{sx}", (sx * 12.6, 30, cz), (1.6, 4, 6), "iron_dark")
            for sz in (-1, 1):
                torso.box(f"cauldron_leg_{sx}{sz}", (sx * 9.5, 13.6, cz + sz * 8.5), (4, 3.4, 4), "iron_dark")
        for i, y in enumerate((23, 30)):
            torso.box(f"rope_front_{i}", (0, y, -RD / 2 - 0.4), (RW + 1.6, 1.4, 0.8), "rope")
            for sd in (-1, 1):
                torso.box(f"rope_side_{i}_{sd}", (sd * (RW / 2 + 0.4), y, cz / 2 - 1), (0.8, 1.4, cz + RD / 2 + 2), "rope")
            torso.box(f"rope_back_{i}", (0, y, cz + 11.4), (24.6, 1.4, 0.8), "rope")
        sleeve(torso, 1, (7, 29, -15))
        sleeve(torso, -1, (-9.5, 25, -3.5))
        torso.box("cast", (7, 29, -17.4), (3.4, 3.4, 3.4), glow, rotation=(45, 45, 0))
    elif vessel == "bottles":
        # a belt from her left shoulder across her chest to her right hip, round her back; big bottles ride it
        fz = -RD / 2 - 0.5
        torso.box("strap_front", (0, 29, fz), (2.4, 22, 1), "strap", rotation=(0, 0, -38))
        torso.box("strap_back", (0, 29, RD / 2 + 0.5), (2.4, 22, 1), "strap", rotation=(0, 0, 38))
        torso.box("buckle", (0, 29, fz - 0.6), (3.2, 3.2, 0.6), "buckle", rotation=(0, 0, -38))
        for i, t in enumerate((-0.62, -0.2, 0.22, 0.64)):
            bx, by = 7.6 * t * 1.05, 29 - 9.5 * t
            bottle(torso, f"bottle_{i}", (bx, by - 1, fz - 3.2), role, 0.95, rot=(0, 0, -12 + i * 6))
        sleeve(torso, 1, (9, 38, -12))
        bottle(torso, "bottle_held", (9.5, 44, -13), role, 1.15, rot=(0, 0, -10))
        sleeve(torso, -1, (-9.5, 25, -3.5))
    else:
        # an iron pot held out in front in both sleeves, its brew steaming
        pz = -14
        torso.box("pot", (0, 18.5, pz), (14, 9, 12), "iron")
        torso.box("pot_lip", (0, 23.6, pz), (15.4, 1.8, 13.4), "iron_dark")
        torso.box("pot_brew", (0, 24.1, pz), (12, 1.2, 10), glow)
        torso.box("pot_base", (0, 13.5, pz), (10, 1.6, 8), "iron_dark")
        for i, (x, h, lean) in enumerate(((-3, 4, 10), (2, 5.5, -8))):
            torso.box(f"steam_{i}", (x, 25 + h / 2, pz + (i - 0.5) * 3), (1.2, h, 1.2), steam, rotation=(0, 0, lean))
        for sd in (-1, 1):
            torso.box(f"pot_handle_{sd}", (sd * 8.2, 21.5, pz), (2.2, 2, 5), "iron_dark")
            sleeve(torso, sd, (sd * 10, 22, pz + 1))
    head = torso.group("hi_head", (0, 38, -1.5), (-4, 0, 0))
    hw, hh = 8 * K, 10 * K
    hc = (0, 38 + hh / 2, -1.5)
    head.box("head", hc, (hw, hh, hw), "skin")
    face(head, hc, hw, hh, hc[2] - hw / 2)
    return root


def build(vessel, role):
    model = Model(f"occultech_coven_{vessel}")
    witch(model, vessel, role)
    return model


def shifted(boxes, dx):
    out = []
    for b in boxes:
        b = dict(b)
        b["corners"] = (np.array(b["corners"]) + np.array([dx, 0, 0])).tolist()
        out.append(b)
    return out


SET_VIEWS = [
    {"name": "set_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.3, "dist": 10, "target_z": 2.0},
    {"name": "set_34", "mode": "flat", "camera": "persp", "yaw": -32, "height": 3.0, "dist": 11, "target_z": 2.0},
    {"name": "set_eye", "mode": "flat", "camera": "persp", "yaw": -12, "height": 1.62, "dist": 6.5, "target_z": 2.5,
     "lens": 24, "player": False},
    {"name": "set_back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 3.0, "dist": 11, "target_z": 2.0},
    {"name": "set_side", "mode": "silhouette", "camera": "ortho_side"},
]
ONE_VIEWS = [
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": -18, "height": 2.9, "dist": 2.8, "target_z": 2.75, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": -35, "height": 2.8, "dist": 6.5, "target_z": 2.0},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": -90, "height": 2.2, "dist": 6.5, "target_z": 2.0, "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 3.0, "dist": 6.5, "target_z": 2.0, "player": False},
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    boxes, items = [], []
    for i, (vessel, role, title) in enumerate(SISTERS):
        model = build(vessel, role)
        out = OUT / vessel
        out.mkdir()
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, ONE_VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        boxes += shifted(model.render_json(PALETTE), (i - 1) * 44)
        items.append((vessel, title))
        print(vessel, stats["cubes"], stats["size_blocks"])
    v2.run_blender(boxes, OUT, SET_VIEWS)
    sheet.compare_sheet(OUT, items, OUT / "sisters.png", heading="Witch Coven - the three sisters (step 3)",
                        views=("face", "three_quarter", "side", "back"))
    from PIL import Image, ImageDraw
    tiles = [Image.open(OUT / f"{v['name']}.png") for v in SET_VIEWS[:4]]
    w, h = tiles[0].size
    img = Image.new("RGB", (w * 2 + 30, h * 2 + 80), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((10, 14), "Witch Coven - the coven together: front, three-quarter, player's eye, back", font=sheet._font(30),
            fill=sheet.INK)
    for n, t in enumerate(tiles):
        img.paste(t, (10 + (n % 2) * (w + 10), 60 + (n // 2) * (h + 10)))
    img.save(OUT / "coven.png")


if __name__ == "__main__":
    main()
