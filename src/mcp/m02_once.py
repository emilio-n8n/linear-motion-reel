"""M2 ONCE — the accent.

The brief's swing beat. A felt-tip loop closes around "entire organization", the
loop deploys outward and dissolves, and the word "Once" lands large in the centre
with a firm underline. The company's people populate the right of the frame.

The craft is the ring. It overshoots its own start rather than closing, and it
leaves by expanding rather than fading — which is what the brief means by "la
boucle se déploie".
"""

from __future__ import annotations

import math

from components import avatar
from camera import Z_BACKDROP, Z_BEHIND, Z_CONTROL, Z_NEAR, Z_RAISED, Z_SURFACE, Camera, Rig
from easing import seg
from layout import measure, svg_font
from sketch import line, ring
from svg import Doc
from tokens import (
    CORAL,
    CORAL_DEEP,
    H,
    INK,
    PAPER,
    SANS,
    SERIF,
    W,
)

# The statement carried over from M1, positioned as it ended there.
LINE_1 = "Authorize MCP connectors"
LINE_2 = "for your entire organization"
TEXT_X = 230.0
LINE_Y = H * 0.5 - 52
SIZE = 82.0

ONCE = "Once"
ONCE_SIZE = 268.0

AVATARS = [
    ("CL", "#7C6BD6"), ("ZB", "#4E9E7B"), ("BR", "#C2803F"),
    ("JE", "#5B7FC7"), ("MK", "#A9618F"), ("TS", "#6E8B54"),
    ("AN", "#8A6BC1"), ("RD", "#C06A57"), ("LP", "#4A8FA8"),
]


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    statement = seg(clock.u, 0.0, 0.10, "out")
    # The statement clears well before "Once" arrives: two focal points at once
    # reads as muddle, and the carried text is the weaker of the two.
    fade = seg(clock.u, 0.28, 0.22, "inout")
    ring_on = seg(clock.u, 0.06, 0.26, "expo")
    deploy = seg(clock.u, 0.34, 0.28, "inout")
    once_in = seg(clock.u, 0.52, 0.24, "expo")
    underline = seg(clock.u, 0.66, 0.22, "out")
    grid = seg(clock.u, 0.34, 0.52, "out")

    # Camera pulls back as the loop deploys, so the frame opens up rather than
    # closing — the opposite of the first scene's push, which gives the two beats
    # different energy without changing the vocabulary.
    dx, dy = Rig.drift(clock.u, amount=13.0, rate=0.7, phase=2.1)
    cam = Camera(
        x=W / 2 + dx + 60.0 * deploy,
        y=H / 2 + dy,
        push=Rig.dolly_in(clock.u, 0.30, 0.60, -0.16, "inout"),
    )

    if grid > 0:
        with d.group(transform=cam.transform(Z_BEHIND)):
            _grid(d, grid)
    if statement > 0:
        with d.group(transform=cam.transform(Z_SURFACE)):
            _carried(d, statement, fade)
            # The ring belongs to the text it circles, so it shares the layer.
            if ring_on > 0:
                _ring(d, ring_on, deploy)
    if once_in > 0:
        with d.group(transform=cam.transform(Z_RAISED)):
            _once(d, once_in, underline)

    return d.render()


def _carried(d: Doc, u: float, fade: float) -> None:
    """The statement from the previous scene, which the ring then circles."""
    fam, weight = svg_font(SERIF)
    op = u * (1.0 - fade)
    if op <= 0.01:
        return
    for k, text in enumerate((LINE_1, LINE_2)):
        ink = INK if k == 0 else CORAL_DEEP
        d.text(TEXT_X, LINE_Y + k * 106, text, SIZE, fam, weight, ink,
               tracking=-0.4, opacity=op)
    tw = measure(SERIF, SIZE, LINE_2, -0.4)
    d.line(TEXT_X, LINE_Y + 106 + 34, TEXT_X + tw, LINE_Y + 106 + 34,
           CORAL_DEEP, 2.0, opacity=0.5 * op)


def _ring(d: Doc, u: float, deploy: float) -> None:
    """The felt loop around "entire organization".

    Positioned from the measured text, so it lands around the words themselves
    rather than around where the words were assumed to be. It leaves by scaling
    up and fading, which reads as the loop being cast off rather than deleted.
    """
    fam, _ = svg_font(SERIF)
    prefix_w = measure(SERIF, SIZE, "for your ", -0.4)
    target_w = measure(SERIF, SIZE, "entire organization", -0.4)

    cx = TEXT_X + prefix_w + target_w / 2
    cy = LINE_Y + 106 - 26
    rx = target_w / 2 + 22
    ry = 66.0

    scale = 1.0 + 0.62 * deploy
    opacity = u * (1.0 - deploy) ** 1.4
    if opacity <= 0.01:
        return

    with d.group(
        transform=(
            f"translate({cx:.2f} {cy:.2f}) scale({scale:.3f}) "
            f"translate({-cx:.2f} {-cy:.2f})"
        ),
        opacity=opacity,
    ):
        for p in ring(cx, cy, rx, ry, width=6.5, seed=11, overshoot=0.26,
                      span=max(u, 0.02)):
            d.path(p, fill=CORAL_DEEP)


def _once(d: Doc, u: float, underline: float) -> None:
    """The word, landing large and centred, then firmly underlined."""
    fam, weight = svg_font(SERIF)
    tw = measure(SERIF, ONCE_SIZE, ONCE, -4.0)
    x = W / 2 - tw / 2
    base = H * 0.46

    # Settles from slightly large, which gives the landing weight.
    s = 1.0 + (1.0 - u) * 0.08
    op = min(u * 1.6, 1.0)
    with d.group(
        transform=(
            f"translate({W / 2:.2f} {base:.2f}) scale({s:.4f}) translate({-W / 2:.2f} {-base:.2f})"
        ),
        opacity=op,
    ):
        d.text(x, base, ONCE, ONCE_SIZE, fam, weight, INK, tracking=-4.0)

    if underline <= 0.01:
        return
    y = base + 34
    # Heavy pass, drawn on left to right.
    for p in line(x - 10, y, x + tw + 10, y + 3, width=9.0, seed=5, wobble=2.8,
                  span=underline):
        d.path(p, fill=CORAL, opacity=min(underline * 1.5, 1.0))
    # A lighter trailing pass: a felt tip lays ink down unevenly, and one clean
    # pass reads as a vector rule rather than a mark.
    trail = max(0.0, underline - 0.14) / 0.86
    for p in line(x - 6, y + 4.5, x + tw + 4, y + 6.5, width=4.4, seed=17,
                  wobble=2.0, span=trail):
        d.path(p, fill=CORAL_DEEP, opacity=0.42 * underline)


def _grid(d: Doc, u: float) -> None:
    """The company's people, populating the right of the frame.

    Columns are computed from the width left over beside the centred word, so the
    field cannot drift into the type if either changes.
    """
    fam, _ = svg_font(SERIF)
    # Clear of the largest thing that ever occupies the right of the frame: the
    # word when it is centred, and the carried statement before that.
    line_w = measure(SERIF, SIZE, LINE_2, -0.4)
    left = max(W / 2 + measure(SERIF, ONCE_SIZE, ONCE, -4.0) / 2, TEXT_X + line_w) + 110.0
    right = W - 140.0                    # margin
    cols = len(AVATARS) // 3
    rows = 3
    dx = (right - left) / max(cols - 1, 1) if cols > 1 else 0.0
    dy = 150.0
    y0 = H * 0.5 - dy

    for i, (initials, fill) in enumerate(AVATARS):
        col, row = i % cols, i // cols
        local = seg(u, (i / max(len(AVATARS) - 1, 1)) * 0.55, 0.45, "expo")
        if local <= 0:
            continue
        r = 36.0 * (0.65 + 0.35 * local)
        avatar(d, left + col * dx, y0 + row * dy, r, initials, fill, opacity=local)
