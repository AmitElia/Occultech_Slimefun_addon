"""Brood Mother redesign, session 6: texture polish and variants.

Review fixes from session 5 went in at their source, so every stage regenerates the same model:
- candles are vanilla's lit candles at twice vanilla's size (brood_s2.candle; painted from vanilla's lit white
  candle in brood_s5): a 4-wide body (2-wide for small ones) with vanilla's two-column shading and warm band, a wick of
  two crossed planes, and a clear flame of two crossed planes painted from vanilla's flame particle, always upright;
- the wax is drippier: runs of wax hang over the edge of every step of every lump and from the edge of the abdomen,
  some ending in a bead, and run down the candles (brood_s2.drips, lump_steps).

Brood Mother has no phases, so her variant follows her health: her candles go out as she weakens. The flames are
already grouped by area, so Mythic only hides bones (BetterModel part visibility), with no texture swap:
  75%  the knee and flank candles go out   (glow_leg_*_knee, glow_flank_flames)
  50%  the thorax and head candles go out  (glow_thorax_flames, glow_head_flames)
  25%  the wax pile goes out               (glow_pile_flames): only her red eyes still glow

Readability is checked at night (light level ~4: everything but the full-bright parts dims) and under the red damage
tint. The review model for the test server is `occultech_brood_mother_rig`.

Run from the repository root: python tools/art/bosses/brood_s6.py
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
from bosses import brood_s3 as s3, brood_s4 as s4, brood_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s6_variants"
KNEES = ("glow_leg_r1_knee", "glow_leg_l0_knee", "glow_leg_l2_knee")
SNUFF = {   # health left -> flame bones out by then
    "health_100": (),
    "health_75": KNEES + ("glow_flank_flames",),
    "health_50": KNEES + ("glow_flank_flames", "glow_thorax_flames", "glow_head_flames"),
    "health_25": KNEES + ("glow_flank_flames", "glow_thorax_flames", "glow_head_flames", "glow_pile_flames"),
}


def in_group(cube, names):
    g = cube.group
    while g is not None:
        if g.name in names:
            return True
        g = g.parent
    return False


def lit_mask(model, keys, positions, height):
    """A per-pixel mask of the atlas islands drawn full-bright (eyes and flames)."""
    mask = np.zeros((height, s4.SIZE), bool)
    for (i, _), key in keys.items():
        if model.cubes[i].mat in s4.GLOW_ZONES:
            x, y, w, h = positions[key]
            mask[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return mask


def variant_atlas(atlas, mask, scale, tint=(1, 1, 1)):
    """Lighting stand-in: scale pixels outside `mask` (the full-bright parts) by a brightness and tint."""
    a = np.asarray(atlas).astype(float)
    a[~mask, :3] *= np.array(tint) * scale
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def views():
    return [v for v in s5.views() if v["name"] in ("hero", "player_eye", "back")]


def render_state(model, keys, positions, atlas_path, out, hidden_bones):
    out.mkdir(parents=True, exist_ok=True)
    boxes = []
    for i, c in enumerate(model.cubes):
        if in_group(c, hidden_bones):
            continue
        uv = {}
        for f in FACES:
            key = keys.get((i, f))
            x, y, w, h = positions[key] if key else (0, 0, 0, 0)
            uv[f] = {"uv": [x, y, x + w, y + h]}
        boxes.append({"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
                      "glow": c.mat in s4.GLOW_ZONES, "uv": uv})
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views(), "player_at": (5.5, 2.5)}), encoding="utf-8")
    result = subprocess.run([str(s4.v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def contact_sheet(states):
    names = [v["name"] for v in views()]
    tw, th, pad, top, left = 440, 330, 10, 56, 330
    img = Image.new("RGB", (left + len(names) * (tw + pad), top + len(states) * (th + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Brood Mother - variants and readability (session 6)", font=sheet._font(28), fill=sheet.INK)
    for r, (state, label) in enumerate(states.items()):
        y = top + r * (th + pad)
        dr.text((pad, y + th // 2 - 10), label, font=sheet._font(19), fill=sheet.INK)
        for c, name in enumerate(names):
            img.paste(sheet._tile(OUT / "renders" / state / f"{name}.png", tw, th), (left + c * (tw + pad), y))
    img.save(OUT / "sheet.png")


def main():
    model, keys, atlas, positions, used, height = s5.painted()
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_brood_mother.png"
    atlas.save(atlas_path)
    atlas.resize((s4.SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb = s5.to_bbmodel(model, keys, positions, height, atlas_path)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    glow = lit_mask(model, keys, positions, height)
    night = variant_atlas(atlas, glow, 0.3, tint=(0.85, 0.9, 1.0))
    hurt = variant_atlas(atlas, np.zeros_like(glow), 1.0, tint=(1.0, 0.5, 0.5))
    atlases = {"base": atlas_path}
    for name, img in (("night", night), ("damage_tint", hurt)):
        p = OUT / "atlases" / f"{name}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p)
        atlases[name] = p
    states = {
        "health_100": ("full health: every candle lit", "base", SNUFF["health_100"]),
        "health_75": ("75%: knees and flank out", "base", SNUFF["health_75"]),
        "health_50": ("50%: thorax and head out", "base", SNUFF["health_50"]),
        "health_25": ("25%: the pile out, eyes only", "base", SNUFF["health_25"]),
        "night": ("night, full health", "night", SNUFF["health_100"]),
        "night_25": ("night, 25%", "night", SNUFF["health_25"]),
        "damage_tint": ("red damage tint", "damage_tint", SNUFF["health_100"]),
    }
    for key, (_, atlas_name, hidden) in states.items():
        render_state(model, keys, positions, atlases[atlas_name], OUT / "renders" / key, hidden)
    contact_sheet({k: v[0] for k, v in states.items()})
    report = {"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions), "cubes": len(model.cubes),
              "drips": sum(1 for c in model.cubes if "_drip" in c.name or "_bead_" in c.name),
              "displays": s3.v3.display_count(model)[0], "snuff": {k: list(v) for k, v in SNUFF.items()}}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("atlas", "rows_used", "cubes", "drips", "displays")}))


if __name__ == "__main__":
    main()
