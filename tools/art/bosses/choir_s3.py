"""The Blaze Choir redesign, session 3: rig and pose test (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

On top of the session 2 design lock (choir_s2.py), unchanged in look: the quarter-turn saving, the pivot and tag checks, a
display count (cutting it waits for the M6 pass), a flat colour per material so the models can be seen in game before
texturing (the fire and mouths full-bright), and the six key poses as BetterModel animations:
  /bm test occultech_blaze_choir_soprano_rig <pose>
Review models only, never shipped.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s3.py [--no-server] <folder>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s2 as a2, archevoker_s3 as a3, choir_s2 as s2, volley_crone_s2 as v2  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
TEST_MODELS = ROOT / "run-mythic-b/plugins/BetterModel/models"
a3.GLOWING = ("white_fire", "fire", "red_fire", "mouth", "blaze")
a3.INTENDED.update({n: {"glow"} for n in ("glow_mouth", "glow_wisp", "glow_sail", "glow_ember", "glow_clapper")})
_NUDGES = {}


def rig_id(singer):
    return f"{s2.ID}{singer}_rig"


def build(singer, pose):
    m = s2.model(singer, pose, preview=False)
    if singer not in _NUDGES:
        rest = s2.model(singer, "idle", preview=False)
        names = [c.name for c in rest.cubes]
        assert len(names) == len(set(names)), "cube names must be unique"
        _NUDGES[singer] = {}
        _resolve(rest, _NUDGES[singer])
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES[singer].items():
        c = by_name[name]
        c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]
    a3.fold_quarter_turns(m)
    return m


def pose_table(singer):
    rest = build(singer, "idle")
    r_rot = {g.name: g.rotation for g in rest.groups}
    r_org = {g.name: np.array(g.origin) for g in rest.groups}
    poses = {}
    for key in s2.POSES:
        posed = build(singer, key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups if any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, r_rot[g.name]))}
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in posed.groups}
        pos = {}
        for g in posed.groups:                                # what a bone moved beyond what its parent carried it
            parent = moved.get(g.parent.name, np.zeros(3))
            d = moved[g.name] - parent
            if np.abs(d).max() > 1e-6:
                pos[g.name] = tuple(float(v) for v in d)
        poses[key] = (rot, pos)
    return poses


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = dict(s2.PALETTE)
    v2.PALETTE.update(a2.PALETTE)
    summary = {}
    for singer in s2.RIGS:
        name, hitbox = rig_id(singer), s2.HITBOX[singer]
        model = build(singer, "idle")
        longest = max((max(np.array(c.to) - np.array(c.frm)), c.name) for c in model.cubes)
        assert longest[0] <= 48, longest
        bb, _ = a3.flat_bbmodel(model, name, hitbox, pose_table(singer).items())
        path = OUT / f"{name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        rep, rows = a3.report(model, hitbox, {"animations": list(s2.POSES), "longest_cube": [float(longest[0]), longest[1]]})
        (OUT / f"{singer}_report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
        (OUT / f"{singer}_pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
        summary[singer] = {k: rep[k] for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs", "pivots_to_check",
                                               "unintended_tags", "longest_cube")}
        if "--no-server" not in argv:
            for folder in (SERVER_MODELS, TEST_MODELS):
                if folder.is_dir():
                    shutil.copyfile(path, folder / path.name)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
