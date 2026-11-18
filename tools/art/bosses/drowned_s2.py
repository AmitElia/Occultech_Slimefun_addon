"""The Drowned Elder redesign, session 2: design lock (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

The approved blockout (drowned_blockout.py: the Wyrm + H3 Spike Hood + S2 Shingle) rebuilt as one rig on whole texels,
`occultech_drowned_elder`. The bind pose is the serpent laid out straight along +z, the face towards -z, the head's centre
at the model origin's x/z, HEAD_Y over the floor:

  base (the head's centre: the carrier; the whole body turns and moves with it)
    hi_head (the elder head, its plates and spikes) > glow_eye, hood0..hood8 (the fan's spikes), web0..web7 (the fin
      between them; each web bone is turned into its own plane in the bind pose so it can widen with one scale axis)
    seg0 (behind the neck) > seg1 > ... > seg9 > tail0 > tail1 > fluke    (the body: a chain, each joint at a segment's
      front, so bending any joint carries everything behind it)
      seg0 > fin_right, fin_left (the pectoral fins)
      seg2, seg4, seg6 > gill<i>_right, gill<i>_left (the side shingles that swing open) and glow_eye<i> (the beam eyes)
    ob_head, ob_body0..ob_body2 (BetterModel hitboxes: the head, and segments 2, 5 and 8, following the body)

Poses are worked out from a curve: each joint takes the turn of the curve at its segment (Spine frames, the same curves as
the blockout), so every pose is joint rotations plus one move of `base`, nothing else.

Key moments (DrownedElder.java): idle (swimming), aim (the multi-beam tell), stare (the Mining Fatigue pulse), dive (the
Tidal Surge going in), emerge (bursting back out, the waves start), death.

Run from the repository root: python tools/art/bosses/drowned_s2.py [pose ...]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2  # noqa: E402
from bosses import drowned_study as st  # noqa: E402
from bosses.archevoker_s2 import cubes_in, group, move, parts_list, translate  # noqa: E402
from bosses.drowned_blockout import SPINES as BLOCKOUT_SPINES, ring, shingle  # noqa: E402
from bosses.drowned_serpent import K, Spine, along, n, spike  # noqa: E402
from bosses.tempest_s2 import snap  # noqa: E402
from bosses.tempest_silhouettes import axis_angle  # noqa: E402
from bosses.tide_silhouettes import euler  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s2_design"
NAME = "occultech_drowned_elder"
PALETTE = dict(st.PAL, hitbox=(235, 70, 70, 70))
HEAD_Y = 40.0                       # the head's centre over the floor in the bind pose
FACE_Z = -8 * K                     # the face; the head's centre is at z = 0
NECK = 16 * K - 2                   # arc length (from the face) where seg0 starts
COUNT = 10
EYES = (2, 4, 6)
UP = np.array([0.0, 1.0, 0.0])
B = np.column_stack([[-1.0, 0, 0], [0, 1.0, 0], [0, 0, -1.0]])   # the Spine frame (right, up, forward) when straight
HOOD_ANGLES = (-100, -75, -50, -25, 0, 25, 50, 75, 100)
SIDE = {"r": "right", "l": "left"}   # bone names spell the side out: a lone r/l could read as a BetterModel tag
HOOD = {"rest": 0.35, "flare": 3.2, "half": 1.4, "tuck": 0.08}


def seg_sizes():
    """(width, length, start arc length) per segment, then where the tail starts."""
    out, s = [], NECK
    for i in range(COUNT):
        t = i / (COUNT - 1)
        w, ln = round(28 - 16 * t), round(26 - 8 * t)
        out.append((w, ln, s))
        s += ln - 2
    return out, s


SEGS, TAIL_S = seg_sizes()
TAIL = [(11, 26), (8, 24)]          # tail0, tail1: (width, length)
FLUKE = 36


def at(s):
    """A bind-pose point at arc length s from the face."""
    return np.array([0.0, HEAD_Y, FACE_Z + s])


# ---- the rig ------------------------------------------------------------------------------------------------------------

def hood_dirs(spread):
    """Base point, direction and length of each hood spike for a spread (in the bind frame)."""
    r, u, f = B.T
    c = at(8 * K)
    out = []
    for th in HOOD_ANGLES:
        t = math.radians(th)
        o = u * math.cos(t) + r * math.sin(t)
        out.append((c - f * 6 * K + o * 7 * K, n(o * spread - f), (23 - 8 * abs(th) / 100) * K))
    return out


def web_frame(a, b):
    """The fin between two hood spikes: its frame (thin, along, across), centre, height and width."""
    (b0, d0, l0), (b1, d1, l1) = a, b
    m0, m1 = b0 + d0 * l0 * 0.38, b1 + d1 * l1 * 0.38
    dm = n(d0 + d1)
    across = m1 - m0
    x = n(np.cross(dm, across))
    F = np.column_stack([x, dm, np.cross(x, dm)])
    return F, (m0 + m1) / 2, (l0 + l1) / 2 * 0.62, float(np.linalg.norm(across)) + 1, (b0 + b1) / 2


def build_head(m, base):
    sp = Spine([tuple(at(0)), tuple(at(600))])
    hd = base.group("hi_head", tuple(at(8 * K)))
    c, F = st.head_core(hd, sp)
    r, u, f = F.T
    st.edge_spikes(hd, c, F, lambda off, d: np.dot(off, f) > -1 and -0.3 < np.dot(d, u) < 0.3)
    eye = next(x for x in hd.children if getattr(x, "name", "") == "eye")
    move(eye, hd.group("glow_eye", tuple(eye.origin)))
    rest = hood_dirs(HOOD["rest"])
    for i, (b, d, length) in enumerate(rest):
        spike(hd.group(f"hood{i}", tuple(b)), f"hood{i}", b, d, length, 2 * K)
    for i in range(len(rest) - 1):
        Fw, centre, h, w, o = web_frame(rest[i], rest[i + 1])
        g = hd.group(f"web{i}", tuple(o), euler(Fw))
        local = o + Fw.T @ (centre - o)          # rest space: as if the bone were not turned
        g.box(f"web{i}", tuple(local), (1.0, h, w), "membrane")


def build_body(m, base):
    parent = base
    for i, (w, ln, s) in enumerate(SEGS):
        seg = parent.group(f"seg{i}", tuple(at(s)))
        sp = Spine([tuple(at(0)), tuple(at(600))])
        eye = "shut" if i in EYES else None
        shingle(seg, sp, s, i, w, ln, eye, 44 - 22 * i / (COUNT - 1))
        if eye:
            c = at(s + ln / 2)
            eyes = [x for x in list(seg.children) if getattr(x, "name", "").startswith(f"seg{i}_eye")]
            ge = seg.group(f"glow_eye{i}", tuple(c))
            for x in eyes:
                x.mat = "glow"
                move(x, ge)
            for side, sx in (("r", -1), ("l", 1)):       # bind right is -x
                sh = next(x for x in seg.children if getattr(x, "name", "") == f"seg{i}_sh{side}")
                hinge = c + np.array([sx * (w / 2 + 1), 0, 0]) + np.array([0, 0, -1.0]) * ln * 0.45
                move(sh, seg.group(f"gill{i}_{SIDE[side]}", tuple(hinge)))
        if i == 0:
            c = at(s + ln / 2)
            for side, sx in (("r", -1), ("l", 1)):
                root = c + np.array([sx * (w / 2 + 2), -4, 0])
                d = n(np.array([sx * 0.55, -0.45, 1.0]))
                fin = seg.group(f"fin_{SIDE[side]}", tuple(root))
                along(fin, f"fin_{side}", root + np.array([sx * 6, 0, 0]) + d * 16, d, (1.2, 36, 22), "fin", thin=UP)
        parent = seg
    # the tail: two tapering pieces and the forked fluke, each its own joint
    s = TAIL_S
    for j, (w, ln) in enumerate(TAIL):
        tg = parent.group(f"tail{j}", tuple(at(s)))
        tg.box(f"tail{j}", tuple(at(s + ln / 2)), (w, w, ln), "hide")
        parent, s = tg, s + ln - 2
    fl = parent.group("fluke", tuple(at(s)))
    tip = at(s)
    for sy in (-1, 1):
        d = n(np.array([0, sy * 0.75, 1.0]))
        along(fl, f"fluke{sy}", tip + d * FLUKE / 2, d, (1.2, FLUKE, FLUKE * 0.34), "fin", thin=(1, 0, 0))
        along(fl, f"fluke{sy}_root", tip + d * FLUKE * 0.22, d, (1.6, FLUKE * 0.45, FLUKE * 0.5), "fin", thin=(1, 0, 0))


HITBOXES = {"ob_head": ("base", 8 * K, (48, 48, 54)), "ob_body0": ("seg2", None, (30, 30, 30)),
            "ob_body1": ("seg5", None, (26, 26, 26)), "ob_body2": ("seg8", None, (20, 20, 22))}


def hitboxes(m):
    for name, (bone, s, size) in HITBOXES.items():
        parent = group(m, bone)
        if s is None:
            i = int(bone[3:])
            s = SEGS[i][2] + SEGS[i][1] / 2
        g = parent.group(name, tuple(at(s)))
        g.box(name, tuple(at(s)), size, "hitbox")


def rig(name):
    m = Model(name)
    base = m.group("base", tuple(at(8 * K)))
    build_head(m, base)
    build_body(m, base)
    hitboxes(m)
    return m


# ---- the poses ------------------------------------------------------------------------------------------------------------

def joints():
    """(bone, parent bone, arc length of the frame it follows), body chain only."""
    out, parent = [], "base"
    for i, (w, ln, s) in enumerate(SEGS):
        out.append((f"seg{i}", parent, s + ln / 2))
        parent = f"seg{i}"
    s = TAIL_S
    for j, (w, ln) in enumerate(TAIL):
        out.append((f"tail{j}", parent, s + ln / 2))
        parent, s = f"tail{j}", s + ln - 2
    out.append(("fluke", parent, s + 6))
    return out


def rot_between(a, b):
    a, b = n(a), n(b)
    axis = np.cross(a, b)
    if np.linalg.norm(axis) < 1e-9:
        return np.eye(3)
    return axis_angle(axis, math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b)))))))


def set_hood(m, spread):
    rest, now = hood_dirs(HOOD["rest"]), hood_dirs(spread)
    for i, ((b, d0, _), (_, d1, _)) in enumerate(zip(rest, now)):
        group(m, f"hood{i}").rotation = list(euler(rot_between(d0, d1)))
    for i in range(len(rest) - 1):
        F0, _, _, w0, _ = web_frame(rest[i], rest[i + 1])
        F1, _, _, w1, _ = web_frame(now[i], now[i + 1])
        g = group(m, f"web{i}")
        g.rotation = list(euler(F1))
        g.scale = [1.0, 1.0, w1 / w0]


def set_gills(m, open_):
    for i in EYES:
        for side, sx in (("r", -1), ("l", 1)):
            out = np.array([sx, 0, 0.0])
            rest = n(np.array([0, 0, 1.0]) * math.cos(math.radians(7)) + out * math.sin(math.radians(7)))
            want = n(np.array([0, 0, 1.0]) * math.cos(math.radians(55)) + out * math.sin(math.radians(55)))
            group(m, f"gill{i}_{SIDE[side]}").rotation = list(euler(rot_between(rest, want))) if open_ else [0, 0, 0]


def bend(m, pts, up0=None):
    """Turns base and every joint so the body follows the curve pts (head first), then moves base onto it. up0: the
    head's up from the frame before (animation), so the roll never flips. Returns the curve."""
    sp = Spine(pts, up0=up0)
    world = {}
    p, F = sp.at(8 * K)
    world["base"] = F @ B.T
    translate(m, group(m, "base"), p - at(8 * K))
    group(m, "base").rotation = list(euler(world["base"]))
    for bone, parent, s in joints():
        _, F = sp.at(s)
        world[bone] = F @ B.T
        group(m, bone).rotation = list(euler(world[parent].T @ world[bone]))
    return sp


def drop_to(m, floor):
    lo = min(float(c.corners()[:, 1].min()) for c in m.cubes if c.mat != "hitbox")
    translate(m, group(m, "base"), (0, floor - lo, 0))


SPINES = dict(BLOCKOUT_SPINES)
SPINES["dive"] = SPINES.pop("surge")
SPINES["emerge"] = [(0, 150, -40), (0, 160, 0), (0, 130, 40), (0, 80, 50), (0, 30, 52), (0, -20, 52), (0, -80, 52),
                    (0, -160, 52), (0, -240, 52), (0, -320, 52)]
SPINES["death"] = [(0, 14, -60), (8, 14, -20)] + ring(20, 14, 30, 64, -150, 200, 14, 14, 10)
FLOOR = {"idle": 20.0, "aim": 20.0, "stare": 36.0, "dive": -8.0, "emerge": None, "death": 0.0}
POSES = {"idle": "idle: swimming", "aim": "aim: the multi-beam tell", "stare": "stare: the pressure pulse",
         "dive": "dive: the surge goes in", "emerge": "emerge: it bursts out, the waves start", "death": "death"}


def pose(m, p):
    set_hood(m, {"stare": HOOD["flare"], "dive": HOOD["tuck"], "emerge": HOOD["half"], "death": HOOD["tuck"]}
             .get(p, HOOD["rest"]))
    set_gills(m, p == "aim")
    bend(m, SPINES[p])
    eye = cubes_in(m, group(m, "glow_eye"))
    for c in eye:
        c.mat = "glow" if p == "stare" else ("lid" if p == "death" else "eye")
    if p == "death":
        for i in EYES:
            for c in cubes_in(m, group(m, f"glow_eye{i}")):
                c.mat = "lid"
    if FLOOR[p] is not None:
        drop_to(m, FLOOR[p])


# ---- export and renders -------------------------------------------------------------------------------------------------

def model(p=None, name=None):
    m = rig(name or f"drowned_{p or 'bind'}")
    snap(m)
    if p:
        pose(m, p)
    return m


def export():
    from bosses.coven_s2 import _resolve
    out = OUT / "design"
    out.mkdir(parents=True, exist_ok=True)
    m = rig(NAME)
    snap(m)
    nudges = {}
    _resolve(m, nudges)
    bb = m.to_bbmodel()
    hit = {c.name for c in m.cubes if c.mat == "hitbox"}
    for e in bb["elements"]:
        if e["name"] in hit:
            e["faces"] = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in e["faces"]}
    (out / f"{NAME}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    shown = [c for c in m.cubes if c.mat != "hitbox"]
    geo = sum(1 for g in m.groups if any(not hasattr(c, "children") and c.mat != "hitbox" for c in g.children))
    lo = np.min([c.corners().min(0) for c in shown], axis=0)
    hi = np.max([c.corners().max(0) for c in shown], axis=0)
    stats = {"cubes": len(shown), "bones": len(m.groups), "bones_with_geometry": geo,
             "size_blocks": [round(float(v) / 16, 2) for v in hi - lo], "flicker_nudges": len(nudges),
             "hitboxes": {k: [round(s / 16, 2) for s in v[2]] for k, v in HITBOXES.items()}}
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text("# Drowned Elder blockout parts (session 2)\n\nGenerated by "
                                  f"`tools/art/bosses/drowned_s2.py`.\n\n## {NAME}\n\n{parts_list(m)}\n", encoding="utf-8")
    print(json.dumps(stats))
    return m


def render_boxes(m, hitbox=False, only=None):
    """Boxes for Blender: no hitboxes unless asked, nothing buried under the floor (the emerge's body below ground is
    never seen in game), and only the cubes of the `only` bones when given."""
    keep = None if only is None else {id(c) for c in m.cubes if c.group.name in only} |         {id(c) for b in only if b.startswith("hi_") for c in cubes_in(m, group(m, b))}
    out = []
    for c, b in zip(m.cubes, m.render_json(v2.PALETTE)):
        if (b["mat"] == "hitbox" and not hitbox) or (keep is not None and id(c) not in keep):
            continue
        if max(p[1] for p in b["corners"]) < -4:
            continue
        out.append(b)
    return out


DESIGN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 32, "height": 6.0, "dist": 22},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top"},
]
HEAD_VIEWS = [{"name": "flat_head", "mode": "flat", "camera": "persp", "yaw": 30, "height": 3.6, "dist": 8.5,
               "player": False}]
HIT_VIEWS = [{"name": "flat_hitbox", "mode": "flat", "camera": "persp", "yaw": 55, "height": 7.0, "dist": 22}]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 7.0, "dist": 22},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -35, "height": 1.62, "dist": 18},
    {"name": "flat_close", "mode": "flat", "camera": "persp", "yaw": 100, "height": 4.0, "dist": 12, "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_side": "side, silhouette", "sil_top": "top, silhouette",
          "flat_head": "the head, close", "flat_hitbox": "hitboxes (red)", "clay_eye": "a player's eye",
          "flat_close": "close, from the right"}


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    keys = [a for a in argv if a in POSES]
    if not keys:
        export()
        m = model("idle")
        v2.run_blender(render_boxes(m), OUT / "main", DESIGN_VIEWS)
        v2.run_blender(render_boxes(m, only=["hi_head", "seg0", "fin_right", "fin_left"]), OUT / "main", HEAD_VIEWS)
        v2.run_blender(render_boxes(m, hitbox=True), OUT / "main", HIT_VIEWS)
        views = DESIGN_VIEWS + HEAD_VIEWS + HIT_VIEWS
        tw, th = 360, 280
        img = Image.new("RGB", (12 + len(views) * (tw + 12), 60 + th + 40), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((12, 12), "Drowned Elder, session 2: the design (idle)", font=sheet._font(26), fill=sheet.INK)
        for c, v in enumerate(views):
            img.paste(sheet._tile(OUT / "main" / f"{v['name']}.png", tw, th), (12 + c * (tw + 12), 60))
            dr.text((12 + c * (tw + 12), 66 + th), LABELS[v["name"]], font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / "design.png")
    for p in keys or POSES:
        m = model(p)
        lo = np.min([c.corners().min(0) for c in m.cubes if c.mat != "hitbox"], axis=0)
        hi = np.max([c.corners().max(0) for c in m.cubes if c.mat != "hitbox"], axis=0)
        print(p, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "lowest y", round(float(lo[1]), 1))
        v2.run_blender(render_boxes(m), OUT / "poses" / p, POSE_VIEWS)
    tw, th, pad, top = 360, 280, 10, 56
    img = Image.new("RGB", (pad + len(POSE_VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Drowned Elder, session 2: the key poses", font=sheet._font(26), fill=sheet.INK)
    for r, p in enumerate(POSES):
        for c, v in enumerate(POSE_VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            f = OUT / "poses" / p / f"{v['name']}.png"
            if f.exists():
                img.paste(sheet._tile(f, tw, th), (x, y))
            dr.text((x, y + th + 6), f"{POSES[p]} ({LABELS[v['name']]})" if c == 0 else LABELS[v["name"]],
                    font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "poses.png")


if __name__ == "__main__":
    main(sys.argv[1:])
