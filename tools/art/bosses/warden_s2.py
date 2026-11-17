"""The Abyssal Warden redesign, session 2: design lock (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

The approved blockout (warden_s1.py) rebuilt as a rig, at its final size, every cube snapped to whole texels:
- one model, `occultech_abyssal_warden`. The 33% hand is part of it, hidden until the side window bursts (BetterModel
  part visibility), so it needs no second carrier.
- the bones (BetterModel names): `base` (everything, its pivot on the ground: the float, the rest's sink, the death),
  `body` (the bowed helmet: the hull, the windows' frames and bolts, the sclera; it pivots at the sphere's centre),
  `glow_iris` (the iris and glint, slid round the window to look) with `pupil` (scaled to narrow and flare), the four
  `valve*` (they jump out at the spike burst), `spray` (the jets from the valves, hidden), `window_r_glass` (the right
  side window's glass and grille, until 33%), `window_r_burst` (its shards, bent bars, squeezed flesh: from 33%),
  the hose as `hose1`..`hose4` (the lash), the growth as `growth`, `tendrils_even`, `tendrils_odd` and `kelp` (they
  sway against each other), and the arm as `arm`, `forearm`, `hand` (hidden until 33%), straight out of the window in
  the bind pose and aimed per pose;
- the windows' own groups are baked into `body`: a bone per window would cost displays for nothing;
- the hitbox (`ob_hitbox`): the helmet's sphere only; the hose, the growth and the hand stay outside it;
- the flicker fix (no two faces on one plane), found in the bind pose and kept for every pose;
- the fight's key poses, posed from the rig, as renders for the design (not animation).

Units are model pixels (16 = one block). The window faces -z; his right is +x.

Run from the repository root: python tools/art/bosses/warden_s2.py [pose ...]
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox, pivot_matrix, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, warden_silhouettes as w1, warden_take2 as t2  # noqa: E402
from bosses import warden_window as ww, warden_s1 as s1  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s2_design"
PALETTE = dict(s1.PALETTE, hitbox=(220, 60, 60), spray=(226, 246, 250, 190))
C = np.array(t2.C, float)
R = t2.R
SIDE = t2.SIDE / np.linalg.norm(t2.SIDE)
SHOULDER = C + SIDE * (R - 8)                   # inside the right side window, in the body's (bowed) space
UPPER, FORE = 42, 40                            # the arm's lengths
NECK = np.array((0, C[1] - R * 0.74, 2))       # where the growth hangs from
LEGAL = (0.0, 22.5, -22.5, 45.0, -45.0)
BAKE_ALL_GROUPS = True      # session 3 keeps the side windows (and the hull's columns) as their own bones


# ---- rig helpers ---------------------------------------------------------------------------------------------------

def group(m, name):
    return next(g for g in m.groups if g.name == name)


def subtree(g):
    out = [g]
    for ch in g.children:
        if hasattr(ch, "children"):
            out += subtree(ch)
    return out


def cubes_in(m, g):
    gs = set(map(id, subtree(g)))
    return [c for c in m.cubes if id(c.group) in gs]


def euler(rm):
    """Blockbench's rotation (x, y, z in degrees, R = Rz Ry Rx) for a rotation matrix."""
    b = -math.asin(max(-1.0, min(1.0, rm[2, 0])))
    a = math.atan2(rm[2, 1], rm[2, 2])
    c = math.atan2(rm[1, 0], rm[0, 0])
    return [round(math.degrees(v), 4) + 0.0 for v in (a, b, c)]


def rehome(c, g):
    """Moves a cube onto another bone, keeping it where it is in the bind pose (the old bone's turn is baked into it)."""
    old = c.group.world_matrix() @ pivot_matrix(c.origin, c.rotation)
    new_o = np.linalg.solve(g.world_matrix(), c.group.world_matrix() @ np.array([*c.origin, 1.0]))[:3]
    rot = np.linalg.solve(g.world_matrix()[:3, :3], old[:3, :3])
    d = new_o - np.array(c.origin)
    c.frm, c.to = (np.array(c.frm) + d).tolist(), (np.array(c.to) + d).tolist()
    c.origin, c.rotation = new_o.tolist(), euler(rot)
    c.group.children.remove(c)
    g.children.append(c)
    c.group = g


def drop_group(m, g):
    g.parent.children.remove(g)
    m.groups.remove(g)


def translate(m, g, d):
    for x in subtree(g):
        x.origin = [x.origin[i] + d[i] for i in range(3)]
    for c in cubes_in(m, g):
        c.frm = [c.frm[i] + d[i] for i in range(3)]
        c.to = [c.to[i] + d[i] for i in range(3)]
        c.origin = [c.origin[i] + d[i] for i in range(3)]


def align(a, b):
    """The smallest rotation turning direction a onto direction b."""
    a, b = (np.array(v, float) / np.linalg.norm(v) for v in (a, b))
    v, cos = np.cross(a, b), float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if cos > 0 else rotation_matrix((0, 180, 0))
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1 / (1 + cos))


def basis(f, n):
    n = np.array(n, float) / np.linalg.norm(n)
    f = np.array(f, float) - n * np.dot(f, n)
    f /= np.linalg.norm(f)
    return np.column_stack([np.cross(f, n), f, n])


# ---- the rig ---------------------------------------------------------------------------------------------------------

# the arm's bind pose: straight out of the window, palm down, fingers pointing away from him
BIND_ELBOW = SHOULDER + SIDE * UPPER
BIND_WRIST = BIND_ELBOW + SIDE * FORE
BIND_PALM, BIND_FINGERS = (0, -1.0, 0), SIDE

ARM = re.compile(r"^hand_(upper|elbow)")
FORE_ = re.compile(r"^hand_fore")
BURST = re.compile(r"^(burst_shard|bent_bar|squeeze)")


def spray(g):
    """The jets of spray out of the four valves at the spike burst: three widening puffs along each valve."""
    for i, d in enumerate(VALVES):
        d = np.array(d, float) / np.linalg.norm(d)
        for k, (o, w, l) in enumerate(((10, 4, 7), (17, 7, 8), (25, 10, 9))):
            a, b = w1.on_sphere(C, R, d, o - l / 2), w1.on_sphere(C, R, d, o + l / 2)
            w1.beam(g, f"spray{i}_{k}", a, b, w, "spray")


VALVES = ((1, 0.7, 0.5), (-1, 0.7, 0.5), (1, -0.3, 0.8), (-1, -0.3, 0.8))     # as in take 2


def rig(name):
    saved = (w1.window, t2.limb, t2.mutated_hand, ww.veins)
    m = s1.build(name, "idle")
    bowed = group(m, "bowed")
    # the arm in its bind pose, and the burst window's wreckage (both hidden until 33%), built like the blockout's
    w1.window, t2.limb, t2.mutated_hand, ww.veins = saved[0], s1.infected_limb, s1.infected_hand, s1.no_veins
    try:
        s1.infected_hand(bowed, "hand", SHOULDER, BIND_ELBOW, BIND_WRIST, BIND_PALM, BIND_FINGERS)
    finally:
        w1.window, t2.limb, t2.mutated_hand, ww.veins = saved
    ww.burst(bowed)
    spray(bowed)

    root = group(m, "root")
    root.name = "base"
    bowed.name = "body"
    body = bowed
    # the windows' groups baked into the body
    for g in [g for g in list(m.groups) if g.parent is body and (BAKE_ALL_GROUPS or g.name == "window")]:
        for c in cubes_in(m, g):
            rehome(c, body)
        drop_group(m, g)

    def bone(name, origin, test, parent=body, visible=True, source=None):
        g = parent.group(name, tuple(map(float, origin)))
        g.visible = visible
        src = source or parent
        for c in [c for c in cubes_in(m, src) if c.group is src and test(c.name)]:
            rehome(c, g)
        return g

    iris = bone("glow_iris", C, lambda n: n in ("iris", "iris_inner", "glint") or n.startswith(("iris_", "glint")))
    pupil_c = next(c for c in m.cubes if c.name == "pupil")
    bone("pupil", (np.array(pupil_c.frm) + pupil_c.to) / 2, lambda n: n == "pupil", parent=body)
    p = group(m, "pupil")
    p.parent.children.remove(p)
    iris.children.append(p)
    p.parent = iris
    for i, d in enumerate(VALVES):
        bone(f"valve{i}", w1.on_sphere(C, R, d, 0), lambda n, i=i: n.startswith(f"valve{i}_"))
    bone("spray", C, lambda n: n.startswith("spray"), visible=False)
    side_r = body if BAKE_ALL_GROUPS else group(m, "side_r")
    bone("window_r_glass", C + SIDE * math.sqrt(R * R - 64),
         lambda n: n.startswith(("side_r_glass", "side_r_bar")), parent=side_r)
    bone("window_r_burst", C + SIDE * math.sqrt(R * R - 64), lambda n: bool(BURST.match(n)), parent=side_r,
         visible=False, source=body)
    hose_pts = [w1.on_sphere(C, R, (0, 0.55, 1), 2), (0, 70, 50), (0, 52, 72), (0, 38, 88)]
    parent = body
    for k in range(4):
        test = (lambda n, k=k: n in (f"hose_{k}", f"hose_band{k}") or (k == 3 and n == "hose_nozzle"))
        parent = bone(f"hose{k + 1}", hose_pts[k], test, parent=body)
        if k:
            parent.parent.children.remove(parent)
            prev = group(m, f"hose{k}")
            prev.children.append(parent)
            parent.parent = prev
    growth = bone("growth", NECK, lambda n: n.startswith("mass"))
    bone("tendrils_even", NECK, lambda n: re.match(r"tendril\d+_", n) and int(re.match(r"tendril(\d+)", n)[1]) % 2 == 0,
         parent=body)
    bone("tendrils_odd", NECK, lambda n: n.startswith("tendril"), parent=body)
    bone("kelp", NECK, lambda n: n.startswith("kelp"), parent=body)
    for nm in ("tendrils_even", "tendrils_odd", "kelp"):
        g = group(m, nm)
        g.parent.children.remove(g)
        growth.children.append(g)
        g.parent = growth
    arm = bone("arm", SHOULDER, lambda n: bool(ARM.match(n)), visible=False)
    fore = bone("forearm", BIND_ELBOW, lambda n: bool(FORE_.match(n)), visible=False)
    hand = bone("hand", BIND_WRIST, lambda n: n.startswith("hand_"), visible=False)
    for child, par in ((fore, arm), (hand, fore)):
        child.parent.children.remove(child)
        par.children.append(child)
        child.parent = par
    for g in (fore, hand):
        g.visible = False
    names = [c.name for c in m.cubes]
    assert len(names) == len(set(names)), "cube names must be unique (the flicker fix finds cubes by name)"
    return m


# ---- the poses -------------------------------------------------------------------------------------------------------
#   body: the helmet's turn on top of its 12-degree bow (pitch negative = the window tips further down); base: (dx, dy,
#   dz) for the whole model; look: where the iris sits in the window, (x, y) as a share of its radius (+x his right);
#   pupil: its width as a share (narrow < 1 < flared); valves: how far they jump out; spray: True shows the jets;
#   hose: (yaw, pitch) per segment; growth: (x, z) sway of the tendrils and the kelp, opposite ways;
#   arm: None (hidden, the window intact) or (elbow, wrist, palm, fingers) in the body's space; burst: the window
#   burst (with arm None: the moment after)

POSES = {
    "idle": ("idle: gliding, the eye looking ahead, the hose trailing", {}),
    "beam": ("the beam's tell: the eye locked on its target, the pupil narrowed to a thread", {
        "body": (-6, 14, 0), "look": (0.35, -0.2), "pupil": 0.35}),
    "lash": ("the lash: the hose whipped round at anyone close", {
        "body": (4, -14, 6), "hose": ((0, 38, 0), (0, 34, 0), (0, 30, 0), (0, 20, 0)), "growth": (5, -3),
        "look": (0.4, 0.1)}),
    "spikes": ("the spike burst: the valves blow out in jets of spray", {
        "body": (6, 0, 0), "valves": 3, "spray": True, "pupil": 1.6, "look": (0, 0.05)}),
    "rest": ("the rest: sunk and venting, the eye drooping", {
        "body": (-14, 0, 8), "base": (0, -3, 0), "look": (-0.1, -0.45), "pupil": 1.3, "growth": (0, 3),
        "hose": ((0, 0, -10), (0, 0, -12), (0, 0, -8), (0, 0, 0))}),
    "burst": ("33%: the side window bursts and the hand claws its way out", {
        "body": (0, -12, -10), "burst": True,
        "arm": ((58, 74, 12), (58, 98, -10), (-0.8, -0.2, -0.5), (0, 0.9, -0.4)), "look": (0.45, 0), "pupil": 1.5}),
    "raised": ("the smash's wind-up: the hand over a player, the eye still on another", {
        "burst": True, "arm": ((64, 66, -2), (74, 84, -26), (-0.1, -0.7, -0.7), (-0.1, 0.6, -0.8)),
        "look": (-0.3, -0.1), "pupil": 0.5}),
    "slam": ("the slam: the hand flat on the floor, left down as the opening", {
        "body": (-4, 0, 0), "burst": True,
        "arm": ((72, 36, -12), (78, 0, -44), (0, -0.98, 0.2), (-0.15, -0.2, -1)), "look": (0.4, -0.5)}),
    "death": ("death: the hull caves in and sinks, the eye rolled up", {
        "body": (-26, 10, 18), "base": (0, -4, 0), "burst": True, "look": (0, 0.55), "pupil": 0.6,
        "arm": ((60, 40, 8), (70, 18, -10), (0, -1, 0.1), (0.3, -0.1, -1)), "growth": (-4, 2),
        "hose": ((0, 0, -18), (0, -10, -16), (0, -14, -12), (0, 0, 0))}),
}


def pose(m, spec):
    body = group(m, "body")
    turn = spec.get("body", (0, 0, 0))
    body.rotation = [12 + turn[0], turn[1], turn[2]]
    if spec.get("base"):
        translate(m, group(m, "base"), spec["base"])
    lx, ly = spec.get("look", (0.2, -0.1))
    rw = 16
    iris = group(m, "glow_iris")
    translate(m, iris, (lx * rw - 0.2 * rw, ly * rw + 0.1 * rw, 0))   # the blockout's iris sits at (0.2, -0.1)
    p = next(c for c in m.cubes if c.name == "pupil")
    if spec.get("pupil"):                                    # the renders only: in game the pupil bone is scaled
        w = (p.to[0] - p.frm[0]) * spec["pupil"]
        cx = (p.frm[0] + p.to[0]) / 2
        p.frm[0], p.to[0] = cx - w / 2, cx + w / 2
    for i, d in enumerate(VALVES):
        d = np.array(d, float) / np.linalg.norm(d)
        translate(m, group(m, f"valve{i}"), d * spec.get("valves", 0))
    for k, rot in enumerate(spec.get("hose", ())):
        group(m, f"hose{k + 1}").rotation = list(map(float, rot))
    sx, sz = spec.get("growth", (0, 0))
    group(m, "tendrils_even").rotation = [sz * 2.0, 0, -sx * 2.0]
    group(m, "tendrils_odd").rotation = [-sz * 1.5, 0, sx * 1.5]
    group(m, "kelp").rotation = [sz * 3.0, 0, -sx * 3.0]
    if spec.get("arm"):
        elbow, wrist, palm, fingers = (np.array(v, float) for v in spec["arm"])
        arm, fore, hand = group(m, "arm"), group(m, "forearm"), group(m, "hand")
        r1 = align(SIDE, elbow - SHOULDER)
        arm.rotation = euler(r1)
        r2 = align(SIDE, r1.T @ (wrist - elbow))
        fore.rotation = euler(r2)
        bind = basis(BIND_FINGERS, BIND_PALM)
        target = basis(fingers, palm)
        hand.rotation = euler((r1 @ r2).T @ target @ bind.T)


def shown(m, spec):
    """The cubes a pose shows: the hidden bones only when the pose calls for them."""
    hide = set()
    if not spec.get("spray"):
        hide.add("spray")
    if spec.get("burst"):
        hide.add("window_r_glass")
    else:
        hide.add("window_r_burst")
    if not spec.get("arm"):
        hide.update(("arm", "forearm", "hand"))
    gone = set()
    for nm in hide:
        gone |= set(map(id, cubes_in(m, group(m, nm))))
    return [c for c in m.cubes if id(c) not in gone]


# ---- snap, flicker fix, hitbox ---------------------------------------------------------------------------------------

def snap(m):
    """Whole-texel sizes. The hull's panels and the frames round up, so their joints overlap instead of opening."""
    for c in m.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, raw = (lo + hi) / 2, hi - lo
        up = c.name.startswith(("hull", "window_frame", "side_l_frame", "side_r_frame", "neck_ring"))
        size = np.maximum(1, np.ceil(raw - 0.01) if up else np.round(raw))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


_NUDGES = None


def finish(m):
    global _NUDGES
    snap(m)
    if _NUDGES is None:
        bind = rig("nudge_bind")
        snap(bind)
        from bosses.coven_s2 import _resolve
        _NUDGES = {}
        _resolve(bind, _NUDGES)
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES.items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]


HITBOX = ((-34.0, 22.0, -34.0), (34.0, 90.0, 34.0))   # the sphere (the bow turns it about its own centre)


def displays(m):
    """BetterModel's cost: a display per bone with cubes, plus one per other cube turn its item model can't keep."""
    out = {}
    for g in m.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if not cubes:
            continue
        turns = set()
        for c in cubes:
            r = [round(v, 2) for v in c.rotation]
            axes = [v for v in r if abs(v) > 1e-6]
            if not axes or (len(axes) == 1 and any(abs((axes[0] % 90) - (v % 90)) < 1e-3 for v in LEGAL)):
                continue
            turns.add(tuple(r))
        out[g.name] = 1 + len(turns)
    return out


def parts_list(m):
    rows = []
    for g in m.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None else "-"
            rows.append(f"| `{g.name}` | {parent} | {'yes' if g.visible else 'hidden'} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | At spawn | Cubes | Materials |", "|---|---|---|---|---|"] + rows)


# ---- renders ---------------------------------------------------------------------------------------------------------

MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.8, "dist": 15, "target_z": 3.9},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 14, "target_z": 3.8,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -35, "height": 3.8, "dist": 15, "target_z": 3.9,
     "player": False},
]
POSE_VIEWS = [                                   # yaw 40 is from his right: the side the hand comes out of
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.8, "dist": 16, "target_z": 3.9,
     "player": False},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 15, "target_z": 3.8,
     "player": False},
]


def build(key):
    m = rig(f"occultech_abyssal_warden_{key}")
    finish(m)
    pose(m, POSES[key][1])
    return m


def render(m, spec, palette=None):
    pal = palette or v2.PALETTE
    keep = set(map(id, shown(m, spec)))
    return [b for c, b in zip(m.cubes, m.render_json(pal)) if id(c) in keep]


def side_by_side(paths, out):
    ims = [Image.open(p) for p in paths]
    img = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) - 1), max(i.height for i in ims)), sheet.BG)
    x = 0
    for i in ims:
        img.paste(i, (x, 0))
        x += i.width + 10
    img.save(out)


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    if not only:
        for old in OUT.rglob("*"):                           # files only: an open folder can't be removed
            if old.is_file() and old.name != "README.md":
                old.unlink()
        bind = rig("occultech_abyssal_warden")
        finish(bind)
        bb = bind.to_bbmodel()
        add_hitbox(bb, *HITBOX)
        (OUT / "design").mkdir(exist_ok=True)
        (OUT / "design" / "occultech_abyssal_warden_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n",
                                                                                   encoding="utf-8")
        from bosskit.checks import flicker_pairs
        cost = displays(bind)
        stats = dict(bind.stats(), bones_with_geometry=len(cost), displays_estimate=sum(cost.values()),
                     displays_by_bone=cost, flicker_pairs=len(flicker_pairs(bind.cubes)),
                     hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(*HITBOX)])
        idle = build("idle")
        lo = min(float(c.corners()[:, 1].min()) for c in shown(idle, {}))
        stats["idle_lowest_point"] = round(lo, 1)
        stats["idle_cubes_shown"] = len(shown(idle, {}))
        (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        (OUT / "parts.md").write_text(
            "# The Abyssal Warden blockout parts (session 2)\n\nGenerated by `tools/art/bosses/warden_s2.py`. Cube "
            "sizes are whole texels. Hidden bones are shown by the fight (part visibility).\n\n" + parts_list(bind) + "\n",
            encoding="utf-8")
        print(json.dumps(stats))
        v2.run_blender(render(idle, {}), OUT / "design", MAIN_VIEWS)
        sheet.compare_sheet(OUT, [("design", "the design lock")], OUT / "design.png",
                            heading="The Abyssal Warden - design lock (session 2)",
                            views=("flat_34", "flat_front", "sil_side", "clay_34"))
        boxes = render(idle, {}, PALETTE)
        for bx in boxes:
            bx["color"] = [c * 0.55 + 0.4 for c in bx["color"]]
        boxes.append(dict(v2.box_json("hitbox", *HITBOX, "hitbox"), alpha=0.35))
        v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                               {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
        side_by_side([OUT / "hitbox" / f"hitbox_{v}.png" for v in ("front", "side")], OUT / "hitbox.png")
    for key in (only or POSES):
        m = build(key)
        spec = POSES[key][1]
        lo = min(float(c.corners()[:, 1].min()) for c in shown(m, spec))
        hand_lo = min((float(c.corners()[:, 1].min()) for c in cubes_in(m, group(m, "hand"))), default=None)
        print(key, "lowest", round(lo, 1), "hand lowest", round(hand_lo, 1) if spec.get("arm") else "-")
        v2.run_blender(render(m, spec), OUT / "poses" / key, POSE_VIEWS)
    keys = list(POSES)
    if all((OUT / "poses" / k / "flat_34.png").exists() for k in keys):
        for i, chunk in enumerate((keys[:5], keys[5:])):
            sheet.compare_sheet(OUT / "poses", [(k, "") for k in chunk], OUT / f"poses_{i + 1}.png",
                                heading="The Abyssal Warden - the key poses", views=("flat_34", "flat_front"))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
