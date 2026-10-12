"""Witch Coven redesign, session 3: rig and pose test of the three sisters.

On top of the session 2 design lock (coven_s2.py), this session adds, per sister:
- a pivot check: every bone's pivot must sit in its joint;
- a BetterModel tag check: only the intended bones carry a tag;
- a display count: what the model costs to draw;
- a flat colour per material, so the sister can be seen in game before texturing (the brew drawn full-bright);
- six test poses, saved as BetterModel animations (`/bm test occultech_coven_<vessel>_rig <pose>`).

Output: docs/art/bosses/witch_coven/overhaul/s3_rig/, plus the review models copied into run/plugins/BetterModel/models.
They are never shipped.

Run from the repository root: python tools/art/bosses/coven_s3.py
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
from bosskit import sheet  # noqa: E402
from bosses import coven_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
GLOWING = ("glow_", "hot_", "steam_")
INTENDED_TAGS = {"h_head": {"h"}, "glow_brew": {"glow"}, "glow_cast": {"glow"}, "ob_hitbox": {"ob"}}


def model_id(vessel):
    return f"occultech_coven_{vessel}_rig"


def pose_table(vessel, role):
    """Absolute rotations per pose: the bones each pose turns away from rest."""
    rest = {g.name: g.rotation for g in s2.build(vessel, role).groups}
    poses = {}
    for key, (_, per) in s2.POSES.items():
        posed = s2.build(vessel, role, per.get(vessel, {}))
        poses[key] = {g.name: tuple(g.rotation) for g in posed.groups
                      if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest[g.name]))}
    return poses


def build_bbmodel(vessel, role, poses):
    model = s2.build(vessel, role)
    model.name = model_id(vessel)
    v3.s2.PALETTE = s2.PALETTE   # the atlas swatches read Volley's module palette
    img, uv, png = v3.material_atlas(model)
    texture = {"name": f"{model.name}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(model.name + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat.startswith(GLOWING):
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{model.name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "",
                         "animators": v3.keyframes(model, pose)}
                        for key, pose in poses.items()]
    return model, bb, img


def main():
    if OUT.exists():                              # regenerate everything but the hand-written README
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for vessel, role, title in s2.SISTERS:
        out = OUT / vessel
        poses = pose_table(vessel, role)
        model, bb, img = build_bbmodel(vessel, role, poses)
        out.mkdir()
        path = out / f"{model.name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        img.resize((256, 256), Image.NEAREST).save(out / "material_atlas.png")
        if SERVER_MODELS.is_dir():
            shutil.copyfile(path, SERVER_MODELS / path.name)

        # pivots: a red marker at every bone's pivot, over the model in pale flat colours
        boxes = model.render_json(s2.PALETTE)
        for b in boxes:
            b["color"] = [v * 0.5 + 0.45 for v in b["color"]]
        for g in model.groups:
            p = v3.world_pivot(g)
            boxes.append(v2.box_json("pivot_" + g.name, p - 1.2, p + 1.2, "hitbox"))
        v2.run_blender(boxes, out / "pivots", v3.PIVOT_VIEWS)
        a, b = Image.open(out / "pivots/pivots_front.png"), Image.open(out / "pivots/pivots_side.png")
        both = Image.new("RGB", (a.width + b.width, a.height))
        both.paste(a, (0, 0))
        both.paste(b, (a.width, 0))
        both.save(out / "pivots.png")

        rows, bad = v3.pivot_report(model)
        found = {}
        for g in model.groups:
            tags = {w for w in g.name.lower().split("_") if w in v3.BETTERMODEL_TAGS}
            if tags:
                found[g.name] = tags
        found["ob_hitbox"] = {"ob"}
        wrong = {k: v for k, v in found.items() if INTENDED_TAGS.get(k) != v}
        total, per_bone = v3.display_count(model)
        report[vessel] = {"bones": len(model.groups) + 1, "bones_with_cubes": len(per_bone), "cubes": len(model.cubes),
                          "displays": total, "pivots_to_check": bad, "tags": {k: sorted(v) for k, v in found.items()},
                          "unintended_tags": {k: sorted(v) for k, v in wrong.items()},
                          "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1])),
                          "animations": list(poses)}
        (out / "pivots.md").write_text(f"# Witch Coven, {title}: rig pivots (session 3)\n\nGenerated by "
                                       "`tools/art/bosses/coven_s3.py`. Gap = distance from the pivot to the bone's "
                                       "nearest cube, in model units.\n\n| Bone | Pivot | Gap | |\n|---|---|---|---|\n"
                                       + "\n".join(rows) + "\n", encoding="utf-8")
        print(vessel, json.dumps({k: report[vessel][k] for k in ("bones_with_cubes", "cubes", "displays",
                                                                 "pivots_to_check", "unintended_tags")}))
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # the six test poses of each sister, from the design lock's renders
    rows = []
    for vessel, _, _ in s2.SISTERS:
        rows.append(Image.open(ROOT / "docs/art/bosses/witch_coven/overhaul/s2_design" / vessel / "poses.png"))
    w = max(r.width for r in rows)
    img = Image.new("RGB", (w, sum(r.height for r in rows)), sheet.BG)
    y = 0
    for r in rows:
        img.paste(r, (0, y))
        y += r.height
    img.save(OUT / "poses.png")


if __name__ == "__main__":
    main()
