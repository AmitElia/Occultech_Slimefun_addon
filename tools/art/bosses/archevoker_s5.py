"""The Archevoker redesign, session 5: texture painting (plan: docs/art/bosses/archevoker/overhaul/plan.md).

Paints session 4's layouts (the priest's 512 x 256 atlas, each casting hand's 64 x 128; the same islands):
- the robe: the evoker's black wool, folds running down each panel's length, its upper edges catching light, its
  lower ones in shade; the hood's long sides fold the same way;
- the gold trim: an embroidered braid, a repeat of bright stitches between a dark border at each edge;
- the stole: violet velvet, its edges lighter, a small gold sigil every few texels down its length;
- the illager's grey skin, mottled; the face: two creases across the forehead, shadow under the brow, the sunken
  sockets darkest at their inner corners, the cheeks hollow, the chin a step darker; the nose with a lit ridge and
  dark nostrils underneath;
- the gold: polished, a lit border round each plate and a darker field inside it; on every hand the fingers parted by
  dark gaps, knuckle creases across them, two creases on the palm; the chain's links alternating;
- the emeralds cut: a lit half and a dark half, a glint;
- the dark oak: grain along each board's length, carved panels sunk inside a lit bevel on the big faces;
- the velvet: tufted, buttoned in a diamond grid on the throne's back and seat;
- the eye in each palm: a white with shaded corners;
- the magic as gradients, never flat: the slit eyes, the irises and the runes brightest in their middle, the spell
  circles and the rune ring carrying a repeat of glyph marks.
Form only, no painted light direction: ambient occlusion is baked from the real geometry.

Run from the repository root: python tools/art/bosses/archevoker_s5.py
"""
import json
import math
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_s2 as s2, archevoker_s3 as s3, archevoker_s4 as s4  # noqa: E402
from bosses import brood_s4 as b4, brood_s5 as b5, coven_s5 as c5, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp

# every ramp runs from a cool dark through the zone's colour (session 4) to a warm light; (ramp, the zone's level)
RAMP = {
    "robe": mk((6, 5, 12), (46, 44, 52), (104, 98, 108), 9),
    "robe_dark": mk((3, 2, 6), (20, 18, 24), (54, 48, 58), 7),
    "hood_in": [(4, 3, 8), (12, 10, 16), (22, 18, 28)],
    "trim": mk((64, 40, 16), (192, 160, 74), (252, 232, 156), 7),
    "stole": mk((28, 8, 50), (104, 58, 150), (172, 132, 208), 9),
    "skin": mk((58, 60, 72), (150, 156, 156), (208, 212, 204), 9),
    "nose": mk((50, 52, 62), (116, 122, 122), (172, 176, 170), 7),
    "brow": [(10, 10, 14), (32, 32, 38), (58, 58, 66)],
    "shoe": mk((32, 20, 16), (96, 76, 60), (152, 126, 96), 7),
    "gold": mk((70, 44, 14), (220, 184, 86), (255, 242, 176), 9),
    "gold_dark": mk((38, 24, 8), (150, 112, 46), (212, 172, 92), 7),
    "emerald": mk((4, 40, 26), (28, 150, 84), (160, 244, 190), 7),
    "oak": mk((20, 13, 9), (82, 56, 34), (138, 102, 66), 9),
    "oak_dark": mk((10, 7, 5), (46, 31, 21), (88, 64, 42), 7),
    "velvet": mk((18, 3, 12), (58, 18, 34), (112, 46, 68), 7),
    "white": mk((150, 142, 134), (248, 246, 240), (255, 255, 252), 7),
    "cyan": [(18, 104, 160), (40, 160, 214), (80, 220, 250), (168, 244, 255), (236, 255, 255)],
    "purple": [(70, 24, 128), (128, 62, 210), (186, 104, 255), (222, 176, 255), (250, 236, 255)],
}
LEVEL = {"robe": 4, "robe_dark": 3, "hood_in": 1, "trim": 3, "stole": 4, "skin": 4, "nose": 3, "brow": 1, "shoe": 3,
         "gold": 4, "gold_dark": 3, "emerald": 3, "oak": 4, "oak_dark": 3, "velvet": 3, "white": 3, "cyan": 2,
         "purple": 2}
GLOWING = s4.GLOWING


def base(cube, w, h):
    return np.full((h, w), LEVEL[cube.mat], int), []


def clusters(seed, x, y, lo=170, hi=830, cell=2):
    r = noise(seed, x, y, cell)
    return -1 if r < lo else (1 if r > hi else 0)


def mottle(lv, seed, lo=170, hi=830, cell=2):
    h, w = lv.shape
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, lo, hi, cell)


def form(lv, face):
    """Form, not light: upper edges lit, lower edges in shade; tops a step lighter, undersides darker."""
    h, w = lv.shape
    if face == "up":
        lv += 1
    elif face == "down":
        lv -= 2
    elif h >= 3:
        lv[0, :] += 1
        lv[h - 1, :] -= 1


# ---- painters ---------------------------------------------------------------------------------------------------------

def paint_robe(cube, face, w, h, seed):
    """Black wool, folds down each panel's length: a dark crease with a lit ridge beside it, spaced unevenly."""
    lv, over = base(cube, w, h)
    mottle(lv, seed, 90, 930, 2)
    along_v = h >= w                                             # folds run along the face's longer side
    n = h if not along_v else w
    length = w if not along_v else h
    if n >= 6 and length >= 6 and face not in ("up", "down"):
        x = 2 + noise(seed, 0, 0, 1) % 3
        while x < n - 2:
            for t in range(length):
                wob = 1 if noise(seed, t, x, 6) > 640 else 0
                a = min(n - 1, x + wob)
                b = min(n - 1, a + 1)
                if along_v:
                    lv[t, a] -= 2
                    lv[t, b] += 1
                else:
                    lv[a, t] -= 2
                    lv[b, t] += 1
            x += 4 + noise(seed, x, 7, 1) % 4
    form(lv, face)
    return lv, over


def paint_trim(cube, face, w, h, seed):
    """An embroidered braid: dark borders at its two long edges, bright stitches repeating between them."""
    lv, over = base(cube, w, h)
    along_v = h > w
    n, length = (w, h) if along_v else (h, w)
    for t in range(length):
        for s in range(n):
            y, x = (t, s) if along_v else (s, t)
            if n >= 3 and s in (0, n - 1):
                lv[y, x] -= 1
            elif t % 3 == 0:
                lv[y, x] += 1
    return lv, over


def paint_stole(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    mottle(lv, seed, 200, 820, 1)
    if face == "north" and w >= 3:
        lv[:, 0] += 1
        lv[:, w - 1] += 1
        for y0 in range(3, h - 3, 7):                           # a small gold sigil: a diamond with a dot inside
            cx = (w - 1) // 2
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                over.append((y0 + dy, cx + dx, "trim", 4))
            over.append((y0, cx, "stole", 1))
    return lv, over


def paint_skin(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    mottle(lv, seed, 40, 975, 2)                                 # vanilla's skin: nearly even, a few soft flecks
    if cube.name == "head" and face in ("east", "west", "south") and h >= 10:
        lv[: h // 4, :] += 1                                     # the crown of the head a step lighter
        lv[-(h // 4):, :] -= 1
    if cube.name == "head" and face == "north":
        paint_face_front(lv, over)
    elif cube.name == "head" and face == "up":
        lv += 1
    elif cube.name == "head" and face == "down":
        lv -= 2
    return lv, over


def paint_face_front(lv, over):
    """The face (20 x 25 texels, row 0 at the top): forehead creases, shadow under the brow, the cheeks and the chin."""
    h, w = lv.shape
    for x in range(5, 15):                                       # two creases across the forehead
        if x not in (9, 10):
            lv[4, x] -= 1
        if 6 <= x <= 13:
            lv[6, x] -= 1
    lv[9:11, 3:17] -= 1                                          # the brow's shadow, under the scowl
    for y in range(13, 16):                                      # under the sockets: tired, sunken
        for x in (4, 5, 6, 13, 14, 15):
            lv[y, x] -= 1
    for y in range(15, 22):                                      # the hollow cheeks, deepening downwards
        lv[y, 2:4] -= 1 + (y > 18)
        lv[y, 16:18] -= 1 + (y > 18)
    lv[h - 3:, :] -= 1                                           # the chin and jaw a step darker
    lv[13, 9:11] += 1                                            # the bridge of the nose catching light


def paint_nose(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    mottle(lv, seed, 40, 975, 2)
    if face == "north":
        mid = (w - 1) / 2
        for x in range(w):
            lv[:, x] += 1 if abs(x - mid) < 1 else (-1 if abs(x - mid) > 1.8 else 0)   # a lit ridge
        lv[h - 2:, :] += 1                                       # the tip
    elif face == "down":
        lv -= 1
        for x in (1, w - 2):                                     # nostrils
            if 0 <= x < w:
                over.append((h // 2, x, "brow", 0))
    elif cube.name.startswith("socket"):
        lv[:, :] -= 1
    else:
        form(lv, face)
    if cube.name.startswith(("socket", "cheek")):
        lv[:, :] -= 1
    return lv, over


def paint_flat(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    if face not in ("up", "down") and h >= 2:
        lv[0, :] += 1
    return lv, over


def paint_gold(cube, face, w, h, seed):
    """Polished gold: a lit border round each plate, a smooth field, a soft glint on big faces; hands get their
    fingers, knuckles and palm creases."""
    lv, over = base(cube, w, h)
    mottle(lv, seed, 60, 960, 3)
    n = cube.name
    if w >= 4 and h >= 4:
        lv[0, :] += 1
        lv[:, 0] += 1
        lv[h - 1, :] -= 1
        lv[:, w - 1] -= 1
    if w >= 6 and h >= 6 and face not in ("down",):
        for k in range(min(w, h) // 3):                          # a short diagonal glint near the top corner
            y, x = 1 + k, 2 + k
            if y < h and x < w:
                lv[y, x] += 2
    is_finger = "_f" in n and n.rsplit("_f", 1)[-1][:1].isdigit() or n.startswith(("finger_", "thumb"))
    if is_finger and face in ("north", "south", "east", "west"):
        if w >= 3:
            lv[:, 0] -= 2                                        # the gaps between the fingers
            lv[:, w - 1] -= 2
        for frac in (0.4, 0.7):                                  # knuckle creases
            y = int(h * frac)
            if 1 <= y < h - 1:
                lv[y, 1:w - 1] -= 1
        lv[0:2, :] += 1                                          # the fingertip
    if n.endswith("_palm") and face == "north" and w >= 8:
        for x in range(2, w - 2):                                # two creases across the palm, curving
            y1 = int(h * 0.25 + abs(x - w / 2) * 0.25)
            y2 = int(h * 0.7 - abs(x - w / 2) * 0.2)
            for y in (y1, y2):
                if 0 <= y < h:
                    lv[y, x] -= 1
    if n.endswith("_palm") and face == "south" and w >= 8:
        for x in range(1, w - 1, 4):                             # knuckles on the back of the hand
            lv[0:2, x:x + 2] += 1
    form(lv, face) if face in ("up", "down") else None
    return lv, over


def paint_chain(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    along_v = h > w
    length = h if along_v else w
    for t in range(length):
        k = 1 if (t // 2) % 2 == 0 else -1                       # the links: bright, dark, bright
        if along_v:
            lv[t, :] += k
        else:
            lv[:, t] += k
    return lv, over


def paint_emerald(cube, face, w, h, seed):
    """A cut gem: a lit half and a dark half across its diagonal, a dark edge, a glint."""
    lv, over = base(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if x + y < (w + h) / 2 - 1 else -1
    if w >= 3 and h >= 3:
        lv[0, :] -= 1
        lv[h - 1, :] -= 1
        lv[1, 1] += 3
    return lv, over


def paint_oak(cube, face, w, h, seed):
    """Dark oak: grain along the board's length; on big faces a carved panel sunk inside a lit bevel."""
    lv, over = base(cube, w, h)
    along_v = h > w
    for y in range(h):
        for x in range(w):
            a, b = (y, x) if along_v else (x, y)
            r = noise(seed, b, a, 1) if noise(seed, b, a // 5, 1) > 500 else noise(seed, b, a // 7, 1)
            lv[y, x] += -1 if r < 180 else (1 if r > 880 else 0)
    if w >= 14 and h >= 14 and face in ("north", "south", "east", "west"):
        for y in range(3, h - 3):                                # the carved panel: a lit bevel, a dark groove
            for x in range(3, w - 3):
                edge = min(x - 3, w - 4 - x, y - 3, h - 4 - y)
                if edge == 0:
                    lv[y, x] += 1
                elif edge == 1:
                    lv[y, x] -= 2
                else:
                    lv[y, x] -= 1 if (x + y) % 9 == 0 else 0
    form(lv, face)
    return lv, over


def paint_velvet(cube, face, w, h, seed):
    """Tufted velvet: buttons on a diamond grid, the cloth pulled into creases between them."""
    lv, over = base(cube, w, h)
    mottle(lv, seed, 80, 940, 2)
    if w >= 8 and h >= 8 and face in ("north", "south", "up"):
        step = 6
        for y in range(h):
            for x in range(w):
                u, v = (x + y) % step, (x - y) % step
                if u == 0 or v == 0:
                    lv[y, x] -= 1                                # the creases
                if u == 0 and v == 0:
                    over.append((y, x, "gold_dark", 3))          # a button
                elif (u in (2, 3)) and (v in (2, 3)):
                    lv[y, x] += 1                                # the puffed cushion between
    return lv, over


def paint_white(cube, face, w, h, seed):
    lv, over = base(cube, w, h)
    if w >= 3:
        lv[:, 0] -= 2
        lv[:, w - 1] -= 2
    if h >= 3:
        lv[h - 1, :] -= 1
    return lv, over


def paint_glow(cube, face, w, h, seed):
    """Magic as a gradient: brightest along the middle, dimmer to the edges; long bars carry glyph marks."""
    lv = np.zeros((h, w), int)
    for y in range(h):
        for x in range(w):
            dy = abs(y - (h - 1) / 2) / max(1, h / 2)
            dx = abs(x - (w - 1) / 2) / max(1, w / 2)
            d = max(dx, dy) if min(w, h) > 2 else (dy if w > h else dx)
            lv[y, x] = (4 if d < 0.3 else (3 if d < 0.65 else 2)) if min(w, h) >= 3 else (3 if d < 0.5 else 2)
    n = cube.name
    if ("circle" in n or "rune" in n) and max(w, h) >= 6:
        length = max(w, h)
        for t in range(length):
            if t % 5 == 2:                                       # glyph marks along the bar
                if w >= h:
                    lv[:, t] = 1
                else:
                    lv[t, :] = 1
    return lv, []


def painter_for(cube):
    n = cube.name
    if n.startswith("chain_"):
        return paint_chain
    return {"robe": paint_robe, "robe_dark": paint_robe, "hood_in": paint_flat, "trim": paint_trim,
            "stole": paint_stole, "skin": paint_skin, "nose": paint_nose, "brow": paint_flat, "shoe": paint_flat,
            "gold": paint_gold, "gold_dark": paint_gold, "emerald": paint_emerald, "oak": paint_oak,
            "oak_dark": paint_oak, "velvet": paint_velvet, "white": paint_white, "cyan": paint_glow,
            "purple": paint_glow}[cube.mat]


def paint_face(model, i, face, w, h, solids):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    lv, over = painter_for(cube)(cube, face, w, h, seed)
    if cube.mat not in GLOWING:
        ao = b5.occlusion(model, i, face, w, h, solids)
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    out = c5.from_levels(lv, RAMP[cube.mat], None)
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w:
            r = RAMP[rname]
            out[y, x, :3] = r[max(0, min(len(r) - 1, shade))]
    return out


def painted(model, size):
    keys = s4.island_keys(model)
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    b4.SIZE = size
    positions, used, _ = b4.pack(sizes)
    height = 16
    while height < used:
        height *= 2
    owner = {}
    for (i, f), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, f))
    solids = b5.solids_of(model)
    atlas = Image.new("RGBA", (size, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, f = owner[key]
        patch = Image.fromarray(paint_face(model, i, f, w, h, solids), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return keys, positions, height, atlas


CLOSE = [
    {"name": "face_close", "location": (1.4, 10, 6.3), "target": (0, 0.2, 5.9), "scale": 2.6, "player": False},
    {"name": "robe_close", "location": (3, 8, 4.2), "target": (0, 0.4, 3.8), "scale": 4.5, "player": False},
    {"name": "throne_back", "location": (5, -12, 6), "target": (0, -1.5, 4.8), "scale": 6.5, "player": False},
    {"name": "ring_close", "location": (6, 9, 7.5), "target": (1.8, -1.6, 6.2), "scale": 3.2, "player": False},
]


def model_pass(model, name, size, hitbox, poses, out, views):
    model.name = name
    keys, positions, height, atlas = painted(model, size)
    atlas_path = out / f"{name}.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(out / f"{name}_preview.png")
    bb, _ = s4.textured_bbmodel(model, keys, positions, atlas_path, size, height, hitbox, poses)
    path = out / f"{name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    return bb, atlas_path


def grid(paths, labels, out, heading, cols=3, tw=470, th=352):
    pad, top = 12, 56
    rows = (len(paths) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading, font=sheet._font(28), fill=sheet.INK)
    for n_, (p, label) in enumerate(zip(paths, labels)):
        x, y = pad + (n_ % cols) * (tw + pad), top + (n_ // cols) * (th + 34 + pad)
        img.paste(sheet._tile(p, tw, th), (x, y))
        dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    model = s3.build("rest")
    bb, atlas_path = model_pass(model, s3.MODEL_ID, s4.SIZE, s2.hitbox_bounds(model), s3.pose_table().items(), OUT,
                                s4.VIEWS)
    s4.render(model, bb, atlas_path, OUT / "renders", s4.VIEWS + CLOSE)
    names = ["hero", "front", "back", "player_eye", "face_close", "robe_close", "throne_back", "ring_close", "side"]
    grid([OUT / "renders" / f"{n}.png" for n in names], [n.replace("_", " ") for n in names], OUT / "sheet.png",
         "The Archevoker - painted (session 5)")
    hand_paths = []
    for glow in ("cyan", "purple"):
        hm = s2.hand_model(glow)
        s3.fold_quarter_turns(hm)
        hbb, hpath = model_pass(hm, f"occultech_archevoker_hand_{glow}_rig", s4.HAND_SIZE, s2.HAND_HITBOX, (), OUT,
                                s4.HAND_VIEWS)
        s4.render(hm, hbb, hpath, OUT / f"hand_{glow}", s4.HAND_VIEWS)
        hand_paths += [OUT / f"hand_{glow}" / f"{v['name']}.png" for v in s4.HAND_VIEWS]
    grid(hand_paths, [f"{g}: {v['name'].replace('_', ' ')}" for g in ("cyan", "purple") for v in s4.HAND_VIEWS],
         OUT / "hands.png", "The casting hands - painted (session 5)", tw=400, th=330)
    print("painted")


if __name__ == "__main__":
    main()
