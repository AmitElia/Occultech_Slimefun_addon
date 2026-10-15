"""The Elder of Ash, session 3: rig and pose test (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

The session 2 design lock drew as 173 display entities: BetterModel gives a cube its own display unless it is turned
on one axis by 0, 22.5 or 45 degrees, and the volcano's slabs (two-axis turns) and the lava's streams (any angle) were
almost all different. This session rebuilds those parts on legal angles, keeping the look:
- the body: an octagon seen from the front, its slopes at 45 degrees; the neck and the rump slope at 45 too;
- the volcano: one 22.5-degree cone from the body's top to the rim (45 below it, on the body: still concave), in
  colour bands from skin through ash to basalt. Each ring has eight slabs: four facing front, back and the sides on
  the `volcano` bone, four on `volcano_45`, a bone turned 45 degrees, so in its own frame those face square on too;
- the lava: flat strips lying on the slabs and slopes, each turned like the face it lies on (`glow_lava` and
  `glow_lava_45`); the streams' wiggle goes into the texture;
- the brows: each brow is a bone turned at F3's angle, its tufts snapped to 22.5-degree steps inside it;
- the pipe: a bone turned outwards, the stem tilted 22.5 down inside it;
- fingers and toes at 0, 22.5 and 45 degrees.

Then, as for the other bosses:
- a pivot check (every bone's pivot in its joint) and a BetterModel tag check;
- a display count;
- a flat colour per material, so he can be seen in game before texturing (the eyes, the lava, the crater and the
  pipe's ember full-bright);
- the seven key poses saved as BetterModel animations (`/bm test occultech_elder_of_ash_rig <pose>`).

Output: docs/art/bosses/elder_of_ash/overhaul/s3_rig/, plus the review model copied into run/plugins/BetterModel/models.
It is never shipped.

Run from the repository root: python tools/art/bosses/ash_s3.py
"""
import base64
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import ash_face as f1, ash_face2 as f2, ash_s1 as s1, ash_s2 as s2  # noqa: E402
from bosses import volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_elder_of_ash_rig"
GLOWING = ("eye", "lava", "ember", "tongue_tip")
INTENDED_TAGS = {"hi_head": {"hi"}, "glow_eye": {"glow"}, "glow_crater": {"glow"}, "glow_lava": {"glow"},
                 "glow_lava_45": {"glow"}, "glow_pipe": {"glow"}, "ob_hitbox": {"ob"}}
T225 = math.tan(math.radians(22.5))

CZ = 12                       # the volcano's axis (z) and the body's middle front to back
TOP = 50                      # the body's flat top, where the cone starts
CONE_R0, RIM_R = 30, 9
CONE_TOP = TOP + (CONE_R0 - RIM_R) / T225          # 22.5 degrees all the way: about 100.7
s1.CONE_Z, s1.CONE_TOP = CZ, CONE_TOP               # the face and markings code reads these


# ---- faces: a box lying on a sloped face, in one of the four square-on directions -------------------------------------

FACING = {"right": ("z", 1, (1, 0)), "left": ("z", -1, (-1, 0)), "front": ("x", 1, (0, -1)), "back": ("x", -1, (0, 1))}


def snap_angle(a):
    return min((0.0, 22.5, -22.5, 45.0, -45.0), key=lambda v: abs(v - a))


def face_box(g, name, facing, a, b, thick, lateral, mat, centre=(0.0, CZ), out=False, along=0.0):
    """A box whose outer face (or, with out=True, whose inner face) lies on the line from a to b, given as (u, y): u is
    the distance out from the centre in that direction. The line must slope at a legal angle (0, 22.5, 45). lateral is
    the box's width across the face; along shifts it sideways along the face."""
    (u0, y0), (u1, y1) = (a, b) if a[1] <= b[1] else (b, a)
    du, dv = u1 - u0, y1 - y0
    ln = math.hypot(du, dv)
    theta = snap_angle(math.degrees(math.atan2(-du, dv)))
    nu, nv = dv / ln, -du / ln                           # the outward normal in (u, y)
    s = 0.5 if out else -0.5
    cu, cv = (u0 + u1) / 2 + nu * thick * s, (y0 + y1) / 2 + nv * thick * s
    axis, sign, (dx, dz) = FACING[facing]
    cx0, cz0 = centre
    if axis == "z":
        pos = (cx0 + dx * cu, cv, cz0 + along)
        g.box(name, pos, (thick, ln, lateral), mat, rotation=(0, 0, sign * theta))
    else:
        pos = (cx0 + along, cv, cz0 + dz * cu)
        g.box(name, pos, (lateral, ln, thick), mat, rotation=(sign * theta, 0, 0))


# ---- the body ----------------------------------------------------------------------------------------------------------

def body(root):
    """Seen from the front an octagon: the belly tucked under at 45 degrees, the flanks upright, the back sloping in at
    45 degrees to a flat top 60 wide, where the cone grows. The neck rises at 45 from behind the head, and the rump
    slopes and tucks down behind, also at 45."""
    b = root.group("body", (0, 24, CZ))
    b.box("core", (0, 27, CZ), (60, 46, 60), "skin")                    # y 4..50, the top under the cone
    b.box("mid", (0, 23, CZ + 2), (92, 22, 72), "flank")                # the flanks: x +-46, y 12..34
    b.box("belly", (0, 8, CZ + 2), (80, 8, 64), "belly")
    b.box("chest", (0, 15, -22.6), (58, 18, 1.4), "belly")
    b.box("rump_wall", (0, 27, CZ + 36), (80, 30, 4), "flank")          # the rump's back: z 46..50
    for side in ("right", "left"):
        face_box(b, f"slope_{side}", side, (46, 34), (30, 50), 10, 68, "skin", centre=(0, CZ), along=2)
        face_box(b, f"tuck_{side}", side, (40, 6), (46, 12), 7, 62, "flank", along=2)
    face_box(b, "rump_slope", "back", (38, 42), (30, 50), 10, 60, "skin", centre=(0, CZ), out=False)
    face_box(b, "rump_tuck", "back", (32, 6), (38, 12), 6, 76, "flank")
    face_box(b, "neck_slope", "front", (42, 38), (30, 50), 12, 56, "skin")
    for i, (x, y, z, s) in enumerate(((-46.2, 22, -12, 6), (46.2, 18, 14, 7), (-46.2, 26, 26, 5), (46.2, 26, -14, 5))):
        b.box(f"wart{i}", (x + (0.8 if x > 0 else -0.8), y, z), (1.6, s, s), "wart")
    return b


# ---- the volcano -------------------------------------------------------------------------------------------------------

BANDS = (("skin_ash", 0.0, 6.0), ("ash", 6.0, 12.0), ("ash_dark", 12.0, 18.0), ("basalt", 18.0, CONE_TOP - TOP))


def cone_u(y):
    return CONE_R0 - (y - TOP) * T225


def cone_half(v, tag):
    """One half of the cone, square on in this bone's frame: front, back and the two sides of every colour band, the
    rim's teeth, a core, and rocks (hardened warts) round its foot."""
    for mat, h0, h1 in BANDS:
        y0, y1 = TOP + h0, TOP + h1
        u0 = cone_u(y0)
        width = 2 * math.pi * u0 / 8 * 1.12
        for facing in FACING:
            face_box(v, f"cone{tag}_{mat}_{facing}", facing, (u0, y0), (cone_u(y1), y1), 8, width,
                     "basalt_lit" if (mat == "basalt" and facing == "front" and tag == "") else mat)
    for i, (h0, h1, half) in enumerate(((0, 22, 14), (22, 40, 9), (40, CONE_TOP - TOP - 3, 5))):
        v.box(f"core{tag}_{i}", (0, TOP + (h0 + h1) / 2, CZ), (2 * half, h1 - h0, 2 * half), "basalt")
    for facing, (dx, dz) in ((f, FACING[f][2]) for f in FACING):
        h = {"front": 5, "back": 6, "right": 4, "left": 7}[facing] - (1 if tag else 0)
        u = RIM_R + 0.5
        v.box(f"rim{tag}_{facing}", (dx * u, CONE_TOP - 1 + h / 2, CZ + dz * u), (6, h, 6), "basalt")
        r = cone_u(TOP + 3) + 1.5
        s = 7 if tag else 6
        v.box(f"rock{tag}_{facing}", (dx * r + dz * 6, TOP + 2.5, CZ + dz * r - dx * 6), (s, 5, s), "ash_dark")


def volcano(root):
    v = root.group("volcano", (0, TOP, CZ))
    cone_half(v, "")
    v45 = root.group("volcano_45", (0, TOP, CZ), (0, 45, 0))
    cone_half(v45, "45")
    crater = v.group("crater_g", (0, CONE_TOP, CZ))
    crater.box("crater", (0, CONE_TOP - 1.0, CZ), (14, 1, 14), "lava")
    crater.box("crater_hot", (0, CONE_TOP - 0.4, CZ), (7, 1, 7), "lava_hot")
    return v


def stream(g, name, facing, path, along, w=4.0, jogs=(0, 3, -2, 2, -1)):
    """A lava stream: flat strips (a texel thick) lying on the faces along path [(u, y), ...] at `along` across them,
    jogging sideways from run to run, and a drip at its end. The path's runs must slope at legal angles. The cone's run
    is split in two so the stream jogs on the way down."""
    (u0, y0), (u1, y1) = path[0], path[1]
    mid = (u0 + (u1 - u0) * 0.45, y0 + (y1 - y0) * 0.45)
    path = [path[0], mid] + list(path[1:])
    for i, (a, b) in enumerate(zip(path, path[1:])):
        face_box(g, f"{name}_{i}", facing, a, b, 1, w - i * 0.25, "lava", out=True, along=along + jogs[i % len(jogs)])
    along = along + jogs[(len(path) - 2) % len(jogs)]
    u, y = path[-1]
    axis, sign, (dx, dz) = FACING[facing]
    if axis == "z":
        g.box(f"{name}_drip", (dx * (u + 0.6), y - 2, CZ + along), (1.2, 4, w * 0.8), "lava")
    else:
        g.box(f"{name}_drip", (along, y - 2, CZ + dz * (u + 0.6)), (w * 0.8, 4, 1.2), "lava")


def lava(root):
    """Three streams square on (`lava`): down his right side and his left side to the flanks, and down the back over
    the rump; one on a diagonal (`lava_45`) ending on the cone's foot. The wiggle is painted."""
    g = root.group("lava", (0, TOP, CZ))
    rim = (RIM_R + 0.3, CONE_TOP - 0.5)
    stream(g, "lava_right", "right", [rim, (CONE_R0, TOP), (46, 34), (46, 15)], 5)
    stream(g, "lava_left", "left", [rim, (CONE_R0, TOP), (46, 34), (46, 18)], -8)
    stream(g, "lava_back", "back", [rim, (CONE_R0, TOP), (38, 42), (38, 16)], -6, 3.6)
    g45 = root.group("lava_45", (0, TOP, CZ), (0, 45, 0))
    stream(g45, "lava_diag", "front", [rim, (CONE_R0 - 1, TOP + 2)], 4, 3.6)


# ---- the parts that keep their shape, rebuilt on legal angles ------------------------------------------------------

def finger(g, name, base, yaw, length, w=4.0):
    """A slim toad finger at a legal yaw (0, 22.5, 45), a round bump at its tip: a pad and a smaller cap on it."""
    yaw = snap_angle(yaw)
    a = math.radians(yaw)
    tip = (base[0] + math.sin(a) * length, base[1], base[2] - math.cos(a) * length)
    mid = ((base[0] + tip[0]) / 2, base[1], (base[2] + tip[2]) / 2)
    g.box(name, mid, (w, w * 0.85, length), "toe", rotation=(0, -yaw, 0))
    bump = w * 1.75
    g.box(name + "_tip", (tip[0], base[1] + 0.3, tip[2]), (bump, bump * 0.7, bump), "pad", rotation=(0, -yaw, 0))
    g.box(name + "_tip_cap", (tip[0], base[1] + bump * 0.55, tip[2]), (bump * 0.7, bump * 0.4, bump * 0.7), "pad",
          rotation=(0, -yaw, 0))


def brows(h, sd, x, y, front):
    """The brow on its own bone, turned at F3's angle (inner end low); inside it the ridge is square and the three
    ash-white tufts sweep out at 0, -22.5 and -45 degrees (the Hermit's droop), past the eye's outer corner."""
    c = (sd * (x + 0.5), y + 6.8, front + 2.6)
    g = h.group(f"brow_{s2.SIDES[sd]}", c, (-8, 0, sd * 11))
    g.box(f"brow_{sd}", c, (21, 3.6, 8), "brow")
    for i, (ox, oy, ln, th, tilt) in enumerate(((1, 2.2, 19, 3.4, 0), (4, 0.6, 18, 3.0, -22.5), (7.5, -1.2, 15, 2.6, -45))):
        a = math.radians(tilt)
        cx = c[0] + sd * (ox + ln / 2 * math.cos(a))
        cy = c[1] + oy + ln / 2 * math.sin(a)
        g.box(f"brow_ash_{sd}_{i}", (cx, cy, front + 1.5 - i * 0.9), (ln, th, 6 - i),
              "brow_ash" if i < 2 else "brow_ash_dark", rotation=(0, 0, sd * tilt))


PIPE_FROM = (31, 19.6, -55)
PIPE_YAW = -31                # turned outwards
PIPE_LEN = 29


def pipe(h, held="clenched"):
    """The pipe on its own bone, turned outwards from his right mouth corner; inside it the stem runs straight ahead
    and 22.5 degrees down to the bowl, which stands upright."""
    m = PIPE_FROM
    p = h.group("pipe", m, (0, PIPE_YAW, 0))
    a = math.radians(22.5)
    end = (m[0], m[1] - math.sin(a) * PIPE_LEN, m[2] - math.cos(a) * PIPE_LEN)
    p.box("pipe_mouthpiece", m, (3.6, 3.4, 6), "pipe_metal")
    p.box("pipe_stem", (m[0], (m[1] + end[1]) / 2, (m[2] + end[2]) / 2), (2.6, 2.6, PIPE_LEN), "pipe", rotation=(-22.5, 0, 0))
    p.box("pipe_ferrule", (end[0], end[1] + 1.4, end[2] + 2.4), (3.4, 3.4, 4), "pipe_metal", rotation=(-22.5, 0, 0))
    p.box("pipe_bowl", (end[0], end[1] + 4, end[2] - 1), (6, 8, 6), "pipe_metal")
    p.box("pipe_ember", (end[0], end[1] + 8.1, end[2] - 1), (4.2, 0.4, 4.2), "ember")
    if held == "clenched":
        p.box("lip_clench", (m[0] - 0.6, m[1] + 1.8, m[2] + 0.5), (5, 2.2, 6), "skin")


def slope_markings(b, sd):
    """Two strokes up the 45-degree back slope towards the volcano (paint; shown over the renders)."""
    for i, along in enumerate((-12, 18)):
        face_box(b, f"mark_slope_{sd}_{i}", "right" if sd > 0 else "left", (46, 34), (30, 50), 0.4, 2.0, "mark", out=True, along=along)


def build(model):
    """The blockout on legal angles (session 1's build with the parts above swapped in)."""
    saved = (s1.body, s1.volcano, s1.lava, s1.finger, s1.slope_markings, f1.pipe)
    s1.body, s1.volcano, s1.lava, s1.finger, s1.slope_markings, f1.pipe = body, volcano, lava, finger, slope_markings, pipe
    real_ash_brows = f2.ash_brows
    f2.ash_brows = lambda h, sd, x, y, front: None
    try:
        root = s1.build(model)
    finally:
        s1.body, s1.volcano, s1.lava, s1.finger, s1.slope_markings, f1.pipe = saved
        f2.ash_brows = real_ash_brows
    # the brows: swap the blockout's turned ridges for brow bones
    head = next(g for g in model.groups if g.name == "hi_head")
    for c in [c for c in head.children if not hasattr(c, "children") and c.name in ("brow_-1", "brow_1")]:
        head.children.remove(c)
        model.cubes.remove(c)
    x, y, z = f1.EYE_AT
    for sd in (-1, 1):
        brows(head, sd, x, y, z - 7.5)
    # the smoke placeholders are particles in game
    smoke = next((g for g in model.groups if g.name == "smoke"), None)
    if smoke:
        for c in [c for c in smoke.children if not hasattr(c, "children")]:
            model.cubes.remove(c)
        smoke.parent.children.remove(smoke)
        model.groups.remove(smoke)
    for c in [c for c in model.cubes if c.name in ("mouth_corner_-1", "mouth_corner_1")]:
        c.rotation = [0.0, 0.0, 0.0]
    return root


# ---- the review model ----------------------------------------------------------------------------------------------

# The user rejected the legal-angle rebuild (2026-10-14: it lost the mountain's and the back's detail), and the
# drawing-cost pass is for all bosses together once every boss is designed (the M6 performance pass). So the rig keeps
# session 2's geometry; the legal-angle builder above stays as the M6 starting point (LEGAL = True to use it).
LEGAL = False


def setup():
    s2.BUILDER = build if LEGAL else None
    s2._NUDGES = None
    s1.ARM.update({})                                   # the limbs are unchanged


def pose_table():
    """Per pose: the bones turned away from rest (absolute rotations) and position offsets (model units): the whole
    toad's lift or drop, the tongue sliding out along itself, the brows lifting."""
    rest = s2.build("rest")
    rest_rot = {g.name: g.rotation for g in rest.groups}
    poses = {}
    for key, (_, spec) in s2.POSES.items():
        posed = s2.build("p", key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest_rot[g.name]))}
        pos = {}
        if spec.get("y"):
            pos["base"] = (0.0, float(spec["y"]), 0.0)
        if spec.get("tongue"):
            a = math.radians(spec.get("jaw", 0) * 0.5)
            pos["tongue"] = (0.0, math.sin(a) * spec["tongue"], -math.cos(a) * spec["tongue"])
        if spec.get("brows"):
            pos["brows"] = (0.0, float(spec["brows"]), 0.0)
        poses[key] = (rot, pos)
    return poses


def keyframes(model, rot, pos):
    animators = v3.keyframes(model, rot)
    for name, (x, y, z) in pos.items():
        point = {"x": round(-x, 2), "y": round(y, 2), "z": round(z, 2)}
        frames = [{"channel": "position", "data_points": [point], "uuid": _uuid(f"{model.name}/kfp/{name}/{t}"),
                   "time": t, "color": -1, "interpolation": "linear"} for t in (0, 0.5)]
        uid = _uuid(f"{model.name}/group/{name}")
        animators.setdefault(uid, {"name": name, "type": "bone", "keyframes": []})["keyframes"] += frames
    return animators


def build_bbmodel(poses):
    model = s2.build(MODEL_ID, decals=False)
    s2.finish(model)
    v3.s2.PALETTE = s2.PALETTE
    img, uv, png = v3.material_atlas(model)
    texture = {"name": f"{MODEL_ID}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat.startswith(GLOWING):
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "",
                         "animators": keyframes(model, rot, pos)}
                        for key, (rot, pos) in poses.items()]
    return model, bb, img, (frm, to)


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 4.4, "dist": 13, "target_z": 2.9},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.0, "dist": 13, "target_z": 3.0},
    {"name": "flat_back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 4.4, "dist": 13, "target_z": 2.8,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
]


def main():
    setup()
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    poses = pose_table()
    model, bb, img, (frm, to) = build_bbmodel(poses)
    path = OUT / f"{MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), Image.NEAREST).save(OUT / "material_atlas.png")
    if SERVER_MODELS.is_dir():
        shutil.copyfile(path, SERVER_MODELS / path.name)

    # the rig as it goes in game (the painted details drawn over, so it reads)
    shown = s2.build("shown")
    s2.finish(shown)
    f1.render(shown, OUT / "rig", VIEWS, {"player_at": [-5.2, 1.0]})
    sheet.compare_sheet(OUT, [("rig", "the review rig (session 2's geometry)")], OUT / "rig.png",
                        heading="The Elder of Ash - session 3: the rig", views=("flat_34", "flat_front", "flat_back", "sil_side"))

    # pivots: a red marker at every bone's pivot, over the model in pale flat colours
    boxes = model.render_json(s2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.5 + 0.45 for c in b["color"]]
    for g in model.groups:
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, p - 1.2, p + 1.2, "hitbox"))
    v2.run_blender(boxes, OUT / "pivots", v3.PIVOT_VIEWS)
    a, b = Image.open(OUT / "pivots/pivots_front.png"), Image.open(OUT / "pivots/pivots_side.png")
    both = Image.new("RGB", (a.width + b.width, a.height))
    both.paste(a, (0, 0))
    both.paste(b, (a.width, 0))
    both.save(OUT / "pivots.png")

    from bosskit.checks import flicker_pairs
    rows, bad = v3.pivot_report(model)
    found = {}
    for g in model.groups:
        tags = {w for w in g.name.lower().split("_") if w in v3.BETTERMODEL_TAGS}
        if tags:
            found[g.name] = tags
    found["ob_hitbox"] = {"ob"}
    wrong = {n: t for n, t in found.items() if INTENDED_TAGS.get(n) != t}
    total, per_bone = v3.display_count(model)
    report = {"bones": len(model.groups) + 1, "bones_with_cubes": len(per_bone), "cubes": len(model.cubes),
              "displays": total, "flicker_pairs": len(flicker_pairs(model.cubes)), "pivots_to_check": bad,
              "tags": {n: sorted(t) for n, t in found.items()},
              "unintended_tags": {n: sorted(t) for n, t in wrong.items()},
              "hitbox_blocks": [round((t - f) / 16, 2) for f, t in zip(frm, to)],
              "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1])), "animations": list(poses)}
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# The Elder of Ash: rig pivots (session 3)\n\nGenerated by `tools/art/bosses/ash_s3.py`. "
                                   "Gap = distance from the pivot to the bone's nearest cube, in model units.\n\n"
                                   "| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("bones_with_cubes", "cubes", "displays", "flicker_pairs",
                                                   "pivots_to_check", "unintended_tags", "hitbox_blocks",
                                                   "displays_per_bone")}))


if __name__ == "__main__":
    main()
