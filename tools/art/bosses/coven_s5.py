"""Witch Coven redesign, session 5: texture painting (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

Paints the session 4 layout (one shared 256 x 256 atlas for the three sisters, same islands):
- vanilla's witch in its own colours, aged: a purple robe with deep folds and vanilla's green stripe down its front,
  a ragged hem (a cut-out plane: torn teeth and holes, so it reads as rags as she hovers), a brown coat with seams,
  a patch and worn edges, sleeves creased at the elbow, frayed dark cuffs;
- the face: pale skin with forehead wrinkles, crow's feet, sagging cheeks and age spots, grey hair hanging from under
  the hat at the back and sides, a bristly brow, purple eyes with a dark pupil and a catch-light, the nose with a
  nostril line, the brown mole;
- vanilla's near-black felt hat with a lit brim edge and a green band with a buckle;
- iron in vanilla's cauldron greys: a darker border round each panel, rust spots, soot low down, a bright lip;
  twisted rope, a stitched leather strap, glass with a highlight, cork;
- **the brew in neutral greys** (brew, foam, drips, steam, the bottles' liquid, the cast): in game the fight tints
  those bones the role colour (BetterModel's per-bone tint multiplies the texture), so the greys carry only the
  shading. Previews and the review rigs show each sister with her brew tinted;
- form only, no painted light direction: ambient occlusion baked from the real geometry. Shared body islands take
  their occlusion from the body alone, so one sister's ropes or pot never print on another's robe.

Run from the repository root: python tools/art/bosses/coven_s5.py
"""
import base64
import json
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, brood_s5 as b5, coven_s2 as s2, coven_s3 as s3, coven_s4 as s4  # noqa: E402
from bosses import volley_crone_s3 as v3, volley_crone_s4 as v4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s5_paint"
noise = v5.noise
ROLE_TINT = {"green": (120, 235, 90), "purple": (176, 84, 230), "red": (232, 76, 60)}
TINTED = ("brew", "foam", "steam")          # zones on the tinted glow bones, painted in neutral greys

# Ramps, dark to light, hue-shifted (shadows cool or violet, lights warm). Session 4's flat colour is one level of each.
RAMP = {
    "robe": [(12, 3, 22), (24, 9, 38), (36, 15, 56), (52, 24, 78), (66, 34, 96), (86, 50, 114)],
    "coat": [(26, 20, 14), (40, 32, 21), (56, 46, 30), (78, 64, 42), (98, 82, 56), (124, 106, 76)],
    "cuff": [(12, 10, 9), (22, 18, 15), (30, 25, 20), (44, 37, 29)],
    "skin": [(98, 86, 82), (124, 112, 102), (148, 136, 120), (171, 159, 141), (190, 180, 162), (210, 202, 186)],
    "mole": [(66, 38, 28), (94, 56, 36), (117, 71, 47), (146, 96, 68)],
    "brow": [(66, 62, 60), (102, 98, 94), (140, 136, 130), (180, 176, 168)],     # grey, bushy old brows
    "eye": [(40, 18, 56), (92, 50, 118), (138, 84, 164), (186, 140, 206), (236, 220, 244)],
    "hair": [(104, 102, 100), (140, 137, 132), (174, 170, 164), (208, 204, 196)],
    "hat": [(10, 9, 14), (18, 17, 22), (30, 29, 35), (46, 44, 52), (62, 60, 70), (82, 80, 92)],
    "band": [(24, 44, 24), (36, 64, 32), (52, 88, 44), (74, 116, 58), (112, 162, 82)],
    "iron": [(28, 28, 34), (42, 42, 48), (56, 56, 62), (74, 74, 80), (94, 94, 100), (118, 118, 124), (146, 146, 152)],
    "rust": [(84, 48, 34), (112, 70, 44), (140, 94, 60)],
    "rope": [(80, 62, 38), (108, 88, 56), (146, 124, 82), (180, 158, 110)],
    "strap": [(66, 44, 28), (94, 66, 40), (122, 88, 54), (152, 114, 74)],
    "buckle": [(92, 84, 62), (150, 140, 110), (200, 190, 154)],
    "glass": [(106, 132, 138), (146, 172, 178), (178, 202, 204), (224, 238, 238)],
    "cork": [(80, 58, 36), (102, 76, 48), (126, 96, 62), (154, 122, 84)],
    "herb": [(40, 50, 28), (60, 72, 40), (86, 98, 58), (114, 126, 78)],
    "bone": [(136, 126, 104), (170, 160, 136), (200, 190, 164), (228, 220, 198)],
    "neutral": [(118, 118, 118), (158, 158, 158), (194, 194, 194), (224, 224, 224), (248, 248, 248)],
}
# zone -> (ramp, base level)
ZONE = {"robe": ("robe", 3), "robe_hem": ("robe", 1), "coat": ("coat", 3), "coat_dark": ("coat", 1),
        "cuff": ("cuff", 2), "skin": ("skin", 3), "nose": ("skin", 2), "mole": ("mole", 2), "brow": ("brow", 2),
        "eye": ("eye", 2), "hat": ("hat", 3), "hat_tip": ("hat", 1), "band": ("band", 2), "iron": ("iron", 4),
        "iron_dark": ("iron", 2), "rope": ("rope", 2), "strap": ("strap", 2), "buckle": ("buckle", 1),
        "glass": ("glass", 2), "cork": ("cork", 2), "herb": ("herb", 2), "bone": ("bone", 2),
        "brew": ("neutral", 2), "foam": ("neutral", 4), "steam": ("neutral", 3)}


def zone_for(cube):
    """Session 4's zones, with every role colour folded into one neutral brew, foam or steam."""
    z = s4.zone_for(cube)
    for t in TINTED:
        if z.startswith(t + "_"):
            return t
    return z


def island_key(cube, face, w, h):
    name = cube.name
    if name.startswith("left_"):
        name = "right_" + name[5:]
    return (name, face, w, h, zone_for(cube))


def in_subtree(cube, names):
    g = cube.group
    while g is not None:
        if g.name in names:
            return True
        g = g.parent
    return False


def is_body(cube):
    """A part every sister shares (its islands are shared too)."""
    return not in_subtree(cube, {"vessel", "pot_carry", "bottle_held", "glow_cast"}) and not cube.name.startswith("rope_")


# ---- painters: level maps on a ramp --------------------------------------------------------------------------------

def from_levels(lv, ramp, alpha=None):
    lv = np.clip(lv, 0, len(ramp) - 1)
    rgb = np.array(ramp, np.uint8)[lv]
    a = np.full(lv.shape + (1,), 255, np.uint8) if alpha is None else alpha[..., None].astype(np.uint8)
    return np.concatenate([rgb, a], -1)


def paint_levels(cube, face, w, h, seed):
    zone = zone_for(cube)
    ramp, base = ZONE[zone]
    lv = np.full((h, w), base, int)
    upright = face not in ("up", "down")
    n = cube.name
    for y in range(h):
        for x in range(w):
            r = noise(seed, x, y)
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if zone in ("robe", "robe_hem"):
                fold = (x + seed % 3) % 4
                if upright and fold == 0:
                    lv[y, x] -= 1                                   # deep vertical folds
                elif upright and fold == 2 and noise(seed + 3, x, y, 3) < 500:
                    lv[y, x] += 1                                   # the lit ridge between them
                if n == "robe_lower_box" and face == "north" and abs(x - (w - 1) / 2) < 1:
                    lv[y, x] = -10                                  # vanilla's green stripe down the front
            elif zone in ("coat", "coat_dark"):
                if r < 70:
                    lv[y, x] -= 1                                   # grime in clusters
                elif r > 950:
                    lv[y, x] += 1
                if upright and y == 0:
                    lv[y, x] += 1                                   # worn top edges
                if n.startswith("robe_upper") and face == "north" and abs(x - (w - 1) / 2) < 1:
                    lv[y, x] -= 2                                   # the coat's front opening
                if n == "robe_upper_h" and face == "east" and 3 <= y <= 7 and 2 <= x <= 6:
                    lv[y, x] = 4 if not (y in (3, 7) or x in (2, 6)) else (2 if (x + y) % 2 else 4)   # a patch, stitched
                if n.endswith("_sleeve") and upright and y % 4 == 3:
                    lv[y, x] -= 1                                   # creases down the sleeve
            elif zone == "cuff":
                if upright and y == h - 1 and noise(seed + 5, x, 0, 1) < 400:
                    lv[y, x] += 1                                   # frayed threads at the end
            elif zone in ("skin", "nose"):
                if r < 60:
                    lv[y, x] -= 1                                   # age spots
            elif zone == "brow":
                lv[y, x] += 1 if (x % 2 == 0 and y == 0) else (-1 if x % 3 == 1 else 0)   # bristles
            elif zone == "mole":
                lv[y, x] += 1 if y == 0 else 0
            elif zone in ("hat", "hat_tip"):
                if r < 90:
                    lv[y, x] -= 1                                   # felt
                elif r > 930:
                    lv[y, x] += 1
                if n == "hat_brim" and face == "up" and edge == 0:
                    lv[y, x] += 2                                   # the brim's lit edge
                if n == "hat_brim" and face == "down":
                    lv[y, x] = 1
            elif zone == "band":
                if upright and y in (0, h - 1):
                    lv[y, x] -= 1
            elif zone in ("iron", "iron_dark"):
                if edge == 0 and min(w, h) > 3:
                    lv[y, x] -= 1                                   # a darker border round each panel
                elif r < 50 and zone == "iron":
                    lv[y, x] = -20                                  # rust (painted from the rust ramp)
                elif r > 940:
                    lv[y, x] += 1
                if upright and h >= 8 and y >= h - 2:
                    lv[y, x] -= 1                                   # soot low down
                if "lip" in n and face == "up":
                    lv[y, x] += 2                                   # the rim catches the light
            elif zone == "rope":
                lv[y, x] += -1 if (x + y) % 3 == 0 else (1 if (x + y) % 3 == 1 else 0)   # a twist
            elif zone == "strap":
                if upright and (x + y) % 2 == 0 and (x in (0, w - 1) or y in (0, h - 1)):
                    lv[y, x] += 1                                   # stitches along the edges
            elif zone == "glass":
                lv[y, x] += 2 if x == 0 else (-1 if y == h - 1 else 0)     # a highlight down one side
            elif zone in ("cork", "herb", "bone"):
                lv[y, x] += 1 if r > 850 else (-1 if r < 150 else 0)
            elif zone == "brew":
                blot = noise(seed + 17, x, y, 3)
                lv[y, x] += 1 if blot > 720 else (-1 if blot < 160 else 0)          # soft blotches in the brew
            elif zone == "foam":
                lv[y, x] -= 1 if edge == 0 and min(w, h) > 2 else 0
            elif zone == "steam":
                lv[y, x] += 1 if (face == "up" or y == 0) else 0
    return lv


def paint_head(face, w, h, seed):
    """The face and head: wrinkles, crow's feet, sagging cheeks, age spots; grey hair from under the hat."""
    lv = np.full((h, w), 3, int)
    hair = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            if noise(seed, x, y) < 60:
                lv[y, x] -= 1
            if face == "north":
                if y in (1, 3) and 2 <= x <= w - 3 and noise(seed + 1, x, y, 1) < 700:
                    lv[y, x] -= 1                                   # forehead wrinkles under the hat
                if 5 <= y <= 7 and x in (0, 1, w - 2, w - 1):
                    lv[y, x] -= 1 if (y + x) % 2 else 0             # crow's feet beside the eyes
                if 9 <= y <= 12 and (x <= 2 or x >= w - 3):
                    lv[y, x] -= 1                                   # sagging cheeks
                if y == h - 1:
                    lv[y, x] -= 1
            elif face in ("south", "east", "west"):
                back = face == "south" or (x < w // 2 if face == "east" else x >= w // 2)
                strand = noise(seed + 2, x, 0, 1)
                if back and y < 6 + strand % 6:
                    hair[y, x] = True                               # grey hair hanging from under the hat
    out = from_levels(lv - 0, RAMP["skin"])
    if hair.any():
        hl = np.clip(2 + (np.arange(w)[None, :] % 3 == 0) - (np.arange(w)[None, :] % 3 == 2), 0, 3)
        hl = np.broadcast_to(hl, (h, w))
        hair_rgb = from_levels(hl, RAMP["hair"])
        out[hair] = hair_rgb[hair]
    return out


def paint_eye(face, w, h):
    lv = np.full((h, w), 2, int)
    if face == "north":
        lv[:, w // 2 - (w > 1): w // 2 + 1] = 0                     # the dark pupil
        lv[0, 0] = 4                                                # a catch-light
    return from_levels(lv, RAMP["eye"])


def paint_hem(cube, face, w, h, seed):
    """A ragged hem plane: torn teeth down its lower edge and a few holes, cut out with alpha."""
    lv = paint_levels(cube, face, w, h, seed)
    alpha = np.full((h, w), 255, np.uint8)
    for x in range(w):
        tear = noise(seed + 11, x, 0, 1) % 4                        # how far this strip is torn up from the bottom
        alpha[h - tear:, x] = 0 if tear else 255
    for y in range(1, h - 1):
        for x in range(w):
            if noise(seed + 13, x, y, 1) < 40:
                alpha[y, x] = 0                                     # moth holes
    lv[0, :] += 1                                                   # the seam where it hangs from the robe
    return from_levels(lv, RAMP["robe"], alpha)


def paint_face(model, i, face, w, h, solids_all, solids_body):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = zone_for(cube)
    if cube.name.startswith("hem_"):
        return paint_hem(cube, face, w, h, seed)
    if cube.name == "head":
        out = paint_head(face, w, h, seed)
    elif zone == "eye":
        return paint_eye(face, w, h)
    else:
        lv = paint_levels(cube, face, w, h, seed)
        ramp = RAMP[ZONE[zone][0]]
        stripe = lv == -10
        rust = lv == -20
        if zone not in TINTED:
            ao = b5.occlusion(model, i, face, w, h, solids_body if is_body(cube) else solids_all)
            lv = lv - (ao >= 0.34) - (ao >= 0.6)
        out = from_levels(np.clip(lv, 0, len(ramp) - 1), ramp)
        if stripe.any():
            out[stripe] = from_levels(np.full((h, w), 1, int), RAMP["band"])[stripe]
        if rust.any():
            out[rust] = from_levels(np.full((h, w), 1, int), RAMP["rust"])[rust]
        return out
    ao = b5.occlusion(model, i, face, w, h, solids_body)
    shade = (ao >= 0.34).astype(int) + (ao >= 0.6)
    if shade.any():                                                 # the hat's brim and the nose shade the face
        darker = from_levels(np.full((h, w), 2, int), RAMP["skin"])
        out[shade > 0] = (out[shade > 0].astype(int) * 3 // 4 + darker[shade > 0].astype(int) // 4).astype(np.uint8)
    return out


def build_atlas(models, keys, positions):
    owner = {}
    for mi, k in enumerate(keys):
        for (i, f), key in sorted(k.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
            owner.setdefault(key, (mi, i, f))
    solids = []
    for m in models:
        everything = b5.solids_of(m)
        body = [s for s in everything if is_body(m.cubes[s[0]])]
        solids.append((everything, body))
    height = max(y + h for (_, y, _, h) in positions.values()) + 1
    height = 256 if height <= 256 else 512
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        mi, i, f = owner[key]
        cube = models[mi].cubes[i]
        patch = Image.fromarray(paint_face(models[mi], i, f, w, h, *solids[mi]), "RGBA")
        if not cube.name.startswith("hem_"):           # cut-out planes keep a clear border
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas


def tinted(atlas, positions, role):
    """The atlas as one sister looks in the fight: every brew, foam and steam island multiplied by her role colour."""
    img = np.array(atlas).astype(int)
    tint = np.array(ROLE_TINT[role])
    for key, (x, y, w, h) in positions.items():
        if key[4] in TINTED:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] = img[y - 1:y + h + 1, x - 1:x + w + 1, :3] * tint // 255
    return Image.fromarray(img.astype(np.uint8), "RGBA")


VIEWS = s4.VIEWS + [
    {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.9), "scale": 8, "player": False,
     "res": (640, 480)},
    {"name": "vessel", "location": (3.6, -3.2, 4.2), "target": (0, -0.6, 2.1), "scale": 2.6, "player": False},
]
VESSEL_VIEW = {   # each sister's close-up of her vessel
    "cauldron": {"name": "vessel", "location": (3.6, -3.2, 4.2), "target": (0, -0.6, 2.1), "scale": 2.6, "player": False},
    "bottles": {"name": "vessel", "location": (-1.8, 4.2, 2.6), "target": (0.1, 0.4, 1.9), "scale": 2.0, "player": False},
    "pot": {"name": "vessel", "location": (1.6, 4.0, 3.3), "target": (0, 0.9, 1.3), "scale": 2.0, "player": False},
}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
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
                k[(i, f)] = island_key(c, f, w, h)
                sizes[k[(i, f)]] = (w, h)
        models.append(m)
        keys.append(k)
    positions, used, height = b4.pack(sizes)
    atlas = build_atlas(models, keys, positions)
    atlas_path = OUT / "occultech_coven.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    for (vessel, role, title), model, k in zip(s2.SISTERS, models, keys):
        out = OUT / vessel
        out.mkdir()
        preview = tinted(atlas, positions, role)
        preview_path = out / f"occultech_coven_{role}.png"
        preview.save(preview_path)
        # the review rig carries the tinted atlas so it looks right in game before session 6 wires the tint
        bb, _ = s4.rig_bbmodel(model, k, positions, preview_path, atlas.height, s3.pose_table(vessel, role))
        for element, cube in zip(bb["elements"], model.cubes):      # the hitbox element comes last
            element["light_emission"] = 15 if zone_for(cube) in TINTED else 0
        path = out / f"{model.name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c) in TINTED,
                  "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
        job_file = out / "render_job.json"
        job_file.write_text(json.dumps({"texture": str(preview_path), "out": (out / "renders").as_posix(),
                                        "boxes": boxes, "views": VIEWS[:-1] + [VESSEL_VIEW[vessel]],
                                        "player_at": (2.0, 1.6)}), encoding="utf-8")
        (out / "renders").mkdir()
        import subprocess
        result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                                 str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                                capture_output=True, text=True)
        if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
            raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
        job_file.unlink()
        names = [v["name"] for v in VIEWS]
        tw, th, pad, top, cols = 470, 352, 12, 56, 4
        rows = (len(names) + cols - 1) // cols
        img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Witch Coven - {title}, painted (session 5; brew shown in her role colour)",
                font=sheet._font(28), fill=sheet.INK)
        for n, name in enumerate(names):
            x, y = pad + (n % cols) * (tw + pad), top + (n // cols) * (th + 34 + pad)
            img.paste(sheet._tile(out / "renders" / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
        img.save(out / "sheet.png")
        print(vessel, "painted")
    print(json.dumps({"atlas": [s4.SIZE, atlas.height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
