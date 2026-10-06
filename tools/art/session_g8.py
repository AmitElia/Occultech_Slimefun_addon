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

PLATE = RAMPS["violet"]       # deep purple plates
DUSK = RAMPS["dusk"]          # the warm violet-rose underlayer, as in the Frenzy Idol's stone
SILVER = RAMPS["boundsteel"]  # grey-silver trims and horns
EMBER = RAMPS["ember"]        # only where it glows


# ---------------------------------------------------------------- worn layers

def seam(c, F, pts):
    """An ember seam: a thin line of fire glowing in the gap between plates (bright core, dimmer ends)."""
    for i, (u, v) in enumerate(pts):
        c.px(F, u, v, EMBER[3] if i in (0, len(pts) - 1) else EMBER[4])


def frenzied_armor():
    """Frenzied, worn - dusk-violet plates over a dark warm underlayer, grey-silver trims, ember seams glowing between
    the plates. Chest: two pectoral plates either side of a silver ridge with an ember sun at its heart, two abdominal
    bands, ember seams between them. Pauldrons: three layered rounded plates with a silver rim and a curl of silver on
    the outer face. Leggings: a silver belt with an ember buckle, thigh plates, silver knee cops with an ember stud.
    Boots: violet greaves, silver toe caps, a thin ember line. No back piece."""
    c = g.covered_canvas()
    H, L = "humanoid", "humanoid_leggings"
    for layer in (H, L):                                     # the calm underlayer: dark warm violet, darker at the bottom
        for part in ("body", "arm", "leg"):
            for face in ("front", "back", "right", "left", "top", "bottom"):
                F = c.face(layer, part, face)
                for v in range(F[4]):
                    for u in range(F[3]):
                        c.px(F, u, v, DUSK[1] if v < F[4] - 2 else DUSK[0])

    # chest: pectorals either side of a silver ridge, the ember sun, two abdominal bands, seams between
    F = c.face(H, "body", "front")
    c.plate(F, 0, 0, 2, 4, PLATE, 2); c.plate(F, 5, 0, 7, 4, PLATE, 2)
    for v in range(0, 10):                                    # the silver ridge down the middle
        c.px(F, 3, v, SILVER[4] if v % 4 else SILVER[5]); c.px(F, 4, v, SILVER[2])
    c.gem(F, 3, 2, 4, 3, EMBER)                               # the ember sun
    c.px(F, 2, 2, EMBER[3]); c.px(F, 5, 3, EMBER[3])          # its rays, into the plates
    c.plate(F, 0, 6, 2, 7, PLATE, 2); c.plate(F, 5, 6, 7, 7, PLATE, 2)
    c.plate(F, 1, 9, 2, 10, PLATE, 2); c.plate(F, 5, 9, 6, 10, PLATE, 2)
    seam(c, F, [(1, 5), (2, 5)]); seam(c, F, [(5, 5), (6, 5)])   # under the pectorals, either side of the sun
    for u in range(8):
        c.px(F, u, 11, SILVER[3] if u % 2 else SILVER[2])     # the silver hem
    F = c.face(H, "body", "back")
    c.plate(F, 0, 0, 2, 5, PLATE, 2); c.plate(F, 5, 0, 7, 5, PLATE, 2); c.plate(F, 1, 7, 6, 9, PLATE, 2)
    for v in range(0, 11):
        c.px(F, 3, v, SILVER[3]); c.px(F, 4, v, SILVER[2])
    for u in range(8):
        c.px(F, u, 11, SILVER[2])
    for face in ("right", "left"):
        F = c.face(H, "body", face)
        c.plate(F, 0, 0, 3, 4, PLATE, 2); c.plate(F, 0, 6, 3, 9, PLATE, 2)
        seam(c, F, [(0, 5), (1, 5), (2, 5), (3, 5)])
    c.plate(c.face(H, "body", "top"), 0, 0, 7, 3, PLATE, 2)

    # pauldrons: three layered rounded plates, a silver rim, a silver curl on the outer face, seams between the layers
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "arm", face)
        c.plate(F, 0, 0, 3, 1, PLATE, 3); c.plate(F, 0, 2, 3, 3, PLATE, 2); c.plate(F, 0, 4, 3, 4, PLATE, 2)
        c.rect(F, 0, 5, 3, 5, SILVER[3]); c.px(F, 0, 5, SILVER[4])
    for face in ("right", "left"):                            # the curl, mirrored on the two arms
        F = c.face(H, "arm", face)
        for (u, v) in ((1, 1), (2, 1), (2, 2), (1, 3)):
            c.px(F, u if face == "left" else 3 - u, v, SILVER[4])
    F = c.face(H, "arm", "top")
    c.plate(F, 0, 0, 3, 3, PLATE, 3); c.px(F, 1, 1, SILVER[5]); c.px(F, 2, 2, SILVER[3])

    # boots: violet greaves, silver toe caps, an ember line
    for face in ("front", "back", "right", "left"):
        F = c.face(H, "leg", face)
        c.plate(F, 0, 7, 3, 9, PLATE, 2)
        c.rect(F, 0, 10, 3, 11, PLATE[1])
    F = c.face(H, "leg", "front")
    c.plate(F, 0, 10, 3, 11, SILVER, 2)                       # the silver toe cap
    seam(c, F, [(1, 9), (2, 9)])
    c.rect(c.face(H, "leg", "bottom"), 0, 0, 3, 3, PLATE[1])

    # leggings: a silver belt with an ember buckle, thigh plates, silver knee cops with an ember stud
    for face in ("front", "back", "right", "left"):
        F = c.face(L, "body", face)
        for u in range(F[3]):
            c.px(F, u, 8, SILVER[3]); c.px(F, u, 9, SILVER[2])
        G = c.face(L, "leg", face)
        c.plate(G, 0, 0, 3, 3, PLATE, 2)
        c.plate(G, 0, 6, 3, 7, PLATE, 2)
    c.gem(c.face(L, "body", "front"), 3, 8, 4, 9, EMBER)
    F = c.face(L, "leg", "front")
    c.plate(F, 0, 4, 3, 5, SILVER, 2); c.gem(F, 1, 4, 2, 4, EMBER)
    c.plate(c.face(L, "leg", "top"), 0, 0, 3, 3, PLATE, 2)
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


# the horns are shaped like vanilla's warm-cow horns (WarmCowModel, read from the 26.2 client): per side a bar out from
# the side of the head and one block rising at its outer end - two boxes, no staircase. At helm scale (16 units = the
# head) that is a bar 8 out and 4 thick, and a tip block 4 x 5 x 4 standing on its end. The tip burns: a molten amber
# skin glowing toward the top, and a little flame (vanilla's own fire animation) on top of it.
HORN_BAR = (-8.0, 0.0, 10.4, 14.4, 5.0, 9.0)       # x0, x1, y0, y1, z0, z1 (left side; mirrored for the right)
HORN_TIP = (-8.0, -4.0, 14.4, 19.4, 5.0, 9.0)
FLAME = (-7.5, -4.5, 19.4, 22.9, 7.0)               # x0, x1, y0, y1, z centre of the crossed flames


def tip_frames(n=8):
    """The horn tip: grey-silver at its foot turning to molten amber at the top, hot pixels flickering through it."""
    import random
    frames = []
    for f in range(n):
        rnd = random.Random(907 + f)
        img = g.blank()
        for y in range(16):
            for x in range(16):
                heat = (15 - y) / 15                     # 0 at the foot .. 1 at the top
                heat += rnd.uniform(-0.12, 0.12)
                if heat < 0.45:                          # the lower half is still horn
                    c = SILVER[4] if y < 12 else SILVER[3]
                elif heat < 0.55:
                    c = EMBER[1]
                elif heat < 0.7:
                    c = EMBER[2]
                elif heat < 0.85:
                    c = EMBER[3]
                else:
                    c = EMBER[4]
                img.putpixel((x, y), c)
        for _ in range(5):                               # flickering hot spots in the upper half
            img.putpixel((rnd.randrange(16), rnd.randrange(0, 8)), EMBER[5])
        frames.append(img)
    return frames


def vanilla_flame():
    """Vanilla's fire_0 animation (all its frames, its own timing): the flame burning on each horn tip."""
    import json
    meta = json.load(open(os.path.join(g.VANILLA_FIRE, "fire_0.png.mcmeta")))
    strip = Image.open(os.path.join(g.VANILLA_FIRE, "fire_0.png")).convert("RGBA")
    return [strip.crop((0, k * 16, 16, k * 16 + 16)) for k in range(strip.size[1] // 16)], meta


def frenzied_helm_worn():
    """The Frenzied Helm worn - open-faced (the whole face shows): a domed helm of deep violet plate; a heavy silver
    brow ridge bearing down toward the centre, the Frenzy Idol's ember sun set in it (breathing glow); silver cheek
    guards; and two horns shaped like the warm cow's - a smooth grey-silver bar out from each side and a tip block
    rising at its end - the tips burning: molten amber glowing toward the top, a small flame on each."""
    m = Model("frenzied_helmet_head")
    m.part = True
    top_i, side_i, back_i = g.tex_helm(PLATE, tone=3)
    t_top, t_side, t_back = m.texture("helm_top", top_i), m.texture("helm_side", side_i), m.texture("helm_back", back_i)
    t_brow = m.texture("brow", g.tex_smooth(SILVER, tone=3))
    t_horn = m.texture("horn", horn_tex())
    t_tip = m.texture("tip", tip_frames())
    flame_frames, flame_meta = vanilla_flame()
    t_flame = m.texture("flame", flame_frames)
    m.mcmeta["flame"] = flame_meta
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
    # the horns, mirrored: a bar and a burning tip block, with a small flame on top
    mirror = lambda x0, x1, side: (x0, x1) if side < 0 else (16 - x1, 16 - x0)  # noqa: E731
    for side in (-1, 1):
        x0, x1, y0, y1, z0, z1 = HORN_BAR
        a, b = mirror(x0, x1, side)
        m.box((a, y0, z0), (b, y1, z1), {d: (t_horn, [0, 0, 16, 16]) for d in g.FACES_ALL})
        x0, x1, y0, y1, z0, z1 = HORN_TIP
        a, b = mirror(x0, x1, side)
        m.box((a, y0, z0), (b, y1, z1), {d: (t_tip, [0, 0, 16, 16]) for d in g.FACES_ALL}, light=12)
        x0, x1, y0, y1, zc = FLAME
        a, b = mirror(x0, x1, side)
        cx = (a + b) / 2
        for angle in (45, -45):
            el = m.box((a, y0, zc), (b, y1, zc), {"north": (t_flame, [0, 0, 16, 16]), "south": (t_flame, [16, 0, 0, 16])},
                       shade=False, light=15)
            el["rotation"] = {"origin": [cx, y0, zc], "axis": "y", "angle": angle}
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


def helm_gif(helm, path):
    frames = [render3d.render(helm, frame=f, yaw=210, pitch=20, s=9, size=(360, 360), center=(8, 14, 8)).convert("RGB") for f in range(4)]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=220, loop=0)


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    layers = frenzied_armor()
    helm = frenzied_helm_worn()
    suffix = "" if version == "final" else "-" + version
    sheet(layers, helm, os.path.join(OUT, f"review-g8{suffix}.png"))
    helm_gif(helm, os.path.join(OUT, f"helm-g8{suffix}.gif"))
    d = os.path.join(OUT, "equipment", "frenzied")
    os.makedirs(d, exist_ok=True)
    for layer, img in layers.items():
        img.save(os.path.join(d, f"{layer}.png"))
    if version == "final":           # approved: into session-g, where build_pack picks it up
        g.save(helm)
        g.save_armor("frenzied", layers)
    print(os.path.join(OUT, f"review-g8{suffix}.png"))
