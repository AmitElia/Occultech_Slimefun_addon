"""The Mirrored Magus redesign, session 3: rig and pose test.

On top of the session 2 design lock (magus_s2.py):
- a pivot check: every bone's pivot must sit in its joint;
- a BetterModel tag check: only the intended bones carry a tag;
- a display count: what the model costs to draw (four of him at once: the real one and three decoys);
- a flat colour per material, so he can be seen in game before texturing (the crystal bow and the glint in his
  sockets full-bright);
- the seven key poses, saved as BetterModel animations (`/bm test occultech_mirrored_magus_rig <pose>`). Poses that
  bring him down to the floor (the blink's crouch, the death's heap) sink the hips with a position key.

Output: docs/art/bosses/mirrored_magus/overhaul/s3_rig/, plus the review model copied into
run/plugins/BetterModel/models. It is never shipped.

Run from the repository root: python tools/art/bosses/magus_s3.py
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
from bosses import magus_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_mirrored_magus_rig"
GLOWING = ("eye_glint",)
INTENDED_TAGS = {"hi_head": {"hi"}, "glow_eyes": {"glow"}, "ob_hitbox": {"ob"}}


def pose_table():
    """Per pose: the bones it turns away from rest (absolute rotations), and how far the hips sink."""
    rest = s2.build("rest")
    rest_rot = {g.name: tuple(g.rotation) for g in rest.groups}
    poses = {}
    for key in s2.POSES:
        posed = s2.build("p")
        s2.finish(posed)
        d = s2.pose(posed, key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest_rot[g.name]))}
        pos = {"hips": (0.0, -round(d, 2), 0.0)} if abs(d) > 0.05 else {}
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
    model = s2.build(MODEL_ID)
    s2.finish(model)
    v2.PALETTE.update(s2.PALETTE)
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
    poses = pose_table()
    model, bb, img = build_bbmodel(poses)
    path = OUT / f"{MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), Image.NEAREST).save(OUT / "material_atlas.png")
    if SERVER_MODELS.is_dir():
        shutil.copyfile(path, SERVER_MODELS / path.name)
    boxes = model.render_json(v2.PALETTE)
    for b in boxes:
        b["color"] = [v * 0.5 + 0.45 for v in b["color"]]
    for g in model.groups:
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, p - 1, p + 1, "hitbox"))
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
    wrong = {n: sorted(t) for n, t in found.items() if INTENDED_TAGS.get(n) != t}
    missing = [n for n in INTENDED_TAGS if n not in found]
    total, per_bone = v3.display_count(model)
    report = {"bones_with_cubes": len(per_bone), "cubes": len(model.cubes), "displays": total, "pivots_to_check": bad,
              "unintended_tags": wrong, "missing_tags": missing, "displays_per_bone": per_bone,
              "animations": list(poses)}
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# The Mirrored Magus: rig pivots (session 3)\n\nGenerated by "
                                   "`tools/art/bosses/magus_s3.py`. Gap = distance from the pivot to the bone's "
                                   "nearest cube, in model units.\n\n| Bone | Pivot | Gap | |\n|---|---|---|---|\n"
                                   + "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("bones_with_cubes", "cubes", "displays", "pivots_to_check",
                                                   "unintended_tags", "missing_tags")}))


if __name__ == "__main__":
    main()
