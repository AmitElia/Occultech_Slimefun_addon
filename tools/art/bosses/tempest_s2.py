"""The Tempest redesign, session 2: design lock (plan: docs/art/bosses/tempest/overhaul/plan.md).

The approved blockout (tempest_blockout.py: Frozen Blast + Full Storm + Seal Circlet + Cracked Heart) rebuilt as one rig
on whole texels, `occultech_tempest`:

  base (the core's centre)
    funnel > ribbon0..ribbon3 (the twister's bands, each can spin), rods (three breeze rods)
    core (stood on its corner) > glow_heart (the light inside), tip (the blown-off top block)
    hi_head (the breeze head) > glow_eyes, circlet > glow_circlet, circlet_chunk
    seal (the disc, stood up behind the core) > shard0..shard6 > glow_shard0..glow_shard6
    arms (spins in the seal's plane) > arm0..arm3 > arm0_mid > arm0_end (each a chain, so it can curl)

The bind pose is the WHOLE seal: every shard sits in its true place, so the volley's "snap together" returns every shard
bone to zero and nothing can drift. Every other moment moves the shards out from there.

Key moments (Tempest.java): idle (the frozen blast), locked (gust volley), burst (wind burst), spent (the opening),
split (below half: the seal breaks in two as the small gales join), death.

Session 1 notes fixed here: the twister's lip curls up and whips thin instead of sitting as a shelf under the core; the
idle arms end at the shards (the shards ride their tips), which opens the front silhouette.

Run from the repository root: python tools/art/bosses/tempest_s2.py [pose ...]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tempest_silhouettes as ts, volley_crone_s2 as v2  # noqa: E402

ts.CORE_Y = 72
from bosses import tempest_study as st  # noqa: E402
from bosses.archevoker_s2 import cubes_in, group, new_bone, parts_list, translate  # noqa: E402
from bosses.tempest_blockout import lift_above  # noqa: E402
from bosses.tide_silhouettes import euler, plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s2_design"
NAME = "occultech_tempest"
PALETTE = dict(st.PALETTE)
K, CORE, CORE_Y, TIP, CORE_ROT = ts.K, ts.CORE, ts.CORE_Y, ts.CORE_TIP, ts.CORE_ROT
HEAD_Y = CORE_Y + TIP - 4
SEAL_C = (0, CORE_Y, 12)          # the whole seal stands behind the core
SEAL_ROT = (90, 0, 0)
ARM_Z = 6.0
SEVEN = ts.SEVEN


# ---- the rig ------------------------------------------------------------------------------------------------------------

def funnel(f):
    """The twister: four bands on a flaring helix from the floor to under the core; the last quarter of each band
    curls up and thins to a whip (session 1's lip read as a shelf)."""
    bottom, top, r_bot, r_top, turns, seg = 2.0, CORE_Y - 17, 3.0, 40.0, 1.35, 16
    for k in range(4):
        rb = f.group(f"ribbon{k}", (0, 0, 0))
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = 2 * math.pi * (turns * t + k / 4)
            r = r_bot + (r_top - r_bot) * t ** 1.7
            y = bottom + (top - bottom) * t + 10 * max(0.0, (t - 0.85) / 0.15) ** 2   # the lip flicks up
            pts.append((r * math.sin(a), y, r * math.cos(a)))
        for i in range(seg):
            t = i / seg
            h = (4 + 8 * t) * min(1.0, (1 - t) * 4 + 0.2)      # thickens, then whips thin at the lip
            plank(rb, f"band{k}_{i}", pts[i], pts[i + 1], h, 2, "wind" if k % 2 == 0 else "wind_dark")
    rods = f.group("rods", (0, 26, 0))
    for i in range(3):
        a = 120 * i + 30
        ar = math.radians(a)
        rods.box(f"rod{i}", (13 * math.sin(ar), 26, 13 * math.cos(ar)), (2 * ts.ROD_K, 8 * ts.ROD_K, 2 * ts.ROD_K), "rod",
                 rotation=(22.5, a, 0))


def core(base, m):
    rot = rotation_matrix(CORE_ROT)
    q = CORE / 4
    octs = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    tip = max(octs, key=lambda o: (rot @ np.array(o, float))[1])
    c = base.group("core", (0, CORE_Y, 0), CORE_ROT)
    for o in octs:
        if o != tip:
            c.box(f"oct{o[0] + 1}{o[1] + 1}{o[2] + 1}", (o[0] * q, CORE_Y + o[1] * q, o[2] * q), (CORE / 2 - 1,) * 3, "steel")
    g = c.group("glow_heart", (0, CORE_Y, 0))
    g.box("heart", (0, CORE_Y, 0), (CORE - 4,) * 3, "core_glow")
    lift = rot.T @ np.array([26.0, -2.0, -18.0])
    at = (tip[0] * q + lift[0], CORE_Y + tip[1] * q + lift[1], tip[2] * q + lift[2])
    t = c.group("tip", at, (25, 30, -20))
    t.box("tip_block", at, (CORE / 2 - 1,) * 3, "steel")


def head(base, m):
    h = base.group("hi_head", (0, HEAD_Y, 0))
    st.h2(h, HEAD_Y)
    new_bone(m, h, "glow_eyes", (0, HEAD_Y + 3.5 * K, -4.2 * K), [c for c in h.children if hasattr(c, "frm") and c.name.startswith("eye")])
    circ = group(m, "circlet")
    new_bone(m, circ, "glow_circlet", circ.origin, [c for c in circ.children if hasattr(c, "frm") and "glyph" in c.name])
    chunk = next(c for c in circ.children if hasattr(c, "frm") and c.name == "circ_chunk")
    new_bone(m, circ, "circlet_chunk", chunk.origin, [chunk])


def seal(base, m):
    """The whole seal, each shard its own bone with its pivot at the shard's middle."""
    n = len(SEVEN)
    ts.seal(base, "seal", SEAL_C, SEAL_ROT, SEVEN, "bind", [0.8] * n, [0] * n, [0] * n)
    for i in range(n):
        sg = group(m, f"seal_s{i}")
        sg.name = f"shard{i}"
        new_bone(m, sg, f"glow_shard{i}", sg.origin, [c for c in sg.children if hasattr(c, "frm") and "glyph" in c.name])


def arm_points(k, r1=54.0, sweep=1.15 * math.pi, seg=9):
    r0 = 15.0
    b = math.log(r1 / r0) / sweep
    th0 = k * math.pi / 2 + 0.4
    out = []
    for i in range(seg + 1):
        t = i / seg
        th = th0 + sweep * t
        r = r0 * math.exp(b * sweep * t)
        out.append((r * math.cos(th), CORE_Y + r * math.sin(th), ARM_Z))
    return out


def arms(base, m):
    a = base.group("arms", (0, CORE_Y, ARM_Z))
    for k in range(4):
        pts = arm_points(k)
        bones = [a.group(f"arm{k}", pts[0])]
        bones.append(bones[0].group(f"arm{k}_mid", pts[3]))
        bones.append(bones[1].group(f"arm{k}_end", pts[6]))
        for i in range(9):
            w = 11 * (1 - i / 9) ** 0.8 + 2
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2 - CORE_Y
            plank(bones[i // 3], f"arm{k}_board{i}", pts[i], pts[i + 1], w, 2, "wind" if k % 2 == 0 else "wind_dark",
                  up=(mx, my, 0))


def rig(name):
    m = Model(name)
    base = m.group("base", (0, CORE_Y, 0))
    funnel(base.group("funnel", (0, 0, 0)))
    core(base, m)
    head(base, m)
    seal(base, m)
    arms(base, m)
    return m


# ---- the poses -----------------------------------------------------------------------------------------------------------

BLAST = dict(push=[18, 22, 16, 24, 19, 23, 17], lift=[14, -12, 8, -16, 12, -8, 16], tilt=[28, -34, 22, -30, 36, -24, 30],
             spin=[40, -30, 55, -45, 35, -50, 25])


def place_shards(m, push, lift, tilt, spin, drop=None):
    """Moves each shard bone from its true place: out along its radius (push), along the disc's normal (lift), turned
    about its tangent (tilt) and radius (spin); drop is a world offset. Same maths as the blockout."""
    r_inv = rotation_matrix(SEAL_ROT).T
    for i, (a0, a1, _, _) in enumerate(SEVEN):
        am = math.radians((a0 + a1) / 2)
        u = np.array([math.sin(am), 0.0, math.cos(am)])
        tang = np.array([math.cos(am), 0.0, -math.sin(am)])
        off = u * (push[i] - 0.8) + np.array([0, lift[i], 0])
        if drop is not None:
            off = off + r_inv @ np.array(drop[i], float)
        sg = group(m, f"shard{i}")
        translate(m, sg, off)
        sg.rotation = list(euler(ts.axis_angle(u, spin[i]) @ ts.axis_angle(tang, tilt[i])))


def curl(m, deg, scale=1.0, spin=0.0):
    """The arms: each joint turned about the seal's normal (+ winds tighter), the whole whirl scaled and spun."""
    a = group(m, "arms")
    a.rotation = [0, 0, spin]
    a.scale = [scale, scale, 1]
    for k in range(4):
        for suffix in ("", "_mid", "_end"):
            group(m, f"arm{k}{suffix}").rotation = [0, 0, deg]


def glow_off(m, names):
    for n in names:
        for c in cubes_in(m, group(m, n)):
            c.mat = "recess" if c.mat == "core_glow" else ("stone_dark" if c.mat in ("glyph",) else c.mat)


def pose(m, p):
    hd, fun, tip = group(m, "hi_head"), group(m, "funnel"), group(m, "tip")
    if p == "idle":
        place_shards(m, **BLAST)
    elif p == "locked":
        curl(m, 18, 0.78, 25)
        fun.scale = [0.8, 1.05, 0.8]
        translate(m, tip, (-6, -3, 5))
        hd.rotation = [4, 0, 0]
    elif p == "burst":
        place_shards(m, [v * 1.6 + 6 for v in BLAST["push"]], [v * 1.4 for v in BLAST["lift"]], BLAST["tilt"], BLAST["spin"])
        curl(m, -16, 1.18, -20)
        translate(m, group(m, "arms"), (0, 9, 0))      # the whirl rides up as it opens, clear of the floor
        fun.scale = [1.2, 1.0, 1.2]
        translate(m, tip, (8, 6, -6))
        hd.rotation = [14, 0, 0]
    elif p == "spent":
        place_shards(m, [14, 16, 12, 18, 14, 16, 12], [6, -6, 4, -8, 6, -4, 8], [60, -55, 50, -62, 58, -52, 60],
                     [20, -15, 25, -20, 15, -25, 10], drop=[(0, -120, 0)] * 7)
        curl(m, -28, 0.55, -30)
        translate(m, group(m, "arms"), (0, -10, 0))
        fun.scale = [0.5, 0.6, 0.5]
        translate(m, group(m, "core"), (0, -8, 0))
        translate(m, hd, (0, -10, 0))
        hd.rotation = [-22, 0, 0]
        translate(m, tip, (0, -30, 0))
        glow_off(m, ["glow_heart"] + [f"glow_shard{i}" for i in range(7)])
    elif p == "split":
        # the seal breaks in two: the left half (shards 3-6) swings off to the left, the right (0-2) to the right
        push = [10, 12, 10, 10, 12, 10, 12]
        lift = [6, -4, 4, -6, 4, -4, 6]
        place_shards(m, push, lift, [10, -12, 8, -10, 12, -8, 10], [0] * 7)
        for i in range(7):
            sg = group(m, f"shard{i}")
            side = 1 if i <= 2 else -1
            translate(m, sg, tuple(rotation_matrix(SEAL_ROT).T @ np.array([side * 36.0, -8.0, -4.0])))
        curl(m, -8, 1.15, 40)
        hd.rotation = [10, 0, -12]
    elif p == "death":
        place_shards(m, [8, 10, 6, 12, 8, 10, 6], [4, -4, 2, -6, 4, -2, 6], [80, -75, 70, -85, 78, -72, 82],
                     [10, -10, 15, -15, 10, -15, 5], drop=[(0, -120, 0)] * 7)
        curl(m, -35, 0.4, -60)
        translate(m, group(m, "arms"), (0, -30, 0))
        fun.scale = [0.4, 0.35, 0.4]
        translate(m, group(m, "core"), (0, -44, 0))
        translate(m, hd, (6, -50, -8))
        hd.rotation = [-35, 20, 24]
        translate(m, tip, (0, -40, 0))
        glow_off(m, ["glow_heart"] + [f"glow_shard{i}" for i in range(7)])
    for g in list(m.groups):
        if g.name.startswith("shard") or g.name in ("tip", "funnel", "hi_head", "core"):
            lift_above(g)


POSES = {"idle": "idle: the frozen blast", "locked": "locked: the gust volley", "burst": "burst: the wind burst",
         "spent": "spent: the opening", "split": "split: below half, the gales join", "death": "death"}


# ---- whole texels, hitbox, export -----------------------------------------------------------------------------------------

def snap(m):
    """Whole texels: turned cubes round up so tiles and boards overlap at their joints; straight ones round."""
    for c in m.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, raw = (lo + hi) / 2, hi - lo
        turned = any(abs(a) > 0.01 for a in c.rotation)
        size = np.maximum(1, np.ceil(raw - 0.01) if turned else np.round(raw))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


HITBOX = ((-20.0, 24.0, -20.0), (20.0, 128.0, 20.0))   # the head, the heart and the twister's throat: not shards or arms


def model(p, name=None):
    m = rig(name or f"tempest_{p}")
    snap(m)
    pose(m, p)
    return m


def export():
    from bosses.coven_s2 import _resolve
    out = OUT / "design"
    out.mkdir(parents=True, exist_ok=True)
    m = rig(NAME)
    snap(m)
    _resolve(m, {})
    bb = m.to_bbmodel()
    add_hitbox(bb, *HITBOX)
    (out / f"{NAME}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    geo = sum(1 for g in m.groups if any(not hasattr(c, "children") for c in g.children))
    lo, hi = HITBOX
    stats = dict(m.stats(), bones_with_geometry=geo, hitbox_blocks=[round((b - a) / 16, 2) for a, b in zip(lo, hi)])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text(f"# Tempest blockout parts (session 2)\n\nGenerated by `tools/art/bosses/tempest_s2.py`.\n\n"
                                  f"## {NAME}\n\n{parts_list(m)}\n", encoding="utf-8")
    print(json.dumps(stats))


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 28, "height": 4.2, "dist": 15, "target_z": 4.2},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 15, "target_z": 4.2,
     "player": False},
]
MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 28, "height": 4.2, "dist": 15, "target_z": 4.2},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -24, "height": 1.62, "dist": 12.5, "target_z": 4.2,
     "player": False},
]


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    keys = [a for a in argv if a in POSES]
    if not keys:
        export()
        m = model("idle")
        v2.run_blender(m.render_json(v2.PALETTE), OUT / "main", MAIN_VIEWS)
        img = Image.new("RGB", (12 + 4 * 412, 60 + 320 + 40), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((12, 12), "Tempest, session 2: the design (idle)", font=sheet._font(26), fill=sheet.INK)
        for c, v in enumerate(MAIN_VIEWS):
            img.paste(sheet._tile(OUT / "main" / f"{v['name']}.png", 400, 320), (12 + c * 412, 60))
            dr.text((12 + c * 412, 386), ts.LABELS[v["name"]], font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / "design.png")
    for p in keys or POSES:
        m = model(p)
        lo, hi = m.bounds()
        print(p, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "lowest y", round(float(lo[1]), 1))
        v2.run_blender(m.render_json(v2.PALETTE), OUT / "poses" / p, VIEWS)
    tw, th, pad, top = 330, 290, 8, 56
    img = Image.new("RGB", (pad + 6 * (tw + pad), top + 2 * (th + pad) + 30), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tempest, session 2: the key poses", font=sheet._font(26), fill=sheet.INK)
    for c, p in enumerate(POSES):
        dr.text((pad + c * (tw + pad), top - 2), POSES[p], font=sheet._font(15), fill=sheet.DIM)
        for r, v in enumerate(VIEWS):
            f = OUT / "poses" / p / f"{v['name']}.png"
            if f.exists():
                img.paste(sheet._tile(f, tw, th), (pad + c * (tw + pad), top + 24 + r * (th + pad)))
    img.save(OUT / "poses.png")


if __name__ == "__main__":
    main(sys.argv[1:])
