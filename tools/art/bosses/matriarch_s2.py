"""The Night Matriarch redesign, session 2: design lock.

The approved blockout (matriarch_s1.py, take 2) rebuilt as a rig:
- every part on a named bone (BetterModel names): `body`, `hi_head` (the head, turning with its children), the crown's
  bones, both wings in two parts (`wing_*`, `wing_*_tip`), the `tail` with its owl's fan;
- the glow on its own bones, drawn full-bright: `glow_eye` (her green eye and the sculk light in the empty socket),
  `glow_tendrils` (the tips of the sensor tendrils on her back) and one bone per sculk gill, `glow_gill_<side>_<n>`,
  so each gill can flick on its own like an axolotl's;
- every gill is one flat plane, like vanilla's axolotl gills and warden horns: its frond is cut out of the texture
  (session 5). The renders here draw that frond (a stalk with filaments) in place of the plane;
- every cube snapped to whole texels; every turned cube turned on one axis by 22.5 or 45 degrees, so it costs no extra
  display: the finger bones are snapped to those angles, and the crown's bones sit on four bones raked back 22.5, 45,
  67.5 and 90 degrees, each bone leaning out only in its own frame;
- the hitbox (`ob_hitbox`): her body, head and the inner wing panels, not the outer wings, tail or crown;
- the fight's key poses.

Run from the repository root: python tools/art/bosses/matriarch_s2.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import matriarch_s1 as s1, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402
from bosses.unbound_s2 import euler  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s2_design"
PALETTE = dict(s1.PALETTE, hitbox=(220, 60, 60), hole=(14, 12, 18))
U, L, W, H, FRONT = s1.U, s1.L, s1.W, s1.H, s1.FRONT
HL, HW, HH, ZF = s1.HL, s1.HW, s1.HH, s1.ZF
LIFT = H / 2 + 3                                # the rig stands with her belly just off the floor
CHORD = 9 * U


def group(model, name):
    return next(g for g in model.groups if g.name == name)


def bake(model, target):
    """Folds every bone under `target` into it: each cube keeps its place and turn (its turn becomes the cube's own)."""
    inv = np.linalg.inv(target.world_matrix())
    for sub in [g for g in model.groups if g is not target and _under(g, target)]:
        for c in [c for c in sub.children if not hasattr(c, "children")]:
            m = inv @ c.group.world_matrix() @ np.array(_pivot(c))
            centre = (m @ np.array([*((np.array(c.frm) + np.array(c.to)) / 2), 1.0]))[:3]
            half = (np.array(c.to) - np.array(c.frm)) / 2
            c.frm, c.to = (centre - half).tolist(), (centre + half).tolist()
            c.rotation = [round(a, 3) + 0.0 for a in euler(m[:3, :3])]
            c.origin = centre.tolist()
            sub.children.remove(c)
            target.children.append(c)
            c.group = target
    for sub in [g for g in model.groups if g is not target and _under(g, target)]:
        sub.parent.children.remove(sub)
        model.groups.remove(sub)


def _under(g, target):
    p = g.parent
    while p is not None:
        if p is target:
            return True
        p = p.parent
    return False


def _pivot(c):
    from bosskit.bbmodel import pivot_matrix
    return pivot_matrix(c.origin, c.rotation)


# ---- the head --------------------------------------------------------------------------------------------------------

CROWN_PIVOT = (0, HH / 2, ZF + 5)
# The crown (take 2 of the blockout's crown, back to the scarier take-2 study at the user's request): jagged bone shards
# broken out through her brow, tallest in the middle, fanning out and raked back like a crown; the big ones have a
# narrower point and a spur. (x, z from the face, height, rake back, lean out, width, spur)
CROWN = ((0, 2.0, 18, 22.5, 0, 3.6, True),
         (-6.5, 2.8, 13, 22.5, 22.5, 3.2, True), (6.5, 2.8, 13, 22.5, -22.5, 3.2, True),
         (-12, 4.5, 8, 45, 45, 2.8, False), (12, 4.5, 8, 45, -45, 2.8, False),
         (-3.2, 8.0, 7, 45, 22.5, 2.4, False), (3.2, 8.5, 6, 45, -22.5, 2.4, False),
         (-9, 9.5, 5, 45, 45, 2.2, False), (9, 9.5, 5, 45, -45, 2.2, False))


def crown(head):
    """Each shard goes on the crown bone raked back as far as it is (22.5 or 45 degrees); inside that bone it only
    leans out (a turn about z, by 22.5 or 45), so no cube is turned on two axes."""
    bones = {}
    p = np.array(CROWN_PIVOT, float)

    def put(name, base, length, width, rake, lean):
        if rake not in bones:
            bones[rake] = head.group(f"crown_{int(rake * 10)}", tuple(p), (rake, 0, 0))
        R = rotation_matrix((rake, 0, 0)) @ rotation_matrix((0, 0, lean))
        centre = base + R @ np.array([0, length / 2, 0])
        local = rotation_matrix((rake, 0, 0)).T @ (centre - p) + p
        bones[rake].box(name, tuple(local), (width, length, width), "bone", rotation=(0, 0, lean))
        return base + R @ np.array([0, length, 0])

    for i, (x, z, h, rake, lean, width, spur) in enumerate(CROWN):
        base = np.array([x, HH / 2 - 0.5, ZF + z], float)
        top = put(f"crown_{i}", base, h * 0.72, width, rake, lean)
        put(f"crown_{i}_point", top - (rotation_matrix((rake, 0, 0)) @ rotation_matrix((0, 0, lean)))
            @ np.array([0, 0.5, 0]), h * 0.32, width * 0.55, rake, lean)
        if spur:                                         # a shorter shard split off its base, leaning further out
            out = lean + (22.5 if x <= 0 else -22.5)
            put(f"crown_{i}_spur", base + np.array([0, 0, 1.2]), h * 0.42, width * 0.6, rake, out)


GILLS = ((5, 45, 14, 7), (0.5, 0, 17, 8), (-4, -45, 12, 6))      # (height, fan, length, width)


def gills(head, preview):
    for sx in (-1, 1):
        word = "left" if sx < 0 else "right"
        for i, (y, fan, length, width) in enumerate(GILLS):
            name = f"glow_gill_{word}_{i}"
            base = (sx * (HW / 2 - 0.5), y, ZF + HL - 7 + i)
            g = head.group(name, base, (0, -sx * 22.5, sx * fan))
            x0 = base[0] + sx * length / 2
            if not preview:
                g.box(f"gill_{word}_{i}_plane", (x0, y, base[2]), (length, width, 0), "sculk")
                continue
            # what the cut-out will show: a glowing stalk, filaments along both edges
            g.box(f"gill_{word}_{i}_stalk", (x0, y, base[2]), (length, 1.6, 0.4), "sculk_glow")
            for k in range(int(length // 4)):
                reach = 1.4 + 1.6 * (1 - abs(k - length / 8) / (length / 8))
                g.box(f"gill_{word}_{i}_f{k}", (base[0] + sx * (3 + k * 4), y, base[2]), (1.2, 1.6 + 2 * reach, 0.4),
                      "sculk")


def head_parts(head, preview):
    zc = FRONT - HL / 2
    head.box("head", (HW / 4, 0, zc), (HW / 2, HH, HL), "hide")
    head.box("skull", (-HW / 4 + 0.5, -0.5, zc + 0.5), (HW / 2 - 1, HH - 1, HL - 1), "bone")
    for i, (y, h, d) in enumerate(((4, 4, 5), (-1, 6, 3), (-4.5, 3, 6))):
        head.box(f"hide_tatter_{i}", (-1.2, y, ZF + d / 2 + 0.6), (2.4, h, d), "hide")
    # a menacing face: a heavy brow pressed down in a V (inner ends low); the phantom's long green eye slanting the same
    # way, sunk in a dark pit; on the skull side a deep empty socket under a bare brow ridge, a sculk light far inside
    head.box("brow_right", (7.8, 4.2, ZF - 0.4), (15, 3.4, 3.6), "hide_dark", rotation=(0, 0, 22.5))
    head.box("brow_left", (-7.8, 4.0, ZF - 0.1), (15, 3, 3.2), "bone", rotation=(0, 0, -22.5))
    head.box("eye_pit", (8.6, 0.6, ZF + 0.15), (11, 4.6, 0.6), "hole", rotation=(0, 0, 22.5))
    head.box("socket_left", (-8.6, 0.4, ZF + 0.9), (9, 6.5, 1.6), "hole")
    head.box("nose_pit", (0, -2.2, ZF + 0.2), (3, 3.5, 0.6), "hole")
    head.box("cheekbone_left", (-11, -3.4, ZF + 0.2), (7, 2, 2), "bone")
    eye = head.group("glow_eye", (9, 1, ZF))
    eye.box("eye_right", (8.6, 0.6, ZF - 0.3), (9, 2.2, 0.6), "eye", rotation=(0, 0, 22.5))
    eye.box("socket_light", (-8.6, 0.4, ZF + 0.5), (1.6, 1.6, 0.6), "sculk_glow")
    crown(head)
    gills(head, preview)


# ---- the wings: take 2's torn shape, the finger bones snapped to 22.5 and 45 degrees ------------------------------------

INNER = {1: [(9, 40), (9, 34), (9, 38)], -1: [(9, 39), (9, 26), (9, 37)]}
OUTER = {1: [(8, 36), (8, 24), (7, 15), (8, 31), (7, 16), (7, 11), (6, 6), (7.5, 7)],
         -1: [(8, 33), (8, 20), (7, 28), (8, 18), (7, 10), (7, 22), (6, 9), (7.5, 5)]}
FINGERS_INNER = ((0, 45, 34),)                                       # (start along the spar, angle back, length)
FINGERS_OUTER = ((0, 45, 38), (0, 22.5, 44), (30, 45, 24))


def finger(g, name, start, angle, length, sx):
    d = np.array([sx * math.cos(math.radians(angle)), 0, math.sin(math.radians(angle))])
    centre = np.array(start) + d * length / 2
    g.box(name, tuple(centre), (length, 2, 2), "bone", rotation=(0, -sx * angle, 0))


def wing(body, sx):
    word = "left" if sx < 0 else "right"
    x0, y0, z0 = sx * W / 2, 3.0, FRONT + 2
    g = body.group(f"wing_{word}", (x0, y0, z0))
    span = 0.0
    for part, (length, spar, strips, fingers) in enumerate(((6 * U, 4, INNER[sx], FINGERS_INNER),
                                                            (13 * U, 3, OUTER[sx], FINGERS_OUTER))):
        if part == 1:
            g = g.group(f"wing_{word}_tip", (x0 + sx * span, y0, z0))
        g.box(f"wing_{word}_{part}_spar", (x0 + sx * (span + length / 2), y0 + 0.5, z0 + spar / 2 - 0.5),
              (length, spar, spar), "bone")
        x = span
        for j, (w, c) in enumerate(strips):
            g.box(f"wing_{word}_{part}_m{j}", (x0 + sx * (x + w / 2), y0, z0 + c / 2), (w, 1, c),
                  "membrane" if j % 2 else "membrane_dark")
            x += w
        for k, (start, angle, length_f) in enumerate(fingers):
            finger(g, f"wing_{word}_{part}_finger{k}", (x0 + sx * (span + start), y0 + 0.9, z0 + 1), angle, length_f, sx)
        span += length


# ---- the rig ---------------------------------------------------------------------------------------------------------

# sculk sensor tufts across her back: (x, z, size)
TUFTS = ((5, -14, 7), (-6, -9, 6), (8.5, -3, 6), (-4, 2, 7), (6, 8, 6), (-8, 12, 5), (3, 16, 6), (9.5, 14, 5),
         (-2, -16, 5))
BELLY_TUFTS = ((5, -12, 6), (-3, -4, 5), (7, 4, 6), (1, 12, 5), (-6, 15, 5), (9, -18, 4))


def build(name, preview=False):
    model = Model(name)
    body = model.group("body", (0, 0, 0))
    s1.body_parts(body)
    for c in [c for c in body.children if not hasattr(c, "children") and c.name.startswith("tendril")]:
        body.children.remove(c)                         # the blockout's box tendrils: replaced by the tufts below
        model.cubes.remove(c)
    tufts = body.group("glow_tendrils", (TUFTS[0][0], H / 2, TUFTS[0][1]))
    for i, (x, z, size) in enumerate(TUFTS):
        # sculk sensor tendrils growing out of her back: two crossed planes, the tendrils cut out of the texture
        tufts.box(f"sensor_{i}_a", (x, H / 2 + size / 2, z), (size, size, 0), "sculk")
        tufts.box(f"sensor_{i}_b", (x, H / 2 + size / 2, z), (0, size, size), "sculk")
    for i, (x, z, size) in enumerate(BELLY_TUFTS):
        # and hanging from her belly, where players look up at her
        y = -H / 2 - 1.5 - size / 2
        tufts.box(f"sensor_h{i}_a", (x, y, z), (size, size, 0), "sculk")
        tufts.box(f"sensor_h{i}_b", (x, y, z), (0, size, size), "sculk")
    head = body.group("hi_head", (0, 0, FRONT))
    head_parts(head, preview)
    tail = body.group("tail", (0, 0, L / 2))
    s1.tail_parts(tail)
    bake(model, tail)
    for sx in (-1, 1):
        wing(body, sx)
    translate(model, (0, LIFT, 0))
    return model


def translate(model, d):
    for g in model.groups:
        g.origin = [g.origin[i] + d[i] for i in range(3)]
    for c in model.cubes:
        c.frm = [c.frm[i] + d[i] for i in range(3)]
        c.to = [c.to[i] + d[i] for i in range(3)]
        c.origin = [c.origin[i] + d[i] for i in range(3)]


_NUDGES = None


def finish(model):
    """Whole-texel sizes, flat cut-out planes, and the flicker fix: no two faces share a plane (they z-fight in game).
    The smaller part of each clash moves a fraction of a texel off the plane (the Witch Coven's resolver); the nudges
    are found once in the rest pose and kept per cube, so every pose gets the same model, and sizes don't change, so
    the texture layout doesn't either."""
    global _NUDGES
    _finish_base(model)
    if _NUDGES is None:
        _NUDGES = {}
        rest = build("nudge_rest")
        _finish_base(rest)
        from bosses.coven_s2 import _resolve
        nudges = {}
        _resolve(rest, nudges)
        _NUDGES = nudges
    by_name = {c.name: c for c in model.cubes}
    for name, d in _NUDGES.items():
        if name in by_name:
            c = by_name[name]
            c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]


def _finish_base(model):
    """Whole-texel sizes; the cut-out planes stay flat (snapping makes every size at least 1): the gills and the
    tufts' first planes across z, the tufts' second planes across x."""
    v2.snap(model)
    for c in model.cubes:
        flat = 2 if c.name.endswith("_plane") or (c.name.startswith("sensor_") and c.name.endswith("_a")) else \
            0 if c.name.startswith("sensor_") and c.name.endswith("_b") else None
        if flat is not None:
            lo, hi = np.array(c.frm), np.array(c.to)
            mid = (lo[flat] + hi[flat]) / 2
            lo[flat] = hi[flat] = mid
            c.frm, c.to = lo.tolist(), hi.tolist()


def hitbox_bounds(model):
    """Her body, head and inner wing panels; not the outer wings, the tail, the crown or the gills."""
    keep = [c for c in model.cubes if c.group.name in ("body", "hi_head") or c.group.name in ("wing_left", "wing_right")]
    pts = np.vstack([c.corners() for c in keep])
    lo, hi = pts.min(0), pts.max(0)
    half = float(np.ceil(max(-lo[0], hi[0])))
    return (-half, float(np.floor(lo[1])), float(np.floor(lo[2]))), (half, float(np.ceil(hi[1])), float(np.ceil(hi[2])))


# ---- poses -----------------------------------------------------------------------------------------------------------
# body: (pitch, yaw, roll); head and tail: pitch; wing: per side (shoulder, elbow) as functions of sx; gill: an extra
# turn on every gill bone (sx -> rotation); altitude: the lowest point (model units)

POSES = {
    "glide": ("circling: banking over the arena", {
        "body": (4, 0, 16), "head": -6, "tail": -4, "alt": 150,
        "wing": lambda sx: ((0, 0, sx * 8), (0, 0, sx * 4))}),
    "tell": ("the dive's tell (1.5 s): she rears, wings raised high, head down at her target, gills flared", {
        "body": (22, 0, 0), "head": -28, "tail": 14, "alt": 140,
        "wing": lambda sx: ((0, sx * 10, sx * 50), (0, 0, sx * 25)), "gill": lambda sx: (0, sx * 22.5, 0)}),
    "dive": ("the dive: nose down, wings swept back, gills streaming", {
        "body": (-40, 0, 0), "head": -6, "tail": 12, "alt": 80,
        "wing": lambda sx: ((0, -sx * 60, sx * 14), (0, -sx * 28, sx * 6)), "gill": lambda sx: (0, -sx * 22.5, 0)}),
    "impact": ("the impact: slammed into the floor, wings flung forward", {
        "body": (8, 0, 0), "head": -20, "tail": 20, "alt": 0,
        "wing": lambda sx: ((0, sx * 30, -sx * 4), (0, sx * 20, -sx * 14))}),
    "grounded": ("stunned on the floor (1.5 s): sprawled, wings limp, gills drooping", {
        "body": (0, 0, 6), "head": -14, "tail": -2, "alt": 0,
        "wing": lambda sx: ((0, 0, -sx * 6), (0, 0, -sx * 10)), "gill": lambda sx: (0, 0, -sx * 22.5)}),
    "takeoff": ("taking off again: a great downbeat, nose up", {
        "body": (28, 0, 0), "head": 8, "tail": 18, "alt": 16,
        "wing": lambda sx: ((0, 0, -sx * 30), (0, 0, -sx * 20))}),
    "call": ("calling the swarm: head thrown up, wings spread wide, gills flared", {
        "body": (10, 0, 0), "head": 32, "tail": -8, "alt": 150,
        "wing": lambda sx: ((0, sx * 8, sx * 22), (0, 0, sx * 12)), "gill": lambda sx: (0, sx * 22.5, 0)}),
    "death": ("death: crashed on her side, one wing folded over her", {
        "body": (0, 0, 28), "head": -24, "tail": -6, "alt": 0,
        "wing": lambda sx: ((0, sx * 15, sx * 172), (0, 0, sx * 25)) if sx < 0 else ((0, 0, -sx * 4), (0, 0, -sx * 18)),
        "gill": lambda sx: (0, 0, -sx * 22.5)}),
}


def pose(model, spec):
    def add(g, r):
        g.rotation = [g.rotation[i] + r[i] for i in range(3)]
    add(group(model, "body"), spec["body"])
    add(group(model, "hi_head"), (spec["head"], 0, 0))
    add(group(model, "tail"), (spec["tail"], 0, 0))
    for sx in (-1, 1):
        word = "left" if sx < 0 else "right"
        shoulder, elbow = spec["wing"](sx)
        add(group(model, f"wing_{word}"), shoulder)
        add(group(model, f"wing_{word}_tip"), elbow)
        if "gill" in spec:
            for i in range(len(GILLS)):
                add(group(model, f"glow_gill_{word}_{i}"), spec["gill"](sx))
    lo, _ = model.bounds()
    translate(model, (0, spec["alt"] - float(lo[1]), 0))


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(sorted({c.mat for c in cubes}))} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


def view_set(alt):
    a = alt / 16
    return [{"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": a + 4, "dist": 14,
             "target_z": a + 0.6, "player": alt == 0},
            {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False}]


DESIGN_VIEWS = [
    {"name": "flat_below", "mode": "flat", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 8, "target_z": 9.6,
     "lens": 30},
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 14, "dist": 13, "target_z": 9.3},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top", "player": False},
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": 25, "height": 10.4, "dist": 6.5, "target_z": 9.9,
     "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    rest = build("occultech_night_matriarch_blockout")
    finish(rest)
    frm, to = hitbox_bounds(rest)
    bb = rest.to_bbmodel()
    add_hitbox(bb, frm, to)
    (OUT / "occultech_night_matriarch_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    total, per_bone = v3.display_count(rest)
    stats = dict(rest.stats(), displays=total, hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(frm, to)])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text("# The Night Matriarch's parts (session 2)\n\nGenerated by "
                                  "`tools/art/bosses/matriarch_s2.py`. Cube sizes are whole texels.\n\n"
                                  + parts_list(rest) + "\n", encoding="utf-8")
    # the design views: gliding at 9 blocks, the gills drawn as their fronds
    glide = build("glide", preview=True)
    finish(glide)
    pose(glide, POSES["glide"][1])
    v2.run_blender(glide.render_json(v2.PALETTE), OUT / "design", DESIGN_VIEWS)
    # the hitbox, a red box over the rest pose
    boxes = rest.render_json(v2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
    boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
    v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                           {"name": "hitbox_top", "mode": "flat", "camera": "ortho_top"}])
    # the key poses
    for key, (_, spec) in POSES.items():
        posed = build(key, preview=True)
        finish(posed)
        pose(posed, spec)
        v2.run_blender(posed.render_json(v2.PALETTE), OUT / "poses" / key, view_set(spec["alt"]))
    sheets(stats)
    print(json.dumps({k: stats[k] for k in ("cubes", "bones_with_geometry", "displays", "size_blocks", "hitbox_blocks")}))
    print(per_bone)


def sheets(stats):
    tw, th, pad, top = 460, 350, 12, 60
    font, small = sheet._font(26), sheet._font(17)
    # design: four views and the hitbox
    cells = [(OUT / "design" / "flat_below.png", "gliding, from below (a player's eye)"),
             (OUT / "design" / "flat_34.png", "gliding, three-quarter"),
             (OUT / "design" / "sil_top.png", "from above"),
             (OUT / "design" / "face.png", "her head"),
             (OUT / "hitbox" / "hitbox_front.png", "the hitbox (red), front"),
             (OUT / "hitbox" / "hitbox_top.png", "the hitbox (red), from above")]
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Night Matriarch - design lock (session 2): {stats['cubes']} cubes, {stats['displays']} displays",
            font=font, fill=sheet.INK)
    for k, (path, label) in enumerate(cells):
        x, y = pad + (k % 3) * (tw + pad), top + (k // 3) * (th + 34 + pad)
        img.paste(sheet._tile(path, tw, th), (x, y))
        dr.text((x, y + th + 6), label, font=small, fill=sheet.DIM)
    img.save(OUT / "design.png")
    # poses: two per row, three-quarter and side
    keys = list(POSES)
    for n, chunk in enumerate((keys[:4], keys[4:])):
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), "Night Matriarch - key poses (" + ", ".join(chunk) + ")", font=font, fill=sheet.INK)
        for k, key in enumerate(chunk):
            for v, view in enumerate(("flat_34", "sil_side")):
                x, y = pad + ((k % 2) * 2 + v) * (tw + pad), top + (k // 2) * (th + 34 + pad)
                img.paste(sheet._tile(OUT / "poses" / key / f"{view}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{key}: {'three-quarter' if v == 0 else 'side'}", font=small, fill=sheet.DIM)
        img.save(OUT / f"poses_{n + 1}.png")


if __name__ == "__main__":
    main()
