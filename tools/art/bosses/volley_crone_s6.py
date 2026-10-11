"""Volley redesign, session 6: texture polish and variants.

Volley has no phases, so his variants follow the fight; Mythic switches them with BetterModel's brightness and
part-visibility mechanics. All three are added on top of the session 5 painted model:
- wards up: while an amethyst ward stands, `crystals_back` is drawn at full brightness, so every shard lights;
- cracked: below 40% health the three big glowing shards (`glow_crystals`) are hidden and `glow_crystals_broken` is
  shown: snapped stumps with glowing cores;
- eye glint: one small amethyst glint in his right eye socket (`glow_eye`), the single face light, so he still has a
  face at night.

Readability is checked at night (light level ~4: everything but the full-bright parts dims) and under the red damage
tint. Review models for the test server: `occultech_volley_rig` (as he spawns) and `occultech_volley_rig_cracked`
(the cracked variant shown).

Run from the repository root: python tools/art/bosses/volley_crone_s6.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as s1, volley_crone_s2 as s2, volley_crone_s3 as s3  # noqa: E402
from bosses import volley_crone_s4 as s4, volley_crone_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s6_variants"
# the three big lit geode shards (session 1, direction B): dx, dy, pitch, side, length, width
LIT_SHARDS = ((0, 2, 62, 0, 22, 6), (-4, -1, 45, -30, 18, 5), (4.5, 0, 50, 32, 17, 5))


def stump(group, name, base, pitch, side, length, width):
    """A snapped shard: the lower third of the crystal and a chipped splinter standing off the break."""
    rot = (-pitch, side, 0)
    axis = s1.rotation_matrix(rot) @ np.array([0.0, 0.0, 1.0])
    body = round(length * 0.36)
    group.box(name, np.array(base, float) + axis * body / 2, (width, width, body), "glow", rotation=rot)
    chip = np.array(base, float) + axis * (body + 1) + np.array([width * 0.2, 0, 0])
    group.box(name + "_splinter", chip, (max(1, round(width * 0.4)), max(1, round(width * 0.4)), 3), "glow",
              rotation=(rot[0] + 12, rot[1] - 10, 0))


def build():
    model = s2.build()
    model.name = s3.MODEL_ID
    s4.remove_face_insets(model)
    groups = {g.name: g for g in model.groups}
    torso, head = groups["torso"], groups["h_head"]
    # the glint sits in the right eye slit (vanilla columns 1-2, doubled: x 2..6), half sunk into the socket
    eye = head.group("glow_eye", (4, 53.5, -22))
    eye.box("eye_glint", (4, 53.5, -22), (2, 1, 1), "glow")
    root = groups["crystals_back"].origin
    broken = torso.group("glow_crystals_broken", root)
    broken.visible = False
    for i, (dx, dy, pitch, side, length, width) in enumerate(LIT_SHARDS):
        stump(broken, f"stump_{i}", (dx, root[1] + dy, root[2] + 1), pitch, side, length, width)
    s2.snap(model)
    return model


def hidden(cube):
    g = cube.group
    while g is not None:
        if not g.visible:
            return True
        g = g.parent
    return False


def in_group(cube, name):
    g = cube.group
    while g is not None:
        if g.name == name:
            return True
        g = g.parent
    return False


def to_bbmodel(model, positions, atlas_path, name, show_broken):
    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": s4.SIZE, "height": s4.HEIGHT, "uv_width": s4.SIZE, "uv_height": s4.HEIGHT,
               "particle": False, "use_as_default": True, "layers_enabled": False, "render_mode": "default",
               "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
               "frame_interpolate": False, "visible": True, "internal": True, "saved": False,
               "uuid": _uuid(s3.MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    groups = {g.name: g for g in model.groups}
    groups["glow_crystals_broken"].visible = show_broken
    groups["glow_crystals"].visible = not show_broken
    old_name, model.name = model.name, name
    try:
        bb = model.to_bbmodel(texture_size=(s4.SIZE, s4.HEIGHT), textures=(texture,))
        bb["animations"] = [{"uuid": _uuid(f"{name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                             "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                             "blend_weight": "", "start_delay": "", "loop_delay": "",
                             "animators": s3.keyframes(model, pose)} for key, pose in s3.POSES.items()]
    finally:
        model.name = old_name
        groups["glow_crystals_broken"].visible = False
        groups["glow_crystals"].visible = True
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            x, y, w, h = positions[(i, f)]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if s4.zone_for(model.cubes[i]) == "glow":
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    return bb


def lit_mask(model, positions, rule):
    """A per-pixel mask of the atlas islands whose cubes match rule."""
    mask = np.zeros((s4.HEIGHT, s4.SIZE), bool)
    for (i, _), (x, y, w, h) in positions.items():
        if rule(model.cubes[i]):
            mask[y - 1:y + h + 1, x - 1:x + w + 1] = True
    return mask


def variant_atlas(atlas, mask, scale, tint=(1, 1, 1), only=None):
    """Lighting stand-ins: scale pixels outside `mask` (the full-bright parts) by a brightness and tint."""
    a = np.asarray(atlas).astype(float)
    k = np.array(tint) * scale
    target = ~mask if only is None else only
    a[target, :3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def views():
    return [v for v in s5.views() if v["name"] in ("hero", "player_eye", "back")]


def main():
    model = build()
    rects = [((i, f), *s4.face_size(c, f)) for i, c in enumerate(model.cubes) for f in FACES]
    positions, used = s4.pack(rects)
    atlas = s5.paint(model, positions, shadowed=lambda c: not hidden(c))
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_volley.png"
    atlas.save(atlas_path)
    atlas.resize((s4.SIZE * 2, s4.HEIGHT * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    for name, broken in ((s3.MODEL_ID, False), (s3.MODEL_ID + "_cracked", True)):
        bb = to_bbmodel(model, positions, atlas_path, name, broken)
        path = OUT / f"{name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    glow = lit_mask(model, positions, lambda c: s4.zone_for(c) == "glow")
    crystal = lit_mask(model, positions, lambda c: s4.zone_for(c) == "crystal")
    bright_crystal = variant_atlas(atlas, glow, 1.25, only=crystal & ~glow)
    night = variant_atlas(atlas, glow, 0.3, tint=(0.85, 0.9, 1.0))
    night_wards = variant_atlas(bright_crystal, glow | crystal, 0.3, tint=(0.85, 0.9, 1.0))
    hurt = variant_atlas(atlas, np.zeros_like(glow), 1.0, tint=(1.0, 0.5, 0.5))
    states = {
        "base": (atlas, lambda c: s4.zone_for(c) == "glow", False),
        "wards_up": (bright_crystal, lambda c: s4.zone_for(c) in ("glow", "crystal"), False),
        "cracked": (atlas, lambda c: s4.zone_for(c) == "glow", True),
        "night": (night, lambda c: s4.zone_for(c) == "glow", False),
        "night_wards_up": (night_wards, lambda c: s4.zone_for(c) in ("glow", "crystal"), False),
        "damage_tint": (hurt, lambda c: s4.zone_for(c) == "glow", False),
    }
    for key, (img, lit, broken) in states.items():
        path = OUT / "atlases" / f"{key}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        shown = [i for i, c in enumerate(model.cubes)
                 if not (in_group(c, "glow_crystals_broken") and not broken) and not (in_group(c, "glow_crystals") and broken)]
        render_states(model, positions, shown, path, OUT / "renders" / key, lit)
    contact_sheet(list(states))
    print(json.dumps({"rows_used": used, "cubes": len(model.cubes), "displays": s3.display_count(model)[0]}))


def render_states(model, positions, shown, atlas_path, out, lit):
    import subprocess
    out.mkdir(parents=True, exist_ok=True)
    boxes = []
    for i in shown:
        c = model.cubes[i]
        uv = {f: {"uv": [x, y, x + w, y + h]} for f in FACES for (x, y, w, h) in [positions[(i, f)]]}
        boxes.append({"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": lit(c), "uv": uv})
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views()}), encoding="utf-8")
    result = subprocess.run([str(s2.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def contact_sheet(states):
    names = [v["name"] for v in views()]
    tw, th, pad, top, left = 440, 330, 10, 56, 170
    img = Image.new("RGB", (left + len(names) * (tw + pad), top + len(states) * (th + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volley - variants and readability (session 6)", font=sheet._font(28), fill=sheet.INK)
    for r, state in enumerate(states):
        y = top + r * (th + pad)
        dr.text((pad, y + th // 2 - 10), state.replace("_", " "), font=sheet._font(20), fill=sheet.INK)
        for c, name in enumerate(names):
            img.paste(sheet._tile(OUT / "renders" / state / f"{name}.png", tw, th), (left + c * (tw + pad), y))
    img.save(OUT / "sheet.png")


if __name__ == "__main__":
    main()
