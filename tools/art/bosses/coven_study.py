"""Witch Coven redesign, step 2: the character study of the cauldron witch (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

Built from vanilla's own parts at 1.45x, read from the 26.2 client (VillagerModel, WitchModel):
- the villager head 8x10x8 and nose 2x4x2;
- the robe ("jacket") 8x20x6;
- the witch's mole;
- the witch's hat: a 10x2x10 brim, then 7x4x7, 4x4x4 and a 1x2x1 tip, each tier offset back and bent a little more.

On top of vanilla:
- an old woman's stoop: the upper robe leans forward on rounded shoulders, with no hump;
- free sleeves with dark cuffs (no hands);
- a flat ragged hem hanging below the robe as she hovers;
- the extra-large cauldron roped to her back, its brew glowing in the role colour (green here, the healer).

Three faces on the same body ("the vanilla witch face, but more interesting"):
  F1  Vanilla, aged   vanilla's face exactly at 1.45x (unibrow, eyes, nose and mole), a heavier brow
  F2  The crone       a long nose bent down at the tip with two moles, a drooping brow, a jutting chin, small eyes
                      lit faintly in the role colour
  F3  Under the brim  the brim pulled down and tipped forward so the face is in its shadow, only two lit eyes and
                      the long nose showing, grey hair hanging from under the hat

Run from the repository root: python tools/art/bosses/coven_study.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s2_study"
K = 1.45
PALETTE = {
    "robe": (70, 58, 46), "robe_dark": (50, 41, 33), "hem": (58, 48, 38), "sleeve": (62, 51, 41), "cuff": (32, 26, 22),
    "skin": (152, 130, 100), "skin_dark": (126, 104, 80), "nose": (140, 116, 88), "mole": (96, 120, 60),
    "brow": (66, 52, 40), "eye": (44, 76, 44), "eye_glow": (150, 240, 110), "hair": (170, 166, 156), "shade": (30, 26, 30),
    "hat": (44, 36, 52), "hat_dark": (32, 26, 40), "band": (84, 98, 54),
    "iron": (60, 58, 64), "iron_dark": (36, 35, 40), "rope": (150, 128, 84), "glow": (120, 235, 90), "steam": (180, 240, 160),
    "herb": (86, 96, 58), "bone": (196, 186, 160),
}
FACES = {"F1": "Vanilla, aged", "F2": "The crone", "F3": "Under the brim"}


def hat(g, top, cz, brim_tilt=0.0, wide=1.0):
    """Vanilla's witch hat at 1.45x, made taller so it reads at this size: the brim, then three tiers, each set back
    and bent further, so the tip curls back the way vanilla's does."""
    h = g.group("hat", (0, top, cz), (brim_tilt, 0, 0))
    bw = 10 * K * wide
    h.box("hat_brim", (0, top + 1, cz), (bw, 2, bw), "hat")
    h.box("hat_band", (0.4, top + 2.9, cz + 0.6), (7 * K + 0.6, 1.8, 7 * K + 0.6), "band")
    y = top + 2
    # a stepped cone: each tier about two thirds the width of the one below, so it narrows like vanilla's
    t2 = h.group("hat_t2", (0.4, y, cz + 0.7), (-6, 0, 3))
    t2.box("hat_t2_box", (0.4, y + 2.9, cz + 0.7), (7 * K, 5.8, 7 * K), "hat")
    t3 = t2.group("hat_t3", (0.9, y + 5.8, cz + 1.8), (-14, 0, 5))
    t3.box("hat_t3_box", (0.9, y + 5.8 + 3.6, cz + 1.8), (4.6 * K, 7.2, 4.6 * K), "hat")
    t4 = t3.group("hat_tip", (1.4, y + 13, cz + 2.6), (-34, 0, 10))
    t4.box("hat_tip_box", (1.4, y + 13 + 3, cz + 2.6), (2.6, 6, 2.6), "hat_dark")


def ragged_hem(g, y, half_w, half_d):
    """The hovering hem: flat planes hanging from the robe's lower edge, torn into teeth (the rags go in the texture)."""
    for side in ("front", "back", "left", "right"):
        for i, (off, ln) in enumerate(((-0.75, 5), (-0.25, 4), (0.25, 5.8), (0.75, 4.4))):
            if side in ("front", "back"):
                z = -half_d if side == "front" else half_d
                g.box(f"hem_{side}_{i}", (off * half_w, y - ln / 2, z), (half_w * 0.5, ln, 0), "hem")
            else:
                x = -half_w if side == "left" else half_w
                g.box(f"hem_{side}_{i}", (x, y - ln / 2, off * half_d), (0, ln, half_d * 0.5), "hem")


def body(model, face):
    root = model.group("root", (0, 0, 0))
    lower = root.group("robe_lower", (0, 9, 0))
    rw, rd = 8 * K + 1, 6 * K + 1                          # the villager jacket (8x20x6, inflated 0.5) at 1.45x
    lower.box("robe_lower_box", (0, 15.5, 0), (rw, 13, rd), "robe")
    ragged_hem(lower, 9, rw / 2, rd / 2)
    lower.box("herb", (-rw / 2 - 0.8, 15, -1), (1.6, 6, 3), "herb", rotation=(0, 0, 6))
    lower.box("charm", (-rw / 2 - 0.8, 11, 1.5), (1.6, 2.4, 1.6), "bone")
    # the old woman's stoop: everything above the waist leans forward on the hips
    torso = root.group("torso", (0, 21, 0), (-11, 0, 0))
    m1.octo(torso, "robe_upper", (0, 29.5, 0), (rw, 17, rd), "robe", 0.22)
    torso.box("collar", (0, 37.5, -0.5), (rw - 2, 2, rd - 1), "robe_dark")
    # the extra-large cauldron on her back, roped round her middle
    cz = rd / 2 + 12.5
    # vanilla's cauldron, grown: a square iron pot with a lip, a dark band, notched sides and four stubby legs
    torso.box("cauldron", (0, 25, cz), (24, 20, 22), "iron")
    torso.box("cauldron_lip", (0, 35.6, cz), (26, 2.4, 24), "iron_dark")
    torso.box("cauldron_band", (0, 21, cz), (24.6, 2.4, 22.6), "iron_dark")
    torso.box("brew", (0, 36.4, cz), (21, 1.2, 19), "glow")
    for i, (x, h) in enumerate(((-4, 6), (3, 8), (8, 5))):
        torso.box(f"steam_{i}", (x, 37 + h / 2, cz + (i - 1) * 4), (1.6, h, 1.6), "steam")
    for sx in (-1, 1):
        torso.box(f"cauldron_ear_{sx}", (sx * 12.6, 30, cz), (1.6, 4, 6), "iron_dark")
        for sz in (-1, 1):
            torso.box(f"cauldron_leg_{sx}{sz}", (sx * 9.5, 13.6, cz + sz * 8.5), (4, 3.4, 4), "iron_dark")
    for i, y in enumerate((23, 30)):                       # two ropes round her middle and the cauldron
        torso.box(f"rope_front_{i}", (0, y, -rd / 2 - 0.4), (rw + 1.6, 1.4, 0.8), "rope")
        for sd in (-1, 1):
            torso.box(f"rope_side_{i}_{sd}", (sd * (rw / 2 + 0.4), y, cz / 2 - 1), (0.8, 1.4, cz + rd / 2 + 2), "rope")
        torso.box(f"rope_back_{i}", (0, y, cz + 11.4), (24.6, 1.4, 0.8), "rope")
    # free sleeves (no hands): the right raised forward, casting; the left low at her side
    for sd, cuff in ((1, (7, 29, -15)), (-1, (-9.5, 25, -3.5))):
        sh = (sd * (rw / 2 + 2.6), 35, -0.5)
        m1.tapered(torso, f"sleeve_{sd}", sh, cuff, 6.2, 6.8, "sleeve")
        torso.box(f"cuff_{sd}", cuff, (7.6, 7.6, 2.4), "cuff")
    torso.box("cast", (7, 29, -17.4), (3.4, 3.4, 3.4), "glow", rotation=(45, 45, 0))
    head = torso.group("hi_head", (0, 38, -1.5), (-4, 0, 0))
    hw, hh = 8 * K, 10 * K
    hc = (0, 38 + hh / 2, -1.5)
    head.box("head", hc, (hw, hh, hw), "skin")
    face_front = hc[2] - hw / 2
    FACE_BUILD[face](head, hc, hw, hh, face_front)
    return root


def face_vanilla(h, hc, hw, hh, f):
    x, y, z = hc
    h.box("brow", (x, y + 1.6, f - 0.5), (8 * K, 2.2, 1.4), "brow")          # vanilla's unibrow, a little heavier
    for sd in (-1, 1):
        h.box(f"eye_{sd}", (sd * 2 * K, y - 0.3, f - 0.2), (1.6, 1.6, 0.4), "eye")
    h.box("nose", (x, y - 3.2, f - 1.45), (2 * K, 4 * K, 2 * K + 0.4), "nose")
    h.box("mole", (x + 0.4, y - 5.3, f - 3.4), (1.2, 1.2, 1.2), "mole")
    hat(h, y + hh / 2, z)


def face_crone(h, hc, hw, hh, f):
    x, y, z = hc
    h.box("brow", (x, y + 1.3, f - 0.9), (8 * K + 0.4, 2.6, 2.2), "brow", rotation=(-14, 0, 0))   # a drooping brow shelf
    for sd in (-1, 1):
        h.box(f"eye_{sd}", (sd * 2.6, y - 0.6, f - 0.2), (1.4, 1.2, 0.4), "eye_glow")
        h.box(f"cheek_{sd}", (sd * 3.6, y - 2.8, f - 0.4), (3, 2.4, 1), "skin_dark")
    h.box("nose", (x, y - 2.0, f - 1.8), (2.4, 5.8, 3.0), "nose", rotation=(24, 0, 0))            # long, hooked down
    h.box("nose_tip", (x, y - 5.2, f - 3.9), (2.2, 2.6, 2.4), "nose", rotation=(50, 0, 0))
    h.box("mole", (x + 1.2, y - 4.4, f - 3.6), (1.2, 1.2, 1.2), "mole")
    h.box("mole_2", (x - 3.6, y + 0.2 - 2.0, f - 0.5), (1.1, 1.1, 1.1), "mole")
    h.box("chin", (x, y - hh / 2 + 0.6, f - 1.1), (5, 3, 2.6), "skin")                        # a jutting chin
    hat(h, y + hh / 2, z)


def face_brim(h, hc, hw, hh, f):
    x, y, z = hc
    h.box("shadow", (x, y + hh / 4, f - 0.3), (8 * K + 0.2, hh / 2 + 0.4, 0.6), "shade")      # the upper face in the brim's shadow
    for sd in (-1, 1):
        h.box(f"eye_{sd}", (sd * 2.6, y + 0.4, f - 0.7), (1.6, 1.2, 0.4), "eye_glow")
        for i in range(2):                                                                   # grey hair from under the hat
            h.box(f"hair_{sd}_{i}", (sd * (hw / 2 + 0.2), y - 1 - i * 1.5, z - 2 + i * 4), (0, 9 - i * 2, 3.2), "hair")
    h.box("hair_back", (x, y - 1.5, z + hw / 2 + 0.2), (hw - 2, 9, 0), "hair")
    h.box("nose", (x, y - 3.6, f - 2.2), (2 * K, 5 * K, 2 * K + 0.6), "nose", rotation=(14, 0, 0))
    h.box("mole", (x - 0.6, y - 6.6, f - 4.2), (1.2, 1.2, 1.2), "mole")
    hat(h, y + hh / 2 - 1.6, z - 0.5, brim_tilt=-12, wide=1.18)                # the brim pulled down, tipped forward


FACE_BUILD = {"F1": face_vanilla, "F2": face_crone, "F3": face_brim}
VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.4, "dist": 6, "target_z": 2.0, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": -35, "height": 2.8, "dist": 6.5, "target_z": 2.0},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.62, "dist": 3.6, "target_z": 2.6,
     "lens": 24, "player": False},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": -90, "height": 2.2, "dist": 6.5, "target_z": 2.0, "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 140, "height": 3.2, "dist": 6.5, "target_z": 2.0, "player": False},
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": -15, "height": 2.9, "dist": 2.6, "target_z": 2.75, "player": False},
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    items = []
    for key, title in FACES.items():
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = Model(f"occultech_witch_study_{key.lower()}")
        body(model, key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        items.append((key, title))
        print(key, stats["cubes"], stats["size_blocks"])
    sheet.compare_sheet(OUT, items, OUT / "study.png", heading="Witch Coven - the cauldron witch, three faces (step 2)",
                        views=("face", "front", "three_quarter", "player_eye", "side", "back"))


if __name__ == "__main__":
    main()
