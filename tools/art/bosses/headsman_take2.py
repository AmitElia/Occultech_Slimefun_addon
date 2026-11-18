"""The Hollow Warlord (the Headsman), session 1 step 1, take 2: a complete overhaul after take 1.

User (2026-11-18) on take 1: all three looked extremely goofy; too lean in the shoulders; the bucket helm looked goofy;
keep the idea of the three skulls, but floating above and behind his head, where the Rack put them.

What changed: a heavy, hunched top (broad shoulders, the head set low between them, long heavy arms, a V down to a
narrow, hollow waist), bent knees, a tattered tabard instead of the apron, and the three taken skulls floating in an arc
behind his head with soul fire trailing under each (no spikes). The takes differ in build and helm:

  A  the Plate      blackstone plate over the chest and layered pauldrons with raised neck guards; a sallet helm,
                    swept back, the slit at the eyes, the jaw bare; the waist bare bone (the hollow)
  B  the Ossuary    no plate: the skeleton itself is massive (huge collarbones, flaring ribs, shoulder blades jutting up);
                    a riveted blackstone mask across the eyes, the cranium bare
  C  the Butcher    one-sided: the sword arm in a huge pauldron and gauntlet, the other side bare ribs and bone;
                    a rounded closed helm with a jutting brow

Each is shown resting (the sword's point on the floor in front), walking (dragging it) and sweeping (the hip-height
whirl). Model units: 16 = one block, y up, he faces -z, his right side is +x. Colours are blockout zones.

Run from the repository root: python tools/art/bosses/headsman_take2.py [A B C]
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
from bosses import volley_crone_s2 as v2  # noqa: E402
from bosses.headsman_silhouettes import PALETTE as P1, _n, beam, octo, sword, world  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s1_take2"
PALETTE = dict(P1, plate=(66, 64, 78), plate_lit=(96, 92, 110), cloth=(64, 52, 58), cloth_dark=(46, 38, 44),
               flame=(120, 240, 246))
REST, WALK, SWEEP = "rest", "walk", "sweep"
POSES = (REST, WALK, SWEEP)
HIP = 34.0
SKULL = 16           # his skull, the vanilla head at 2x
TROPHY = 16          # the taken skulls at the same 2x (one density)
SH = 19.0            # shoulder joints at +-SH


def T(x, y, z):
    return (x, HIP + y, z)


# ---- the torso pieces (in the torso group; y from the pelvis) ---------------------------------------------------------

def spine_and_waist(t):
    """The bare waist, the hollow: pelvis, spine, two short floating ribs."""
    t.box("pelvis", T(0, 1, 0.5), (19, 8, 10), "bone_dark")
    beam(t, "spine", T(0, 3, 4), T(0, 30, 4), 6, "bone")
    for i, y in enumerate((9, 14)):
        for s, tag in ((-1, "l"), (1, "r")):
            beam(t, f"low_rib{i}_{tag}", T(s * 2, y, 5), T(s * 9, y - 1, -1), 3.2, "bone")


def breastplate(t, half=None):
    """A keeled blackstone breastplate from the waist up: two plates meeting in a ridge, broad at the top.
    half: None = both sides, 1 = the right side only."""
    sides = ((-1, "l"), (1, "r")) if half is None else ((half, "r" if half > 0 else "l"),)
    for s, tag in sides:
        t.box(f"chest_{tag}", T(s * 7.5, 27, -2.5), (16, 14, 12), "plate", rotation=(0, s * 14, -s * 12))
        t.box(f"chest_{tag}_lit", T(s * 6.5, 27, -8.4), (13, 12, 1.2), "plate_lit", rotation=(0, s * 24, -s * 12))
        t.box(f"flank_{tag}", T(s * 12.5, 27, 2.5), (7, 13, 14), "plate", rotation=(0, 0, -s * 16))
        t.box(f"back_{tag}", T(s * 7, 27, 7), (14, 14, 5), "plate")
    if half is None:
        t.box("keel", T(0, 26, -9.4), (3, 14, 2.4), "plate_lit")


def bone_chest(t, side=None):
    """The bare ribcage, massive: five flaring ribs, a sternum, huge collarbones. side: None = both, -1 = left only."""
    sides = ((-1, "l"), (1, "r")) if side is None else ((side, "l" if side < 0 else "r"),)
    for i in range(5):
        y = 15 + i * 3.9
        hw = 10 + i * 1.6
        front = -6 - i * 0.5
        for s, tag in sides:
            beam(t, f"rib{i}_{tag}_side", T(s * hw, y, front + 2.5), T(s * hw * 0.62, y + 1.5, 6), 3.6, "bone")
            beam(t, f"rib{i}_{tag}_front", T(s * 2.2, y + 2, front), T(s * hw, y, front + 2.5), 3.6, "bone")
    if side is None:
        t.box("sternum", T(0, 24, -8.6), (4.4, 18, 3), "bone")
    for s, tag in sides:
        beam(t, f"clavicle_{tag}", T(s * 1.5, 33, -4), T(s * (SH + 1), 34, 0), 5.5, "bone")


def scapulae(t):
    """Shoulder blades jutting up behind the shoulders like fins."""
    for s, tag in ((-1, "l"), (1, "r")):
        t.box(f"scapula_{tag}", T(s * 11, 33, 8.5), (12, 22, 3.2), "bone", rotation=(-14, -s * 12, -s * 16))
        t.box(f"scapula_{tag}_ridge", T(s * 12.5, 38, 9.5), (4, 18, 4), "bone_dark", rotation=(-14, -s * 12, -s * 22))


def pauldron(t, s, big=1.0):
    """Layered blackstone lames over the shoulder, sloping down and out, with a raised guard on the neck side."""
    tag = "r" if s > 0 else "l"
    sx, sy = s * SH, HIP + 32
    k = big
    for i, (dx, dy, w, ang) in enumerate(((2, 6.5, 20, 16), (6, 2.5, 21, 30), (9.5, -2, 19, 46))):
        t.box(f"pauldron_{tag}{i}", (sx + s * dx * k, sy + dy * k, 0.5), (w * k, 4.6 * k, 20 * k),
              "plate" if i % 2 == 0 else "plate_lit", rotation=(0, 0, -s * ang))
    t.box(f"guard_{tag}", (sx - s * 4.5 * k, sy + 8.5, 1), (3.4, 7, 17 * k), "plate", rotation=(0, 0, s * 18))


def gorget(t):
    octo(t, "gorget", T(0, 33.5, 0.5), 11, 4.2, "plate")


def tabard(t, ragged=True):
    """A belt and a dark tattered tabard: two front strips and two back strips of different lengths."""
    t.box("belt", T(0, 2.5, 0.5), (19, 3.6, 11), "leather_dark")
    for name, x, z, length, ang in (("tab_fl", -2.6, -6.5, 24, -8), ("tab_fr", 2.8, -6.6, 18, -6),
                                    ("tab_bl", -3, 7, 20, 10), ("tab_br", 3, 7.1, 25, 12)):
        t.box(name, (x, HIP - length / 2 + 1, z), (5.4, length, 1.6), "cloth" if "f" in name else "cloth_dark",
              rotation=(ang, 0, 0), origin=(x, HIP + 1, z))


# ---- the helms (in the head group, the skull from `base` to base + 16) ------------------------------------------------

def helm_sallet(h, base):
    """A sallet: a low dome down to the eyes, swept back into a long tail; the slit at the eyes; the jaw bare."""
    octo(h, "sallet", (0, base + 12.4, -0.5), 10.2, 10, "plate")
    octo(h, "sallet_top", (0, base + 18.2, 0), 8.2, 1.8, "plate_lit")
    h.box("sallet_comb", (0, base + 19.2, 1), (2.6, 2.4, 19), "plate")
    h.box("sallet_tail", (0, base + 9.5, 12), (19.6, 3, 13), "plate", rotation=(24, 0, 0))
    h.box("sallet_tail_lip", (0, base + 5.4, 18.6), (17, 2.2, 4), "plate_lit", rotation=(24, 0, 0))
    h.box("slit_cut", (0, base + 9.2, -10.75), (16, 2.4, 0.4), "socket")
    h.box("slit", (0, base + 9.2, -10.95), (12, 1.2, 0.4), "slit")
    h.box("visor_lip", (0, base + 7.6, -10.9), (18, 1.4, 1.6), "plate_lit")


def helm_mask(h, base):
    """A riveted blackstone mask across the eyes and nose, wrapped round to the temples; the cranium bare."""
    h.box("mask", (0, base + 9.2, -9.6), (18, 7.4, 2.6), "plate")
    for s in (-1, 1):
        h.box(f"mask_side{s}", (s * 8.9, base + 9.2, -4), (2.2, 6, 11), "plate")
        h.box(f"mask_eye{s}", (s * 4.2, base + 10, -11), (3.6, 2.2, 0.4), "slit")
        h.box(f"rivet{s}", (s * 7.6, base + 11.8, -11), (1.4, 1.4, 0.6), "iron")
    h.box("mask_brow", (0, base + 13.4, -9.4), (18.6, 1.8, 3.4), "plate_lit")
    h.box("band", (0, base + 13.4, -1), (16.6, 1.8, 16.6), "plate")


def helm_closed(h, base):
    """A rounded closed helm over the whole skull, a heavy brow jutting over the slit, a low comb."""
    octo(h, "closed", (0, base + 8.4, -1), 10.4, 17.6, "plate")
    octo(h, "closed_top", (0, base + 17.9, -1), 8, 1.6, "plate_lit")
    h.box("brow", (0, base + 11.4, -11.8), (18, 3.2, 4), "plate_lit", rotation=(-12, 0, 0))
    h.box("slit_cut", (0, base + 9, -11.15), (14, 2, 0.4), "socket")
    h.box("slit", (0, base + 9, -11.35), (10, 1, 0.4), "slit")
    h.box("comb", (0, base + 19.2, -1), (2.4, 3, 16), "plate")
    for i in range(3):
        h.box(f"breath{i}", (3.5, base + 3.2 + i * 1.8, -11.15), (5, 0.8, 0.4), "socket")


# ---- the floating skulls ----------------------------------------------------------------------------------------------

def taken_skull(g, name, c, yaw=0.0, lit=True, roll=0.0):
    """A floating wither skull: the cube, its sockets and jaw on the front, soul fire trailing under it."""
    c = np.array(c, float)
    g.box(name, tuple(c), (TROPHY, TROPHY, TROPHY), "trophy", rotation=(0, yaw, roll))
    f = np.array([-math.sin(math.radians(yaw)), 0, -math.cos(math.radians(yaw))])
    r = np.array([math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw))])
    for s in (-1, 1):
        g.box(f"{name}_eye{s}", tuple(c + f * (TROPHY / 2 + 0.05) + r * s * 3.6 + [0, 1.5, 0]), (4, 3.2, 0.4),
              "soul" if lit else "socket", rotation=(0, yaw, 0))
    g.box(f"{name}_jaw", tuple(c + f * (TROPHY / 2 + 0.05) + [0, -4.6, 0]), (9, 1.4, 0.4), "socket", rotation=(0, yaw, 0))
    if lit:      # soul fire trailing under it, narrowing
        for i, (w, h) in enumerate(((9, 3.4), (4.4, 3.4))):
            g.box(f"{name}_fire{i}", tuple(c + [0, -TROPHY / 2 - 1.6 - i * 3.2, 2 + i * 1.6]), (w, h, w), "flame",
                  rotation=(0, 45 * (i % 2) + yaw, 0))


def halo(g, head_c, twist=0.0):
    """The three taken skulls floating in a wide arc high behind his head (world space: they don't lean with him),
    turned a little towards the middle, the side ones tipped."""
    hx, hy, hz = head_c
    a = math.radians(twist)
    for name, dx, dy, dz, yaw, roll in (("taken_c", 0, 38, 20, 0, 0), ("taken_l", -30, 28, 16, -20, 12),
                                        ("taken_r", 30, 28, 16, 20, -12)):
        x, z = dx * math.cos(a) + dz * math.sin(a), -dx * math.sin(a) + dz * math.cos(a)
        taken_skull(g, name, (hx + x, hy + dy, hz + z), yaw + twist, roll=roll)


# ---- assembly ---------------------------------------------------------------------------------------------------------

def arm(g, tag, shoulder, elbow, hand, gauntlet, plate_upper=False):
    beam(g, f"upper_{tag}", shoulder, elbow, 6.4, "bone")
    g.box(f"elbow_{tag}", tuple(elbow), (7.6, 7.6, 7.6), "bone_dark")
    beam(g, f"fore_{tag}", elbow, hand, 5.8, "bone")
    if plate_upper:
        beam(g, f"rerebrace_{tag}", shoulder + (np.array(elbow) - shoulder) * 0.15,
             shoulder + (np.array(elbow) - shoulder) * 0.8, 9, "plate")
    if gauntlet:
        a, b = np.array(elbow, float), np.array(hand, float)
        beam(g, f"gauntlet_{tag}", a + (b - a) * 0.35, b, 10.5, "plate")
        beam(g, f"gauntlet_{tag}_cuff", a + (b - a) * 0.3, a + (b - a) * 0.45, 12.5, "plate_lit")
    g.box(f"hand_{tag}", tuple(np.array(hand, float) + [0, -2.5, 0]), (8.4, 8.4, 8.4), "plate" if gauntlet else "bone")


def leg(g, tag, hip, knee, ankle, toe=(0, 0, -1)):
    beam(g, f"thigh_{tag}", hip, knee, 5.6, "bone")
    beam(g, f"shin_{tag}", knee, ankle, 6.4, "bone")
    k, a = np.array(knee, float), np.array(ankle, float)
    beam(g, f"greave_{tag}", k + (a - k) * 0.25, a + (a - k) * 0.05, 9.6, "plate")
    g.box(f"knee_{tag}", tuple(k + [0, 0, -1.5]), (9.4, 8.4, 6.4), "plate_lit")
    yaw = math.degrees(math.atan2(-toe[0], -toe[2]))
    g.box(f"foot_{tag}", tuple(a + [0, -2.4, 0] + _n(toe) * 4), (10, 5, 16), "plate", rotation=(0, yaw, 0))


def build(key, pose):
    m = Model(f"headsman2_{key}_{pose}")
    root = m.group("body", (0, 0, 0))
    ank = 5.0
    if pose == REST:
        lean, twist = 18, 0
        legs = {"r": ((7, HIP, 0), (10, 18, -6), (11, ank, -1)), "l": ((-7, HIP, 0), (-10, 18, -2), (-12, ank, 4))}
    elif pose == WALK:
        lean, twist = 22, 0
        legs = {"r": ((7, HIP, 0), (9, 18, 4), (9, ank, 16)), "l": ((-7, HIP, 0), (-9, 17, -12), (-9, ank, -10))}
    else:
        lean, twist = 20, -32
        legs = {"r": ((7, HIP, 0), (15, 17, -9), (20, ank, -6)), "l": ((-7, HIP, 0), (-15, 17, 6), (-20, ank, 10))}
    for tag, (h, k, a) in legs.items():
        leg(root, tag, h, k, a)
    t = root.group("torso", (0, HIP, 0), (-lean, twist, 0))
    spine_and_waist(t)
    tabard(t)
    if key == "A":
        breastplate(t)
        bone_chest(t)            # the ribs show under the plate's lower edge only
        pauldron(t, 1)
        pauldron(t, -1)
        gorget(t)
    elif key == "B":
        bone_chest(t)
        scapulae(t)
        for s, tag in ((-1, "l"), (1, "r")):
            t.box(f"shoulder_{tag}", T(s * (SH + 1), 32, 0), (12, 11, 12), "bone_dark")
    else:
        breastplate(t, half=1)
        bone_chest(t, side=-1)
        pauldron(t, 1, big=1.3)
        t.box("shoulder_l", T(-(SH + 1), 32, 0), (10, 10, 10), "bone_dark")
        beam(t, "strap", T(13, 34, -6), T(-11, 14, -8), 3, "leather_dark")
    # the head: low between the shoulders, pushed forward, looking ahead
    base = HIP + 35
    tilt = {REST: (lean - 4, 0, 0), WALK: (lean - 4, 0, 0), SWEEP: (lean - 6, -20, 0)}[pose]
    beam(t, "neck", T(0, 29, 2), (0, base + 1, -3), 6, "bone")
    h = t.group("head", (0, base, -3), tilt)
    h.box("skull", (0, base + SKULL / 2, -3), (SKULL, SKULL, SKULL), "skull")
    h.box("teeth", (0, base + 3.4, -11.05), (11, 1.2, 0.2), "socket")
    {"A": helm_sallet, "B": helm_mask, "C": helm_closed}[key](h, base) if True else None
    for c in h.children:     # every helm piece was placed for a skull centred at z -1: shift to the skull at z -3
        if hasattr(c, "frm") and c.name not in ("skull", "teeth"):
            c.frm[2] -= 2
            c.to[2] -= 2
            c.origin[2] -= 2
    halo(root, world(h, (0, base + 8, -3)), twist)
    # arms and the sword (world space)
    sh_r, sh_l = world(t, T(SH + 1, 31, 0)), world(t, T(-SH - 1, 31, 0))
    gl, gr = key in ("A", "C"), key in ("A", "C")
    gl = key == "A"
    if pose == REST:     # point on the floor ahead, the right hand on the grip at his hip, the left hand hanging
        grip = np.array([17, 40, -12])
        tip_dir = _n([0.25, -0.62, -1])
        sword(root, grip, tip_dir, (1, 0.2, -0.1))
        arm(root, "r", sh_r, sh_r + [6, -18, 2], grip + [0, 3, 0], gr, key == "C")
        arm(root, "l", sh_l, sh_l + [-6, -20, -2], sh_l + [-7, -40, -8], gl)
    elif pose == WALK:   # dragged behind, the edge down, the flat to the side
        grip = np.array([19, 26, 12])
        sword(root, grip, (0.22, -0.36, 1), (1, 0, -0.22))
        arm(root, "r", sh_r, sh_r + [4, -19, 7], grip + [0, 3, 0], gr, key == "C")
        arm(root, "l", sh_l, sh_l + [-4, -18, -9], sh_l + [-5, -36, -18], gl)
    else:                # the whirl: two hands, the blade level out to his right, the flat to the front
        grip = np.array([17, 36, -24])
        tip = _n([1, 0.04, 0.32])
        sword(root, grip, tip, (-0.32, 0, 1))
        arm(root, "r", sh_r, sh_r + [10, -13, -12], grip + tip * 4, gr, key == "C")
        arm(root, "l", sh_l, sh_l + [10, -17, -16], grip - tip * 4, gl)
    return m


TAKES = {"A": "The Plate", "B": "The Ossuary", "C": "The Butcher"}
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 32, "height": 3.0, "dist": 14, "target_z": 3.2},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_low", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 13, "target_z": 3.6,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_front": "front, silhouette", "sil_side": "side, silhouette",
          "clay_low": "a player's eye"}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in POSES:
            m = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == REST:
                lo, hi = m.bounds()
                print(key, TAKES[key], "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Hollow Warlord take 2, {key}: {TAKES[key]}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(POSES):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{TAKES[key].lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
