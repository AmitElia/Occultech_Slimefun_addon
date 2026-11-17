"""The Abyssal Warden redesign, session 1 step 2: the window study - the crammed eye, the bursting side window and
the mutated hand, close up, three takes.

Built on take 2 (warden_take2.py: the Lost Helmet, the hand out of his right side window, the growth). Each take
pairs an eye with a hand; parts can be mixed.
  W1  the Slit Eye      the eyeball pressed flat against the glass, crammed flesh bulging into the window's rim,
                        a cyan iris with a dark inner ring and a vertical slit pupil (a guardian's stare)
        the Swollen Hand  take 2's hand: broad and buff, a sixth finger, uneven fingers, barnacles on the arm
  W2  the Ringed Eye    a bigger iris in three rings round a round pupil that can tighten (the beam's tell), less
                        flesh, more veins
        the Webbed Hand   four long fingers webbed together, long hooked claws, a fin of spines down the forearm
  W3  the Lidded Eye    a heavy fold of flesh sagging over the top of the eye, the iris looking up from under it
        the Crusted Hand  long knobbly fingers of three joints, one stunted, barnacle clusters over the back of the
                        hand and up the arm
In all three the side window has burst: jagged glass left in its frame, the grille's bars bent outwards, the arm's
flesh bulging against the frame where it squeezes through.

Run from the repository root: python tools/art/bosses/warden_window.py
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, warden_silhouettes as w1, warden_take2 as t2  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s1_window"
PALETTE = dict(t2.PALETTE, iris_dark=(30, 120, 140), iris_light=(150, 244, 248), glint=(250, 252, 255),
               flesh_wet=(132, 120, 116), web=(84, 112, 98))
beam, lump, limb, oriented = t2.beam, t2.lump, t2.limb, t2.oriented
_window = w1.window


# ---- the eyes (built inside the front window's group: its face at z, the glass at z + 0.5, outward is -z) ------------

def flesh_rim(w, name, x, y, z, rw, n=9, size=6.5):
    for i in range(n):
        a = math.radians(360 * i / n + 13)
        w.box(f"{name}_flesh{i}", (x + math.sin(a) * (rw - 1.5), y + math.cos(a) * (rw - 1.5), z + 2.2),
              (size, size * 0.8, 3), "flesh_wet", rotation=(0, 0, 360 * i / n))


def veins(w, name, x, y, z, rw, n=6):
    for i in range(n):
        a = math.radians(i * 360 / n + 25)
        l = 6 + (i * 3) % 5
        beam(w, f"{name}_vein{i}", (x + math.cos(a) * rw * 0.95, y + math.sin(a) * rw * 0.95, z + 0.45),
             (x + math.cos(a) * (rw * 0.95 - l), y + math.sin(a) * (rw * 0.95 - l), z + 0.45), 1.1, "vein")


def eye_slit(w, x, y, z, rw):
    w1.disc(w, "sclera", (x, y, z + 5), rw + 0.8, 9, "sclera")
    flesh_rim(w, "rim", x, y, z, rw)
    ix, iy = x + 0.2 * rw, y - 0.1 * rw
    w1.disc(w, "iris", (ix, iy, z + 0.25), rw * 0.5, 1, "iris")
    w1.disc(w, "iris_inner", (ix, iy, z + 0.05), rw * 0.34, 0.6, "iris_dark")
    w.box("pupil", (ix, iy, z - 0.2), (2.4, rw * 0.6, 0.6), "pupil")
    w.box("glint", (ix - rw * 0.2, iy + rw * 0.22, z - 0.3), (1.6, 1.6, 0.4), "glint")
    veins(w, "eye", x, y, z, rw)


def eye_ringed(w, x, y, z, rw):
    w1.disc(w, "sclera", (x, y, z + 5), rw + 0.8, 9, "sclera")
    flesh_rim(w, "rim", x, y, z, rw, n=5, size=5)
    ix, iy = x + 0.15 * rw, y - 0.05 * rw
    w1.disc(w, "iris_outer", (ix, iy, z + 0.3), rw * 0.62, 1, "iris_dark")
    w1.disc(w, "iris", (ix, iy, z + 0.1), rw * 0.5, 0.6, "iris")
    w1.disc(w, "iris_light", (ix, iy, z - 0.1), rw * 0.36, 0.6, "iris_light")
    w1.disc(w, "pupil", (ix, iy, z - 0.3), rw * 0.2, 0.6, "pupil")
    w.box("glint", (ix - rw * 0.26, iy + rw * 0.26, z - 0.45), (1.6, 1.6, 0.4), "glint")
    veins(w, "eye", x, y, z, rw, n=10)


def eye_lidded(w, x, y, z, rw):
    w1.disc(w, "sclera", (x, y, z + 5), rw + 0.8, 9, "sclera")
    flesh_rim(w, "rim", x, y, z, rw)
    ix, iy = x + 0.1 * rw, y - 0.25 * rw
    w1.disc(w, "iris", (ix, iy, z + 0.25), rw * 0.46, 1, "iris")
    w1.disc(w, "iris_inner", (ix, iy, z + 0.05), rw * 0.3, 0.6, "iris_dark")
    w1.disc(w, "pupil", (ix, iy, z - 0.2), rw * 0.16, 0.6, "pupil")
    # the heavy lid: flesh sagging over the top of the eye, pressed against the glass, its edge lumpy
    w.box("lid", (x, y + rw * 0.52, z + 1.2), (2 * rw * 0.95, rw * 0.95, 3), "flesh_wet")
    for i in range(5):
        w.box(f"lid_edge{i}", (x + (i - 2) * rw * 0.34, y + rw * 0.06 - abs(i - 2) * 0.8, z + 1.0),
              (rw * 0.36, 3, 3.2), "flesh", rotation=(0, 0, (i - 2) * 8))
    veins(w, "eye", x, y, z, rw, n=4)


# ---- the hands ------------------------------------------------------------------------------------------------------

def hand_basis(wrist, palm_dir, finger_dir):
    wrist, n, f = (np.array(v, float) for v in (wrist, palm_dir, finger_dir))
    n /= np.linalg.norm(n)
    f = f - n * np.dot(f, n)
    f /= np.linalg.norm(f)
    return wrist, n, f, np.cross(f, n)


def webbed_hand(g, name, shoulder, elbow, wrist, palm_dir, finger_dir):
    limb(g, name + "_upper", shoulder, elbow, 16, 13, "flesh", bulges=((0.5, 9, (1, 0.6)),), barnacles=2)
    lump(g, name + "_elbow", elbow, 13, "flesh_dark")
    limb(g, name + "_fore", elbow, wrist, 14, 11, "flesh")
    e, wv = np.array(elbow, float), np.array(wrist, float)
    up = np.cross(wv - e, [0, 0, 1.0])
    up = up / (np.linalg.norm(up) or 1) * 8
    for i in range(5):                                       # a fin of spines down the forearm
        p = e + (wv - e) * (0.15 + 0.17 * i)
        beam(g, f"{name}_fin{i}", p, p + up * (1.1 - i * 0.12) + (wv - e) * 0.06, 2, "flesh_dark")
    wrist, n, f, across = hand_basis(wrist, palm_dir, finger_dir)
    oriented(g, name + "_palm", wrist + f * 9, (22, 20, 8), across, f, n, "flesh")
    tips = []
    for i, (off, length, splay) in enumerate(((-8, 26, 14), (-2.6, 30, 4), (2.6, 30, -4), (8, 26, -14))):
        base = wrist + f * 19 + across * off
        sp = math.radians(splay)
        fd = f * math.cos(sp) - across * math.sin(sp)          # fanned out from the middle
        bend = base + fd * length * 0.6 + n * 2
        tip = bend + fd * length * 0.4 + n * 7
        beam(g, f"{name}_finger{i}_a", base, bend, 4.4, "flesh")
        beam(g, f"{name}_finger{i}_b", bend, tip, 3.6, "flesh")
        beam(g, f"{name}_claw{i}", tip, tip + fd * 6 + n * 5, 2.4, "nail")
        tips.append((base, bend))
    for i in range(3):                                       # the webbing between the fingers
        (b0, m0), (b1, m1) = tips[i], tips[i + 1]
        c = (b0 + b1 + m0 + m1) / 4
        oriented(g, f"{name}_web{i}", c - n * 0.5, (float(np.linalg.norm(b1 - b0)) + 1.5,
                                                   float(np.linalg.norm(m0 - b0)) * 1.05, 1.2), across, f, n, "web")
    tb = wrist + f * 5 - across * 11
    beam(g, name + "_thumb", tb, tb - across * 9 + f * 12 + n * 4, 5, "flesh")


def crusted_hand(g, name, shoulder, elbow, wrist, palm_dir, finger_dir):
    limb(g, name + "_upper", shoulder, elbow, 17, 14, "flesh", bulges=((0.4, 10, (1, 0.5)),), barnacles=6)
    lump(g, name + "_elbow", elbow, 14, "flesh_dark")
    limb(g, name + "_fore", elbow, wrist, 15, 12, "flesh", barnacles=5)
    wrist, n, f, across = hand_basis(wrist, palm_dir, finger_dir)
    oriented(g, name + "_palm", wrist + f * 10, (24, 22, 9), across, f, n, "flesh")
    for i, (du, dv, s) in enumerate(((-6, 6, 4), (4, 10, 5), (8, 3, 3.5), (-2, 14, 3), (0, 2, 4.5))):
        g.box(f"{name}_crust{i}", tuple(wrist + f * dv + across * du - n * 5.5), (s, 2.6, s), "barnacle",
              rotation=(0, 25 * i, 0))
    fingers = ((-9, 24, 4.4, 14), (-3, 30, 4.8, 4), (3, 28, 4.8, -5), (9, 9, 4.6, -16))     # the last one stunted
    for i, (off, length, thick, splay) in enumerate(fingers):
        base = wrist + f * 21 + across * off
        sp = math.radians(splay)
        fd = f * math.cos(sp) - across * math.sin(sp)          # fanned out from the middle
        pts = [base, base + fd * length * 0.4 + n * 1.5, base + fd * length * 0.75 + n * 4,
               base + fd * length + n * 8]
        for k in range(3):
            beam(g, f"{name}_finger{i}_{k}", pts[k], pts[k + 1], thick * (1 - 0.12 * k), "flesh")
            lump(g, f"{name}_joint{i}_{k}", pts[k + 1], thick * 1.35, "flesh_dark")
        beam(g, f"{name}_claw{i}", pts[3], pts[3] + fd * 4 + n * 3, thick * 0.5, "nail")
    tb = wrist + f * 6 - across * 12
    beam(g, name + "_thumb", tb, tb - across * 8 + f * 12 + n * 4, 6, "flesh")


# ---- the burst side window ------------------------------------------------------------------------------------------

def burst(bow):
    """Jagged glass left in the side window's frame, two bent bars, the arm's flesh bulging against the frame."""
    d = t2.SIDE / np.linalg.norm(t2.SIDE)
    centre = np.array(t2.C) + d * math.sqrt(t2.R ** 2 - 8 ** 2)
    up, fwd = np.array([0, 1.0, 0]), np.cross(d, [0, 1.0, 0])
    for i in range(7):                                       # shards pointing in from the rim
        a = math.radians(i * 51 + 10)
        rim = centre + (up * math.cos(a) + fwd * math.sin(a)) * 8.5
        tip = centre + (up * math.cos(a) + fwd * math.sin(a)) * (4 + i % 3) + d * 0.5
        beam(bow, f"burst_shard{i}", rim, tip, 1.4, "shard")
    for i, s in enumerate((-1, 1)):                          # two bars, bent outwards
        a = centre + fwd * 4 * s + up * 8 + d * 1
        b = centre + fwd * 5 * s + up * 2 + d * 7
        c = centre + fwd * 7 * s - up * 3 + d * 10
        beam(bow, f"bent_bar{i}_a", a, b, 1.8, "brass")
        beam(bow, f"bent_bar{i}_b", b, c, 1.8, "brass")
    for i in range(6):                                       # flesh squeezing out round the arm
        a = math.radians(i * 60 + 30)
        lump(bow, f"squeeze{i}", centre + (up * math.cos(a) + fwd * math.sin(a)) * 7 + d * 2.5, 6, "flesh_dark")


TAKES = {
    "W1": ("The Slit Eye and the Swollen Hand", eye_slit, t2.mutated_hand),   # take 2's hand
    "W2": ("The Ringed Eye and the Webbed Hand", eye_ringed, webbed_hand),
    "W3": ("The Lidded Eye and the Crusted Hand", eye_lidded, crusted_hand),
}


def build(key, part):
    """part: 'eye' (the helmet front, no hose or growth), 'side' (the burst side window with the arm raised), 'hand'
    (the hand alone)."""
    _, eye, hand = TAKES[key]

    def window(g, name, c, r, d, rw, frame_mat="brass", bolts=8, grille=False, eye_=False, look=(0.25, -0.1), **kw):
        has_eye = kw.pop("eye", eye_)
        w = _window(g, name, c, r, d, rw, frame_mat, bolts, grille, False, look)
        if has_eye:
            dd = np.array(d, float) / np.linalg.norm(d)
            x, y, z = np.array(c) + dd * math.sqrt(r * r - rw * rw)
            eye(w, x, y, z, rw)
        return w

    w1.window = window
    m = Model(f"warden_{key}_{part}")
    if part == "hand":
        root = m.group("root", (0, 0, 0))
        # palm to the camera, fingers up, so its shape reads (the arm is left out: the side view shows it)
        hand(root, "hand", (0, 0, 40), (0, 10, 20), (0, 30, 0), (0, 0, -1), (0, 1, 0))
        arm = re.compile(r"_(upper|fore|elbow)_|_elbow|_fin\d")      # not _finger: the fingers stay
        for c in [c for c in m.cubes if arm.search(c.name)]:
            m.cubes.remove(c)                                # the hand alone: the arm is shown in the side view
            c.group.children.remove(c)
        w1.window = _window
        return m
    saved = (t2.growth, w1.hose, t2.mutated_hand)
    t2.growth = lambda g: None
    w1.hose = lambda *a, **k: None
    t2.mutated_hand = hand
    try:
        t2.helmet(m, "idle" if part == "eye" else "raised")
        if part == "side":
            burst(next(g for g in m.groups if g.name == "bowed"))
            for c in [c for c in m.cubes if c.name == "ring_mark"]:
                m.cubes.remove(c)
                c.group.children.remove(c)
    finally:
        t2.growth, w1.hose, t2.mutated_hand = saved
        w1.window = _window
    return m


VIEWS = {
    "eye": [{"name": "eye", "mode": "flat", "camera": "persp", "yaw": 0, "height": 4.3, "dist": 6.2, "target_z": 4.1,
             "player": False, "lens": 45}],
    "side": [{"name": "side", "mode": "flat", "camera": "persp", "yaw": 55, "height": 5.2, "dist": 14,
              "target_z": 5.6, "player": False, "lens": 32}],
    "hand": [{"name": "hand", "mode": "flat", "camera": "persp", "yaw": 12, "height": 3.6, "dist": 6.0,
              "target_z": 3.6, "player": False, "lens": 40}],
}
LABELS = {"eye": "the eye in its window", "side": "the side window burst, the arm out", "hand": "the hand"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(PALETTE)
    for key in TAKES:
        for part, views in VIEWS.items():
            m = build(key, part)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key, views)
        print(key, "done")
    tw, th, pad, top = 470, 400, 12, 56
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + len(TAKES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Abyssal Warden, step 2: the eye, the burst side window, the hand", font=sheet._font(26),
            fill=sheet.INK)
    for r, (key, (title, _, _)) in enumerate(TAKES.items()):
        for c, part in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / f"{part}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key} {title}: {LABELS[part]}", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "window.png")


if __name__ == "__main__":
    main()
