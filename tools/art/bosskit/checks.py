"""Geometry checks for boss models, run by the boss scripts before shipping."""
import itertools

import numpy as np

# corner indices of each face (corner order from bbmodel.Cube.corners: x outer, y middle, z inner)
QUADS = {"north": (0, 2, 6, 4), "south": (1, 5, 7, 3), "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
         "down": (0, 4, 5, 1), "up": (2, 3, 7, 6)}


def _faces(cubes):
    out = []
    for c in cubes:
        p = c.corners()
        centre = p.mean(0)
        for face, q in QUADS.items():
            pts = p[list(q)]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-9:      # the edge of a zero-thickness card: no area, never drawn
                continue
            n /= np.linalg.norm(n)
            if np.dot(pts.mean(0) - centre, n) < 0:
                n = -n
            out.append((c, face, pts, n, float(np.dot(n, pts[0]))))
    return out


def _covered(a, b, samples=6):
    """Share of quad a lying inside quad b (both on one plane)."""
    u, v = a[1] - a[0], a[3] - a[0]
    bu, bv = b[1] - b[0], b[3] - b[0]
    hits = 0
    for i in range(samples):
        for j in range(samples):
            d = a[0] + u * (i + 0.5) / samples + v * (j + 0.5) / samples - b[0]
            x, y = np.dot(d, bu) / np.dot(bu, bu), np.dot(d, bv) / np.dot(bv, bv)
            hits += -0.01 < x < 1.01 and -0.01 < y < 1.01
    return hits / samples ** 2


def flicker_pairs(cubes, threshold=0.03):
    """Faces of different cubes that lie on one plane, face the same way and overlap: they z-fight in game.

    Faces pressed back to back (opposite normals) are inside the model and harmless, so they are not reported.
    Returns (overlap, cube, face, other cube, other face), largest first, in the rest pose.
    """
    out = []
    # only faces on one plane can fight: bucket them by direction and offset (neighbouring buckets too, for rounding)
    buckets = {}
    for f in _faces(cubes):
        key = (tuple(np.round(f[3], 2)), round(f[4] * 10))
        buckets.setdefault(key, []).append(f)
    pairs = []
    for (n, d), group in buckets.items():
        pairs += itertools.combinations(group, 2)
        pairs += [(a, b) for a in group for b in buckets.get((n, d + 1), ())]
    for (c1, f1, p1, n1, d1), (c2, f2, p2, n2, d2) in pairs:
        if c1 is c2 or np.dot(n1, n2) < 1 - 1e-3 or abs(d1 - d2) > 0.05:
            continue
        share = _covered(p1, p2)
        if share > threshold:
            out.append((round(share, 2), c1.name, f1, c2.name, f2))
    return sorted(out, reverse=True)
