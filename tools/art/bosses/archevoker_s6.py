"""The Archevoker redesign, session 6: variants and readability (plan: docs/art/bosses/archevoker/overhaul/plan.md).

His variants are BetterModel per-bone tints (a colour multiplied into the texture, no texture swap). The glows are
now painted as a neutral white gradient (session 5's cyan and purple ramps, without their hue), so one texture takes
every state's colour:
  the priest's glow (`glow_eyes`, `glow_ring`, `glow_runes`):
    calm       (80, 220, 250)    spirit cyan: both hands alive
    tell       (200, 250, 255)   flaring: the moment a pattern or the burst is cast
    wounded    (54, 150, 176)    one hand dead: the ring and the runes dim, his eyes with them
    caught     (255, 232, 160)   cheating death: a gold-white flash while the hands hold him up
    risen      (206, 96, 255)    both hands dead: he burns violet, casting for himself
    dead       (46, 48, 56)      out
  each casting hand (`glow_eye`, `glow_circle`):
    calm       cyan (80, 220, 250) / purple (186, 104, 255)
    tell       (200, 250, 255) / (232, 196, 255): drawing a pattern on the floor
    dying      (52, 52, 60)      the light goes out as the eyelid closes
  one part swap: each casting hand has an `eyelid` bone, hidden until the hand dies, that shuts over the eye.
Readability is checked at night (light level ~4: everything but the full-bright parts dims) and under BetterModel's
red hit tint (it multiplies the texture like any tint).

Run from the repository root: python tools/art/bosses/archevoker_s6.py (after archevoker_s5.py)
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
from bosses import archevoker_s2 as s2, archevoker_s3 as s3, archevoker_s4 as s4, archevoker_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s6_variants"
NEUTRAL = [(104, 106, 116), (160, 162, 170), (214, 216, 222), (242, 244, 248), (255, 255, 255)]
PRIEST = {"calm": (80, 220, 250), "tell": (200, 250, 255), "wounded": (54, 150, 176), "caught": (255, 232, 160),
          "risen": (206, 96, 255), "dead": (46, 48, 56)}
HAND = {"cyan": {"calm": (80, 220, 250), "tell": (200, 250, 255), "dying": (52, 52, 60)},
        "purple": {"calm": (186, 104, 255), "tell": (232, 196, 255), "dying": (52, 52, 60)}}
DAMAGE_TINT = (255, 128, 128)
EYE = [{"name": "eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 3.8), "scale": 10.5, "player": False}]
HERO = [{"name": "hero", "location": (10, 14, 8), "target": (0, 0, 4.2), "scale": 11.5, "player": False}]
HAND_EYE = [{"name": "hand", "location": (1.5, 8, 1.9), "target": (0, 0, 1.8), "scale": 3.6, "player": False}]


def neutral_glows():
    """Session 5's painters with the glows' hue taken out: tints colour them in game."""
    s5.RAMP["cyan"] = NEUTRAL
    s5.RAMP["purple"] = NEUTRAL


def hand_with_lid(glow):
    """A casting hand with its eyelid: a hidden gold bone that shuts over the eye when the hand dies."""
    m = s2.hand_model(glow)
    h = next(g for g in m.groups if g.name == "hand")
    lid = h.group("eyelid", (0, 25, -3))
    lid.box("eyelid", (0, 25, -3.4), (13, 6, 1), "gold")
    lid.box("eyelid_crease", (0, 24.5, -4.1), (10, 1, 1), "gold_dark")
    lid.visible = False
    s3.fold_quarter_turns(m)
    return m


def glow_mask(positions, size, height):
    glow = np.zeros((height, size), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in s4.GLOWING:
            glow[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return glow


def tinted(atlas, glow, colour, whole=None):
    img = np.array(atlas).astype(float)
    img[glow, :3] *= np.array(colour) / 255
    if whole is not None:
        img[..., :3] *= np.array(whole) / 255
    return img


def night(img, glow):
    img = img.copy()
    img[~glow, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


def render_posed(model, positions, atlas_path, size, height, out, views):
    keys = s4.island_keys(model)
    bb, _ = s4.textured_bbmodel(model, keys, positions, atlas_path, size, height, ((0, 0, 0), (1, 1, 1)))
    s4.render(model, bb, atlas_path, out, views)


def contact_sheet(cells, out_path, title, tw=420, th=315):
    pad, top = 12, 56
    img = Image.new("RGB", (pad + len(cells) * (tw + pad), top + th + 40), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(26), fill=sheet.INK)
    for c, (path, label) in enumerate(cells):
        x = pad + c * (tw + pad)
        img.paste(sheet._tile(path, tw, th), (x, top))
        dr.text((x, top + th + 8), label, font=sheet._font(18), fill=sheet.DIM)
    img.save(out_path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    neutral_glows()
    r, at = OUT / "renders", OUT / "atlases"

    # the priest: one neutral texture, every state a tint
    model = s3.build("rest")
    model.name = s3.MODEL_ID
    keys, positions, height, atlas = s5.painted(model, s4.SIZE)
    neutral = at / f"{s3.MODEL_ID}.png"
    neutral.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(neutral)
    bb, _ = s4.textured_bbmodel(model, keys, positions, neutral, s4.SIZE, height, s2.hitbox_bounds(model),
                                s3.pose_table().items())
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    glow = glow_mask(positions, s4.SIZE, height)
    states = {name: save(tinted(atlas, glow, c), at / f"priest_{name}.png") for name, c in PRIEST.items()}
    pose_of = {"calm": "rest", "tell": "line", "wounded": "fold", "caught": "caught", "risen": "risen", "dead": "death"}
    for name, key in pose_of.items():
        render_posed(s3.build(key), positions, states[name], s4.SIZE, height, r / f"priest_{name}", HERO)
    contact_sheet([(r / f"priest_{n}" / "hero.png", n) for n in PRIEST], OUT / "priest_states.png",
                  "The Archevoker - his states as tints on one texture", tw=330, th=330)
    calm_night = save(night(tinted(atlas, glow, PRIEST["calm"]), glow), at / "priest_night.png")
    risen_night = save(night(tinted(atlas, glow, PRIEST["risen"]), glow), at / "priest_night_risen.png")
    hit = save(tinted(atlas, glow, PRIEST["calm"], DAMAGE_TINT), at / "priest_hit.png")
    render_posed(s3.build("rest"), positions, calm_night, s4.SIZE, height, r / "night", EYE)
    render_posed(s3.build("risen"), positions, risen_night, s4.SIZE, height, r / "night_risen", EYE)
    render_posed(s3.build("rest"), positions, hit, s4.SIZE, height, r / "hit", EYE)

    # the casting hands: open and calm, telling, dead with the eyelid shut
    cells = []
    for colour in ("cyan", "purple"):
        hm = hand_with_lid(colour)
        name = f"occultech_archevoker_hand_{colour}_rig"
        hm.name = name
        hkeys, hpos, hheight, hatlas = s5.painted(hm, s4.HAND_SIZE)
        hneutral = at / f"{name}.png"
        hatlas.save(hneutral)
        hbb, _ = s4.textured_bbmodel(hm, hkeys, hpos, hneutral, s4.HAND_SIZE, hheight, s2.HAND_HITBOX)
        hpath = OUT / f"{name}.bbmodel"
        hpath.write_text(json.dumps(hbb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(hpath, s3.SERVER_MODELS / hpath.name)
        hglow = glow_mask(hpos, s4.HAND_SIZE, hheight)
        open_hand = hand_with_lid(colour)
        lid = [c for c in open_hand.cubes if c.name.startswith("eyelid")]
        for c in lid:                                        # rendered open: the lid stays hidden in game
            open_hand.cubes.remove(c)
            c.group.children.remove(c)
        for state, c in HAND[colour].items():
            tex = save(tinted(hatlas, hglow, c), at / f"{colour}_{state}.png")
            shown = hm if state == "dying" else open_hand
            render_posed(shown, hpos, tex, s4.HAND_SIZE, hheight, r / f"{colour}_{state}", HAND_EYE)
            cells.append((r / f"{colour}_{state}" / "hand.png", f"{colour}: {state}"))
        hnight = save(night(tinted(hatlas, hglow, HAND[colour]["calm"]), hglow), at / f"{colour}_night.png")
        render_posed(open_hand, hpos, hnight, s4.HAND_SIZE, hheight, r / f"{colour}_night", HAND_EYE)
        cells.append((r / f"{colour}_night" / "hand.png", f"{colour}: at night"))
    contact_sheet(cells[:4], OUT / "hands_cyan.png", "The cyan hand - calm, telling, dead (the eyelid shut), night",
                  tw=300, th=300)
    contact_sheet(cells[4:], OUT / "hands_purple.png", "The purple hand - calm, telling, dead, night", tw=300, th=300)
    contact_sheet([(r / "night" / "eye.png", "night (light ~4)"), (r / "night_risen" / "eye.png", "night: risen"),
                   (r / "hit" / "eye.png", "the red hit flash")],
                  OUT / "readability.png", "The Archevoker - night and the hit flash, from a player's eye")
    print("variants done")


if __name__ == "__main__":
    main()
