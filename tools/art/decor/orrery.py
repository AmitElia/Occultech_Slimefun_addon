"""The Orrery: a standalone decoration (MythicMobs + BetterModel, nothing else). A sun the size of a block, with the
eight planets on Kepler orbits around it inside a 9x9 area, Earth's moon, a comet now and then and shooting stars.

Like the mounts (tools/art/mounts/), it is a mob wearing a BetterModel model; the Mythic pack (decor/orrery/MythicMobs)
places it with a spawn egg and plays the clips. This script writes the model and its clips:
- the sun: two flat discs (the disc and its corona) on one bone at the model's origin, billboarded by the skills so
  they always face the viewer. Only a bone at the origin can be billboarded: the client turns a billboarded display's
  whole transformation to the camera, offsets included (DisplayRenderer.submit: orientation, then transformation),
- the planets: little round bodies (stacked octagon slices, round from every side), each on its own bone, all in one
  looping clip (idle). The orbits are ellipses with the sun at a focus; the positions come from Kepler's equation,
  so a planet speeds up near the sun, and the periods follow Kepler's third law (T ~ a^1.5) on the model's own
  distances (squeezed from the real ones to fit 4.5 blocks),
- the moon on a bone inside Earth's, Saturn's ring tilted on Saturn's bone,
- a comet on a long thin orbit, its tail always pointing away from the sun (the comet sits on an arm turning about the
  sun, its tail along the arm), played as one pass now and then (model orrery_comet),
- six shooting stars, each a streak flying along its own arm, played at random (model orrery_meteors).
The three are separate models because BetterModel plays one clip per model at a time.

Writes decor/orrery/BetterModel/models/orrery*.bbmodel and the zip dist/orrery.zip (decor/orrery/ as it lands in
plugins/). Run from the repository root: python tools/art/decor/orrery.py
"""
import base64
import io
import json
import math
import random
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, _uuid, add_hitbox  # noqa: E402

MODEL_ID = "orrery"
PACK = ROOT / "decor/orrery"
ZIP = ROOT / "dist/orrery.zip"
PREVIEW = ROOT / "docs/art/decor/orrery"

U = 16                      # model units per block
TEX = 128                   # the atlas is TEX x TEX
FLIP_X = True               # BetterModel reads position keyframes with x mirrored (measured in game: meteors flew backwards)

SUN_R = 0.62                # the sun disc's radius (blocks): the placed block is its core
HALO_R = 0.95
MERCURY_T = 3.2             # seconds; every other period follows from T ~ a^1.5
LOOP = 240                  # the orbit clip's length (s): each period is rounded to a whole number of turns in it

# name, a (semi-major axis, blocks), e, body radius, perihelion longitude (deg), inclination (deg), start phase (deg)
PLANETS = [
    ("mercury", 0.95, 0.28, 0.07, 20, 3.0, 0),
    ("venus", 1.40, 0.12, 0.11, 140, 1.5, 200),
    ("earth", 1.85, 0.13, 0.12, 250, 0.0, 95),
    ("mars", 2.35, 0.11, 0.09, 330, 1.8, 290),
    ("jupiter", 2.95, 0.09, 0.24, 75, 1.2, 40),
    ("saturn", 3.50, 0.07, 0.19, 190, 2.2, 160),
    ("uranus", 3.98, 0.05, 0.14, 300, 0.8, 250),
    ("neptune", 4.30, 0.03, 0.14, 45, 1.6, 330),
]
MOON = (0.30, 0.045, 1.4)                    # orbit radius about Earth, body radius, period (s)
RING = (0.24, 0.40, (24.0, 0.0, 12.0))       # inner, outer radius, tilt
COMET = (2.45, 0.75, 0.085, 230.0)           # a, e, head radius, perihelion longitude
METEORS = 6


def period(a):
    return round(MERCURY_T * (a / PLANETS[0][1]) ** 1.5, 1)


def kepler(M, e):
    E = M
    for _ in range(12):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    return E


# ---- textures --------------------------------------------------------------------------------------------------------
# Atlas regions (x0, y0, x1, y1) in pixels
REG = {
    "sun": (0, 0, 64, 64), "halo": (64, 0, 128, 64), "ring": (0, 64, 32, 96),
    "tail": (32, 64, 64, 72), "streak": (32, 72, 64, 80), "tail_end": (64, 64, 68, 68),
    "tail_glow": (32, 80, 64, 88),
    "mercury": (0, 96, 16, 112), "venus": (16, 96, 32, 112), "earth": (32, 96, 48, 112), "mars": (48, 96, 64, 112),
    "jupiter": (64, 96, 80, 112), "saturn": (80, 96, 96, 112), "uranus": (96, 96, 112, 112),
    "neptune": (112, 96, 128, 112), "moon": (0, 112, 16, 128), "comet": (16, 112, 32, 128),
    "meteor": (32, 112, 48, 128),
}


def noise(h, w, scale, rng):
    """Smooth value noise in 0..1."""
    gh, gw = h // scale + 2, w // scale + 2
    g = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / scale
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[y0, x0], g[y0, x0 + 1]
    c, d = g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def lerp(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(c0, float) * (1 - t) + np.array(c1, float) * t


def ramp(stops, t):
    """stops: [(t, rgb)...] ascending."""
    out = np.zeros(t.shape + (3,))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        out[m] = lerp(c0, c1, (t[m] - t0) / (t1 - t0))
    out[t < stops[0][0]] = stops[0][1]
    out[t > stops[-1][0]] = stops[-1][1]
    return out


def sun_tex(rng):
    n = 64
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5 - n / 2) / (n / 2)
    r = np.hypot(xs, ys)
    gran = noise(n, n, 3, rng) * 0.6 + noise(n, n, 7, rng) * 0.4
    col = ramp([(0, (255, 250, 214)), (0.45, (255, 214, 92)), (0.8, (255, 160, 40)), (1, (232, 96, 22))],
               r + (gran - 0.5) * 0.22)
    # two sunspots
    for cx, cy, s in ((0.32, -0.18, 0.09), (-0.22, 0.36, 0.06)):
        d = np.hypot(xs - cx, ys - cy) / s
        col = lerp(col, (150, 60, 16), np.clip(1.4 - d, 0, 1) * 0.8)
    alpha = np.clip((1 - r) * n / 2 + 0.5, 0, 1) * 255
    return np.dstack([col, alpha])


def halo_tex(rng):
    n = 64
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5 - n / 2) / (n / 2)
    r = np.hypot(xs, ys)
    ang = np.arctan2(ys, xs)
    inner = SUN_R / HALO_R
    rays = 0.55 + 0.45 * np.abs(np.sin(ang * 6 + 0.3 * np.sin(ang * 3))) ** 3
    fall = np.clip((1 - r) / (1 - inner), 0, 1) ** 1.6
    a = fall * (0.35 + 0.65 * rays) * (r > inner - 0.04)
    a *= 0.85 + 0.15 * noise(n, n, 4, rng)
    col = lerp((255, 120, 30), (255, 214, 110), fall)
    return np.dstack([col, np.clip(a, 0, 1) * 200])


def ring_tex(rng):
    n = 32
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5 - n / 2) / (n / 2)
    r = np.hypot(xs, ys)
    lo = RING[0] / RING[1]
    t = (r - lo) / (1 - lo)
    bands = 0.6 + 0.4 * np.sin(t * 19) * np.sin(t * 7 + 1)
    col = ramp([(0, (196, 170, 120)), (0.5, (236, 216, 168)), (1, (170, 146, 104))], t)
    a = ((t >= 0) & (t <= 1)) * (0.45 + 0.5 * bands)
    a[(t > 0.62) & (t < 0.68)] *= 0.15        # the Cassini division
    return np.dstack([col, np.clip(a, 0, 1) * 255])


def gradient_tex(w, h, c0, c1, a0, a1):
    t = np.linspace(0, 1, w)[None, :].repeat(h, 0)
    edge = 1 - np.abs(np.linspace(-1, 1, h))[:, None] ** 2
    col = lerp(c0, c1, t)
    a = (a0 + (a1 - a0) * t) * (0.5 + 0.5 * edge)
    return np.dstack([col, np.clip(a, 0, 1) * 255])


def body_tex(kind, rng):
    n = 16
    ys, xs = np.mgrid[0:n, 0:n] / n
    nz = noise(n, n, 4, rng)
    fine = noise(n, n, 2, rng)
    if kind == "mercury":
        col = lerp((120, 116, 110), (176, 170, 160), nz)
        for _ in range(5):
            cx, cy = rng.random(2)
            d = np.hypot(xs - cx, ys - cy)
            col = lerp(col, (88, 84, 80), (d < 0.09) * 0.7)
    elif kind == "venus":
        col = ramp([(0, (206, 160, 92)), (0.5, (236, 206, 140)), (1, (250, 232, 186))],
                   np.sin((ys + nz * 0.4) * 9) * 0.5 + 0.5)
    elif kind == "earth":
        land = noise(n, n, 5, rng) * 0.7 + fine * 0.3
        col = np.where((land > 0.55)[..., None], lerp((70, 140, 60), (150, 130, 80), fine), lerp((24, 70, 170), (50, 120, 210), nz))
        cloud = noise(n, n, 3, rng)
        col = lerp(col, (245, 248, 252), np.clip((cloud - 0.62) * 3, 0, 0.85))
        col = lerp(col, (240, 246, 250), ((ys < 0.1) | (ys > 0.9)) * 0.9)
    elif kind == "mars":
        col = lerp((176, 74, 36), (222, 120, 66), nz)
        col = lerp(col, (110, 46, 26), np.clip((fine - 0.6) * 3, 0, 0.7))
        col = lerp(col, (240, 236, 230), (ys < 0.08) * 0.9)
    elif kind == "jupiter":
        band = np.sin((ys + (nz - 0.5) * 0.08) * math.pi * 7)
        col = ramp([(-1, (150, 96, 60)), (0, (214, 176, 128)), (1, (244, 228, 200))], band)
        d = np.hypot((xs - 0.65) / 1.6, ys - 0.66)
        col = lerp(col, (196, 82, 52), (d < 0.07) * 0.9)
    elif kind == "saturn":
        band = np.sin((ys + (nz - 0.5) * 0.05) * math.pi * 5)
        col = ramp([(-1, (196, 168, 112)), (1, (240, 222, 170))], band)
    elif kind == "uranus":
        col = lerp((132, 206, 214), (176, 230, 232), ys * 0.5 + nz * 0.5)
    elif kind == "neptune":
        col = lerp((44, 76, 190), (78, 118, 226), nz)
        col = lerp(col, (180, 200, 250), (np.abs(ys - 0.35 - (xs - 0.5) * 0.1) < 0.04) * 0.7)
    elif kind == "moon":
        col = lerp((150, 150, 148), (206, 206, 202), nz)
    elif kind == "comet":
        col = lerp((210, 236, 255), (255, 255, 255), nz)
    else:  # meteor
        col = lerp((255, 214, 150), (255, 252, 236), nz)
    # a little shading noise everywhere
    col = col * (0.92 + 0.16 * fine[..., None])
    return np.dstack([np.clip(col, 0, 255), np.full((n, n), 255.0)])


def build_atlas():
    rng = np.random.default_rng(7)
    atlas = np.zeros((TEX, TEX, 4))

    def put(name, img):
        x0, y0, x1, y1 = REG[name]
        atlas[y0:y1, x0:x1] = img
    put("sun", sun_tex(rng))
    put("halo", halo_tex(rng))
    put("ring", ring_tex(rng))
    put("tail", gradient_tex(32, 8, (255, 255, 255), (150, 200, 255), 0.9, 0.0))
    put("tail_glow", gradient_tex(32, 8, (190, 225, 255), (90, 150, 255), 0.45, 0.0))
    put("streak", gradient_tex(32, 8, (255, 248, 220), (255, 160, 70), 1.0, 0.0))
    put("tail_end", np.dstack([np.full((4, 4, 3), 235.0), np.full((4, 4), 30.0)]))
    for k in ("mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune", "moon", "comet", "meteor"):
        put(k, body_tex(k, rng))
    return Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), "RGBA")


# ---- geometry --------------------------------------------------------------------------------------------------------

def ball(g, name, r_blocks, mat):
    """A round body: horizontal slices, each a regular octagon (four boxes turned 0, 45, 90 and 135 degrees, half
    length = the octagon's apothem, half width = apothem * tan 22.5), the slices' widths following the sphere. From
    the side the outline is a stepped circle, from above an octagon. Each slice's sides carry its own latitude band
    of the texture, so the bands run on across slices. The four boxes of a slice end a hair apart in height, so their
    tops and bottoms never share a plane."""
    r = r_blocks * U
    layers = 7 if r_blocks >= 0.15 else 5
    x0, y0, x1, y1 = REG[mat]
    for i in range(layers):
        lo, hi = -r + 2 * r * i / layers, -r + 2 * r * (i + 1) / layers
        t = (lo + hi) / 2 / r
        rho = r * math.sqrt(1 - t * t) * 1.02
        band = (x0, y1 - (y1 - y0) * (i + 1) / layers, x1, y1 - (y1 - y0) * i / layers)
        cap = (x0 + 4, y0 + 4, x1 - 4, y1 - 4)
        for k, turn in enumerate((0, 45, 90, 135)):
            d = 0.02 * k
            c = g.cube(f"{name}_{i}_{k}", (-rho, lo - d, -rho * 0.4142), (rho, hi + d, rho * 0.4142), mat,
                       rotation=(0, turn, 0), origin=(0, 0, 0))
            c.faces = {f: band for f in ("north", "east", "south", "west")}
            c.faces.update(up=cap, down=cap)


def flat(g, name, half, mat, z=0.0, plane="xy"):
    """A zero-thickness square textured on both sides (xy: facing z; xz: facing up)."""
    if plane == "xy":
        c = g.cube(name, (-half, -half, z), (half, half, z), mat)
        c.faces = {"north": REG[mat], "south": REG[mat]}
    else:
        c = g.cube(name, (-half, z, -half), (half, z, half), mat)
        c.faces = {"up": REG[mat], "down": REG[mat]}
    return c


def tail(g, name, length, w0, w1, segments, mat):
    """A comet's tail from the bone's origin out along +x: segments narrowing from w0 to w1, each a box whose long
    faces carry its own stretch of the gradient (bright and opaque at the head, gone at the end). No end faces: an
    end cap would show as a solid square."""
    u0, v0, u1, v1 = REG[mat]
    for i in range(segments):
        a, b = i / segments, (i + 1) / segments
        w = (w0 + (w1 - w0) * a) / 2
        c = g.cube(f"{name}_{i}", (length * a, -w, -w), (length * b, w, w), mat)
        ua, ub = u0 + (u1 - u0) * a, u0 + (u1 - u0) * b
        # north is drawn with u running along -x, the others along +x: flip it so every side fades the same way
        c.faces = {"south": (ua, v0, ub, v1), "up": (ua, v0, ub, v1), "down": (ua, v0, ub, v1),
                   "north": (ub, v0, ua, v1)}


def euler_for(d):
    """Blockbench rotation [x, y, z] (degrees) that turns +x onto the unit vector d (Rz Ry Rx order)."""
    dx, dy, dz = d
    yaw = math.asin(max(-1.0, min(1.0, -dz)))
    pitch = math.atan2(dy, dx) if abs(math.cos(yaw)) > 1e-6 else 0.0
    return [0.0, math.degrees(yaw), math.degrees(pitch)]


def meteor_paths():
    rng = random.Random(11)
    paths = []
    for k in range(METEORS):
        phi = 2 * math.pi * (k + rng.random() * 0.6) / METEORS
        start = np.array([math.cos(phi) * 4.4, 1.6 + rng.random() * 1.2, math.sin(phi) * 4.4])
        miss = (1.4 + rng.random() * 1.6) * (1 if k % 2 else -1)     # passes this far from the sun
        across = np.array([-math.sin(phi), 0, math.cos(phi)])
        end = np.array([-math.cos(phi) * 3.6, -0.2 - rng.random() * 0.5, -math.sin(phi) * 3.6]) + across * miss
        d = end - start
        length = float(np.linalg.norm(d))
        paths.append((start, d / length, length, 0.6 + rng.random() * 0.3))
    return paths


def finish(m, clips_fn, hitbox=False):
    """The .bbmodel: each cube's own UV regions (to_bbmodel writes placeholders), the hitbox, the clips."""
    bb = m.to_bbmodel(texture_size=(TEX, TEX), textures=[texture_entry(m.name)])
    for el, cube in zip(bb["elements"], m.cubes):
        faces = getattr(cube, "faces", {})
        el["faces"] = {f: ({"uv": list(faces[f]), "texture": 0} if f in faces else {"uv": [0, 0, 0, 0], "texture": None})
                       for f in ("north", "east", "south", "west", "up", "down")}
    if hitbox:
        add_hitbox(bb, (-8, -8, -8), (8, 8, 8))
    bb["model_identifier"] = m.name
    bb["animations"] = clips_fn({g["name"]: g["uuid"] for g in bb["groups"]})
    return bb


def build_orrery():
    """The sun and the planets, with the click box (the sun's core, one block)."""
    m = Model(MODEL_ID)
    sun = m.group("sun", (0, 0, 0))
    flat(sun, "sun_disc", SUN_R * U, "sun", 0.0)
    flat(sun, "sun_halo", HALO_R * U, "halo", -0.05)
    bodies = {}
    for name, a, e, rad, *_ in PLANETS:
        g = m.group(name, (0, 0, 0))
        ball(g, name, rad, name)
        bodies[name] = g
    ring = bodies["saturn"].group("saturn_ring", (0, 0, 0), RING[2])
    flat(ring, "ring", RING[1] * U, "ring", 0.0, plane="xz")
    moon = bodies["earth"].group("moon", (0, 0, 0))
    ball(moon, "moon", MOON[1], "moon")
    return m, finish(m, lambda u: [orbits_clip(u)], hitbox=True)


def build_comet():
    m = Model(MODEL_ID + "_comet")
    arm = m.group("comet_arm", (0, 0, 0))
    comet = arm.group("comet", (0, 0, 0))
    ball(comet, "comet_head", COMET[2], "comet")
    tail_bone = comet.group("comet_tail", (0, 0, 0))
    tail(tail_bone, "tail_core", 1.5 * U, 0.08 * U, 0.03 * U, 4, "tail")
    tail(tail_bone, "tail_glow", 1.1 * U, 0.2 * U, 0.06 * U, 4, "tail_glow")
    return m, finish(m, lambda u: [comet_clip(u)])


def build_meteors():
    m = Model(MODEL_ID + "_meteors")
    paths = meteor_paths()
    for k, (start, d, length, dur) in enumerate(paths, 1):
        arm_k = m.group(f"meteor_arm_{k}", (start * U).tolist(), euler_for(d))
        met = arm_k.group(f"meteor_{k}", (start * U).tolist())
        c = met.box(f"meteor_{k}_head", (start * U).tolist(), [0.07 * U] * 3, "meteor")
        c.faces = {f: REG["meteor"] for f in ("north", "east", "south", "west", "up", "down")}
        sub_streak(met, f"meteor_{k}", start * U)
    return m, finish(m, lambda u: [meteor_clip(k, length, dur, u) for k, (_, _, length, dur) in enumerate(paths, 1)])


def sub_streak(g, name, origin):
    """A meteor's trail: beams from the head back along the arm's -x (rest space: the arm's rotation turns them)."""
    x, y, z = origin
    for part, length, width in (("core", 0.9, 0.035), ("glow", 0.6, 0.08)):
        w = width * U / 2
        c = g.cube(f"{name}_{part}", (x - length * U, y - w, z - w), (x, y + w, z + w), "streak")
        u0, v0, u1, v1 = REG["streak"]
        fwd, back = (u1, v0, u0, v1), (u0, v0, u1, v1)       # bright end at the head (+x)
        c.faces = {"south": fwd, "up": fwd, "down": fwd, "north": back,
                   "east": REG["meteor"], "west": REG["tail_end"]}


def texture_entry(model):
    buf = io.BytesIO()
    build_atlas().save(buf, "PNG")
    return {
        "name": f"{model}.png", "relative_path": f"{model}.png", "folder": "", "namespace": "", "id": "0",
        "group": "", "scope": 0, "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
        "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
        "render_mode": "default", "render_sides": "auto", "wrap_mode": "limited", "pbr_channel": "color", "fps": 7,
        "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
        "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
        "uuid": _uuid(f"{model}/texture"),
        "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
    }


# ---- clips -----------------------------------------------------------------------------------------------------------

def key(clip, bone, channel, t, v, interp="linear"):
    return {"channel": channel, "data_points": [{"x": str(round(v[0], 4)), "y": str(round(v[1], 4)),
                                                  "z": str(round(v[2], 4))}],
            "time": round(t, 4), "color": -1, "interpolation": interp,
            "uuid": _uuid(f"{MODEL_ID}/{clip}/{bone}/{channel}/{round(t, 4)}")}


def clip(name, length, loop, tracks, uuids):
    animators = {uuids[b]: {"name": b, "type": "bone", "keyframes": frames} for b, frames in tracks.items()}
    return {"uuid": _uuid(f"{MODEL_ID}/anim/{name}"), "name": name, "loop": loop, "override": False,
            "length": round(length, 4), "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
            "start_delay": "", "loop_delay": "", "animators": animators}


def px(x):
    return -x if FLIP_X else x


def orbit_point(a, e, w, inc, M):
    """Heliocentric position (blocks) at mean anomaly M on an ellipse with the sun at a focus."""
    E = kepler(M, e)
    x, z = a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    cw, sw = math.cos(w), math.sin(w)
    X, Z = x * cw - z * sw, x * sw + z * cw
    r, th = math.hypot(X, Z), math.atan2(Z, X)
    return X, r * math.sin(inc) * math.sin(th - w), Z


def loop_period(T):
    """T rounded so the body goes round a whole number of times in one LOOP."""
    n = max(1, round(LOOP / T))
    return LOOP / n, n


def orbit_keys(bone, a, e, w, inc, phase, per_orbit):
    T, n = loop_period(period(a))
    keys = []
    steps = per_orbit * n
    for i in range(steps + 1):
        M = math.radians(phase) + 2 * math.pi * i / per_orbit
        X, Y, Z = orbit_point(a, e, math.radians(w), math.radians(inc), M)
        keys.append(key("orbits", bone, "position", LOOP * i / steps, (px(X * U), Y * U, Z * U), "catmullrom"))
    return keys


def orbits_clip(uuids):
    """Every body of the main model in ONE looping clip: BetterModel lets one clip at a time drive a model (a clip
    started later takes every bone, even those it doesn't animate), so the orbits can't be clips of their own. The
    clip lasts LOOP seconds and each period is rounded so its body goes round a whole number of times in it. It is
    named idle, BetterModel's own name for the clip it plays by itself while the mob stands still (always, for this
    stand): BetterModel rebuilds a model when its mob loads (restart, chunk), after the mob's load skills ran, so a
    clip started by a skill would stop there; idle starts again by itself."""
    tracks = {}
    for i, (name, a, e, rad, w, inc, phase) in enumerate(PLANETS):
        tracks[name] = orbit_keys(name, a, e, w, inc, phase, 24 + 4 * i)
    # the moon: circular, about Earth (in Earth's bone)
    r, _, T = MOON
    T, n = loop_period(T)
    steps = 10 * n
    tracks["moon"] = [key("orbits", "moon", "position", LOOP * i / steps,
                          (px(r * U * math.cos(2 * math.pi * i / 10)), 0, r * U * math.sin(2 * math.pi * i / 10)),
                          "catmullrom") for i in range(steps + 1)]
    # the sun: the corona turns slowly (billboarded, so about the line of sight) and pulses gently
    spin = [key("orbits", "sun", "rotation", t, (0, 0, -15 * t)) for t in range(0, LOOP + 1, 2)]
    pulse = [key("orbits", "sun", "scale", t0 + t, (s, s, s), "catmullrom") for t0 in range(0, LOOP, 6)
             for t, s in ((0, 1), (1.5, 1.035), (3, 1), (4.5, 1.02))] + [key("orbits", "sun", "scale", LOOP, (1, 1, 1))]
    tracks["sun"] = spin + pulse
    return clip("idle", LOOP, "loop", tracks, uuids)


def comet_clip(uuids):
    """One pass: from far out (aphelion) in, round the sun and back out. The arm turns to the comet's direction
    (rotation about y); the comet sits out along the arm at its distance; its tail, along the arm, grows near the sun."""
    a, e, _, w = COMET
    T = period(a)
    steps = round(T * 10)
    arm, pos, tail = [], [], []
    prev = None
    for i in range(steps + 1):
        M = math.pi + 2 * math.pi * i / steps        # aphelion to aphelion
        X, _, Z = orbit_point(a, e, math.radians(w), 0, M)
        r = math.hypot(X, Z)
        th = -math.degrees(math.atan2(Z, X))            # turning +x onto (X, Z): rotation y = -atan2(z, x)
        if prev is not None:
            while th - prev > 180:
                th -= 360
            while th - prev < -180:
                th += 360
        prev = th
        t = T * i / steps
        arm.append(key("comet", "comet_arm", "rotation", t, (0, th, 0)))
        pos.append(key("comet", "comet", "position", t, (px(r * U), 0, 0)))
        s = min(2.4, max(0.35, 0.9 / max(r, 0.3)))      # the tail grows as the comet nears the sun
        tail.append(key("comet", "comet_tail", "scale", t, (s, 1, 1)))
    return clip("comet", T, "once", {"comet_arm": arm, "comet": pos, "comet_tail": tail}, uuids)


def meteor_clip(k, length, dur, uuids):
    """The streak flies along its arm (+x) the whole path; it brightens in and fades out by size."""
    n = 8
    pos, scl = [], []
    for i in range(n + 1):
        f = i / n
        pos.append(key(f"meteor_{k}", f"meteor_{k}", "position", dur * f, (px(length * U * f), 0, 0)))
        s = 0.35 + 0.65 * math.sin(math.pi * f) ** 0.6
        scl.append(key(f"meteor_{k}", f"meteor_{k}", "scale", dur * f, (s, s, s)))
    return clip(f"meteor_{k}", dur, "once", {f"meteor_{k}": pos + scl}, uuids)


# ---- output ----------------------------------------------------------------------------------------------------------

def pack():
    ZIP.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PACK.rglob("*")):
            if f.is_file() and f.suffix != ".zip":
                z.write(f, f.relative_to(PACK).as_posix())


def main():
    PREVIEW.mkdir(parents=True, exist_ok=True)
    build_atlas().resize((TEX * 4, TEX * 4), Image.NEAREST).save(PREVIEW / "atlas.png")
    out = {}
    for build in (build_orrery, build_comet, build_meteors):
        m, bb = build()
        path = PACK / "BetterModel/models" / f"{m.name}.bbmodel"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bb, separators=(",", ":")) + "\n", encoding="utf-8")
        out[m.name] = {"cubes": len(bb["elements"]), "bones": len(bb["groups"]),
                       "clips": {c["name"]: c["length"] for c in bb["animations"]},
                       "kb": round(path.stat().st_size / 1024)}
    out["periods"] = {p[0]: round(loop_period(period(p[1]))[0], 3) for p in PLANETS}
    pack()
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
