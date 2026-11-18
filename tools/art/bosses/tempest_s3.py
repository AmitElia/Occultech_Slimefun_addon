"""The Tempest redesign, session 3: rig and pose test (plan: docs/art/bosses/tempest/overhaul/plan.md).

On top of the session 2 design lock (tempest_s2.py), unchanged in look: the flicker resolver, the quarter-turn saving,
the pivot and tag checks, a display count (cutting it waits for the M6 pass), a flat colour per material so the model can
be seen in game before texturing (the heart, glyphs and eyes full-bright), and the six key poses as BetterModel
animations, with scale keys where a pose scales a bone (the arms' whirl, the twister):
  /bm test occultech_tempest_rig <pose>
A review model only, never shipped.

Run from the repository root: python tools/art/bosses/tempest_s3.py [--no-server]
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid  # noqa: E402
from bosses import archevoker_s2 as a2, archevoker_s3 as a3, volley_crone_s2 as v2  # noqa: E402
from bosses import tempest_s2 as s2  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
TEST_MODELS = ROOT / "run-mythic-b/plugins/BetterModel/models"
RIG = "occultech_tempest_rig"
a3.GLOWING = ("core_glow", "glyph", "eye", "eye_gold")
a3.INTENDED.update({n: {"glow"} for n in ["glow_heart", "glow_eyes", "glow_circlet"] + [f"glow_shard{i}" for i in range(7)]})
_NUDGES = None


def build(pose):
    global _NUDGES
    m = s2.model(pose, RIG)
    if _NUDGES is None:
        rest = s2.rig("nudge_rest")
        s2.snap(rest)
        names = [c.name for c in rest.cubes]
        assert len(names) == len(set(names)), "cube names must be unique"
        _NUDGES = {}
        _resolve(rest, _NUDGES)
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES.items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]
    a3.fold_quarter_turns(m)
    return m


def rest_model():
    """The bind pose: the whole seal, nothing moved (tempest_s2.model would apply a pose)."""
    m = s2.rig(RIG)
    s2.snap(m)
    by_name = {c.name: c for c in m.cubes}
    build("idle")    # fills the nudges
    for name, d in _NUDGES.items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]
    a3.fold_quarter_turns(m)
    return m


def pose_table(rest):
    r_rot = {g.name: g.rotation for g in rest.groups}
    r_org = {g.name: np.array(g.origin) for g in rest.groups}
    poses = {}
    for key in s2.POSES:
        posed = build(key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, r_rot[g.name]))}
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in posed.groups}
        pos = {}
        for g in posed.groups:          # what a bone moved beyond what its parent carried it
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            d = moved[g.name] - parent
            if np.abs(d).max() > 1e-6:
                pos[g.name] = tuple(float(v) for v in d)
        scale = {g.name: tuple(g.scale) for g in posed.groups if getattr(g, "scale", None) is not None
                 and any(abs(s - 1) > 1e-9 for s in g.scale)}
        poses[key] = (rot, pos, scale)
    return poses


def with_scale(bb, model, poses):
    for anim in bb["animations"]:
        _, _, scale = poses[anim["name"]]
        for name, (x, y, z) in scale.items():
            point = {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3)}
            frames = [{"channel": "scale", "data_points": [point], "uuid": _uuid(f"{model.name}/kfs/{anim['name']}/{name}/{t}"),
                       "time": t, "color": -1, "interpolation": "linear"} for t in (0, 0.5)]
            uid = _uuid(f"{model.name}/group/{name}")
            anim["animators"].setdefault(uid, {"name": name, "type": "bone", "keyframes": []})["keyframes"] += frames
    return bb


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = dict(s2.PALETTE)
    v2.PALETTE.update(a2.PALETTE)
    model = rest_model()
    longest = max((max(np.array(c.to) - np.array(c.frm)), c.name) for c in model.cubes)
    assert longest[0] <= 48, longest
    poses = pose_table(model)
    bb, img = a3.flat_bbmodel(model, RIG, s2.HITBOX, [(k, (r, p)) for k, (r, p, _) in poses.items()])
    with_scale(bb, model, poses)
    path = OUT / f"{RIG}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    rep, rows = a3.report(model, s2.HITBOX, {"animations": list(s2.POSES), "longest_cube": [float(longest[0]), longest[1]],
                                             "nudges": len(_NUDGES)})
    (OUT / "report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    summary = {k: rep[k] for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs", "pivots_to_check",
                                   "unintended_tags", "longest_cube", "hitbox_blocks", "nudges")}
    summary["top_display_bones"] = dict(list(rep["displays_per_bone"].items())[:8])
    if "--no-server" not in argv:
        for folder in (SERVER_MODELS, TEST_MODELS):
            if folder.is_dir():
                shutil.copyfile(path, folder / path.name)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
