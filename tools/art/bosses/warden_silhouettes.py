"""The Abyssal Warden redesign, session 1 step 1: three takes on the diving-helmet bathysphere, as cuboid blockouts.

The brief (docs/art/bosses/abyssal_warden/overhaul/plan.md, 2026-10-29): a round bathysphere that looks like the
sphere of an old diving helmet; in its central window a crammed eye that looks around and fires the lasers; rivets
and pressure valves that burst out in jets of spray; at 33% the window cracks and a hand comes out, the pupil still
visible above it.

The sphere is built the way a cuboid model can be round: latitude bands of tilted panels (12 round, 22.5 degrees
apart), flat caps top and bottom, the panels left out behind each window. The three takes differ in what frames it:
  A  the Diving Helmet   the classic standard dress helmet: three windows (front and both sides, grilled), the top
                         window, a flared breastplate under it with wing nuts, the air hose from the gooseneck behind
  B  the Bathysphere     a pressure sphere: one big front window, an equator flange and two straps of heavy rivets, a
                         hatch on top with its wheel, a ballast weight under it, the hose from the hatch
  C  the Lost Helmet     a helmet with no diver: no breastplate, the open neck ring underneath dark inside with kelp
                         hanging out of it, bowed a little forward, three windows
Each is shown idle and at 33% (the hand out through the cracked window). Model units: 16 = one block, y up, the
window towards -z. The blue figure is a player (1.8 blocks). Colours are blockout zones, not the palette; the glass is
see-through.

Run from the repository root: python tools/art/bosses/warden_silhouettes.py [A B C]
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

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s1_silhouettes"
PALETTE = {
    "copper": (178, 104, 68), "copper_dark": (122, 66, 42), "verdigris": (74, 148, 126), "brass": (170, 132, 70),
    "rivet": (210, 150, 104), "glass": (150, 214, 224, 90), "sclera": (226, 218, 200), "iris": (70, 226, 236),
    "pupil": (16, 20, 26), "vein": (160, 60, 60), "skin": (86, 118, 104), "skin_dark": (60, 86, 76),
    "hose": (72, 62, 50), "hose_band": (128, 88, 58), "kelp": (52, 104, 50), "dark": (14, 16, 20),
    "lead": (70, 72, 80), "spray": (200, 236, 244, 120),
}
R = 36                       # the sphere's radius: 4.5 blocks across


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


def sphere(g, name, c, r, mat, skip=lambda d: False, n=12, bands=(-67.5, -45, -22.5, 0, 22.5, 45, 67.5), t=3.0,
           band_mats=None):
    """A sphere of tilted panels: latitude bands between the given angles, n panels round each; `skip` leaves out
    the panels whose middle direction it accepts (the windows). Flat caps close the top and the bottom."""
    cx, cy, cz = c
    for b, (p0, p1) in enumerate(zip(bands, bands[1:])):
        y0, y1 = cy + r * math.sin(math.radians(p0)), cy + r * math.sin(math.radians(p1))
        r0, r1 = r * math.cos(math.radians(p0)), r * math.cos(math.radians(p1))
        h = y1 - y0
        tilt = math.degrees(math.atan2(r0 - r1, h))
        slant = math.hypot(h, r0 - r1)
        rm = (r0 + r1) / 2
        width = 2 * rm * math.tan(math.pi / n) * 1.1
        pm = math.radians((p0 + p1) / 2)
        for i in range(n):
            a = 360 * i / n + 180 / n
            ar = math.radians(a)
            d = np.array([math.sin(ar) * math.cos(pm), math.sin(pm), math.cos(ar) * math.cos(pm)])
            if skip(d):
                continue
            m = band_mats[b] if band_mats else mat
            g.box(f"{name}_{b}_{i}", (cx + rm * math.sin(ar), (y0 + y1) / 2, cz + rm * math.cos(ar)), (width, slant, t),
                  m, rotation=(-tilt, a, 0))
    top, bottom = math.radians(bands[-1]), math.radians(bands[0])
    for nm, p in ((name + "_cap_top", top), (name + "_cap_bottom", bottom)):
        rr = r * math.cos(p) + 0.6
        y = cy + r * math.sin(p)
        g.box(nm + "_a", (cx, y, cz), (2 * rr * 0.83, t, 2 * rr * 0.83), mat)
        g.box(nm + "_b", (cx, y, cz), (2 * rr * 0.83, t, 2 * rr * 0.83), mat, rotation=(0, 45, 0))


def disc(g, name, c, r, thick, mat, facing="z"):
    """A round plate as a regular octagon (a cross of two bars and four 45-degree corner plates), facing along an
    axis. r is the octagon's apothem."""
    x, y, z = c
    side = 2 * r * math.tan(math.pi / 8)                     # an octagon side
    cut = r - side / 2                                       # how far each corner is cut back, along each axis
    plate = cut / math.sqrt(2) + 0.8                         # a corner plate's thickness: the notch's depth, plus overlap
    reach = (r - plate / 2) / math.sqrt(2)                   # its centre, along each axis

    def put(nm, du, dv, su, sv, angle=0.0):
        if facing == "z":
            g.box(nm, (x + du, y + dv, z), (su, sv, thick), mat, rotation=(0, 0, angle))
        elif facing == "y":
            g.box(nm, (x + du, y, z + dv), (su, thick, sv), mat, rotation=(0, -angle, 0))
        else:
            g.box(nm, (x, y + dv, z + du), (thick, sv, su), mat, rotation=(angle, 0, 0))

    put(name + "_h", 0, 0, 2 * r, side, 0)
    put(name + "_v", 0, 0, side, 2 * r, 0)
    for su in (-1, 1):
        for sv in (-1, 1):
            put(f"{name}_c{su}{sv}", su * reach, sv * reach, side + 0.4, plate, -45 * su * sv)


def ring(g, name, c, r_in, r_out, thick, mat, n=16, facing="z", skip=lambda a: False):
    """A flat ring of n slabs round a centre, in the plane across `facing` (a window frame, a flange)."""
    cx, cy, cz = c
    rm, w = (r_in + r_out) / 2, r_out - r_in
    seg = 2 * rm * math.tan(math.pi / n) * 1.08
    for i in range(n):
        a = 360 * i / n
        ar = math.radians(a)
        if skip(a):
            continue
        if facing == "z":
            g.box(f"{name}_{i}", (cx + rm * math.sin(ar), cy + rm * math.cos(ar), cz), (seg, w, thick), mat,
                  rotation=(0, 0, -a))
        else:                                                # facing y: a horizontal ring
            g.box(f"{name}_{i}", (cx + rm * math.sin(ar), cy, cz + rm * math.cos(ar)), (seg, thick, w), mat,
                  rotation=(0, a, 0))


def on_sphere(c, r, d, out=0.0):
    d = np.array(d, float) / np.linalg.norm(d)
    return tuple(np.array(c) + d * (r + out))


def window(g, name, c, r, d, rw, frame_mat="brass", bolts=8, grille=False, eye=False, look=(0.25, -0.1)):
    """A bolted window where direction d meets the sphere: a frame ring, the glass, bolts; the eye behind the front one."""
    d = np.array(d, float) / np.linalg.norm(d)
    dist = math.sqrt(r * r - rw * rw)
    centre = np.array(c) + d * dist
    yaw = math.degrees(math.atan2(d[0], -d[2]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d[1]))))
    w = g.group(name, tuple(centre), (pitch, -yaw, 0))
    x, y, z = centre
    ring(w, name + "_frame", (x, y, z - 1.5), rw, rw + 4.5, 5, frame_mat)
    disc(w, name + "_glass", (x, y, z + 0.5), rw + 0.5, 1, "glass")
    for i in range(bolts):
        a = math.radians(360 * i / bolts + 180 / bolts)
        w.box(f"{name}_bolt{i}", (x + (rw + 2.3) * math.sin(a), y + (rw + 2.3) * math.cos(a), z - 4.6), (2.6, 2.6, 2), "rivet")
    if grille:
        for i, dx in enumerate((-rw * 0.5, 0, rw * 0.5)):
            w.box(f"{name}_bar{i}", (x + dx, y, z - 3), (1.8, 2 * rw * 0.95, 1.8), frame_mat)
    if eye:
        # the crammed eye fills the glass: sclera bulging against it, the iris turned to look, the pupil
        disc(w, name + "_sclera", (x, y, z + 5), rw + 0.8, 9, "sclera")
        ix, iy = x + look[0] * rw, y + look[1] * rw
        disc(w, name + "_iris", (ix, iy, z + 0.2), rw * 0.48, 1, "iris")
        disc(w, name + "_pupil", (ix, iy, z - 0.2), rw * 0.2, 1, "pupil")
        for i, (a, l) in enumerate(((20, 9), (160, 8), (250, 7), (320, 9))):                    # veins
            ar = math.radians(a)
            beam(w, f"{name}_vein{i}", (x + math.cos(ar) * rw * 0.95, y + math.sin(ar) * rw * 0.95, z + 0.4),
                 (x + math.cos(ar) * (rw * 0.95 - l), y + math.sin(ar) * (rw * 0.95 - l), z + 0.4), 1.2, "vein")
    return w


def valve(g, name, c, r, d, length=7, wheel=5):
    """A pressure valve standing out of the sphere: a stem along d and a hand-wheel across its end."""
    d = np.array(d, float) / np.linalg.norm(d)
    a, b = on_sphere(c, r, d, -1), on_sphere(c, r, d, length)
    beam(g, name + "_stem", a, b, 3.5, "copper_dark")
    beam(g, name + "_cap", on_sphere(c, r, d, length - 1.5), on_sphere(c, r, d, length + 0.5), wheel * 1.4, "brass")


def hose(g, name, start, points, w0=7, w1=4, mat="hose"):
    """The air hose trailing like the guardian's tail: segments thinning to a brass nozzle, banded."""
    pts = [start] + points
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        w = w0 + (w1 - w0) * i / max(1, len(pts) - 2)
        beam(g, f"{name}_{i}", a, b, w, mat)
        beam(g, f"{name}_band{i}", tuple(np.array(a) * 0.8 + np.array(b) * 0.2),
             tuple(np.array(a) * 0.7 + np.array(b) * 0.3), w + 1.2, "hose_band")
    beam(g, name + "_nozzle", pts[-1], tuple(np.array(pts[-1]) + (np.array(pts[-1]) - np.array(pts[-2])) * 0.25),
         w1 + 2, "brass")


def hand(g, name, wrist, reach, palm_down=True):
    """The hand out through the cracked window: forearm from inside, a big palm, four fingers and a thumb, reaching
    forward and down (to slam)."""
    wx, wy, wz = wrist
    beam(g, name + "_forearm", (wx, wy + 4, wz + 14), wrist, 9, "skin_dark")
    rx, ry, rz = reach
    beam(g, name + "_palm", wrist, reach, 13, "skin")
    d = np.array(reach) - np.array(wrist)
    d = d / np.linalg.norm(d)
    side = np.array([1.0, 0, 0])
    for i, off in enumerate((-4.5, -1.5, 1.5, 4.5)):
        base = np.array(reach) + side * off
        tip = base + d * (9 - abs(off) * 0.4) + np.array([0, -3, 0])
        beam(g, f"{name}_finger{i}", tuple(base), tuple(tip), 3, "skin")
    beam(g, name + "_thumb", tuple(np.array(wrist) * 0.4 + np.array(reach) * 0.6 + side * -7),
         tuple(np.array(reach) + side * -9 + d * 3), 3, "skin")


# ---- the takes ---------------------------------------------------------------------------------------------------

FRONT = np.array([0, 0, -1.0])


def near(d, axis, deg):
    return math.degrees(math.acos(max(-1, min(1, float(np.dot(d, axis) / np.linalg.norm(axis)))))) < deg


def take_a(m, cracked):
    root = m.group("root", (0, 0, 0))
    c = (0, 60, 0)
    side_l, side_r, top = np.array([-1, 0.05, -0.1]), np.array([1, 0.05, -0.1]), np.array([0, 0.75, -0.65])
    skip = lambda d: near(d, FRONT, 27) or near(d, side_l, 15) or near(d, side_r, 15) or near(d, top, 11)  # noqa: E731
    sphere(root, "hull", c, R, "copper", skip)
    window(root, "window", c, R, FRONT, 16, eye=True)
    window(root, "side_l", c, R, side_l, 8, grille=True, bolts=6)
    window(root, "side_r", c, R, side_r, 8, grille=True, bolts=6)
    window(root, "top_window", c, R, top, 6, bolts=6)
    # the breastplate (corselet) flaring under the neck ring, wing nuts on its flange
    ring(root, "neck_ring", (0, 60 - R * 0.85, 0), R * 0.5, R * 0.62, 5, "brass", facing="y")
    import importlib
    s1 = importlib.import_module("bosses.archevoker_silhouettes")
    s1.ring_panels(root, "breastplate", 60 - R * 0.82, 60 - R - 14, R * 0.58, R * 1.02, "copper_dark", n=12, t=3,
                   start=15)
    ring(root, "flange", (0, 60 - R - 13, 0), R * 0.98, R * 1.12, 4, "brass", facing="y")
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        root.box(f"wingnut{i}", (math.sin(a) * R * 1.05, 60 - R - 10, math.cos(a) * R * 1.05), (5, 6, 5), "rivet",
                 rotation=(0, i * 45 + 22.5, 0))
    for i, d in enumerate(((1, 0.7, 0.5), (-1, 0.7, 0.5), (1, -0.4, 0.8), (-1, -0.4, 0.8), (0.6, 0.9, -0.2),
                           (-0.6, 0.9, -0.2))):
        valve(root, f"valve{i}", c, R, d)
    # the gooseneck behind, and the hose trailing down like the guardian's tail
    g0 = on_sphere(c, R, (0, 0.55, 1), 2)
    hose(root, "hose", g0, [(0, 70, 52), (0, 44, 76), (0, 20, 92), (0, 6, 112)])
    if cracked:
        hand(root, "hand", (0, 48, -36), (0, 34, -60))
    return root


def take_b(m, cracked):
    root = m.group("root", (0, 0, 0))
    c = (0, 52, 0)
    skip = lambda d: near(d, FRONT, 31)  # noqa: E731
    sphere(root, "hull", c, R, "copper", skip)
    window(root, "window", c, R, FRONT, 19, eye=True, bolts=12)
    # the equator flange stops at the window's frame (a = 180 is the front, -z)
    ring(root, "equator", (0, 52, 0), R - 1, R + 4, 6, "copper_dark", n=20, facing="y", skip=lambda a: abs(a - 180) < 40)
    for i in range(16):                                     # rivets along the equator flange
        a = math.radians(i * 22.5 + 11.25)
        if abs(math.sin(a)) < 0.5 and math.cos(a) < 0:
            continue
        root.box(f"eq_rivet{i}", (math.sin(a) * (R + 4.5), 55, math.cos(a) * (R + 4.5)), (2.4, 2.4, 2.4), "rivet")
    for i, d in enumerate(((1, 0, 0.6), (-1, 0, 0.6), (0.7, 0, 1), (-0.7, 0, 1))):
        valve(root, f"valve{i}", c, R + 3, d, length=6)
    # a hatch on top with its wheel, a ballast weight underneath
    disc(root, "hatch", (0, 52 + R + 1, 0), 10, 4, "copper_dark", facing="y")
    ring(root, "hatch_wheel", (0, 52 + R + 7, 0), 6, 8, 1.6, "brass", n=10, facing="y")
    beam(root, "hatch_stem", (0, 52 + R + 2, 0), (0, 52 + R + 7, 0), 2, "brass")
    disc(root, "ballast", (0, 52 - R - 3, 0), 9, 6, "lead", facing="y")
    hose(root, "hose", (0, 52 + R + 2, 4), [(0, 100, 30), (0, 76, 58), (0, 44, 80), (0, 18, 96), (0, 6, 116)])
    if cracked:
        hand(root, "hand", (0, 38, -36), (0, 24, -60))
    return root


def take_c(m, cracked):
    root = m.group("root", (0, 0, 0))
    bow = root.group("bowed", (0, 56, 0), (12, 0, 0))                    # bowed forward a little
    c = (0, 56, 0)
    side_l, side_r = np.array([-1, 0.05, -0.1]), np.array([1, 0.05, -0.1])
    neck = np.array([0, -1.0, 0.1])
    skip = lambda d: near(d, FRONT, 27) or near(d, side_l, 15) or near(d, side_r, 15) or near(d, neck, 34)  # noqa: E731
    sphere(bow, "hull", c, R, "copper", skip, band_mats=["verdigris", "copper", "copper", "copper", "copper",
                                                           "copper"])
    window(bow, "window", c, R, FRONT, 16, eye=True)
    window(bow, "side_l", c, R, side_l, 8, grille=True, bolts=6)
    window(bow, "side_r", c, R, side_r, 8, grille=True, bolts=6)
    # the open neck underneath: a ragged brass ring, darkness inside, kelp hanging out
    ring(bow, "neck_ring", (0, 56 - R * 0.82, 2), R * 0.48, R * 0.62, 5, "brass", facing="y")
    disc(bow, "neck_dark", (0, 56 - R * 0.7, 2), R * 0.5, 2, "dark", facing="y")
    # kelp spilling out of the neck: short, thin, curling outwards (long straight strands read as legs)
    for i in range(9):
        a = math.radians(i * 40 + 10)
        x0, z0 = math.sin(a) * 11, math.cos(a) * 11 + 2
        l = 9 + (i * 7) % 8
        mid = (x0 * 1.6, 56 - R * 0.75 - l * 0.6, z0 * 1.6 + 3)
        beam(bow, f"kelp{i}", (x0, 56 - R * 0.72, z0), mid, 2, "kelp")
        beam(bow, f"kelp{i}_tip", mid, (x0 * 2.3, 56 - R * 0.75 - l, z0 * 2.3 + 6), 1.6, "kelp")
    for i, d in enumerate(((1, 0.7, 0.5), (-1, 0.7, 0.5), (1, -0.3, 0.8), (-1, -0.3, 0.8))):
        valve(bow, f"valve{i}", c, R, d)
    g0 = on_sphere(c, R, (0, 0.55, 1), 2)
    hose(bow, "hose", g0, [(0, 66, 52), (0, 40, 74), (0, 18, 90), (0, 6, 110)])
    if cracked:
        hand(bow, "hand", (0, 44, -36), (0, 30, -60))
    return root


TAKES = {"A": ("The Diving Helmet", take_a), "B": ("The Bathysphere", take_b), "C": ("The Lost Helmet", take_c)}
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 12, "target_z": 3.2},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.4, "dist": 11, "target_z": 3.4,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 11, "target_z": 3.4,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "flat_front": "front", "sil_side": "side, silhouette", "clay_eye": "a player's eye"}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        title, fn = TAKES[key]
        for old in (OUT / key).rglob("*") if (OUT / key).exists() else ():
            if old.is_file():
                old.unlink()
        for pose in ("idle", "cracked"):
            m = Model(f"warden_{key}_{pose}")
            fn(m, pose == "cracked")
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Abyssal Warden {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(("idle", "cracked")):
            for col, v in enumerate(VIEWS):
                x, y = pad + col * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                label = "idle" if pose == "idle" else "33%: the hand out"
                dr.text((x, y + th + 6), f"{label}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
