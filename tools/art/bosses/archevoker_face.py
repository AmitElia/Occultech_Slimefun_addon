"""The Archevoker redesign, session 1 step 2: the face, the vestments and the hands, three takes.

B take 2 was approved (2026-10-15): the dark priest on the floating rose-window throne, his arms on the armrests,
the ring of free gilded hands behind. This study dresses him three ways, each with its own casting hands. They sit on
the same seated body and throne (archevoker_silhouettes.py), so each is judged in its real frame. The head stays
vanilla's illager head at 2.5x in all three; what changes is what frames it, the eyes and the brow.
  F1  the Watcher    a deep hood and a shoulder cape; eyes glowing spirit cyan; hands with an open eye in the palm
  F2  the Bishop     a two-peaked mitre with lappets, a short buttoned cape; vanilla green eyes under a scowl; plate
                     gauntlets with knuckle plates and a flared cuff
  F3  the Cardinal   a skullcap and a heavy gold chain of office with an emerald medallion; sunken, glowing slit eyes;
                     jewelled hands with rings, a bracelet and dark nails
Parts can be mixed. Model units: 16 = one block, y up, his face towards -z.

Run from the repository root: python tools/art/bosses/archevoker_face.py
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
from bosses import archevoker_silhouettes as s1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s1_face"
PALETTE = dict(s1.PALETTE, white=(232, 226, 210), nail=(60, 36, 72), hood_in=(20, 18, 24))
K = s1.HEAD_K
X, Y, Z = s1.HIP
HB = Y + 37                  # the chin's underside
HZ = Z                       # the head's centre (z)
FACE = HZ - 4 * K            # the face's plane
TOP = HB + 10 * K            # the head's top


def panels(g, name, cz, top_y, bot_y, top_r, bot_r, mat, n=8, t=2.0, fill=1.12, start=22.5, skip=()):
    """ring_panels round a centre at z = cz (a cape round his neck)."""
    h = top_y - bot_y
    tilt = math.degrees(math.atan2(bot_r - top_r, h))
    slant = math.hypot(h, bot_r - top_r)
    rm = (top_r + bot_r) / 2
    width = 2 * rm * math.tan(math.pi / n) * fill
    for i in range(n):
        if i in skip:
            continue
        a = start + 360 * i / n
        ar = math.radians(a)
        g.box(f"{name}_{i}", (rm * math.sin(ar), (top_y + bot_y) / 2, cz + rm * math.cos(ar)), (width, slant, t), mat,
              rotation=(-tilt, a, 0))


# ---- the faces (the illager head itself is vanilla's; these add its eyes and brow) --------------------------------

def head_base(g):
    g.box("head", (0, HB + 5 * K, HZ), (8 * K, 10 * K, 8 * K), "skin")
    g.box("nose", (0, HB + 2 * K, FACE - K), (2 * K, 4 * K, 2 * K), "nose")


def eyes(g, mat, w=K, h=K):
    for sx in (-1, 1):
        g.box(f"eye_{sx}", (sx * 1.5 * K, HB + 5.5 * K, FACE - 0.3), (w, h, 0.6), mat)


def brow_straight(g, thick=1.0):
    g.box("brow", (0, HB + 6.5 * K + (thick - 1) * K / 2, FACE - 0.3), (6 * K, thick * K, 0.6), "brow")


def brow_scowl(g, angle=13):
    """The unibrow broken into a V: the inner ends low, over the nose."""
    for sx in (-1, 1):
        g.box(f"brow_{sx}", (sx * 1.6 * K, HB + 6.6 * K, FACE - 0.35), (3.4 * K, 1.1 * K, 0.7), "brow",
              rotation=(0, 0, sx * angle))


def face_watcher(g):
    head_base(g)
    brow_straight(g)
    eyes(g, "cyan")


def face_bishop(g):
    head_base(g)
    brow_scowl(g)
    eyes(g, "eye")


def face_cardinal(g):
    head_base(g)
    for sx in (-1, 1):                                       # sunken sockets, slit eyes, hollow cheeks
        g.box(f"socket_{sx}", (sx * 1.5 * K, HB + 5.3 * K, FACE - 0.15), (1.7 * K, 1.3 * K, 0.4), "nose")
        g.box(f"cheek_{sx}", (sx * 2.9 * K, HB + 3.0 * K, FACE - 0.15), (0.45 * K, 2.6 * K, 0.4), "nose")
    brow_scowl(g, angle=8)
    eyes(g, "cyan", w=K * 1.1, h=K * 0.45)


# ---- the vestments ---------------------------------------------------------------------------------------------------

def hood(head, torso, cape=True):
    """A deep hood standing proud of the face: its opening a pointed arch, its sides flaring to the shoulders, its
    point folded back; over a shoulder cape."""
    w, d = 8 * K + 5, 8 * K + 6
    peak = TOP + 8
    for sx in (-1, 1):
        # the crown of the hood: two slabs leaning together into a peak, and the rim along their front edge
        head.box(f"hood_crown_{sx}", (sx * 6.2, TOP + 3.6, HZ + 1), (15, 3, d), "robe", rotation=(0, 0, -sx * 30))
        head.box(f"hood_rim_crown_{sx}", (sx * 6.2, TOP + 3.6, FACE - 2.4), (15, 2.4, 2), "trim",
                 rotation=(0, 0, -sx * 30))
        head.box(f"hood_side_{sx}", (sx * (w / 2 - 0.5), HB + 5 * K, HZ + 1), (3, 10 * K + 4, d), "robe",
                 rotation=(0, 0, sx * 6))
        head.box(f"hood_rim_{sx}", (sx * (w / 2 - 1.2), HB + 5 * K, FACE - 2.4), (2.2, 10 * K + 4, 2), "trim",
                 rotation=(0, 0, sx * 6))
    head.box("hood_fill", (0, TOP + 1.5, HZ + 1), (w - 6, 3, d), "robe")
    head.box("hood_back", (0, HB + 6 * K, HZ + d / 2 - 0.5), (w + 2, 10 * K + 8, 3), "robe")
    head.box("hood_shadow", (0, TOP - 1, FACE - 0.2), (8 * K, 2.4, 1.6), "hood_in")
    head.box("hood_point", (0, peak - 2, HZ + d / 2 + 1), (8, 8, 12), "robe", rotation=(-40, 0, 45))
    if cape:
        panels(torso, "cape", Z + 1, Y + 38, Y + 22, 13, 22, "robe")
        panels(torso, "cape_hem", Z + 1, Y + 23, Y + 21, 21.6, 22.6, "trim", t=1.2)
        torso.box("cape_clasp", (0, Y + 34, Z - 12), (5, 5, 1.6), "emerald", rotation=(0, 0, 45))


def mitre(head, torso):
    """A two-peaked mitre (front and back panels, each ending in a point), a gold orphrey, lappets; a short cape."""
    base = TOP - 1
    for sz, name in ((-1, "front"), (1, "back")):
        z = HZ + sz * 3.5
        head.box(f"mitre_{name}", (0, base + 11, z), (17, 22, 2), "robe", rotation=(-sz * 7, 0, 0), origin=(0, base, z))
        head.box(f"mitre_{name}_point", (0, base + 22, z + sz * 1.3), (12, 12, 2), "robe", rotation=(-sz * 7, 0, 45),
                 origin=(0, base + 22, z))
    for sx in (-1, 1):
        head.box(f"mitre_side_{sx}", (sx * 7.6, base + 9, HZ), (1.8, 18, 7), "robe_dark")
    head.box("mitre_band", (0, base + 1.5, HZ), (19, 3, 9.6), "trim")
    head.box("mitre_orphrey", (0, base + 12, HZ - 4.9), (3.2, 20, 0.6), "trim", rotation=(7, 0, 0), origin=(0, base, HZ - 4.9))
    head.box("mitre_gem", (0, base + 9, HZ - 6.6), (4, 4, 1), "emerald", rotation=(0, 0, 45))
    for sx in (-1, 1):
        head.box(f"lappet_{sx}", (sx * 5, HB + 2, HZ + 10.6), (3.4, 26, 1), "robe_dark")
        head.box(f"lappet_tip_{sx}", (sx * 5, HB - 11.5, HZ + 10.6), (3.8, 2.5, 1.2), "trim")
    panels(torso, "cape", Z + 1, Y + 38, Y + 26, 12, 20, "robe_dark")
    for i in range(3):
        torso.box(f"cape_button_{i}", (0, Y + 35 - i * 3.6, Z - 11.6 + i * 1.4), (2, 2, 1.2), "trim")


def cardinal(head, torso):
    """A skullcap, and a heavy gold chain of office lying on the shoulders with an emerald medallion."""
    head.box("skullcap", (0, TOP + 0.8, HZ + 1.5), (15, 2, 15), "stole")
    head.box("skullcap_top", (0, TOP + 2.2, HZ + 1.5), (8, 1.2, 8), "stole")
    chain_of_office(torso)


def chain_of_office(torso):
    panels(torso, "chain", Z + 1, Y + 37.5, Y + 35, 11.5, 17.5, "gold", n=14, t=1.2, fill=0.5, start=12.86)
    for sx in (-1, 1):
        s1.beam(torso, f"chain_drop_{sx}", (sx * 6, Y + 33.5, Z - 7.5), (sx * 2, Y + 26, Z - 9.4), 1.6, "gold")
    torso.box("medallion", (0, Y + 23, Z - 9.6), (9, 9, 1.6), "gold", rotation=(0, 0, 45))
    torso.box("medallion_gem", (0, Y + 23, Z - 10.6), (5, 5, 1), "emerald", rotation=(0, 0, 45))


# ---- the casting hands -----------------------------------------------------------------------------------------------

def hand_core(h, name, x, y, z, glow, segmented=False, nails=False, mirror=False):
    """Palm, four fingers held together, the thumb out, the cuff; returns nothing. Palm out towards -z."""
    h.box(name + "_palm", (x, y, z), (16, 17, 5), "gold")
    for i, dx in enumerate((-5.85, -1.95, 1.95, 5.85)):
        length = (11, 14, 13, 10)[i]
        if segmented:
            lo = length * 0.55
            h.box(f"{name}_f{i}a", (x + dx, y + 8.5 + lo / 2, z), (3.7, lo, 4.2), "gold")
            h.box(f"{name}_f{i}j", (x + dx, y + 8.5 + lo + 0.5, z + 0.3), (3.9, 1.2, 4.4), "gold_dark")
            h.box(f"{name}_f{i}b", (x + dx, y + 8.5 + lo + 1 + (length - lo - 1) / 2, z), (3.4, length - lo - 1, 4.0),
                  "gold")
        else:
            h.box(f"{name}_f{i}", (x + dx, y + 8.5 + length / 2, z), (3.7, length, 4.2), "gold")
        if nails:
            h.box(f"{name}_nail{i}", (x + dx, y + 8.5 + length - 1.2, z + 2.3), (2.6, 2.6, 0.6), "nail")
    m = -1 if mirror else 1                                  # a right hand's thumb is on -x, a left hand's on +x
    h.box(name + "_thumb", (x - m * 10, y + 1, z - 0.5), (4, 11, 4.2), "gold", rotation=(0, 0, m * 34),
          origin=(x - m * 7.5, y - 4, z))
    for i in range(8):                                       # the spell circle behind
        a = math.radians(i * 45 + 22.5)
        r = 19
        h.box(f"{name}_circle{i}", (x + r * math.sin(a), y + 3 + r * math.cos(a), z + 4), (r * 0.83, 1.6, 0.8), glow,
              rotation=(0, 0, -(i * 45 + 22.5)))


def hand_eye(g, name, centre, rot, glow, mirror=False):
    """The Watcher's hand: smooth gold, an open eye in the palm, its iris in the hand's glow."""
    x, y, z = centre
    h = g.group(name, centre, rot)
    hand_core(h, name, x, y, z, glow, mirror=mirror)
    h.box(name + "_cuff", (x, y - 11.5, z + 0.5), (13, 6, 7), "gold_dark")
    h.box(name + "_eye_white", (x, y + 1, z - 2.7), (11, 5, 0.6), "white")
    h.box(name + "_eye_corner", (x, y + 1, z - 2.75), (5.6, 5.6, 0.6), "white", rotation=(0, 0, 45))
    h.box(name + "_lid_top", (x, y + 4.6, z - 2.9), (12, 1.6, 0.8), "gold_dark")
    h.box(name + "_lid_bottom", (x, y - 2.6, z - 2.9), (9, 1.4, 0.8), "gold_dark")
    h.box(name + "_iris", (x, y + 1, z - 3.1), (4.4, 4.4, 0.6), glow)
    h.box(name + "_pupil", (x, y + 1, z - 3.5), (1.2, 4.4, 0.4), "brow")


def hand_gauntlet(g, name, centre, rot, glow):
    """The Bishop's hand: a plate gauntlet, jointed fingers, a knuckle plate, a flared cuff; a sigil on the palm."""
    x, y, z = centre
    h = g.group(name, centre, rot)
    hand_core(h, name, x, y, z, glow, segmented=True)
    h.box(name + "_knuckles", (x, y + 8.2, z + 2.9), (16.5, 3.4, 1.6), "gold_dark")
    h.box(name + "_back_plate", (x, y + 1, z + 2.9), (13, 9, 1.2), "gold_dark")
    h.box(name + "_cuff", (x, y - 11.5, z + 0.5), (13, 6, 7), "gold_dark")
    for sx in (-1, 1):
        h.box(f"{name}_flare_{sx}", (x + sx * 6.5, y - 15.5, z + 0.5), (6, 3, 9.5), "gold", rotation=(0, 0, sx * 22.5))
    h.box(name + "_flare_mid", (x, y - 15.8, z + 0.5), (8, 3, 9.5), "gold")
    h.box(name + "_sigil", (x, y + 1, z - 2.8), (8, 8, 0.6), glow, rotation=(0, 0, 45))


def hand_jewelled(g, name, centre, rot, glow):
    """The Cardinal's hand: rings on the fingers, dark nails, a chain bracelet; a sigil on the palm."""
    x, y, z = centre
    h = g.group(name, centre, rot)
    hand_core(h, name, x, y, z, glow, nails=True)
    for i, (dx, ring_y, mat) in enumerate(((-5.85, 13, "emerald"), (1.95, 15, "gold_dark"), (5.85, 12.5, glow))):
        h.box(f"{name}_ring{i}", (x + dx, y + ring_y, z), (4.4, 1.6, 4.9), "gold_dark")
        h.box(f"{name}_ring{i}_gem", (x + dx, y + ring_y, z - 2.7), (2, 2, 0.8), mat, rotation=(0, 0, 45))
    h.box(name + "_cuff", (x, y - 10, z + 0.5), (11, 4, 6), "gold")
    for i in range(5):                                       # the bracelet's links
        h.box(f"{name}_link{i}", (x - 6 + i * 3, y - 12.6, z - 3.2), (2.4, 1.6, 1), "gold_dark",
              rotation=(0, 0, 25 if i % 2 else -25))
    h.box(name + "_sigil", (x, y + 1, z - 2.8), (7, 7, 0.6), glow, rotation=(0, 0, 45))


# ---- the takes -------------------------------------------------------------------------------------------------------

TAKES = {
    "F1": ("The Watcher", face_watcher, hood, hand_eye),
    "F2": ("The Bishop", face_bishop, mitre, hand_gauntlet),
    "F3": ("The Cardinal", face_cardinal, cardinal, hand_jewelled),
}


def build(key):
    title, face, dress, hand = TAKES[key]
    s1.evoker_head = lambda g, base, k=K: face(g)               # the priest builder calls this for the head
    m = Model(f"archevoker_face_{key}")
    root = m.group("root", (0, 0, 0))
    _, p = s1.TAKES["B"]
    s1.throne(root, p["back_top"])
    s1.hand_ring(root, *p["ring"])
    torso = s1.priest(root, "rest")
    head = next(g for g in m.groups if g.name == "head")
    dress(head, torso)
    hands = root.group("casting", (0, 0, 0))
    hand(hands, "hand_cyan", (48, 74, -12), (0, -14, -6), "cyan")
    hand(hands, "hand_purple", (-48, 74, -12), (0, 14, 6), "purple")
    solo = Model(f"archevoker_hand_{key}")
    hand(solo.group("root", (0, 0, 0)), "hand", (0, 26, 0), (0, -20, 0), "cyan")
    return m, solo, title


VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 6.6, "dist": 8.0, "target_z": 6.1,
     "player": False, "lens": 40},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 38, "height": 6.8, "dist": 8.2, "target_z": 5.9,
     "player": False, "lens": 40},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -22, "height": 1.62, "dist": 9.5, "target_z": 4.8,
     "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 38, "height": 6.8, "dist": 8.2, "target_z": 5.9,
     "player": False, "lens": 40},
]
HAND_VIEWS = [{"name": "hand", "mode": "flat", "camera": "persp", "yaw": 25, "height": 2.0, "dist": 4.6,
               "target_z": 1.85, "player": False, "lens": 40}]
LABELS = {"front": "front", "three_quarter": "three-quarter", "player_eye": "a player's eye", "clay": "clay",
          "hand": "the casting hand"}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in TAKES:
        m, solo, title = build(key)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, VIEWS)
        v2.run_blender(solo.render_json(v2.PALETTE), OUT / key, HAND_VIEWS)
        print(key, title, "cubes", len(m.cubes))
    names = [v["name"] for v in VIEWS + HAND_VIEWS]
    tw, th, pad, top = 330, 330, 10, 56
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + len(TAKES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Archevoker, session 1 step 2: the face, the vestments and the hands", font=sheet._font(26),
            fill=sheet.INK)
    for r, (key, (title, *_)) in enumerate(TAKES.items()):
        for c, n in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / f"{n}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key} {title}: {LABELS[n]}", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT / "faces.png")


# ---- take 2: the user's mix (2026-10-15) -------------------------------------------------------------------------

OUT2 = ROOT / "docs/art/bosses/archevoker/overhaul/s1_face2"


def small_hand_eye(g, name, centre, angle):
    """A hand of the ring with the casting hands' open eye in its palm."""
    x, y, z = centre
    h = g.group(name, centre, (0, 0, -angle))
    h.box(name + "_palm", (x, y, z), (7, 7.5, 2.5), "gold")
    for i, dx in enumerate((-2.55, -0.85, 0.85, 2.55)):
        h.box(f"{name}_f{i}", (x + dx, y + 3.75 + 2.6, z), (1.6, 5.2 + (i in (1, 2)) * 0.8, 2.2), "gold")
    h.box(name + "_thumb", (x - 4.6, y + 0.5, z - 0.3), (1.8, 5, 2.2), "gold", rotation=(0, 0, 32))
    h.box(name + "_cuff", (x, y - 5, z + 0.3), (6, 3, 3), "gold_dark")
    h.box(name + "_eye", (x, y + 0.3, z - 1.4), (5, 2.4, 0.4), "white")
    h.box(name + "_iris", (x, y + 0.3, z - 1.65), (2, 2, 0.3), "cyan")
    h.box(name + "_pupil", (x, y + 0.3, z - 1.85), (0.6, 2, 0.2), "brow")


def dress_mix(head, torso):
    hood(head, torso, cape=False)
    chain_of_office(torso)


MIX = {
    "M1": ("The Watcher's eyes", face_watcher),
    "M2": ("The Cardinal's slit eyes", face_cardinal),
}


def mix():
    """The hood (without its cape), F3's neck and chain of office, the eye in the palm on every gilded hand; two
    faces in the hood."""
    if OUT2.exists():
        shutil.rmtree(OUT2)
    OUT2.mkdir(parents=True)
    v2.PALETTE.update(PALETTE)
    s1.small_hand = small_hand_eye
    for key, (title, face) in MIX.items():
        TAKES[key] = (title, face, dress_mix, hand_eye)
        m, _, _ = build(key)
        v2.run_blender(m.render_json(v2.PALETTE), OUT2 / key, VIEWS)
        print(key, title, "cubes", len(m.cubes))
    solo = Model("archevoker_ring_hand")
    small_hand_eye(solo.group("root", (0, 0, 0)), "ring_hand", (0, 26, 0), 0)
    v2.run_blender(solo.render_json(v2.PALETTE), OUT2, [{"name": "ring_hand", "mode": "flat", "camera": "persp",
                   "yaw": 20, "height": 1.8, "dist": 2.4, "target_z": 1.7, "player": False, "lens": 40}])
    names = [v["name"] for v in VIEWS]
    tw, th, pad, top = 360, 360, 10, 56
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad) + th + 34 + pad), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Archevoker, step 2 take 2: the hood, the chain of office, eyes in every palm",
            font=sheet._font(26), fill=sheet.INK)
    for r, (key, (title, _)) in enumerate(MIX.items()):
        for c, n in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT2 / key / f"{n}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key} {title}: {LABELS[n]}", font=sheet._font(16), fill=sheet.DIM)
    y = top + 2 * (th + 34 + pad)
    img.paste(sheet._tile(OUT2 / "ring_hand.png", tw, th), (pad, y))
    dr.text((pad, y + th + 6), "a hand of the ring, close up", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT2 / "faces.png")


# ---- take 3: a better hood, and a clear neck and shoulders (2026-10-15) -------------------------------------------

OUT3 = ROOT / "docs/art/bosses/archevoker/overhaul/s1_face3"


# the hood's opening seen from the front, his right half (x, height above the chin): the wall past the jaw, a short
# chamfer round the head's corner, the crown up to a soft peak
HOOD_LINE = [(12.6, -5.5), (12.2, 20.0), (9.4, 29.0), (0.0, 33.0)]


def hood_line(inset=0.0):
    """The whole line, left wall to right wall; inset moves it inward along its normals."""
    half = [(x, HB + y) for x, y in HOOD_LINE]
    pts = [(-x, y) for x, y in half] + [(x, y) for x, y in reversed(half[:-1])]
    if not inset:
        return pts
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty)
        out.append((x - ty / n * inset, y + tx / n * inset))
    return out


def mitred(g, name, pts, t, zr, mat):
    """Slabs along a line, each lengthened at a joint by just enough that the two outer faces meet in a clean mitre
    (no gap, no overhang). zr: (z0, z1) for every slab, or one pair for all."""
    angles = [math.atan2(b[1] - a[1], b[0] - a[0]) for a, b in zip(pts, pts[1:])]
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        z0, z1 = zr[i] if isinstance(zr[0], tuple) else zr
        ext = [0.0, 0.0]
        if i > 0:
            ext[0] = t / 2 * abs(math.tan((angles[i] - angles[i - 1]) / 2))
        if i < len(angles) - 1:
            ext[1] = t / 2 * abs(math.tan((angles[i + 1] - angles[i]) / 2))
        length = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        shift = (ext[1] - ext[0]) / 2                        # lengthen unevenly: move the centre towards the longer end
        c = ((x0 + x1) / 2 + ux * shift, (y0 + y1) / 2 + uy * shift, (z0 + z1) / 2)
        g.box(f"{name}_{i}", c, (length + ext[0] + ext[1], t, z1 - z0), mat, rotation=(0, 0, math.degrees(angles[i])))


def hood_draped(head, torso):
    """The hood made to hang like cloth: a pointed opening whose walls, chamfers and crown meet in clean mitres (no
    eaves, no ridge), a thin gold edge with a dark lining inside it, sides that drop past the jaw and turn out over the
    shoulders, a back that falls between the shoulder blades and ends in a point. The front stays open on the collar
    and the chain."""
    w, d = 8 * K + 5, 8 * K + 7
    t = 2.8
    zf = FACE - 2.2                                          # the opening's front edge
    zb = HZ + 1.5 + d / 2                                    # its back
    line = hood_line()
    walls, top = (zf, HZ + 10), (zf, zb)
    mitred(head, "hood", line, t, [walls, top, top, top, top, walls], "robe")
    mitred(head, "hood_edge", hood_line(inset=0.7), 1.3, (zf - 1.0, zf + 0.2), "trim")
    mitred(head, "hood_lining", hood_line(inset=2.3), 1.6, (zf + 0.2, zf + 2.2), "hood_in")
    for sx in (-1, 1):
        # the back corners chamfered at 45 degrees, so the hood rounds off behind instead of ending in a box
        head.box(f"hood_corner_{sx}", (sx * (w / 2 - 2.6), HB + 7.25, HZ + d / 2 - 2.4), (6.2, 25.5, 2.8), "robe",
                 rotation=(0, sx * 45, 0))
        # where the hood meets the body: the cloth turns out over each shoulder
        torso.box(f"hood_drape_{sx}", (sx * 13.5, Y + 36.2, Z + 3), (10, 2.6, 19), "robe", rotation=(0, 0, -sx * 24))
        torso.box(f"hood_drape_edge_{sx}", (sx * 13.5, Y + 36.2, Z - 6.6), (10, 2.6, 1.2), "trim",
                  rotation=(0, 0, -sx * 24))
    # the crown's underside filled behind the opening, and the back
    head.box("hood_fill", (0, HB + 28.2, HZ + 1.5), (17, 3, d - 4), "robe")
    head.box("hood_fill_top", (0, HB + 30.4, HZ + 1.5), (9, 2.4, d - 4), "robe")
    head.box("hood_back", (0, HB + 10, zb - 1.5), (w - 5, 35, 3), "robe")
    # the cloth falls on down the back and ends in a point between the shoulder blades
    torso.box("hood_back_fall", (0, Y + 30, Z + 12.6), (24, 13, 2.6), "robe", rotation=(8, 0, 0))
    torso.box("hood_point", (0, Y + 23.5, Z + 13.6), (12, 12, 2.4), "robe", rotation=(8, 0, 45))


def neck_and_shoulders(torso):
    """A standing collar the head sits in (the cassock's), and shoulders that slope down from it to the arms."""
    s1.vocto(torso, "neck_collar", (0, Y + 37.5, Z + 1), 18, 5, 16, "robe_dark", cham=0.25)
    torso.box("neck_collar_edge", (0, Y + 40.2, Z - 6.9), (12, 0.8, 1), "trim")
    for sx in (-1, 1):
        torso.box(f"shoulder_{sx}", (sx * 12.5, Y + 34.2, Z + 1.5), (13, 4, 16.5), "robe", rotation=(0, 0, -sx * 18))


def chain_draped(torso):
    """The chain of office lying over the shoulders and hanging in a U down the chest to the medallion."""
    pts = [(10.5, Y + 37.6, Z + 5), (14.2, Y + 35.4, Z + 0.5), (13.0, Y + 32.5, Z - 6.4), (9.2, Y + 28.6, Z - 9.0),
           (4.6, Y + 25.6, Z - 9.7)]
    for sx in (-1, 1):
        for i in range(len(pts) - 1):
            a = (sx * pts[i][0], pts[i][1], pts[i][2])
            b = (sx * pts[i + 1][0], pts[i + 1][1], pts[i + 1][2])
            s1.beam(torso, f"chain_{sx}_{i}", a, b, 2.4 if i % 2 == 0 else 1.8, "gold" if i % 2 == 0 else "gold_dark")
    torso.box("medallion", (0, Y + 23, Z - 9.9), (9, 9, 1.6), "gold", rotation=(0, 0, 45))
    torso.box("medallion_gem", (0, Y + 23, Z - 10.9), (5, 5, 1), "emerald", rotation=(0, 0, 45))


def drop(model, names):
    """Removes cubes by name (parts of the shared body that this take replaces)."""
    gone = [c for c in model.cubes if c.name in names]
    for c in gone:
        model.cubes.remove(c)
        c.group.children.remove(c)


def dress_hood3(head, torso):
    hood_draped(head, torso)
    neck_and_shoulders(torso)
    chain_draped(torso)


VIEWS3 = VIEWS[:2] + [
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 6.6, "dist": 8.0, "target_z": 5.9,
     "player": False, "lens": 40},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 7.2, "dist": 8.4, "target_z": 5.9,
     "player": False, "lens": 40},
    VIEWS[3],
]
LABELS.update(side="side", back="back three-quarter")


def hood3():
    for old in (OUT3.rglob("*") if OUT3.exists() else ()):   # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    OUT3.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    s1.small_hand = small_hand_eye
    for key, (title, face) in MIX.items():
        TAKES[key] = (title, face, dress_hood3, hand_eye)
        m, _, _ = build(key)
        drop(m, {"pendant", "collar"})
        if key == "M2":                                       # a look from behind: without the throne and the ring
            back = Model("archevoker_back")
            root = back.group("root", (0, 0, 0))
            torso = s1.priest(root, "rest")
            dress_hood3(next(g for g in back.groups if g.name == "head"), torso)
            drop(back, {"pendant", "collar"})
            v2.run_blender(back.render_json(v2.PALETTE), OUT3 / key / "alone", [VIEWS3[3]])
        v2.run_blender(m.render_json(v2.PALETTE), OUT3 / key, VIEWS3)
        print(key, title, "cubes", len(m.cubes))
    names = [v["name"] for v in VIEWS3]
    tw, th, pad, top = 330, 330, 10, 56
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Archevoker, step 2 take 3: the draped hood, the collar and shoulders, the chain",
            font=sheet._font(26), fill=sheet.INK)
    for r, (key, (title, _)) in enumerate(MIX.items()):
        for c, n in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT3 / key / f"{n}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key} {title}: {LABELS[n]}", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT3 / "faces.png")


if __name__ == "__main__":
    if sys.argv[1:] == ["mix"]:
        mix()
    elif sys.argv[1:] == ["hood"]:
        hood3()

    else:
        main()
