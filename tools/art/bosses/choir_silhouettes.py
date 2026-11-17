"""The Blaze Choir redesign, session 1 step 1: three takes on the trio, as cuboid blockouts.

The brief (docs/art/bosses/blaze_choir/overhaul/plan.md, 2026-11-09): vanilla's floating blaze head stays, made special,
over a body that is a musical instrument instead of rods. Three singers, three silhouettes, three instruments.

  Soprano  a wind chime of hanging organ pipes, tall and thin, a fan of pipes behind the head
  Alto     a pair of great cymbals either side of a tower of small ones, wide, a nimbus behind the head
  Bass     the take's own heavy percussion, a crown on the head:
             A  the Great Bell    a church bell, the fire its clapper
             B  the Gong          a great gong hung in a frame, a padded mallet
             C  the Kettledrum    a wide copper bowl, two mallets

Each is shown idle and playing. Model units: 16 = one block, y up, the face towards -z. The blue figure is a player
(1.8 blocks). Colours are blockout zones, not the palette.

Run from the repository root: python tools/art/bosses/choir_silhouettes.py [A B C]
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
from bosses.archevoker_silhouettes import ring_panels, vocto  # noqa: E402
from bosses.tide_silhouettes import euler, frame  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s1_silhouettes"
PALETTE = {
    "blaze": (232, 176, 52), "blaze_dark": (176, 104, 30), "eye": (60, 34, 20),
    "brass": (196, 150, 70), "brass_dark": (128, 92, 48), "inside": (52, 36, 30),
    "copper": (168, 96, 62), "skin": (214, 200, 168), "cord": (150, 40, 44), "felt": (120, 40, 48), "wood": (84, 56, 40),
    "white_fire": (255, 244, 200), "fire": (255, 158, 50), "red_fire": (232, 66, 34),
}
SPACE = 58
PLAY = "playing"


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, tuple(map(float, a)), tuple(map(float, b)), w, mat)


def head(g, x, y, k):
    """Vanilla's blaze head at scale k; y = its underside."""
    g.box("head", (x, y + 4 * k, 0), (8 * k, 8 * k, 8 * k), "blaze")
    face = -4 * k
    for sx in (-1, 1):
        g.box(f"eye_{sx}", (x + sx * 1.5 * k, y + 4.5 * k, face - 0.2), (2 * k, k, 0.4), "eye")
    g.box("mouth", (x, y + 2 * k, face - 0.2), (2 * k, 0.5 * k, 0.4), "blaze_dark")


def flame(g, name, x, y, r, mat):
    """A diamond of fire: two crossed turned squares."""
    g.box(name + "_a", (x, y, 0), (r, r, r * 0.4), mat, rotation=(0, 0, 45))
    g.box(name + "_b", (x, y, 0), (r * 0.4, r, r), mat, rotation=(45, 0, 0))


def dish(g, name, c, apex, r, mat, across=(0, 1, 0), boss=None):
    """A cymbal: a shallow cone of panels, a raised dome at the centre; the dome points along apex."""
    apex = np.array(apex, float)
    xdir = np.cross(across, apex)
    d = g.group(name, tuple(c), euler(frame(xdir, apex)))
    x, y, z = c
    drop = r * 0.17
    for i, (r1, r2, n) in enumerate(((0.27, 0.55, 12), (0.55, 0.8, 18), (0.8, 1.0, 24))):
        ring_panels(d, f"{name}_bow{i}", y - drop * (r1 - 0.27) / 0.73, y - drop * (r2 - 0.27) / 0.73, r * r1, r * r2, mat, n=n,
                    t=1.1, start=i * 5, fill=1.2, cx=x, cz=z)
    ring_panels(d, name + "_dome", y + r * 0.13, y, r * 0.1, r * 0.27, boss or mat, n=8, t=1.1, cx=x, cz=z)
    d.box(name + "_cap", (x, y + r * 0.13, z), (r * 0.25, 1.1, r * 0.25), boss or mat)
    return d


def fan_crown(g, x, y):
    """The Soprano's: a facade of organ pipes behind the head, the tallest in the middle."""
    for i in range(-5, 6):
        h = 12 + 22 * math.cos(i / 6 * math.pi / 2)
        w, px = 3, x + i * 3.1
        g.box(f"fan_{i + 5}", (px, y + h / 2, 10), (w, h, w), "brass")
        g.box(f"fan_mouth_{i + 5}", (px, y + h * 0.82, 10 - w / 2 - 0.1), (w * 0.6, 1.6, 0.3), "inside")


def spiked_crown(g, x, y, k):
    """The Bass's: a band round the top of the head and one clean triangle per point."""
    w = 8 * k + 1.5
    vocto(g, "crown_band", (x, y, 0), w, 5, w, "brass", cham=0.1)
    for i in (-1, 0, 1):
        p = 9 if i == 0 else 7
        off = i * k * 2.6
        g.box(f"crown_f{i + 1}", (x + off, y + 2.5, -w / 2 + 0.6), (p, p, 1.4), "brass", rotation=(0, 0, 45))
        g.box(f"crown_b{i + 1}", (x + off, y + 2.5, w / 2 - 0.6), (p, p, 1.4), "brass", rotation=(0, 0, 45))
        g.box(f"crown_l{i + 1}", (x - w / 2 + 0.6, y + 2.5, off), (1.4, p, p), "brass", rotation=(45, 0, 0))
        g.box(f"crown_r{i + 1}", (x + w / 2 - 0.6, y + 2.5, off), (1.4, p, p), "brass", rotation=(45, 0, 0))


# ---- the singers ------------------------------------------------------------------------------------------------------

def soprano(root, x, pose):
    g = root.group("soprano", (x, 0, 0))
    top = 64
    head_y = top + 7
    head(g, x, head_y, 2)
    fan_crown(g, x, head_y + 4)
    flame(g, "wisp", x, top + 3.5, 6, "white_fire")
    vocto(g, "plate", (x, top, 0), 30, 2.5, 30, "brass", cham=0.29)
    vocto(g, "plate_cap", (x, top + 2, 0), 16, 1.6, 16, "brass_dark", cham=0.29)
    swing = 20 if pose == PLAY else 0
    radius = 12
    for i in range(8):
        a = 360 * i / 8 + 22.5
        length = 16 + i * 5
        yaw = g.group(f"tube{i}", (x, 0, 0), (0, a, 0))
        t = yaw.group(f"tube{i}_swing", (x, top - 1, radius), (-swing, 0, 0))
        t.box(f"wire{i}", (x, top - 2.5, radius), (0.6, 3.5, 0.6), "brass_dark")
        end = top - 4
        t.box(f"pipe{i}", (x, end - length / 2, radius), (3.6, length, 3.6), "brass")
        t.box(f"mouth{i}", (x, end - 4, radius + 1.9), (2.2, 2.2, 0.3), "inside")
        t.box(f"band{i}", (x, end - 0.8, radius), (4.4, 1.2, 4.4), "brass_dark")
        t.box(f"foot{i}", (x, end - length - 0.6, radius), (2, 1.2, 2), "brass_dark")
    g.box("striker_rod", (x, top - 22, 0), (0.8, 42, 0.8), "brass_dark")
    vocto(g, "striker", (x, top - 28, 0), 12, 1.6, 12, "brass", cham=0.29)
    flame(g, "sail", x, 16, 13, "white_fire")


def alto(root, x, pose):
    g = root.group("alto", (x, 0, 0))
    head_y = 56
    k = 3
    head(g, x, head_y, k)
    halo = dish(g, "nimbus", (x, head_y + 4 * k, 15), (0, 0, 1), 18, "brass", across=(1, 0, 0))
    g.box("spindle", (x, 33, 0), (3, 40, 3), "brass_dark")
    for i, (y, r) in enumerate(((50, 13), (37, 10), (25, 7))):
        dish(g, f"tier{i}", (x, y, 0), (0, 1, 0), r, "brass", across=(0, 0, 1))
    flame(g, "ember", x, 13, 10, "fire")
    for sx in (-1, 1):
        if pose == PLAY:
            c, ap = (x + sx * 2.5, 42, -34), (sx, 0, 0)
        else:
            c, ap = (x + sx * 36, 27, 0), (sx * 0.5, 0, 0.87)
        d = dish(g, f"cymbal_{sx}", c, ap, 25, "brass", across=(0, 0, 1) if pose == PLAY else (0, 1, 0), boss="brass_dark")
        cx, cy, cz = c
        d.box(f"tassel_{sx}", (cx, cy + 25 * 0.13 + 2.5, cz), (1.4, 4, 1.4), "cord")
    return halo


def bell(g, x, pose):
    k = 3
    head_y = 50
    head(g, x, head_y, k)
    spiked_crown(g, x, head_y + 8 * k, k)
    flame(g, "wisp", x, 45, 8, "red_fire")
    tilt = 20 if pose == PLAY else 0
    b = g.group("bell", (x, 44, 0), (0, 0, tilt))
    profile = ((40, 10), (35, 12.5), (26, 14), (18, 17.5), (12, 23), (8, 29))
    for i in range(len(profile) - 1):
        (y1, r1), (y2, r2) = profile[i], profile[i + 1]
        ring_panels(b, f"bell_{i}", y1, y2, r1, r2, "brass", n=12, t=1.6, start=15, cx=x)
    ring_panels(b, "bell_lip", 12.5, 10, 23, 25.3, "brass_dark", n=12, t=2.2, start=15, cx=x)
    ring_panels(b, "bell_band", 36, 33, 12.2, 13.2, "brass_dark", n=12, t=2, start=15, cx=x)
    vocto(b, "bell_top", (x, 40, 0), 20, 2, 20, "brass_dark", cham=0.29)
    vocto(b, "bell_dark", (x, 20, 0), 28, 1, 28, "inside", cham=0.29)
    for a in (0, 90):
        b.box(f"canon_{a}", (x, 43.5, 0), (15, 5, 3), "brass_dark", rotation=(0, a, 0))
    c = b.group("clapper", (x, 36, 0), (0, 0, -tilt * 1.8))
    c.box("clapper_rod", (x, 22, 0), (1.5, 26, 1.5), "brass_dark")
    flame(c, "clapper_fire", x, 7, 11, "red_fire")


def gong(g, x, pose):
    k = 3
    head_y = 66
    head(g, x, head_y, k)
    spiked_crown(g, x, head_y + 8 * k, k)
    flame(g, "wisp", x, 62, 5, "red_fire")
    for sx in (-1, 1):
        beam(g, f"post_{sx}", (x + sx * 29, 6, 0), (x + sx * 29, 60, 0), 4, "wood")
        g.box(f"post_foot_{sx}", (x + sx * 29, 7, 0), (7, 3, 12), "brass_dark")
        g.box(f"bar_end_{sx}", (x + sx * 36, 60, 0), (4, 7, 7), "brass_dark", rotation=(0, 0, 45))
        g.box(f"cord_{sx}", (x + sx * 13, 56, 0), (1, 8, 1), "cord")
    g.box("bar", (x, 60, 0), (72, 5, 5), "wood")
    tilt = -16 if pose == PLAY else 0
    gr = g.group("gong", (x, 54, 0), (tilt, 0, 0))
    dish(gr, "gong_disc", (x, 31, 0), (0, 0, -1), 25, "brass", across=(1, 0, 0), boss="red_fire")
    if pose == PLAY:
        beam(g, "mallet_shaft", (x + 18, 40, -30), (x + 3, 34, -10), 2, "wood")
        g.box("mallet_head", (x + 2, 33.5, -8), (8, 8, 8), "felt")
    else:
        beam(g, "mallet_shaft", (x + 40, 18, -2), (x + 40, 44, -2), 2, "wood")
        g.box("mallet_head", (x + 40, 47, -2), (8, 8, 8), "felt")


def kettledrum(g, x, pose):
    k = 3
    head_y = 52
    head(g, x, head_y, k)
    spiked_crown(g, x, head_y + 8 * k, k)
    flame(g, "wisp", x, 47.5, 7, "red_fire")
    profile = ((42, 27), (34, 27), (26, 23.5), (19, 17), (14, 9))
    for i in range(len(profile) - 1):
        (y1, r1), (y2, r2) = profile[i], profile[i + 1]
        ring_panels(g, f"bowl_{i}", y1, y2, r1, r2, "copper", n=12, t=2, start=15, cx=x)
    vocto(g, "drumhead", (x, 42, 0), 54, 1, 54, "skin", cham=0.29)
    ring_panels(g, "hoop", 44, 41, 27.8, 27.8, "brass", n=12, t=2, start=15, cx=x)
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        g.box(f"rod{i}", (x + 29 * math.sin(a), 35, 29 * math.cos(a)), (1.4, 14, 1.4), "brass_dark")
    flame(g, "ember", x, 9, 11, "red_fire")
    for sx in (-1, 1):
        if pose == PLAY:
            a, b = (x + sx * 30, 74, -14), (x + sx * 12, 50, -14)
        else:
            a, b = (x + sx * 38, 18, -4), (x + sx * 38, 44, -4)
        beam(g, f"mallet_shaft_{sx}", a, b, 2, "wood")
        g.box(f"mallet_head_{sx}", b, (8, 8, 8), "felt")


TAKES = {"A": ("The Great Bell", bell), "B": ("The Gong", gong), "C": ("The Kettledrum", kettledrum)}


def build(key, pose):
    title, bass = TAKES[key]
    m = Model(f"choir_{key}_{pose}")
    root = m.group("root", (0, 0, 0))
    soprano(root, -SPACE, pose)
    alto(root, 0, pose)
    bass(root.group("bass", (SPACE + 8, 0, 0)), SPACE + 8, pose)
    return m, title


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 24, "height": 3.6, "dist": 15, "target_z": 3.2},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.2, "dist": 14.5, "target_z": 3.2,
     "player": False},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -22, "height": 1.62, "dist": 13, "target_z": 3.4,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "flat_front": "front", "sil_front": "front, silhouette", "clay_eye": "a player's eye"}
POSES = ("idle", PLAY)


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in POSES:
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Blaze Choir {key}: chime, cymbals, {title.lower()}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(POSES):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
