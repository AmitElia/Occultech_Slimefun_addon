"""The Blaze Choir redesign, session 1 step 2: the heads. Three headpieces and faces for each singer, on its own body.

The head is vanilla's blaze head, its real pixels (from the 26.2 client) on the cube at a whole scale. The eyes stay.

  Soprano  S1 Pipe Fan      organ pipes in an arc behind the head               vanilla face
           S2 Pipe Mitre    a band on the head, a pointed rank of pipes on it    a singing mouth
           S3 Chime Fringe  a hanging fringe of small tubes round a circlet      a thin humming slit
  Alto     A1 Nimbus        a plain dished disc behind the head                  vanilla face
           A2 Tambourine    an open ring with pairs of jingles set in it         a singing mouth
           A3 Finger Cymbals  a cantor's cap, a small cymbal at each temple      a thin humming slit
  Bass     B1 Points        a band and a row of triangles                        vanilla face
           B2 Arched Crown  arches meeting over the head, a small bell on top    a singing mouth
           B3 Belfry        a little bell tower round the top of the head        a thin humming slit

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/choir_heads.py <folder>
"""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import choir_silhouettes as cs, volley_crone_s2 as v2  # noqa: E402
from bosses.archevoker_silhouettes import ring_panels, vocto  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s1_heads"
SKIN = Image.open(Path(sys.argv[-1]) / "assets/minecraft/textures/entity/blaze/blaze.png").convert("RGB") if len(sys.argv) > 1 else None
ORIGINAL_DISH = cs.dish
HOT = (255, 196, 70)
MOUTH = {
    "vanilla": {},
    "sing": {(c, r): HOT for c in (3, 4) for r in (5, 6)},
    "hum": {(c, 6): HOT for c in (2, 3, 4, 5)},
}


def pixel_mat(rgb):
    name = "px_%02x%02x%02x" % tuple(rgb)
    v2.PALETTE.setdefault(name, tuple(rgb))
    return name


def face_of(u, v, face, mouth):
    for r in range(8):
        for c in range(8):
            rgb = (mouth or {}).get((c, r), SKIN.getpixel((u + c, v + r)))
            yield c, r, pixel_mat(rgb)


def textured_head(mouth):
    def head(g, x, y, k):
        g.box("head", (x, y + 4 * k, 0), (8 * k - 0.1, 8 * k - 0.1, 8 * k - 0.1), "blaze_dark")
        half, t = 4 * k, 0.15
        for c, r, m in face_of(8, 8, "front", MOUTH[mouth]):              # the viewer's left is the model's +x
            g.box(f"f{c}{r}", (x + half - (c + 0.5) * k, y + 8 * k - (r + 0.5) * k, -half), (k, k, t), m)
        for c, r, m in face_of(0, 8, "side", None):
            g.box(f"r{c}{r}", (x + half, y + 8 * k - (r + 0.5) * k, half - (c + 0.5) * k), (t, k, k), m)
        for c, r, m in face_of(16, 8, "side", None):
            g.box(f"l{c}{r}", (x - half, y + 8 * k - (r + 0.5) * k, -half + (c + 0.5) * k), (t, k, k), m)
        for c, r, m in face_of(8, 0, "top", None):
            g.box(f"t{c}{r}", (x + half - (c + 0.5) * k, y + 8 * k, half - (r + 0.5) * k), (k, t, k), m)
    return head


# ---- the Soprano's: y is 4 units over the head's underside, the head is 16 across ----------------------------------

def pipe_fan(g, x, y):
    for i in range(-5, 6):
        h = 12 + 22 * math.cos(i / 6 * math.pi / 2)
        px = x + i * 3.1
        g.box(f"fan_{i + 5}", (px, y + h / 2, 10), (3, h, 3), "brass")
        g.box(f"fan_mouth_{i + 5}", (px, y + h * 0.82, 8.4), (1.8, 1.6, 0.3), "inside")
    g.box("fan_rail", (x, y + 2, 10), (36, 2, 4.2), "brass_dark")


def pipe_mitre(g, x, y):
    top = y + 12
    vocto(g, "mitre_band", (x, top + 1.2, 0), 18, 3, 18, "brass_dark", cham=0.12)
    for row, z in enumerate((3.6, -0.0)):
        for i in range(-3, 4):
            h = (26 if row else 20) - abs(i) * 6
            px = x + i * 3.5 + (1.75 if row and i < 3 else 0) * 0
            g.box(f"mitre_{row}{i + 3}", (px, top + 3 + h / 2, z), (3.2, h, 3.2), "brass")
            g.box(f"mitre_lip_{row}{i + 3}", (px, top + 3 + h - 1, z), (3.8, 0.9, 3.8), "brass_dark")
            g.box(f"mitre_mouth_{row}{i + 3}", (px, top + 5, z - 1.7), (1.8, 2, 0.3), "inside")


def chime_fringe(g, x, y):
    top = y + 12
    vocto(g, "fringe_plate", (x, top + 1, 0), 24, 2, 24, "brass", cham=0.29)
    vocto(g, "fringe_cap", (x, top + 3, 0), 12, 2, 12, "brass_dark", cham=0.29)
    g.box("fringe_spire", (x, top + 13, 0), (3, 18, 3), "brass")
    g.box("fringe_spire_lip", (x, top + 21.5, 0), (3.8, 1, 3.8), "brass_dark")
    g.box("fringe_spire_tip", (x, top + 24, 0), (3, 3, 3), "white_fire", rotation=(0, 45, 45))
    for i in range(16):
        a = 360 * (i + 0.5) / 16
        if abs((a + 180) % 360 - 180) > 140 and False:
            continue
        ar = math.radians(a)
        px, pz = x + 11.3 * math.sin(ar), 11.3 * math.cos(ar)
        front = pz < -6 and abs(px - x) < 8
        length = 4 if front else 7 + (i % 3) * 3.5
        g.box(f"fringe_{i}", (px, top - length / 2, pz), (1.5, length, 1.5), "brass")


# ---- the Alto's: c is behind the middle of the head, which is 24 across --------------------------------------------

def nimbus(g, c):
    ORIGINAL_DISH(g, "nimbus", c, (0, 0, 1), 18, "brass", across=(1, 0, 0))


def tambourine(g, c):
    x, y, z = c
    z = z - 2
    r = 19
    for i in range(16):
        a = 360 * i / 16
        ar = math.radians(a)
        g.box(f"tam_{i}", (x + r * math.sin(ar), y + r * math.cos(ar), z), (r * 0.42, 4, 3), "brass", rotation=(0, 0, -a))
    for i in range(8):                                                 # a slot through the ring, a pair of jingles in it
        a = 360 * (i + 0.5) / 8
        ar = math.radians(a)
        px, py = x + r * math.sin(ar), y + r * math.cos(ar)
        n = g.group(f"jingle{i}", (px, py, z), (0, 0, -a))
        n.box(f"slot{i}", (px, py, z), (5, 4.2, 1.2), "inside")
        for s in (-1, 1):
            n.box(f"zil{i}{s}a", (px, py, z + s * 2.4), (5, 5, 0.8), "brass_dark")
            n.box(f"zil{i}{s}b", (px, py, z + s * 2.4), (5, 5, 0.8), "brass_dark", rotation=(0, 0, 45))


def finger_cymbals(g, c):
    x, y, z = c
    top = y + 12
    ring_panels(g, "cap", top + 6, top + 0.5, 6, 12.9, "cord", n=8, t=1.6, start=22.5, cx=x)
    vocto(g, "cap_band", (x, top + 0.5, 0), 26, 2.2, 26, "brass", cham=0.12)
    g.box("cap_knob", (x, top + 7.5, 0), (3.4, 3.4, 3.4), "brass_dark", rotation=(0, 45, 45))
    for sx in (-1, 1):
        ORIGINAL_DISH(g, f"finger_{sx}", (x + sx * 17, y + 2, 0), (sx, 0, 0), 10, "brass", boss="brass_dark")
        g.box(f"finger_cord_{sx}", (x + sx * 14, y + 2, 0), (5, 1, 1), "cord")


# ---- the Bass's: y is the top of the head, k is 3 ----------------------------------------------------------------------

def points(g, x, y, k):
    cs_original_crown(g, x, y, k)


def arched_crown(g, x, y, k):
    w = 8 * k + 1.5
    vocto(g, "crown_band", (x, y, 0), w, 5, w, "brass", cham=0.1)
    top = y + 15
    for a in (45, 135, 225, 315):
        ar = math.radians(a)
        cr, sr = math.sin(ar), math.cos(ar)
        out = (x + cr * 16.5, y + 2, sr * 16.5)
        knee = (x + cr * 18, y + 9, sr * 18)
        peak = (x + cr * 10, y + 14.5, sr * 10)
        close = (x, top, 0)
        cs.beam(g, f"arch_a{a}", out, knee, 3, "brass")
        cs.beam(g, f"arch_b{a}", knee, peak, 3, "brass")
        cs.beam(g, f"arch_c{a}", peak, close, 3, "brass")
    g.box("crown_cap", (x, top + 0.5, 0), (7, 2, 7), "brass_dark", rotation=(0, 45, 0))
    for i, (y1, r1, y2, r2) in enumerate(((top + 8.5, 1.8, top + 5.5, 2.6), (top + 5.5, 2.6, top + 2, 4.8))):
        ring_panels(g, f"crown_bell{i}", y1, y2, r1, r2, "brass", n=8, t=1, cx=x)
    g.box("crown_bell_top", (x, top + 9, 0), (3.4, 1.2, 3.4), "brass_dark")


def belfry(g, x, y, k):
    w = 8 * k + 2
    vocto(g, "bel_floor", (x, y + 0.5, 0), w, 3, w, "brass_dark", cham=0.1)
    roof = y + 15
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box(f"bel_post{sx}{sz}", (x + sx * 11, y + 8, sz * 11), (3.2, 13, 3.2), "brass")
        g.box(f"bel_beam_x{sx}", (x, roof - 1, sx * 11), (25, 2.4, 3.4), "brass_dark")
        g.box(f"bel_beam_z{sx}", (x + sx * 11, roof - 1, 0), (3.4, 2.4, 25), "brass_dark")
    ring_panels(g, "bel_roof", roof + 10, roof, 1.2, 18, "copper", n=4, t=1.4, start=0, fill=1.05, cx=x)
    g.box("bel_finial", (x, roof + 12, 0), (3.4, 3.4, 3.4), "brass_dark", rotation=(0, 45, 45))
    g.box("bel_rope", (x, roof - 2, 0), (1, 3, 1), "cord")
    for i, (y1, r1, y2, r2) in enumerate(((roof - 3, 2.4, roof - 7, 3.4), (roof - 7, 3.4, roof - 11, 6.5))):
        ring_panels(g, f"bel_bell{i}", y1, y2, r1, r2, "brass", n=8, t=1, cx=x)


cs_original_crown = cs.spiked_crown
OPTIONS = {
    "S1": ("soprano", "Pipe Fan", "vanilla", pipe_fan), "S2": ("soprano", "Pipe Mitre", "sing", pipe_mitre),
    "S3": ("soprano", "Chime Fringe", "hum", chime_fringe),
    "A1": ("alto", "Nimbus", "vanilla", nimbus), "A2": ("alto", "Tambourine", "sing", tambourine),
    "A3": ("alto", "Finger Cymbals", "hum", finger_cymbals),
    "B1": ("bass", "Points", "vanilla", points), "B2": ("bass", "Arched Crown", "sing", arched_crown),
    "B3": ("bass", "Belfry", "hum", belfry),
}
TARGET = {"soprano": 5.5, "alto": 4.4, "bass": 4.6}


def build(key):
    singer, title, mouth, piece = OPTIONS[key]
    cs.head = textured_head(mouth)
    m = Model(f"head_{key}")
    root = m.group("root", (0, 0, 0))
    if singer == "soprano":
        cs.fan_crown = piece
        cs.soprano(root, 0, "idle")
    elif singer == "alto":
        def dish(g, name, c, apex, r, mat, across=(0, 1, 0), boss=None):
            if name == "nimbus":
                piece(g, c)
                return None
            return ORIGINAL_DISH(g, name, c, apex, r, mat, across, boss)
        cs.dish = dish
        cs.alto(root, 0, "idle")
        cs.dish = ORIGINAL_DISH
    else:
        cs.spiked_crown = piece
        cs.bell(root.group("bass", (0, 0, 0)), 0, "idle")
    return m, singer, title


def views(singer):
    t = TARGET[singer]
    return [
        {"name": "hero", "mode": "flat", "camera": "persp", "yaw": -30, "height": t + 0.4, "dist": 3.7, "target_z": t, "player": False},
        {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": t, "dist": 3.7, "target_z": t, "player": False},
        {"name": "low", "mode": "clay", "camera": "persp", "yaw": 26, "height": 1.62, "dist": 5.5, "target_z": t, "player": False},
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(cs.PALETTE)
    keys = list(OPTIONS)
    for key in keys:
        m, singer, title = build(key)
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, views(singer))
        print(key, title, "cubes", len(m.cubes))
    tw, th, pad, top = 260, 300, 8, 56
    img = Image.new("RGB", (pad + 9 * (tw + pad) + 3 * pad, top + 3 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Blaze Choir: the heads", font=sheet._font(26), fill=sheet.INK)
    for r in range(3):
        for c in range(3):
            key = keys[r * 3 + c]
            for i, view in enumerate(("hero", "front", "low")):
                x, y = pad + (c * 3 + i) * (tw + pad) + c * 2 * pad, top + r * (th + 30 + pad)
                img.paste(sheet._tile(OUT / key / f"{view}.png", tw, th), (x, y))
                if i == 0:
                    dr.text((x, y + th + 5), f"{key}: {OPTIONS[key][1]}", font=sheet._font(17), fill=sheet.INK)
    img.save(OUT / "heads.png")


if __name__ == "__main__":
    main()
