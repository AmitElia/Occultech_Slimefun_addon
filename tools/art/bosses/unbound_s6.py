"""The Unbound redesign, session 6: variants and readability (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

His variants are the fire's stages. He speeds up as he loses health, and the fire in his chest grows with him. The
fire is painted near white (session 5), and BetterModel's per-bone tint multiplies a stage colour into it (no
texture swap). Flames licking up out of the grate are their own bone, `glow_flames`, hidden until the fire grows:
  embers    (230, 96, 40)    above 2/3 health: a low red-orange glow behind the grate, no flames
  burning   (255, 150, 60)   below 2/3: orange, the flames shown
  inferno   (255, 236, 200)  below 1/3, enraged: white-hot, the flames shown
  sated     (150, 60, 36)    the 3 s after he devours a thrall: dull coals, the flames hidden
  dead      (52, 40, 38)     the fire goes out as he falls
The tinted bones are `glow_chest` (the fire behind the grate) and `glow_flames`.

Readability is checked at night (light level ~4: everything but the full-bright fire and eye dims) and under
BetterModel's red damage tint, applied the way BetterModel applies it: the colour multiplies the texture.

Run from the repository root: python tools/art/bosses/unbound_s6.py
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
from bosses import unbound_s3 as s3, unbound_s4 as s4, unbound_s5 as s5, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s6_variants"
STAGES = {"embers": (230, 96, 40), "burning": (255, 150, 60), "inferno": (255, 236, 200), "sated": (150, 60, 36),
          "dead": (52, 40, 38)}
FLAMES = {"embers": False, "burning": True, "inferno": True, "sated": False, "dead": False}
FIRE_ZONES = ("fire", "fire_hot")
TINT_BONES = ("glow_chest", "glow_flames")
DAMAGE_TINT = (255, 128, 128)               # a stand-in for BetterModel's red hit tint (multiplies like any tint)
GLOW_ZONES = ("fire", "fire_hot", "eye", "eye_hot", "eye_dim")


def stage_atlas(atlas, positions, tint):
    img = np.array(atlas).astype(float)
    for key, (x, y, w, h) in positions.items():
        if key[4] in FIRE_ZONES:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] *= np.array(tint) / 255
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


VIEWS = [
    {"name": "front", "location": (0, 10, 1.9), "target": (0, 0, 1.9), "scale": 4.6, "player": False},
    {"name": "player_eye", "location": (-2.4, 5.5, 1.62), "target": (0, 0, 2.4), "scale": 4.8, "player": False},
    {"name": "chest", "location": (1.2, 5.0, 2.4), "target": (0, 0.6, 2.2), "scale": 2.2, "player": False},
]


def render(model, bb, atlas_path, flames, out):
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
              "glow": s4.zone_for(c) in GLOW_ZONES, "uv": bb["elements"][i]["faces"]}
             for i, c in enumerate(model.cubes) if flames or not s5.hidden(c)]
    out.mkdir(parents=True, exist_ok=True)
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": VIEWS, "player_at": (2.6, 1.0)}), encoding="utf-8")
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
    k, model, keys, positions, used, height, atlas = s5.painted()
    neutral = OUT / "atlases" / "neutral.png"
    neutral.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(neutral)
    bb, _ = s4.rig_bbmodel(model, keys, positions, neutral, height, s3.pose_table(k))
    glow = np.zeros((height, s4.SIZE), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in GLOW_ZONES:
            glow[y - 1:y + h + 1, x - 1:x + w + 1] = True
    states = {}
    for stage, tint in STAGES.items():
        states[stage] = (save(stage_atlas(atlas, positions, tint), OUT / "atlases" / f"{stage}.png"), FLAMES[stage])
    for stage in ("embers", "inferno"):            # night (light ~4): all but the full-bright fire and eye dim
        img = stage_atlas(atlas, positions, STAGES[stage])
        img[~glow, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
        states[f"night_{stage}"] = (save(img, OUT / "atlases" / f"night_{stage}.png"), FLAMES[stage])
    img = stage_atlas(atlas, positions, STAGES["burning"])             # the hit flash tints every bone
    img[..., :3] *= np.array(DAMAGE_TINT) / 255
    states["hit"] = (save(img, OUT / "atlases" / "hit.png"), True)
    for name, (path, flames) in states.items():
        render(model, bb, path, flames, OUT / "renders" / name)
        print(name, "rendered")
    labels = {"embers": "embers (above 2/3 health)", "burning": "burning (below 2/3), flames", "inferno":
              "inferno (below 1/3, enraged)", "sated": "sated: coals", "dead": "dead: out",
              "night_embers": "night, embers", "night_inferno": "night, inferno", "hit": "red hit flash (burning)"}
    contact_sheet(["embers", "burning", "inferno", "sated", "dead"], labels, "chest", OUT / "stages_chest.png",
                  "The Unbound - the fire's stages, close up")
    contact_sheet(["embers", "burning", "inferno", "sated", "dead"], labels, "front", OUT / "stages_front.png",
                  "The Unbound - the fire's stages")
    contact_sheet(["night_embers", "night_inferno", "hit"], labels, "player_eye", OUT / "readability.png",
                  "The Unbound - night and the hit flash at a player's eye height")


if __name__ == "__main__":
    main()
