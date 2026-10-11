"""Boss model builder: cuboids in a bone hierarchy, written as a Generic Blockbench model (BetterModel's format).

Coordinates are Blockbench units (16 = one block), +Y up, the model faces north (-Z), its right side is +X.
Like Blockbench, every position is given in *rest space*: as if no group were rotated. A group rotates its
whole subtree about its origin, so a leg is laid out straight along +X and folded by its joint rotations.
Rotations are degrees [x, y, z], applied X, then Y, then Z (Blockbench's ZYX Euler order).
"""
import json
import math
import uuid as uuidlib

import numpy as np

FACES = ("north", "east", "south", "west", "up", "down")


def _uuid(seed):
    return str(uuidlib.uuid5(uuidlib.NAMESPACE_URL, "occultech/" + seed))


def rotation_matrix(r):
    x, y, z = (math.radians(a) for a in r)
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rz @ ry @ rx


def pivot_matrix(origin, r):
    """4x4: rotate by r about origin."""
    m = np.eye(4)
    m[:3, :3] = rotation_matrix(r)
    o = np.array(origin, float)
    m[:3, 3] = o - m[:3, :3] @ o
    return m


class Group:
    def __init__(self, model, name, origin, rotation=(0, 0, 0), parent=None):
        self.model, self.name, self.parent = model, name, parent
        self.origin, self.rotation = list(map(float, origin)), list(map(float, rotation))
        self.children = []          # Groups and Cubes, in order

    def group(self, name, origin, rotation=(0, 0, 0)):
        g = Group(self.model, name, origin, rotation, self)
        self.children.append(g)
        self.model._register_group(g)
        return g

    def cube(self, name, frm, to, mat, rotation=(0, 0, 0), origin=None, inflate=0.0):
        c = Cube(name, frm, to, mat, rotation, origin, inflate, self)
        self.children.append(c)
        self.model.cubes.append(c)
        return c

    def box(self, name, center, size, mat, rotation=(0, 0, 0), origin=None):
        """Cube by centre and size; rotates about its centre unless origin is given."""
        c = np.array(center, float)
        s = np.array(size, float) / 2
        return self.cube(name, c - s, c + s, mat, rotation, center if origin is None else origin)

    def blob(self, name, center, radii, mat, layers=5):
        """A stepped ellipsoid: slabs stacked along Y unioned with slabs stacked along Z (rounded in every view)."""
        cx, cy, cz = center
        rx, ry, rz = radii
        out = []
        for axis in ("y", "z"):
            r = ry if axis == "y" else rz
            for i in range(layers):
                t0, t1 = -1 + 2 * i / layers, -1 + 2 * (i + 1) / layers
                t = min(abs(t0), abs(t1)) if t0 * t1 > 0 else 0.0
                s = math.sqrt(max(0.0, 1 - t * t))
                lo, hi = t0 * r, t1 * r
                if axis == "y":
                    out.append(self.cube(f"{name}_y{i}", (cx - rx * s, cy + lo, cz - rz * s), (cx + rx * s, cy + hi, cz + rz * s), mat))
                else:
                    out.append(self.cube(f"{name}_z{i}", (cx - rx * s, cy - ry * s, cz + lo), (cx + rx * s, cy + ry * s, cz + hi), mat))
        return out

    def world_matrix(self):
        own = pivot_matrix(self.origin, self.rotation)
        return own if self.parent is None else self.parent.world_matrix() @ own


class Cube:
    def __init__(self, name, frm, to, mat, rotation, origin, inflate, group):
        lo = np.minimum(frm, to).astype(float)
        hi = np.maximum(frm, to).astype(float)
        self.name, self.mat, self.group = name, mat, group
        self.frm, self.to = lo.tolist(), hi.tolist()
        self.rotation = list(map(float, rotation))
        self.origin = list(map(float, origin)) if origin is not None else ((lo + hi) / 2).tolist()
        self.inflate = inflate

    def corners(self):
        """8 world-space corners (Blockbench units)."""
        lo, hi = np.array(self.frm), np.array(self.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        m = self.group.world_matrix() @ pivot_matrix(self.origin, self.rotation)
        return (m @ pts)[:3].T


class Model:
    def __init__(self, name):
        self.name = name
        self.root = Group(self, "root", (0, 0, 0))
        self.groups = []
        self.cubes = []

    def _register_group(self, g):
        if any(o.name == g.name for o in self.groups):
            raise ValueError("duplicate bone name " + g.name)
        self.groups.append(g)

    def group(self, name, origin, rotation=(0, 0, 0)):
        return self.root.group(name, origin, rotation)

    # ---- queries -------------------------------------------------------------------------------------------
    def bounds(self):
        pts = np.vstack([c.corners() for c in self.cubes])
        return pts.min(0), pts.max(0)

    def stats(self):
        lo, hi = self.bounds()
        moving = [g for g in self.groups if any(isinstance(ch, Cube) for ch in g.children)]
        return {"cubes": len(self.cubes), "bones": len(self.groups), "bones_with_geometry": len(moving),
                "size_blocks": [round(float(v) / 16, 2) for v in (hi - lo)],
                "min": [round(float(v), 1) for v in lo], "max": [round(float(v), 1) for v in hi]}

    # ---- export --------------------------------------------------------------------------------------------
    def render_json(self, palette):
        """World-space boxes for the Blender renderer. palette: mat -> (r, g, b) 0..255."""
        out = []
        for c in self.cubes:
            out.append({"name": c.name, "mat": c.mat, "color": [v / 255 for v in palette[c.mat][:3]],
                        "corners": c.corners().tolist()})
        return out

    def to_bbmodel(self, texture_size=(64, 64), textures=()):
        elements, uuids = [], {}
        for i, c in enumerate(self.cubes):
            u = _uuid(f"{self.name}/cube/{i}/{c.name}")
            uuids[id(c)] = u
            faces = {f: {"uv": [0, 0, 1, 1], "texture": 0 if textures else None} for f in FACES}
            elements.append({
                "name": c.name, "box_uv": False, "rescale": False, "locked": False, "light_emission": 0,
                "render_order": "default", "allow_mirror_modeling": True,
                "from": c.frm, "to": c.to, "autouv": 0, "color": _COLOR_INDEX.get(c.mat, 0),
                "inflate": c.inflate, "rotation": c.rotation, "origin": c.origin,
                "faces": faces, "type": "cube", "uuid": u,
            })

        def outline(g):
            node = {"name": g.name, "origin": g.origin, "rotation": g.rotation, "color": 0,
                    "uuid": _uuid(f"{self.name}/group/{g.name}"), "export": True, "mirror_uv": False,
                    "isOpen": False, "locked": False, "visibility": True, "autouv": 0, "children": []}
            for ch in g.children:
                node["children"].append(uuids[id(ch)] if isinstance(ch, Cube) else outline(ch))
            return node

        outliner = [outline(g) for g in self.root.children if isinstance(g, Group)]
        outliner += [uuids[id(c)] for c in self.root.children if isinstance(c, Cube)]
        groups = []
        for g in self.groups:
            groups.append({"name": g.name, "origin": g.origin, "rotation": g.rotation, "color": 0,
                           "uuid": _uuid(f"{self.name}/group/{g.name}"), "export": True, "mirror_uv": False,
                           "isOpen": False, "locked": False, "visibility": True, "autouv": 0})
        return {
            "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": self.name, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
            "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
            "resolution": {"width": texture_size[0], "height": texture_size[1]},
            "elements": elements, "groups": groups, "outliner": outliner,
            "textures": list(textures), "animations": [],
        }

    def write_bbmodel(self, path, **kw):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_bbmodel(**kw), f, indent=1)


def add_hitbox(bb, frm, to, name="ob_hitbox"):
    """Adds BetterModel's hitbox bone to a finished .bbmodel dict: one untextured box, never drawn in game.

    BetterModel turns an `ob_` bone into an invisible hitbox entity that follows the model and passes every hit on to the
    boss (with the attacker kept, so Occultech's contribution and arena rules still apply). Sizes are model units.
    """
    seed = f"{bb['name']}/hitbox"
    cube = _uuid(seed + "/cube")
    bb["elements"].append({
        "name": "hitbox", "box_uv": False, "rescale": False, "locked": False, "light_emission": 0,
        "render_order": "default", "allow_mirror_modeling": True, "from": list(frm), "to": list(to), "autouv": 0,
        "color": 8, "inflate": 0.0, "rotation": [0, 0, 0], "origin": [0, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES}, "type": "cube", "uuid": cube,
    })
    group = {"name": name, "origin": [0, 0, 0], "rotation": [0, 0, 0], "color": 0, "uuid": _uuid(seed + "/group"),
             "export": True, "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0}
    bb["groups"].append(dict(group))
    bb["outliner"].append(dict(group, children=[cube]))
    return bb


# Blockbench's cube marker colours, so materials are told apart in the editor before texturing
_COLOR_INDEX = {"chitin": 0, "bone": 1, "silk": 2, "glow": 3, "iron": 4, "wax": 5, "chalk": 6, "flesh": 7}


# ---- helpers for creatures -------------------------------------------------------------------------------------

def leg(parent, name, hip, yaw, segments, ground=0.0, joint_scale=1.2, mat="chitin", knuckle_mat=None, bristles=0,
        bristle_mat="chitin_lit"):
    """A jointed leg laid along +X from hip, yawed about Y, each segment pitched about Z.

    segments: [(length, absolute_pitch_deg, thickness), ...]; positive pitch rises. If the last length is None it is
    solved so the foot touches `ground`. Returns the list of joint groups (hip yaw bone first).
    """
    hip = np.array(hip, float)
    segs = list(segments)
    if segs[-1][0] is None:
        y = hip[1]
        for length, pitch, _ in segs[:-1]:
            y += length * math.sin(math.radians(pitch))
        pitch = segs[-1][1]
        segs[-1] = (max(2.0, (y - ground) / -math.sin(math.radians(pitch))), pitch, segs[-1][2])
    bones = [parent.group(f"{name}_hip", hip, (0, yaw, 0))]
    x, prev = hip[0], 0.0
    cur = bones[0]
    for i, (length, pitch, t) in enumerate(segs):
        cur = cur.group(f"{name}_{i}", (x, hip[1], hip[2]), (0, 0, pitch - prev))
        bones.append(cur)
        cur.cube(f"{name}_{i}", (x - t * 0.15, hip[1] - t / 2, hip[2] - t / 2), (x + length, hip[1] + t / 2, hip[2] + t / 2), mat)
        k = t * joint_scale
        cur.cube(f"{name}_{i}_joint", (x - k / 2, hip[1] - k / 2, hip[2] - k / 2), (x + k / 2, hip[1] + k / 2, hip[2] + k / 2),
                 knuckle_mat or mat)
        for b in range(bristles if i < len(segs) - 1 else 0):
            bx = x + length * (b + 1) / (bristles + 1)
            side = 1 if b % 2 else -1
            cur.cube(f"{name}_{i}_hair{b}", (bx - 0.6, hip[1] + t / 2 - 0.2, hip[2] + side * t * 0.25 - 0.6),
                     (bx + 0.6, hip[1] + t / 2 + 2.2, hip[2] + side * t * 0.25 + 0.6), bristle_mat, rotation=(0, 0, -25),
                     origin=(bx, hip[1] + t / 2, hip[2]))
        x += length
        prev = pitch
    return bones
