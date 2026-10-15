"""The Elder of Ash: hero shots in his key poses, with the volcano's effects as the fight draws them.

Each shot is the shipped rig (session 6's atlas, the stage's lava tint), posed with session 2's pose code, from a low
three-quarter hero angle (a perspective camera at about a player's eye height, a little off to his right). The
effects are drawn as sprites where MireMonarch.java spawns its particles, and match its stages:
  calm      the dormant plume: a lazy column of smoke rising from the crater and drifting with the wind, a few embers,
            ash falling round the volcano, a wisp from the pipe
  coil      the leap's warning: the plume thick and dark, fireballs popping at the crater's rim, lava spraying up
  erupt     at 2/3: a tall boiling column, lava bombs arcing out (the magma spawn), embers and ash everywhere
  blown     below 1/3: the top gone; a fountain of lava welling up out of the wide crater under a heavy black plume
  dying     the plume thinning to a last wisp, the lava cooled

Run from the repository root: python tools/art/bosses/ash_hero.py
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import ash_s2 as s2, ash_s3 as s3, ash_s4 as s4, ash_s6 as s6, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s8_ship/hero"
S6 = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s6_variants"
P = {k: v[1] for k, v in s2.POSES.items()}
WIND = np.array((0.55, 0.0, 0.35))            # the plume leans right and back (model units per unit of height)

SHOTS = [
    # name, title, pose spec, stage atlas, blown top, effects
    ("idle", "idle: the dormant volcano smoking", {"plant": True}, "dormant", False, "calm"),
    ("coil", "the coil: the leap's warning", P["coil"], "coil", False, "coil"),
    ("leap", "the leap", dict(P["leap"], y=34), "dormant", False, "calm"),
    ("tongue", "the tongue lash", P["tongue"], "dormant", False, "calm"),
    ("erupt", "the eruption at 2/3", P["erupt"], "awake", False, "erupt"),
    ("blown", "below 1/3: the top blown off", dict(P["erupt"], head=14, jaw=-14), "blown", True, "blown"),
    ("death", "death: the volcano cooling", P["death"], "dead", False, "dying"),
]


# ---- effect sprites ------------------------------------------------------------------------------------------------

def box(centre, size, color, alpha=1.0, emit=False, rot=(0, 0, 0)):
    c = np.array(centre, float)
    h = np.array(size, float) / 2 if hasattr(size, "__len__") else np.array((size, size, size), float) / 2
    r = rotation_matrix(rot)
    corners = [c + r @ (np.array((sx, sy, sz)) * h) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return {"corners": [list(map(float, p)) for p in corners], "color": [v / 255 for v in color], "alpha": alpha,
            "emit": emit}


def plume(rng, base, height, size0, size1, dark, light, density=2, alpha=(0.92, 0.4), tight=1.0):
    """Puffs rising from base, growing, leaning with the wind, darker at the root and paler up high."""
    out = []
    n = max(4, int(height / 5))
    for i in range(n):
        t = i / (n - 1)
        centre = np.array(base) + WIND * (t ** 1.3) * height + np.array((0, t * height, 0))
        size = size0 + (size1 - size0) * t ** 0.8
        shade = tuple(int(d + (l - d) * t) for d, l in zip(dark, light))
        for k in range(density):
            j = rng.normal(0, size * 0.28 * tight, 3)
            s = size * rng.uniform(0.6, 1.0)
            out.append(box(centre + j, s, shade, alpha[0] + (alpha[1] - alpha[0]) * t,
                           rot=rng.uniform(-40, 40, 3)))
    return out


def embers(rng, base, n, spread, rise, size=1.6, fall=False):
    out = []
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = abs(rng.normal(0, spread))
        y = rng.uniform(-rise * 0.3 if fall else 0, rise)
        p = np.array(base) + np.array((math.cos(a) * r, y, math.sin(a) * r))
        col = (255, 230, 140) if rng.random() < 0.35 else (255, 140, 40)
        out.append(box(p, size * rng.uniform(0.7, 1.3), col, 1.0, True, rng.uniform(0, 90, 3)))
    return out


def ash(rng, centre, n, radius, y0, y1):
    out = []
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(radius * 0.3, radius)
        p = np.array(centre) + np.array((math.cos(a) * r, rng.uniform(y0, y1) - centre[1], math.sin(a) * r))
        out.append(box(p, 1.0, (200, 196, 190), 0.9, False, rng.uniform(0, 90, 3)))
    return out


def fireball(rng, centre, r):
    out = [box(centre, r * 1.6, (60, 52, 50), 0.75, rot=rng.uniform(0, 90, 3))]
    for _ in range(6):
        out.append(box(np.array(centre) + rng.normal(0, r * 0.35, 3), r * rng.uniform(0.6, 1.0),
                       (255, 200, 90) if rng.random() < 0.5 else (255, 120, 30), 1.0, True, rng.uniform(0, 90, 3)))
    return out


def bombs(rng, base, n, reach, height):
    """Lava bombs arcing out of the crater, each with a smoky trail behind it."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        d = np.array((math.cos(a), 0, math.sin(a)))
        t = rng.uniform(0.35, 0.75)
        pos = np.array(base) + d * reach * t + np.array((0, height * 4 * t * (1 - t), 0))
        out.append(box(pos, 6.5, (255, 160, 60), 1.0, True, rng.uniform(0, 90, 3)))
        for k in range(1, 4):
            tt = t - 0.05 * k
            trail = np.array(base) + d * reach * tt + np.array((0, height * 4 * tt * (1 - tt), 0))
            out.append(box(trail, 3 + k, (70, 64, 62), 0.55 - 0.1 * k, rot=rng.uniform(0, 90, 3)))
    return out


def fountain(rng, base, height, scale=1.0):
    """Lava welling up out of the crater: a glowing column, white-hot at its root, spattering at its top."""
    out = []
    for i in range(22):
        t = i / 21
        spread = (3.0 * (1 - t) + 1.5) * scale
        p = np.array(base) + np.array((rng.normal(0, spread), t * height, rng.normal(0, spread)))
        out.append(box(p, (7 - 3.5 * t) * scale, (255, 240, 170) if t < 0.45 else (255, 150, 50), 1.0, True,
                       rng.uniform(0, 90, 3)))
    for _ in range(10):                                  # spatter falling back round the rim
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6, 16) * scale
        p = np.array(base) + np.array((math.cos(a) * r, rng.uniform(height * 0.4, height * 1.1), math.sin(a) * r))
        out.append(box(p, 2.4 * scale, (255, 130, 40), 1.0, True, rng.uniform(0, 90, 3)))
    return out


def effects(kind, crater, bowl, rng):
    fx = []
    smoke_dark, smoke_light = (52, 48, 50), (132, 128, 126)
    if kind == "calm":
        fx += plume(rng, crater + (0, 4, 0), 72, 7, 26, smoke_dark, smoke_light, density=3, alpha=(0.8, 0.22))
        fx += embers(rng, crater + (0, 3, 0), 6, 4, 14)
        fx += ash(rng, crater, 26, 60, 40, 110)
        fx += plume(rng, bowl + (0, 3, 0), 16, 1.8, 5, (150, 148, 146), (190, 188, 184), density=1, alpha=(0.6, 0.2))
    elif kind == "coil":
        fx += plume(rng, crater + (0, 4, 0), 86, 10, 34, (34, 30, 32), (112, 108, 106), density=4, alpha=(0.86, 0.25))
        for i in range(3):
            a = 2 * math.pi * i / 3 + 0.4
            fx += fireball(rng, crater + (math.cos(a) * 10, 5 + i * 3, math.sin(a) * 10), 8)
        fx += embers(rng, crater + (0, 6, 0), 30, 8, 30, 2.0)
        fx += ash(rng, crater, 36, 64, 40, 120)
    elif kind == "erupt":
        fx += plume(rng, crater + (0, 24, 0), 100, 14, 46, (30, 26, 28), (120, 114, 110), density=4, alpha=(0.85, 0.25),
                    tight=0.8)
        fx += fountain(rng, crater + (0, 1, 0), 30, 1.5)
        fx += bombs(rng, crater + (0, 8, 0), 7, 120, 90)
        fx += embers(rng, crater + (0, 8, 0), 44, 14, 50, 2.0)
        fx += ash(rng, crater, 50, 90, 30, 150)
    elif kind == "blown":
        fx += plume(rng, crater + (0, 30, 0), 90, 16, 48, (22, 18, 20), (96, 90, 88), density=4, alpha=(0.85, 0.25))
        fx += fountain(rng, crater + (0, 1, 0), 34, 1.8)
        fx += embers(rng, crater + (0, 6, 0), 40, 14, 44, 2.0)
        fx += ash(rng, crater, 50, 80, 30, 140)
    elif kind == "dying":
        fx += plume(rng, crater + (0, 3, 0), 34, 2.5, 9, (120, 116, 112), (170, 166, 162), density=2, alpha=(0.45, 0.12),
                    tight=0.5)
    return fx


# ---- render -------------------------------------------------------------------------------------------------------

HERO = [{"name": "hero", "location": (8.6, 12.2, 2.5), "target": (0, 0.2, 5.4), "scale": 12, "lens": 22,
         "player": False, "res": (1500, 1125)}]


def centre_top(model, name):
    c = next(c for c in model.cubes if c.name == name)
    pts = c.corners()
    return np.array((pts[:, 0].mean(), pts[:, 1].max(), pts[:, 2].mean()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s3.setup()
    bb = json.loads((S6 / f"{s3.MODEL_ID}.bbmodel").read_text(encoding="utf-8"))
    for name, title, spec, stage, blown, kind in SHOTS:
        model = s2.rig(f"hero_{name}", decals=False)
        s2.pose(model, spec)
        s2.finish(model)
        crater = centre_top(model, "crater_blown" if blown else "crater")
        bowl = centre_top(model, "pipe_bowl")
        fx = effects(kind, crater, bowl, np.random.default_rng(abs(hash(name)) % 2 ** 32))
        boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
                  "glow": s4.zone_for(c).startswith(s4.GLOWING), "uv": bb["elements"][i]["faces"]}
                 for i, c in enumerate(model.cubes) if not s6.hidden_in(c, blown)]
        out = OUT / name
        out.mkdir(parents=True, exist_ok=True)
        job = out / "job.json"
        job.write_text(json.dumps({"texture": str(S6 / "atlases" / f"{stage}.png"), "out": out.as_posix(),
                                   "boxes": boxes, "fx": fx, "views": HERO, "player_at": (6.5, 3.5)}), encoding="utf-8")
        r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                            str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                           capture_output=True, text=True)
        if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
            raise SystemExit(r.stdout[-3000:] + r.stderr[-3000:])
        job.unlink()
        print(name, "rendered")
    tw, th, pad, top = 620, 465, 12, 56
    cols = 3
    rows = (len(SHOTS) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Elder of Ash - hero shots, with the volcano's effects", font=sheet._font(28), fill=sheet.INK)
    for n, (name, title, *_rest) in enumerate(SHOTS):
        x, y = pad + (n % cols) * (tw + pad), top + (n // cols) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / name / "hero.png", tw, th), (x, y))
        dr.text((x, y + th + 6), title, font=sheet._font(18), fill=sheet.DIM)
    img.save(OUT.parent / "hero_poses.png")


if __name__ == "__main__":
    main()
