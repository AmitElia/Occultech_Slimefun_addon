"""The Elder of Ash, session 6: variants and readability (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

His variants are the volcano's stages. The lava (the streams, the crater) is painted near white, warm, and
BetterModel's per-bone tint multiplies a stage colour into it, so there is no texture swap. The tinted bones are
`glow_lava`, `glow_lava_cap` (the streams' tops, on the cap), `glow_crater` and
`glow_crater_blown`:
  dormant   (255, 140, 30)    above 2/3 health: orange
  awake     (190, 25, 10)     below 2/3 (after the eruption that throws the Ash Frogs): deep red, the fight's second
                              and far more dangerous stage
  blown     (176, 20, 8)      below 1/3: deep red still (the colour changes only between the two stages); the cap
                              is blown off: `cone_cap` hidden, `cone_blown` shown (broken stumps leaning out round a
                              crater twice as wide, lava welling in it)
  dead      (60, 46, 42)      it cools to dark crust as he dies (the eyes too)

Readability is checked at night (light level ~4: everything but the full-bright lava, crater, eyes and ember dims)
and under BetterModel's red damage tint, applied the way BetterModel applies it: the colour multiplies the texture.

Run from the repository root: python tools/art/bosses/ash_s6.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import ash_s3 as s3, ash_s4 as s4, ash_s5 as s5, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s6_variants"
STAGES = {"dormant": (255, 140, 30), "awake": (190, 25, 10), "blown": (176, 20, 8), "dead": (60, 46, 42)}
BLOWN = {"blown"}                            # the stages with the cap blown off
LAVA_ZONES = ("lava", "lava_hot")
TINT_BONES = ("glow_lava", "glow_lava_cap", "glow_crater", "glow_crater_blown")
DAMAGE_TINT = (255, 128, 128)               # a stand-in for BetterModel's red hit tint (multiplies like any tint)
EYE_DEAD = (70, 46, 34)

# the lava painted near white and warm (the stage tint colours it); the basalt's glowing cracks stay painted amber
s5.RAMP["crack"] = s5.LAVA
s5.RAMP["lava"] = s5.RAMP["lava_hot"] = s5.mk((150, 120, 100), (236, 220, 196), (255, 253, 246), 9)


def bone_names(cube):
    out = []
    g = cube.group
    while g is not None:
        out.append(g.name)
        g = g.parent
    return out


def hidden_in(cube, blown):
    names = bone_names(cube)
    if "cone_blown" in names:
        return not blown
    if "cone_cap" in names:
        return blown
    return False


def stage_atlas(atlas, positions, tint, eye_tint=None):
    img = np.array(atlas).astype(float)
    for key, (x, y, w, h) in positions.items():
        if key[4] in LAVA_ZONES:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] *= np.array(tint) / 255
        elif eye_tint and key[4] == "eye":
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] *= np.array(eye_tint) / 255
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


VIEWS = [
    {"name": "hero", "location": (11, 13, 8), "target": (0, -0.3, 2.8), "scale": 12.5, "player": False},
    {"name": "volcano", "location": (6, 8, 9), "target": (0, -0.4, 5.2), "scale": 6.0, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 1.9), "scale": 11.5, "player": False},
]


def render(model, bb, atlas_path, blown, out):
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": s4.zone_for(c).startswith(s4.GLOWING),
              "uv": bb["elements"][i]["faces"]}
             for i, c in enumerate(model.cubes) if not hidden_in(c, blown)]
    out.mkdir(parents=True, exist_ok=True)
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": VIEWS, "player_at": (5.6, 2.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def contact_sheet(states, labels, view, out_path, title):
    tw, th, pad, top = 420, 315, 12, 56
    img = Image.new("RGB", (pad + len(states) * (tw + pad), top + th + 40), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(26), fill=sheet.INK)
    for c, st in enumerate(states):
        x = pad + c * (tw + pad)
        img.paste(sheet._tile(OUT / "renders" / st / f"{view}.png", tw, th), (x, top))
        dr.text((x, top + th + 8), labels[st], font=sheet._font(18), fill=sheet.DIM)
    img.save(out_path)


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    model, keys, positions, used, height, atlas = s5.painted()
    neutral = OUT / "atlases" / "neutral.png"
    neutral.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(neutral)
    bb, _ = s4.rig_bbmodel(model, keys, positions, neutral, height, s3.pose_table())
    # the shipped review rig: the neutral atlas (the stage tint colours the lava in game)
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    glow = np.zeros((height, s4.SIZE), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4].startswith(s4.GLOWING):
            glow[y - 1:y + h + 1, x - 1:x + w + 1] = True
    states = {}
    for stage, tint in STAGES.items():
        img = stage_atlas(atlas, positions, tint, EYE_DEAD if stage == "dead" else None)
        states[stage] = (save(img, OUT / "atlases" / f"{stage}.png"), stage in BLOWN)
    for stage in ("dormant", "blown"):           # night (light ~4): all but the full-bright parts dim
        img = stage_atlas(atlas, positions, STAGES[stage])
        img[~glow, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
        states[f"night_{stage}"] = (save(img, OUT / "atlases" / f"night_{stage}.png"), stage in BLOWN)
    img = stage_atlas(atlas, positions, STAGES["awake"])             # the hit flash tints every bone
    img[..., :3] *= np.array(DAMAGE_TINT) / 255
    states["hit"] = (save(img, OUT / "atlases" / "hit.png"), False)
    for name, (atlas_path, blown) in states.items():
        render(model, bb, atlas_path, blown, OUT / "renders" / name)
        print(name, "rendered")
    labels = {"dormant": "dormant (above 2/3)", "awake": "awake (below 2/3)", "blown": "blown (below 1/3): the top gone",
              "dead": "dead: cooled",
              "night_dormant": "night, dormant", "night_blown": "night, blown", "hit": "red hit flash (awake)"}
    order = ["dormant", "awake", "blown", "dead"]
    contact_sheet(order, labels, "volcano", OUT / "stages_volcano.png", "The Elder of Ash - the volcano's stages, close up")
    contact_sheet(order, labels, "hero", OUT / "stages_hero.png", "The Elder of Ash - the volcano's stages")
    contact_sheet(["night_dormant", "night_blown", "hit"], labels, "player_eye", OUT / "readability.png",
                  "The Elder of Ash - night and the hit flash at a player's eye height")


if __name__ == "__main__":
    main()
