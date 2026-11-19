"""Heartwood Horror, session 3: rig and pose test (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

On top of the session 2 design lock (heartwood_s2.py), unchanged in look: the flicker resolver, the quarter-turn fold,
the pivot and tag checks, the display count, a flat colour per material so it can be seen in game before texturing
(the glows full-bright), and the eight key poses as BetterModel animations, with position keys where a pose moves the
hips:
  /bm test occultech_heartwood_horror_rig <pose>
A review model only, never shipped.

Run from the repository root: python tools/art/bosses/heartwood_s3.py [--no-server]
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s2 as a2, archevoker_s3 as a3, volley_crone_s2 as v2  # noqa: E402
from bosses import heartwood_s2 as s2  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
TEST_MODELS = ROOT / "run-mythic-b/plugins/BetterModel/models"
RIG = "occultech_heartwood_horror_rig"
a3.GLOWING = tuple(s2.GLOW)
_NUDGES = None


def intended(m):
    tags = {"hi_lantern": {"hi"}, "ob_hitbox": {"ob"}}
    tags.update({g.name: {"glow"} for g in m.groups if g.name.startswith("glow_")})
    return tags


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
        rest = s2.build().m
        names = [c.name for c in rest.cubes]
        assert len(names) == len(set(names)), "cube names must be unique"
        _NUDGES = {}
        for c in rest.cubes:          # an inflated cube (the lantern's glow) is drawn that much bigger: check it so
            if c.inflate:
                c.frm = (np.array(c.frm) - c.inflate).tolist()
                c.to = (np.array(c.to) + c.inflate).tolist()
        _resolve(rest, _NUDGES)


def model(key="idle"):
    fill_nudges()
    return nudge(s2.build(key).m)


def wrap(a):
    return (a + 180) % 360 - 180


def pose_table(rest):
    r_rot = {g.name: g.rotation for g in rest.groups}
    r_org = {g.name: np.array(g.origin) for g in rest.groups}
    poses = {}
    for key in s2.POSES:
        m = model(key)
        rot = {}
        for g in m.groups:
            d = [wrap(a - b) for a, b in zip(g.rotation, r_rot[g.name])]
            if any(abs(v) > 1e-6 for v in d):
                rot[g.name] = tuple(r_rot[g.name][i] + d[i] for i in range(3))
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in m.groups}
        pos = {}
        for g in m.groups:
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            d = moved[g.name] - parent
            if np.abs(d).max() > 1e-6:
                pos[g.name] = tuple(float(v) for v in d)
        poses[key] = (rot, pos)
    return poses


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = dict(s2.PALETTE)
    v2.PALETTE.update(a2.PALETTE)
    rest = model()
    a3.INTENDED = intended(rest)
    longest = max((max(np.array(c.to) - np.array(c.frm)), c.name) for c in rest.cubes)
    assert longest[0] <= 48, longest
    poses = pose_table(rest)
    hitbox = s2.hitbox_bounds(s2.build().m)
    bb, img = a3.flat_bbmodel(rest, RIG, hitbox, list(poses.items()))
    path = OUT / f"{RIG}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    img.resize((256, 256), 0).save(OUT / "material_atlas.png")
    rep, rows = a3.report(rest, hitbox, {"animations": list(s2.POSES), "longest_cube": [float(longest[0]), longest[1]],
                                         "nudges": len(_NUDGES),
                                         "position_keys": {k: sorted(p) for k, (_, p) in poses.items()}})
    (OUT / "report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n",
                                   encoding="utf-8")
    summary = {k: rep[k] for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs", "pivots_to_check",
                                   "unintended_tags", "longest_cube", "hitbox_blocks", "nudges")}
    summary["top_display_bones"] = dict(list(rep["displays_per_bone"].items())[:10])
    if "--no-server" not in argv:
        for folder in (SERVER_MODELS, TEST_MODELS):
            if folder.is_dir():
                shutil.copyfile(path, folder / path.name)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
