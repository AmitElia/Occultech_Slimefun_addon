"""Witch Coven effects, E2: deeper attack clips and personality (plan.md, "Effects and deeper attacks").

Session 7's clips stay (idle, walk, spawn, rotation, death); this replaces heal, curse and throw with deeper versions
per sister and adds three personality clips. Each action has anticipation, contact and follow-through, with secondary
motion on top: the hat's tip lags behind her, the robe swings, the brew sloshes in its vessel. The release points
stay session 7's (heal 0.8 s, curse 1.0 s, throw 0.65 s), so the fight's timing doesn't change.

  heal    cauldron  reaches back over her shoulder into the cauldron, scoops (the brew dips), sweeps the brew out
                    to her sister at 0.8 s, her sleeve's cast flaring
          bottles   draws the bottle down to her chest, raises it high and lobs it at 0.8 s, then reaches across to
                    her belt and draws a fresh one
          pot       hugs the pot in, then tips it forward and pours a long stream at 0.8 s, the brew level dropping
  curse   cauldron  bows deeper and deeper through the warning until the brew sloshes over her shoulder at 1.0 s
          bottles   winds up and aims, trembling, through the warning, smashes a bottle on the mark at 1.0 s, draws
                    a fresh one
          pot       tips the pot further and further through the warning, pours it out onto the mark at 1.0 s
  throw   cauldron  reaches back into the cauldron, scoops a glob, swings it up and hurls it at 0.65 s, lunging
          bottles   winds up and hurls at 0.65 s, then draws a fresh bottle from her belt
          pot       dips, heaves the pot out to her side and flings the wave at 0.65 s, the pot emptied, then refills
  flinch  0.4 s     hit: she recoils, her hat jolts (layered over whatever she is doing)
  cackle  1.6 s     her head thrown back, her shoulders shaking, the hat's tip flopping
  glance  1.4 s     at a fallen sister: the server turns her towards the body; she bows, a sleeve to her chest

The bottle witch's belt always stays full: the held bottle (bone `bottle_held`) slides up into her sleeve as it
leaves her hand and drops back out as her sleeve comes away from the belt. The animation does it, no extra fight
code. (It used to shrink to nothing: a near-zero scale in game is not worth the risk.)

The brew never moves on its own (fix after the in-game review): its bone also holds the drips down the vessel's
sides and the steam above it, so any scale or tilt pulled the drips off the walls and pushed the liquid through
them, and the bottles' liquid out of their glass. Every clip's brew keys are dropped; the sloshing is left to the
fight's bubble and splash effects.

Run from the repository root: python tools/art/bosses/coven_e2.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import coven_s2 as s2, coven_s3 as s3, coven_s7 as s7  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/fx_clips"
RIGS = ROOT / "docs/art/bosses/witch_coven/overhaul/s7_animation"
ZERO, ONE = (0, 0, 0), (1, 1, 1)
SLEEVE, TUCKED = (0, 13, 0), (0.85, 0.85, 0.85)   # the held bottle put away in her sleeve
rot = s7.rot
RELEASE = dict(s7.RELEASE)
PARTIAL = s7.PARTIAL + ("flinch", "cackle", "glance")


def arm(vessel, side, target):
    """A sleeve's delta from its rest to an absolute rotation."""
    rest = s2.REST[vessel][0 if side == "right" else 1]
    return tuple(target[i] - rest[i] for i in range(3))


def lag(keys, delay, amount):
    """Secondary motion: a track that follows another a little late and a little less (the hat's tip, the robe)."""
    out = []
    for t, v, interp in keys:
        out.append((t + delay, tuple(-x * amount for x in v), interp))
    end = max(t for t, _, _ in keys)
    return [(0, ZERO, "catmullrom")] + [k for k in out if k[0] < end] + [(end, ZERO, "catmullrom")]


def secondary(bones, torso_keys):
    bones.setdefault("hat_tip", {})["rotation"] = lag(torso_keys, 0.12, 0.8)
    bones.setdefault("hat_t3", {})["rotation"] = lag(torso_keys, 0.08, 0.35)
    bones.setdefault("robe_lower", {})["rotation"] = lag(torso_keys, 0.1, 0.25)
    return bones


def belt_reach(vessel, t0, length):
    """The bottle witch draws a fresh bottle: her sleeve crosses to the belt, the bottle grows back as it leaves."""
    belt = arm(vessel, "right", (55, 0, -42))
    # hidden up the sleeve: the bottle hangs below the cuff, so 13 px up (and a touch smaller) puts it inside
    keys = lambda inside, out: rot((0, out), (t0 - 0.2, out), (t0 - 0.18, inside), (t0 + 0.2, inside),
                                   (t0 + 0.32, out), (length, out), interp="linear")
    return (rot((t0, belt), (t0 + 0.25, belt), (length, ZERO)),
            {"position": keys(SLEEVE, ZERO), "scale": keys(TUCKED, ONE)})


def heal(vessel):
    r = RELEASE["heal"]
    if vessel == "cauldron":
        back = arm(vessel, "right", (-150, 0, -16))
        out_ = arm(vessel, "right", (70, 0, 75))
        torso = rot((0, ZERO), (0.3, (6, 8, 0)), (0.6, (0, -10, 0)), (r, (-6, -14, 0)), (1.0, (-4, -10, 0)), (1.6, ZERO))
        b = {"arm_right": {"rotation": rot((0, ZERO), (0.3, back), (0.5, back), (r, tuple(x * 1.12 for x in out_)),
                                           (1.0, out_), (1.6, ZERO))},
             "arm_left": {"rotation": rot((0, ZERO), (0.5, (20, 0, -20)), (r, (36, 0, -40)), (1.6, ZERO))},
             "torso": {"rotation": torso},
             "h_head": {"rotation": rot((0, ZERO), (0.3, (8, 30, 0)), (r, (-4, -24, 0)), (1.6, ZERO))},
             "glow_brew": {"scale": rot((0, ONE), (0.35, ONE), (0.5, (1, 0.8, 1)), (0.9, (1, 0.85, 1)), (1.6, ONE))},
             "glow_cast": {"scale": rot((0, ONE), (r - 0.05, ONE), (r + 0.05, (1.8, 1.8, 1.8)), (1.1, ONE), (1.6, ONE))}}
        return 1.6, secondary(b, torso)
    if vessel == "bottles":
        high = arm(vessel, "right", (160, 0, -38))
        low = arm(vessel, "right", (20, 0, -20))
        torso = rot((0, ZERO), (0.3, (-6, 0, 0)), (0.7, (6, 0, 0)), (r, (-4, 0, 0)), (1.7, ZERO))
        reach, bottle = belt_reach(vessel, 1.0, 1.7)
        b = {"arm_right": {"rotation": rot((0, ZERO), (0.3, low), (0.7, high), (r, tuple(x * 1.1 for x in high)),
                                           (0.9, high)) + reach},
             "bottle_held": bottle,
             "torso": {"rotation": torso},
             "h_head": {"rotation": rot((0, ZERO), (0.3, (-12, 0, 0)), (0.7, (14, 0, 0)), (r, (10, 0, 0)), (1.7, ZERO))}}
        return 1.7, secondary(b, torso)
    tilt = s7.pose_deltas(vessel, "red", "heal")
    torso = rot((0, ZERO), (0.3, (6, 0, 0)), (0.7, tilt.get("torso", (-3, 0, 0))), (1.1, tilt.get("torso", ZERO)),
                (1.5, ZERO))
    b = {"pot_carry": {"rotation": rot((0, ZERO), (0.3, (-10, 0, 0)), (0.7, tilt["pot_carry"]), (1.1, tilt["pot_carry"]),
                                       (1.5, ZERO))},
         "vessel": {"rotation": rot((0, ZERO), (0.3, (6, 0, 0)), (0.7, tilt["vessel"]),
                                    (r, tuple(x * 1.35 for x in tilt["vessel"])), (1.1, tilt["vessel"]), (1.5, ZERO))},
         "arm_right": {"rotation": rot((0, ZERO), (0.3, (-8, 0, 0)), (0.7, tilt["arm_right"]), (1.1, tilt["arm_right"]),
                                       (1.5, ZERO))},
         "arm_left": {"rotation": rot((0, ZERO), (0.3, (-8, 0, 0)), (0.7, tilt["arm_left"]), (1.1, tilt["arm_left"]),
                                      (1.5, ZERO))},
         "glow_brew": {"scale": rot((0, ONE), (r, ONE), (1.1, (1, 0.7, 1)), (1.5, ONE))},
         "torso": {"rotation": torso}}
    return 1.5, secondary(b, torso)


def curse(vessel):
    r = RELEASE["curse"]
    trem = lambda base, n=6: [(0.4 + 0.08 * i, tuple(x + (1.6 if i % 2 else -1.6) for x in base)) for i in range(n)]
    if vessel == "cauldron":
        deep = (-30, 0, 0)
        torso = rot((0, ZERO), (0.35, (-14, 0, 0)), *trem((-20, 0, 0)), (0.9, deep), (r, (-36, 0, 0)),
                    (1.2, (-24, 0, 0)), (1.7, ZERO))
        b = {"torso": {"rotation": torso},
             "arm_right": {"rotation": rot((0, ZERO), (0.35, arm(vessel, "right", (38, 0, 4))),
                                           (r, arm(vessel, "right", (55, 0, 10))), (1.7, ZERO))},
             "arm_left": {"rotation": rot((0, ZERO), (0.35, arm(vessel, "left", (38, 0, -4))),
                                          (r, arm(vessel, "left", (55, 0, -10))), (1.7, ZERO))},
             "h_head": {"rotation": rot((0, ZERO), (0.35, (-10, 0, 0)), (r, (-16, 0, 0)), (1.7, ZERO))},
             "glow_brew": {"rotation": rot((0, ZERO), (0.9, (-10, 0, 0)), (r, (-28, 0, 0)), (1.2, (-8, 0, 0)),
                                           (1.7, ZERO)),
                           "scale": rot((0, ONE), (r, (1.1, 1.3, 1.1)), (1.2, (1, 0.8, 1)), (1.7, ONE))}}
        return 1.7, secondary(b, torso)
    if vessel == "bottles":
        wind = arm(vessel, "right", (176, 0, -42))
        down = arm(vessel, "right", (50, 0, -10))
        torso = rot((0, ZERO), (0.35, (4, 0, 0)), (0.9, (2, 0, 0)), (r, (-14, 0, 0)), (1.2, (-8, 0, 0)), (1.8, ZERO))
        reach, bottle = belt_reach(vessel, 1.2, 1.8)
        b = {"arm_right": {"rotation": rot((0, ZERO), (0.35, wind), *trem(wind, 5), (0.9, wind), (r, down),
                                           (1.1, down)) + reach},
             "bottle_held": bottle,
             "torso": {"rotation": torso},
             "h_head": {"rotation": rot((0, ZERO), (0.35, (-8, 0, 0)), (r, (-14, 0, 0)), (1.8, ZERO))}}
        return 1.8, secondary(b, torso)
    tilt = s7.pose_deltas(vessel, "red", "curse")
    pot = tilt["vessel"]
    torso = rot((0, ZERO), (0.35, tuple(x * 0.6 for x in tilt["torso"])), (0.9, tilt["torso"]),
                (r, tuple(x * 1.15 for x in tilt["torso"])), (1.7, ZERO))
    b = {"vessel": {"rotation": rot((0, ZERO), (0.35, tuple(x * 0.4 for x in pot)), *trem(tuple(x * 0.7 for x in pot)),
                                    (0.9, pot), (r, tuple(x * 1.2 for x in pot)), (1.3, pot), (1.7, ZERO))},
         "pot_carry": {"rotation": rot((0, ZERO), (0.6, tilt["pot_carry"]), (1.3, tilt["pot_carry"]), (1.7, ZERO))},
         "arm_right": {"rotation": rot((0, ZERO), (0.6, tilt["arm_right"]), (1.3, tilt["arm_right"]), (1.7, ZERO))},
         "arm_left": {"rotation": rot((0, ZERO), (0.6, tilt["arm_left"]), (1.3, tilt["arm_left"]), (1.7, ZERO))},
         "h_head": {"rotation": rot((0, ZERO), (0.6, tilt["h_head"]), (1.3, tilt["h_head"]), (1.7, ZERO))},
         "glow_brew": {"scale": rot((0, ONE), (r, ONE), (1.3, (1, 0.6, 1)), (1.7, ONE))},
         "torso": {"rotation": torso}}
    return 1.7, secondary(b, torso)


def throw(vessel):
    r = RELEASE["throw"]
    if vessel in ("cauldron", "bottles"):
        rest = s2.REST[vessel][0]
        wind = arm(vessel, "right", (176, 0, -42))
        follow = (40 - rest[0], -rest[1], -rest[2])
        torso = rot((0, ZERO), (0.25, (6, 10, 0)), (0.5, (8, 14, 0)), (r, (-10, -8, 0)), (0.85, (-8, -4, 0)), (1.3, ZERO))
        b = {"torso": {"rotation": torso},
             "h_head": {"rotation": rot((0, ZERO), (0.5, (10, 10, 0)), (r, (-6, -6, 0)), (1.3, ZERO))},
             "arm_left": {"rotation": rot((0, ZERO), (0.5, (30, 0, -30)), (r, (-20, 0, -10)), (1.3, ZERO))}}
        if vessel == "cauldron":
            back = arm(vessel, "right", (-150, 0, -16))
            b["arm_right"] = {"rotation": rot((0, ZERO), (0.2, back), (0.3, back), (0.5, wind), (r, follow),
                                              (0.85, follow), (1.3, ZERO))}
            b["glow_brew"] = {"scale": rot((0, ONE), (0.2, ONE), (0.3, (1, 0.8, 1)), (0.6, (1, 0.85, 1)), (1.3, ONE))}
            b["glow_cast"] = {"scale": rot((0, ONE), (r - 0.05, ONE), (r + 0.05, (1.8, 1.8, 1.8)), (0.9, ONE),
                                           (1.3, ONE))}
            return 1.3, secondary(b, torso)
        reach, bottle = belt_reach(vessel, 0.85, 1.4)
        b["arm_right"] = {"rotation": rot((0, ZERO), (0.5, wind), (r, follow), (0.75, follow)) + reach}
        b["bottle_held"] = bottle
        b["torso"]["rotation"] = rot((0, ZERO), (0.25, (6, 10, 0)), (0.5, (8, 14, 0)), (r, (-10, -8, 0)),
                                     (0.85, (-8, -4, 0)), (1.4, ZERO))
        return 1.4, secondary(b, b["torso"]["rotation"])
    heave = s7.pose_deltas(vessel, "red", "throw")
    carry = heave["pot_carry"]
    fling = (carry[0] + 8, carry[1] - 22, carry[2])          # further out and up, clear of her head
    # no twist here: turning her torso would swing the heaved pot back across her face
    torso = rot((0, ZERO), (0.2, (8, 0, 0)), (0.5, (-6, 0, 0)), (r, (-12, 0, 0)), (0.9, (-6, 0, 0)), (1.4, ZERO))
    carry = (carry[0], carry[1] - 10, carry[2])
    b = {"pot_carry": {"rotation": rot((0, ZERO), (0.2, (-15, 0, 0)), (0.5, carry), (r, fling), (0.85, carry),
                                       (1.4, ZERO))},
         "arm_right": {"rotation": rot((0, ZERO), (0.2, (-12, 0, 0)), (0.5, heave["arm_right"]),
                                       (r, tuple(x * 1.15 for x in heave["arm_right"])), (1.4, ZERO))},
         "arm_left": {"rotation": rot((0, ZERO), (0.2, (-12, 0, 0)), (0.5, heave["arm_left"]),
                                      (r, tuple(x * 1.15 for x in heave["arm_left"])), (1.4, ZERO))},
         "glow_brew": {"scale": rot((0, ONE), (r, ONE), (r + 0.08, (1, 0.35, 1)), (1.0, (1, 0.4, 1)), (1.4, ONE))},
         "torso": {"rotation": torso}}
    return 1.4, secondary(b, torso)


def personality(vessel):
    out = {}
    torso = rot((0, ZERO), (0.08, (10, 0, 0)), (0.2, (4, 0, 0)), (0.4, ZERO))
    out["flinch"] = (0.4, "once", secondary({
        "torso": {"rotation": torso},
        "h_head": {"rotation": rot((0, ZERO), (0.08, (14, 0, 4)), (0.4, ZERO))},
        "arm_left": {"rotation": rot((0, ZERO), (0.08, (-12, 0, -8)), (0.4, ZERO))}}, torso))
    shakes = [(0.3 + 0.1 * i, (8, 0, 2 if i % 2 else -2)) for i in range(10)]
    torso = rot((0, ZERO), *shakes, (1.6, ZERO))
    out["cackle"] = (1.6, "once", secondary({
        "torso": {"rotation": torso},
        "h_head": {"rotation": rot((0, ZERO), (0.3, (24, 0, 0)), *[(0.35 + 0.1 * i, (24 + (4 if i % 2 else -2), 0, 0))
                                                                  for i in range(9)], (1.6, ZERO))},
        "arm_left": {"rotation": rot((0, ZERO), (0.3, (30, 0, 10)), (1.3, (30, 0, 10)), (1.6, ZERO))}}, torso))
    # a bow over the body, her free sleeve drawn to her chest (the server turns her to face it)
    torso = rot((0, ZERO), (0.3, (8, 0, 0)), (1.1, (8, 0, 0)), (1.4, ZERO))
    b = {"torso": {"rotation": torso},
         "h_head": {"rotation": rot((0, ZERO), (0.3, (-26, 0, 0)), (1.1, (-26, 0, 0)), (1.4, ZERO))},
         "arm_left": {"rotation": rot((0, ZERO), (0.3, (-34, 0, 12)), (1.1, (-34, 0, 12)), (1.4, ZERO))}}
    if vessel != "pot":
        b["arm_right"] = {"rotation": rot((0, ZERO), (0.3, (-14, 0, 0)), (1.1, (-14, 0, 0)), (1.4, ZERO))}
    out["glance"] = (1.4, "once", secondary(b, torso))
    return out


def clips(vessel, role):
    base = s7.clips(vessel, role)
    for name, fn in (("heal", heal), ("curse", curse), ("throw", throw)):
        length, bones = fn(vessel)
        base[name] = (length, "once", bones)
    base.update(personality(vessel))
    for _, _, bones in base.values():
        bones.pop("glow_brew", None)          # the brew stays put (see the module notes)
    return base


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    s7.PARTIAL = PARTIAL
    summary = {}
    for vessel, role, title in s2.SISTERS:
        model = s2.build(vessel, role)
        clip_set = clips(vessel, role)
        names = {g.name for g in model.groups}
        missing = sorted({b for _, _, bones in clip_set.values() for b in bones} - names)
        if missing:
            raise SystemExit(f"{vessel}: clips key bones the model doesn't have: {missing}")
        model_id = s3.model_id(vessel)
        rig = json.loads((RIGS / vessel / f"{model_id}.bbmodel").read_text(encoding="utf-8"))
        rig["animations"] = [a for a in rig["animations"] if a["name"] not in clip_set] + \
            s7.blockbench_animations(model_id, clip_set)
        out = OUT / vessel
        (out / "gifs").mkdir(parents=True)
        path = out / f"{model_id}.bbmodel"
        path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        stills = []
        for name in ("heal", "curse", "throw", "flinch", "cackle", "glance"):
            length, loop, bones = clip_set[name]
            frames = [s7.frame(model, bones, t, role) for t in np.arange(0, length + 1e-6, 1 / 15)]
            frames[0].save(out / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
            if name in RELEASE:
                rel = RELEASE[name]
                picks = [0.0, rel * 0.4, rel, min(length, rel + 0.35), length]
            else:
                picks = [length * f for f in (0, 0.2, 0.4, 0.7, 1.0)]
            stills.append((name, [(t, s7.frame(model, bones, t, role, size=(260, 280), scale=2.8)) for t in picks]))
        tw, th, pad, top, left = 260, 280, 8, 54, 110
        img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Witch Coven - {title}: deeper attacks and personality (effects E2)",
                font=sheet._font(24), fill=sheet.INK)
        for r_, (name, row) in enumerate(stills):
            y = top + r_ * (th + 26 + pad)
            dr.text((pad, y + th // 2 - 10), name, font=sheet._font(19), fill=sheet.INK)
            for c, (t, im) in enumerate(row):
                img.paste(im, (left + c * (tw + pad), y))
                mark = " release" if name in RELEASE and abs(t - RELEASE[name]) < 1e-6 else ""
                dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15),
                        fill=sheet.DIM)
        img.save(out / "keyframes.png")
        summary[vessel] = {k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in clip_set.items()}
        print(vessel, "animated")
    (OUT / "clips.json").write_text(json.dumps({"release_seconds": RELEASE, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")


if __name__ == "__main__":
    main()
