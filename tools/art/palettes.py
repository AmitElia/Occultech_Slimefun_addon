"""Occultech palettes: hue-shifted ramps, dark to light (shadows lean blue/violet, highlights lean warm).

Each tier has its own family so an item's tier reads at a glance; accents are shared sparingly.
"""

def hexes(*codes):
    return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for c in codes]

RAMPS = {
    # neutrals
    "chalk":    hexes("#2e2c3e", "#5d5a6e", "#9a948f", "#cfc6b4", "#efe7d4", "#fffcf2"),
    "bone":     hexes("#2b2420", "#5e4f43", "#9a876f", "#cdbb98", "#ece0c0", "#fff8e6"),
    "iron":     hexes("#1c1d29", "#3b3e52", "#62677f", "#9196ad", "#c6cadb", "#f0f2fa"),
    "wood":     hexes("#24150f", "#4d2e1a", "#7d4e2b", "#a8743f", "#d0a066", "#efcf96"),
    "twine":    hexes("#2a1a12", "#5a3a22", "#8c6338", "#b98f55", "#dcbd80"),
    "wax":      hexes("#3b1d14", "#7a3e24", "#b56e3a", "#e0a35a", "#f6d28c", "#fff1c8"),
    # tier 1: bound (violet, silver, spirit)
    "violet":   hexes("#160b26", "#2f1650", "#4f2483", "#7a3db3", "#a771dc", "#d6b3fb"),
    "glass":    hexes("#1a1030", "#33245a", "#5a4a8c", "#8f86bd", "#c9c4e8", "#f4f2ff"),
    "spirit":   hexes("#0b2d3d", "#155c6e", "#1f949f", "#3fcfc6", "#9ef5e6", "#f0fffb"),
    # tier 2: abyssal (teal, deep navy, sea glow)
    "abyss":    hexes("#06131f", "#0d2a3b", "#144559", "#1e6a7a", "#3a9ca0", "#7fd4c8"),
    "seaglow":  hexes("#0a3b3a", "#11706a", "#1fb09e", "#58e6c8", "#b8fff0", "#ffffff"),
    # tier 3: hollow (sculk black-teal, bone, cyan, crimson)
    "sculk":    hexes("#04090d", "#0a1a22", "#11303a", "#1a4a55", "#2a6f78", "#4fa6a8"),
    "hollowcy": hexes("#06343f", "#0c6a7c", "#15a7b8", "#4fe0e8", "#bdfbff", "#ffffff"),
    "crimson":  hexes("#1e0610", "#4a0b1c", "#86142a", "#c4243a", "#f2554a", "#ffb08a"),
    # accents
    "ember":    hexes("#3a0f05", "#7a2508", "#c4500e", "#f08a1e", "#ffc65a", "#fff3c0"),
    "gold":     hexes("#2a1a06", "#5c3c0c", "#9a6a16", "#d6a230", "#f6d470", "#fff6c8"),
}

#: light comes from the top-left, slightly in front (screen y grows downward)
LIGHT = (-0.55, -0.62, 0.56)

TIER_FAMILY = {
    0: ["chalk", "bone", "wax", "twine", "iron", "ember"],
    1: ["violet", "glass", "spirit", "iron"],
    2: ["abyss", "seaglow", "iron", "gold"],
    3: ["sculk", "hollowcy", "crimson", "bone"],
}
