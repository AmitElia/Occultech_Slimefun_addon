"""The Hollow Warlord redesign, session 1 step 1: three takes on the Headsman, as cuboid blockouts.

The brief (docs/art/bosses/hollow_warlord/overhaul/plan.md, 2026-11-18): the Nether fortress's executioner, a giant,
lean wither skeleton in a tall blackstone headsman's helm with one soul-cyan eye slit, the skull's jaw showing below; a
square-ended executioner's sword with a crimson brand down the fuller; three wither skeleton skulls he took, one per
guard of his warband, burning with soul fire while their guard lives.

The takes differ in where the three skulls are carried:

  A  the Yoke       a bone yoke across his shoulders, the skulls hung from its ends on iron hooks (two left, one right)
  B  the Girdle     a heavy belt over a leather apron, the skulls hung round his hips
  C  the Rack       three iron spikes fanned up from his back, a skull impaled on each, above his head

Each is shown resting (the sword on his shoulder), walking (dragging it behind) and sweeping (the hip-height whirl).
Model units: 16 = one block, y up, he faces -z, his right side is +x. The blue figure is a player (1.8 blocks).
Colours are blockout zones, not the palette.

Vanilla geometry (SkeletonModel; the wither skeleton draws it at 1.2x): head 8x8x8, body 8x12x4, limbs 2x12x2. Here
the skull is 2x (16); the bones are his own, taller and heavier than vanilla's sticks; the ribcage is real ribs.

Run from the repository root: python tools/art/bosses/headsman_silhouettes.py [A B C]
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import frame, obox  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s1_silhouettes"
PALETTE = {
    "bone": (118, 116, 124), "bone_dark": (84, 82, 92), "skull": (112, 110, 118), "socket": (30, 30, 36),
    "helm": (58, 56, 70), "helm_rim": (86, 82, 98), "slit": (90, 236, 244),
    "leather": (116, 82, 62), "leather_dark": (86, 60, 48), "iron": (150, 150, 160),
    "blade": (92, 96, 116), "guard": (70, 70, 84), "grip": (96, 70, 52), "brand": (226, 54, 50),
    "trophy": (176, 170, 160), "soul": (86, 232, 240), "yoke": (150, 136, 112),
}
REST, WALK, SWEEP = "rest", "walk", "sweep"
POSES = (REST, WALK, SWEEP)
HIP = 36.0                # the pelvis; everything on the torso is placed from here
SKULL = 16                # his own skull: the vanilla head at 2x
TROPHY = 12               # the taken skulls (their density is decided in the head study)
SWORD = {"blade": 54, "width": 11, "guard": 26, "grip": 14}


def _n(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def world(g, p):
    """A point given in g's rest space, in world space (after g's and its parents' rotations)."""
    return (g.world_matrix() @ np.array([*p, 1.0]))[:3]


def beam(g, name, a, b, w, mat, d=None):
    return v1.beam(g, name, tuple(map(float, a)), tuple(map(float, b)), w, mat, d)


def octo(g, name, c, r, h, mat):
    """An upright octagonal prism (a cross of two boxes plus the same pair turned 45 degrees), centre c."""
    side = 2 * r * math.tan(math.pi / 8)
    g.box(name + "_a", c, (2 * r, h, side + 0.01), mat)
    g.box(name + "_b", c, (side, h - 0.02, 2 * r), mat)
    g.box(name + "_c", c, (2 * r - 0.04, h - 0.04, side), mat, rotation=(0, 45, 0))
    g.box(name + "_d", c, (side - 0.02, h - 0.06, 2 * r - 0.04), mat, rotation=(0, 45, 0))


def T(x, y, z):
    """A torso point: y counted from the pelvis."""
    return (x, HIP + y, z)


# ---- the body ---------------------------------------------------------------------------------------------------------

def ribcage(t):
    """Spine, five ribs broadening to the chest, the sternum, the collar bar, the pelvis."""
    beam(t, "spine", T(0, 0, 3.5), T(0, 33, 3.5), 5, "bone")
    for i in range(5):
        y = 10 + i * 4.8
        hw = 8.5 + i * 1.3                      # half width: narrow at the waist, broad at the top
        front = -5 - i * 0.4
        for s, tag in ((-1, "l"), (1, "r")):
            beam(t, f"rib{i}_{tag}_side", T(s * hw, y, front + 1.8), T(s * hw * 0.65, y + 1.2, 4.2), 3, "bone")
            beam(t, f"rib{i}_{tag}_front", T(s * 1.8, y + 1.6, front), T(s * hw, y, front + 1.8), 3, "bone")
    t.box("sternum", T(0, 21, -6.2), (3.6, 19, 2.6), "bone")
    t.box("pelvis", T(0, 0.5, 0.5), (17, 7, 8.5), "bone_dark")


def gorget(t):
    """The blackstone gorget the helm sits on: a bevelled collar over the shoulders, the armour's lower half."""
    octo(t, "gorget", T(0, 31.2, 0.4), 13.5, 4.4, "helm")
    octo(t, "gorget_lip", T(0, 33.9, 0.4), 11.2, 1.6, "helm_rim")
    t.box("collar", T(0, 30.6, 0.6), (33, 4.2, 6), "bone")


def apron(t):
    """A heavy leather apron, front and back, from a wide belt."""
    t.box("belt", T(0, 2.5, 0.5), (20, 4.6, 11), "leather_dark")
    t.box("apron_front", T(0, -9, -6.6), (15, 22, 1.8), "leather", rotation=(-5, 0, 0), origin=T(0, 1, -6.6))
    t.box("apron_back", T(0, -6, 7.2), (15, 16, 1.8), "leather", rotation=(9, 0, 0), origin=T(0, 1, 7.2))


def head(t, pose, helm=True):
    """The neck and the vanilla skull at 2x; the tall blackstone headsman's helm over the cranium and eyes, its slit."""
    beam(t, "neck", T(0, 31, 1.5), T(0, 37, 0), 5, "bone")
    tilt = {REST: (10, 0, 0), WALK: (16, 0, 0), SWEEP: (12, -18, 0)}[pose]   # counter the stoop: he looks ahead
    base = HIP + 36
    h = t.group("head", (0, base, 0), tilt)
    h.box("skull", (0, base + SKULL / 2, -1), (SKULL, SKULL, SKULL), "skull")
    h.box("teeth", (0, base + 3.6, -9.05), (10, 1.2, 0.2), "socket")          # the teeth line, below the helm
    if not helm:
        for s in (-1, 1):
            h.box(f"socket_{s}", (s * 4, base + 9, -9.05), (4, 3, 0.2), "slit")
        return h
    rim = base + 6                                                              # the helm's lower edge
    top = base + SKULL + 7                                                      # 7 above the skull
    octo(h, "helm_rim", (0, rim + 1.3, -1), 11.3, 2.6, "helm_rim")              # a flared rim below the slit
    octo(h, "helm", (0, (rim + 2.6 + top) / 2, -1), 10.5, top - rim - 2.6, "helm")
    octo(h, "helm_crown", (0, top + 1, -1), 8.6, 2, "helm_rim")                 # the chamfered top, two steps in
    octo(h, "helm_cap", (0, top + 2.6, -1), 5.4, 1.2, "helm")
    h.box("slit_cut", (0, rim + 4.6, -11.35), (14, 2.8, 0.4), "socket")         # the eye slit, glowing in its cut
    h.box("slit", (0, rim + 4.6, -11.5), (11, 1.4, 0.4), "slit")
    h.box("nasal", (0, rim + 8.5, -11.35), (2.4, 9, 0.6), "helm_rim")           # a raised bar down the front
    return h


def arm(g, side, shoulder, elbow, hand, fist_dir=(0, -1, 0)):
    beam(g, f"upper_{side}", shoulder, elbow, 5, "bone")
    beam(g, f"fore_{side}", elbow, hand, 4.6, "bone")
    g.box(f"elbow_{side}", tuple(elbow), (6, 6, 6), "bone_dark")
    g.box(f"shoulder_{side}", tuple(shoulder), (8, 8, 8), "bone_dark")
    c = np.array(hand, float) + _n(fist_dir) * 2.5
    g.box(f"hand_{side}", tuple(c), (6.4, 7, 6.4), "bone")


def leg(g, side, hip, knee, ankle, toe_dir=(0, 0, -1)):
    beam(g, f"thigh_{side}", hip, knee, 5.6, "bone")
    beam(g, f"shin_{side}", knee, ankle, 5, "bone")
    g.box(f"knee_{side}", tuple(knee), (6.6, 6.6, 6.6), "bone_dark")
    f = np.array(ankle, float) + np.array([0, -2.2, 0]) + _n(toe_dir) * 3
    yaw = math.degrees(math.atan2(-toe_dir[0], -toe_dir[2]))
    g.box(f"foot_{side}", tuple(f), (6.4, 3.4, 12), "bone", rotation=(0, yaw, 0))


def sword(g, grip, tip_dir, flat_normal):
    """The executioner's sword from the middle of its grip: blade towards tip_dir, its flat facing flat_normal."""
    a = _n(tip_dir)
    w = _n(np.cross(flat_normal, a))
    m = frame(a, w)
    p = np.array(grip, float)
    G, B, W = SWORD["grip"], SWORD["blade"], SWORD["width"]
    obox(g, "grip", p, (G, 3.4, 3.4), m, "grip")
    obox(g, "pommel", p - a * (G / 2 + 2.2), (4.4, 5.4, 5.4), m, "guard")
    guard = p + a * (G / 2 + 1.6)
    obox(g, "guard", guard, (3.2, SWORD["guard"], 4.4), m, "guard")
    mid = guard + a * (1.6 + B / 2)
    obox(g, "blade", mid, (B, W, 2), m, "blade")
    obox(g, "brand", mid - a * 4, (B - 16, 2.6, 2.4), m, "brand")          # the brand-rune down the fuller
    return guard + a * (1.6 + B)                                            # the square end


# ---- poses ------------------------------------------------------------------------------------------------------------

def pose_body(m, pose):
    root = m.group("body", (0, 0, 0))
    ank = 5.0
    if pose == REST:
        lean, twist = 8, 0
        legs = {"r": ((6, HIP, 0), (7, 19, -2.5), (8, ank, 1)), "l": ((-6, HIP, 0), (-7, 19, -2.5), (-8, ank, 1))}
    elif pose == WALK:
        lean, twist = 15, 0
        legs = {"r": ((6, HIP, 0), (7, 19.5, 5), (7, ank, 15)), "l": ((-6, HIP, 0), (-7, 20, -11), (-7, ank, -9))}
    else:
        lean, twist = 14, -30
        legs = {"r": ((6, HIP, 0), (13, 19, -8), (17, ank, -6)), "l": ((-6, HIP, 0), (-13, 19, 5), (-17, ank, 9))}
    t = root.group("torso", (0, HIP, 0), (-lean, twist, 0))
    ribcage(t)
    gorget(t)
    apron(t)
    for side, (hip, knee, ankle) in legs.items():
        leg(root, side, hip, knee, ankle)
    return root, t


def take(m, key, pose):
    root, t = pose_body(m, pose)
    head(t, pose)
    sh_r, sh_l = world(t, T(15.5, 30, 0.6)), world(t, T(-15.5, 30, 0.6))
    if pose == REST:     # the sword on his right shoulder, the flat on it; the left arm hangs
        grip = np.array([13, 44, -9])
        sword(root, grip, (0.22, 0.72, 0.66), (-1, 0.4, 0))
        arm(root, "r", sh_r, sh_r + [4, -17, -6], grip + [0, -3, 0])
        arm(root, "l", sh_l, sh_l + [-4, -19, 1], sh_l + [-5, -37, -2])
    elif pose == WALK:   # dragged behind, the edge down, the flat to the side
        grip = np.array([16, 27, 12])
        sword(root, grip, (0.22, -0.4, 1), (1, 0, -0.22))
        arm(root, "r", sh_r, sh_r + [3, -18, 6], grip + [0, 2.5, 0])
        arm(root, "l", sh_l, sh_l + [-3, -17, -8], sh_l + [-4, -32, -15])
    else:                # the whirl: two hands, the blade level out to his right, the flat to the front
        grip = np.array([15, 38, -19])
        tip = _n([1, 0.04, 0.32])
        sword(root, grip, tip, (-0.32, 0, 1))
        arm(root, "r", sh_r, sh_r + [9, -12, -10], grip + tip * 3.5)
        arm(root, "l", sh_l, sh_l + [9, -16, -14], grip - tip * 3.5)
    trophies(root, t, key)


def skull_on(g, name, c, face=(0, 0, -1)):
    """A taken skull: the cube, two dark sockets and the jaw on the side it faces, soul fire on top."""
    c = np.array(c, float)
    g.box(name, tuple(c), (TROPHY, TROPHY, TROPHY), "trophy")
    f = _n(face)
    for s in (-1, 1):
        side = _n(np.cross((0, 1, 0), f)) * s * 2.8
        g.box(f"{name}_eye{s}", tuple(c + f * (TROPHY / 2 + 0.05) + side + [0, 1, 0]), (3, 2.4, 3), "socket")
    g.box(name + "_soul", tuple(c + [0, TROPHY / 2 + 2, 0]), (TROPHY * 0.6, 4, TROPHY * 0.6), "soul")


def hanging_skull(g, name, hook, length, face=(0, 0, -1)):
    """An iron hook straight down from `hook`, the skull hung plumb on it (whatever the body does)."""
    hook = np.array(hook, float)
    g.box(name + "_hook", tuple(hook - [0, length / 2, 0]), (1.6, length, 1.6), "iron")
    skull_on(g, name, hook - [0, length + TROPHY / 2 - 1, 0], face)


def trophies(root, t, key):
    if key == "A":       # the yoke: a beam across the shoulders behind the neck, its ends rising
        for s, tag in ((-1, "l"), (1, "r")):
            beam(t, f"yoke_{tag}", T(0, 33, 5.5), T(s * 22, 34, 5.5), 4.6, "yoke")
            beam(t, f"yoke_end_{tag}", T(s * 21, 33.9, 5.5), T(s * 31, 38, 5.5), 4, "yoke")
        hanging_skull(root, "trophy_r", world(t, T(30, 37.5, 5.5)), 9)
        hanging_skull(root, "trophy_l1", world(t, T(-23, 34.5, 5.5)), 7)
        hanging_skull(root, "trophy_l2", world(t, T(-31, 38, 5.5)), 20)
    elif key == "B":     # the girdle: hung from the belt round his hips, facing out
        for name, p, face in (("trophy_l1", T(-9.5, 2, -6), (-0.4, 0, -1)), ("trophy_l2", T(-11, 2, 4), (-1, 0, 0)),
                              ("trophy_r", T(10.5, 2, 4.5), (1, 0, 0.3))):
            hanging_skull(root, name, world(t, p), 9, face)   # low, swinging at the thighs
    else:                # the rack: three spikes fanned up from a plate on his back, a skull impaled on each
        t.box("rack_plate", T(0, 22, 7.6), (14, 18, 2.6), "leather_dark")
        for name, top in (("trophy_c", T(0, 84, 14)), ("trophy_l", T(-26, 64, 13)), ("trophy_r", T(26, 64, 13))):
            foot = np.array(T(top[0] * 0.12, 20, 8.8))
            beam(t, name + "_spike", foot, top, 2.2, "iron")
            skull_on(t, name, np.array(top) - _n(np.array(top) - foot) * 10)


TAKES = {"A": "The Yoke", "B": "The Girdle", "C": "The Rack"}


def build(key, pose):
    m = Model(f"headsman_{key}_{pose}")
    take(m, key, pose)
    return m, TAKES[key]


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 32, "height": 3.2, "dist": 14, "target_z": 3.0},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -26, "height": 1.62, "dist": 11, "target_z": 3.2},
]
LABELS = {"flat_34": "three-quarter", "sil_front": "front, silhouette", "sil_side": "side, silhouette",
          "clay_eye": "a player's eye"}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in POSES:
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == REST:
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Hollow Warlord {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(POSES):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
