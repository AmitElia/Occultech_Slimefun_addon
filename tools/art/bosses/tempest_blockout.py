"""The Tempest redesign, session 1 step 3: the full blockout.

Picked 2026-11-17: C, the Frozen Blast (seven seal shards thrown wide) + W3, the Full Storm (a floor twister under the
core, four galaxy arms whirling out of it carrying the shards) + H2, the Seal Circlet (vanilla's breeze head at 4x, a
cracked stone ring round its crown) + K3, the Cracked Heart (the heavy core on its corner, split into eight blocks with
seams of light, its top tip blown off and floating beside the head).

Poses, one per moment of the fight (Tempest.java):
  idle    the frozen blast, everything drifting
  locked  the gust volley: the seal snaps back together behind the core, the wind drawn in tight, the tip pulled close
  burst   the wind burst: shards and arms flung out to their widest, the head thrown back
  spent   after the burst: shards on the floor, arms limp, the funnel a spout, the seams dark, the head bowed

The arms use fewer, longer boards than take 2 so the three-quarter view calms down.
Model units: 16 = one block, y up, the face towards -z. Run: python tools/art/bosses/tempest_blockout.py
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tempest_silhouettes as ts, volley_crone_s2 as v2  # noqa: E402

ts.CORE_Y = 54 + 18          # floated a block higher for the twister (take 2)
from bosses import tempest_study as st, tempest_take2 as t2  # noqa: E402
from bosses.tide_silhouettes import plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s1_blockout"
IDLE, LOCKED, BURST, SPENT = "idle", "locked", "burst", "spent"
POSES = (IDLE, LOCKED, BURST, SPENT)
CORE, CORE_Y, TIP = ts.CORE, ts.CORE_Y, ts.CORE_TIP
HEAD_Y = CORE_Y + TIP - 4
PALETTE = dict(st.PALETTE)


def head(g, pose):
    pitch = {SPENT: -22, BURST: 14, LOCKED: 4}.get(pose, 0)
    y = HEAD_Y - (10 if pose == SPENT else 0)
    h = g.group("head", (0, y, 0), (pitch, 0, 0))
    st.h2(h, y)


def core(g, pose):
    """K3 with the pose: the seams dim when spent, the blown tip pulled close when locked, flung when bursting."""
    y = CORE_Y - (8 if pose == SPENT else 0)
    rot = rotation_matrix(ts.CORE_ROT)
    q = CORE / 4
    octs = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    tip = max(octs, key=lambda o: (rot @ np.array(o, float))[1])
    c = g.group("core", (0, y, 0), ts.CORE_ROT)
    c.box("core_light", (0, y, 0), (CORE * 0.86,) * 3, "recess" if pose == SPENT else "core_glow")
    gap = 1.6 if pose == BURST else 1.2
    for o in octs:
        if o != tip:
            c.box(f"oct{o}", (o[0] * q, y + o[1] * q, o[2] * q), (CORE / 2 - gap,) * 3, "steel")
    fling = {IDLE: (26, -2, -18), LOCKED: (16, 2, -10), BURST: (34, 4, -24), SPENT: (24, -30, -16)}[pose]
    lift = rot.T @ np.array(fling, float)
    at = (tip[0] * q + lift[0], y + tip[1] * q + lift[1], tip[2] * q + lift[2])
    t = c.group("tip", at, (25, 30, -20))
    t.box("tip_block", at, (CORE / 2 - 1.2,) * 3, "steel")


def arms(g, pose):
    """W3's galaxy arms in the seal's plane, eight long boards each."""
    cz, n, seg = 6.0, 4, 8
    r0 = 15.0
    r1, sweep = {IDLE: (62.0, 1.15), LOCKED: (40.0, 1.6), BURST: (90.0, 0.95), SPENT: (26.0, 0.55)}[pose]
    sweep *= math.pi
    b = math.log(r1 / r0) / sweep
    for k in range(n):
        th0 = k * 2 * math.pi / n + 0.4
        pts = []
        for i in range(seg + 1):
            t = i / seg
            th = th0 + sweep * t
            r = r0 * math.exp(b * sweep * t)
            x, y = r * math.cos(th), r * math.sin(th)
            if pose == SPENT:
                y -= 18 * t ** 1.5
            low = -(CORE_Y - 4)
            if y < low:                       # an arm that reaches the floor spreads along it
                y = low - (y - low) * 0.05
            pts.append((x, CORE_Y + y, cz + 2 * math.sin(3 * t + k)))
        for i in range(seg):
            w = (14 if pose == BURST else 11) * (1 - i / seg) ** 0.8 + 2
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2 - CORE_Y
            plank(g, f"arm{k}_{i}", pts[i], pts[i + 1], w, 1.8, "wind" if k % 2 == 0 else "wind_dark", up=(mx, my, 0))


def seal(g, pose):
    n = len(ts.SEVEN)
    if pose == LOCKED:
        ts.seal(g, "seal", (0, CORE_Y, 12), (90, 0, 0), ts.SEVEN, pose, [0.8] * n, [0] * n, [0] * n)
        return
    push = [18, 22, 16, 24, 19, 23, 17]
    lift = [14, -12, 8, -16, 12, -8, 16]
    tilt = [28, -34, 22, -30, 36, -24, 30]
    spin = [40, -30, 55, -45, 35, -50, 25]
    drop = None
    if pose == BURST:
        push = [p * 1.6 + 6 for p in push]
        lift = [v * 1.4 for v in lift]
    elif pose == SPENT:
        push = [14, 16, 12, 18, 14, 16, 12]
        lift = [6, -6, 4, -8, 6, -4, 8]
        tilt = [60, -55, 50, -62, 58, -52, 60]
        spin = [20, -15, 25, -20, 15, -25, 10]
        drop = [(0, -120, 0)] * n          # all on the floor (lift_above rests them on it)
    ts.seal(g, "seal", (0, CORE_Y, 0), (90, 0, 0), ts.SEVEN, pose, push, lift, tilt, spin=spin, drop=drop,
            glow=pose != SPENT)


def funnel(g, pose):
    t2.funnel(g, {BURST: IDLE}.get(pose, pose))
    t2.rods(g, pose if pose != BURST else IDLE)


def subtree_cubes(g):
    out = []
    for ch in g.children:
        out.extend(subtree_cubes(ch) if hasattr(ch, "children") else [ch])
    return out


def lift_above(g, floor=1.0):
    """Shift a bone's subtree up (in world space) until nothing in it is below the floor; shards rest on it."""
    cubes = subtree_cubes(g)
    low = min(float(c.corners()[:, 1].min()) for c in cubes)
    if low >= floor:
        return
    parent = g.parent.world_matrix()[:3, :3]
    d = parent.T @ np.array([0.0, floor - low, 0.0])
    def move(node):
        node.origin = (np.array(node.origin) + d).tolist()
        for ch in node.children:
            if hasattr(ch, "children"):
                move(ch)
            else:
                ch.frm = (np.array(ch.frm) + d).tolist()
                ch.to = (np.array(ch.to) + d).tolist()
                ch.origin = (np.array(ch.origin) + d).tolist()
    move(g)


def build(pose):
    m = Model(f"tempest_blockout_{pose}")
    body = m.group("body", (0, 0, 0))
    funnel(body.group("funnel", (0, 0, 0)), pose)
    core(body, pose)
    head(body, pose)
    seal(body, pose)
    arms(body.group("arms", (0, CORE_Y, 0)), pose)
    for g in m.groups:
        if g.name.startswith("seal_s") or g.name in ("funnel", "tip"):
            lift_above(g)
    return m


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 28, "height": 4.2, "dist": 15, "target_z": 4.2},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -24, "height": 1.62, "dist": 12.5, "target_z": 4.2,
     "player": False},
]
LABELS = dict(ts.LABELS)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    v2.PALETTE.update(PALETTE)
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tempest, the Shattered Seal: full blockout", font=sheet._font(26), fill=sheet.INK)
    for r, pose in enumerate(POSES):
        m = build(pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS)
        lo, hi = m.bounds()
        print(pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "min y", round(float(lo[1]), 1),
              "cubes", len(m.cubes))
        for c, v in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


if __name__ == "__main__":
    main()
