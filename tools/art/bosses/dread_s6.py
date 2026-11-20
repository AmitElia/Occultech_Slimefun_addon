"""Dread Riders, session 6: variants and readability (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

The glows are painted neutral (near-white) and tinted per state with BetterModel's per-bone tint, so one model serves
every moment of the fight. Glow bones: `glow_eyes` on both mounts, `glow_sigil` (the charger's chest boss),
`glow_arrow` (the nocked arrow's head) and `glow_rune` (the mirror plate's rune) on the Outrider.

The Vanguard (crimson):
    calm      crimson: riding, the lance sweep, the spear throw
    tell      white-hot red: the charge's wind-up (the rear) and the charge itself
    stunned   a dull ember: the 2 s after a charge cut short, "hit me now"
    enraged   the Outrider's storm cyan: the Outrider has fallen and the Vanguard takes up its storm
    dead      out
The Outrider (hollow cyan):
    calm      cyan: circling, volleys
    lock      white-cyan: the snipe's aiming line has locked; the arrow is about to loose
    enraged   the Vanguard's crimson: the Vanguard has fallen; the archer fires faster and closer in its colour
    dead      out
The survivor taking the fallen rider's colour is the enrage's tell (the plan's idea from the restart's first round of
notes). No part swaps: the riders' moments are poses (session 2) and clips (session 7). Readability is checked at night
(light ~4: everything but the glows at 30%) and under BetterModel's red hit flash.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument (run it after
session 5: it writes the neutral-glow review rigs to run/plugins/BetterModel/models with --server):
python tools/art/bosses/dread_s6.py <client folder> [--server]
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s2 as a2, archevoker_s4 as a4, archevoker_s5 as a5, archevoker_s6 as a6  # noqa: E402
from bosses import dread_s2 as s2, dread_s3 as s3, dread_s4 as s4, dread_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s6_variants"
STATES = {
    "vanguard": {"calm": (232, 48, 56), "tell": (255, 176, 150), "stunned": (96, 30, 30), "enraged": (96, 236, 226),
                 "dead": (44, 36, 38)},
    "outrider": {"calm": (96, 236, 226), "lock": (214, 255, 246), "enraged": (232, 48, 56), "dead": (40, 44, 46)},
}
GLOW_MATS = ("cyan", "crimson")


def glow_mask(model, keys, positions, shape):
    """Every atlas texel that belongs to a glow cube (the tint applies to those bones only)."""
    mask = np.zeros(shape, bool)
    for (i, f), key in keys.items():
        if model.cubes[i].mat in GLOW_MATS and key in positions:
            x, y, w, h = positions[key]
            mask[y:y + h, x:x + w] = True
    return mask


def img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def main(argv):
    assets = Path(argv[0]) / "assets/minecraft/textures/entity"
    for key, rel in (("zombie", "zombie/zombie.png"), ("skeleton", "skeleton/skeleton.png"),
                     ("horse_zombie", "horse/horse_zombie.png"), ("horse_skeleton", "horse/horse_skeleton.png")):
        s4.TEX[key] = np.array(Image.open(assets / rel).convert("RGBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(s4.ZONES)
    a2.PALETTE = dict(s2.PALETTE)
    a4.ZONES, a4.GLOWING = s4.ZONES, s4.GLOWING
    for z in GLOW_MATS:                       # the glows' hue comes out: the tints colour them in game
        s5.RAMP[z] = a6.NEUTRAL
        s5.MID[z] = 2
    for kind in ("vanguard", "outrider"):
        P = s3.build_pair(kind)
        bbs, atlases, masks = [], [], []
        for part, model, name, hb, poses in (("mount", P["mount"], f"occultech_dread_{kind}_mount_rig", None, P["mount_poses"]),
                                             ("rider", P["rider"], f"occultech_dread_{kind}_rig", P["hitbox"], P["rider_poses"])):
            keys = s4.island_keys(model)
            atlas, positions, height = s5.painted_atlas(kind, part, model, keys)
            path = OUT / f"{name}.png"
            atlas.save(path)
            mask = glow_mask(model, keys, positions, (height, s4.SIZE))
            s3.scale_model(model)
            bb, _ = s4.textured(model, name, keys, positions, path, height, s3.scaled_hitbox(hb), s3.scaled_poses(poses))
            p = OUT / f"{name}.bbmodel"
            p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
            if "--server" in argv and s3.SERVER_MODELS.is_dir():
                shutil.copyfile(p, s3.SERVER_MODELS / p.name)
            bbs.append(bb)
            atlases.append(np.array(atlas).astype(float))
            masks.append(mask)
        P["seat"] = np.array(P["seat"]) * s3.SCALE
        views = s4.views_for(P)
        hero = [v for v in views if v["name"] == "hero"]
        heads = [v for v in views if v["name"] in ("rider_head", "horse_head")]
        low = [dict(v, name="low") for v in views if v["name"] == "player_eye"]
        rows = []
        for state, colour in STATES[kind].items():
            tinted = [img(a6.tinted(a, m, colour)) for a, m in zip(atlases, masks)]
            s4.pair_render(kind, P, bbs, tinted, OUT / kind / state, hero + heads)
            rows.append((state, OUT / kind / state))
        calm = [a6.tinted(a, m, STATES[kind]["calm"]) for a, m in zip(atlases, masks)]
        s4.pair_render(kind, P, bbs, [img(a6.night(c, m)) for c, m in zip(calm, masks)], OUT / kind / "night", low)
        s4.pair_render(kind, P, bbs, [img(a6.tinted(a, m, STATES[kind]["calm"], whole=a6.DAMAGE_TINT))
                                      for a, m in zip(atlases, masks)], OUT / kind / "hit", low)
        last = list(STATES[kind])[-2]           # the enrage at night: the survivor's new colour in the dark
        s4.pair_render(kind, P, bbs, [img(a6.night(a6.tinted(a, m, STATES[kind][last]), m))
                                      for a, m in zip(atlases, masks)], OUT / kind / "night_enraged", low)
        paths, labels = [], []
        for state, d in rows:
            for v in hero + heads:
                paths.append(d / f"{v['name']}.png")
                labels.append(f"{state}: {v['name'].replace('_', ' ')}")
        a5.grid(paths, labels, OUT / f"states_{kind}.png", f"Dread Riders: the {kind.title()}'s glow states (session 6)",
                cols=3, tw=470, th=352)
        a5.grid([OUT / kind / f / "low.png" for f in ("night", "night_enraged", "hit")],
                ["night (light ~4), calm", f"night, {last}", "the red hit flash"], OUT / f"readability_{kind}.png",
                f"Dread Riders: the {kind.title()} at night and under the hit flash", cols=3, tw=470, th=352)
        print("variants", kind)


if __name__ == "__main__":
    main(sys.argv[1:])
