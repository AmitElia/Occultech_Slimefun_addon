"""The Tempest redesign, session 6: variants and readability (plan: docs/art/bosses/tempest/overhaul/plan.md).

The heart and the glyphs (glow_heart, glow_shard0..6, glow_circlet) are painted neutral and tinted per state with
BetterModel's per-bone tint, so one model serves every moment of the fight:
    calm    tier 2's sea teal: between attacks (idle)
    tell    near-white teal: the wind-up of the gust volley and the wind burst; the seal flares as it locks
    storm   a cold electric blue: below half, from the split on; the storm has broken loose
    spent   nearly out, dark sea-green: the 1.5 s opening, the heart dark, "hit me now"
    dead    out
The breeze's own eyes (glow_eyes: the white brows and yellow eyes) keep vanilla's colours, untinted, full-bright like
vanilla's eyes layer, except that they dim when spent and go out when dead.
No part swaps: the seal's moments are poses (session 2) and clips (session 7). Readability is checked at night
(light ~4) and under BetterModel's red hit tint.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument (run it LAST:
it writes the neutral-glow review model to both servers):
python tools/art/bosses/tempest_s6.py <folder>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, archevoker_s6 as a6, brood_s4 as b4  # noqa: E402
from bosses import tempest_s3 as s3, tempest_s4 as s4, tempest_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s6_variants"
TINTED = ("core_glow", "glyph")
EYES = ("eye", "eye_gold")
STATES = {"calm": (86, 232, 208), "tell": (214, 255, 246), "storm": (140, 176, 255), "spent": (40, 84, 80),
          "dead": (44, 40, 40)}
EYE_TINT = {"spent": (130, 130, 140), "dead": (44, 40, 40)}
POSE = {"calm": "idle", "tell": "locked", "storm": "split", "spent": "spent", "dead": "death"}
HERO = [{"name": "hero", "location": (11, 15, 8), "target": (0, 0, 4.3), "scale": 12.0, "player": False}]
LOW = [{"name": "low", "location": (-4.5, 10, 1.62), "target": (0, 0, 4.0), "scale": 11.0, "player": False}]


def neutral():
    for zone in TINTED:
        s5.RAMP[zone] = a6.NEUTRAL
        s5.MID[zone] = 2


def masks(shape):
    model = s3.rest_model()
    s4.zone_materials(model)
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    tint, eyes, bright = (np.zeros(shape, bool) for _ in range(3))
    for key, (x, y, w, h) in positions.items():
        area = (slice(y - 1, y + h + 1), slice(x - 1, x + w + 1))
        if key[4] in TINTED:
            tint[area] = True
        if key[4] in EYES:
            eyes[area] = True
        if key[4] in s4.GLOWING:
            bright[area] = True
    return tint, eyes, bright


def state_atlas(atlas, tint, eyes, state, whole=None):
    img = a6.tinted(atlas, tint, STATES[state], whole=whole)
    if state in EYE_TINT:
        img[eyes, :3] *= np.array(EYE_TINT[state]) / 255
    return img


def shoot(pose, img, folder, views):
    path = a6.save(img, OUT / "_tmp" / "tempest.png")
    model = s3.build(pose)
    s4.zone_materials(model)
    bb = json.loads((OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    a4.render(model, bb, path, OUT / "renders" / folder, views)
    path.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = OUT
    neutral()
    s5.main()
    atlas = np.array(Image.open(OUT / f"{s4.NAME}.png")).astype(float)
    tint, eyes, bright = masks(atlas.shape[:2])
    cells = []
    for state in STATES:
        shoot(POSE[state], state_atlas(atlas, tint, eyes, state), state, HERO)
        cells.append((OUT / "renders" / state / "hero.png", f"{state} ({POSE[state]})"))
    calm = state_atlas(atlas, tint, eyes, "calm")
    shoot("idle", a6.night(calm, bright), "night", LOW)
    shoot("idle", state_atlas(atlas, tint, eyes, "calm", whole=a6.DAMAGE_TINT), "hit", LOW)
    shoot("spent", a6.night(state_atlas(atlas, tint, eyes, "spent"), bright), "night_spent", LOW)
    a5.grid([p for p, _ in cells], [l for _, l in cells], OUT / "states.png", "Tempest: the seal's states", cols=5,
            tw=320, th=270)
    rows = [(OUT / "renders" / k / "low.png", label) for k, label in
            (("night", "night (light ~4), calm"), ("night_spent", "night, spent"), ("hit", "the red hit flash"))]
    a5.grid([p for p, _ in rows], [l for _, l in rows], OUT / "readability.png", "Tempest: night and the hit flash",
            cols=3, tw=420, th=315)
    print("variants done")


if __name__ == "__main__":
    main()
