"""Design tokens for the Claude / MCP film.

A light film, not a dark one. That inverts the visual layer: where the dark reel
built light out of stacked additive passes, this one builds depth out of soft
shadows and thin rules on a warm paper ground.

Palette and type follow the brief: cream ground, terracotta accent, anthracite
text, blue for active controls, and a serif for anything editorial against a
geometric sans for interface.
"""

from __future__ import annotations

import math

# ------------------------------------------------------------------- colour

# Warm off-white. Not #ffffff: pure white reads as a screen, and the brief calls
# for paper.
PAPER = "#FBF9F5"
PAPER_DEEP = "#F4F1EA"  # recessed panels
PAPER_LINE = "#E8E3D9"  # hairlines on paper

INK = "#1F1E1D"  # primary text, softened black
INK_2 = "#4A4744"  # secondary
INK_3 = "#7A756E"  # tertiary
INK_4 = "#A8A29A"  # quaternary / disabled

# Claude coral. The bright tone is for strokes and accents, the deep for text
# where the lighter one would not hold contrast on paper.
CORAL = "#D96B43"
CORAL_DEEP = "#CC5533"
CORAL_SOFT = "#F2D9CF"  # fills

# Controls. Neutral at rest, blue when engaged.
TOGGLE_OFF = "#D8D3C9"
TOGGLE_ON = "#2563EB"
BLUE = "#2563EB"

# Interface surfaces
CARD = "#FFFFFF"
CARD_LINE = "#EAE6DE"

# ------------------------------------------------------------------ layout

W, H = 1920, 1080
FPS = 30
DURATION = 34.0
TOTAL_FRAMES = int(round(DURATION * FPS))

MARGIN = 150
COL = (W - 2 * MARGIN) / 6.0

# -------------------------------------------------------------------- type

SERIF = "SourceSerif4-Semibold"
SERIF_REG = "SourceSerif4-Regular"
SERIF_LIGHT = "SourceSerif4-Light"
SERIF_BOLD = "SourceSerif4-Bold"

SANS = "Inter-SemiBold"
SANS_MED = "Inter-Medium"
SANS_REG = "Inter-Regular"
SANS_BOLD = "Inter-Bold"
MONO = "JetBrainsMono-Medium"

# A type scale, in px at 1080p. Use these rather than ad-hoc sizes: a headline
# that occupies a third of the frame's width reads as a caption, not a headline,
# and it is the most common way a composition ends up looking sparse.
#
# As a rule of thumb, an editorial headline should span 55-80% of the frame width.
HERO = 132.0      # one or two words, the subject of the frame
H1 = 88.0         # a section headline
H2 = 64.0         # a supporting line
LEAD = 36.0       # a short statement
BODY = 17.0       # interface copy
CAPTION = 13.0    # labels

# ----------------------------------------------------------------- scenes

# (name, first_frame, last_frame_exclusive). Frame counts, not seconds, so the
# timeline is exact. Matches the brief's scene timings: 3 / 4 / 5 / 4 / 4 / 8 / 6.
SCENES = [
    ("org", 0, 90),
    ("once", 90, 210),
    ("idp", 210, 360),
    ("login", 360, 480),
    ("tools", 480, 600),
    ("prompt", 600, 840),
    ("packshot", 840, 1020),
]

assert SCENES[-1][2] == TOTAL_FRAMES, (SCENES[-1][2], TOTAL_FRAMES)


def scene_span(name: str) -> tuple[int, int]:
    for n, a, b in SCENES:
        if n == name:
            return a, b
    raise KeyError(name)


def col_x(i: int) -> float:
    return MARGIN + i * COL
