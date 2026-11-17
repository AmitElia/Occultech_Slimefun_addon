"""The Tidebreaker redesign, session 6: variants and readability (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

His only light is the lantern on the dragon's jaw. It is painted neutral and tinted per state with a BetterModel per-bone
tint on `glow_lantern` (the mount's model):
    calm     (255, 214, 110)  the sickly warm oil light
    ram      (120, 190, 255)  flares the blue of the ram's warning lane on the floor, during the warning and the charge
    winded   (150, 104, 58)   guttering: the melee opening
    dead     (44, 42, 46)     out
Nothing swaps parts: the fight has no phases. Readability is checked at night (light ~4) and under BetterModel's red hit
tint, which only the rider's model takes (the nautilus can't be hurt).

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_s6.py <folder>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s6 as a6, brood_s4 as b4, tide_s3 as s3, tide_s4 as s4, tide_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s6_variants"
STATES = {"calm": ((255, 214, 110), "idle"), "ram": ((120, 190, 255), "ram"), "winded": ((150, 104, 58), "winded"),
          "dead": ((44, 42, 46), "death")}
HERO = [{"name": "hero", "location": (9, 13, 7), "target": (0, 0, 2.9), "scale": 10.5, "player": False}]
LOW = [{"name": "low", "location": (-5, 10, 2.8), "target": (0, 0.6, 2.9), "scale": 9.0, "player": False}]


def glow_mask(kind, name):
    model = s3.build(kind, "idle")
    b4.SIZE = s4.SIZE
    keys = s4.island_keys(model)
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    img = Image.open(OUT / f"{name}.png")
    mask = np.zeros((img.height, img.width), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] == "glow":
            mask[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return np.array(img).astype(float), mask


def write(arr, name, tag):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(OUT / f"{name}{tag}.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = s4.OUT = OUT
    s5.RAMP["glow"] = a6.NEUTRAL
    mf, mh = s5.model_pass("mount", s3.MOUNT_ID, s3.MOUNT_HITBOX)
    rf, rh = s5.model_pass("rider", s3.RIDER_ID, s3.RIDER_HITBOX)
    mount, glow = glow_mask("mount", s3.MOUNT_ID)
    rider = np.array(Image.open(OUT / f"{s3.RIDER_ID}.png")).astype(float)

    def shot(tag, key, m, r, views, folder):
        write(m, s3.MOUNT_ID, tag)
        write(r, s3.RIDER_ID, tag)
        s4.VIEWS = views
        s4.together(mf, rf, mh, rh, False, key=key, tag=tag, folder=folder)
        (OUT / f"{s3.MOUNT_ID}{tag}.png").unlink()
        (OUT / f"{s3.RIDER_ID}{tag}.png").unlink()

    def lit(colour):
        out = mount.copy()
        out[glow, :3] *= np.array(colour) / 255
        return out

    def dark(arr, mask=None):
        out = arr.copy()
        keep = mask if mask is not None else np.zeros(arr.shape[:2], bool)
        out[~keep, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
        return out

    for state, (colour, key) in STATES.items():
        shot(f"_{state}", key, lit(colour), rider, HERO, f"renders/{state}")
    a6.contact_sheet([(OUT / "renders" / s / "hero.png", s) for s in STATES], OUT / "states.png",
                     "The Tidebreaker: the lantern's states", tw=400, th=330)
    calm = lit(STATES["calm"][0])
    shot("_night", "idle", dark(calm, glow), dark(rider), LOW, "renders/night")
    hit = rider.copy()
    hit[..., :3] *= np.array((255, 128, 128)) / 255
    shot("_hit", "idle", calm, hit, LOW, "renders/hit")
    a6.contact_sheet([(OUT / "renders/night/low.png", "night (light ~4)"), (OUT / "renders/hit/low.png", "the red hit flash, rider only")],
                     OUT / "readability.png", "The Tidebreaker: night and the hit flash")
    print("variants done")


if __name__ == "__main__":
    main()
