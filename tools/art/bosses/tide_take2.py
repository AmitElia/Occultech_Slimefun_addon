"""The Tidebreaker redesign, session 1 step 1, take 2: the Viking Longship.

The pick (2026-11-04, docs/art/bosses/tidebreaker/overhaul/plan.md): B, the Serpent Stem, because it reads as a
Viking ship, with the rider standing in the bow like C's harpooner. He is a drowned Viking now: a horned helmet,
torn leather clothes, a long spear he throws.

- The bow: B's clinker strakes, lowered to his hips (C's placement) so he stands in plain view; a short deck under
  him, round shields hung along the gunwale as on a longship, the stem post rising and curling into the carved sea
  serpent, the lantern hanging from its jaws.
- The Viking: a drowned at 1.3 times. An iron dome helmet with a brow band, a nasal and two horns curving out and
  up; the drowned's face with a matted beard and barnacles; a torn leather tunic and a tattered cloak; leather
  bracers and leg wraps. A long spear with a leaf blade.
- Three poses: idle (the spear upright), the ram (couched like a lance) and the throw (drawn back over his shoulder:
  the trident volley).

Run from the repository root: python tools/art/bosses/tide_take2.py
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as ms, tide_silhouettes as t1, volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import CY, CZ, R, W, beam, plate, plank, _n  # noqa: E402

K = 1.45                      # the Viking: a drowned at 1.45 times, bigger than the whaler (he is the target)

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s1_take2"
PALETTE = dict(t1.PALETTE, **{
    "leather": (116, 80, 52), "leather_dark": (76, 54, 40), "horn": (216, 202, 170), "hair": (104, 98, 84),
    "fur": (92, 82, 70),
})
POSES = ("idle", "ram", "throw")


def spear(g, hand, d, back, ahead, name="spear"):
    """The long spear: an ash shaft, an iron socket and a broad leaf blade."""
    hand, d = np.array(hand, float), _n(d)
    butt, tip = hand - d * back, hand + d * ahead
    beam(g, name + "_shaft", butt, tip, 1.5, "wood")
    beam(g, name + "_socket", tip - d * 1.5, tip + d * 1.5, 2.2, "iron")
    side = _n(np.cross(d, (0, 1, 0)) if abs(d[1]) < 0.9 else np.cross(d, (1, 0, 0)))
    plank(g, name + "_blade", tip + d * 1.2, tip + d * 9.5, 3.2, 0.8, "iron", up=side)
    plank(g, name + "_point", tip + d * 9.0, tip + d * 11.5, 1.6, 0.8, "iron", up=side)
    beam(g, name + "_butt", butt - d * 0.6, butt + d * 0.8, 2.0, "iron")


def helmet(g, head, k=K):
    """The iron dome helmet: a rounded crown, a brow band, the nasal down his nose, two horns curving out and up."""
    top = head + np.array([0, 3.5 * k, 0])
    ms.ball(g, "helm", tuple(top + (0, 0.6 * k, 0)), (8.8 * k, 5.2 * k, 8.8 * k), "iron", cham=0.34)
    g.box("helm_band", tuple(top + (0, -1.2 * k, 0)), (9.3 * k, 1.4 * k, 9.3 * k), "iron")
    g.box("helm_nasal", tuple(top + (0, -3.2 * k, -4.5 * k)), (1.3 * k, 3.6 * k, 0.8 * k), "iron")
    for s in (-1, 1):
        # a bull's crescent: out of the band, up, then curving forward to a point
        pts = [top + (s * 4.0 * k, 0.4 * k, 0.4 * k), top + (s * 7.0 * k, 1.6 * k, 0), top + (s * 8.8 * k, 4.2 * k, -1.2 * k),
               top + (s * 8.4 * k, 6.8 * k, -3.0 * k), top + (s * 6.8 * k, 8.2 * k, -4.8 * k)]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            beam(g, f"horn_{s}_{i}", a, b, (2.9 - 0.5 * i) * k, "horn")


def viking(g, hip, pose, k=K, head_fn=None):
    """The drowned Viking standing braced in the bow (legs in the mount's space, the rest leaning as one)."""
    hx, hy, hz = hip
    lean = {"idle": -4, "ram": -22, "throw": 8}[pose]
    for s, knee, foot in ((-1, (-2.3 * k, hy - 5.6 * k, hz - 4.2 * k), (-2.5 * k, hy - 11.5 * k, hz - 3.8 * k)),
                          (1, (2.5 * k, hy - 6 * k, hz + 1.8 * k), (2.7 * k, hy - 11.5 * k, hz + 3.6 * k))):
        beam(g, f"thigh_{s}", (s * 2.2 * k, hy, hz), knee, 4.2 * k, "leather_dark")
        beam(g, f"shin_{s}", knee, foot, 3.8 * k, "leather")                 # the leg wraps
        g.box(f"boot_{s}", (foot[0], foot[1] - 0.6, foot[2] - 1.0), (4.4 * k, 2.4 * k, 5.8 * k), "leather_dark")
    r = g.group("rider", tuple(hip), (lean, 0, 0))
    # the torn tunic: a belted body, its hem hanging in ragged strips
    r.box("tunic_hips", (hx, hy + 1.4 * k, hz), (8.8 * k, 3 * k, 5 * k), "leather")
    r.box("belt", (hx, hy + 3.2 * k, hz), (9.2 * k, 1.4 * k, 5.4 * k), "leather_dark")
    r.box("buckle", (hx, hy + 3.2 * k, hz - 2.8 * k), (2 * k, 1.6 * k, 0.6 * k), "iron")
    for i, (dx, ln, dz) in enumerate(((-3.4, 5.5, -1), (-1.2, 3.5, -1), (1.3, 6.5, -1), (3.4, 4, -1),
                                      (-2.6, 5, 1), (2.2, 6, 1))):
        r.box(f"hem{i}", (hx + dx * k, hy - ln / 2 * k + 0.2, hz + dz * 2.3 * k), (2.0 * k, ln * k, 0.9 * k),
              "leather", rotation=(dz * 6, 0, dx * 2))
    r.box("torso", (hx, hy + 8 * k, hz), (8.4 * k, 10 * k, 4.6 * k), "leather")
    r.box("chest_tear", (hx + 1.6 * k, hy + 8.5 * k, hz - 2.35 * k), (2.6 * k, 3.2 * k, 0.4), "skin")
    # the tattered cloak: over the shoulders and down his back in strips; a fur collar
    r.box("fur_collar", (hx, hy + 12.4 * k, hz + 0.4 * k), (10.4 * k, 2.4 * k, 6 * k), "fur")
    r.box("cloak", (hx, hy + 7.5 * k, hz + 3.1 * k), (9.6 * k, 9 * k, 0.9 * k), "leather_dark", rotation=(6, 0, 0))
    for i, (dx, ln) in enumerate(((-3.6, 6), (-1.2, 9), (1.2, 5), (3.6, 8))):
        r.box(f"cloak_strip{i}", (hx + dx * k, hy + 3 * k - ln / 2 * k, hz + 3.7 * k), (2.2 * k, ln * k, 0.8 * k),
              "leather_dark", rotation=(10, 0, dx * 1.5))
    if head_fn:
        head_fn(r, np.array(hip, float))
    else:
        r.box("barnacle_shoulder", (hx - 3.4 * k, hy + 12.9 * k, hz - 1.2 * k), (2.6 * k, 1.8 * k, 2.6 * k), "barnacle")
        # the head: the drowned's face, the matted beard, barnacles; the eyes glow under the helm
        head = np.array([hx, hy + 17.4 * k, hz - 0.4 * k])
        r.box("head", tuple(head), (8 * k, 7 * k, 8 * k), "skin")
        r.box("jaw", tuple(head + (0, -4.2 * k, -0.4 * k)), (7.2 * k, 2 * k, 6.8 * k), "skin_dark", rotation=(6, 0, 0))
        r.box("beard", tuple(head + (0, -6.2 * k, -3.2 * k)), (6.4 * k, 5.4 * k, 2.2 * k), "hair", rotation=(-10, 0, 0))
        r.box("beard_tip", tuple(head + (0.6 * k, -9.6 * k, -3.6 * k)), (3.2 * k, 3 * k, 1.6 * k), "hair",
              rotation=(-14, 0, 4))
        for s in (-1, 1):
            r.box(f"eye_{s}", tuple(head + (s * 1.8 * k, 0.4 * k, -4.05 * k)), (1.6 * k, 1 * k, 0.4), "eye")
        for i, (dx, dy, sz) in enumerate(((2.9, -1.4, 1.6), (-3.3, -2.2, 1.3))):
            r.box(f"barnacle{i}", tuple(head + (dx * k, dy * k, -4.2 * k)), (sz * k, sz * k, 1.2 * k), "barnacle")
        helmet(r, head, k)
    # arms: bare drowned upper arms, leather bracers; the spear in the right hand
    sh_r, sh_l = np.array([hx + 5.4 * k, hy + 11.6 * k, hz]), np.array([hx - 5.4 * k, hy + 11.6 * k, hz])
    if pose == "idle":
        el_r, hand_r = sh_r + (1.4 * k, -5.5 * k, -1 * k), sh_r + (1.4 * k, -8 * k, -5 * k)
        el_l, hand_l = sh_l + (-1.2 * k, -5.5 * k, 0), sh_l + (-1.4 * k, -10.5 * k, 0.5 * k)
        d, back, ahead = (0, 1, -0.06), 24, 30
    elif pose == "ram":
        el_r, hand_r = sh_r + (0.6 * k, -4.5 * k, 3.0 * k), sh_r + (-0.6 * k, -5.5 * k, -4.5 * k)
        el_l, hand_l = sh_l + (1.2 * k, -3.5 * k, -5.0 * k), sh_l + (6.0 * k, -3.6 * k, -10.5 * k)
        d, back, ahead = (-0.1, 0.3, -1), 22, 34
    else:                                                     # drawn back over his shoulder, the left arm aiming
        el_r, hand_r = sh_r + (1.6 * k, 2.6 * k, 3.4 * k), sh_r + (0.8 * k, 6.4 * k, 4.4 * k)
        el_l, hand_l = sh_l + (-0.6 * k, -0.6 * k, -5.4 * k), sh_l + (0.6 * k, 0.6 * k, -10.6 * k)
        d, back, ahead = (0, 0.32, -1), 28, 26
    for side, sh, el, hd in (("r", sh_r, el_r, hand_r), ("l", sh_l, el_l, hand_l)):
        beam(r, f"arm_{side}", sh, el, 3.8 * k, "skin")
        beam(r, f"bracer_{side}", el, hd, 3.7 * k, "leather")
        r.box(f"hand_{side}", tuple(hd), (3 * k, 3 * k, 3 * k), "skin")
    spear(r, hand_r, d, back, ahead)


def serpent(g, top):
    """The stem post rising and leaning out ahead of him, curling into the carved sea serpent: carved wood with red
    paint (green would melt into the drowned's skin), jaws open, horns swept back, a fin down its neck."""
    p = top + np.array([0, 0, -0.8])
    pts = [p, p + (0, 6, -5), p + (0, 12, -8.5), p + (0, 16.5, -9)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        beam(g, f"neck{i}", a, b, 4.6 - i * 0.4, "wood")
    head = pts[-1] + np.array([0, 0.5, -5])
    g.box("serpent_skull", head, (5.4, 5, 8.4), "wood")
    g.box("serpent_snout", head + (0, -0.4, -5.8), (4, 3.4, 4.2), "wood")
    g.box("serpent_jaw", head + (0, -4.0, -3.8), (4.2, 1.6, 8.4), "wood", rotation=(-22, 0, 0))
    g.box("serpent_tongue", head + (0, -2.4, -8.6), (1.2, 0.8, 3.2), "paint_red", rotation=(-12, 0, 0))
    for s in (-1, 1):
        g.box(f"serpent_eye_{s}", head + (s * 2.75, 1.0, -1.8), (0.6, 1.8, 1.8), "paint_white")
        g.box(f"serpent_horn_{s}", head + (s * 1.7, 3.6, 3.0), (1.3, 1.3, 5), "paint_red", rotation=(28, 0, 0))
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        m = (a + b) / 2 + np.array([0, 0, 2.6])
        g.box(f"fin{i}", m, (0.8, 3.8, 3.0), "paint_red", rotation=(-30 + 25 * i, 0, 0))
    return head + np.array([0, -5, -6])


def shields(g, top_deg, d_top, sheer, n=4):
    """Round shields hung outboard along the gunwale, overlapping like a longship's row: painted halves round an
    iron boss. They follow the top strake's own line (stem, mid, flank) from bow.()"""
    yt = CY + R * math.cos(math.radians(top_deg))
    zf = t1.front_z(yt, R + 0.5)
    hw = (W / 2 + 1.5) * min(1.0, 1.35 * math.sqrt(max(0.0, 1 - ((yt - CY) / R) ** 2)))
    for s in (-1, 1):
        line = [np.array(p) for p in ((0, yt + sheer, zf - d_top), (s * hw * 0.64, yt + sheer * 0.3, zf - d_top * 0.42),
                                       (s * hw, yt, zf + 9))]
        for i in range(n):
            f = 0.55 + 0.33 * i                               # along the two segments: 0 at the stem, 2 at the flank
            a, b = (line[0], line[1]) if f < 1 else (line[1], line[2])
            c = a + (b - a) * (f if f < 1 else f - 1)
            c = c + np.array([s * 2.0, -3.0, 0])
            plate(g, f"shield_{s}_{i}", tuple(c), 4.4, 1.0 + 0.3 * i, "paint_red" if (i + (s > 0)) % 2 else "paint_white")
            plate(g, f"shield_boss_{s}_{i}", tuple(c + (s * 0.9, 0, 0)), 1.4, 1.2 + 0.3 * i, "iron")


def longship(m, pose, stem=None, head_fn=None):
    g = t1.mount(m, "ram" if pose == "ram" else "idle")
    t1.shell(g)
    t1.body(g, 0.35 if pose == "ram" else 1.0)
    top_deg = 46
    top, gun = t1.bow(g, d_top=20, d_bot=4, top=top_deg, step=3.6, clinker=True, flank_back=11, flare=0.22, sheer=6)
    deck_y = CY + 2
    zf = t1.front_z(deck_y, R)
    g.box("deck", (0, deck_y, (top[2] + zf) / 2 + 1), (W - 4, 1.6, zf - top[2] + 2), "wood_dark")
    g.box("thwart", (0, deck_y + 6, top[2] + 10), (W - 3, 1.8, 3), "wood_dark")
    if stem:
        stem(g, top)
    else:
        hang = serpent(g, top)
        t1.lantern(g, "lantern", hang + (0, 2.5, 0))
    shields(g, top_deg, 20, 6)
    t1.lashing(g, "lash_bow", CZ - 2, out=2.6)
    t1.lashing(g, "lash_bow2", CZ + 5, out=1.6)
    viking(g, (0, deck_y + 1 + 11.6 * K, zf - 3.6 * K - 2.5), pose, head_fn=head_fn)
    t1.net(g, 262, 352)
    seat = np.array([0, deck_y + 6, zf + 2])
    t1.stuck_harpoon(g, "old_spear_l", (-W / 2 + 1, CY + 8, CZ + 10), (-0.7, 0.5, 0.5), seat + (-6, 0, 0))
    t1.stuck_harpoon(g, "old_spear_r", (W / 2 - 1, CY - 4, CZ + 6), (0.8, 0.15, 0.55), seat + (6, 0, 0))
    for i in range(2):                                        # spare spears racked inside the bow
        beam(g, f"rack{i}", (W / 2 - 1.5, deck_y + 2 + i * 1.8, top[2] + 7), (W / 2, deck_y + 9 + i * 1.8, zf + 4),
             1.3, "wood")


VIEWS = t1.VIEWS + [
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.6, "dist": 10.5, "target_z": 2.4,
     "player": False},
]
LABELS = dict(t1.LABELS, flat_front="front")


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    poses = [p for p in argv if p in POSES] or list(POSES)
    for pose in poses:
        m = Model(f"tidebreaker_longship_{pose}")
        longship(m, pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS[:1] if "quick" in argv else VIEWS)
        if pose == "idle":
            lo, hi = m.bounds()
            print("size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
    if "quick" in argv:
        return
    tw, th, pad, top = 380, 300, 12, 60
    img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tidebreaker, take 2: the Viking Longship", font=sheet._font(26), fill=sheet.INK)
    names = {"idle": "idle", "ram": "the ram", "throw": "the throw"}
    for r, pose in enumerate(POSES):
        for c, v in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{names[pose]}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "longship.png")


if __name__ == "__main__":
    main(sys.argv[1:])
