"""Heartwood Horror, session 6: variants and readability (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

The glowing parts are painted neutral (white to grey) and tinted per state with BetterModel's per-bone tint, so one
model serves every moment of the fight. Each sits on glow_ bones that hold nothing else:
- the eyeblossoms' eyes (glow_blooms_*, glow_hump_blooms);
- the lantern's cracks (glow_lantern: the awake creaking heart's orange cracks, turned neutral);
- the sleeper's eyes (glow_sleeper);
- the womb's chamber (glow_womb): the amber glows from inside, so the sleeper shows against it at night too. It keeps
  its honey paint; the tint only dims or brightens it.
The lantern's block wears the dormant creaking heart, so with its cracks tinted out the lantern is really out.

    state        blooms          lantern            sleeper
    calm         ember orange    ember              shut (dark)       the hearts stand: it can't be hurt
    vulnerable   angry red       flaring, near white OPEN, orange     the hearts are down: the 20 s window
    creak        shut (dark)     out                shut              the vanish-and-strike: every light goes out
    dead         out             out                out

No part swaps: the moments are poses (session 2) and clips (session 7). Readability is checked at night (light ~4)
and under BetterModel's red hit tint.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/heartwood_s6.py <folder>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s5 as a5, archevoker_s6 as a6, brood_s4 as b4  # noqa: E402
from bosses import heartwood_s3 as s3, heartwood_s4 as s4, heartwood_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s6_variants"
BLOOM = {"calm": (255, 150, 40), "vulnerable": (255, 84, 48), "creak": (56, 48, 48), "dead": (36, 32, 32)}
LANTERN = {"calm": (255, 176, 96), "vulnerable": (255, 238, 176), "creak": (44, 34, 30), "dead": (30, 26, 24)}
SLEEPER = {"shut": (50, 44, 44), "open": (255, 150, 40), "dead": (30, 26, 26)}
WOMB = {"calm": (200, 188, 176), "vulnerable": (255, 255, 255), "creak": (70, 60, 56), "dead": (54, 46, 42)}
STATES = {"calm": ("calm", "calm", "shut"), "vulnerable": ("vulnerable", "vulnerable", "open"),
          "creak": ("creak", "creak", "shut"), "dead": ("dead", "dead", "dead")}
HERO = s5.VIEWS[0]
CHEST = {"name": "chest", "location": (0.9, 7.5, 2.4), "target": (0, 1.0, 4.4), "scale": 4.4, "player": False}


def neutral():
    """The glows painted neutral, so a tint sets their colour."""
    for zone, mid in (("bloom", 2), ("eyelid", 3)):
        s5.RAMP[zone] = a6.NEUTRAL
        s5.MID[zone] = mid
    s4.GLOWING = s5.s4.GLOWING = ("bloom", "glow", "eyelid", "resin_core")
    patch_for = s4.patch_for

    def neutral_patch(key):
        img = patch_for(key)
        if key[4] != "glow":
            return img
        arr = np.array(img).astype(float)
        lum = arr[..., :3] @ (0.2126, 0.7152, 0.0722)
        v = np.clip(196 + 59 * (lum - 120) / 120, 150, 255)
        arr[..., 0] = arr[..., 1] = arr[..., 2] = v
        return Image.fromarray(arr.astype(np.uint8), "RGBA")
    s4.patch_for = neutral_patch


def masks(shape):
    model = s3.model()
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    out = {z: np.zeros(shape, bool) for z in ("bloom", "glow", "eyelid", "resin_core")}
    for key, (x, y, w, h) in positions.items():
        if key[4] in out:
            out[key[4]][y - 1:y + h + 1, x - 1:x + w + 1] = True
    return out


def state_atlas(atlas, m, state, whole=None):
    bloom, lantern, sleeper = STATES[state]
    img = np.array(atlas).astype(float)
    img[m["bloom"], :3] *= np.array(BLOOM[bloom]) / 255
    img[m["glow"], :3] *= np.array(LANTERN[lantern]) / 255
    img[m["eyelid"], :3] *= np.array(SLEEPER[sleeper]) / 255
    img[m["resin_core"], :3] *= np.array(WOMB[state]) / 255
    if whole is not None:
        img[..., :3] *= np.array(whole) / 255
    return img


def shoot(pose, img, folder, view):
    path = a6.save(img, OUT / "_tmp" / "heartwood.png")
    model = s3.model(pose)
    for c in model.cubes:
        if c.name.startswith("lantern_root"):
            c.mat = "bark_dark"
    bb = json.loads((OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    s4.render(model, bb, path, OUT / "renders" / folder, [dict(view, name="v")])
    path.unlink()


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = OUT
    neutral()
    s5.main(argv)
    atlas = np.array(Image.open(OUT / f"{s4.NAME}.png")).astype(float)
    m = masks(atlas.shape[:2])
    cells = []
    for state in STATES:
        pose = "death" if state == "dead" else "idle"
        shoot(pose, state_atlas(atlas, m, state), state, HERO)
        shoot("idle", state_atlas(atlas, m, state), state + "_chest", CHEST)
        cells += [(OUT / "renders" / state / "v.png", f"{state}"),
                  (OUT / "renders" / f"{state}_chest" / "v.png", f"{state}: the chest")]
    a5.grid([p for p, _ in cells], [lbl for _, lbl in cells], OUT / "states.png",
            "Heartwood Horror: the glows' states (session 6)", cols=4, tw=400, th=300)
    womb_cells = []
    model = s3.model()
    bb = json.loads((OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    for state, night_ in (("calm", False), ("vulnerable", False), ("calm", True), ("vulnerable", True)):
        img = state_atlas(atlas, m, state)
        if night_:
            img = a6.night(img, m["bloom"] | m["glow"] | m["eyelid"] | m["resin_core"])
        tag = state + ("_night" if night_ else "")
        path = a6.save(img, OUT / "_tmp" / "heartwood.png")
        s5.OUT = OUT / "womb_states" / tag
        s5.womb_view(model, bb, path)
        womb_cells.append((s5.OUT / "womb" / "womb_below.png", tag.replace("_", ", ")))
    s5.OUT = OUT
    a5.grid([p for p, _ in womb_cells], [lbl for _, lbl in womb_cells], OUT / "womb_states.png",
            "Heartwood Horror: the sleeper, calm and vulnerable (eyes open), by day and at night", cols=4, tw=400, th=300)
    glow = m["bloom"] | m["glow"] | m["eyelid"] | m["resin_core"]
    shoot("idle", a6.night(state_atlas(atlas, m, "calm"), glow), "night", HERO)
    shoot("idle", a6.night(state_atlas(atlas, m, "vulnerable"), glow), "night_vulnerable", CHEST)
    shoot("idle", a6.night(state_atlas(atlas, m, "creak"), glow), "night_creak", HERO)
    shoot("idle", state_atlas(atlas, m, "calm", whole=a6.DAMAGE_TINT), "hit", HERO)
    rows = [(OUT / "renders" / k / "v.png", label) for k, label in
            (("night", "night (light ~4), calm"), ("night_vulnerable", "night, vulnerable"),
             ("night_creak", "night, the creak"), ("hit", "the red hit flash"))]
    a5.grid([p for p, _ in rows], [lbl for _, lbl in rows], OUT / "readability.png",
            "Heartwood Horror: night and the hit flash", cols=4, tw=400, th=300)
    shutil.rmtree(OUT / "_tmp", ignore_errors=True)
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(OUT / f"{s4.NAME}.bbmodel", s3.SERVER_MODELS / f"{s4.NAME}.bbmodel")
    print("variants done")


if __name__ == "__main__":
    main(sys.argv[1:])
