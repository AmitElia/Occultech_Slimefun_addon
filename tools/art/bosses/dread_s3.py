"""Dread Riders, session 3: rig and pose test (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

On top of the session 2 design lock (dread_s2.py), unchanged in look:
- the flicker resolver (faces that share a plane are nudged apart by a fraction of a texel);
- the quarter-turn fold (single-axis 22.5-degree multiples stored so BetterModel keeps them in the bone's display);
- long cubes split into pieces of at most 46 units (an item model stops at 48): the lance and the banner pole;
- pivot and tag checks, the display count;
- one flat colour per material so the rigs can be seen in game before texturing (the glows full-bright);
- the key poses as BetterModel animations, the same names on a pair's mount and rider, with a position key where the
  mount is lifted off the floor and scale keys on the drawn bowstring:
    /bm test occultech_dread_vanguard_mount_rig charge     /bm test occultech_dread_vanguard_rig charge
Review models only, never shipped. The riders' models have their origin at the seat.

Run from the repository root: python tools/art/bosses/dread_s3.py [--no-server]
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
from bosses import dread_s2 as s2  # noqa: E402
from bosses.coven_s2 import _resolve  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
TEST_MODELS = ROOT / "run-mythic-b/plugins/BetterModel/models"
LIMIT = 46
# session 5 review ("the riders are too big compared to the player"): the whole pair is shown at 0.75. The scale is
# baked into the geometry after the UVs are laid out, so every face keeps its whole-texel island: the boss's texel
# density is 4/3 per unit (a texel is 0.75 of a vanilla pixel) everywhere, one density for the whole boss.
SCALE = 0.75


def scale_model(m, k=SCALE):
    for c in m.cubes:
        c.frm, c.to, c.origin = [(np.array(v) * k).tolist() for v in (c.frm, c.to, c.origin)]
    for g in m.groups:
        g.origin = (np.array(g.origin) * k).tolist()
    _resolve(m, {})                  # the resolver's nudges shrink with the model: part them again at the new size


def scaled_hitbox(hb, k=SCALE):
    return None if hb is None else tuple(tuple(float(v) * k for v in p) for p in hb)


def scaled_poses(poses, k=SCALE):
    return {key: (rot, {n: tuple(float(v) * k for v in p) for n, p in pos.items()}, sc)
            for key, (rot, pos, sc) in poses.items()}


def wrap(a):
    return (a + 180) % 360 - 180


def split_long(m):
    """Cubes longer than LIMIT along any side become equal pieces along that side (same pivot and turn, so the shape
    is unchanged)."""
    split = []
    for c in list(m.cubes):
        lo, hi = np.array(c.frm), np.array(c.to)
        size = hi - lo
        i = int(np.argmax(size))
        if size[i] <= LIMIT:
            continue
        n = int(np.ceil(size[i] / LIMIT))
        idx = c.group.children.index(c)
        c.group.children.remove(c)
        m.cubes.remove(c)
        for k in range(n):
            a, b = lo.copy(), hi.copy()
            a[i] = lo[i] + size[i] * k / n
            b[i] = lo[i] + size[i] * (k + 1) / n
            piece = c.group.cube(f"{c.name}_p{k}", a, b, c.mat, c.rotation, c.origin)
            c.group.children.remove(piece)
            c.group.children.insert(idx + k, piece)
        split.append((c.name, round(float(size[i]), 1), n))
    return split


def to_seat(rm, seat):
    for g in rm.groups:
        g.origin = (np.array(g.origin) - seat).tolist()
    for c in rm.cubes:
        c.frm, c.to, c.origin = [(np.array(v) - seat).tolist() for v in (c.frm, c.to, c.origin)]


def snapshot(m):
    return {g.name: list(g.rotation) for g in m.groups}


def diff(m, bind):
    rot = {}
    for g in m.groups:
        d = [wrap(a - b) for a, b in zip(g.rotation, bind[g.name])]
        if any(abs(v) > 1e-6 for v in d):
            rot[g.name] = tuple(bind[g.name][i] + d[i] for i in range(3))
    scale = {g.name: tuple(g.scale) for g in m.groups if getattr(g, "scale", None) is not None}
    return rot, scale


def with_scale(bb, model_name, poses):
    for anim in bb["animations"]:
        _, _, scale = poses[anim["name"]]
        for name, (x, y, z) in scale.items():
            point = {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3)}
            frames = [{"channel": "scale", "data_points": [point], "uuid": _uuid(f"{model_name}/kfs/{anim['name']}/{name}/{t}"),
                       "time": t, "color": -1, "interpolation": "linear"} for t in (0, 0.5)]
            uid = _uuid(f"{model_name}/group/{name}")
            anim["animators"].setdefault(uid, {"name": name, "type": "bone", "keyframes": []})["keyframes"] += frames


def finish(m):
    nudges = {}
    _resolve(m, nudges)
    a3.fold_quarter_turns(m)
    return nudges, split_long(m)


def intended(m):
    tags = {"ob_hitbox": {"ob"}, "hi_head": {"hi"}}
    tags.update({g.name: {"glow"} for g in m.groups if g.name.startswith("glow_")})
    return tags


def write(m, name, hitbox, poses, report_extra):
    a3.INTENDED = intended(m)
    bb, img = a3.flat_bbmodel(m, name, hitbox or ((0, 0, 0), (1, 1, 1)),
                              [(k, (rot, pos)) for k, (rot, pos, _) in poses.items()])
    if hitbox is None:                       # the mounts can't be hurt: no hitbox of their own
        bb["elements"] = [e for e in bb["elements"] if e["name"] != "hitbox"]
        bb["groups"] = [g for g in bb["groups"] if g["name"] != "ob_hitbox"]
        bb["outliner"] = [o for o in bb["outliner"] if not (isinstance(o, dict) and o.get("name") == "ob_hitbox")]
    with_scale(bb, name, poses)
    path = OUT / f"{name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    rep, rows = a3.report(m, hitbox or ((0, 0, 0), (0, 0, 0)), report_extra)
    if hitbox is None:
        rep.pop("hitbox_blocks", None)
        rep["tags"].pop("ob_hitbox", None)
        rep["unintended_tags"].pop("ob_hitbox", None)
    longest = max((float(max(np.array(c.to) - np.array(c.frm))), c.name) for c in m.cubes)
    rep["longest_cube"] = list(longest)
    assert longest[0] <= 48, longest
    return path, rep, rows, img


def build_pair(kind):
    """The pair's two review rigs, finished (resolver, fold, split) and posed tables: (mount, rider, frame, seat,
    rider hitbox in seat space, mount poses, rider poses, per-model nudges and splits)."""
    mm, f = s2.mount(kind)
    rm, info = s2.rider_model(kind, f)
    if kind == "outrider":
        s2.add_arrow(rm, info, s2.RIDER_POSES["outrider"]["draw"])
    s2.snap(mm)
    s2.snap(rm)
    hitbox = s2.hitbox_bounds(f, rm)
    seat = f["seat"]
    # the key poses, from the session 2 rigs (before the resolver and fold, which don't touch bones)
    s2.pose_mount(mm, f, s2.MOUNT_POSES[s2.REST])
    s2.reset(rm)
    mbind, rbind = snapshot(mm), snapshot(rm)
    mposes, rposes = {}, {}
    for key, mpose, rpose in s2.PAIRS[kind]:
        lift = s2.pose_mount(mm, f, s2.MOUNT_POSES[mpose])
        rot, scale = diff(mm, mbind)
        mposes[key] = (rot, {"base": (0.0, float(lift), 0.0)} if abs(lift) > 1e-6 else {}, scale)
        s2.pose_rider(rm, info, s2.RIDER_POSES[kind][rpose])
        rot, scale = diff(rm, rbind)
        rposes[key] = (rot, {}, scale)
    s2.pose_mount(mm, f, s2.MOUNT_POSES[s2.REST])
    s2.reset(rm)
    s2.hide_arrow(rm)
    for model, part in ((mm, "mount"), (rm, "rider")):
        for c in [c for c in model.cubes if c.name in s2.DECALS[part]]:
            c.group.children.remove(c)
            model.cubes.remove(c)
    to_seat(rm, seat)
    hit = ((hitbox[0][0], hitbox[0][1] - seat[1], hitbox[0][2] - seat[2]),
           (hitbox[1][0], hitbox[1][1] - seat[1], hitbox[1][2] - seat[2]))
    done = {"mount": finish(mm), "rider": finish(rm)}
    return dict(mount=mm, rider=rm, frame=f, seat=seat, hitbox=hit, mount_poses=mposes, rider_poses=rposes, done=done,
                info=info)


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    a2.PALETTE = dict(s2.PALETTE)
    v2.PALETTE.update(a2.PALETTE)
    a3.GLOWING = ("cyan", "crimson")
    summary, paths = {}, []
    for kind in ("vanguard", "outrider"):
        P = build_pair(kind)
        scale_model(P["mount"])
        scale_model(P["rider"])
        mm, rm = P["mount"], P["rider"]
        hit, mposes, rposes = scaled_hitbox(P["hitbox"]), scaled_poses(P["mount_poses"]), scaled_poses(P["rider_poses"])
        for model, name, hb, poses in ((mm, f"occultech_dread_{kind}_mount_rig", None, mposes),
                                       (rm, f"occultech_dread_{kind}_rig", hit, rposes)):
            nudges, split = P["done"]["mount" if model is mm else "rider"]
            path, rep, rows, img = write(model, name, hb, poses, {
                "animations": list(poses), "nudges": len(nudges), "split": split,
                "position_keys": {k: sorted(p) for k, (_, p, _) in poses.items() if p},
                "scale_keys": {k: sorted(s) for k, (_, _, s) in poses.items() if s}})
            (OUT / f"{name}_report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
            (OUT / f"{name}_pivots.md").write_text("| Bone | Pivot | Gap | |\n|---|---|---|---|\n" + "\n".join(rows) + "\n",
                                                   encoding="utf-8")
            summary[name] = {k: rep.get(k) for k in ("cubes", "bones_with_cubes", "displays", "flicker_pairs",
                                                      "pivots_to_check", "unintended_tags", "longest_cube",
                                                      "hitbox_blocks", "nudges", "split")}
            summary[name]["top_display_bones"] = dict(list(rep["displays_per_bone"].items())[:6])
            paths.append(path)
    if "--no-server" not in argv:
        for folder in (SERVER_MODELS, TEST_MODELS):
            if folder.is_dir():
                for p in paths:
                    shutil.copyfile(p, folder / p.name)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
