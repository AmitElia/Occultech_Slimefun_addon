"""The Unbound redesign, session 3: rig and pose test (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

On top of the session 2 design lock (unbound_s2.py):
- a pivot check: every bone's pivot must sit in its joint;
- a BetterModel tag check: only the intended bones carry a tag;
- a display count: what the model costs to draw;
- a flat colour per material, so he can be seen in game before texturing (the eye and the chest fire full-bright);
- the eight key poses, saved as BetterModel animations (`/bm test occultech_unbound_rig <pose>`). Kneeling poses
  sink the root (a position key); the dropped cleaver is set down with one too.

Output: docs/art/bosses/the_unbound/overhaul/s3_rig/, plus the review model copied into run/plugins/BetterModel/models.
It is never shipped.

Run from the repository root: python tools/art/bosses/unbound_s3.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosses import unbound_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_unbound_rig"
GLOWING = ("fire", "eye")
INTENDED_TAGS = {"hi_head": {"hi"}, "glow_eye": {"glow"}, "glow_chest": {"glow"}, "glow_flames": {"glow"}, "ob_hitbox": {"ob"}}


def scale_factor():
    rest = s2.build("k")
    return s2.s1.HEAD_TOP / float(s2.cube(rest, "head").corners()[:, 1].max())


def pose_table(k):
    """Per pose: the bones it turns away from rest (absolute rotations), and position offsets (model units, after
    scaling) for the root (kneeling) and the cleaver (set down)."""
    rest = s2.build("rest")
    rest_rot = {g.name: g.rotation for g in rest.groups}
    poses = {}
    for key, (_, spec) in s2.POSES.items():
        posed = s2.build("p", key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest_rot[g.name]))}
        pos = {}
        if spec.get("drop"):
            pos["root"] = (0.0, -spec["drop"] * k, 0.0)
        if spec["cleaver"] == "flat":
            cl = s2.group(posed, "cleaver")
            rest_cl = s2.group(s2.build("q", key), "cleaver")      # the same pose before it was set down
            pos["cleaver"] = (0.0, (cl.origin[1] - rest_cl.origin[1]) * k, 0.0)
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


def build_bbmodel(k, poses):
    model = s2.build(MODEL_ID)
    s2.finish(model, k)
    v3.s2.PALETTE = s2.PALETTE   # the atlas swatches read Volley's module palette
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
    return model, bb, img


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    k = scale_factor()
    poses = pose_table(k)
    model, bb, img = build_bbmodel(k, poses)
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
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, p - 1.2, p + 1.2, "hitbox"))
    v2.run_blender(boxes, OUT / "pivots", v3.PIVOT_VIEWS)
    a, b = Image.open(OUT / "pivots/pivots_front.png"), Image.open(OUT / "pivots/pivots_side.png")
    both = Image.new("RGB", (a.width + b.width, a.height))
    both.paste(a, (0, 0))
    both.paste(b, (a.width, 0))
    both.save(OUT / "pivots.png")

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
              "displays": total, "pivots_to_check": bad, "tags": {n: sorted(t) for n, t in found.items()},
              "unintended_tags": {n: sorted(t) for n, t in wrong.items()},
              "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1])), "animations": list(poses)}
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# The Unbound: rig pivots (session 3)\n\nGenerated by `tools/art/bosses/unbound_s3.py`. "
                                   "Gap = distance from the pivot to the bone's nearest cube, in model units.\n\n"
                                   "| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("bones_with_cubes", "cubes", "displays", "pivots_to_check",
                                                   "unintended_tags", "displays_per_bone")}))


if __name__ == "__main__":
    main()
