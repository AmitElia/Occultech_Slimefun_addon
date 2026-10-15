"""The Archevoker redesign, session 3: rig and pose test (plan: docs/art/bosses/archevoker/overhaul/plan.md).

On top of the session 2 design lock (archevoker_s2.py), unchanged in look:
- a free saving: a cube turned on one axis by any multiple of 22.5 degrees is stored as a turn of 0, 22.5 or 45 with
  its two sides swapped, which looks the same but lets BetterModel keep it inside its bone's display;
- a pivot check (every bone's pivot in its joint) and a BetterModel tag check;
- a display count (what the models cost to draw; cutting it waits for the M6 pass);
- a flat colour per material, so both models can be seen in game before texturing (the eyes, the runes and the spell
  circles full-bright);
- the nine key poses as BetterModel animations (`/bm test occultech_archevoker_rig <pose>`), and the casting hand as
  its own review model (`occultech_archevoker_hand_cyan_rig`, `_purple_rig`).

Output: docs/art/bosses/archevoker/overhaul/s3_rig/, plus the review models copied into run/plugins/BetterModel/models.
They are never shipped.

Run from the repository root: python tools/art/bosses/archevoker_s3.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import archevoker_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_archevoker_rig"
GLOWING = ("cyan", "purple")
INTENDED = {"hi_head": {"hi"}, "glow_ring": {"glow"}, "glow_runes": {"glow"}, "glow_eyes": {"glow"},
            "glow_eye": {"glow"}, "glow_circle": {"glow"}, "ob_hitbox": {"ob"}}
LEGAL = (0.0, 22.5, -22.5, 45.0, -45.0)


def fold_quarter_turns(model):
    """Single-axis turns by any multiple of 22.5 degrees become 0/22.5/45 turns with the two sides across the axis
    swapped: the same box, but one BetterModel can keep inside its bone's item model."""
    swaps = {0: (1, 2), 1: (0, 2), 2: (0, 1)}
    for c in model.cubes:
        axes = [i for i, v in enumerate(c.rotation) if abs(v) > 1e-6]
        if len(axes) != 1:
            continue
        i = axes[0]
        a = c.rotation[i]
        turns = round(a / 90)
        rest = a - 90 * turns
        if turns == 0 or not any(abs(rest - v) < 1e-3 for v in LEGAL):
            continue
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, size = (lo + hi) / 2, hi - lo
        if turns % 2:
            j, k = swaps[i]
            size[j], size[k] = size[k], size[j]
        # the box turns about its own origin; its centre must land in the same place
        from bosskit.bbmodel import pivot_matrix
        world_c = (pivot_matrix(c.origin, c.rotation) @ np.array([*centre, 1.0]))[:3]
        rot = [0.0, 0.0, 0.0]
        rot[i] = rest
        local_c = (np.linalg.inv(pivot_matrix(c.origin, rot)) @ np.array([*world_c, 1.0]))[:3]
        c.frm, c.to, c.rotation = (local_c - size / 2).tolist(), (local_c + size / 2).tolist(), rot


def build(key="rest"):
    m = s2.build(key)
    fold_quarter_turns(m)
    return m


def pose_table():
    """Per pose: the bones turned away from rest (absolute rotations) and position offsets (the risen priest's body,
    the dying throne's base)."""
    rest = {g.name: g.rotation for g in build("rest").groups}
    poses = {}
    for key, (_, spec) in s2.POSES.items():
        posed = build(key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if g.name in rest and any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest[g.name]))}
        pos = {}
        if spec.get("body"):
            pos["body"] = tuple(float(v) for v in spec["body"])
        if spec.get("base"):
            pos["base"] = (0.0, float(spec["base"][0]), 0.0)
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


def flat_bbmodel(model, name, hitbox, animations=()):
    v3.s2.PALETTE = s2.PALETTE
    img, uv, png = v3.material_atlas(model)
    texture = {"name": f"{name}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(name + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
    model.name = name
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat in GLOWING:
            element["light_emission"] = 15
    add_hitbox(bb, *hitbox)
    bb["animations"] = [{"uuid": _uuid(f"{name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "",
                         "animators": keyframes(model, rot, pos)} for key, (rot, pos) in animations]
    return bb, img


def report(model, hitbox, extra=None):
    rows, bad = v3.pivot_report(model)
    found = {}
    for g in model.groups:
        tags = {w for w in g.name.lower().split("_") if w in v3.BETTERMODEL_TAGS}
        if tags:
            found[g.name] = tags
    found["ob_hitbox"] = {"ob"}
    wrong = {n: sorted(t) for n, t in found.items() if INTENDED.get(n) != t}
    total, per_bone = v3.display_count(model)
    frm, to = hitbox
    out = {"bones_with_cubes": len(per_bone), "cubes": len(model.cubes), "displays": total,
           "flicker_pairs": len(flicker_pairs(model.cubes)), "pivots_to_check": bad,
           "tags": {n: sorted(t) for n, t in found.items()}, "unintended_tags": wrong,
           "hitbox_blocks": [round((t - f) / 16, 2) for f, t in zip(frm, to)],
           "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1]))}
    if extra:
        out.update(extra)
    return out, rows


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.6, "dist": 12, "target_z": 4.2},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.4, "dist": 12, "target_z": 4.2,
     "player": False},
    {"name": "flat_back", "mode": "flat", "camera": "persp", "yaw": 160, "height": 4.0, "dist": 12, "target_z": 4.2,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(s2.PALETTE)
    poses = pose_table()
    model = build("rest")
    hitbox = s2.hitbox_bounds(model)
    bb, img = flat_bbmodel(model, MODEL_ID, hitbox, poses.items())
    paths = [OUT / f"{MODEL_ID}.bbmodel"]
    paths[0].write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), Image.NEAREST).save(OUT / "material_atlas.png")
    rep, rows = report(model, hitbox, {"animations": list(poses)})
    hands = {}
    for glow in ("cyan", "purple"):
        hm = s2.hand_model(glow)
        fold_quarter_turns(hm)
        name = f"occultech_archevoker_hand_{glow}_rig"
        hb, _ = flat_bbmodel(hm, name, s2.HAND_HITBOX)
        p = OUT / f"{name}.bbmodel"
        p.write_text(json.dumps(hb, indent=1) + "\n", encoding="utf-8")
        paths.append(p)
        hands[glow], _ = report(hm, s2.HAND_HITBOX)
    rep["hand"] = hands["cyan"]
    (OUT / "rig_report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# The Archevoker: rig pivots (session 3)\n\nGenerated by "
                                   "`tools/art/bosses/archevoker_s3.py`. Gap = distance from the pivot to the bone's "
                                   "nearest cube, in model units.\n\n| Bone | Pivot | Gap | |\n|---|---|---|---|\n"
                                   + "\n".join(rows) + "\n", encoding="utf-8")
    if SERVER_MODELS.is_dir():
        for p in paths:
            shutil.copyfile(p, SERVER_MODELS / p.name)
    # the rig as it goes in game, and its pivots
    shown = build("rest")
    s2.casting_hands(shown, s2.POSES["rest"][1])
    v2.run_blender(shown.render_json(v2.PALETTE), OUT / "rig", VIEWS)
    sheet.compare_sheet(OUT, [("rig", "the review rig")], OUT / "rig.png",
                        heading="The Archevoker - session 3: the rig",
                        views=("flat_34", "flat_front", "flat_back", "sil_side"))
    boxes = model.render_json(s2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.5 + 0.45 for c in b["color"]]
    for g in model.groups:
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, (p - 1.2).tolist(), (p + 1.2).tolist(), "hitbox"))
    v2.run_blender(boxes, OUT / "pivots", v3.PIVOT_VIEWS)
    s2.side_by_side([OUT / "pivots/pivots_front.png", OUT / "pivots/pivots_side.png"], OUT / "pivots.png")
    print(json.dumps({k: rep[k] for k in ("bones_with_cubes", "cubes", "displays", "flicker_pairs", "pivots_to_check",
                                          "unintended_tags", "hitbox_blocks", "displays_per_bone")}))
    print("hand", json.dumps({k: hands["cyan"][k] for k in ("cubes", "displays", "flicker_pairs", "unintended_tags")}))


if __name__ == "__main__":
    main()
