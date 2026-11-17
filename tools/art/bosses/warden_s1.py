"""The Abyssal Warden redesign, session 1 step 3: the full blockout.

Everything picked in session 1 (docs/art/bosses/abyssal_warden/overhaul/plan.md and the session 1 READMEs), in one model:
- C, the Lost Helmet (take 2): the copper helmet sphere bowed a little forward, the grilled side windows, the valves,
  the air hose trailing like a tail, the open neck with the growth hanging from it (the fleshy mass, the tendrils, the
  kelp);
- W1's slit eye crammed in the front window, flesh bulging into the window's rim. Its veins are texture now, not cubes
  (the user's change);
- W1's hand: at 33% it bursts out of his right side window, swollen and buff, six uneven clawed fingers. Its barnacles
  are now scattered like an infection (the user's change): uneven clusters of different sizes in random spots along
  the arm, a few lone ones, a crust over the back of the hand and the knuckles.
Poses: idle; the hand raised over a player (the smash's wind-up); the slam. Model units: 16 = one block, y up, the
window towards -z, his right towards +x.

Run from the repository root: python tools/art/bosses/warden_s1.py
"""
import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, warden_silhouettes as w1, warden_take2 as t2  # noqa: E402
from bosses import warden_window as ww  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s1_blockout"
PALETTE = dict(ww.PALETTE, barnacle_old=(150, 146, 132))
_limb, _hand, _window = t2.limb, t2.mutated_hand, ww._window


def barnacle_patch(g, name, centre, normal, seed, count, spread):
    """A clump of barnacles round a point on a surface: uneven sizes, crowded, some old and pale, none in a row."""
    rng = np.random.default_rng(seed)
    normal = np.array(normal, float) / np.linalg.norm(normal)
    a = np.cross(normal, [0, 1.0, 0])
    if np.linalg.norm(a) < 1e-3:
        a = np.cross(normal, [1.0, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(normal, a)
    for i in range(count):
        r = spread * math.sqrt(rng.random())
        th = rng.random() * 2 * math.pi
        s = float(rng.choice([2.0, 2.6, 3.2, 4.0, 5.0], p=[0.25, 0.3, 0.2, 0.15, 0.1]))
        p = np.array(centre, float) + (a * math.cos(th) + b * math.sin(th)) * r + normal * s * 0.45
        mat = "barnacle_old" if rng.random() < 0.3 else "barnacle"
        g.box(f"{name}_{i}", tuple(map(float, p)), (s, s * 0.75, s), mat, rotation=(0, float(rng.integers(0, 4)) * 22.5, 0))


def infected_limb(g, name, a, b, w0, w1_, mat, bulges=(), barnacles=0):
    """take 2's swollen limb without its row of barnacles: patches in random spots round it instead (seeded by name)."""
    _limb(g, name, a, b, w0, w1_, mat, bulges, 0)
    if not barnacles:
        return
    a, b = np.array(a, float), np.array(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    side = np.cross(d, [0, 1.0, 0])
    side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-3 else np.array([1.0, 0, 0])
    up = np.cross(side, d)
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    for k in range(barnacles + 1):
        t = rng.uniform(0.1, 0.9)
        # on one of the beam's four faces (it is square in section), not lost inside its corners
        th = math.radians(90 * int(rng.integers(0, 4)) + rng.uniform(-20, 20))
        n = side * math.cos(th) + up * math.sin(th)
        w = w0 + (w1_ - w0) * t
        centre = a + (b - a) * t + n * w * 0.5 / max(abs(math.cos(th)), abs(math.sin(th)))
        big = rng.random() < 0.5
        barnacle_patch(g, f"{name}_patch{k}", centre, n, int(rng.integers(1 << 30)), int(rng.integers(3, 9) if big else
                       rng.integers(1, 3)), 5 if big else 1.5)


def infected_hand(g, name, shoulder, elbow, wrist, palm_dir, finger_dir):
    _hand(g, name, shoulder, elbow, wrist, palm_dir, finger_dir)
    wv, n, f, across = ww.hand_basis(wrist, palm_dir, finger_dir)
    barnacle_patch(g, name + "_back_crust", wv + f * 9 - n * 4.6 + across * 4, -n, 11, 9, 6)   # the back of the hand
    barnacle_patch(g, name + "_knuckle_crust", wv + f * 21 - n * 6.5 - across * 6, -n, 23, 4, 3)


def no_veins(*a, **k):
    return None


def build(name, pose):
    """The whole Warden in a pose: idle, raised (the smash's wind-up, the ring on the floor) or slam."""

    def window(g, nm, c, r, d, rw, frame_mat="brass", bolts=8, grille=False, eye_=False, look=(0.25, -0.1), **kw):
        has_eye = kw.pop("eye", eye_)
        w = _window(g, nm, c, r, d, rw, frame_mat, bolts, grille, False, look)
        if has_eye:
            dd = np.array(d, float) / np.linalg.norm(d)
            x, y, z = np.array(c) + dd * math.sqrt(r * r - rw * rw)
            ww.eye_slit(w, x, y, z, rw)
        return w

    saved = (w1.window, t2.limb, t2.mutated_hand, ww.veins)
    w1.window, t2.limb, t2.mutated_hand, ww.veins = window, infected_limb, infected_hand, no_veins
    try:
        m = Model(name)
        t2.helmet(m, pose)
        if pose != "idle":
            ww.burst(next(g for g in m.groups if g.name == "bowed"))
    finally:
        w1.window, t2.limb, t2.mutated_hand, ww.veins = saved
    return m


VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 14, "target_z": 3.8,
     "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.8, "dist": 15, "target_z": 3.9},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": -90, "height": 3.6, "dist": 15, "target_z": 3.8,
     "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 4.6, "dist": 15, "target_z": 3.8,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -25, "height": 1.62, "dist": 11, "target_z": 4.0,
     "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 35, "height": 3.8, "dist": 15, "target_z": 3.9,
     "player": False},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]
POSE_VIEWS = [VIEWS[1], VIEWS[0], VIEWS[4]]
CLOSE = [
    {"name": "eye_close", "mode": "flat", "camera": "persp", "yaw": 0, "height": 4.1, "dist": 9.5, "target_z": 4.0,
     "player": False, "lens": 50},
    {"name": "arm_close", "mode": "flat", "camera": "persp", "yaw": 70, "height": 5.0, "dist": 9.5, "target_z": 4.8,
     "player": False, "lens": 36},
]
LABELS = {"front": "front", "three_quarter": "three-quarter", "side": "side", "back": "back three-quarter",
          "player_eye": "a player's eye", "clay": "clay", "sil_front": "silhouette, front", "sil_side": "silhouette, side",
          "eye_close": "the eye", "arm_close": "the arm, its barnacles"}
POSES = (("idle", "idle"), ("raised", "33%: the hand raised"), ("slam", "the slam"))


def grid(rows, title, out, tw=420, th=330):
    pad, top = 12, 60
    cols = max(len(r) for r in rows)
    img = Image.new("RGB", (pad + cols * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 14), title, font=sheet._font(26), fill=sheet.INK)
    for r, row in enumerate(rows):
        for c, (path, label) in enumerate(row):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(path, tw, th), (x, y))
            dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(PALETTE)
    for pose, _ in POSES:
        m = build(f"occultech_abyssal_warden_blockout_{pose}", pose)
        if pose == "idle":
            views = VIEWS
            (OUT / pose).mkdir(exist_ok=True)
            m.write_bbmodel(OUT / pose / "occultech_abyssal_warden_blockout.bbmodel")
            stats = m.stats()
            (OUT / pose / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            print("idle", stats)
        else:
            views = POSE_VIEWS + ([CLOSE[1]] if pose == "raised" else [])
            print(pose, "cubes", len(m.cubes))
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, views + ([CLOSE[0]] if pose == "idle" else []))
    r = OUT / "idle"
    grid([[(r / f"{n}.png", LABELS[n]) for n in ("front", "three_quarter", "side", "back")]],
         "Abyssal Warden blockout, idle: front, three-quarter, side, back", OUT / "views_a.png")
    grid([[(r / f"{n}.png", LABELS[n]) for n in ("player_eye", "clay", "sil_front", "sil_side")]],
         "Abyssal Warden blockout, idle: player's eye, clay, silhouettes", OUT / "views_b.png")
    grid([[(OUT / p / f"{v['name']}.png", f"{label}: {LABELS[v['name']]}") for v in POSE_VIEWS] for p, label in POSES],
         "Abyssal Warden blockout: the three poses", OUT / "poses.png")
    grid([[(OUT / "idle" / "eye_close.png", LABELS["eye_close"]), (OUT / "raised" / "arm_close.png", LABELS["arm_close"])]],
         "Abyssal Warden blockout: close up", OUT / "close.png", tw=560, th=440)


if __name__ == "__main__":
    main()
