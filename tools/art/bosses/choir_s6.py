"""The Blaze Choir redesign, session 6: variants and readability (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

Each singer's fire and singing mouth (glow_wisp, glow_sail, glow_ember, glow_clapper, glow_mouth) are painted neutral
and tinted per state with BetterModel's per-bone tint, so one model serves every moment of the fight:
    calm      the singer's own fire: white (Soprano), orange (Alto), deep red (Bass)
    banked    shielded: the fire drawn down to embers while the instrument closes. The shielded singer looks protected,
              the two you should hit blaze (the fight also outlines it with the vanilla glow)
    hotter    a voice has fallen: the survivors burn hotter
    last      the last singer: its fire at its hottest
    dead      out
No part swaps: the instruments' moments are poses (session 2) and clips (session 7). Readability is checked at night
(light ~4) and under BetterModel's red hit tint.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s6.py <folder>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, archevoker_s6 as a6, brood_s4 as b4  # noqa: E402
from bosses import choir_s2 as s2, choir_s3 as s3, choir_s4 as s4, choir_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s6_variants"
STATES = {
    "soprano": {"calm": (255, 238, 200), "banked": (150, 104, 76), "hotter": (214, 234, 255), "last": (176, 214, 255)},
    "alto": {"calm": (255, 158, 60), "banked": (150, 74, 34), "hotter": (255, 204, 96), "last": (255, 238, 170)},
    "bass": {"calm": (236, 76, 40), "banked": (120, 34, 22), "hotter": (255, 118, 50), "last": (255, 166, 84)},
}
DEAD = (44, 40, 40)
POSE = {"calm": "idle", "banked": "shielded", "hotter": "strike", "last": "last", "dead": "death"}


def neutral():
    for zone in s4.GLOWING:
        s5.RAMP[zone] = a6.NEUTRAL
        s5.MID[zone] = 2


def glow_mask(singer, atlas):
    model = s3.build(singer, "idle")
    s4.bell_bronze(model)
    b4.SIZE = s4.SIZE
    keys = s4.island_keys(model)
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    mask, bright = np.zeros(atlas.shape[:2], bool), np.zeros(atlas.shape[:2], bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in s4.GLOWING:
            mask[y - 1:y + h + 1, x - 1:x + w + 1] = True
        if key[4] in s4.FULL_BRIGHT:
            bright[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return mask, bright


def shoot(singer, pose, img, folder, views):
    path = a6.save(img, OUT / "_tmp" / f"{singer}.png")
    model = s3.build(singer, pose)
    s4.bell_bronze(model)
    bb = json.loads((OUT / f"{s3.rig_id(singer)}.bbmodel").read_text(encoding="utf-8"))
    a4.render(model, bb, path, OUT / "renders" / folder, views)
    path.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = OUT
    neutral()
    cells = []
    for singer in s2.RIGS:
        s5.model_pass(singer)
        atlas = np.array(Image.open(OUT / f"{s3.rig_id(singer)}.png")).astype(float)
        glow, bright = glow_mask(singer, atlas)
        hero = [dict(s5.views(singer)[0], player=False)]
        for state, colour in [*STATES[singer].items(), ("dead", DEAD)]:
            shoot(singer, POSE[state], a6.tinted(atlas, glow, colour), f"{singer}_{state}", hero)
            cells.append((OUT / "renders" / f"{singer}_{state}" / "hero.png", f"{singer}: {state}"))
        low = [{"name": "low", "location": (-4.5, 9, 1.62), "target": (0, 0, 3.4), "scale": s4.WIDE[singer], "player": False}]
        calm = a6.tinted(atlas, glow, STATES[singer]["calm"])
        shoot(singer, "idle", a6.night(calm, bright), f"{singer}_night", low)
        shoot(singer, "idle", a6.tinted(atlas, glow, STATES[singer]["calm"], whole=a6.DAMAGE_TINT), f"{singer}_hit", low)
    a5.grid([p for p, _ in cells], [l for _, l in cells], OUT / "states.png", "The Blaze Choir: the fire's states", cols=5,
            tw=320, th=260)
    rows = [(OUT / "renders" / f"{s}_{k}" / "low.png", f"{s}: {label}") for s in s2.RIGS
            for k, label in (("night", "night (light ~4)"), ("hit", "the red hit flash"))]
    a5.grid([p for p, _ in rows], [l for _, l in rows], OUT / "readability.png", "The Blaze Choir: night and the hit flash",
            cols=2, tw=420, th=315)
    print("variants done")


if __name__ == "__main__":
    main()
