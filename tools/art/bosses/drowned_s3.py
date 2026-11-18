"""The Drowned Elder redesign, session 3: rig and pose test (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

On top of the session 2 design lock (drowned_s2.py), unchanged in look: the flicker resolver, the quarter-turn saving,
the pivot and tag checks, a display count (cutting it waits for the M6 pass), a flat colour per material so the model can
be seen in game before texturing (the eyes full-bright), and the six key poses as BetterModel animations, with a
position key on `base` (the whole body moves onto the pose's curve) and scale keys on the hood's webs:
  /bm test occultech_drowned_elder_rig <pose>
The four `ob_` hitboxes ride in the rig as real bones (the head, segments 3, 6 and 9) with untextured cubes.
A review model only, never shipped.

Run from the repository root: python tools/art/bosses/drowned_s3.py [--no-server]
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s2 as a2, archevoker_s3 as a3, volley_crone_s2 as v2  # noqa: E402
from bosses import drowned_s2 as s2  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402
from bosses.tempest_s3 import with_scale  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
TEST_MODELS = ROOT / "run-mythic-b/plugins/BetterModel/models"
RIG = "occultech_drowned_elder_rig"
HITBOXES = list(s2.HITBOXES)
a3.GLOWING = ("glow", "eye")
a3.INTENDED.update({n: {"glow"} for n in ["glow_eye"] + [f"glow_eye{i}" for i in s2.EYES]})
a3.INTENDED.update({n: {"ob"} for n in HITBOXES})
a3.add_hitbox = lambda bb, *args, **kw: bb          # the hitboxes are bones of the rig already
_NUDGES = None


def nudge(m):
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES.items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]
    a3.fold_quarter_turns(m)
    return m


def fill_nudges():
    global _NUDGES
    if _NUDGES is None:
        rest = s2.rig("nudge_rest")
        s2.snap(rest)
        names = [c.name for c in rest.cubes]
        assert len(names) == len(set(names)), "cube names must be unique"
        _NUDGES = {}
        _resolve(rest, _NUDGES)


def build(pose):
    fill_nudges()
    return nudge(s2.model(pose, RIG))


def rest_model():
    fill_nudges()
    m = s2.rig(RIG)
    s2.snap(m)
    return nudge(m)


def wrap(a):
    return (a + 180) % 360 - 180


def pose_table(rest):
    r_rot = {g.name: g.rotation for g in rest.groups}
    r_org = {g.name: np.array(g.origin) for g in rest.groups}
    poses = {}
    for key in s2.POSES:
        posed = build(key)
        rot = {}
        for g in posed.groups:
            d = [wrap(a - b) for a, b in zip(g.rotation, r_rot[g.name])]
            if any(abs(v) > 1e-6 for v in d):
                rot[g.name] = tuple(r_rot[g.name][i] + d[i] for i in range(3))
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in posed.groups}
        pos = {}
        for g in posed.groups:
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            d = moved[g.name] - parent
            if np.abs(d).max() > 1e-6:
                pos[g.name] = tuple(float(v) for v in d)
        scale = {g.name: tuple(g.scale) for g in posed.groups if getattr(g, "scale", None) is not None
                 and any(abs(s - 1) > 1e-9 for s in g.scale)}
        poses[key] = (rot, pos, scale)
    return poses


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = dict(s2.PALETTE, hitbox=(235, 70, 70))      # opaque: the atlas never holds a half-clear texel
    v2.PALETTE.update(a2.PALETTE)
    model = rest_model()
    shown = [c for c in model.cubes if c.mat != "hitbox"]
    longest = max((max(np.array(c.to) - np.array(c.frm)), c.name) for c in shown)
    assert longest[0] <= 48, longest
    poses = pose_table(model)
    head = next(v for k, v in s2.HITBOXES.items() if k == "ob_head")
    bb, img = a3.flat_bbmodel(model, RIG, ((0, 0, 0), head[2]), [(k, (r, p)) for k, (r, p, _) in poses.items()])
    with_scale(bb, model, poses)
    hit = {c.name for c in model.cubes if c.mat == "hitbox"}
    for e in bb["elements"]:
        if e["name"] in hit:
            e["faces"] = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in e["faces"]}
            e["light_emission"] = 0
    path = OUT / f"{RIG}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    rep, rows = a3.report(model, ((0, 0, 0), head[2]), {"animations": list(s2.POSES),
                                                         "longest_cube": [float(longest[0]), longest[1]],
                                                         "nudges": len(_NUDGES)})
    rep.pop("hitbox_blocks", None)
    rep["tags"].pop("ob_hitbox", None)
    rep["unintended_tags"].pop("ob_hitbox", None)
    for name in HITBOXES:                                   # hitboxes are entities, not displays
        rep["displays"] -= rep["displays_per_bone"].pop(name, 0)
    rep["bones_with_cubes"] -= len(HITBOXES)
    rep["cubes"] = len(shown)
    rep["hitboxes_blocks"] = {k: [round(s / 16, 2) for s in v[2]] for k, v in s2.HITBOXES.items()}
    (OUT / "report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    summary = {k: rep[k] for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs", "pivots_to_check",
                                   "unintended_tags", "longest_cube", "hitboxes_blocks", "nudges")}
    summary["top_display_bones"] = dict(list(rep["displays_per_bone"].items())[:10])
    if "--no-server" not in argv:
        for folder in (SERVER_MODELS, TEST_MODELS):
            if folder.is_dir():
                shutil.copyfile(path, folder / path.name)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
