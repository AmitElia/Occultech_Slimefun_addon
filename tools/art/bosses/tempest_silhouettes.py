"""The Tempest redesign, session 1 step 1: three takes on the Shattered Seal, as cuboid blockouts.

The brief (docs/art/bosses/tempest/overhaul/plan.md, 2026-11-17): the wind was sealed in a carved ritual seal, a stone disc
of glyphs; the summoning cracked it. Vanilla's heavy core is its keystone, glowing at the centre; the shards orbit it on
the wind; vanilla's breeze head above; breeze rods and a twisting vortex below.

The takes differ in how the broken seal is carried:

  A  the Broken Halo     the seal stands upright behind the core, cracked into five shards that drift apart
  B  the Lifted Circle   the seal lies flat round the core's waist like a ritual circle torn off the floor
  C  the Frozen Blast    seven shards thrown far out round the core, frozen mid-explosion

Each is shown idle, locked (the gust volley: the seal snaps back together) and spent (after the burst: the shards drop,
the core is exposed). Model units: 16 = one block, y up, the face towards -z. The blue figure is a player (1.8 blocks).
Colours are blockout zones, not the palette.

Vanilla geometry read from the 26.2 client (BreezeModel): head 8x8x8 with a 10x3x4 visor band 2..5 above its underside,
standing 0.2 proud of the face; rods 2x8x2 tilted 22.5 degrees. The heavy core block is 8x8x8.

Run from the repository root: python tools/art/bosses/tempest_silhouettes.py [A B C]
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
from bosses import volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import euler, plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s1_silhouettes"
PALETTE = {
    "breeze": (171, 156, 203), "breeze_dark": (87, 108, 157), "eye": (243, 245, 255),
    "steel": (94, 101, 111), "steel_dark": (49, 52, 54), "core_glow": (90, 236, 214),
    "stone": (204, 196, 178), "stone_dark": (146, 138, 124), "glyph": (64, 214, 200),
    "wind": (186, 200, 236), "rod": (122, 130, 196),
}
K = 4                  # the breeze head at 4x vanilla
ROD_K = 3              # the rods at 3x
CORE = 24              # the heavy core's edge (vanilla 8 at 3x), stood on a corner like a keystone gem
CORE_Y = 54            # its centre
CORE_TIP = CORE * math.sqrt(3) / 2   # centre to the top corner
CORE_ROT = (35.264, 45, 0)           # a body diagonal straight up
IDLE, LOCKED, SPENT = "idle", "locked", "spent"
POSES = (IDLE, LOCKED, SPENT)


def axis_angle(axis, deg):
    a = np.array(axis, float)
    a /= np.linalg.norm(a)
    t = math.radians(deg)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * k + (1 - math.cos(t)) * k @ k


# ---- the breeze ---------------------------------------------------------------------------------------------------------

def head(g, y, pose):
    """Vanilla's breeze head at K; y = its underside. Spent: bowed forward and sunk."""
    pitch = -22 if pose == SPENT else (6 if pose == LOCKED else 0)
    h = g.group("head", (0, y, 0), (pitch, 0, 0))
    h.box("skull", (0, y + 4 * K, 0), (8 * K, 8 * K, 8 * K), "breeze")
    h.box("visor", (0, y + 3.5 * K, -2.2 * K), (10 * K, 3 * K, 4 * K), "breeze_dark")
    for sx in (-1, 1):   # narrowed, furious: slits on the band
        h.box(f"eye_{sx}", (sx * 2.2 * K, y + 3.6 * K, -4.2 * K - 0.3), (2.4 * K, 0.9 * K, 0.6), "eye", rotation=(0, 0, -sx * 12))


def core(g, pose):
    y = CORE_Y - (8 if pose == SPENT else 0)
    c = g.group("core", (0, y, 0), CORE_ROT)
    c.box("core", (0, y, 0), (CORE, CORE, CORE), "steel")
    c.box("core_band", (0, y, 0), (CORE + 1, 4, CORE + 1), "steel_dark")
    glow = "steel_dark" if pose == SPENT else "core_glow"
    for i, (dx, dz) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        size = (CORE * 0.42, CORE * 0.42, 0.6) if dz else (0.6, CORE * 0.42, CORE * 0.42)
        c.box(f"core_face{i}", (dx * (CORE / 2 + 0.3), y, dz * (CORE / 2 + 0.3)), size, glow)
    return y


def vortex(g, pose, bottom=4.0, top=CORE_Y - 12, r_bot=3.0, r_top=19.0, ribbons=3, turns=1.1, seg=10):
    """The wind body: ribbons on a helix round a cone that opens round the core, each a run of short tilted boards,
    spaced so they read as spiral bands with gaps. Never stacked tiers."""
    if pose == SPENT:
        top, r_top = CORE_Y - 22, 13.0
    for k in range(ribbons):
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = 2 * math.pi * (turns * t + k / ribbons)
            r = r_bot + (r_top - r_bot) * t ** 0.8
            pts.append((r * math.sin(a), bottom + (top - bottom) * t, r * math.cos(a)))
        for i in range(seg):
            h = 4 + 6 * (i / seg)
            plank(g, f"wind{k}_{i}", pts[i], pts[i + 1], h, 1.6, "wind")
    # vanilla's rods, three, tilted 22.5 round the funnel
    for i in range(3):
        a = 120 * i + 30
        r = 11 if pose != SPENT else 8
        ar = math.radians(a)
        g.box(f"rod{i}", (r * math.sin(ar), 26 if pose != SPENT else 18, r * math.cos(ar)), (2 * ROD_K, 8 * ROD_K, 2 * ROD_K), "rod",
              rotation=(22.5, a, 0))


# ---- the seal ---------------------------------------------------------------------------------------------------------

R_IN, R_MID, R_OUT, T = 20.0, 31.0, 44.0, 5.0
STEP = 9.0


def shard_tiles(g, name, a0, a1, j0, j1, ring_glow=True):
    """One shard of the seal, lying flat in x/z round the origin: an inner and an outer row of tiles; the rows end at
    different angles (j0, j1 steps) so every break is jagged. Glyph tiles stand proud on both faces."""
    rows = ((R_IN, R_MID, T, a0 + j0 * STEP, a1 + j1 * STEP, "stone"), (R_MID, R_OUT, T + 1.6, a0, a1, "stone"))
    for r_i, (r1, r2, t, s, e, mat) in enumerate(rows):
        n = max(1, round((e - s) / STEP))
        rm = (r1 + r2) / 2
        for i in range(n):
            a = s + (i + 0.5) * (e - s) / n
            ar = math.radians(a)
            w = 2 * rm * math.tan(math.radians((e - s) / n / 2)) * 1.12
            g.box(f"{name}_r{r_i}_{i}", (rm * math.sin(ar), 0, rm * math.cos(ar)), (w, t, r2 - r1), mat, rotation=(0, a, 0))
        if r_i == 1:   # the rim's lip
            for i in range(n):
                a = s + (i + 0.5) * (e - s) / n
                ar = math.radians(a)
                w = 2 * R_OUT * math.tan(math.radians((e - s) / n / 2)) * 1.12
                g.box(f"{name}_rim_{i}", ((R_OUT - 1.5) * math.sin(ar), 0, (R_OUT - 1.5) * math.cos(ar)), (w, t + 3, 3),
                      "stone_dark", rotation=(0, a, 0))
    if ring_glow:   # the glyph circle between the rows
        for i in range(int((a1 - a0) // STEP)):
            if i % 3 == 2:
                continue
            a = a0 + (i + 0.5) * STEP
            ar = math.radians(a)
            g.box(f"{name}_glyph_{i}", ((R_MID + 4) * math.sin(ar), 0, (R_MID + 4) * math.cos(ar)), (3.2, T + 2.2, 2.2), "glyph",
                  rotation=(0, a, 0))


def seal(g, name, centre, disc_rot, shards, pose, push, normal_lift, tilts, spin=None, drop=None, glow=True):
    """The seal: a disc group (laid flat in rest space, turned by disc_rot) holding one group per shard.
    shards: (a0, a1, j0, j1); push: radial drift; normal_lift: drift along the disc's normal; tilts: about each
    shard's tangent; spin: about its radius; drop: extra world-space offset per shard (turned into rest space)."""
    cx, cy, cz = centre
    d = g.group(name, centre, disc_rot)
    r_inv = rotation_matrix(disc_rot).T
    for i, (a0, a1, j0, j1) in enumerate(shards):
        am = math.radians((a0 + a1) / 2)
        u = np.array([math.sin(am), 0.0, math.cos(am)])
        tang = np.array([math.cos(am), 0.0, -math.sin(am)])
        off = u * push[i] + np.array([0, normal_lift[i], 0])
        if drop is not None:
            off = off + r_inv @ np.array(drop[i], float)
        rot = axis_angle(tang, tilts[i])
        if spin is not None:
            rot = axis_angle(u, spin[i]) @ rot
        mid = u * (R_IN + R_OUT) / 2
        origin = np.array(centre) + mid
        sg = d.group(f"{name}_s{i}", tuple(origin + off), euler(rot))
        before = len(sg.children)
        shard_tiles(sg, f"{name}{i}", a0, a1, j0, j1, ring_glow=glow)
        for c in sg.children[before:]:   # tiles were laid round the origin: move them to the shard's place
            shift = np.array(centre) + off
            c.frm = (np.array(c.frm) + shift).tolist()
            c.to = (np.array(c.to) + shift).tolist()
            c.origin = (np.array(c.origin) + shift).tolist()
    return d


FIVE = ((8, 80, 1, 0), (80, 142, -1, 1), (142, 214, 0, -1), (214, 268, 1, 0), (268, 368, -1, 1))
SEVEN = ((0, 50, 1, 0), (50, 104, 0, -1), (104, 150, -1, 0), (150, 205, 1, 1), (205, 252, 0, -1), (252, 306, 1, 0),
         (306, 360, -1, 1))


def take_a(m, pose):
    """The Broken Halo: upright, behind the core."""
    g = m.group("body", (0, 0, 0))
    vortex(g, pose)
    cy = core(g, pose)
    head(g, cy + CORE_TIP - 4, pose)
    n = len(FIVE)
    if pose == LOCKED:
        push, lift, tilt, drop = [0.8] * n, [0] * n, [0] * n, None
    elif pose == IDLE:
        push, lift, tilt, drop = [5, 7, 4, 6, 9], [2, -3, 3, -2, 1], [8, -10, 6, -12, 10], None
    else:
        push, lift, tilt = [4, 5, 3, 5, 6], [2, -3, 3, -2, 1], [30, -24, 18, -28, 26]
        drop = [(0, -30, 0), (0, -14, 0), (0, -6, 0), (0, -12, 0), (0, -32, 0)]
    seal(g, "seal", (0, CORE_Y, 12), (90, 0, 0), FIVE, pose, push, lift, tilt, drop=drop, glow=pose != SPENT)


def take_b(m, pose):
    """The Lifted Circle: flat round the core's waist."""
    g = m.group("body", (0, 0, 0))
    vortex(g, pose)
    cy = core(g, pose)
    head(g, cy + CORE_TIP - 4, pose)
    n = len(FIVE)
    if pose == LOCKED:
        push, lift, tilt, y = [0.8] * n, [0] * n, [0] * n, CORE_Y
    elif pose == IDLE:
        push, lift, tilt, y = [6, 8, 5, 7, 9], [4, -3, 5, -4, 2], [16, -20, 22, -14, 18], CORE_Y - 6
    else:
        push, lift, tilt, y = [5, 6, 4, 5, 6], [-6, -9, -5, -8, -7], [-34, -30, -38, -28, -36], CORE_Y - 14
    seal(g, "seal", (0, y, 0), (0, 15, 0), FIVE, pose, push, lift, tilt, glow=pose != SPENT)


def take_c(m, pose):
    """The Frozen Blast: seven shards thrown wide; locked = the whole seal snapped back behind it."""
    g = m.group("body", (0, 0, 0))
    vortex(g, pose)
    cy = core(g, pose)
    head(g, cy + CORE_TIP - 4, pose)
    n = len(SEVEN)
    if pose == LOCKED:   # snapped back into a whole seal behind the core
        seal(g, "seal", (0, CORE_Y, 12), (90, 0, 0), SEVEN, pose, [0.8] * n, [0] * n, [0] * n)
        return
    if pose == IDLE:
        push = [18, 22, 16, 24, 19, 23, 17]
        lift = [14, -12, 8, -16, 12, -8, 16]
        tilt = [28, -34, 22, -30, 36, -24, 30]
        spin = [40, -30, 55, -45, 35, -50, 25]
        drop = None
    else:
        push = [14, 16, 12, 18, 14, 16, 12]
        lift = [6, -6, 4, -8, 6, -4, 8]
        tilt = [60, -55, 50, -62, 58, -52, 60]
        spin = [20, -15, 25, -20, 15, -25, 10]
        drop = [(0, -38, 0), (0, -30, 0), (0, -10, 0), (0, -6, 0), (0, -14, 0), (0, -32, 0), (0, -40, 0)]
    seal(g, "seal", (0, CORE_Y, 0), (90, 0, 0), SEVEN, pose, push, lift, tilt, spin=spin, drop=drop, glow=pose != SPENT)


TAKES = {"A": ("The Broken Halo", take_a), "B": ("The Lifted Circle", take_b), "C": ("The Frozen Blast", take_c)}


def build(key, pose):
    title, fn = TAKES[key]
    m = Model(f"tempest_{key}_{pose}")
    fn(m, pose)
    return m, title


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 28, "height": 3.6, "dist": 13, "target_z": 3.4},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -24, "height": 1.62, "dist": 11, "target_z": 3.6,
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
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Tempest {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(POSES):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
