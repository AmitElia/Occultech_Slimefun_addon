"""Witch Coven redesign, session 6: variants and readability (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The coven has no phases. Its variants are the roles: every sister takes every role in turn, and her brew shows which,
by BetterModel's per-bone tint over the neutral brew painted in session 5 (no texture swap, no extra bones):
  healer   green  (150, 214, 108)
  curser   purple (176, 124, 212)
  bomber   red    (220, 112, 88)
  spent    grey   (96, 96, 100)    a dead sister's brew goes dull as she slumps
The tinted bones are the ones whose names start with `glow_brew` (the brew, its foam, drips and steam, the bottles'
liquid) and `glow_cast` (the cauldron witch's cast).

Readability is checked at night (light level ~4: everything but the full-bright brew dims) and under BetterModel's red
damage tint. The tint is applied the way BetterModel applies it: the colour multiplies the texture.

Run from the repository root: python tools/art/bosses/coven_s6.py
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
from bosskit.bbmodel import FACES  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, coven_s2 as s2, coven_s3 as s3, coven_s5 as s5  # noqa: E402
from bosses import volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s6_variants"
TINTS = dict(s5.ROLE_TINT, spent=(96, 96, 100))
ROLE_NAMES = {"green": "healer", "purple": "curser", "red": "bomber", "spent": "dead"}
TINT_BONES = ("glow_brew", "glow_cast")     # BetterModel bone filter: names starting with these
DAMAGE_TINT = (255, 128, 128)               # a stand-in for BetterModel's red hit tint (multiplies like any tint)


def painted():
    """Session 5's models, islands and painted (neutral) atlas."""
    models, keys, sizes = [], [], {}
    for vessel, role, _ in s2.SISTERS:
        m = s2.build(vessel, role)
        m.name = s3.model_id(vessel)
        k = {}
        for i, c in enumerate(m.cubes):
            for f in FACES:
                w, h = v4.face_size(c, f)
                if not w or not h or b4.hidden(c, f):
                    continue
                k[(i, f)] = s5.island_key(c, f, w, h)
                sizes[k[(i, f)]] = (w, h)
        models.append(m)
        keys.append(k)
    positions, used, height = b4.pack(sizes)
    atlas = s5.build_atlas(models, keys, positions)
    return models, keys, positions, atlas


def role_atlas(atlas, positions, tint):
    img = np.array(atlas).astype(int)
    for key, (x, y, w, h) in positions.items():
        if key[4] in s5.TINTED:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] = img[y - 1:y + h + 1, x - 1:x + w + 1, :3] * np.array(tint) // 255
    return img


def lit_mask(positions, height):
    mask = np.zeros((height, 256), bool)
    for key, (x, y, w, h) in positions.items():
        if key[4] in s5.TINTED:
            mask[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return mask


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(path)
    return path


VIEWS = [
    {"name": "hero", "location": (5.5, 6.5, 4.6), "target": (0, 0.2, 1.9), "scale": 5.6, "player": False},
    {"name": "player_eye", "location": (-2.4, 6, 1.62), "target": (0, 0, 2.3), "scale": 4.8, "player": False},
]


def render(model, keys, positions, atlas_path, out):
    out.mkdir(parents=True, exist_ok=True)
    boxes = []
    for i, c in enumerate(model.cubes):
        uv = {}
        for f in FACES:
            key = keys.get((i, f))
            x, y, w, h = positions[key] if key else (0, 0, 0, 0)
            uv[f] = {"uv": [x, y, x + w, y + h]}
        boxes.append({"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
                      "glow": s5.zone_for(c) in s5.TINTED, "uv": uv})
    job = out / "render_job.json"
    job.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes, "views": VIEWS,
                               "player_at": (2.0, 1.6)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job.unlink()


def contact_sheet(states, view, out_path, title):
    tw, th, pad, top, left = 420, 315, 10, 56, 300
    img = Image.new("RGB", (left + 3 * (tw + pad), top + 26 + len(states) * (th + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(28), fill=sheet.INK)
    for c, (_, _, t) in enumerate(s2.SISTERS):
        dr.text((left + c * (tw + pad), top), t, font=sheet._font(19), fill=sheet.DIM)
    for r, (state, label) in enumerate(states.items()):
        y = top + 26 + r * (th + pad)
        dr.text((pad, y + th // 2 - 10), label, font=sheet._font(19), fill=sheet.INK)
        for c, (vessel, _, _) in enumerate(s2.SISTERS):
            img.paste(sheet._tile(OUT / "renders" / state / vessel / f"{view}.png", tw, th), (left + c * (tw + pad), y))
    img.save(out_path)


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    models, keys, positions, atlas = painted()
    lit = lit_mask(positions, atlas.height)
    atlases = {}
    for name, tint in TINTS.items():
        atlases[name] = save(role_atlas(atlas, positions, tint), OUT / "atlases" / f"{name}.png")
    # night (light ~4): everything but the full-bright brew dims and cools; the brew keeps its role colour
    for role in ("green", "purple", "red"):
        night = role_atlas(atlas, positions, TINTS[role]).astype(float)
        night[~lit, :3] *= np.array((0.85, 0.9, 1.0)) * 0.3
        atlases[f"night_{role}"] = save(night, OUT / "atlases" / f"night_{role}.png")
    # the hit flash: BetterModel tints every bone, the brew included
    for role in ("green",):
        hurt = role_atlas(atlas, positions, TINTS[role]).astype(float)
        hurt[..., :3] *= np.array(DAMAGE_TINT) / 255
        atlases[f"damage_{role}"] = save(hurt, OUT / "atlases" / f"damage_{role}.png")
    states = {"green": "healer (green)", "purple": "curser (purple)", "red": "bomber (red)",
              "spent": "dead (spent brew)", "night_green": "night, healer", "night_red": "night, bomber",
              "damage_green": "red hit flash"}
    for state in states:
        for (vessel, _, _), model, k in zip(s2.SISTERS, models, keys):
            render(model, k, positions, atlases[state], OUT / "renders" / state / vessel)
        print(state, "rendered")
    contact_sheet(states, "hero", OUT / "sheet.png", "Witch Coven - variants and readability (session 6)")
    contact_sheet({s: states[s] for s in ("night_green", "night_red", "damage_green")}, "player_eye",
                  OUT / "sheet_player_eye.png", "Witch Coven - night and the hit flash at a player's eye height")
    report = {"tints": {ROLE_NAMES[k]: list(v) for k, v in TINTS.items()}, "tint_bones": list(TINT_BONES),
              "damage_tint_stand_in": list(DAMAGE_TINT),
              "displays": {v: s3.v3.display_count(m)[0] for (v, _, _), m in zip(s2.SISTERS, models)}}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
