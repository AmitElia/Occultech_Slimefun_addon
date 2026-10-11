"""Brood Mother redesign, session 3: rig and pose test.

On top of the session 2 blockout, this session adds:
- a pivot check: every bone's pivot must sit in its joint (the flame bones are moved onto a flame, so a flicker
  scales them in place);
- a BetterModel tag check: only the intended bones carry a tag;
- a display count: what the model costs to draw;
- a flat colour per material, so the model can be seen in game before texturing;
- six test poses, saved as BetterModel animations (`/bm test occultech_brood_mother_rig <pose>`).

Output: docs/art/bosses/brood_mother/overhaul/s3_rig/, plus the review model copied into run/plugins/BetterModel/models.
It is never shipped.

Run from the repository root: python tools/art/bosses/brood_s3.py
"""
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
from bosses import brood_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_brood_mother_rig"
GLOW_BONES = ("glow_pile_flames", "glow_thorax_flames", "glow_head_flames", "glow_flank_flames",
              "glow_leg_r1_knee", "glow_leg_l0_knee", "glow_leg_l2_knee")
INTENDED_TAGS = dict({"h_head": {"h"}, "ob_hitbox": {"ob"}}, **{g: {"glow"} for g in GLOW_BONES})


def threat(groups):
    """The tarantula's threat display: reared on the back legs, the two front pairs lifted, head up, fangs bared."""
    rotate = s2.rotate
    rotate(groups, "h_head", (18, 0, 0))
    s2.front_legs(groups, 22, 34, 14)
    for leg in ("leg_r1", "leg_l1"):
        rotate(groups, f"{leg}_1", (0, 0, 14))
        rotate(groups, f"{leg}_3", (0, 0, 18))
    s2.jaws_open(groups, 32)
    rotate(groups, "abdomen", (8, 0, 0))


TITLES = dict(s2.POSES, threat="threat: reared up, the front legs lifted, fangs bared (spawn and phase moments)")


def rigged():
    """The session 2 blockout with every flame bone's pivot moved onto one of its flames."""
    model = s2.build()
    for g in model.groups:
        if g.name in GLOW_BONES:
            flames = [c for c in g.children if not hasattr(c, "children")]
            f = flames[0]   # the flame's centre where its own lean puts it
            centre = (np.array(f.frm) + np.array(f.to)) / 2
            g.origin = (pivot_matrix(f.origin, f.rotation) @ np.array([*centre, 1.0]))[:3].tolist()
    return model


def posed(key):
    model = rigged()
    groups = {g.name: g for g in model.groups}
    if key == "threat":
        threat(groups)
    else:
        s2.pose(model, key)
    return model


def pose_table():
    """Absolute rotations per pose: the bones each pose turns away from rest."""
    rest = {g.name: g.rotation for g in rigged().groups}
    poses = {}
    for key in TITLES:
        poses[key] = {g.name: tuple(g.rotation) for g in posed(key).groups
                      if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest[g.name]))}
    return poses


def build_bbmodel(poses):
    model = rigged()
    model.name = MODEL_ID
    v3.s2.PALETTE = s2.PALETTE   # the atlas swatches read Volley's module palette
    img, uv, png = v3.material_atlas(model)
    texture = {"name": f"{MODEL_ID}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + __import__("base64").b64encode(png).decode()}
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat == "flame":
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "",
                         "animators": v3.keyframes(model, pose)}
                        for key, pose in poses.items()]
    return model, bb, img


def main():
    poses = pose_table()
    model, bb, img = build_bbmodel(poses)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), Image.NEAREST).save(OUT / "material_atlas.png")
    if SERVER_MODELS.is_dir():
        shutil.copyfile(path, SERVER_MODELS / path.name)

    boxes = model.render_json(s2.PALETTE)
    for b in boxes:
        b["color"] = [v * 0.5 + 0.45 for v in b["color"]]
    for g in model.groups:
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, p - 1.6, p + 1.6, "hitbox"))
    v2.run_blender(boxes, OUT / "pivots", v3.PIVOT_VIEWS)
    a, b = Image.open(OUT / "pivots/pivots_front.png"), Image.open(OUT / "pivots/pivots_side.png")
    both = Image.new("RGB", (a.width + b.width, a.height))
    both.paste(a, (0, 0))
    both.paste(b, (a.width, 0))
    both.save(OUT / "pivots.png")

    for key in poses:
        v2.run_blender(posed(key).render_json(s2.PALETTE), OUT / "poses" / key, s2.POSE_VIEWS)
    sheet.compare_sheet(OUT / "poses", [(k, "") for k in poses], OUT / "poses.png",
                        heading="Brood Mother - six test poses (session 3)")

    rows, bad = v3.pivot_report(model)
    tags, _ = v3.tag_report(model)
    wrong = {k: v for k, v in tags.items() if INTENDED_TAGS.get(k) != v}
    total, per_bone = v3.display_count(model)
    report = {"bones": len(model.groups) + 1, "bones_with_cubes": len(per_bone), "cubes": len(model.cubes),
              "hair_cards": sum(1 for c in model.cubes if c.mat == "hair"), "displays": total,
              "pivots_to_check": bad, "tags": {k: sorted(v) for k, v in tags.items()},
              "unintended_tags": {k: sorted(v) for k, v in wrong.items()},
              "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1])), "animations": list(poses)}
    (OUT / "rig_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# Brood Mother rig pivots (session 3)\n\nGenerated by `tools/art/bosses/brood_s3.py`."
                                   " Gap = distance from the pivot to the bone's nearest cube, in model units.\n\n"
                                   "| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("bones", "bones_with_cubes", "cubes", "displays", "pivots_to_check",
                                             "unintended_tags")}))


if __name__ == "__main__":
    main()
