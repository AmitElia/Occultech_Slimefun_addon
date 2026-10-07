"""Session G8: the Frenzied set - tier-1 worn armor (enchanted-diamond level), themed on the Frenzy Idol.

Deep dusk-violet plates, grey-silver trims and horns, ember orange only where it glows; a 3D helm with big bull horns
built from chunky segments; ember seams and a few sparks. Follows the approved G6 method (session_g.py): vanilla
netherite coverage, all 3D in the helm, clean bevelled plates over a calm underlayer, accents on the structure and
mirrored, no back pieces.

Run: python tools/art/session_g8.py [version]   -> docs/art/session-g8/review-g8[-version].png and a helm GIF
Nothing is packed until the user approves (then `final` saves into session-g for build_pack).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw  # noqa: E402

import session_g as g  # noqa: E402
from blockkit import Model  # noqa: E402
from palettes import RAMPS  # noqa: E402
import render3d  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-g8")
os.makedirs(OUT, exist_ok=True)

SILVER = RAMPS["boundsteel"]  # grey-silver trims
EMBER = RAMPS["ember"]        # the light: orange to yellow to white-hot
BONE = RAMPS["bone"]          # the horns


def _mix(a, b, t):
    return tuple(round(a[k] * (1 - t) + b[k] * t) for k in range(3)) + (255,)


GOLD = RAMPS["gold"]          # the trims: gold brings the yellow (user, v9: more orange and yellow accents)
DUSK = [_mix(SILVER[i], RAMPS["dusk"][i], 0.4) for i in range(6)]   # a violet-grey, for the bone's cool shadows


class Palette:
    """One colour option for the set: the plates, the dark underlayer between them, and the trims."""

    def __init__(self, name, plate, under, trim):
        self.name, self.plate, self.under, self.trim = name, plate, under, trim


def _darker(ramp, k=1):
    return [ramp[max(0, i - k)] for i in range(6)]


ASH = [_mix(SILVER[i], RAMPS["dusk"][i], 0.28) for i in range(6)]       # the Frenzy Idol's stone (v8-v9)
IRON = g.DEEPSLATE                                                      # blackened iron
BRONZE = [(26, 18, 16, 255), (46, 33, 28, 255), (74, 54, 44, 255), (107, 80, 64, 255), (143, 109, 85, 255),
          (184, 148, 120, 255)]                                         # dark, warm, fire-tempered bronze
PALETTES = {
    "ash": Palette("ash (muted grey-violet)", ASH, _darker(ASH), GOLD),
    "iron": Palette("blackened iron", IRON, _darker(IRON), GOLD),
    "bronze": Palette("dark bronze", BRONZE, _darker(BRONZE), GOLD),
}
DEFAULT = "ash"
PLATE = ASH


# ---------------------------------------------------------------- worn layers

def seam(c, F, pts):
    """An ember seam: a line of fire glowing in the gap between plates - orange ends, a yellow core, one white-hot
    pixel."""
    for i, (u, v) in enumerate(pts):
        c.px(F, u, v, EMBER[3] if i in (0, len(pts) - 1) else EMBER[4])
    if len(pts) > 2:
        c.px(F, *pts[len(pts) // 2], EMBER[5])


def warm_plate(c, F, u0, v0, u1, v1, ramp, tone=3):
    """A bevelled plate lit twice: cool grey light on its top-left edges, and warm light from the fire below - its
    lower edge glows orange, brightest (yellow) at the lower-left corner."""
    for v in range(v0, v1 + 1):
        for u in range(u0, u1 + 1):
            col = ramp[tone]
            if v == v0 or u == u0:
                col = ramp[min(5, tone + 1)]
            if (u, v) == (u0, v0):
                col = ramp[min(5, tone + 2)]
            if v == v1 and v1 > v0:                   # warm light: a blend, not a stripe - stronger at the left
                col = _mix(ramp[max(0, tone - 1)], EMBER[3], 0.55 if u == u0 else 0.35)
            c.px(F, u, v, col)


# The body as hand-drawn pixel maps (Session B's lesson: hand-draw when geometry gives mush). v10 stacked plates in
# rows with a seam under each - the whole body turned into horizontal lines. Here every plate is shaded as a curved
# surface (lit left, darker right: columns, not rows), plate edges are V's and curves, the fire is a few deliberate
# things - the chest sun on its gold ridge, the molten V under the breastplate, vents beside the spine, the buckle,
# knee studs, the toe-cap vents - and the gold sits on the edges that frame them.
#   .  underlayer          ,  deep underlayer
#   H L P D K  plate: highlight, light, mid, dark, darkest
#   o q  plate lit by the fire (warm light / warm shadow)
#   G g h j  gold: light, mid, dark, darkest
#   w y e r  fire: white-hot, yellow, orange, deep orange
#   i b B  bone (the horn-stud): its lit tip, body, shadow
MAPS = {
    ("humanoid", "body", "front"): [
        "HL....PD",          # vanilla's chestplate has a V-neck: rows 0-2 cover only the shoulders
        "LL....PD",
        "LPG..GDD",          # the gold rim along the neckline
        "LPreerPD",          # the ember sun, just under the neck
        "LPewyePD",
        "LPreerDD",
        "LPPhgPDD",          # the gold ridge down to the V
        "oPPhgPDq",
        "eoPhgPqr",
        ".eoPPqr.",
        ".qeyyeq.",          # the molten point of the V (row 10 covers u 1-6)
        "..hGGh..",
    ],
    ("humanoid", "body", "back"): [
        "HLPhgPPD",
        "LLPhgPPD",
        "LPehgePD",
        "LPyhgyPD",
        "LPehgePD",
        "LPPhgPDD",
        "oPPhgPDq",
        "eoPhgPqr",
        ".eoPPqr.",
        "..rhgr..",
        ".LP..PD.",
        ".DP..PD.",
    ],
    ("humanoid", "body", "right"): [
        "HLPD", "LPPD", "LPPD", "LPDD", "LPDD", "oPDq", "eoqr", ".eo.", "..e.", "LPD.", "LPD.", "hgh."],
    ("humanoid", "body", "left"): [
        "HLPD", "LPPD", "LPPD", "LPDD", "LPDD", "oPDq", "reoq", ".oe.", ".e..", ".LPD", ".LPD", ".hgh"],
    ("humanoid", "body", "top"): ["HLgGGgPD", "LPPhgPPD", "LPPhgPDD", "LPPPPPDK"],
    # pauldrons (user, v12: more on the shoulders): a gold cap and a gold lower rim lit from just above by the fire,
    # and a bigger bone horn-stud - 2 x 3, its tip catching the light - on the outer face and on top, mirrored
    ("humanoid", "arm", "front"): ["hGGh", "HLPD", "LPPD", "LPDD", "oyeq", "hGgj"],
    ("humanoid", "arm", "back"): ["hggj", "LPPD", "LPPD", "LPDD", "oeeq", "hggj"],
    ("humanoid", "arm", "right"): ["hGGh", "HLib", "LPbB", "LPbB", "oyeq", "hGgj"],
    ("humanoid", "arm", "left"): ["hGGh", "biPD", "BbPD", "BbPD", "qeyo", "jgGh"],
    ("humanoid", "arm", "top"): ["hGGh", "GibH", "gbBh", "hhhj"],
    ("humanoid", "leg", "front"): [None] * 6 + ["HLPD", "LPPD", "LPPD", "oPDq", "Gyeh", "hggj"],   # boots cover rows 6-11
    ("humanoid", "leg", "back"): [None] * 6 + ["LPPD", "LPPD", "LPPD", "LPDD", ".gh.", ".hj."],
    ("humanoid", "leg", "right"): [None] * 6 + ["HLPD", "LPPD", "LPDD", "oPDq", "hggj", "jhhj"],
    ("humanoid", "leg", "left"): [None] * 6 + ["HLPD", "LPPD", "LPDD", "oPDq", "hggj", "jhhj"],
    ("humanoid_leggings", "body", "front"): [None] * 8 + ["hgGyyGgh", "jhgeeghj", "........", "........"],
    ("humanoid_leggings", "body", "back"): [None] * 8 + ["hggggggh", "jhhhhhhj", "........", "........"],
    ("humanoid_leggings", "body", "right"): [None] * 8 + ["hggh", "jhhj", "....", "...."],
    ("humanoid_leggings", "body", "left"): [None] * 8 + ["hggh", "jhhj", "....", "...."],
    ("humanoid_leggings", "leg", "front"): ["HLPD", "LPPD", "LPPD", "oPDq", "hGgh", "gyeh", "hggj", "LPPD", "LPPD"],
    ("humanoid_leggings", "leg", "back"): ["LPPD", "LPPD", "LPPD", "LPDD", "oPDq", ".qr.", "LPPD", "LPDD", "LPDD"],
    ("humanoid_leggings", "leg", "right"): ["HLPD", "LPPD", "LPPD", "oPDq", "eoqr", ".eo.", "LPPD", "LPDD", "LPDD"],
    ("humanoid_leggings", "leg", "left"): ["HLPD", "LPPD", "LPPD", "oPDq", "rqoe", ".oe.", "LPPD", "LPDD", "LPDD"],
    ("humanoid_leggings", "leg", "top"): ["HLPD", "LPPD", "LPDD", "PDDK"],
}


def frenzied_armor(pal=None):
    """Frenzied, worn - a fire-lit plate harness drawn by hand (MAPS): a breastplate shaded as one curved surface with
    a gold ridge carrying the ember sun, its lower edge a V of molten light; a back with ember vents either side of a
    gold spine; rounded pauldrons with a gold cap and a bone horn-stud; a gold belt with a glowing buckle; tassets
    curving to gold knee cops with ember studs; sabatons with gold toe caps and a vent of fire. No back piece."""
    pal = pal or PALETTES[DEFAULT]
    P, U, T = pal.plate, pal.under, pal.trim
    colours = {
        ".": U[3], ",": U[2],                      # one step lighter than v11: the muted grey-violet, not near-black
        "H": P[5], "L": P[4], "P": P[3], "D": P[2], "K": P[1],
        "o": _mix(P[3], EMBER[3], 0.45), "q": _mix(P[2], EMBER[2], 0.4),
        "G": T[4], "g": T[3], "h": T[2], "j": T[1],
        "w": EMBER[5], "y": EMBER[4], "e": EMBER[3], "r": EMBER[2],
        "i": BONE[5], "b": BONE[4], "B": BONE[2],
    }
    c = g.covered_canvas()
    for layer in ("humanoid", "humanoid_leggings"):          # the underlayer everywhere first
        for part in ("body", "arm", "leg"):
            for face in ("front", "back", "right", "left", "top", "bottom"):
                F = c.face(layer, part, face)
                for v in range(F[4]):
                    for u in range(F[3]):
                        c.px(F, u, v, U[3] if v < F[4] - 2 else U[2])
    for (layer, part, face), rows in MAPS.items():
        F = c.face(layer, part, face)
        for v, row in enumerate(rows):
            if row is None:
                continue
            for u, ch in enumerate(row):
                if ch in colours:
                    c.px(F, u, v, colours[ch])
    return c.layers


# ---------------------------------------------------------------- the helm

def horn_tex():
    """A bull horn's skin: ridged rings of grey-silver, lighter toward the tip, lit from the top-left."""
    img = g.blank()
    for y in range(16):
        for x in range(16):
            t = 4 if y < 5 else 3 if y < 12 else 2      # grey-silver, lit from above, one soft shadow beneath
            if x in (5, 11) and 4 <= y <= 13:
                t -= 1                                   # two soft growth rings
            if (x, y) in ((1, 2), (2, 2), (8, 1), (9, 1), (14, 2)):
                t += 1                                   # highlights along the top
            img.putpixel((x, y), SILVER[max(0, min(5, t))])
    return img


def ember_frames(n=4):
    """The breathing ember glow (horn tips, the brow sun): one colour per frame, swelling and fading."""
    return [g.fill(EMBER, [3, 4, 5, 4][f % 4]) for f in range(n)]


def sun_frames():
    """The ember sun on the brow: a hot core with four rays, breathing."""
    frames = []
    for f in range(4):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        hot = [EMBER[4], EMBER[5], EMBER[5], EMBER[4]][f]
        warm = [EMBER[3], EMBER[4], EMBER[4], EMBER[3]][f]
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                ray = abs(x - 7.5) < 1.2 or abs(y - 7.5) < 1.2
                if d < 3.5:
                    img.putpixel((x, y), hot)
                elif d < 5.5 or (ray and d < 7.8):
                    img.putpixel((x, y), warm)
                elif d < 6.5:
                    img.putpixel((x, y), EMBER[2])
        frames.append(img)
    return frames


# The horns, built as modded armor builds them (Blockbench style): a few tapering pieces, each turned a step further
# so the chain curves - a thick root at the temple, out, bending up in 22.5 degree steps, the last pieces leaning
# forward to a small tip. (x0, y0, z0, x1, y1, z1, rotation axis, angle, rotation origin, texture) for the left horn;
# the right is mirrored. The fire is in the material, not a flame on top: an ember crack glowing along the middle
# pieces, and a molten amber tip.
HORN = [
    ((-3.2, 10.2, 4.4), (0.4, 14.6, 9.6), None, 0, None, "root"),
    ((-7.2, 10.8, 4.9), (-2.6, 14.2, 9.1), "z", -22.5, (-2.6, 12.5, 7.0), "mid"),
    ((-10.2, 12.0, 5.3), (-6.2, 15.0, 8.7), "z", -45.0, (-6.2, 13.5, 7.0), "mid"),
    ((-10.6, 14.8, 5.6), (-8.0, 18.8, 8.4), "x", -22.5, (-9.3, 14.8, 7.0), "upper"),
    # the tip: square, not pointed - the horn's own thickness, cut off blunt and burning (user, v6)
    ((-10.6, 18.5, 4.07), (-8.0, 21.5, 6.87), "x", -5.0, (-9.3, 18.5, 5.47), "tip"),    # nearly upright on its base
]


CRIMSON = RAMPS["crimson"]


def bone_shade(y, tone):
    """Bone as a cylinder lit from the top-left (STYLE rule 3): a warm highlight band along its upper side, the body,
    then shadows that lean violet (rule 4) - no lines anywhere."""
    if y < 2:
        return _mix(BONE[min(5, tone + 1)], EMBER[5], 0.15)           # warm highlight
    if y < 5:
        return BONE[min(5, tone + 1)] if y < 3 else BONE[tone]
    if y < 11:
        return BONE[tone]
    if y < 14:
        return _mix(BONE[tone - 1], DUSK[2], 0.25)                     # shadow leaning violet
    return _mix(BONE[tone - 2], DUSK[1], 0.35)


# a few hand-placed wear marks: small soft flecks, never lines (lighter scuffs high up, darker pits low down)
WEAR_LIGHT = ((2, 3), (3, 3), (11, 4), (7, 6))
WEAR_DARK = ((5, 9), (13, 8), (9, 12), (10, 12), (1, 11))


def bone_skin(tone, drips=False):
    """A horn piece of bone, shaded as a cylinder with a few scuffs and pits. `drips`: the blood running down from the
    burning tip reaches over this piece's upper edge (the piece right under the tip)."""
    img = g.blank()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), bone_shade(y, tone))
    for (x, y) in WEAR_LIGHT:
        img.putpixel((x, y), _mix(BONE[min(5, tone + 1)], EMBER[5], 0.25))
    for (x, y) in WEAR_DARK:
        img.putpixel((x, y), _mix(BONE[tone - 1], DUSK[2], 0.4))
    if drips:
        for x, length in DRIP_ENDS:
            for y in range(length):
                img.putpixel((x, y), CRIMSON[2] if y < length - 1 else CRIMSON[1])
            img.putpixel((x, 0), CRIMSON[3])
    return img


# the blood stain on the tip: how far down each column the stain reaches (a ragged edge with drips - hand-drawn), and
# the drips that run on down the piece below
STAIN = [9, 10, 9, 8, 9, 11, 15, 10, 9, 8, 9, 10, 13, 15, 10, 9]
DRIP_ENDS = ((6, 4), (13, 6))


def stain_frames(n=6):
    """The tip, burning like a fresh blood stain: white-hot and yellow at the very top, through orange to blood red,
    to deep crimson at the stain's ragged edge, its drips running down the bone. Emissive (heat-coloured, no outline,
    STYLE rule 10). Animated: the heat breathes up and down, and a glint of light runs down each drip."""
    frames = []
    for f in range(n):
        pulse = [0.0, 0.06, 0.12, 0.08, 0.02, -0.04][f % 6]
        img = g.blank()
        for y in range(16):
            for x in range(16):
                depth = STAIN[x]
                if y >= depth:
                    img.putpixel((x, y), BONE[3] if x < 6 else BONE[2])   # bone below the stain, lit from the left
                    continue
                h = 1 - y / depth + pulse
                col = (EMBER[5] if h > 0.86 else EMBER[4] if h > 0.68 else EMBER[3] if h > 0.5 else CRIMSON[4] if h > 0.34
                       else CRIMSON[3] if h > 0.18 else CRIMSON[2])
                img.putpixel((x, y), col)
        for x, length in ((6, 15), (13, 15)):                  # a glint of light running down each drip
            y = 9 + (f * 2) % 6
            if y < length:
                img.putpixel((x, y), CRIMSON[5])
        frames.append(img)
    return frames


def stain_top_frames(n=6):
    """The tip's cut face: the hottest part, white-hot in the middle cooling to orange and red at the rim."""
    frames = []
    for f in range(n):
        pulse = [0.0, 0.3, 0.6, 0.4, 0.1, -0.2][f % 6]
        img = g.blank()
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5) - pulse
                img.putpixel((x, y), EMBER[5] if d < 3 else EMBER[4] if d < 5.5 else EMBER[3] if d < 7.5 else CRIMSON[4])
        frames.append(img)
    return frames


def frenzied_helm_worn(pal=None):
    """The Frenzied Helm worn - open-faced (the whole face shows): a domed helm of deep violet plate; a heavy silver
    brow ridge bearing down toward the centre, the Frenzy Idol's ember sun set in it (breathing glow); silver cheek
    guards; and two bull horns of bone, built of tapering pieces that bend out, up and forward, cut off square at the
    end - and the tips burn like fresh blood stains: white-hot at the top through orange to blood red, drips running
    down the bone (animated)."""
    pal = pal or PALETTES[DEFAULT]
    m = Model("frenzied_helmet_head")
    m.part = True
    top_i, side_i, back_i = g.tex_helm(pal.plate, tone=3)
    for img in (side_i, back_i):                      # the shell's lower rim: a gold band lit orange by the fire
        for x in range(16):                           # (v12's orange tint over the ash plate read as copper)
            img.putpixel((x, 13), pal.trim[4] if x % 5 else pal.trim[5])
            img.putpixel((x, 14), pal.trim[3])
            img.putpixel((x, 15), _mix(pal.trim[2], EMBER[3], 0.5))
    t_top, t_side, t_back = m.texture("helm_top", top_i), m.texture("helm_side", side_i), m.texture("helm_back", back_i)
    brow = g.tex_smooth(pal.plate, tone=3)
    for x in range(16):                               # a gold upper edge, firelight on the lower edge
        brow.putpixel((x, 0), pal.trim[4] if x < 6 else pal.trim[3])
        brow.putpixel((x, 1), pal.trim[2])
        brow.putpixel((x, 15), _mix(brow.getpixel((x, 15)), EMBER[3], 0.55))
        brow.putpixel((x, 14), _mix(brow.getpixel((x, 14)), EMBER[3], 0.3))
    t_brow = m.texture("brow", brow)
    skins = {"root": m.texture("horn_root", bone_skin(2)), "mid": m.texture("horn_mid", bone_skin(3)),
             "upper": m.texture("horn_upper", bone_skin(3, drips=True)),
             "tip": m.texture("horn_tip", stain_frames()), "tip_top": m.texture("horn_tip_top", stain_top_frames())}
    t_sun = m.texture("sun", sun_frames())
    T = lambda t, w, h: (t, [0, 0, max(1, min(16, round(w))), max(1, min(16, round(h)))])  # noqa: E731
    # the helmet shell (as the approved G6 helms)
    m.cube((0.6, 14.6, 0.6), (15.4, 16.0, 15.6), (t_side, [0, 0, 16, 2]), top=(t_top, [0, 0, 16, 16]))
    m.cube((2.2, 16.0, 2.2), (13.8, 16.8, 14.4), (t_side, [0, 0, 16, 1]), top=(t_top, [2, 2, 14, 14]))
    m.box((0.6, 2.0, 14.6), (15.4, 14.6, 16.0), {"south": (t_back, [0, 2, 16, 16]), "north": (t_side, [0, 2, 16, 16]),
          "west": (t_side, [0, 2, 2, 16]), "east": (t_side, [0, 2, 2, 16]), "down": (t_side, [0, 14, 16, 16])})
    for x0 in (0.0, 14.6):
        m.cube((x0, 3.0, 0.6), (x0 + 1.4, 14.6, 14.6), (t_side, [0, 3, 16, 16]))
    # the heavy silver brow ridge, lower at the middle (bearing down toward the centre), the ember sun in it
    m.cube((0.2, 11.4, -0.6), (15.8, 14.6, 1.2), T(t_brow, 16, 3))
    m.cube((5.4, 10.4, -0.9), (10.6, 12.2, 0.2), T(t_brow, 5, 2))
    m.box((6.6, 11.0, -1.3), (9.4, 13.8, -0.9), {d: (t_sun, [0, 0, 16, 16]) for d in g.FACES_ALL}, shade=False, light=15)
    # silver cheek guards
    for x0 in (0.2, 14.0):
        m.cube((x0, 3.0, -0.2), (x0 + 1.8, 11.4, 1.2), T(t_brow, 2, 8))
    # the horns, mirrored (a mirror reverses turns about y and z)
    for side in (-1, 1):
        for (a, b, axis, angle, origin, skin) in HORN:
            if side > 0:
                a, b = (16 - b[0], a[1], a[2]), (16 - a[0], b[1], b[2])
            faces = {d: (skins[skin], [0, 0, 16, 16]) for d in g.FACES_ALL}
            if skin == "tip":
                faces["up"] = (skins["tip_top"], [0, 0, 16, 16])
            el = m.box(a, b, faces, shade=skin != "tip", light=12 if skin == "tip" else 0)
            if axis:
                o = list(origin) if side < 0 else [16 - origin[0], origin[1], origin[2]]
                el["rotation"] = {"origin": o, "axis": axis, "angle": angle if (side < 0 or axis == "x") else -angle}
    m.display = g.HEAD_DISPLAY
    return m


# ---------------------------------------------------------------- review renders

HEAD_SCALE = 0.625          # vanilla draws a head item at 0.625 of a block, centred on the head (CustomHeadLayer)


def worn_preview(layers, helm):
    """A body wearing the set: the mannequin's boxes with the worn layers, the helm model placed on its head."""
    tmp = os.path.join(OUT, "equipment", "_preview")
    os.makedirs(tmp, exist_ok=True)
    for layer, img in layers.items():
        img.save(os.path.join(tmp, f"{layer}.png"))
    old_out = g.OUT
    g.OUT = OUT
    try:
        body = g.mannequin("_preview")
    finally:
        g.OUT = old_out
    for name, tex in helm.textures.items():
        body.textures["h_" + name] = tex
    for e in helm.elements:
        el = {"from": [], "to": [], "faces": {}, "shade": e.get("shade", True)}
        # a head item is turned half a turn about y (CustomHeadLayer): mirror x and z about the head's centre
        a, b = e["from"], e["to"]
        lo = [8 - (b[0] - 8) * HEAD_SCALE, 28 + (a[1] - 8) * HEAD_SCALE, 8 - (b[2] - 8) * HEAD_SCALE]
        hi = [8 - (a[0] - 8) * HEAD_SCALE, 28 + (b[1] - 8) * HEAD_SCALE, 8 - (a[2] - 8) * HEAD_SCALE]
        el["from"], el["to"] = lo, hi
        if "light_emission" in e:
            el["light_emission"] = e["light_emission"]
        if "rotation" in e:
            r = dict(e["rotation"])
            o = r["origin"]
            r["origin"] = [8 - (o[0] - 8) * HEAD_SCALE, 28 + (o[1] - 8) * HEAD_SCALE, 8 - (o[2] - 8) * HEAD_SCALE]
            if r["axis"] in ("x", "z"):
                r["angle"] = -r["angle"]          # the half turn about y reverses turns about x and z
            el["rotation"] = r
        swap = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "up", "down": "down"}
        for d, face in e["faces"].items():
            el["faces"][swap[d]] = {"texture": "#h_" + face["texture"].lstrip("#"), "uv": face["uv"]}
        body.elements.append(el)
    return body


def sheet(layers, helm, path):
    """The review sheet: the set worn, from four sides, a helm close-up, and the flat layers."""
    worn = worn_preview(layers, helm)
    views = [render3d.render(worn, yaw=yaw, pitch=12, s=11, size=(300, 420), center=(8, 18, 8)) for yaw in (25, 155, 205, 90)]
    # a head model's front is its north face (the game turns it to the wearer's front)
    helm_view = render3d.render(helm, yaw=210, pitch=20, s=10, size=(420, 420), center=(8, 14, 8))
    helm_front = render3d.render(helm, yaw=180, pitch=5, s=10, size=(420, 420), center=(8, 14, 8))
    flat = g.armor_preview(layers, scale=4)
    w = 300 * 4
    out = Image.new("RGBA", (w, 420 + 440 + flat.height + 20), (34, 32, 40, 255))
    for i, v in enumerate(views):
        out.alpha_composite(v, (i * 300, 0))
    out.alpha_composite(helm_view, (60, 430))
    out.alpha_composite(helm_front, (500, 430))
    out.alpha_composite(flat, ((w - flat.width) // 2, 870))
    ImageDraw.Draw(out).text((10, 8), "Frenzied set - worn (front-left, back-right, back-left, side), helm, flat layers", fill=(220, 210, 230, 255))
    out.save(path)
    return worn


def horn_closeup(helm, path):
    """The horn and its burning tip up close, from the front-left and from above-right."""
    views = [render3d.render(helm, frame=f, yaw=yaw, pitch=pitch, s=26, size=(520, 520), center=(18, 16, 7))
             for (f, yaw, pitch) in ((0, 200, 15), (2, 150, 25))]
    out = Image.new("RGBA", (1040, 520))
    for i, v in enumerate(views):
        out.alpha_composite(v, (i * 520, 0))
    out.save(path)


def body_closeup(layers, helm, path):
    """The body large, straight-ish from the front and from behind."""
    worn = worn_preview(layers, helm)
    views = [render3d.render(worn, yaw=y, pitch=5, s=20, size=(480, 760), center=(8, 17, 8)) for y in (15, 195)]
    out = Image.new("RGBA", (960, 760))
    for i, v in enumerate(views):
        out.alpha_composite(v, (i * 480, 0))
    out.save(path)


def helm_gif(helm, path):
    frames = [render3d.render(helm, frame=f, yaw=210, pitch=20, s=9, size=(360, 360), center=(8, 14, 8)).convert("RGB") for f in range(4)]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=220, loop=0)


def colour_sheet(path):
    """The colour options side by side: each palette worn, from the front-left and the back."""
    out = Image.new("RGBA", (300 * 2 * len(PALETTES), 450), (34, 32, 40, 255))
    draw = ImageDraw.Draw(out)
    for k, (key, pal) in enumerate(PALETTES.items()):
        worn = worn_preview(frenzied_armor(pal), frenzied_helm_worn(pal))
        for n, yaw in enumerate((25, 205)):
            out.alpha_composite(render3d.render(worn, yaw=yaw, pitch=12, s=11, size=(300, 420), center=(8, 18, 8)),
                                ((2 * k + n) * 300, 30))
        draw.text((2 * k * 300 + 10, 8), key + ": " + pal.name, fill=(230, 220, 200, 255))
    out.save(path)


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    layers = frenzied_armor()
    helm = frenzied_helm_worn()
    colour_sheet(os.path.join(OUT, f"colours-g8{'' if version == 'final' else '-' + version}.png"))
    suffix = "" if version == "final" else "-" + version
    sheet(layers, helm, os.path.join(OUT, f"review-g8{suffix}.png"))
    helm_gif(helm, os.path.join(OUT, f"helm-g8{suffix}.gif"))
    horn_closeup(helm, os.path.join(OUT, f"horn-g8{suffix}.png"))
    body_closeup(layers, helm, os.path.join(OUT, f"body-g8{suffix}.png"))
    d = os.path.join(OUT, "equipment", "frenzied")
    os.makedirs(d, exist_ok=True)
    for layer, img in layers.items():
        img.save(os.path.join(d, f"{layer}.png"))
    if version == "final":           # approved: into session-g, where build_pack picks it up
        g.save(helm)
        g.save_armor("frenzied", layers)
    print(os.path.join(OUT, f"review-g8{suffix}.png"))
