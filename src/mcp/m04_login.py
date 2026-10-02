"""M4 LOGIN — everything is already connected on the first login.

The brief: the checked discs zoom and transform into personalised welcome cards,
one per employee, each with the asterisk and a prompt bar.

The craft is the morph. The discs do not disappear and the cards do not fade in
independently — each card is the same object as the disc it replaced, so the
transition is a scale on one element rather than a cut between two. That is what
makes it read as a transformation rather than a swap.
"""

from __future__ import annotations

import math

from components import avatar, welcome_card
from easing import seg
from layout import measure, svg_font
from svg import Doc
from tokens import (
    CORAL,
    H1,
    CORAL_DEEP,
    H,
    INK,
    INK_3,
    PAPER,
    SANS_MED,
    SERIF,
    W,
)

HEAD = "Everything's connected on your first login"

# (initials, colour, greeting, name, suggested prompt) — the people from the brief.
PEOPLE = [
    ("CL", "#7C6BD6", "Welcome,", "Chelsea", "Summarise this week's beta"),
    ("ZB", "#4E9E7B", "Back at it,", "Zak", "What shipped yesterday?"),
    ("BR", "#C2803F", "Morning,", "Brooke", "Top customer requests"),
    ("JE", "#5B7FC7", "Hey there,", "Jenn", "Draft the release notes"),
    ("MK", "#A9618F", "Welcome back,", "Mira", "Where is the beta at?"),
    ("TS", "#6E8B54", "Morning,", "Theo", "Unresolved bugs this week"),
    ("AN", "#8A6BC1", "Welcome,", "Ana", "Summarise the design review"),
    ("RD", "#C06A57", "Back at it,", "Ravi", "Which tickets are blocked?"),
    ("LP", "#4A8FA8", "Hey there,", "Lena", "Draft next sprint's goals"),
]

CARD_W = 500.0
CARD_H = 188.0

# The disc grid, from the previous scene's geometry.
GRID_CX = 960.0
GRID_CY = 700.0
DISC_DX = 132.0
DISC_DY = 132.0


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    head = seg(clock.u, 0.02, 0.26, "out")
    discs = seg(clock.u, 0.0, 0.12, "out")
    zoom = seg(clock.u, 0.30, 0.22, "inout")
    morph = seg(clock.u, 0.44, 0.36, "expo")
    settle = seg(clock.u, 0.76, 0.22, "out")

    _heading(d, head, morph)
    if morph < 0.995:
        _discs(d, discs, zoom, morph)
    if morph > 0.005:
        _cards(d, morph, settle)

    return d.render()


def _heading(d: Doc, u: float, fade: float) -> None:
    """The claim, centred, shrinking to a caption as the cards take the frame."""
    fam, weight = svg_font(SERIF)
    # Shrinks and lifts as the cards arrive, so the composition has one subject.
    size = H1 - 22.0 * fade
    base = 220.0 - 70.0 * fade
    tw = measure(SERIF, size, HEAD, -0.8)

    local = seg(u, 0.0, 0.9, "out")
    d.text(W / 2 - tw / 2, base, HEAD, size, fam, weight, INK,
           tracking=-0.8, opacity=local * (1.0 - fade * 0.15))


def _discs(d: Doc, u: float, zoom: float, morph: float) -> None:
    """The checked discs, zooming slightly then handing over to the cards.

    They stay on their own grid positions, so each card can grow out of the disc
    that was already there rather than appearing somewhere new.
    """
    n = len(PEOPLE)
    cols = 3
    op = u * (1.0 - morph) ** 1.3
    if op <= 0.01:
        return
    s = 1.0 + 0.34 * zoom
    for i, (initials, colour, _g, _n, _s) in enumerate(PEOPLE):
        col, row = i % cols, i // cols
        x = GRID_CX + (col - (cols - 1) / 2) * DISC_DX
        y = GRID_CY + (row - 1) * DISC_DY - 120
        avatar(d, x, y, 38.0 * s, initials, colour, check=1.0, opacity=op)


def _cards(d: Doc, morph: float, settle: float) -> None:
    """The welcome cards, growing out of the disc grid.

    Three columns, vertically centred on the frame, with the row spacing opened
    up from the disc grid so the cards have room to breathe.
    """
    n = len(PEOPLE)
    cols = 3
    rows = math.ceil(n / cols)
    dx = CARD_W + 22.0
    dy = CARD_H + 24.0
    x0 = W / 2 - (cols - 1) * dx / 2 - CARD_W / 2
    y0 = H / 2 - (rows - 1) * dy / 2 - CARD_H / 2 + 40.0

    for i, (initials, colour, greeting, name, suggestion) in enumerate(PEOPLE):
        col, row = i % cols, i // cols
        # Diagonal entry order, so the field fills as a wave rather than by index.
        order = (col * 0.6 + row * 1.0) / (cols - 1 + rows - 1)
        local = seg(morph, order * 0.30, 0.70, "expo")
        if local <= 0:
            continue

        x = x0 + col * dx
        y = y0 + row * dy

        # Grows from the disc's scale, overshooting very slightly.
        s = 0.72 + 0.28 * local
        lift = (1.0 - local) * 18
        # A gentle settle wobble once everything has arrived, so the frame is
        # still alive at the end of the scene.
        breathe = 1.0 + math.sin(settle * math.pi * 1.0 + i * 0.5) * 0.006 * settle

        with d.group(
            transform=(
                f"translate({x + CARD_W / 2:.2f} {y + lift + CARD_H / 2:.2f}) "
                f"scale({s * breathe:.4f}) "
                f"translate({-(x + CARD_W / 2):.2f} {-(y + lift + CARD_H / 2):.2f})"
            )
        ):
            welcome_card(d, x, y + lift, CARD_W, CARD_H, greeting, name,
                         lift=local, opacity=local, suggestion=suggestion)
