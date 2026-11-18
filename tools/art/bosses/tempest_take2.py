"""The Tempest redesign, session 1 step 1 take 2: the Frozen Blast (C) with a bigger, more dramatic wind.

The user picked C, the Frozen Blast (2026-11-17), and asked for bigger, more dramatic wind spirals. Three winds on the
same seal, head and core (tempest_silhouettes.take_c):

  W1  the Great Funnel   a twister from the floor that flares wide under the shards, four thick bands
  W2  the Spiral Arms    four galaxy arms whirl out of the core in the seal's plane; the thrown shards ride their tips
  W3  the Full Storm     both: the funnel below, the arms round the core

Locked (the volley) draws the wind in tight and fast; spent drops it: the funnel shrinks, the arms go limp and droop.

Run from the repository root: python tools/art/bosses/tempest_take2.py [W1 W2 W3]
"""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tempest_silhouettes as ts, volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s1_take2"
IDLE, LOCKED, SPENT = ts.IDLE, ts.LOCKED, ts.SPENT
PALETTE = dict(ts.PALETTE, wind=(196, 210, 240), wind_dark=(150, 160, 214))


def rods(g, pose):
    for i in range(3):
        a = 120 * i + 30
        r = 13 if pose != SPENT else 9
        ar = math.radians(a)
        g.box(f"rod{i}", (r * math.sin(ar), 26 if pose != SPENT else 16, r * math.cos(ar)), (2 * ts.ROD_K, 8 * ts.ROD_K, 2 * ts.ROD_K),
              "rod", rotation=(22.5, a, 0))


def funnel(g, pose):
    """W1: a twister from the floor, flaring hard (radius grows with t^2.2) to just under the core's waist."""
    bottom, top, r_bot, r_top, ribbons, turns, seg, h0, h1 = 0.0, ts.CORE_Y - 17, 3.0, 42.0, 4, 1.35, 16, 4.0, 12.0
    if pose == LOCKED:
        top, r_top, turns = ts.CORE_Y - 17, 28.0, 1.8
    elif pose == SPENT:
        top, r_top, turns, h1 = ts.CORE_Y - 26, 18.0, 0.9, 7.0
    for k in range(ribbons):
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = 2 * math.pi * (turns * t + k / ribbons)
            r = r_bot + (r_top - r_bot) * t ** 1.7
            pts.append((r * math.sin(a), bottom + (top - bottom) * t, r * math.cos(a)))
        for i in range(seg):
            t = i / seg
            h = (h0 + (h1 - h0) * t) * min(1.0, (1 - t) * 4 + 0.25)   # thickens, then whips thin at the lip
            # the band leans out with the funnel's flare
            plank(g, f"fun{k}_{i}", pts[i], pts[i + 1], h, 2.0, "wind" if k % 2 == 0 else "wind_dark")


def arms(g, pose):
    """W2: four galaxy arms in the seal's plane (a little behind it), whirling out of the core: logarithmic spirals,
    wide at the root, tapering to a point; boards lie face-on to the front."""
    cz = 6.0
    n, seg = 4, 12
    r0, r1, sweep = 15.0, 70.0, 1.15 * math.pi
    if pose == LOCKED:
        r1, sweep = 40.0, 1.6 * math.pi
    elif pose == SPENT:
        r1, sweep = 34.0, 0.7 * math.pi
    b = math.log(r1 / r0) / sweep
    for k in range(n):
        th0 = k * 2 * math.pi / n + 0.4
        pts = []
        for i in range(seg + 1):
            t = i / seg
            th = th0 + sweep * t
            r = r0 * math.exp(b * sweep * t)
            x, y = r * math.cos(th), r * math.sin(th)
            if pose == SPENT:   # limp: the arms sag towards the floor
                y -= 30 * t ** 1.5
            pts.append((x, ts.CORE_Y + y, cz + 2 * math.sin(3 * t + k)))
        for i in range(seg):
            w = 13 * (1 - i / seg) ** 0.8 + 2
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2 - ts.CORE_Y
            # width runs out from the core, in the seal's plane, so the ribbon faces the front
            plank(g, f"arm{k}_{i}", pts[i], pts[i + 1], w, 1.8, "wind" if k % 2 == 0 else "wind_dark", up=(mx, my, 0))


WINDS = {
    "W1": ("The Great Funnel", lambda g, pose: (funnel(g, pose), rods(g, pose))),
    "W2": ("The Spiral Arms", lambda g, pose: (ts.vortex(g, pose), arms(g, pose))),
    "W3": ("The Full Storm", lambda g, pose: (funnel(g, pose), arms(g, pose), rods(g, pose))),
}
_vanilla_vortex = ts.vortex
FLOATED, FLOAT = ("W1", "W3"), 18


def build(key, pose):
    title, wind = WINDS[key]
    m = Model(f"tempest_c2_{key}_{pose}")
    ts.vortex = lambda g, p: None          # take_c's own vortex is replaced by this take's wind
    core_y = ts.CORE_Y
    if key in FLOATED:                      # a funnel needs height to read as a twister, not a skirt
        ts.CORE_Y = core_y + FLOAT
    try:
        ts.take_c(m, pose)
        ts.vortex = _vanilla_vortex
        wind(m.group("wind", (0, 0, 0)), pose)
    finally:
        ts.vortex = _vanilla_vortex
        ts.CORE_Y = core_y
    return m, title


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    views = ts.VIEWS
    for key in (only or WINDS):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in ts.POSES:
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, views)
            if pose == IDLE:
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(views) * (tw + pad), top + len(ts.POSES) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Tempest C, the Frozen Blast, {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(ts.POSES):
            for c, v in enumerate(views):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {ts.LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
