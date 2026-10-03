"""A small true-3D preview for blockkit Models: honours element rotations, draws every texel as a quad (painter's
order, back faces culled), orthographic, Minecraft's face shading."""
import math
from PIL import Image, ImageDraw

SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.6, "west": 0.6}


def face_frame(d, f, t):
    """origin corner, u axis vector, v axis vector (full face extents) for a face of box f..t (MC uv conventions)."""
    x0, y0, z0 = f
    x1, y1, z1 = t
    if d == "south":
        return (x0, y1, z1), (x1 - x0, 0, 0), (0, y0 - y1, 0)
    if d == "north":
        return (x1, y1, z0), (x0 - x1, 0, 0), (0, y0 - y1, 0)
    if d == "east":
        return (x1, y1, z1), (0, 0, z0 - z1), (0, y0 - y1, 0)
    if d == "west":
        return (x0, y1, z0), (0, 0, z1 - z0), (0, y0 - y1, 0)
    if d == "up":
        return (x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0)
    return (x0, y0, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1)   # down


NORMAL = {"south": (0, 0, 1), "north": (0, 0, -1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def rot(p, r):
    if not r:
        return p
    o, a = r["origin"], math.radians(r["angle"])
    x, y, z = (p[i] - o[i] for i in range(3))
    c, s = math.cos(a), math.sin(a)
    if r["axis"] == "x":
        y, z = y * c - z * s, y * s + z * c
    elif r["axis"] == "y":
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def rotn(n, r):
    if not r:
        return n
    rr = dict(r, origin=[0, 0, 0])
    return rot(n, rr)


def render(model, frame=0, yaw=30, pitch=30, s=24, size=(600, 600), bg=(34, 32, 40, 255), center=(8, 8, 8)):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def view(p):
        x, y, z = (p[i] - center[i] for i in range(3))
        x, z = x * cy - z * sy, x * sy + z * cy          # yaw about y
        y, z = y * cp - z * sp, y * sp + z * cp          # pitch about x
        return x, y, z                                   # camera looks along -z (toward the viewer is +z)

    quads = []
    for e in model.elements:
        r = e.get("rotation")
        for d, face in e["faces"].items():
            n = view(tuple(a + b for a, b in zip(rotn(NORMAL[d], r), center)))
            n = tuple(n[i] for i in range(3))
            if n[2] <= 1e-6:
                continue
            name = face["texture"].lstrip("#")
            img = model.frame(name, frame).convert("RGBA")
            u0, v0, u1, v1 = face["uv"]
            nu, nv = max(1, math.ceil(abs(u1 - u0) - 1e-6)), max(1, math.ceil(abs(v1 - v0) - 1e-6))
            o, du, dv = face_frame(d, e["from"], e["to"])
            light = 1.0 if (not e.get("shade", True) or e.get("light_emission")) else SHADE[d]
            for i in range(nu):
                for j in range(nv):
                    uu = u0 + (u1 - u0) * (i + 0.5) / nu
                    vv = v0 + (v1 - v0) * (j + 0.5) / nv
                    c = img.getpixel((min(15, int(uu * img.width / 16)), min(img.height - 1, int(vv * img.height / 16))))
                    if c[3] < 128:
                        continue
                    pts = []
                    for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                        p = tuple(o[k] + du[k] * a / nu + dv[k] * b / nv for k in range(3))
                        pts.append(view(rot(p, r)))
                    depth = sum(q[2] for q in pts) / 4
                    col = tuple(int(c[k] * light) for k in range(3)) + (255,)
                    quads.append((depth, [(size[0] / 2 + q[0] * s, size[1] / 2 - q[1] * s) for q in pts], col))
    out = Image.new("RGBA", size, bg)
    dr = ImageDraw.Draw(out)
    for depth, pts, col in sorted(quads, key=lambda q: q[0]):
        dr.polygon(pts, fill=col, outline=col)
    return out
