"""The Tidebreaker redesign, session 3: rig and pose test (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

On top of the session 2 design lock (tide_s2.py), unchanged in look: the quarter-turn saving, the pivot and tag checks,
a display count (cutting it waits for the M6 pass), a flat colour per material so both models can be seen in game before
texturing (the lantern full-bright), and the seven key poses as BetterModel animations:
  /bm test occultech_tidebreaker_rig <pose>
  /bm test occultech_tidebreaker_mount_rig <pose>
Both models play the same pose names. Review models only, never shipped.

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_s3.py [--no-server] <folder>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosses import archevoker_s2 as a2, archevoker_s3 as a3, tide_s2 as s2, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MOUNT_ID, RIDER_ID = "occultech_tidebreaker_mount_rig", "occultech_tidebreaker_rig"
MOUNT_HITBOX = ((-20.0, 0.0, -30.0), (20.0, 56.0, 40.0))
RIDER_HITBOX = ((-10.0, 0.0, -8.0), (10.0, 52.0, 8.0))
a3.GLOWING = ("glow",)
a3.INTENDED.update({"glow_lantern": {"glow"}})
_NUDGES = {}


def _raw(kind):
    if kind == "mount":
        return s2.mount_rig("tide_mount")
    m = Model("tide_rider")
    s2.viking_rig(m.group("carrier", (0, 0, 0)), (0, 0, 0), False)
    return m


def build(kind, key):
    m = _raw(kind)
    (s2.pose_mount if kind == "mount" else s2.pose_rider)(m, s2.POSES[key][1])
    s2.snap(m)
    if kind not in _NUDGES:
        rest = _raw(kind)
        (s2.pose_mount if kind == "mount" else s2.pose_rider)(rest, s2.POSES["idle"][1])
        s2.snap(rest)
        names = [c.name for c in rest.cubes]
        assert len(names) == len(set(names)), "cube names must be unique"
        _NUDGES[kind] = {}
        _resolve(rest, _NUDGES[kind])
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES[kind].items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]
    a3.fold_quarter_turns(m)
    return m


def pose_table(kind):
    rest = {g.name: g.rotation for g in build(kind, "idle").groups}
    poses = {}
    for key, (_, spec) in s2.POSES.items():
        posed = build(kind, key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest[g.name]))}
        pos = {}
        if kind == "mount":
            if spec["base"][1]:
                pos["base"] = (0.0, float(spec["base"][1]), 0.0)
            for side in s2.SIDES.values():
                if spec.get("lid"):
                    pos[f"lid_{side}"] = (0.0, float(spec["lid"]), 0.0)
                if spec.get("pupil"):
                    pos[f"pupil_{side}"] = tuple(float(v) for v in spec["pupil"])
        poses[key] = (rot, pos)
    return poses


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = {**s2.PALETTE, **s2.tf2.PAL, "net": s2.PALETTE["net"][:3]}       # flat colours; the net's holes are texture
    v2.PALETTE.update(a2.PALETTE)
    summary = {}
    for kind, name, hitbox in (("mount", MOUNT_ID, MOUNT_HITBOX), ("rider", RIDER_ID, RIDER_HITBOX)):
        model = build(kind, "idle")
        longest = max((max(np.array(c.to) - np.array(c.frm)), c.name) for c in model.cubes)
        assert longest[0] <= 48, longest
        bb, _ = a3.flat_bbmodel(model, name, hitbox, pose_table(kind).items())
        path = OUT / f"{name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        rep, rows = a3.report(model, hitbox, {"animations": list(s2.POSES), "longest_cube": [float(longest[0]), longest[1]]})
        (OUT / f"{kind}_report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
        (OUT / f"{kind}_pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
        summary[kind] = {k: rep[k] for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs", "pivots_to_check",
                                             "unintended_tags", "longest_cube")}
        if "--no-server" not in argv and SERVER_MODELS.is_dir():
            shutil.copyfile(path, SERVER_MODELS / path.name)
        v2.run_blender(build(kind, "idle").render_json(v2.PALETTE), OUT / kind,
                       [{"name": "q", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3, "dist": 10, "target_z": 2.2}])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main(sys.argv[1:])
