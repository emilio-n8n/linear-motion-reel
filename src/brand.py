"""Linear's design tokens, plus the frame-level drawing helpers built on them.

Colour and type values are taken from linear.app's own stylesheet and theme
colour rather than eyeballed, so the reel sits in the brand's actual system.
"""

from __future__ import annotations

import math

# ------------------------------------------------------------------- colour

CANVAS = "#08090a"  # linear.app <meta name="theme-color">
SURFACE = {
    0: "#0f1011",
    1: "#141516",
    2: "#18191a",
    3: "#191a1b",
}

INK = {
    1: "#f7f8f8",
    2: "#d0d6e0",
    3: "#8a8f98",
    4: "#62666d",
}

# Linear reserves brand indigo for interactive and active state, not decoration.
ACCENT = "#5e6ad2"
ACCENT_BRIGHT = "#7170ff"
ACCENT_HOVER = "#828fff"

HAIRLINE = "rgba(255,255,255,0.08)"
HAIRLINE_SOFT = "rgba(255,255,255,0.05)"
HAIRLINE_STRONG = "rgba(255,255,255,0.14)"

# The one place a second hue is allowed: a cool highlight at the far end of the
# accent ramp, so light has somewhere to travel to.
COOL = "#4cc9f0"

# ------------------------------------------------------------------ display

W, H = 1920, 1080
FPS = 30
DURATION = 45.0
TOTAL_FRAMES = int(round(DURATION * FPS))

# 8 x 9 frame grid (3:2), i.e. a 6-column layout field.
MARGIN = 168
COL = (W - 2 * MARGIN) / 6.0

TYPE_DISPLAY = "InterDisplay-Black"
TYPE_DISPLAY_XB = "InterDisplay-ExtraBold"
TYPE_UI = "Inter-SemiBold"
TYPE_UI_MED = "Inter-Medium"
TYPE_UI_REG = "Inter-Regular"
TYPE_MONO = "JetBrainsMono-Medium"

SCENE_NAMES = [
    "ORIGIN",
    "DISPLAY",
    "LATTICE",
    "FIELD",
    "PRISM",
    "MONOLITH",
    "CASCADE",
    "SIGNATURE",
]

# (name, first_frame, last_frame_exclusive) — frame counts, not seconds, so the
# timeline is exact and cannot drift.
SCENES = [
    ("origin", 0, 150),
    ("display", 150, 300),
    ("lattice", 300, 465),
    ("field", 465, 630),
    ("prism", 630, 795),
    ("monolith", 795, 960),
    ("cascade", 960, 1140),
    ("signature", 1140, 1350),
]

assert SCENES[-1][2] == TOTAL_FRAMES, (SCENES[-1][2], TOTAL_FRAMES)


def scene_span(name: str) -> tuple[int, int]:
    for n, a, b in SCENES:
        if n == name:
            return a, b
    raise KeyError(name)


# ------------------------------------------------------------------- helpers


def col_x(i: int) -> float:
    return MARGIN + i * COL


def deg(r: float) -> float:
    return math.degrees(r)


def f(v: float) -> str:
    """Compact number formatting — these strings end up in every frame's SVG."""
    if v == 0:
        return "0"
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"
