"""The Abyssal Warden redesign, session 6: variants and readability (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

His one living light is the eye, so his states are BetterModel tints on `glow_iris` (a colour multiplied into the
texture, no texture swap). The iris is now painted as a neutral grey gradient (session 5's ramps without their hue,
the same values under the calm tint), so one texture takes every state's colour:
    calm       (110, 246, 226)  the sea glow: gliding, watching
    tracking   (236, 255, 250)  the beam's last second, white as the fight's warning
    furious    (150, 255, 196)  below half: hotter and greener, with the bloodshot white
    resting    (44, 120, 116)   the rest after the spikes, his opening: the eye dims while he vents
    dead       (26, 34, 38)     out
One part swap: below half the eye turns bloodshot. The sclera moves to its own bone, `sclera`, and a copy of it,
`sclera_blood` (hidden), is painted pinker with more, longer, thicker veins and a flushed rim; the fight hides one
and shows the other. The veins stay texture, as the user asked.
The phase parts from session 3 stay as they are: the spray jets (spikes), the burst side window and the hand (33%).
Readability is checked at night (light level ~4: everything but the full-bright iris dims) and under BetterModel's red
hit tint (it multiplies the texture like any tint).

Run from the repository root: python tools/art/bosses/warden_s6.py (after warden_s5.py)
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s6 as a6, volley_crone_s3 as v3  # noqa: E402
from bosses import warden_s2 as s2, warden_s3 as s3, warden_s4 as s4, warden_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s6_variants"
IRIS = {"calm": (110, 246, 226), "tracking": (236, 255, 250), "furious": (150, 255, 196),
        "resting": (44, 120, 116), "dead": (26, 34, 38)}
POSE_OF = {"calm": "idle", "tracking": "beam", "furious": "beam", "resting": "rest", "dead": "death"}
DAMAGE_TINT = (255, 128, 128)
# the iris ramps as greys: each level is session 5's colour divided by the calm tint, so calm looks as it did
NEUTRAL = {"iris": [70, 114, 166, 214, 240, 255], "iris_dark": [36, 67, 112, 156, 199]}
EYE = [{"name": "eye", "location": (0.8, 10, 4.3), "target": (0, 0, 4.1), "scale": 3.4, "player": False}]
HERO = [{"name": "hero", "location": (11, 13, 6.5), "target": (0, 0, 3.6), "scale": 10.5, "player": False}]
PLAYER = [{"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 3.4), "scale": 9.5, "player": False}]
HAND = [{"name": "hero", "location": (12, 12, 7), "target": (1.5, 0, 4.2), "scale": 13.0, "player": False}]


def neutral_iris():
    for zone, greys in NEUTRAL.items():
        s5.RAMP[zone] = [(g, g, g) for g in greys]


def with_bloodshot(model, bloodshot=False):
    """The sclera on its own bone, and its bloodshot copy on a hidden one (`bloodshot` shows the copy instead)."""
    body = s2.group(model, "body")
    sclera = [c for c in model.cubes if c.mat == "sclera"]
    h = next(c for c in sclera if c.name == "sclera_h")
    centre = tuple((np.array(h.frm) + h.to) / 2)
    calm = body.group("sclera", centre)
    blood = body.group("sclera_blood", centre)
    for c in sclera:
        body.children.remove(c)
        c.group = calm
        calm.children.append(c)
        blood.cube(c.name.replace("sclera", "sclera_blood", 1), c.frm, c.to, c.mat, c.rotation, c.origin, c.inflate)
    calm.visible, blood.visible = not bloodshot, bloodshot
    return model


def rig(key, bloodshot=False):
    return with_bloodshot(s4.zoned(key), bloodshot)


def keep_of(model, spec):
    """The cubes a pose shows, with whichever sclera is visible."""
    hidden = {g.name for g in model.groups if g.name in ("sclera", "sclera_blood") and not g.visible}
    gone = {id(c) for c in model.cubes if c.group.name in hidden}
    return [i for i in s4.shown_model(model, spec) if id(model.cubes[i]) not in gone]


def eye_view(model):
    """The eye close-up aimed at where the pose puts the eye (the rest and the death sink and tip him)."""
    c = next(c for c in model.cubes if c.name == "iris_h").corners().mean(0)
    x, z = c[0] / 16, c[1] / 16                              # Blender: x across, z up, he faces +y
    return {"name": "eye", "location": (x + 0.8, 10, z + 0.5), "target": (x, 0, z + 0.3), "scale": 3.4,
            "player": False}


def render(key, tex, positions, keys, height, out, views, bloodshot=False, variant=""):
    m = rig(key, bloodshot)
    views = [eye_view(m) if v["name"] == "eye" else v for v in views]
    bb, _ = s4.textured(m, s3.MODEL_ID, keys, positions, tex, height, {}, variant)
    spec = s2.POSES[key][1]
    s4.render(m, bb, tex, out, views, keep_of(m, spec))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    neutral_iris()
    r, at = OUT / "renders", OUT / "atlases"
    at.mkdir(parents=True, exist_ok=True)

    model = rig("idle")
    keys, positions, height, atlas = s5.painted(model)
    name = s3.MODEL_ID
    neutral = OUT / f"{name}.png"
    atlas.save(neutral)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / f"{name}_preview.png")
    poses = s3.pose_table()
    for variant in s3.VARIANTS:
        m = rig("idle")
        bb, _ = s4.textured(m, name + variant, keys, positions, neutral, height, poses, variant)
        path = OUT / f"{name + variant}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    glow = a6.glow_mask(positions, s4.SIZE, height)
    states = {n: a6.save(a6.tinted(atlas, glow, c), at / f"iris_{n}.png") for n, c in IRIS.items()}
    for n, key in POSE_OF.items():
        render(key, states[n], positions, keys, height, r / n, EYE + HERO, bloodshot=n == "furious")
    a6.contact_sheet([(r / n / "eye.png", n) for n in IRIS], OUT / "eye_states.png",
                     "The Abyssal Warden - the eye's states as tints on one texture", tw=300, th=300)
    a6.contact_sheet([(r / n / "hero.png", n) for n in IRIS], OUT / "states.png",
                     "The Abyssal Warden - his states, whole", tw=300, th=300)

    night = a6.save(a6.night(a6.tinted(atlas, glow, IRIS["calm"]), glow), at / "night.png")
    night_33 = a6.save(a6.night(a6.tinted(atlas, glow, IRIS["furious"]), glow), at / "night_furious.png")
    hit = a6.save(a6.tinted(atlas, glow, IRIS["calm"], DAMAGE_TINT), at / "hit.png")
    render("idle", night, positions, keys, height, r / "night", PLAYER)
    render("raised", night_33, positions, keys, height, r / "night_33", HAND, bloodshot=True, variant="_33")
    render("idle", hit, positions, keys, height, r / "hit", PLAYER)
    render("raised", hit, positions, keys, height, r / "hit_33", HAND, variant="_33")
    a6.contact_sheet([(r / "night" / "player_eye.png", "night (light ~4)"),
                      (r / "night_33" / "hero.png", "night: from 33%, furious"),
                      (r / "hit" / "player_eye.png", "the red hit flash"),
                      (r / "hit_33" / "hero.png", "the hit flash: the hand")],
                     OUT / "readability.png", "The Abyssal Warden - night and the hit flash", tw=360, th=300)

    total, per_bone = v3.display_count(model)
    hidden = {"spray", "window_r_burst", "arm", "forearm", "hand", "sclera_blood"}
    report = {"atlas": list(atlas.size), "displays": total,
              "displays_at_spawn": sum(v for k, v in per_bone.items() if k not in hidden),
              "sclera": per_bone.get("sclera"), "sclera_blood": per_bone.get("sclera_blood"),
              "tints": {n: list(c) for n, c in IRIS.items()}}
    (OUT / "variants_report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("variants done", report)


if __name__ == "__main__":
    main()
