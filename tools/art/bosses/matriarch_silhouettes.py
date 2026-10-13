"""The Night Matriarch redesign, session 1 step 1: two directions as cuboid blockouts, each in her three moments.

The brief (user, 2026-10-12): see B and C separately as a first silhouette check.
  B  The Phantom Queen   clearly a phantom (vanilla's PhantomModel at 3x): the long flat body, the two-part wings and
                         the tail, made regal - a bone crown, a spine of bone, ribs under the belly, bone spars along
                         the wings' leading edges, torn trailing edges, a long tattered train
  C  The Widow of Dusk   a gaunt woman in mourning carried by huge phantom wings from her shoulder blades: a veil and
                         a tall mantilla comb over a long head, long thin arms with claws, a ragged gown for legs

Her fight (NightMatriarch.java, unchanged): she circles above the arena and rakes whoever she sweeps past; a dark
circle marks a player's spot for 1.5 s and she dives onto it; she lies stunned on the ground for 1.5 s (the melee
window); small phantoms join; she's stronger at night. So each direction is shown in three poses:
  circling   high overhead, banking: seen from a player's eye below, from above, and in three-quarter
  diving     the committed dive, nose (or head) down, wings swept back
  grounded   stunned on the floor, wings collapsed, clear of the floor's warning ring

Model units: 16 = one block, y up, the front (her head) towards -z. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/matriarch_silhouettes.py
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
from bosses import volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s1_silhouettes"
PALETTE = {
    "membrane": (58, 62, 92), "membrane_dark": (40, 40, 66), "hide": (74, 84, 120), "belly": (150, 160, 170),
    "bone": (214, 206, 182), "eye": (120, 255, 120), "skin": (196, 196, 206), "veil": (30, 26, 36),
    "gown": (46, 36, 58), "gown_dark": (32, 26, 42), "comb": (24, 22, 28), "claw": (60, 56, 64),
}
ALTITUDE = {"circling": 84, "diving": 52, "grounded": 0}       # the lowest point of the model (model units)


# ---- shared helpers --------------------------------------------------------------------------------------------------

def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


def wing(parent, side, pivot, segs, chord, rot, elbow_rot):
    """A two-part bat/phantom wing. side: -1 left, +1 right. segs: [(length, spar width, [(strip width, chord), ...])]
    for the inner and outer part. chord: "z" (the membrane trails back along +z, flat in y: the phantom) or "-y" (it
    hangs down along -y, flat in z: wings on a standing figure's back). Each part's membrane is strips of uneven chord,
    so the trailing edge is torn."""
    sx = side
    word = "left" if sx < 0 else "right"
    g = parent.group(f"wing_{word}", pivot, rot)
    x0, y0, z0 = pivot
    span = 0.0
    for i, (length, spar, strips) in enumerate(segs):
        if i == 1:
            g = g.group(f"wing_{word}_tip", (x0 + sx * span, y0, z0), elbow_rot)
        a = (x0 + sx * span, y0, z0)
        b = (x0 + sx * (span + length), y0, z0)
        beam(g, f"wing_{word}_{i}_spar", a, b, spar, "bone")
        s = span
        for j, (w, c) in enumerate(strips):
            cx = x0 + sx * (s + w / 2)
            if chord == "z":
                g.box(f"wing_{word}_{i}_m{j}", (cx, y0, z0 + c / 2), (w, 1, c), "membrane" if j % 2 else "membrane_dark")
            else:
                g.box(f"wing_{word}_{i}_m{j}", (cx, y0 - c / 2, z0), (w, c, 1), "membrane" if j % 2 else "membrane_dark")
            s += w
        # a finger bone across the outer membrane
        if i == 1:
            far = strips[len(strips) // 2][1] * 0.8
            tip = (x0 + sx * (span + length * 0.75), y0, z0 + far) if chord == "z" else \
                  (x0 + sx * (span + length * 0.75), y0 - far, z0)
            beam(g, f"wing_{word}_finger", a, tip, spar * 0.6, "bone")
        span += length
    return g


def shift(model, dy):
    for g in model.groups:
        g.origin[1] += dy
    for c in model.cubes:
        c.frm[1] += dy
        c.to[1] += dy
        c.origin[1] += dy


def settle(model, pose):
    lo, _ = model.bounds()
    shift(model, ALTITUDE[pose] - float(lo[1]))


# ---- B: the Phantom Queen ----------------------------------------------------------------------------------------------
# vanilla's PhantomModel at 3x: body 5x3x9, wing base 6x2x9 and tip 13x1x9, head 7x3x5, tail 3x2x6 then 1x1x6

K = 3


def queen(pose):
    m = Model(f"matriarch_queen_{pose}")
    bank, pitch = {"circling": (18, 4), "diving": (0, -38), "grounded": (0, 0)}[pose]
    body = m.group("body", (0, 0, 0), (pitch, 0, bank))
    body.box("hull", (0, 0, 0), (5 * K, 3 * K, 9 * K), "hide")
    body.box("belly", (0, -3 * K / 2 - 1.5, 1), (4 * K, 3, 8 * K), "belly")
    for i in range(5):                                                     # ribs round the belly
        body.box(f"rib_{i}", (0, -3 * K / 2 - 2, -9 + i * 5), (5 * K + 3, 2, 1.6), "bone")
    for i, h in enumerate((4, 6, 5, 3)):                                   # a spine of bone along the back, swept
        body.box(f"spine_{i}", (0, 3 * K / 2 + h / 2 - 0.5, -6 + i * 6), (2, h, 2.4), "bone", rotation=(35, 0, 0))
    # the head, slightly down, with its crown of bone tines
    head = body.group("head", (0, 0, -9 * K / 2), (-10 if pose != "grounded" else -18, 0, 0))
    head.box("skull", (0, -1, -9 * K / 2 - 5 * K / 2), (7 * K, 3 * K, 5 * K), "hide")
    for sx in (-1, 1):
        head.box(f"eye_{sx}", (sx * 6.5, 0.5, -9 * K / 2 - 5 * K + 0.4), (4, 2, 1), "eye")
    # the crown: a circlet of bone round her skull, three tines swept back, the middle one tallest
    head.box("circlet", (0, 4.5, -9 * K / 2 - 5 * K / 2), (7 * K + 1.5, 2, 5 * K + 1.5), "bone")
    for i, (x, h, lean) in enumerate(((-7, 10, -22), (0, 15, 0), (7, 10, 22))):
        head.box(f"tine_{i}", (x - lean * h / 90, 5 + h / 2, -9 * K / 2 - 5 * K / 2 + 2), (2.4, h, 2.4), "bone",
                 rotation=(28, 0, lean))
    # the tail, then the train of torn membrane trailing behind it
    tail = body.group("tail", (0, 0, 9 * K / 2), ({"circling": -4, "diving": 14, "grounded": -2}[pose], 0, 0))
    tail.box("tail_base", (0, 0, 9 * K / 2 + 3 * K), (3 * K, 2 * K, 6 * K), "hide")
    tail.box("tail_tip", (0, 0, 9 * K / 2 + 6 * K + 3 * K), (1 * K, 1 * K, 6 * K), "hide")
    for i, (x, L, yaw) in enumerate(((-6, 26, -16), (-2, 40, -5), (2, 34, 5), (6, 22, 16))):
        train = tail.group(f"train_{i}", (x, 0, 9 * K / 2 + 6), (0, yaw, 0))
        train.box(f"train_{i}_strip", (x, -0.5, 9 * K / 2 + 6 + L / 2), (4.5, 1, L), "membrane_dark")
    # the wings: base 6x9 then tip 13x9, the trailing edges torn
    segs = [(6 * K, 3.2, [(6, 27), (6, 24), (6, 27)]),
            (13 * K, 2.4, [(7, 24), (6, 18), (7, 22), (6, 14), (7, 16), (6, 9)])]
    for sx in (-1, 1):
        if pose == "circling":
            rot, elbow = (0, 0, sx * 10), (0, -sx * 14, sx * 6)
        elif pose == "diving":
            rot, elbow = (0, -sx * 58, sx * 16), (0, -sx * 30, sx * 8)
        else:
            rot, elbow = (0, sx * 6, -sx * 6), (0, 0, -sx * 12)
        wing(body, sx, (sx * 5 * K / 2, 3, -9 * K / 2 + 1), segs, "z", rot, elbow)
    settle(m, pose)
    return m


# ---- C: the Widow of Dusk -------------------------------------------------------------------------------------------
# built standing (feet at 0, facing -z), then the whole body turned for the pose

def widow(pose):
    m = Model(f"matriarch_widow_{pose}")
    pitch = {"circling": -72, "diving": -128, "grounded": -86}[pose]
    body = m.group("body", (0, 40, 0), (pitch, 0, 0))
    # the gown, wide at the hem and torn into rags, in place of legs
    gown = body.group("gown", (0, 34, 0), ({"circling": 18, "diving": 8, "grounded": 0}[pose], 0, 0))
    gown.box("gown_hips", (0, 30, 0.5), (14, 8, 10), "gown")
    gown.box("gown_mid", (0, 21, 1), (17, 10, 12.5), "gown")
    gown.box("gown_low", (0, 12, 1.5), (20, 8, 15), "gown_dark")
    for i, (x, z, L) in enumerate(((-8, -5, 13), (-3, -6.5, 9), (3, -6, 14), (8, -4, 10), (-8, 7, 12), (0, 8.5, 16),
                                   (8, 7, 11))):
        gown.box(f"rag_{i}", (x, 8 - L / 2, z), (5, L, 1.2) if abs(z) > 6 else (1.2, L, 5), "gown_dark")
    # the gaunt torso: a narrow corseted waist, a bony chest
    torso = body.group("torso", (0, 36, 0), (0, 0, 0))
    torso.box("waist", (0, 38, 0.5), (10, 6, 7), "veil")
    torso.box("chest", (0, 46, 0.5), (15, 10, 8), "skin")
    torso.box("collar", (0, 51.5, 0.5), (16, 2, 9), "veil")
    torso.box("neck", (0, 54, -0.5), (4, 5, 4), "skin")
    # the head: long and narrow (an illager's length), the veil over it, the mantilla comb standing up behind
    head = torso.group("head", (0, 55, -0.5), ({"circling": 50, "diving": 40, "grounded": 40}[pose], 0, 0))
    head.box("head", (0, 62, -1), (9, 13, 9), "skin")
    for sx in (-1, 1):
        head.box(f"eye_{sx}", (sx * 2.2, 62.5, -5.6), (2, 1.2, 0.4), "eye")
    head.box("veil_top", (0, 69, 0), (11, 1.5, 11), "veil")
    head.box("veil_back", (0, 59, 5.2), (11, 20, 1.2), "veil")
    for sx in (-1, 1):
        head.box(f"veil_side_{sx}", (sx * 5.6, 61, 0.5), (1.2, 14, 10), "veil")
    head.box("comb", (0, 72.5, 3.5), (13, 6, 1.2), "comb", rotation=(-12, 0, 0))          # a fan behind the veil
    head.box("comb_point", (0, 77, 4.4), (3, 6, 1.2), "comb", rotation=(-12, 0, 0))
    for sx in (-1, 1):
        head.box(f"comb_point_{sx}", (sx * 5.2, 75.5, 4.2), (2.6, 6, 1.2), "comb", rotation=(-12, 0, sx * -22))
    # long thin arms ending in claws
    arms = {"circling": ((24, 0, 8), (10, 0, 0)), "diving": ((165, 0, 12), (6, 0, 0)),
            "grounded": ((150, 0, 24), (-12, 0, 0))}[pose]
    for sx in (-1, 1):
        word = "left" if sx < 0 else "right"
        up_r, fore_r = arms
        upper = torso.group(f"arm_{word}", (sx * 8.5, 50, 0.5), (up_r[0], up_r[1], sx * up_r[2]))
        upper.box(f"upper_arm_{word}", (sx * 9, 42, 0.5), (3.5, 16, 3.5), "skin")
        fore = upper.group(f"forearm_{word}", (sx * 9, 34, 0.5), fore_r)
        fore.box(f"forearm_{word}_box", (sx * 9, 26, 0.5), (3, 16, 3), "skin")
        fore.box(f"hand_{word}", (sx * 9, 16.5, 0.5), (4, 4, 3), "skin")
        for j, dx in enumerate((-1.2, 0, 1.2)):
            beam(fore, f"claw_{word}_{j}", (sx * 9 + dx, 15, 0.5), (sx * 9 + dx * 2.4, 6, -2.5), 0.9, "claw")
    # the wings, from her shoulder blades: the membrane hangs from the spar (chord along -y)
    segs = [(18, 3.2, [(6, 30), (6, 26), (6, 32)]),
            (36, 2.4, [(6, 30), (6, 21), (6, 33), (6, 24), (6, 14), (6, 22)])]
    for sx in (-1, 1):
        if pose == "circling":
            rot, elbow = (0, 0, sx * 12), (0, 0, sx * 6)
        elif pose == "diving":
            rot, elbow = (0, -sx * 45, -sx * 68), (0, -sx * 25, -sx * 20)
        else:                                       # lying face down, the wings fallen over her to the floor
            rot, elbow = (0, sx * 22, -sx * 40), (0, sx * 28, -sx * 12)
        wing(torso, sx, (sx * 4, 50, 5), segs, "-y", rot, elbow)
    settle(m, pose)
    return m


DIRECTIONS = {
    "B": ("The Phantom Queen", queen),
    "C": ("The Widow of Dusk", widow),
}


def views(pose, model):
    lo, hi = model.bounds()
    mid = float(lo[1] + hi[1]) / 32
    if pose == "circling":
        return [{"name": "sil_below", "mode": "silhouette", "camera": "persp", "yaw": 25, "height": 1.62, "dist": 9.5,
                 "target_z": mid, "lens": 26},
                {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top", "player": False},
                {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": mid + 3, "dist": 9,
                 "target_z": mid - 0.4}]
    if pose == "diving":
        return [{"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
                {"name": "sil_below", "mode": "silhouette", "camera": "persp", "yaw": -20, "height": 1.62, "dist": 9,
                 "target_z": mid, "lens": 26},
                {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": mid + 2, "dist": 9,
                 "target_z": mid - 0.3}]
    return [{"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
            {"name": "flat_eye", "mode": "flat", "camera": "persp", "yaw": 20, "height": 1.62, "dist": 8.5,
             "target_z": 1.0},
            {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -35, "height": 4.5, "dist": 10, "target_z": 0.8}]


LABELS = {"sil_below": "from below (a player's eye)", "sil_top": "from above", "flat_34": "three-quarter",
          "sil_side": "side", "flat_eye": "a player's eye", "clay_34": "clay"}
POSES = ("circling", "diving", "grounded")


def direction_sheet(key, title, stats):
    tw, th, pad, top = 440, 340, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Night Matriarch {key}: {title}  -  span {stats['span']} blocks, body {stats['length']} long",
            font=sheet._font(26), fill=sheet.INK)
    for r, pose in enumerate(POSES):
        names = [v["name"] for v in views(pose, DIRECTIONS[key][1](pose))]
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / pose / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{pose}: {LABELS[name]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key, (title, build) in DIRECTIONS.items():
        stats = {}
        for pose in POSES:
            model = build(pose)
            if pose == "circling":
                lo, hi = model.bounds()
                stats = {"span": round(float(hi[0] - lo[0]) / 16, 1), "length": round(float(hi[2] - lo[2]) / 16, 1)}
            v2.run_blender(model.render_json(v2.PALETTE), OUT / key / pose, views(pose, model))
        direction_sheet(key, title, stats)
        print(key, stats)


if __name__ == "__main__":
    main()
