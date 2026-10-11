"""Volley redesign, session 3: rig and pose test.

On top of the session 2 blockout, this session adds:
- a pivot check: every bone's pivot must sit in its joint;
- a BetterModel tag check: only the intended bones carry a tag;
- a display count: what the model costs to draw;
- a flat colour per material, so the model can be seen in game before texturing;
- six test poses, saved as BetterModel animations (`/bettermodel test occultech_volley_rig <pose>`).

Output: docs/art/bosses/volley/overhaul/s3_rig/, plus the review model copied into run/plugins/BetterModel/models.
It is never shipped: the plugin still installs the textured model from src/main/models.

Run from the repository root: python tools/art/bosses/volley_crone_s3.py
"""
import base64
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as s2  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_volley_rig"
BEND = s2.BEND

# BetterModel's bone-name tags (BoneTags in BetterModel 3.5.0): a bone whose name has one of these as a word gets it
BETTERMODEL_TAGS = {"h", "hi", "b", "ob", "p", "sp", "tag", "mtag", "ptag", "glow", "pli", "li", "pri", "ri", "ph",
                    "pra", "prfa", "pla", "plfa", "phip", "pw", "pc", "prl", "prfl", "pll", "plfl", "cape"}
INTENDED_TAGS = {"h_head": {"h"}, "glow_crystals": {"glow"}, "ob_hitbox": {"ob"}}

# Six test poses: absolute bone rotations, like Blockbench's group rotations (session 2's three plus three new)
POSES = dict({k: v for k, (_, v) in s2.POSES.items()}, **{
    "windup": {   # cranking: the arbalest pulled up against the chest, the left fist on the windlass
        "arm_right_upper": (BEND + 30, 0, 4), "arm_right_forearm": (95, 0, -10), "arbalest": (-20, 0, 0),
        "arm_left_upper": (BEND + 55, 0, 40), "arm_left_forearm": (70, 0, 0), "h_head": (BEND * 0.2, 0, 0),
        "torso": (-BEND * 0.8, 0, 0)},
    "recoil": {   # the bolt is away: the weapon kicks up, the chest rocks back, the jaw drops
        "arm_right_upper": (BEND + 85, 0, 4), "arm_right_forearm": (24, 0, 0), "arbalest": (-12, 0, 0),
        "arm_left_upper": (BEND + 40, 0, 15), "arm_left_forearm": (30, 0, 0), "torso": (-BEND * 0.45, 0, 0),
        "h_head": (BEND * 0.7, 0, 0), "jaw_counter": (14, 0, 0)},
    "stagger": {  # a ward breaks: he twists away from it, the head lolls, the left arm catches the ground
        "waist": (-BEND * 0.5, 14, 8), "torso": (-BEND * 0.75, 10, 10), "h_head": (BEND * 0.15, -20, -18),
        "arm_left_upper": (BEND + 40, 0, -6), "arm_left_forearm": (5, 0, 0),
        "arm_right_upper": (BEND - 10, 0, 30), "arm_right_forearm": (40, 0, 0), "jaw_counter": (10, 0, 0)},
})


def material_atlas(model):
    """A 32x32 atlas with one flat swatch per material: what BetterModel draws until the real texture exists."""
    mats = sorted({c.mat for c in model.cubes})
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    uv = {}
    for i, mat in enumerate(mats):
        x, y = (i % 8) * 4, (i // 8) * 4
        img.paste(Image.new("RGBA", (4, 4), tuple(s2.PALETTE[mat][:3]) + (255,)), (x, y))
        uv[mat] = [x + 1, y + 1, x + 3, y + 3]
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return img, uv, buf.getvalue()


def keyframes(model, pose):
    """A held pose as a Blockbench animation. Keyframes are offsets from the rest rotation; Blockbench's animator
    turns bones the opposite way round X and Y to its group rotation, so those two are negated."""
    rest = {g.name: g.rotation for g in model.groups}
    animators = {}
    for name, rot in pose.items():
        d = [rot[i] - rest[name][i] for i in range(3)]
        point = {"x": round(-d[0], 2), "y": round(-d[1], 2), "z": round(d[2], 2)}
        frames = [{"channel": "rotation", "data_points": [point], "uuid": _uuid(f"{model.name}/kf/{name}/{t}"),
                   "time": t, "color": -1, "interpolation": "linear"} for t in (0, 0.5)]
        animators[_uuid(f"{model.name}/group/{name}")] = {"name": name, "type": "bone", "keyframes": frames}
    return animators


def build_bbmodel():
    model = s2.build()
    model.name = MODEL_ID
    img, uv, png = material_atlas(model)
    texture = {"name": "occultech_volley_rig.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat == "glow":
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "", "animators": keyframes(model, pose)}
                        for key, pose in POSES.items()]
    return model, bb, img


def world_pivot(g):
    """Where a bone's pivot is in the rest pose, in model units."""
    parent = g.parent.world_matrix() if g.parent is not None else np.eye(4)
    return (parent @ np.array([*g.origin, 1.0]))[:3]


def _gap(point, cube):
    """Distance from a rest-space point to a cube, with the cube's own rotation taken into account."""
    local = np.linalg.inv(pivot_matrix(cube.origin, cube.rotation)) @ np.array([*point, 1.0])
    lo, hi = np.array(cube.frm), np.array(cube.to)
    return float(np.linalg.norm(np.maximum(0, np.maximum(lo - local[:3], local[:3] - hi))))


def pivot_report(model):
    """Distance from each bone's pivot to its own nearest cube (rest space): a joint pivot sits inside or on it."""
    rows, bad = [], []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if not cubes:
            continue
        gap = min(_gap(np.array(g.origin), c) for c in cubes)
        ok = gap <= 1.5
        rows.append(f"| `{g.name}` | {', '.join(f'{v:g}' for v in g.origin)} | {gap:.1f} | {'in the joint' if ok else 'CHECK'} |")
        if not ok:
            bad.append(g.name)
    return rows, bad


def tag_report(model):
    found = {}
    for g in model.groups:
        tags = {w for w in g.name.lower().split("_") if w in BETTERMODEL_TAGS}
        if tags:
            found[g.name] = tags
    found["ob_hitbox"] = {"ob"}
    wrong = {k: v for k, v in found.items() if INTENDED_TAGS.get(k) != v}
    return found, wrong


def display_count(model):
    """BetterModel draws each bone as one item display, plus one more for every distinct cube rotation it can't keep
    inside an item model (anything but a single 22.5- or 45-degree turn)."""
    valid = {0.0, 22.5, 45.0, -22.5, -45.0}
    total, per_bone = 0, {}
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if not cubes:
            continue
        keys = set()
        for c in cubes:
            r = tuple(round(v, 3) for v in c.rotation)
            keys.add((0, 0, 0) if sum(v != 0 for v in r) < 2 and all(v in valid for v in r) else r)
        per_bone[g.name] = len(keys)
        total += len(keys)
    return total, per_bone


PIVOT_VIEWS = [
    {"name": "pivots_front", "mode": "flat", "camera": "ortho_front", "xray": 0.45},
    {"name": "pivots_side", "mode": "flat", "camera": "ortho_side", "xray": 0.45},
]


def main():
    model, bb, img = build_bbmodel()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), Image.NEAREST).save(OUT / "material_atlas.png")
    if SERVER_MODELS.is_dir():
        shutil.copyfile(path, SERVER_MODELS / path.name)

    # pivots: a red marker at every bone's pivot, over the model in pale flat colours
    boxes = model.render_json(s2.PALETTE)
    for b in boxes:
        b["color"] = [v * 0.5 + 0.45 for v in b["color"]]
    for g in model.groups:
        p = world_pivot(g)
        boxes.append(s2.box_json("pivot_" + g.name, p - 1.6, p + 1.6, "hitbox"))
    s2.run_blender(boxes, OUT / "pivots", PIVOT_VIEWS)
    a, b = Image.open(OUT / "pivots/pivots_front.png"), Image.open(OUT / "pivots/pivots_side.png")
    both = Image.new("RGB", (a.width + b.width, a.height))
    both.paste(a, (0, 0))
    both.paste(b, (a.width, 0))
    both.save(OUT / "pivots.png")

    for key, pose in POSES.items():
        posed = s2.build()
        groups = {g.name: g for g in posed.groups}
        for name, rot in pose.items():
            groups[name].rotation = [float(v) for v in rot]
        s2.run_blender(posed.render_json(s2.PALETTE), OUT / "poses" / key, s2.POSE_VIEWS)
    sheet.compare_sheet(OUT / "poses", [(k, "") for k in POSES], OUT / "poses.png",
                        heading="Volley - six test poses (session 3)")

    rows, bad = pivot_report(model)
    tags, wrong = tag_report(model)
    total, per_bone = display_count(model)
    report = {"bones": len(model.groups) + 1, "cubes": len(model.cubes), "displays": total,
              "pivots_to_check": bad, "tags": {k: sorted(v) for k, v in tags.items()},
              "unintended_tags": {k: sorted(v) for k, v in wrong.items()},
              "displays_per_bone": per_bone, "animations": list(POSES)}
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# Volley rig pivots (session 3)\n\nGenerated by `tools/art/bosses/volley_crone_s3.py`."
                                   " Gap = distance from the pivot to the bone's nearest cube, in model units.\n\n"
                                   "| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("bones", "cubes", "displays", "pivots_to_check", "unintended_tags")}))


if __name__ == "__main__":
    main()
