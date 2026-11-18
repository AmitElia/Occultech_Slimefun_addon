"""The Hollow Warlord (the Headsman), session 6: variants and readability (plan: docs/art/bosses/hollow_warlord/overhaul/plan.md).

The glows are painted neutral (white to light grey) and tinted per state with BetterModel's per-bone tint, so one model
serves every moment of the fight. Three groups tint on their own:
    glow_eyes + glow_brand    his eyes and the sword's brand
    glow_skull_c / _l / _r    each taken skull's eyes: lit while its guard lives, out when it dies

    calm      soul cyan: idle, his guards standing (all three skulls lit)
    tell      near-white cyan: the soul sweep's warning (eyes and brand flare)
    broken    two guards down: two skulls dark, one still lit (the shield is off below two)
    enraged   below 35%: the eyes and brand white-hot cyan (the hat stays on: session 7's review)
    dead      out
Readability is checked at night (light ~4) and under BetterModel's red hit tint.

Run from the repository root, with the 26.2 client's assets folder as the argument (run it LAST: it writes the
neutral-glow review model to run/ models):
python tools/art/bosses/headsman_s6.py <client folder>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Group  # noqa: E402
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, archevoker_s6 as a6, brood_s4 as b4  # noqa: E402
from bosses import headsman_s2 as s2, headsman_s3 as s3, headsman_s4 as s4, headsman_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s6_variants"
TINTED = ("soul", "brand")
SOUL = (92, 232, 240)
DARK = (40, 44, 44)
HIS = {"calm": SOUL, "tell": (214, 255, 252), "broken": SOUL, "enraged": (200, 255, 255), "dead": DARK}
SKULLS = {"calm": {"c": SOUL, "l": SOUL, "r": SOUL}, "tell": {"c": SOUL, "l": SOUL, "r": SOUL},
          "broken": {"c": SOUL, "l": DARK, "r": DARK}, "enraged": {"c": SOUL, "l": DARK, "r": DARK},
          "dead": {"c": DARK, "l": DARK, "r": DARK}}
POSE = {"calm": "idle", "tell": "windup", "broken": "idle", "enraged": "enraged", "dead": "death"}
HERO = [{"name": "hero", "location": (-9, 13, 6), "target": (0, 0, 3.9), "scale": 11.0, "player": False}]
LOW = [{"name": "low", "location": (4.0, 11, 1.62), "target": (0, 0, 3.4), "scale": 12.0, "player": False}]


def owner_bone(c):
    g = c.group
    while g is not None:
        if g.name.startswith("glow_"):
            return g.name
        g = g.parent
    return None


def masks(shape):
    """Per tint group, the atlas texels it owns (with their 1-pixel bleed border)."""
    model = s3.rest_model()
    s4.zone_materials(model)
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    by_name = {c.name: c for c in model.cubes}
    groups = {"his": np.zeros(shape, bool), **{k: np.zeros(shape, bool) for k in s2.SKULLS}}
    bright = np.zeros(shape, bool)
    for key, (x, y, w, h) in positions.items():
        area = (slice(y - 1, y + h + 1), slice(x - 1, x + w + 1))
        if key[4] in s4.GLOWING:
            bright[area] = True
        if key[4] not in TINTED:
            continue
        bone = owner_bone(by_name[key[0]])
        if bone and bone.startswith("glow_skull_"):
            groups[bone[-1]][area] = True
        else:
            groups["his"][area] = True
    return groups, bright


def state_atlas(atlas, groups, state, whole=None):
    img = np.array(atlas).astype(float)
    img[groups["his"], :3] *= np.array(HIS[state]) / 255
    for k, colour in SKULLS[state].items():
        img[groups[k], :3] *= np.array(colour) / 255
    if whole is not None:
        img[..., :3] *= np.array(whole) / 255
    return img


def shoot(state, img, folder, views):
    path = a6.save(img, OUT / "_tmp" / "warlord.png")
    model = s3.posed(POSE[state])
    s4.zone_materials(model)
    bb = json.loads((OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    a4.render(model, bb, path, OUT / "renders" / folder, views)
    path.unlink()


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = OUT
    for zone in TINTED:
        s5.RAMP[zone] = a6.NEUTRAL
        s5.MID[zone] = 2
    s5.main([argv[0]])
    atlas = np.array(Image.open(OUT / f"{s4.NAME}.png")).astype(float)
    groups, bright = masks(atlas.shape[:2])
    cells = []
    for state in HIS:
        shoot(state, state_atlas(atlas, groups, state), state, HERO)
        cells.append((OUT / "renders" / state / "hero.png", f"{state} ({POSE[state]})"))
    shoot("calm", a6.night(state_atlas(atlas, groups, "calm"), bright), "night", LOW)
    shoot("enraged", a6.night(state_atlas(atlas, groups, "enraged"), bright), "night_enraged", LOW)
    shoot("calm", state_atlas(atlas, groups, "calm", whole=a6.DAMAGE_TINT), "hit", LOW)
    a5.grid([p for p, _ in cells], [l for _, l in cells], OUT / "states.png", "Hollow Warlord: the glow states",
            cols=5, tw=320, th=270)
    rows = [(OUT / "renders" / k / "low.png", label) for k, label in
            (("night", "night (light ~4), calm"), ("night_enraged", "night, enraged"), ("hit", "the red hit flash"))]
    a5.grid([p for p, _ in rows], [l for _, l in rows], OUT / "readability.png",
            "Hollow Warlord: night and the hit flash", cols=3, tw=420, th=315)
    shutil.rmtree(OUT / "_tmp", ignore_errors=True)
    p = OUT / f"{s4.NAME}.bbmodel"
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    print("variants done")


if __name__ == "__main__":
    main(sys.argv[1:])
