"""The Mirrored Magus redesign, session 1 step 4: take 4, horror proportions.

The user (2026-10-13) on take 3 (magus_take3.py): the smile belongs in the texture (the modelled one looked awful);
the collar needs to look much better, and the details overall; it looks too goofy - give it horror proportions, and
a better mask.

So the clown is gone from the proportions and the horror comes in:
- a marionette's build: narrow shoulders, a cinched waist, a long thin neck, a long head tilted to one side;
  stick-thin legs; arms so long his clawed fingers hang past his knees; a slight hunch;
- long pointed shoes curling up at the tip (not clown boots);
- a long coat cut into hanging points (dagged) down to his knees, split black and white, a crimson corset at the
  waist; tight sleeves with pointed shoulder caps;
- the collar: a pleated ruff close round his neck, and a collar of long pointed petals draped over his shoulders,
  chest and back;
- the mask: a porcelain Venetian face, curved round his face (three panels), a heavy brow over deep sunken eye
  sockets, high cheekbones, its own long nose over the illager's, a pointed chin; the grin and the crack are painted
  later;
- the hat: take 3's three floppy points with little bells; the crystal-shard bow.
Colours are flat zones; the harlequin diamonds belong to the texture.

Run from the repository root: python tools/art/bosses/magus_take4.py
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
from bosses import magus_silhouettes as t1, magus_take2 as t2, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s1_take4"
beam = t2.beam
HIP = 46.0
PALETTE = dict(t2.PALETTE, porcelain=(236, 230, 216), socket=(10, 8, 14), leg=(30, 26, 34))


def body(m, pose):
    root = m.group("root", (0, 0, 0))
    # stick legs, knees, long pointed shoes curling up at the tip
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        leg = root.group(f"leg_{side}", (sx * 2.8, HIP, 0))
        leg.box(f"thigh_{side}", (sx * 2.8, 35, 0), (4.2, 22, 4.2), "leg")
        leg.box(f"knee_{side}", (sx * 2.8, 24, -0.4), (4.8, 3, 4.8), "black")
        leg.box(f"shin_{side}", (sx * 2.8, 13, 0), (3.6, 20, 3.6), "leg")
        leg.box(f"shoe_{side}", (sx * 2.8, 1.5, -3), (4.6, 3, 12), "black")
        beam(leg, f"shoe_point_{side}", (sx * 2.8, 1.6, -8.5), (sx * 2.8, 4.5, -14.5), 2.4, "crimson")
        beam(leg, f"shoe_curl_{side}", (sx * 2.8, 4.5, -14.5), (sx * 2.8, 7.5, -13), 1.6, "crimson")
    hunch = {"idle": -10, "draw": -5}[pose]
    torso = root.group("torso", (0, HIP, 0), (hunch, 0, 0))
    h = HIP
    # the corseted waist, a narrow chest widening a little to narrow shoulders
    torso.box("corset", (0, h + 3, 0), (8, 6, 6), "crimson")
    for sx in (-1, 1):
        torso.box(f"ribs_{sx}", (sx * 2.75, h + 10, 0), (5.5, 8, 6.6), "black" if sx < 0 else "white")
        torso.box(f"chest_{sx}", (sx * 3.5, h + 17, 0), (7, 6, 7.4), "black" if sx < 0 else "white")
    # the long coat: hanging points from the waist to the knees, round the sides and back, split black / white
    for i in range(9):
        a = math.radians(-120 + i * 30)                     # from his left side round the back to his right
        x, z = math.sin(a) * 4.8, math.cos(a) * 3.6 + 0.5
        length = 22 - abs(i - 4) * 1.5
        mat = "black" if x < 0 else "white"
        torso.box(f"coat_{i}", (x, h - length / 2, z), (4.6, length, 1.0), mat, rotation=(0, math.degrees(a), 0))
        torso.box(f"coat_point_{i}", (x, h - length - 1.2, z), (3.2, 3.2, 1.0), mat,
                  rotation=(0, math.degrees(a), 45))
    # the collar: a pleated ruff close round the neck, then long pointed petals draped over shoulders, chest and back
    for i in range(16):
        a = math.radians(i * 22.5)
        torso.box(f"ruff_{i}", (math.sin(a) * 5.2, h + 21.5, math.cos(a) * 4.4), (1.2, 2.8, 5.2),
                  "white" if i % 2 else "black", rotation=(0, math.degrees(a), 0))
    # two layers of flat pointed petals fanned over his shoulders, chest and back: crimson and black outside, white
    # inside, offset half a petal
    for layer, (r0, out, drop, width, length, mats, offset) in enumerate(
            ((5.2, 9.5, 10, 5.6, 1.0, ("crimson", "black"), 22.5), (5.0, 6.5, 6.5, 4.4, 0.8, ("white", "white"), 0))):
        for i in range(8):
            a = math.radians(i * 45 + offset)
            radial = np.array([math.sin(a), 0, math.cos(a) * 0.85])
            root_pt = np.array([0, h + 21 + layer * 0.8, 0.4]) + radial * r0
            tip = root_pt + radial * out + np.array([0, -drop, 0])
            petal(torso, f"petal_{layer}_{i}", root_pt, tip, width, mats[i % 2])

    # arms so long the fingers hang past his knees: tight sleeves, pointed shoulder caps, clawed fingers
    arms = {"idle": {"left": (12, 0, -6), "right": (16, 0, 9)},
            "draw": {"left": (92, 0, -4), "right": (82, -34, 20)}}[pose]
    hands = {}
    sh = h + 18
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        arm = torso.group(f"arm_{side}", (sx * 7.6, sh, 0), arms[side])
        arm.box(f"cap_{side}", (sx * 8.2, sh + 0.5, 0), (5.6, 3, 5.6), "crimson")
        beam(arm, f"cap_point_{side}", (sx * 9.5, sh, 0), (sx * 12.5, sh - 4, 0), 2.2, "crimson")
        arm.box(f"upper_{side}", (sx * 7.6, sh - 9, 0), (3.8, 18, 3.8), "white" if sx < 0 else "black")
        arm.box(f"fore_{side}", (sx * 7.6, sh - 27, 0), (3.4, 18, 3.4), "black" if sx < 0 else "white")
        arm.box(f"cuff_{side}", (sx * 7.6, sh - 35.5, 0), (4.8, 2.4, 4.8), "crimson")
        arm.box(f"hand_{side}", (sx * 7.6, sh - 38.5, 0), (3.4, 4, 3.2), "skin")
        for j, dx in enumerate((-1.2, -0.4, 0.4, 1.2)):
            beam(arm, f"finger_{side}_{j}", (sx * 7.6 + dx, sh - 40, -0.3),
                 (sx * 7.6 + dx * 1.5, sh - 50 + abs(dx) * 1.5, -2.2), 0.8, "claw")
        hands[side] = tuple((arm.world_matrix() @ np.array([sx * 7.6, sh - 40, 0, 1.0]))[:3])
    neck = torso.group("neck", (0, h + 22, 0), ({"idle": 10, "draw": 4}[pose], 0, {"idle": 16, "draw": 4}[pose]))
    neck.box("neck", (0, h + 25, 0), (3.4, 7, 3.4), "skin")
    yh = h + 36.5
    neck.box("head", (0, yh, 0), (11, 16, 11), "skin")
    neck.box("nose", (0, yh - 5, -7), (3, 6, 3), "nose")
    return root, neck, hands, yh


def petal(g, name, a, b, width, mat):
    """A flat pointed petal from a to b: a broad plate, then a narrower point."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    mid = a + d * 0.38
    tip = a + d * 0.86
    flat = lambda c, ln, w: g.box(c, tuple(mid if c == name else tip), (ln, 1.0, w), mat,  # noqa: E731
                                  rotation=_aim(d))
    flat(name, np.linalg.norm(d) * 0.76, width)
    flat(f"{name}_point", np.linalg.norm(d) * 0.3, width * 0.5)


def _aim(d):
    """Blockbench angles for a plate along x pointing along d, lying flat: its width runs round him (horizontal, at
    right angles to d), its thin side faces outward."""
    from bosses.unbound_s2 import euler
    x = np.array(d, float) / np.linalg.norm(d)
    z = np.cross(x, [0, 1, 0])
    z = z / np.linalg.norm(z) if np.linalg.norm(z) > 1e-6 else np.array([0, 0, 1.0])
    y = np.cross(z, x)
    return tuple(euler(np.column_stack([x, y, z])))


def mask(g, yh):
    """A porcelain Venetian face, curved round his: a centre panel and two side panels turned back, a heavy brow over
    deep sunken eye sockets, high cheekbones, its own long nose sheathing the illager's, a pointed chin."""
    zf = -5.5
    g.box("mask_centre", (0, yh - 0.5, zf - 0.8), (6.4, 18, 1.4), "porcelain")
    for sx in (-1, 1):
        g.box(f"mask_side_{sx}", (sx * 4.8, yh - 0.5, zf + 0.2), (4, 16, 1.2), "porcelain", rotation=(0, -sx * 22.5, 0))
        # a deep socket: dark, sunk behind the mask's face, slanting up and out
        g.box(f"mask_socket_{sx}", (sx * 3.1, yh + 2.2, zf - 1.15), (3.6, 2.2, 0.8), "socket", rotation=(0, 0, -sx * 22.5))
        g.box(f"mask_cheek_{sx}", (sx * 3.4, yh - 2.2, zf - 1.7), (3.2, 1.6, 1.0), "porcelain", rotation=(0, 0, sx * 22.5))
    g.box("mask_brow", (0, yh + 4.4, zf - 1.9), (10, 2.2, 1.6), "porcelain")
    g.box("mask_peak", (0, yh + 7.4, zf - 1.1), (2.4, 3, 1.2), "porcelain", rotation=(0, 0, 45))    # a widow's peak
    g.box("mask_nose", (0, yh - 4.6, -8.1), (3.8, 7.6, 3.8), "porcelain")                         # over the illager's
    g.box("mask_chin", (0, yh - 10, zf - 0.6), (3.4, 3.4, 1.2), "porcelain", rotation=(0, 0, 45))


def floppy_hat(head, yh):
    top = yh + 8
    head.box("hat_band", (0, top + 1.2, 0), (12.4, 2.6, 12.4), "crimson")
    head.box("hat_cap", (0, top + 4, 0.5), (11.2, 4, 11.2), "black")
    for i, (d, bend, mats) in enumerate((((-0.85, 1.0, 0.15), (-0.05, -0.62, 0.06), ("black", "crimson")),
                                         ((0.85, 1.0, 0.15), (0.05, -0.62, 0.06), ("white", "black")),
                                         ((0, 1.0, 0.9), (0, -0.62, 0.14), ("crimson", "white")))):
        p = np.array([d[0] * 4, top + 4.5, d[2] * 3])
        dd = np.array(d, float)
        for k in range(8):
            dd = dd / np.linalg.norm(dd)
            q = p + dd * 5.2
            beam(head, f"hat_point_{i}_{k}", tuple(p), tuple(q), 6.2 - k * 0.62, mats[k % 2])
            p = q
            dd = dd + np.array(bend)
        head.box(f"hat_bell_{i}", tuple(p + np.array([0, -1.3, 0])), (2.2, 2.2, 2.2), "gold")


def build(pose):
    m = Model(f"magus4_{pose}")
    root, neck, hands, yh = body(m, pose)
    floppy_hat(neck, yh)
    mask(neck, yh)
    t1.crystal_bow(root, hands["left"], "y", drawn=pose == "draw")
    return m


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 9.5, "target_z": 2.7},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.8, "dist": 9, "target_z": 2.8,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 9, "target_z": 3.0,
     "player": False},
]
CLOSE = [
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": 18, "height": 5.0, "dist": 3.0, "target_z": 4.95,
     "player": False},
    {"name": "face_side", "mode": "flat", "camera": "persp", "yaw": 70, "height": 5.0, "dist": 3.0, "target_z": 4.9,
     "player": False},
    {"name": "collar", "mode": "flat", "camera": "persp", "yaw": -40, "height": 4.9, "dist": 3.4, "target_z": 4.2,
     "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for pose in ("idle", "draw"):
        m = build(pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS + (CLOSE if pose == "idle" else []))
        if pose == "idle":
            lo, hi = m.bounds()
            print(round(float(hi[1]) / 16, 2), "blocks tall,", len(m.cubes), "cubes")
    labels = dict(t1.LABELS, face="his mask", face_side="his mask, side", collar="the collar")
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + 4 * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus take 4: horror proportions, the ruff and petal collar, the porcelain mask",
            font=sheet._font(26), fill=sheet.INK)
    cells = [("idle", v["name"]) for v in VIEWS] + [("draw", v["name"]) for v in VIEWS] + \
            [("idle", v["name"]) for v in CLOSE]
    for k, (pose, name) in enumerate(cells):
        x, y = pad + (k % 4) * (tw + pad), top + (k // 4) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / pose / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), f"{pose}: {labels[name]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "take4.png")


if __name__ == "__main__":
    main()
