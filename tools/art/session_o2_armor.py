"""Session O2: the armor inventory icons redrawn - vanilla's armor silhouettes (helmet, chestplate, leggings, boots: what
players read as armor at a glance), exactly symmetric, finished. Each icon is drawn as its left half and mirrored; the
mirrored half is shaded a step darker (the light comes from the top-left). Details are the worn sets' (G6).

Legend (left half): . empty | O outline (lit side; mirrors to the dark-side outline) | 1-5 the set's metal ramp
(5 brightest; mirrors one step darker) | K the inside, darkest | G glow (pulses) | g glow, dim | the set's own letters.

Run: python tools/art/session_o2_armor.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from PIL import Image  # noqa: E402

ART = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art")

# ---------------------------------------------------------------- Abyssal (T2): teal plate, scales, fins, sea glow
ABYSSAL = {
    "abyssal_helm": [
        "........",
        "........",
        ".......O",
        ".....OO5",
        ".O..O454",
        ".OfOO443",
        "..fO4433",
        "...OGGGG",
        "...O43KK",
        "...O32KK",
        "...O32KK",
        "....O2O.",
        "........",
        "........",
        "........",
        "........",
    ],
    "abyssal_chestplate": [
        "........",
        "........",
        ".OOOOO..",
        ".O5554O.",
        ".O54G4OO",
        ".O44433O",
        ".O4333G3",
        ".OO43333",
        "...O4334",
        "...Os33s",
        "...O3443",
        "...O3ss3",
        "...O2332",
        "....OO22",
        ".....OOO",
        "........",
    ],
    "abyssal_greaves": [
        "........",
        "........",
        "....OOOO",
        "...O5GGG",
        "...O4444",
        "...O43s3",
        "...O433O",
        "...O43O.",
        "...Of3O.",
        "...O43O.",
        "...O33O.",
        "...O3sO.",
        "...O22O.",
        "...OOOO.",
        "........",
        "........",
    ],
    "abyssal_boots": [
        "........",
        "........",
        "........",
        "...OOOO.",
        "...O55O.",
        "...OGGO.",
        "...O43O.",
        "..fO43O.",
        "..fO33O.",
        "..O443O.",
        ".O5443O.",
        "O54433O.",
        "OGGGGGO.",
        "OOOOOOO.",
        "........",
        "........",
    ],
}

# ---------------------------------------------------------------- Hollow (T3): black-grey steel, sculk, soul blue, purple
HOLLOW = {
    "hollow_crown": [
        "........",
        ".P......",
        ".PP.....",
        "..PP.OOO",
        "..pPO554",
        "...O4444",
        "...O3GGG",
        "...O43KK",
        "...OS3KK",
        "...OSsKK",
        "...Os3KK",
        "....O3O.",
        "........",
        "........",
        "........",
        "........",
    ],
    "hollow_cuirass": [
        "........",
        "........",
        ".OOOOO..",
        ".O5544O.",
        ".O4G44OO",
        ".Op4433O",
        ".O4333S3",
        ".OO43SGG",
        "...O3SGW",
        "...O33Ss",
        "...O3s33",
        "...O3G33",
        "...O2233",
        "....OPPP",
        ".....OOO",
        "........",
    ],
    "hollow_greaves": [
        "........",
        "........",
        "....OOOO",
        "...O5554",
        "...O44G4",
        "...OS433",
        "...OTS3O",
        "...OSsO.",
        "...OPpO.",
        "...O4GO.",
        "...O33O.",
        "...O32O.",
        "...O22O.",
        "...OOOO.",
        "........",
        "........",
    ],
    "hollow_sabatons": [
        "........",
        "........",
        "........",
        "...OOOO.",
        "...OPPO.",
        "...OppO.",
        "...O43O.",
        "...OS3O.",
        "...Os3O.",
        "..O443O.",
        ".O5443O.",
        "O5S433O.",
        "OGGGGGO.",
        "OOOOOOO.",
        "........",
        "........",
    ],
}


def mirror(rows):
    """The full 16 px row from its left half: the right half mirrored, a step darker, the outline its dark tone."""
    out = []
    for row in rows:
        assert len(row) == 8, row
        right = []
        for ch in reversed(row):
            if ch.isdigit():
                right.append(str(max(1, int(ch) - 1)))
            elif ch == "O":
                right.append("o")
            else:
                right.append(ch)
        out.append(row + "".join(right))
    return out


def draw(rows, cols, frame):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(mirror(rows)):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            c = cols(ch, frame)
            img.putpixel((x, y), c[:3] + (255,))
    return img


def abyssal_cols(ch, frame):
    ab, sg = RAMPS["abyss"], RAMPS["seaglow"]
    if ch.isdigit():
        return ab[int(ch)]
    return {"O": ab[1], "o": ab[0], "K": ab[0], "G": sg[[3, 4, 5, 4][frame % 4]], "g": sg[2],
            "f": sg[3], "s": ab[2]}[ch]


HOLLOW_STEEL = [(20, 20, 24, 255), (36, 36, 43, 255), (53, 53, 62, 255), (74, 74, 84, 255), (98, 98, 108, 255),
                (126, 126, 136, 255)]


def hollow_cols(ch, frame):
    st, sk, hc, vi = HOLLOW_STEEL, RAMPS["sculk"], RAMPS["hollowcy"], RAMPS["violet"]
    if ch.isdigit():
        return st[int(ch)]
    return {"O": st[1], "o": st[0], "K": st[0], "G": hc[[3, 4, 5, 4][frame % 4]], "W": (230, 250, 255, 255),
            "S": sk[3], "s": sk[1], "T": sk[4], "P": vi[4], "p": vi[2]}[ch]


SETS = [("session-e", ABYSSAL, abyssal_cols), ("session-f", HOLLOW, hollow_cols)]


def icon(name, frame=0):
    """One icon's frame (for session_e / session_f, whose functions now draw these)."""
    for session, maps, cols in SETS:
        if name in maps:
            return draw(maps[name], cols, frame)
    raise KeyError(name)


def all_icons():
    out = []
    for session, maps, cols in SETS:
        for name, rows in maps.items():
            out.append((session, name, [draw(rows, cols, f) for f in range(4)]))
    return out


if __name__ == "__main__":
    for session, name, frames in all_icons():
        for f, img in enumerate(frames):
            img.save(os.path.join(ART, session, f"{name}_{f}.png"))
    print("saved")
