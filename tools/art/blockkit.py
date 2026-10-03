"""Block kit: build Minecraft block models (elements of boxes with textured faces) and preview them in 3D.

A Model is a set of named textures (16x16 images, or lists of frames for animated ones) and elements - axis-aligned
boxes in block units (0..16), each face pointing at a texture and a uv rectangle. The same data is
  * written out as the model JSON the resource pack needs (`Model.to_json`), and
  * drawn by a tiny isometric renderer (`render_iso`) the way the inventory shows a block - top lit, the two visible
    sides shaded - so every block can be reviewed in 3D before it goes in game.

Skins: a placed Occultech block keeps its vanilla block; an item display shows our model over it, slightly larger, so
the vanilla block is hidden. A skin must therefore enclose the vanilla block's shape (see `docs/art/SESSIONS.md`, G1).
"""
import math

from PIL import Image, ImageDraw

FACES = ("down", "up", "north", "south", "west", "east")


class Model:
    def __init__(self, key):
        self.key = key              # e.g. "initiate_altar" -> occultech:block/initiate_altar
        self.textures = {}          # name -> Image (16x16) or [Image, ...] (animated, frames)
        self.elements = []
        self.display = None         # optional display transforms (e.g. a tall model's inventory scale)
        self.part = False           # a part shown by the plugin (not a block skin): build_pack skips the skins list
        self.mcmeta = {}            # texture name -> its .png.mcmeta (default: build_pack's frametime)
        self.extra = {}             # other top-level model fields (e.g. gui_light)

    def texture(self, name, img_or_frames):
        self.textures[name] = img_or_frames
        return "#" + name

    def box(self, frm, to, faces, shade=True, light=0, rotation=None):
        """faces: {direction: texture ref or (texture ref, uv)}; directions not given are left out (not drawn).
        Without an explicit uv a face uses the matching area of its texture (Minecraft's default).
        light: the element's light_emission (0-15) - it glows in the dark. rotation: (axis, angle) about the box's
        centre, angle a multiple of 22.5 in -45..45 (the preview draws it unrotated)."""
        el = {"from": list(frm), "to": list(to), "faces": {}, "shade": shade}
        if light:
            el["light_emission"] = light
        if rotation:
            el["rotation"] = {"origin": [(a + b) / 2 for a, b in zip(frm, to)], "axis": rotation[0], "angle": rotation[1]}
        for direction, spec in faces.items():
            ref, uv = (spec, None) if isinstance(spec, str) else spec
            el["faces"][direction] = {"texture": ref, "uv": list(uv) if uv else default_uv(direction, frm, to)}
        self.elements.append(el)
        return el

    def cube(self, frm, to, side, top=None, bottom=None):
        """A box with the same texture on its four sides (and its own top/bottom)."""
        faces = {d: side for d in ("north", "south", "west", "east")}
        faces["up"] = top or side
        faces["down"] = bottom or side
        return self.box(frm, to, faces)

    def frame(self, name, i):
        t = self.textures[name]
        return t[i % len(t)] if isinstance(t, list) else t

    def to_json(self, ns="occultech"):
        textures = {name: f"{ns}:block/{self.key}_{name}" for name in self.textures}
        textures["particle"] = textures[next(iter(self.textures))]
        elements = []
        for e in self.elements:
            out = {"from": e["from"], "to": e["to"], "shade": e["shade"]}
            for extra in ("light_emission", "rotation"):
                if extra in e:
                    out[extra] = e[extra]
            out["faces"] = {d: {"texture": f["texture"], "uv": f["uv"], **({"tintindex": f["tintindex"]} if "tintindex" in f else {})}
                            for d, f in e["faces"].items()}
            elements.append(out)
        model = {"parent": "minecraft:block/block", "textures": textures, "elements": elements}
        model.update(self.extra)
        if self.display:
            model["display"] = self.display
        return model


def default_uv(direction, frm, to):
    """Minecraft's automatic uv: the face's own area of the 16x16 texture."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    if direction in ("up", "down"):
        return [x0, z0, x1, z1]
    if direction in ("north", "south"):
        return [x0, 16 - y1, x1, 16 - y0]
    return [z0, 16 - y1, z1, 16 - y0]


# ------------------------------------------------------------------ the isometric preview renderer

SHADE = {"up": 1.0, "south": 0.8, "east": 0.62}   # as the inventory lights a block: top, left side, right side
COS30, SIN30 = math.cos(math.radians(30)), 0.5


def project(x, y, z, s, ox, oy):
    """Block units to screen: x goes right-down, z goes left-down, y goes up."""
    return (ox + (x - z) * COS30 * s, oy + (x + z) * SIN30 * s - y * s)


def render_iso(model, frame=0, s=6, size=None, bg=(34, 32, 40, 255), lift=0.0):
    """Draw the model's visible faces (up, south, east) texel by texel, far elements first. lift moves the view down
    (a fraction of the height) for tall models."""
    w = size or int(32 * COS30 * s + 40)
    h = size or int(40 * s)
    img = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(img)
    ox, oy = w / 2, h * (0.42 + lift)
    order = sorted(model.elements, key=lambda e: (e["from"][0] + e["to"][0]) + (e["from"][2] + e["to"][2])
                   + 0.5 * (e["from"][1] + e["to"][1]))
    for e in order:
        (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
        for direction in ("up", "south", "east"):
            f = e["faces"].get(direction)
            if not f:
                continue
            tex = model.frame(f["texture"][1:], frame)
            u0, v0, u1, v1 = f["uv"]
            if direction == "up":
                quad = lambda a, b: (x0 + a * (x1 - x0), y1, z0 + b * (z1 - z0))  # noqa: E731
            elif direction == "south":
                quad = lambda a, b: (x0 + a * (x1 - x0), y1 - b * (y1 - y0), z1)  # noqa: E731
            else:
                quad = lambda a, b: (x1, y1 - b * (y1 - y0), z1 - a * (z1 - z0))  # noqa: E731
            ku, kv = tex.size[0] / 16, tex.size[1] / 16   # texels per uv unit (a 64 px texture has 4)
            nu, nv = max(1, round(abs(u1 - u0) * ku)), max(1, round(abs(v1 - v0) * kv))
            for j in range(nv):
                for i in range(nu):
                    tu = int(min(u0, u1) * ku + (i if u1 >= u0 else nu - 1 - i))
                    tv = int(min(v0, v1) * kv + (j if v1 >= v0 else nv - 1 - j))
                    c = tex.getpixel((min(tex.size[0] - 1, tu), min(tex.size[1] - 1, tv)))
                    if c[3] < 8:
                        continue
                    k = SHADE[direction] if e.get("shade", True) else 1.0
                    col = (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255)
                    pts = [project(*quad(a / nu, b / nv), s, ox, oy) for a, b in
                           ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                    d.polygon(pts, fill=col)
    return img


def review(models, path, frames=1, s=6):
    """A sheet: each model in 3D (frame 0), plus its frames if animated."""
    cell = render_iso(models[0][1], 0, s)
    cw, ch = cell.size
    out = Image.new("RGBA", (180 + cw * max(1, frames), ch * len(models)), (34, 32, 40, 255))
    d = ImageDraw.Draw(out)
    for r, (name, m) in enumerate(models):
        d.text((8, r * ch + ch // 2), name, fill=(230, 230, 240, 255))
        for f in range(max(1, frames)):
            out.alpha_composite(render_iso(m, f, s), (180 + f * cw, r * ch))
    out.save(path)
    return path
