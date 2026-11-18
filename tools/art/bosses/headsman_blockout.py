"""The Hollow Warlord (the Headsman), session 1 step 3: the full blockout.

Picked (2026-11-18): take 2's A, the Plate (s1_take2), with H3, the Kettle Hat, and S1, the Executioner's sword
(s1_study). The skulls carry the real wither skeleton pixels (26.2 client) at 2x, the eyes lit soul cyan.

Poses, one per moment of the fight (HollowWarlord.java):
  idle     the sword's point on the floor ahead, the skulls lit (his guards shield him)
  walk     dragging the sword behind him
  windup   the soul sweep's warning: twisted back, the blade trailing low behind his right side
  sweep    the whirl: the blade level at hip height, two hands
  enraged  below 35%: the hat torn off, bare skull, lower and faster, the sword cocked over his shoulder
  death    on one knee, the sword driven into the floor, head bowed; the skulls gone dark, sinking

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/headsman_blockout.py <folder> [pose ...]
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Group, Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import headsman_study as st, headsman_take2 as h2, volley_crone_s2 as v2  # noqa: E402
from bosses.headsman_silhouettes import _n, beam, world  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s1_blockout"
HIP = h2.HIP
T = h2.T
POSES = ("idle", "walk", "windup", "sweep", "enraged", "death")


def translate(g, d):
    """Moves a whole group subtree (bosskit has no translation on a bone, so the geometry and pivots move)."""
    d = np.array(d, float)
    g.origin = (np.array(g.origin) + d).tolist()
    for ch in g.children:
        if isinstance(ch, Group):
            translate(ch, d)
        else:
            ch.frm = (np.array(ch.frm) + d).tolist()
            ch.to = (np.array(ch.to) + d).tolist()
            ch.origin = (np.array(ch.origin) + d).tolist()


# per pose: lean, twist, hip drop, head tilt (x, y), helm on, skulls lit, legs {side: (hip, knee, ankle, toe)}
A = 5.0
POSE = {
    "idle": dict(lean=18, twist=0, drop=0, head=(14, 0), helm=True, lit=True,
                 legs={"r": ((7, HIP, 0), (10, 18, -6), (11, A, -1), (0, 0, -1)),
                       "l": ((-7, HIP, 0), (-10, 18, -2), (-12, A, 4), (0, 0, -1))}),
    "walk": dict(lean=22, twist=0, drop=0, head=(18, 0), helm=True, lit=True,
                 legs={"r": ((7, HIP, 0), (9, 18, 4), (9, A, 16), (0, 0, -1)),
                       "l": ((-7, HIP, 0), (-9, 17, -12), (-9, A, -10), (0, 0, -1))}),
    "windup": dict(lean=20, twist=34, drop=3, head=(16, -30), helm=True, lit=True,
                   legs={"r": ((7, HIP - 3, 0), (14, 16, 4), (18, A, 10), (0.3, 0, -1)),
                         "l": ((-7, HIP - 3, 0), (-14, 16, -9), (-18, A, -8), (-0.2, 0, -1))}),
    "sweep": dict(lean=20, twist=-32, drop=0, head=(14, -20), helm=True, lit=True,
                  legs={"r": ((7, HIP, 0), (15, 17, -9), (20, A, -6), (0, 0, -1)),
                        "l": ((-7, HIP, 0), (-15, 17, 6), (-20, A, 10), (0, 0, -1))}),
    "enraged": dict(lean=22, twist=12, drop=5, head=(10, -6), helm=False, lit=True,
                    legs={"r": ((7, HIP - 5, 0), (12, 15, 6), (13, A, 13), (0, 0, -1)),
                          "l": ((-7, HIP - 5, 0), (-12, 16, -12), (-13, A, -11), (0, 0, -1))}),
    "death": dict(lean=26, twist=0, drop=13, head=(-8, 0), helm=True, lit=False,
                  legs={"r": ((7, HIP - 13, 0), (8, 4.5, -3), (8, 4, 15), (0, -0.4, 1)),
                        "l": ((-7, HIP - 13, 0), (-8, 18, -17), (-9, A, -14), (0, 0, -1))}),
}


def build(pose):
    p = POSE[pose]
    m = Model(f"headsman_{pose}")
    root = m.group("body", (0, 0, 0))
    for tag, (hp, kn, an, toe) in p["legs"].items():
        h2.leg(root, tag, hp, kn, an, toe)
    t = root.group("torso", (0, HIP, 0), (-p["lean"], p["twist"], 0))
    h2.spine_and_waist(t)
    h2.tabard(t)
    h2.breastplate(t)
    h2.bone_chest(t)
    h2.pauldron(t, 1)
    h2.pauldron(t, -1)
    h2.gorget(t)
    base = HIP + 35
    beam(t, "neck", T(0, 29, 2), (0, base + 1, -3), 6, "bone")
    tx, ty = p["head"]
    hd = t.group("head", (0, base, -3), (tx, ty, 0))
    hd.box("skull", (0, base + 8, -3), (16, 16, 16), "skull")      # replaced by the pixel skull below
    hd.box("teeth", (0, base + 3.4, -11.05), (11, 1.2, 0.2), "socket")
    if p["helm"]:
        st.helm_kettle(hd, base)
    else:
        st.face(hd, base)
    for c in hd.children:     # authored for a skull centred at z -1: move to the skull at z -3
        if hasattr(c, "frm"):
            c.frm[2] -= 2
            c.to[2] -= 2
            c.origin[2] -= 2
    if p["drop"]:
        translate(t, (0, -p["drop"], 0))
    # the taken skulls
    head_c = world(hd, (0, base + 8, -3))
    if p["lit"]:
        st.taken_skull_fn = st.taken_skull
        h2.taken_skull = st.taken_skull
        h2.halo(root, head_c, p["twist"])
    else:                      # dark, fallen to the floor round him, tipped where they landed
        for name, x, z, yaw, roll in (("taken_c", 4, 26, 20, 0), ("taken_l", -30, -6, -50, 18),
                                      ("taken_r", 32, 8, 35, -12)):
            st.pixel_skull(root, (x, 8.6 if not roll else 9.6, z), (0, yaw, roll), eyes=False, name=name)
    arms(root, t, pose)
    return m


def arms(root, t, pose):
    sh_r, sh_l = world(t, T(h2.SH + 1, 31, 0)), world(t, T(-h2.SH - 1, 31, 0))
    sw, arm = st.sword_executioner, h2.arm
    if pose == "idle":
        grip = np.array([17, 40, -12])
        sw(root, grip, _n([0.25, -0.62, -1]), (1, 0.2, -0.1))
        arm(root, "r", sh_r, sh_r + [6, -18, 2], grip + [0, 3, 0], True)
        arm(root, "l", sh_l, sh_l + [-6, -20, -2], sh_l + [-7, -40, -8], True)
    elif pose == "walk":
        grip = np.array([19, 28, 12])
        sw(root, grip, (0.22, -0.33, 1), (1, 0, -0.22))
        arm(root, "r", sh_r, sh_r + [4, -19, 7], grip + [0, 3, 0], True)
        arm(root, "l", sh_l, sh_l + [-4, -18, -9], sh_l + [-5, -36, -18], True)
    elif pose == "windup":
        tip = _n([0.55, -0.32, 0.78])
        grip = np.array([22, 32, 10])
        sw(root, grip, tip, (0.8, 0.2, -0.55))
        arm(root, "r", sh_r, sh_r + [7, -16, 8], grip + tip * 3.5, True)
        arm(root, "l", sh_l, sh_l + [10, -18, 2], grip - tip * 3.5, True)
    elif pose == "sweep":
        tip = _n([1, 0.04, 0.32])
        grip = np.array([17, 36, -24])
        sw(root, grip, tip, (-0.32, 0, 1))
        arm(root, "r", sh_r, sh_r + [10, -13, -12], grip + tip * 4, True)
        arm(root, "l", sh_l, sh_l + [10, -17, -16], grip - tip * 4, True)
    elif pose == "enraged":      # cocked over the right shoulder, the blade hanging back behind him
        tip = _n([0.2, -0.42, 1])
        grip = np.array([15, 76, -2])
        sw(root, grip, tip, (1, 0.2, 0))
        arm(root, "r", sh_r, sh_r + [9, 2, -6], grip + tip * 3.5, True)
        arm(root, "l", sh_l, sh_l + [8, 4, -16], grip - tip * 3.5, True)
    else:                        # death: driven into the floor before him, both hands on the grip
        grip = np.array([0, 44, -24])
        tip = _n([0, -1, -0.08])
        sw(root, grip, tip, (0, 0, -1))
        arm(root, "r", sh_r, sh_r + [3, -14, -12], grip + [2.5, 2, 0], True)
        arm(root, "l", sh_l, sh_l + [-3, -14, -12], grip + [-2.5, 2, 0], True)


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 2.8, "dist": 14, "target_z": 3.4},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "flat_eye", "mode": "flat", "camera": "persp", "yaw": -24, "height": 1.62, "dist": 9, "target_z": 3.6,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_front": "front", "sil_side": "side", "flat_eye": "a player's eye"}


def main(args):
    st.SKIN = Image.open(Path(args[0]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    v2.PALETTE.update(h2.PALETTE)
    OUT.mkdir(parents=True, exist_ok=True)
    poses = args[1:] or POSES
    for pose in poses:
        if (OUT / pose).exists():
            shutil.rmtree(OUT / pose)
        m = build(pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS)
        lo, hi = m.bounds()
        print(pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes),
              "lowest", round(float(lo[1]), 1))
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Hollow Warlord, the Headsman - full blockout (Plate, Kettle Hat, Executioner's sword)",
            font=sheet._font(26), fill=sheet.INK)
    for r, pose in enumerate(POSES):
        for c, v in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            f = OUT / pose / f"{v['name']}.png"
            if f.exists():
                img.paste(sheet._tile(f, tw, th), (x, y))
            dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


if __name__ == "__main__":
    main(sys.argv[1:])
