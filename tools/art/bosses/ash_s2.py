"""The Elder of Ash, session 2: design lock (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

The approved blockout (ash_s1.py, take 2) rebuilt as a rig:
- every part on a named bone (BetterModel names): `base` (the whole toad, its pivot on the ground under his middle),
  `body`, `volcano`, `hi_head` with its `jaw` (and the `tongue` hidden in it), `brows` and the `pipe`; each front leg
  as `arm_*`, `forearm_*`, `hand_*`; each hind leg as `thigh_*`, `shin_*`, `foot_*`;
- the glow on its own bones: `glow_eye` (both eyes), `glow_crater`, `glow_lava` (the streams), `glow_pipe` (the
  bowl's ember);
- at his final size already (16 model units a block), every cube snapped to whole texels, and the flicker fix (no two
  faces on one plane);
- the painted details (the tribal markings, the mouth's line, the pupils and the nostrils) are texture: they are left
  out of the model and only drawn over the renders, so the design reads;
- the hitbox (`ob_hitbox`): the toad's body, head and haunches and the volcano's foot; not the fingers, toes, brows,
  pipe or the upper cone;
- the fight's key poses, posed from the rig (hands and feet planted on the ground where they should be).

Units are model pixels (16 = one block). The front is -z; his right is +x.

Run from the repository root: python tools/art/bosses/ash_s2.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import ash_face as f1, ash_s1 as s1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s2_design"
PALETTE = dict(f1.PALETTE, hitbox=(220, 60, 60), tongue=(196, 92, 84), tongue_tip=(255, 150, 60))
f1.PALETTE.update(PALETTE)
v2.PALETTE.update(PALETTE)
SIDES = {-1: "left", 1: "right"}


# ---- rig helpers ---------------------------------------------------------------------------------------------------

def group(model, name):
    return next(g for g in model.groups if g.name == name)


def move(c, g):
    """Puts a cube on another bone (cube coordinates are model-space, so it stays where it is)."""
    c.group.children.remove(c)
    g.children.append(c)
    c.group = g


def regroup(g, new_parent):
    g.parent.children.remove(g)
    new_parent.children.append(g)
    g.parent = new_parent


def drop_group(model, g):
    for c in [ch for ch in g.children if not hasattr(ch, "children")]:
        model.cubes.remove(c)
    for ch in [ch for ch in g.children if hasattr(ch, "children")]:
        drop_group(model, ch)
    g.parent.children.remove(g)
    model.groups.remove(g)


def subtree(g):
    out = [g]
    for ch in g.children:
        if hasattr(ch, "children"):
            out += subtree(ch)
    return out


def cubes_in(model, g):
    gs = set(id(x) for x in subtree(g))
    return [c for c in model.cubes if id(c.group) in gs]


def is_decal(c):
    """A painted detail: thinner than a texel (markings, the mouth's line, pupils, sockets, nostrils), not a glow."""
    return c.mat == "mark" or (min(np.array(c.to) - np.array(c.frm)) < 0.6 and c.mat not in f1.GLOW)


BUILDER = None               # session 3 swaps in its own geometry (ash_s3.build); None = the session 1 blockout


def rig(name, decals=True):
    model = Model(name)
    (BUILDER or s1.build)(model)
    base = group(model, "root")
    base.name = "base"
    if any(g.name == "smoke" for g in model.groups):
        drop_group(model, group(model, "smoke"))
    for c in [c for c in model.cubes if c.name.startswith("smoke")]:
        model.cubes.remove(c)
        c.group.children.remove(c)
    body, head = group(model, "body"), group(model, "hi_head")
    # the volcano and the lava ride on the body; the lava and the crater glow
    for n in ("volcano", "lava", "volcano_45", "lava_45"):
        if any(g.name == n for g in model.groups):
            regroup(group(model, n), body)
    group(model, "lava").name = "glow_lava"
    if any(g.name == "lava_45" for g in model.groups):
        group(model, "lava_45").name = "glow_lava_45"
    vol = group(model, "volcano")
    # the crater's glow rides on the cap (hidden with it at 33%); the blown top has its own
    crater_cube = next(c for c in model.cubes if c.name == "crater")
    crater = crater_cube.group.group("glow_crater", (0, s1.CONE_TOP, s1.CONE_Z))
    for c in [c for c in model.cubes if c.name in ("crater", "crater_hot")]:
        move(c, crater)
    if any(g.name == "cone_cap" for g in model.groups):
        # the streams' tops, up on the cap, are hidden with it when the top blows off
        cap = group(model, "cone_cap")
        lava_cap = cap.group("glow_lava_cap", (0, s1.CAP_Y, s1.CONE_Z))
        for c in [c for c in model.cubes if c.group.name == "glow_lava" and c.corners()[:, 1].max() > s1.CAP_Y + 1]:
            move(c, lava_cap)
    if any(c.name == "crater_blown" for c in model.cubes):
        blown_cube = next(c for c in model.cubes if c.name == "crater_blown")
        blown_glow = blown_cube.group.group("glow_crater_blown", (0, s1.CAP_Y, s1.CONE_Z))
        for c in [c for c in model.cubes if c.name in ("crater_blown", "crater_blown_hot")]:
            move(c, blown_glow)
    regroup(head, body)
    # the head: the jaw on its hinge at the back of the mouth, the tongue in it, the brows, the glowing eyes, the pipe
    jaw = head.group("jaw", (0, 20, -22))
    for c in [c for c in model.cubes if c.group is head and (c.name in ("jaw", "throat") or c.name.startswith("mark_chin"))]:
        move(c, jaw)
    # the tongue: rooted at the back of the mouth, on the head (not the jaw), lying flat in the closed mouth's seam
    # like vanilla's frog; it lashes out of the middle of the open mouth
    # thin and long (5 blocks): retracted, it runs back down his throat into the body, hidden
    tongue = head.group("tongue", (0, 20, -24))
    tongue.box("tongue", (0, 20, -14), (4, 1, 80), "tongue")
    tongue.box("tongue_tip", (0, 20.5, -55), (6, 2, 4), "tongue_tip")
    # the inside of the mouth (paint: the jaw's top and the head's underside), seen when the jaw drops
    jaw.box("maw_floor", (0, 20.3, -39), (58, 0.4, 32), "mouth")
    head.box("maw_roof", (0, 19.7, -39), (58, 0.4, 32), "mouth")
    brows = head.group("brows", (0, 50, -48))
    for c in [c for c in model.cubes if c.group is head and c.name.startswith("brow_") and c.name != "brow_dip"]:
        move(c, brows)
    for g in [g for g in model.groups if g.parent is head and g.name.startswith("brow_")]:
        regroup(g, brows)                                  # session 3: each brow is its own bone
    eyes = head.group("glow_eye", (0, 44, -55))
    for c in [c for c in model.cubes if c.group is head and c.mat == "eye"]:
        move(c, eyes)
    for c in [c for c in model.cubes if c.mat == "eye_socket"]:      # the socket is paint
        model.cubes.remove(c)
        c.group.children.remove(c)
    pipe = group(model, "pipe")
    regroup(pipe, jaw)                                    # held in the lower lip: it drops with the jaw
    glow_pipe = pipe.group("glow_pipe", (46, 16, -80))
    move(next(c for c in model.cubes if c.name == "pipe_ember"), glow_pipe)
    for c in [c for c in model.cubes if c.name == "lip_clench"]:
        move(c, pipe)
    # the front legs: arm (shoulder), forearm (elbow), hand (wrist)
    for sd, side in SIDES.items():
        arm = group(model, f"arm_{sd}")
        arm.name = f"arm_{side}"
        sh, el, wr = ((sd * v[0], v[1], v[2]) for v in (s1.ARM["sh"], s1.ARM["el"], s1.ARM["wr"]))
        fore = arm.group(f"forearm_{side}", el)
        hand = fore.group(f"hand_{side}", wr)
        marks = group(model, f"arm_marks_{sd}")
        for c in [c for c in model.cubes if c.group in (arm, marks)]:
            n = c.name
            if n.startswith((f"arm_{sd}_palm", f"arm_{sd}_finger", "mark_hand")):
                move(c, hand)
            elif n.startswith((f"arm_{sd}_fore", f"arm_{sd}_wrist", "mark_fore")):
                move(c, fore)
            else:
                move(c, arm)
        marks.parent.children.remove(marks)
        model.groups.remove(marks)
        # the hind legs: thigh (hip), shin (knee), foot (ankle)
        leg = group(model, f"leg_{sd}")
        leg.name = f"thigh_{side}"
        knee, ankle = (sd * 54, 10, 1), (sd * 55, 5, 36)
        shin = leg.group(f"shin_{side}", knee)
        foot = shin.group(f"foot_{side}", ankle)
        for c in [c for c in model.cubes if c.group is leg]:
            if c.name.startswith((f"foot_{sd}", f"toe_{sd}")):
                move(c, foot)
            elif c.name.startswith(f"shin_{sd}"):
                move(c, shin)
    if not decals:
        for c in [c for c in model.cubes if is_decal(c)]:
            model.cubes.remove(c)
            c.group.children.remove(c)
    return model


# ---- poses -----------------------------------------------------------------------------------------------------------

def translate(model, g, d):
    for x in subtree(g):
        x.origin = [x.origin[i] + d[i] for i in range(3)]
    for c in cubes_in(model, g):
        c.frm = [c.frm[i] + d[i] for i in range(3)]
        c.to = [c.to[i] + d[i] for i in range(3)]
        c.origin = [c.origin[i] + d[i] for i in range(3)]


def low_y(model, g):
    return min(c.corners()[:, 1].min() for c in cubes_in(model, g))


def plant(model, bone, axis, sub, sign=1):
    """Turns a bone about one axis until the lowest point of `sub` rests on the ground (y 0)."""
    g = group(model, bone)
    base = g.rotation[axis]
    best = None
    for tenth in range(-400, 401, 5):                   # small turns only: the hand never flips over
        g.rotation[axis] = base + sign * tenth / 10
        err = abs(low_y(model, group(model, sub)))
        key = (round(err * 2), abs(tenth))              # good enough (to half a texel), then the smallest turn
        if best is None or key < best[0]:
            best = (key, g.rotation[axis])
    g.rotation[axis] = best[1]


#   y: raise (+) or drop (-) the whole toad; tilt: pitch of the whole toad (+ nose up); head, jaw: pitch (+ up);
#   arm / thigh: (x, y, z) of the left side, mirrored for the right; plant: put hands and feet back on the ground;
#   tongue: how far it slides out of the mouth; brows: lift
POSES = {
    "idle": ("idle: still, heavy, the pipe smoking", {}),
    "coil": ("the coil before the leap: sunk low, elbows up, glaring up at the target",
             {"y": -11, "head": 12, "arm": (0, 0, -24), "thigh": (0, 0, -14), "plant": True, "brows": -1.5}),
    "leap": ("the leap: launched nose-up, arms reaching, hind legs thrown back",
             {"y": 34, "tilt": 16, "head": -6, "arm": (-40, 0, 6), "forearm": (-30, 0, 0), "thigh": (-85, 0, 0),
              "shin": (-10, 0, 0), "foot": (60, 0, 0)}),
    "slam": ("the slam: landed flat, splayed, the ground cracking", {"y": -9, "head": -6, "jaw": -8,
             "arm": (0, 0, -30), "thigh": (0, 0, -18), "plant": True}),
    "tongue": ("the tongue: the jaw dropped, the flat tongue lashing out", {"head": -4, "jaw": -22, "tongue": 82,
               "brows": 1.5, "arm": (0, 0, -6), "plant": True}),
    "erupt": ("the eruption at 66%: head thrown back, the volcano bursting", {"y": 3, "tilt": -4, "head": 20, "jaw": -22,
              "brows": 2, "arm": (0, 0, 6), "plant": True}),
    "death": ("death: slumped flat, chin on the ground, the volcano gone cold", {"y": -10, "tilt": -5, "head": -12,
              "jaw": -6, "arm": (0, 0, -40), "thigh": (0, 0, -24), "plant": True}),
}


def pose(model, spec):
    base, head = group(model, "base"), group(model, "hi_head")
    base.rotation = [spec.get("tilt", 0), 0, 0]
    head.rotation = [spec.get("head", 0), spec.get("turn", 0), 0]
    group(model, "jaw").rotation = [spec.get("jaw", 0), 0, 0]
    for sd, side in SIDES.items():
        m = -sd                                            # the spec is for the left side (sd -1)
        for bone in ("arm", "forearm", "thigh", "shin", "foot"):
            r = spec.get(f"{bone}_{side}", spec.get(bone, (0, 0, 0)))     # a per-side key wins (session 7's walk)
            group(model, f"{bone}_{side}").rotation = [r[0], r[1] * m, r[2] * m]
    # the pipe stays in the lower lip but tips back up as the jaw drops, so its bowl never digs into the ground
    pipe = group(model, "pipe")
    pipe.rotation = [-spec.get("jaw", 0) * 1.5 - min(0, spec.get("head", 0) + spec.get("tilt", 0)) + 3,
                     pipe.rotation[1], pipe.rotation[2]]
    tilt = spec.get("jaw", 0) * 0.5                       # the tongue comes out of the middle of the open mouth
    group(model, "tongue").rotation = [tilt, 0, 0]
    if spec.get("tongue"):                                # slid out along itself; its root stays at the back of the mouth
        for c in cubes_in(model, group(model, "tongue")):
            for v in (c.frm, c.to, c.origin):
                v[2] -= spec["tongue"]
    if spec.get("brows"):
        translate(model, group(model, "brows"), (0, spec["brows"], 0))
    if spec.get("y"):
        translate(model, base, (0, spec["y"], 0))
    if spec.get("plant"):
        lifted = spec.get("lifted", ())                    # a limb in mid-step stays off the ground
        for sd, side in SIDES.items():
            if f"hand_{side}" not in lifted:
                plant(model, f"forearm_{side}", 2, f"hand_{side}")
            if f"foot_{side}" not in lifted:
                plant(model, f"shin_{side}", 0, f"foot_{side}")


def build(name, key="idle", decals=True):
    model = rig(name, decals)
    pose(model, POSES[key][1])
    return model


# ---- snap, flicker fix, hitbox --------------------------------------------------------------------------------------

_NUDGES = None


def _snap(model):
    v2.snap(model)
    for c in model.cubes:                  # the glowing eyes (and the painted pupils on them) are flat planes
        if c.mat in ("eye", "pupil"):
            z = min(c.frm[2], c.to[2]) + (0.3 if c.mat == "eye" else 0.1)
            c.frm[2] = c.to[2] = z


def finish(model):
    """Snapped to whole texels, then the flicker fix: the smaller part of each clash moves a fraction of a texel off
    the plane (the Witch Coven's resolver). The nudges are found once in the rest pose (without the painted details)
    and kept in each cube's own space, so every pose gets the same model."""
    global _NUDGES
    _snap(model)
    if _NUDGES is None:
        rest = rig("nudge_rest", decals=False)
        _snap(rest)
        from bosses.coven_s2 import _resolve
        _NUDGES = {}
        _resolve(rest, _NUDGES)
    by_name = {c.name: c for c in model.cubes}
    for name, d in _NUDGES.items():
        if name in by_name:
            c = by_name[name]
            c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]


def hitbox_bounds(model):
    """The body, the head and the haunches, the arms down to the elbow and the volcano's foot (to the skirt's top): not
    the hands, feet, brows or pipe, so nothing loose is a free target; the cone above stays out of reach anyway."""
    keep = []
    skip = ("brows", "pipe", "glow_", "hand_", "foot_", "forearm_", "tongue")
    for c in model.cubes:
        names = [g.name for g in [c.group] + _ancestors(c.group)]
        if any(n.startswith(skip) for n in names):
            continue
        keep.append(c.corners())
    pts = np.vstack(keep)
    lo, hi = pts.min(0), pts.max(0)
    half_x = float(np.ceil(max(-lo[0], hi[0])))
    top = min(float(np.ceil(hi[1])), s1.SKIRT[3])
    return (-half_x, 0.0, float(np.floor(lo[2]))), (half_x, top, float(np.ceil(hi[2])))


def _ancestors(g):
    out = []
    while g.parent is not None:
        g = g.parent
        out.append(g)
    return out


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 4.4, "dist": 13, "target_z": 2.9},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.0, "dist": 13, "target_z": 3.0},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -32, "height": 4.2, "dist": 15, "target_z": 2.8,
     "player": False},
]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 4.4, "dist": 12.5, "target_z": 3.0,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]
MOUTH_VIEWS = [
    {"name": "mouth_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 2.2, "dist": 8.5, "target_z": 1.6,
     "player": False},
    {"name": "mouth_side", "mode": "flat", "camera": "persp", "yaw": 80, "height": 1.8, "dist": 8.5, "target_z": 1.5,
     "player": False},
]


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    if not only:
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
        # the model: no painted details, the hitbox added
        rest = build("occultech_elder_of_ash_blockout", decals=False)
        finish(rest)
        frm, to = hitbox_bounds(rest)
        bb = rest.to_bbmodel()
        add_hitbox(bb, frm, to)
        main_dir = OUT / "design"
        main_dir.mkdir()
        (main_dir / "occultech_elder_of_ash_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        stats = dict(rest.stats(), hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(frm, to)],
                     bones_with_geometry=sum(1 for g in rest.groups if any(not hasattr(c, "children") for c in g.children)))
        (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        (OUT / "parts.md").write_text("# The Elder of Ash blockout parts (session 2)\n\nGenerated by "
                                      "`tools/art/bosses/ash_s2.py`. Cube sizes are whole texels; the painted details "
                                      "are not in the model.\n\n" + parts_list(rest) + "\n", encoding="utf-8")
        print(stats)
        # the renders: with the painted details drawn over, so the design reads
        shown = build("occultech_elder_of_ash_shown")
        finish(shown)
        f1.render(shown, main_dir, MAIN_VIEWS, {"player_at": [-5.2, 1.0]})
        sheet.compare_sheet(OUT, [("design", "the design lock")], OUT / "design.png",
                            heading="The Elder of Ash - design lock (session 2)",
                            views=("flat_34", "flat_front", "sil_side", "clay_34"))
        boxes = rest.render_json(PALETTE)
        for b in boxes:
            b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
        boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
        v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                               {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
        from PIL import Image
        a, b = (Image.open(OUT / "hitbox" / f"hitbox_{v}.png") for v in ("front", "side"))
        both = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
        both.paste(a, (0, 0))
        both.paste(b, (a.width + 10, 0))
        both.save(OUT / "hitbox.png")
    for key in (only or POSES):
        posed = build(f"occultech_elder_of_ash_{key}", key)
        finish(posed)
        f1.render(posed, OUT / "poses" / key, POSE_VIEWS + (MOUTH_VIEWS if key in ("idle", "tongue", "erupt") else []))
    keys = list(POSES)
    if all((OUT / "poses" / k / "flat_34.png").exists() for k in keys):
        for i, chunk in enumerate((keys[:4], keys[4:])):
            sheet.compare_sheet(OUT / "poses", [(k, k) for k in chunk], OUT / f"poses_{i + 1}.png",
                                heading="The Elder of Ash - the key poses", views=("flat_34", "sil_side"))
        sheet.compare_sheet(OUT / "poses", [(k, k) for k in ("idle", "tongue", "erupt")], OUT / "mouth.png",
                            heading="The Elder of Ash - the mouth: the tongue from inside, the pipe on the lower lip",
                            views=("mouth_34", "mouth_side"))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
