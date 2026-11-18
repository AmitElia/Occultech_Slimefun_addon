"""The Drowned Elder redesign, session 6: variants and readability (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

The eyes are painted neutral (white to grey) and tinted per state with BetterModel's per-bone tint, so one model serves
every moment of the fight. Both kinds of eye are full-bright.
- The three beam eyes (glow_eye2, glow_eye4, glow_eye6), each its own bone, so each beam's eye can flare on its own:
    calm     tier 2's sea glow, between beams
    lock     near-white sea glow: the 0.5 s lock before its beam fires (only the locked eyes flare)
    surged   a cold abyss blue: below half health, when the beams come faster
    dead     out
- The head's great eye (glow_eye):
    calm     the elder's pale, near-vanilla white
    stare    cold sea glow: the Mining Fatigue pulse
    dead     out
The head's eye keeps vanilla's plain look (no pupil); the beam eyes keep their slit pupils. No part swaps: the moments
are poses (session 2) and clips (session 7). Readability is checked at night (light ~4) and under BetterModel's red hit
tint.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument (run it LAST:
it writes the neutral-eye review model to both servers):
python tools/art/bosses/drowned_s6.py <folder>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, archevoker_s6 as a6, brood_s4 as b4  # noqa: E402
from bosses import drowned_s2 as s2, drowned_s3 as s3, drowned_s4 as s4, drowned_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s6_variants"
BEAM = {"calm": (110, 232, 206), "lock": (214, 255, 246), "surged": (110, 160, 255), "dead": (40, 44, 48)}
HEAD = {"calm": (236, 230, 220), "stare": (140, 255, 228), "dead": (52, 50, 54)}
# what each review shot shows: pose, beam-eye tint, head-eye tint, view
SHOTS = {
    "calm": ("idle", "calm", "calm", "hero"),
    "lock": ("open", "lock", "calm", "eyes"),
    "stare": ("bind", "calm", "stare", "stare"),
    "surged": ("open", "surged", "calm", "eyes"),
    "dead": ("death", "dead", "dead", "dead"),
}
VIEW = {
    "hero": {"name": "v", "location": (16, 9, 10), "target": (0, -6.5, 3.2), "scale": 19.0, "player": False},
    "eyes": {"name": "v", "location": (14, -2, 4.5), "target": (0, -5.5, 3.6), "scale": 12.0, "player": False},
    "stare": {"name": "v", "location": (-3, 10, 1.62), "target": (0, -1, 5.5), "scale": 11.0, "player": False},
    "dead": {"name": "v", "location": (12, 12, 8), "target": (0, -2.5, 0.8), "scale": 14.0, "player": False},
    "low": {"name": "v", "location": (-7, 9, 1.62), "target": (0, -4, 3.4), "scale": 15.0, "player": False},
}


def neutral():
    """Both eyes painted neutral; the head's eye painted plain (vanilla's eye has no pupil), not from the skin."""
    for zone in ("glow", "eye"):
        s5.RAMP[zone] = a6.NEUTRAL
        s5.MID[zone] = 2
    s4.GLOWING = a4.GLOWING = ("glow", "eye")
    skin_part = s4.skin_part
    s4.skin_part = lambda c: None if c.name == "eye" else skin_part(c)
    paint = s5.paint

    def paint_eyes(model, i, face, w, h, solids):
        if model.cubes[i].mat != "eye":
            return paint(model, i, face, w, h, solids)
        out = np.zeros((h, w, 4), np.uint8)
        for y in range(h):
            for x in range(w):
                d = max(abs(y - (h - 1) / 2) / max(1, h / 2), abs(x - (w - 1) / 2) / max(1, w / 2))
                out[y, x, :3] = a6.NEUTRAL[4 if d < 0.4 else 3]
                out[y, x, 3] = 255
        return out
    s5.paint = paint_eyes


def masks(shape):
    model = s3.rest_model()
    s4.zone_materials(model)
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, _, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    beam, head = np.zeros(shape, bool), np.zeros(shape, bool)
    for key, (x, y, w, h) in positions.items():
        area = (slice(y - 1, y + h + 1), slice(x - 1, x + w + 1))
        if key[4] == "glow":
            beam[area] = True
        elif key[4] == "eye":
            head[area] = True
    return beam, head


def state_atlas(atlas, beam, head, b, h, whole=None):
    img = np.array(atlas).astype(float)
    img[beam, :3] *= np.array(BEAM[b]) / 255
    img[head, :3] *= np.array(HEAD[h]) / 255
    if whole is not None:
        img[..., :3] *= np.array(whole) / 255
    return img


def blender(p):
    return (p[0] / 16, -p[2] / 16, p[1] / 16)


def eye_view(model, cube_name, dist, scale, up=0.0):
    """A camera looking straight at an eye: from its face's outward normal (worked out on the posed model)."""
    c = next(x for x in model.cubes if x.name == cube_name)
    corners = c.corners()
    centre = corners.mean(0)
    owner = c.group.parent if c.group.name.startswith("glow_eye") else c.group
    ref = np.mean([x.corners().mean(0) for x in model.cubes if x.group is owner or x.group is c.group], axis=0)
    if cube_name == "eye":
        ref = next(x for x in model.cubes if x.name == "head").corners().mean(0)
    n = centre - ref
    n = n / np.linalg.norm(n)
    loc = centre + n * dist * 16 + np.array([0, up * 16, 0])
    return {"name": "v", "location": blender(loc), "target": blender(centre), "scale": scale, "player": False}


def shoot(pose, img, folder, view):
    path = a6.save(img, OUT / "_tmp" / "drowned.png")
    # the eyes are shot on the straight bind pose (the curled poses hide them behind the body); "open" swings the gills
    model = s3.build(None if pose in ("bind", "open") else pose)
    if pose == "open":
        s2.set_gills(model, True)
    s4.zone_materials(model)
    bb = json.loads((OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    bb = s5.shown(model, bb)
    if view == "eyes":
        z0 = s2.FACE_Z + s2.SEGS[2][2]
        z1 = s2.FACE_Z + s2.SEGS[6][2] + s2.SEGS[6][1]
        mid = -(z0 + z1) / 2 / 16
        v = {"name": "v", "location": (6.5, mid - 3.5, 3.6), "target": (0, mid, s2.HEAD_Y / 16), "scale": 9.0,
             "player": False}
    elif view == "stare":
        v = {"name": "v", "location": (1.2, 7, 3.2), "target": (0, 0, s2.HEAD_Y / 16), "scale": 5.0, "player": False}
    else:
        v = VIEW[view]
    a4.render(model, bb, path, OUT / "renders" / folder, [v])
    path.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s5.OUT = OUT
    neutral()
    s5.main()
    atlas = np.array(Image.open(OUT / f"{s4.NAME}.png")).astype(float)
    beam, head = masks(atlas.shape[:2])
    cells = []
    for state, (pose, b, h, view) in SHOTS.items():
        shoot(pose, state_atlas(atlas, beam, head, b, h), state, view)
        cells.append((OUT / "renders" / state / "v.png", f"{state} ({pose})"))
    a5.grid([p for p, _ in cells], [lbl for _, lbl in cells], OUT / "states.png", "Drowned Elder: the eyes' states",
            cols=5, tw=340, th=270)
    bright = beam | head
    shoot("idle", a6.night(state_atlas(atlas, beam, head, "calm", "calm"), bright), "night", "low")
    shoot("open", a6.night(state_atlas(atlas, beam, head, "lock", "calm"), bright), "night_lock", "eyes")
    shoot("bind", a6.night(state_atlas(atlas, beam, head, "calm", "stare"), bright), "night_stare", "stare")
    shoot("idle", state_atlas(atlas, beam, head, "calm", "calm", whole=a6.DAMAGE_TINT), "hit", "low")
    rows = [(OUT / "renders" / k / "v.png", label) for k, label in
            (("night", "night (light ~4), swimming"), ("night_lock", "night, beam lock"),
             ("night_stare", "night, the stare"), ("hit", "the red hit flash"))]
    a5.grid([p for p, _ in rows], [lbl for _, lbl in rows], OUT / "readability.png",
            "Drowned Elder: night and the hit flash", cols=4, tw=400, th=300)
    print("variants done")


if __name__ == "__main__":
    main()
