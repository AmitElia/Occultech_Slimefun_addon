"""The Blaze Choir redesign, session 7: animation (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

Each clip is a few of session 2's whole poses at key times, plus small additive moves (a wind chime's sway, the
tower's spin). All three singers carry the same clip names, so the fight plays one name on whichever singer acts.

Timed to BlazeChoir.java:
  idle      3.0 s loop   breathing: the chime's pipes sway out of step, the cymbals bob, the bell rocks, the
                         Alto's tower spins like a blaze's rods
  spawn     2.0 s once   rising out of the circle, the instrument unfolding
  strike    0.8 s once   the fireball on the beat: a wind-up, then the strike at 0.5 s (the fireball leaves then)
  shield    0.6 s hold   the shield arrives: the instrument closes and stays closed
  unshield  0.6 s once   the shield passes on: it opens again
  chorus    2.0 s once   the flame circles: gathering through the 1.5 s warning, the full chorus at 1.5 s (the
                         eruption), then back
  last      1.0 s loop   the last singer's idle: its instrument flailing
  flinch    0.4 s once   hit
  death     2.5 s hold   a last spasm, then the instrument falls apart and sinks

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s7.py <folder>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s7 as a7, choir_s2 as s2, choir_s3 as s3, choir_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/blaze_choir/overhaul/s6_variants"
a7.OUT = OUT
a7.s4.ZONES, a7.s4.GLOWING = s4.ZONES, s4.FULL_BRIGHT
CONTACT = {"strike": 0.5, "chorus": 1.5}
OVERRIDE = ("spawn", "strike", "shield", "unshield", "chorus", "last", "flinch", "death")
TAU = 2 * math.pi


def wrap(d):
    return (d + 180) % 360 - 180


_TABLES = {}


def table(singer, pose):
    """A named pose as (absolute rotation, offset from its parent) per bone."""
    k = (singer, pose)
    if k not in _TABLES:
        rest, posed = s3.build(singer, "idle"), s3.build(singer, pose)
        r_org = {g.name: np.array(g.origin) for g in rest.groups}
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in posed.groups}
        rot, pos = {}, {}
        for g in posed.groups:
            rot[g.name] = np.array(g.rotation, float)
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            pos[g.name] = moved[g.name] - parent
        _TABLES[k] = (rot, pos)
    return _TABLES[k]


# ---- the additive moves ----------------------------------------------------------------------------------------------

def sway(singer, ph, amp=1.0):
    """Small life on top of a pose: bone -> (rotation, position)."""
    out = {}
    if singer == "soprano":
        for i, (a, _) in enumerate(s2.TUBES):
            s = math.sin(ph + i * 0.8) * 4 * amp
            ar = math.radians(a)
            out[f"tube{i}"] = ((s * math.cos(ar), 0, -s * math.sin(ar)), (0, 0, 0))
        out["striker"] = ((math.sin(ph + 1.3) * 3 * amp, 0, math.cos(ph) * 3 * amp), (0, 0, 0))
        out["hi_head"] = ((0, 0, 0), (0, math.sin(ph) * 1.2 * amp, 0))
    elif singer == "alto":
        for sx, side in s2.SIDES.items():
            out[f"cymbal_{side}"] = ((0, 0, 0), (0, math.sin(ph + (0 if sx > 0 else math.pi)) * 1.5 * amp, 0))
        out["hi_head"] = ((0, 0, 0), (0, math.sin(ph + 0.6) * 1.0 * amp, 0))
    else:
        out["bell"] = ((0, 0, math.sin(ph) * 4 * amp), (0, 0, 0))
        out["clapper"] = ((0, 0, -math.sin(ph - 0.5) * 6 * amp), (0, 0, 0))
        out["wheel"] = ((0, 0, -math.sin(ph) * 6 * amp), (0, 0, 0))
        out["hi_head"] = ((0, 0, 0), (0, math.sin(ph + 0.8) * 1.0 * amp, 0))
    return out


def wind_up(singer):
    """The anticipation before the strike: the opposite of it."""
    return {"soprano": {"hi_head": ((-6, 0, 0), (0, -1.5, 0))},
            "alto": {"hi_head": ((-6, 0, 0), (0, -1, 0))},
            "bass": {"bell": ((0, 0, -10), (0, 0, 0)), "clapper": ((0, 0, 14), (0, 0, 0)), "wheel": ((0, 0, 12), (0, 0, 0)),
                     "hi_head": ((-6, 0, 0), (0, 0, 0))}}[singer]


def kick(singer):
    return {"hi_head": ((-14, 0, 8), (0, 1, 0)), **({"bell": ((0, 0, 7), (0, 0, 0))} if singer == "bass" else {})}


def sunk(dy):
    return {"base": ((0, 0, 0), (0, dy, 0))}


# ---- the clips ---------------------------------------------------------------------------------------------------------

def clips(singer):
    """name -> (length, loop, [(t, pose, extras)])."""
    idle = [(t, "idle", sway(singer, TAU * t / 3)) for t in (0, 0.75, 1.5, 2.25, 3.0)]
    last = [(t, "last", sway(singer, TAU * t, 2.5)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    spread = {"soprano": "strike", "alto": "idle", "bass": "idle"}[singer]
    over = {"wheel": ((0, 0, 0), (0, 26, -14))} if singer == "bass" else None     # the wheel goes over the head, not through it
    closed = "idle" if singer == "bass" else "shielded"                           # the Bass gathers without its grille
    gather = wind_up(singer) if singer == "bass" else {}
    return {
        "idle": (3.0, "loop", idle),
        "spawn": (2.0, "once", [(0, closed, sunk(-40)), (0.8, closed, sunk(-14)), (1.4, spread, sunk(2)), (2.0, "idle", {})]),
        "strike": (0.8, "once", [(0, "idle", {}), (0.35, "idle", wind_up(singer)), (0.5, "strike", {}), (0.62, "strike", {}),
                                 (0.8, "idle", {})]),
        "shield": (0.6, "hold", [(0, "idle", {}), *([(0.25, "idle", over)] if over else []), (0.45, "shielded", {}), (0.6, "shielded", {})]),
        "unshield": (0.6, "once", [(0, "shielded", {}), *([(0.3, "idle", over)] if over else []), (0.6, "idle", {})]),
        "chorus": (2.0, "once", [(0, "idle", {}), (0.5, closed, gather), (1.2, closed, {**gather, **sunk(-3)}), (1.5, "chorus", {}),
                                 (1.7, "chorus", {}), (2.0, "idle", {})]),
        "last": (1.0, "loop", last),
        "flinch": (0.4, "once", [(0, "idle", {}), (0.1, "idle", kick(singer)), (0.4, "idle", {})]),
        "death": (2.5, "hold", [(0, "idle", {}), (0.4, "last", sway(singer, 1.0, 3)), (1.6, "death", sunk(-4)),
                                (2.5, "death", sunk(-8))]),
    }


def spin(clip):
    """The Alto's tower turns like a blaze's rods: a full turn every idle loop, linear, continuous."""
    length, loop, keys = clip
    return [(t, (0.0, -360.0 * t / length, 0.0), "linear") for t in (0, length / 3, 2 * length / 3, length)]


def tracks(singer, clip):
    length, loop, keys = clip
    rest_rot, _ = table(singer, "idle")
    bones = {}
    names = list(rest_rot)
    for name in names:
        rot, pos, prev = [], [], None
        for t, pose, extra in keys:
            r, p = table(singer, pose)
            er, ep = extra.get(name, ((0, 0, 0), (0, 0, 0)))
            d = [wrap(r[name][i] - rest_rot[name][i]) + er[i] for i in range(3)]
            if prev is not None:
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            rot.append((t, tuple(round(float(v), 2) for v in d), "catmullrom"))
            pos.append((t, tuple(round(float(p[name][i] + ep[i]), 3) for i in range(3)), "catmullrom"))
        ch = {}
        if any(any(abs(v) > 0.05 for v in k[1]) for k in rot):
            ch["rotation"] = rot
        if any(any(abs(v) > 1e-3 for v in k[1]) for k in pos):
            ch["position"] = pos
        if ch:
            bones[name] = ch
    if singer == "alto" and clip[1] == "loop" and "tower" in names:
        bones.setdefault("tower", {})["rotation"] = spin(clip)
    return bones


def main():
    (OUT / "gifs").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "gifs").glob("*.gif"):
        old.unlink()
    summary = {}
    for singer in s2.RIGS:
        defs = clips(singer)
        clip_set = {n: (c[0], c[1], tracks(singer, c)) for n, c in defs.items()}
        name = s3.rig_id(singer)
        rig = json.loads((S6 / f"{name}.bbmodel").read_text(encoding="utf-8"))
        rig["animations"] = a7.blockbench_animations(name, clip_set, OVERRIDE)
        p = OUT / f"{name}.bbmodel"
        p.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
            if folder.is_dir():
                shutil.copyfile(p, folder / p.name)
        model = s3.build(singer, "idle")
        s4.bell_bronze(model)
        img = a7.previews(model, clip_set, f"{singer}_", {"yaw": -30, "pitch": 8, "scale": 3.0}, CONTACT,
                          f"The Blaze Choir: {singer}, key frames (session 7); the GIFs show the motion")
        img.save(OUT / f"keyframes_{singer}.png")
        summary[singer] = {n: {"length": c[0], "loop": c[1]} for n, c in defs.items()}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary["soprano"]}, indent=2) + "\n",
                                    encoding="utf-8")
    print("clips written")


if __name__ == "__main__":
    main()
