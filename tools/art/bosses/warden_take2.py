"""The Abyssal Warden redesign, session 1 step 1, take 2: C, the Lost Helmet, with the user's changes (2026-10-29).

- The hand no longer comes out of the eye's window: it bursts out of a side window, where the ears are (his right),
  shattering the glass and bending the grille. It is much larger, buff and mutated: a swollen arm with lumps and
  barnacles along it, oversized knuckles, fingers of uneven length and thickness, and an extra one.
- The tendrils and kelp hanging from the open neck are a growth now: a fleshy mass bulging out of the neck, thick
  tendrils curling out of it, and dense kelp, ragged and uneven so it never reads as legs.
- The rest is C: the helmet sphere bowed a little forward, the bolted front window with the crammed eye (it stays clear,
  so the pupil keeps firing), the grilled side windows, the valves, the hose.
Poses: idle; the hand raised over a player (the smash's wind-up, the ring on the floor below); the slam.

Run from the repository root: python tools/art/bosses/warden_take2.py
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, warden_silhouettes as w1  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s1_take2"
PALETTE = dict(w1.PALETTE, flesh=(110, 132, 116), flesh_dark=(66, 84, 74), barnacle=(196, 190, 172),
               nail=(40, 44, 40), shard=(170, 226, 232, 150), ring_mark=(80, 220, 230, 120))
R = w1.R
C = (0, 56, 0)
SIDE = np.array([1, 0.05, -0.1])            # his right side window: where the ear would be


def beam(g, name, a, b, w, mat):
    return w1.beam(g, name, tuple(map(float, a)), tuple(map(float, b)), w, mat)


def lump(g, name, c, size, mat):
    """A rounded lump: a box and the same box turned 45 degrees about two axes, so no corner reads square."""
    g.box(name + "_a", tuple(map(float, c)), (size, size * 0.8, size), mat)
    g.box(name + "_b", tuple(map(float, c)), (size * 0.8, size, size * 0.8), mat, rotation=(45, 45, 0))


def limb(g, name, a, b, w0, w1_, mat, bulges=(), barnacles=0):
    """A swollen limb segment from a to b, thick at a, with lumps along it and barnacles crusted on."""
    a, b = np.array(a, float), np.array(b, float)
    mid = (a + b) / 2
    beam(g, name + "_a", a, mid, w0, mat)
    beam(g, name + "_b", mid, b, (w0 + w1_) / 2, mat)
    d = (b - a) / np.linalg.norm(b - a)
    side = np.cross(d, [0, 1, 0])
    if np.linalg.norm(side) < 1e-3:
        side = np.array([1.0, 0, 0])
    side /= np.linalg.norm(side)
    up = np.cross(side, d)
    for i, (t, s, off) in enumerate(bulges):                 # (along, size, which way it bulges)
        p = a + (b - a) * t + (side * off[0] + up * off[1]) * w0 * 0.42
        lump(g, f"{name}_bulge{i}", p, s, "flesh_dark")
    for i in range(barnacles):
        t = 0.2 + 0.6 * i / max(1, barnacles - 1)
        p = a + (b - a) * t + up * w0 * 0.5 + side * (w0 * 0.3 * (-1) ** i)
        g.box(f"{name}_barnacle{i}", tuple(p), (3, 2.4, 3), "barnacle", rotation=(0, 30 * i, 0))


def oriented(g, name, centre, size, across, along, normal, mat):
    """A box whose x runs `across`, y `along` and z along `normal` (any directions; turned with Blockbench's Euler
    order, R = Rz Ry Rx)."""
    rmat = np.column_stack([np.array(v, float) / np.linalg.norm(v) for v in (across, along, normal)])
    b = -math.asin(max(-1.0, min(1.0, rmat[2, 0])))
    a = math.atan2(rmat[2, 1], rmat[2, 2])
    c = math.atan2(rmat[1, 0], rmat[0, 0])
    g.box(name, tuple(map(float, centre)), size, mat, rotation=tuple(math.degrees(v) for v in (a, b, c)))


def mutated_hand(g, name, shoulder, elbow, wrist, palm_dir, finger_dir):
    """The arm out of the side window and its hand: a swollen upper arm and forearm, a broad flat palm with a heavy
    knuckle ridge, five fingers of uneven length and thickness (one extra) spread wide, a thick thumb, all clawed."""
    limb(g, name + "_upper", shoulder, elbow, 18, 15, "flesh", bulges=((0.35, 11, (1, 0.6)), (0.7, 9, (-0.8, 0.9))),
         barnacles=3)
    lump(g, name + "_elbow", elbow, 15, "flesh_dark")
    limb(g, name + "_fore", elbow, wrist, 16, 13, "flesh", bulges=((0.45, 10, (0.9, -0.4)),), barnacles=2)
    wrist, n, f = (np.array(v, float) for v in (wrist, palm_dir, finger_dir))
    n /= np.linalg.norm(n)
    f = f - n * np.dot(f, n)                                 # fingers run across the palm's face
    f /= np.linalg.norm(f)
    across = np.cross(f, n)
    oriented(g, name + "_palm", wrist + f * 10, (26, 22, 9), across, f, n, "flesh")
    oriented(g, name + "_palm_pad", wrist + f * 6 + n * 4, (18, 12, 3), across, f, n, "flesh_dark")
    oriented(g, name + "_knuckles", wrist + f * 21 - n * 1, (28, 7, 12), across, f, n, "flesh_dark")
    fingers = ((-10.5, 15, 4.6, 22), (-4.5, 21, 5.4, 9), (1.5, 24, 5.6, -2), (7.5, 19, 5.0, -13), (12.5, 12, 3.8, -30))
    for i, (off, length, thick, splay) in enumerate(fingers):
        base = wrist + f * 23 + across * off
        sp = math.radians(splay)
        fd = f * math.cos(sp) - across * math.sin(sp)          # fanned out from the middle
        bend = base + fd * length * 0.55 + n * 1.5
        tip = bend + fd * length * 0.45 + n * 5                 # curling a little towards the palm's side
        beam(g, f"{name}_finger{i}_a", base, bend, thick, "flesh")
        beam(g, f"{name}_finger{i}_b", bend, tip, thick * 0.8, "flesh")
        beam(g, f"{name}_claw{i}", tip, tip + fd * 3 + n * 3, thick * 0.55, "nail")
    tb = wrist + f * 6 - across * 13
    beam(g, name + "_thumb_a", tb, tb - across * 7 + f * 7, 7, "flesh")
    beam(g, name + "_thumb_b", tb - across * 7 + f * 7, tb - across * 9 + f * 15 + n * 4, 5.5, "flesh")


def growth(g):
    """What hangs from the open neck: a fleshy mass bulging out, thick tendrils curling from it, and dense kelp."""
    ny = C[1] - R * 0.74
    lump(g, "mass", (0, ny - 3, 2), 26, "flesh_dark")
    lump(g, "mass_low", (3, ny - 10, 5), 16, "flesh")
    for i, (x, z, sz) in enumerate(((-11, -4, 9), (10, 8, 8), (-6, 12, 7), (12, -6, 6))):     # swellings on the mass
        lump(g, f"mass_swell{i}", (x, ny - 6, z), sz, "flesh")
    rng = np.random.default_rng(7)
    for i in range(10):                                      # tendrils: thick at the root, tapering, curling outwards
        a = math.radians(i * 36 + 15)
        root = np.array([math.sin(a) * (7 + i % 3 * 3), ny - 6, math.cos(a) * (7 + i % 3 * 3) + 3])
        out = np.array([math.sin(a), 0, math.cos(a)])
        length = 12 + (i * 7) % 9                            # the longest stop just off the floor
        pts = [root]
        for k in range(1, 4):
            t = k / 3
            pts.append(root + out * (length * 0.55 * t + 4 * t * t) + np.array([0, -length * t, 0])
                       + np.array([math.cos(a + k), 0, -math.sin(a + k)]) * 3 * t)
        for k in range(3):
            beam(g, f"tendril{i}_{k}", pts[k], pts[k + 1], 6.5 - k * 1.8, "flesh" if k % 2 == 0 else "flesh_dark")
    for i in range(22):                                      # kelp: flat ragged strands, uneven, swaying
        a = math.radians(i * 16.4 + 5)
        r0 = 6 + (i % 4) * 3.5
        root = np.array([math.sin(a) * r0, ny - 2, math.cos(a) * r0 + 2])
        length = 12 + rng.integers(0, 12)
        sway = np.array([math.sin(a + 1.3), 0, math.cos(a + 1.3)]) * 3
        p1 = root + np.array([math.sin(a) * 4, -length * 0.5, math.cos(a) * 4]) + sway
        p2 = p1 + np.array([math.sin(a) * 3, -length * 0.5, math.cos(a) * 3]) - sway
        yaw = math.degrees(math.atan2(math.sin(a), math.cos(a)))
        for k, (s, e) in enumerate(((root, p1), (p1, p2))):
            mid = (s + e) / 2
            d = e - s
            tilt = math.degrees(math.atan2(math.hypot(d[0], d[2]), -d[1]))
            g.box(f"kelp{i}_{k}", tuple(mid), (4 - k, float(np.linalg.norm(d)), 0.8), "kelp", rotation=(-tilt, yaw, 0))
        g.box(f"kelp{i}_bulb", tuple(root + np.array([0, -3, 0])), (2.4, 2.4, 2.4), "kelp", rotation=(0, 45, 0))


def helmet(m, pose):
    root = m.group("root", (0, 0, 0))
    bow = root.group("bowed", (0, 56, 0), (12, 0, 0))
    side_l = np.array([-1, 0.05, -0.1])
    neck = np.array([0, -1.0, 0.1])
    skip = lambda d: (w1.near(d, w1.FRONT, 27) or w1.near(d, side_l, 15) or w1.near(d, SIDE, 15)  # noqa: E731
                      or w1.near(d, neck, 34))
    w1.sphere(bow, "hull", C, R, "copper", skip, band_mats=["verdigris", "copper", "copper", "copper", "copper",
                                                              "copper"])
    w1.window(bow, "window", C, R, w1.FRONT, 16, eye=True)
    w1.window(bow, "side_l", C, R, side_l, 8, grille=True, bolts=6)
    out = pose != "idle"
    if out:
        # the right side window burst open: its frame stays, the glass is gone, two bars bent outwards, shards out
        sw = w1.window(bow, "side_r", C, R, SIDE, 8, grille=False, bolts=6)
        p = np.array(C) + SIDE / np.linalg.norm(SIDE) * (R + 2)
        for i, (dy, dz) in enumerate(((6, -4), (-5, 3), (2, 7))):
            bow.box(f"shard{i}", tuple(p + np.array([4 + i * 3, dy, dz])), (3, 4, 0.8), "shard",
                    rotation=(20 * i, 40, 30))
        _ = sw
    else:
        w1.window(bow, "side_r", C, R, SIDE, 8, grille=True, bolts=6)
    ring_cap = (0, 56 - R * 0.82, 2)
    w1.ring(bow, "neck_ring", ring_cap, R * 0.48, R * 0.62, 5, "brass", facing="y")
    for i, d in enumerate(((1, 0.7, 0.5), (-1, 0.7, 0.5), (1, -0.3, 0.8), (-1, -0.3, 0.8))):
        w1.valve(bow, f"valve{i}", C, R, d)
    w1.hose(bow, "hose", w1.on_sphere(C, R, (0, 0.55, 1), 2), [(0, 70, 50), (0, 52, 72), (0, 38, 88), (0, 30, 104)])   # bowed 12: it ends just off the floor
    growth(bow)
    shoulder = np.array(C) + SIDE / np.linalg.norm(SIDE) * (R - 8)
    if pose == "raised":
        # raised high and forward, the palm turned down towards the player, the fingers spread to swat
        mutated_hand(bow, "hand", shoulder, (64, 66, -2), (74, 84, -26), palm_dir=(-0.1, -0.7, -0.7),
                     finger_dir=(-0.1, 0.6, -0.8))
        m.group("floor", (0, 0, 0)).box("ring_mark", (70, 0.3, -66), (40, 0.4, 40), "ring_mark")
    elif pose == "slam":
        # (in the bowed frame: the bow tips these 12 degrees, so the hand lands flat on the floor)
        mutated_hand(bow, "hand", shoulder, (72, 36, -12), (78, 0, -44), palm_dir=(0, -0.98, 0.2), finger_dir=(-0.15, -0.2, -1))
    return root


POSES = (("idle", "idle"), ("raised", "33%: the hand raised over a player"), ("slam", "the slam"))
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": -40, "height": 3.6, "dist": 15, "target_z": 4.0},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 14, "target_z": 4.0,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": 35, "height": 1.62, "dist": 14, "target_z": 4.0,
     "player": False},
]
LABELS = w1.LABELS


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(PALETTE)
    for pose, _ in POSES:
        m = Model(f"warden_take2_{pose}")
        helmet(m, pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS)
        lo, hi = m.bounds()
        print(pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + 4 * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Abyssal Warden, take 2: the Lost Helmet, the mutated hand out of the side, the growth",
            font=sheet._font(26), fill=sheet.INK)
    for r, (pose, label) in enumerate(POSES):
        for col, v in enumerate(VIEWS):
            x, y = pad + col * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{label}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "take2.png")


if __name__ == "__main__":
    main()
