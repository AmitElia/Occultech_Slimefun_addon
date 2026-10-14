"""The Mirrored Magus redesign, session 6: variants and readability.

His variants are BetterModel per-bone tints (a colour multiplied into the texture, no texture swap). The painted
textures are the brightest they get; each tint dims or colours them.
  his eyes (`glow_eyes`, full-bright):
    calm      (120, 132, 142)  the cold stare, dimmed (so the flare reads, at night too)
    tell      (255, 255, 255)  flaring to full: the prism burst's warning and the jacks' finger-snap
    dead      (40, 44, 48)     out
  the whole rig, for a moment:
    shatter   (170, 225, 255)  a decoy struck: an icy mirror flash over every bone before it breaks apart
  the Jack-in-the-Box's eyes:
    popped    (255, 255, 255)  awake, bopping
    winding   (96, 104, 112)   the wind-down: the spring sags, the lights go out
The decoys wear the calm tint, exactly like him: the mechanic depends on them being identical (the real Magus is told
apart only by the sparkle particles the fight code trails behind him).
Readability is checked at night (light level ~4: everything but the full-bright eyes dims) and under BetterModel's red
hit tint, applied the way BetterModel applies it: the colour multiplies the texture.

Run from the repository root: python tools/art/bosses/magus_s6.py (after magus_s5.py)
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import magus_s2 as s2, magus_s3 as s3, magus_s4 as s4, magus_s5 as s5, magus_jack as jack  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s6_variants"
EYES = {"calm": (120, 132, 142), "tell": (255, 255, 255), "dead": (40, 44, 48)}
SHATTER = (170, 225, 255)
JACK = {"popped": (255, 255, 255), "winding": (96, 104, 112)}
DAMAGE_TINT = (255, 128, 128)          # a stand-in for BetterModel's red hit tint (multiplies like any tint)
GLOW_ZONES = s4.GLOWING

PLAYER_EYE = [{"name": "eye", "location": (8, 11.5, 1.62), "target": (0, 0, 3.0), "scale": 12.5, "player": False}]
FACE = [{"name": "face", "location": (1.4, 5, 5.3), "target": (0, -0.1, 5.15), "scale": 1.7, "player": False}]
DOWN = [{"name": "eye", "location": (4, 8, 2.4), "target": (0.8, 0, 0.9), "scale": 7.5, "player": False}]
JACK_EYE = [{"name": "eye", "location": (2.4, 4.2, 1.62), "target": (0, 0, 1.0), "scale": 2.6, "player": False}]


def glow_mask(positions, height):
    glow = np.zeros((height, s4.SIZE), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in GLOW_ZONES:
            glow[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return glow


def tinted(atlas, glow, eyes, whole=None):
    img = np.array(atlas).astype(float)
    img[glow, :3] *= np.array(eyes) / 255
    if whole is not None:
        img[..., :3] *= np.array(whole) / 255
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


def night(img, glow):
    """Light level ~4: all but the full-bright parts dims to a cold dark."""
    img = img.copy()
    img[~glow, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
    return img


def posed(key):
    m = s2.build(f"s6_{key}")
    s2.finish(m)
    s2.pose(m, key)
    return m


def contact_sheet(cells, out_path, title):
    tw, th, pad, top = 420, 315, 12, 56
    img = Image.new("RGB", (pad + len(cells) * (tw + pad), top + th + 40), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(26), fill=sheet.INK)
    for c, (path, label) in enumerate(cells):
        x = pad + c * (tw + pad)
        img.paste(sheet._tile(path, tw, th), (x, top))
        dr.text((x, top + th + 8), label, font=sheet._font(18), fill=sheet.DIM)
    img.save(out_path)


def magus(r, atlases):
    s2.MASK = "clown"
    model, keys, positions, used, height, atlas = s5.painted()
    neutral = atlases / "neutral.png"
    atlas.save(neutral)
    bb, _ = s4.rig_bbmodel(model, keys, positions, neutral, height, s3.pose_table())
    glow = glow_mask(positions, height)
    paths = {name: save(tinted(atlas, glow, tint), atlases / f"{name}.png") for name, tint in EYES.items()}
    paths["shatter"] = save(tinted(atlas, glow, EYES["calm"], SHATTER), atlases / "shatter.png")
    paths["night"] = save(night(tinted(atlas, glow, EYES["calm"]), glow), atlases / "night.png")
    paths["night_tell"] = save(night(tinted(atlas, glow, EYES["tell"]), glow), atlases / "night_tell.png")
    paths["hit"] = save(tinted(atlas, glow, EYES["calm"], DAMAGE_TINT), atlases / "hit.png")
    idle, prism, laugh, death = posed("idle"), posed("prism"), posed("laugh"), posed("death")
    s4.render(idle, bb, paths["calm"], r / "calm", PLAYER_EYE + FACE)
    s4.render(prism, bb, paths["tell"], r / "tell", PLAYER_EYE)
    s4.render(idle, bb, paths["tell"], r / "tell", FACE)        # the prism's raised arms hide his face; the flare shows the same
    s4.render(laugh, bb, paths["shatter"], r / "shatter", PLAYER_EYE)
    s4.render(death, bb, paths["dead"], r / "dead", DOWN)
    s4.render(idle, bb, paths["night"], r / "night", PLAYER_EYE)
    s4.render(prism, bb, paths["night_tell"], r / "night_tell", PLAYER_EYE)
    s4.render(idle, bb, paths["hit"], r / "hit", PLAYER_EYE)


def jacks(r, atlases):
    s2.MASK = "clown"
    build = s2.build
    out = {}
    for key, kw, tint in (("popped", dict(stretch=16.0), JACK["popped"]),
                          ("winding", dict(stretch=4.0, nod=45.0), JACK["winding"])):
        s2.build = lambda name, kw=kw: jack.build(**kw)
        model, keys, positions, used, height, atlas = s5.painted()
        jack.settle(model)
        glow = glow_mask(positions, height)
        neutral = save(np.array(atlas).astype(float), atlases / f"jack_{key}_neutral.png")
        bb, _ = s4.rig_bbmodel(model, keys, positions, neutral, height, {})
        out[key] = save(tinted(atlas, glow, tint), atlases / f"jack_{key}.png")
        s4.render(model, bb, out[key], r / f"jack_{key}", JACK_EYE, player_at=(-1.3, 0.3))
        if key == "popped":
            for name, img in (("night", night(tinted(atlas, glow, tint), glow)),
                              ("hit", tinted(atlas, glow, tint, DAMAGE_TINT))):
                s4.render(model, bb, save(img, atlases / f"jack_{name}.png"), r / f"jack_{name}", JACK_EYE,
                          player_at=(-1.3, 0.3))
    s2.build = build


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    r, atlases = OUT / "renders", OUT / "atlases"
    atlases.mkdir(parents=True, exist_ok=True)
    magus(r, atlases)
    jacks(r, atlases)
    contact_sheet([(r / "calm" / "eye.png", "calm (and every decoy)"),
                   (r / "tell" / "eye.png", "the tell: eyes flare (prism, snap)"),
                   (r / "shatter" / "eye.png", "a decoy struck: the mirror flash"),
                   (r / "dead" / "eye.png", "dead: the eyes go out")],
                  OUT / "states.png", "Mirrored Magus - his states")
    contact_sheet([(r / "calm" / "face.png", "his face: calm"),
                   (r / "tell" / "face.png", "his face: the tell")],
                  OUT / "states_face.png", "Mirrored Magus - his eyes, close up")
    contact_sheet([(r / "jack_popped" / "eye.png", "jack: popped, bopping"),
                   (r / "jack_winding" / "eye.png", "jack: winding down")],
                  OUT / "jack_states.png", "Mirrored Magus - the Jack-in-the-Box's states")
    contact_sheet([(r / "night" / "eye.png", "night (light ~4)"),
                   (r / "night_tell" / "eye.png", "night: the tell"),
                   (r / "hit" / "eye.png", "the red hit flash"),
                   (r / "jack_night" / "eye.png", "jack at night"),
                   (r / "jack_hit" / "eye.png", "jack: the hit flash")],
                  OUT / "readability.png", "Mirrored Magus - night and the hit flash, from a player's eye")
    print("rendered")


if __name__ == "__main__":
    main()
