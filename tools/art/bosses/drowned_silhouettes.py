"""The Drowned Elder redesign, session 1 step 1: three takes on the Lure-Eyed Oracle, as cuboid blockouts.

The brief (docs/art/bosses/drowned_elder/overhaul/plan.md, 2026-11-17): an ancient Elder Guardian, its great eye gone
blind, seeing through three anglerfish lures that rise from its back, each tipped with a small glowing eye; a crown of
bleached dead coral and wet sponge over its brow; tattered fins.

Shared: vanilla's guardian (GuardianModel, 26.2 client) at 4x: the 12x12x16 body with its four 2-texel plates, the twelve
2x9x2 spikes on the body's edges, the 2x2 eye, the three tail segments and the fin.

The takes differ in where the lures grow and where their eyes hang:
  A  the Angler      three lures arch forward over the brow; their eyes hang in front of the blind face
  B  the Candelabra  three tall stalks rise from the back and hook over at the top; the eyes look down from high above
  C  the Spine-Seer  three of its own top spikes have grown into the lures, curving forward: the strongest vanilla tie

Each is shown idle, aiming (the multi-beam: each lure locked on its own player) and in the surge (reared up).
Model units: 16 = one block, y up, the face towards -z. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/drowned_silhouettes.py [A B C]
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
from bosses.tide_silhouettes import beam, euler, frame  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s1_silhouettes"
PALETTE = {
    "hide": (176, 170, 150), "hide_dark": (133, 126, 106), "spike": (126, 110, 170), "eye_blind": (226, 232, 236),
    "coral": (222, 214, 204), "coral_dark": (176, 168, 160), "sponge": (176, 162, 72), "fin": (150, 140, 160),
    "lure": (120, 112, 104), "lure_eye": (130, 236, 210), "lid": (90, 84, 78),
}
K = 4
C = np.array([0.0, 44.0, 0.0])          # the body's centre (vanilla's (0, 16, 0))
IDLE, AIM, SURGE = "idle", "aim", "surge"
POSES = (IDLE, AIM, SURGE)


def v(x, y, z):
    """A vanilla model point (relative to the body's centre, texels) in model units."""
    return C + np.array([x, y, z], float) * K


def box(g, name, lo, hi, mat):
    lo, hi = np.array(lo, float), np.array(hi, float)
    g.box(name, tuple((lo + hi) / 2), tuple(hi - lo), mat)


def oriented(g, name, centre, along, size, mat, up=(0, 1, 0)):
    """A box whose local y runs along `along`."""
    along = np.array(along, float)
    side = np.cross(up, along)
    if np.linalg.norm(side) < 1e-6:
        side = np.array([1.0, 0, 0])
    m = frame(side, along)
    g.box(name, tuple(np.array(centre, float)), size, mat, rotation=euler(m))


# ---- the guardian -----------------------------------------------------------------------------------------------------

def oct_prism(g, name, cy, w, h, z0, z1, mat, cham=0.28):
    """A section of the body along z: an octagon in cross-section (vanilla's plates, chamfered), from z0 to z1 (texels)."""
    ch = cham * min(w, h)
    zc, ln = (z0 + z1) / 2, z1 - z0
    g.box(name + "_a", tuple(v(0, cy, zc)), (w * K, (h - 2 * ch) * K, ln * K), mat)
    g.box(name + "_b", tuple(v(0, cy, zc)), ((w - 2 * ch) * K, h * K, ln * K - 0.4), mat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box(f"{name}_c{sx}{sy}", tuple(v(sx * (w / 2 - 0.75 * ch), cy + sy * (h / 2 - 0.75 * ch), zc)),
                  (ch * math.sqrt(2) * K, ch / math.sqrt(2) * K, ln * K - 0.8), mat, rotation=(0, 0, 45 * sx * sy))


# the body's sections, front to back: (name, centre y, width, height, z from, z to), texels
SECTIONS = [("head", 0, 16, 15, -8, 1), ("mid", -0.5, 13.5, 12.5, 1, 9), ("rear", -1, 9.5, 8.5, 9, 15),
            ("tail0", -1.5, 5, 5, 15, 21)]
# spikes: (x, y, z) on the sections' edges, the way they point, length (texels); short underneath so they never read as legs
SPIKES = [((0, 7.5, -5), (0, 1, -0.5), 9), ((0, 6.5, 4), (0, 1, 0.3), 9), ((7.5, 5.5, -3), (1, 1, 0), 8),
          ((-7.5, 5.5, -3), (-1, 1, 0), 8), ((8, 0, -5), (1, 0, -0.4), 8), ((-8, 0, -5), (-1, 0, -0.4), 8),
          ((6.5, -0.5, 5), (1, 0, 0.5), 7), ((-6.5, -0.5, 5), (-1, 0, 0.5), 7), ((6.5, 5, 5), (1, 1, 0.4), 7),
          ((-6.5, 5, 5), (-1, 1, 0.4), 7), ((5, -6.5, -2), (0.7, -1, 0), 4), ((-5, -6.5, -2), (-0.7, -1, 0), 4)]


def spike(g, name, at, d, length):
    d = np.array(d, float)
    d /= np.linalg.norm(d)
    base = v(*at)
    oriented(g, name + "_base", base + d * length * K * 0.25, d, (1.3 * K, length * K * 0.55, 1.3 * K), "spike")
    oriented(g, name + "_tip", base + d * length * K * 0.7, d, (0.6 * K, length * K * 0.45, 0.6 * K), "spike")


def body(g, skip_spikes=()):
    for name, cy, w, h, z0, z1 in SECTIONS:
        oct_prism(g, name, cy, w, h, z0, z1, "hide" if name != "head" else "hide")
    # vanilla's plates on the head, a texel proud: the face keeps the guardian's look
    oct_prism(g, "face_plate", 0, 14, 13, -8.6, -7.9, "hide_dark")
    # the blind eye, big, milky, in a dark octagonal socket, under a heavy brow
    oct_prism(g, "socket", 1.0, 6.5, 5.5, -9.1, -8.5, "lid", cham=0.3)
    oct_prism(g, "eye", 1.0, 4.4, 3.6, -9.5, -9.0, "eye_blind", cham=0.3)
    g.box("brow", tuple(v(0, 4.6, -9.4)), (15 * K, 2.4 * K, 3 * K), "hide_dark", rotation=(16, 0, 0))
    # an anglerfish's underbite: the lower jaw juts past the face, slightly open; its teeth are small guardian spikes
    g.box("jaw", tuple(v(0, -6.6, -9.0)), (17 * K, 2.6 * K, 8 * K), "hide_dark", rotation=(-14, 0, 0))
    box(g, "mouth", v(-7, -5.6, -9.2), v(7, -4.0, -5), "lid")
    # needle fangs, irregular: long ones rising from the jutting jaw and leaning back, shorter ones hanging from the face
    lower = [(-6.8, 3.6, 10), (-4.6, 2.2, -6), (-2.6, 4.4, 8), (-0.4, 2.6, -4), (1.8, 4.8, 6), (4.0, 2.4, -8), (6.4, 3.8, 9)]
    for i, (x, h, lean) in enumerate(lower):
        g.box(f"fang_lo{i}", tuple(v(x, -5.0 + h / 2 - 0.6, -12.0 - abs(x) * 0.1)), (0.7 * K, h * K, 0.7 * K), "spike",
              rotation=(24, 0, lean))
    upper = [(-5.6, 2.2, -8), (-3.0, 3.0, 6), (-0.8, 1.8, -5), (1.4, 2.8, 7), (3.8, 2.0, -6), (5.8, 2.6, 8)]
    for i, (x, h, lean) in enumerate(upper):
        g.box(f"fang_up{i}", tuple(v(x, -4.2 - h / 2 + 0.6, -9.2)), (0.6 * K, h * K, 0.6 * K), "spike", rotation=(-12, 0, lean))
    for i, (at, d, length) in enumerate(SPIKES):
        if i not in skip_spikes:
            spike(g, f"spike{i}", at, d, length)
    # the tail: tapering on from the body, curling down a little, the fin at its end
    g.box("tail1", tuple(v(0, -2.6, 23.5)), (3.5 * K, 3.5 * K, 6 * K), "hide", rotation=(-12, 0, 0))
    g.box("tail2", tuple(v(0, -4, 28.5)), (2.2 * K, 2.2 * K, 5 * K), "hide", rotation=(-20, 0, 0))
    g.box("tail_fin", tuple(v(0, -5.8, 32.5)), (0.5 * K, 10 * K, 7 * K), "fin", rotation=(-24, 0, 0))
    # tattered pectoral fins behind the face, swept back and down; a dorsal fin along the back
    for sx in (-1, 1):
        g.box(f"fin_{sx}", tuple(v(sx * 9.6, -3.5, 2)), (0.5 * K, 7 * K, 10 * K), "fin", rotation=(-28, 0, sx * 32))
    g.box("dorsal", tuple(v(0, 8.5, 10)), (0.5 * K, 5 * K, 10 * K), "fin", rotation=(-14, 0, 0))


def crown(g):
    """Bleached dead coral fans (crossed planes, like vanilla coral) and wet sponge over the brow."""
    fans = [(-4.5, -6.5, 5.5), (0.0, -7.2, 6.8), (4.5, -6.0, 5.0), (-2.2, -3.5, 6.0), (2.6, -3.0, 5.2), (-5.5, -1.5, 4.2),
            (5.5, -1.0, 4.0), (0.6, -0.4, 4.6)]
    for i, (x, z, h) in enumerate(fans):
        base = v(x, 7.2, z)
        height = h * K
        for a in (45, -45):
            g.box(f"coral{i}_{a}", tuple(base + (0, height / 2, 0)), (h * K * 0.85, height, 0.6), "coral",
                  rotation=(0, a + i * 13, (i % 3 - 1) * 10))
    for i, (x, z, s) in enumerate([(-2.0, -6.4, 3.2), (3.4, -5.2, 2.6), (-5.8, -3.6, 2.4), (1.2, -2.0, 2.2), (5.6, -3.4, 2.0)]):
        g.box(f"sponge{i}", tuple(v(x, 7.5 + s / 2 - 0.5, z)), (s * K, s * K, s * K), "sponge", rotation=(0, i * 17, 0))


def lure(g, name, pts, eye_dir):
    """A stalk through a few points, tapering, ending in a hooded glowing eye that looks along eye_dir."""
    pts = [np.array(p, float) for p in pts]
    for i in range(len(pts) - 1):
        w = 6.0 - 3.0 * i / max(1, len(pts) - 2)
        beam(g, f"{name}_seg{i}", pts[i], pts[i + 1], max(3.0, w), "lure")
    tip = pts[-1]
    d = np.array(eye_dir, float)
    d /= np.linalg.norm(d)
    oriented(g, f"{name}_hood", tip - d * 2.5, d, (14, 6, 14), "lid")
    oriented(g, f"{name}_eye", tip + d * 1.5, d, (9, 9, 9), "lure_eye")


def bezier(a, b, c, n=7):
    a, b, c = (np.array(p, float) for p in (a, b, c))
    return [(1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c for t in np.linspace(0, 1, n)]


AIMS = [np.array(d, float) for d in ((-0.55, -0.35, -1), (0, -0.4, -1), (0.55, -0.35, -1))]


def angler(g, pose):
    for i, sx in enumerate((-1, 0, 1)):
        root = v(sx * 3, 8, 2 + abs(sx) * 1.5)
        if pose == AIM:
            tip = root + AIMS[i] / np.linalg.norm(AIMS[i]) * 70 + (0, 30, 0)
            ctrl = root + (sx * 6, 34, -6)
            eye = AIMS[i]
        else:
            tip = v(sx * 7, 9 - abs(sx) * 2, -17 - abs(sx) * 1)
            ctrl = v(sx * 5, 22, -4)
            eye = (sx * 0.2, -0.6, -1)
        lure(g, f"lure{i}", bezier(root, ctrl, tip), eye)


def candelabra(g, pose):
    for i, sx in enumerate((-1, 0, 1)):
        root = v(sx * 4, 8, 5)
        top = root + (sx * 12, 64 + (8 if sx == 0 else 0), 6)
        if pose == AIM:
            tip = top + AIMS[i] / np.linalg.norm(AIMS[i]) * 18
            eye = AIMS[i]
        else:
            tip = top + (sx * 4, -10, -14)
            eye = (sx * 0.2, -0.8, -1)
        pts = bezier(root, root + (sx * 2, 36, 4), top, 6) + [top + (tip - top) * 0.6, tip]
        lure(g, f"lure{i}", pts, eye)


def seer(g, pose):
    """Three of its own top spikes (the crown's, the right and the left) grown into the lures."""
    for i, (sx, idx) in enumerate(((0, 0), (1, 2), (-1, 3))):
        root = v(*SPIKES[idx][0])
        out = np.array(SPIKES[idx][1], float)
        out /= np.linalg.norm(out)
        if pose == AIM:
            j = {0: 1, 1: 2, -1: 0}[sx]
            tip = root + AIMS[j] / np.linalg.norm(AIMS[j]) * 64 + (0, 26, 0)
            ctrl = root + out * 30
            eye = AIMS[j]
        else:
            ctrl = root + out * 34 + (0, 10, 0)
            tip = v(sx * 9, 13, -16) if sx else v(0, 16, -18)
            eye = (sx * 0.3, -0.6, -1)
        lure(g, f"lure{i}", bezier(root, ctrl, tip), eye)


TAKES = {"A": ("The Angler", angler, ()), "B": ("The Candelabra", candelabra, ()),
         "C": ("The Spine-Seer", seer, (0, 2, 3))}


def build(key, pose):
    title, lures, skip = TAKES[key]
    m = Model(f"drowned_{key}_{pose}")
    pitch = {SURGE: 32, IDLE: 0, AIM: -4}[pose]
    lift = 18 if pose == SURGE else 0
    g = m.group("body", tuple(C + (0, lift, 0)), (pitch, 0, 0))
    gb = g.group("bodyparts", (0, 0, 0))
    body(gb, skip)
    crown(gb)
    lures(gb, pose)
    if lift:
        for c in m.cubes:
            c.frm[1] += lift
            c.to[1] += lift
            c.origin[1] += lift
        for grp in m.groups:
            if grp.name == "bodyparts":
                grp.origin = [grp.origin[0], grp.origin[1] + lift, grp.origin[2]]
    # it glides: the idle's lowest point hovers ~1.4 blocks over the floor, every pose at the same height
    rest = HOVER_SHIFT.setdefault(key, None)
    if rest is None and pose == IDLE:
        HOVER_SHIFT[key] = 22 - float(m.bounds()[0][1])
    shift = HOVER_SHIFT.get(key) or 0.0
    for grp in m.groups:
        grp.origin = [grp.origin[0], grp.origin[1] + shift, grp.origin[2]]
    for c in m.cubes:
        c.frm[1] += shift
        c.to[1] += shift
        c.origin[1] += shift
    return m, title


HOVER_SHIFT = {}


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 34, "height": 5.0, "dist": 16.5, "target_z": 4.6},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -26, "height": 1.62, "dist": 15, "target_z": 4.4,
     "player": False},
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
            if pose == IDLE:
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(x) / 16, 2) for x in hi - lo], "lowest", round(float(lo[1]), 1),
                      "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Drowned Elder {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(POSES):
            for c, vw in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{vw['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[vw['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_').replace('-', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
