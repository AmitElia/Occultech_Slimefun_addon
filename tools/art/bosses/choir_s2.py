"""The Blaze Choir redesign, session 2: design lock (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

The approved blockout (choir_blockout.py) rebuilt as three rigs, one per singer, on whole texels:
- `occultech_blaze_choir_soprano`: `plate`, `tube0` to `tube7` (pivots at their wires, hanging straight in the bind pose),
  `striker` > `glow_sail`, `glow_wisp`, `hi_head` (the Chime Fringe and spire) > `glow_mouth`.
- `occultech_blaze_choir_alto`: `tower` > `tier0` to `tier2`, `glow_ember`, `cymbal_right`, `cymbal_left`, `hi_head` (the cap)
  > `finger_right`, `finger_left`, `glow_mouth`.
- `occultech_blaze_choir_bass`: `bell` > `clapper` > `glow_clapper`, `glow_wisp`, `hi_head` (the yoke) > `wheel`, `glow_mouth`.

The key moments: idle; strike (a fireball on the beat); shielded (the instrument closes); chorus (the flame circles);
last (the last singer, its instrument failing); death.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s2.py [pose ...] <folder>
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_s2 as a2, choir_blockout as cb, choir_heads as h, choir_silhouettes as cs, volley_crone_s2 as v2  # noqa: E402
from bosses.archevoker_s2 import aim, group, new_bone, translate  # noqa: E402
from bosses.archevoker_silhouettes import vocto  # noqa: E402
from bosses.tide_silhouettes import euler, frame  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s2_design"
PALETTE = {**cs.PALETTE, "mouth": h.HOT}
ID = "occultech_blaze_choir_"
SIDES = {1: "right", -1: "left"}
HEAD = {"soprano": (71, 2), "alto": (56, 3), "bass": (50, 3)}
TOP = 64
TUBES = [(22.5 + 45 * i, 16 + 5 * i) for i in range(8)]
RADIUS = 12
CYMBAL = 25
CYMBAL_REST = (36, 27, 0)
TILE_NAMES = ("f", "r", "l", "t")
HITBOX = {"soprano": ((-12.0, 8.0, -12.0), (12.0, 88.0, 12.0)),
          "alto": ((-58.0, 2.0, -12.0), (58.0, 80.0, 12.0)),
          "bass": ((-26.0, 4.0, -26.0), (26.0, 74.0, 26.0))}


def is_tile(name):
    return len(name) == 3 and name[0] in TILE_NAMES and name[1:].isdigit()


def add_head(root, singer, preview):
    y, k = HEAD[singer]
    g = root.group("hi_head", (0, y, 0))
    if preview:
        h.textured_head("vanilla")(g, 0, y, k)
    else:
        g.box("head", (0, y + 4 * k, 0), (8 * k, 8 * k, 8 * k), "blaze")
    m = g.group("glow_mouth", (0, y + 2 * k, -4 * k))
    m.box("mouth", (0, y + 2 * k, -4 * k - 0.25), (2 * k, 2 * k, 1), "mouth")
    return g, y, k


def glow(m, parent, name, origin, cubes_from):
    own = [c for c in cubes_from.children if not hasattr(c, "children") and c.name.startswith(name.split("_", 1)[1])]
    return new_bone(m, parent, name, origin, own)


def soprano_rig(name, preview):
    m = Model(name)
    root = m.group("base", (0, TOP, 0))
    hd, y, k = add_head(root, "soprano", preview)
    h.chime_fringe(hd, 0, y + 4)
    cs.flame(root, "wisp", 0, TOP + 3.5, 6, "white_fire")
    glow(m, root, "glow_wisp", (0, TOP + 3.5, 0), root)
    pl = root.group("plate", (0, TOP, 0))
    vocto(pl, "plate", (0, TOP, 0), 30, 3, 30, "brass", cham=0.29)
    vocto(pl, "plate_cap", (0, TOP + 2, 0), 16, 2, 16, "brass_dark", cham=0.29)
    for i, (a, length) in enumerate(TUBES):
        ar = math.radians(a)
        x, z = round(RADIUS * math.sin(ar)), round(RADIUS * math.cos(ar))
        t = root.group(f"tube{i}", (x, TOP - 1, z))
        t.box(f"wire{i}", (x, TOP - 2.5, z), (1, 4, 1), "brass_dark")
        end = TOP - 4
        if length > 46:                                    # one item-model cube stops at 48 units
            up = round(length / 2)
            t.box(f"pipe{i}", (x, end - up / 2, z), (4, up, 4), "brass")
            t.box(f"pipe{i}_low", (x, end - up - (length - up) / 2, z), (4, length - up, 4), "brass")
        else:
            t.box(f"pipe{i}", (x, end - length / 2, z), (4, length, 4), "brass")
        t.box(f"band{i}", (x, end - 1, z), (5, 1, 5), "brass_dark")
        t.box(f"foot{i}", (x, end - length - 0.5, z), (2, 1, 2), "brass_dark")
    st = root.group("striker", (0, TOP - 1, 0))
    st.box("striker_rod", (0, TOP - 22, 0), (1, 42, 1), "brass_dark")
    vocto(st, "striker_disc", (0, TOP - 28, 0), 12, 2, 12, "brass", cham=0.29)
    s = st.group("glow_sail", (0, 22, 0))
    cs.flame(s, "sail", 0, 16, 13, "white_fire")
    return m


def alto_rig(name, preview):
    m = Model(name)
    root = m.group("base", (0, 33, 0))
    hd, y, k = add_head(root, "alto", preview)
    h.finger_cymbals(hd, (0, y + 4 * k, 15))
    group(m, "finger_1").name, group(m, "finger_-1").name = "finger_right", "finger_left"
    t = root.group("tower", (0, 33, 0))
    t.box("spindle", (0, 33, 0), (3, 40, 3), "brass_dark")
    for i, (yy, r) in enumerate(((50, 13), (37, 10), (25, 7))):
        cs.dish(t, f"tier{i}", (0, yy, 0), (0, 1, 0), r, "brass", across=(0, 0, 1))
    cs.flame(root, "ember", 0, 13, 10, "fire")
    glow(m, root, "glow_ember", (0, 13, 0), root)
    for sx, side in SIDES.items():
        c = (sx * CYMBAL_REST[0], CYMBAL_REST[1], CYMBAL_REST[2])
        d = cs.dish(root, f"cymbal_{side}", c, (0, 1, 0), CYMBAL, "brass", across=(0, 0, 1), boss="brass_dark")
        d.box(f"tassel_{side}", (c[0], c[1] + CYMBAL * 0.13 + 2.5, 0), (2, 4, 2), "cord")
    return m


def bass_rig(name, preview):
    m = Model(name)
    root = m.group("base", (0, 44, 0))
    hd, y, k = add_head(root, "bass", preview)
    cb._pose = "idle"
    cb.bell_wheel(hd, 0, y + 8 * k, k)
    keep_head, keep_crown = cs.head, cs.spiked_crown
    cs.head, cs.spiked_crown = (lambda *a: None), (lambda *a: None)
    cs.bell(root, 0, "idle")
    cs.head, cs.spiked_crown = keep_head, keep_crown
    glow(m, root, "glow_wisp", (0, 45, 0), root)
    cl = group(m, "clapper")
    glow(m, cl, "glow_clapper", (0, 7, 0), cl)
    return m


RIGS = {"soprano": soprano_rig, "alto": alto_rig, "bass": bass_rig}


# ---- the poses -----------------------------------------------------------------------------------------------------

def pose_soprano(m, p):
    swing = {"idle": lambda i: 0.0, "strike": lambda i: 20.0, "shielded": lambda i: -13.0, "chorus": lambda i: 34.0,
             "last": lambda i: (9, 44, 2, 30, 52, 14, 38, 5)[i], "death": lambda i: 62.0 + (i % 3) * 7}[p]
    for i, (a, _) in enumerate(TUBES):
        ar, t = math.radians(a), math.tan(math.radians(swing(i)))
        aim(group(m, f"tube{i}"), (math.sin(ar) * t, -1, math.cos(ar) * t))
    hd, base = group(m, "hi_head"), group(m, "base")
    if p == "strike":
        hd.rotation = [12, 0, 0]
    elif p == "shielded":
        translate(m, hd, (0, -4, 0))
        hd.rotation = [-8, 0, 0]
    elif p == "chorus":
        translate(m, hd, (0, 5, 0))
        hd.rotation = [24, 0, 0]
        translate(m, group(m, "glow_sail"), (0, 10, 0))
    elif p == "last":
        translate(m, hd, (0, 3, 0))
        hd.rotation = [16, 0, -9]
        aim(group(m, "striker"), (0.28, -1, 0))
    elif p == "death":
        translate(m, base, (0, -22, 0))
        hd.rotation = [-26, 0, 22]


CYMBAL_POSES = {   # side +1: centre, the way its dome points; the left mirrors unless given
    "idle": ((36, 27, 0), (.5, 0, .87)),
    "strike": ((5, 42, -40), (1, 0, 0)),
    "shielded": ((19, 38, 0), (1, 0, 0)),
    "chorus": ((36, 78, 0), (.8, .2, .57)),
    "death": ((30, 5, -6), (.12, 1, .1)),
}


def set_cymbal(m, side, sx, centre, apex):
    d = group(m, f"cymbal_{side}")
    translate(m, d, (centre[0] - d.origin[0], centre[1] - d.origin[1], centre[2] - d.origin[2]))
    apex = np.array(apex, float)
    across = (0, 0, 1) if abs(apex[2]) < 0.9 else (0, 1, 0)
    d.rotation = list(euler(frame(np.cross(across, apex), apex)))


def pose_alto(m, p):
    for sx, side in SIDES.items():
        if p == "last":
            c, a = ((36, 44, 0), (.5, 0, .87)) if sx == -1 else ((39, 26, 8), (.3, -.25, .9))
        else:
            c, a = CYMBAL_POSES[p]
        set_cymbal(m, side, sx, (sx * c[0], c[1], c[2]), (sx * a[0], a[1], a[2]))
    hd = group(m, "hi_head")
    if p == "strike":
        hd.rotation = [10, 0, 0]
    elif p == "shielded":
        translate(m, hd, (0, -3, 0))
        hd.rotation = [-8, 0, 0]
    elif p == "chorus":
        translate(m, hd, (0, 4, 0))
        hd.rotation = [22, 0, 0]
    elif p == "last":
        hd.rotation = [14, 0, 10]
    elif p == "death":
        translate(m, hd, (0, -34, 0))
        hd.rotation = [-20, 0, -24]
        translate(m, group(m, "tower"), (0, -16, 0))
        translate(m, group(m, "glow_ember"), (0, -16, 0))


def pose_bass(m, p):
    bell, cl, wheel, hd = (group(m, n) for n in ("bell", "clapper", "wheel", "hi_head"))
    swing, clap, turn = {"idle": (0, 0, 0), "strike": (20, -36, -24), "shielded": (0, 0, 0), "chorus": (38, -52, -52),
                         "last": (-16, 26, 40), "death": (24, -30, 60)}[p]
    bell.rotation, cl.rotation, wheel.rotation = [0, 0, swing], [0, 0, clap], [0, 0, turn]
    if p == "strike":
        hd.rotation = [10, 0, 0]
    elif p == "shielded":
        translate(m, wheel, (0, 0, -37))
        translate(m, hd, (0, -3, 0))
        hd.rotation = [-6, 0, 0]
    elif p == "chorus":
        hd.rotation = [20, 0, 0]
        translate(m, hd, (0, 3, 0))
    elif p == "last":
        hd.rotation = [14, 0, -8]
        translate(m, wheel, (0, -6, 0))
    elif p == "death":
        translate(m, bell, (0, -12, 0))
        translate(m, group(m, "glow_wisp"), (0, -14, 0))
        translate(m, wheel, (10, -30, 12))
        translate(m, hd, (0, -14, 0))
        hd.rotation = [-20, 0, 24]


POSE = {"soprano": pose_soprano, "alto": pose_alto, "bass": pose_bass}
POSES = {"idle": "idle", "strike": "strike: a fireball on the beat", "shielded": "shielded: the instrument closes",
         "chorus": "chorus: the flame circles", "last": "the last singer: its instrument failing", "death": "death"}


def snap(m):
    """Whole texels. Tilted panels round up so their joints overlap; the head's preview tiles are left alone."""
    for c in m.cubes:
        if is_tile(c.name):
            continue
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, raw = (lo + hi) / 2, hi - lo
        turned = any(abs(a) > 0.01 for a in c.rotation)
        size = np.maximum(1, np.ceil(raw - 0.01) if turned else np.round(raw))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


def model(singer, pose, preview=True):
    m = RIGS[singer](f"{ID}{singer}" if not preview else f"{singer}_{pose}", preview)
    POSE[singer](m, pose)
    snap(m)
    return m


def export():
    from bosses.coven_s2 import _resolve
    out = OUT / "design"
    out.mkdir(parents=True, exist_ok=True)
    stats, parts = {}, ["# The Blaze Choir blockout parts (session 2)\n\nGenerated by `tools/art/bosses/choir_s2.py`.\n"]
    for singer in RIGS:
        m = model(singer, "idle", preview=False)
        _resolve(m, {})
        bb = m.to_bbmodel()
        lo, hi = HITBOX[singer]
        add_hitbox(bb, lo, hi)
        (out / f"{ID}{singer}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        geo = sum(1 for g in m.groups if any(not hasattr(c, "children") for c in g.children))
        stats[singer] = dict(m.stats(), bones_with_geometry=geo, hitbox_blocks=[round((b - a) / 16, 2) for a, b in zip(lo, hi)])
        parts += [f"## {ID}{singer}\n", a2.parts_list(m), ""]
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text("\n".join(parts), encoding="utf-8")
    print(json.dumps(stats))


VIEW = [{"name": "q", "mode": "flat", "camera": "persp", "yaw": -30, "height": 2.8, "dist": 11.5, "target_z": 3.0}]


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    keys = [a for a in argv if a in POSES]
    if not keys:
        export()
    for singer in RIGS:
        for pose in keys or POSES:
            m = model(singer, pose)
            lo, _ = m.bounds()
            print(singer, pose, "lowest y", round(float(lo[1]), 1))
            v2.run_blender(m.render_json(v2.PALETTE), OUT / "poses" / singer / pose, VIEW)
    tw, th, pad, top = 320, 290, 8, 56
    img = Image.new("RGB", (pad + 6 * (tw + pad), top + 3 * (th + pad) + 30), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Blaze Choir: the key poses", font=sheet._font(26), fill=sheet.INK)
    for c, p in enumerate(POSES):
        dr.text((pad + c * (tw + pad), top - 2), POSES[p], font=sheet._font(15), fill=sheet.DIM)
        for r, singer in enumerate(RIGS):
            f = OUT / "poses" / singer / p / "q.png"
            if f.exists():
                img.paste(sheet._tile(f, tw, th), (pad + c * (tw + pad), top + 24 + r * (th + pad)))
    img.save(OUT / "poses.png")


if __name__ == "__main__":
    main(sys.argv[1:])
