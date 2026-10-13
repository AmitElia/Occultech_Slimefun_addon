"""The Night Matriarch redesign, session 6: variants and readability.

Her variants are the sculk's glow. Her fight runs day or night and she is stronger at night, so the glow tells which:
BetterModel's per-bone tint multiplies a colour into the glow bones (`glow_eye`, `glow_tendrils`, `glow_gill_*`;
no texture swap). The painted glow is the brightest it gets; the tints dim it:
  day       (118, 134, 144)  dimmed: the sculk smoulders
  night     (255, 255, 255)  the full glow: she's stronger at night
  tell      (255, 255, 255)  the dive's warning: the glow flares to full whatever the hour (with the tell pose: wings
                             raised, gills flared)
  grounded  (78, 90, 98)     stunned after the impact: the sculk gutters low
  dead      (34, 38, 42)     out
Readability is checked at night (light level ~4: everything but the full-bright glow dims) and under BetterModel's red
hit tint, applied the way BetterModel applies it: the colour multiplies the texture.

Run from the repository root: python tools/art/bosses/matriarch_s6.py
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
from bosses import matriarch_s2 as s2, matriarch_s3 as s3, matriarch_s4 as s4, matriarch_s5 as s5  # noqa: E402
from bosses import volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s6_variants"
STATES = {"day": (118, 134, 144), "night": (255, 255, 255), "tell": (255, 255, 255), "grounded": (78, 90, 98),
          "dead": (34, 38, 42)}
TINT_BONES = ("glow_eye", "glow_tendrils", "glow_gill")
DAMAGE_TINT = (255, 128, 128)          # a stand-in for BetterModel's red hit tint (multiplies like any tint)
GLOW_ZONES = s4.GLOWING


def tinted(atlas, positions, tint):
    img = np.array(atlas).astype(float)
    for key, (x, y, w, h) in positions.items():
        if key[4] in GLOW_ZONES:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] *= np.array(tint) / 255
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


BELOW = [{"name": "below", "location": (-2.5, 5, 1.62), "target": (0, 0, 8.0), "scale": 14, "player": False}]
GROUND = [{"name": "eye", "location": (-5, 10, 1.62), "target": (0, 0, 0.6), "scale": 12, "player": False},
          {"name": "face", "location": (2.2, 7, 2.2), "target": (0, 2.6, 1.0), "scale": 4.2, "player": False}]


def posed(pose, alt=None):
    m = s2.build(f"s6_{pose}")
    s2.finish(m)
    spec = dict(s2.POSES[pose][1])
    if alt is not None:
        spec["alt"] = alt
    s2.pose(m, spec)
    return m


def render(model, bb, atlas_path, out, views):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": s4.zone_for(c) in GLOW_ZONES,
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views, "player_at": (5.5, 3.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


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
    glow = np.zeros((height, s4.SIZE), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in GLOW_ZONES:
            glow[y - 1:y + h + 1, x - 1:x + w + 1] = True
    paths = {name: save(tinted(atlas, positions, tint), OUT / "atlases" / f"{name}.png") for name, tint in STATES.items()}
    night = tinted(atlas, positions, STATES["night"])                 # light level ~4: all but the glow dims
    night[~glow, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
    paths["night_dark"] = save(night, OUT / "atlases" / "night_dark.png")
    hit = tinted(atlas, positions, STATES["day"])
    hit[..., :3] *= np.array(DAMAGE_TINT) / 255
    paths["hit"] = save(hit, OUT / "atlases" / "hit.png")

    r = OUT / "renders"
    glide, tell = posed("glide", 128), posed("tell", 112)
    grounded, dead = posed("grounded"), posed("death")
    for name in ("day", "night", "night_dark", "hit"):
        render(glide, bb, paths[name], r / name, BELOW)
    render(tell, bb, paths["tell"], r / "tell", BELOW)
    render(grounded, bb, paths["grounded"], r / "grounded", GROUND)
    render(grounded, bb, paths["day"], r / "grounded_day", GROUND)
    render(dead, bb, paths["dead"], r / "dead", GROUND)
    contact_sheet([(r / "day" / "below.png", "day: the sculk smoulders"),
                   (r / "night" / "below.png", "night: the full glow (stronger)"),
                   (r / "tell" / "below.png", "the dive's tell: the glow flares"),
                   (r / "grounded" / "eye.png", "grounded (stunned): guttering"),
                   (r / "dead" / "eye.png", "dead: out")],
                  OUT / "states.png", "Night Matriarch - the sculk's glow")
    contact_sheet([(r / "grounded_day" / "face.png", "her head: day"),
                   (r / "grounded" / "face.png", "her head: stunned")],
                  OUT / "states_face.png", "Night Matriarch - her glow, close up")
    contact_sheet([(r / "night_dark" / "below.png", "night (light ~4), from below"),
                   (r / "hit" / "below.png", "the red hit flash (day)")],
                  OUT / "readability.png", "Night Matriarch - night and the hit flash, from a player's eye")
    print("rendered")


if __name__ == "__main__":
    main()
