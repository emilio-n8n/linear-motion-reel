"""M3 IDP — identity provider, and the validation wave.

The brief: the headline becomes "Works with your Identity Provider", an identity
provider mark sits in the middle, two drawn connectors run from the interface
through it to the people on the right, and a validation wave crosses the grid —
each person's disc filling like a terracotta gauge and resolving into a check.

The craft is the wave. Every disc is driven by the same travelling front, offset
by its distance from the left edge, so the grid validates as one sweep rather
than as nine independent animations.
"""

from __future__ import annotations

import math

from components import avatar
from camera import Z_BACKDROP, Z_BEHIND, Z_CONTROL, Z_NEAR, Z_RAISED, Z_SURFACE, Camera, Rig
from easing import seg
from layout import measure, svg_font
from marks import tool_glyph
from sketch import arc_arrow, arrowhead, line
from svg import Doc
from tokens import (
    CORAL,
    H1,
    CORAL_DEEP,
    H,
    INK,
    INK_3,
    PAPER,
    PAPER_DEEP,
    PAPER_LINE,
    SANS,
    SANS_MED,
    SANS_REG,
    SERIF,
    W,
)

HEAD_1 = "Works with your"
HEAD_2 = "Identity Provider"

AVATARS = [
    ("CL", "#7C6BD6"), ("ZB", "#4E9E7B"), ("BR", "#C2803F"),
    ("JE", "#5B7FC7"), ("MK", "#A9618F"), ("TS", "#6E8B54"),
    ("AN", "#8A6BC1"), ("RD", "#C06A57"), ("LP", "#4A8FA8"),
]

# Flow geometry: interface on the left, provider in the middle, people on the right.
PANEL_X = 210.0
PANEL_Y = 500.0
PANEL_W = 360.0
PANEL_H = 200.0
IDP_X = 860.0
GRID_X = 1330.0


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    head = seg(clock.u, 0.02, 0.22, "out")
    panel = seg(clock.u, 0.10, 0.22, "expo")
    wire_a = seg(clock.u, 0.22, 0.26, "inout")
    idp = seg(clock.u, 0.30, 0.20, "expo")
    wire_b = seg(clock.u, 0.40, 0.26, "inout")
    grid = seg(clock.u, 0.34, 0.30, "out")
    # The validation front travels once the wiring reaches the people.
    wave = seg(clock.u, 0.56, 0.36, "inout")

    # A lateral track that follows the signal across the frame, from the
    # interface on the left to the people on the right. The camera leads the
    # wires slightly, so the movement feels motivated rather than synchronous.
    dx, dy = Rig.drift(clock.u, amount=9.0, rate=0.9, phase=1.2)
    cam = Camera(
        x=Rig.track(720.0, 1120.0, clock.u, 0.18, 0.66, "inout") + dx,
        y=H / 2 + 40.0 + dy,
        push=Rig.dolly_in(clock.u, 0.05, 0.90, 0.20, "inout"),
    )

    # Everything the wires connect stays on one layer, or the arrowheads would
    # drift off the edges they are supposed to meet.
    with d.group(transform=cam.transform(Z_SURFACE)):
        _heading(d, head)
        if panel > 0:
            _panel(d, panel)
        if grid > 0:
            _people(d, grid, wave)
        if wire_a > 0:
            _wire(d, 0, wire_a)
        if idp > 0:
            _provider(d, idp)
        if wire_b > 0:
            _wire(d, 1, wire_b)

    return d.render()


def _heading(d: Doc, u: float) -> None:
    """Two serif lines, the second carrying the emphasis."""
    fam, weight = svg_font(SERIF)
    size = H1
    x = 210.0
    base = 220.0
    for k, text in enumerate((HEAD_1, HEAD_2)):
        local = seg(u, k * 0.25, 0.75, "out")
        if local <= 0:
            continue
        ink = INK if k == 0 else CORAL_DEEP
        d.text(x, base + k * 82, text, size, fam, weight, ink,
               tracking=-1.2, opacity=local)


def _panel(d: Doc, u: float) -> None:
    """The interface, abstracted to a small card — the detail was in M1."""
    d.rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, fill="#FFFFFF", rx=12, opacity=u)
    d.rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, fill="none", stroke=PAPER_LINE,
           width=1.0, rx=12, opacity=u)
    # A few rows, suggesting the connector list without repeating it.
    for i in range(3):
        y = PANEL_Y + 34 + i * 40
        d.circle(PANEL_X + 30, y, 9, fill=PAPER_DEEP, opacity=u)
        d.rect(PANEL_X + 50, y - 5, 92 + (i % 2) * 34, 10, fill=PAPER_DEEP, rx=5, opacity=u)
        d.rect(PANEL_X + PANEL_W - 62, y - 11, 34, 22, fill=PAPER_DEEP, rx=11, opacity=u)
    d.text(PANEL_X + 24, PANEL_Y + PANEL_H - 22, "Connectors", 13.0,
           *svg_font(SANS_MED), INK_3, opacity=u)


def _provider(d: Doc, u: float) -> None:
    """The identity provider, on a raised white disc."""
    cx, cy = IDP_X, PANEL_Y + PANEL_H / 2
    r = 76.0
    s = 0.86 + 0.14 * u
    d.circle(cx, cy + 3, r * s, fill="rgba(31,30,29,0.07)", opacity=u)
    d.circle(cx, cy, r * s, fill="#FFFFFF", opacity=u)
    d.circle(cx, cy, r * s, fill="none", stroke=PAPER_LINE, width=1.0, opacity=u)
    tool_glyph(d, "okta", cx, cy, 58.0, u)


def _wire(d: Doc, which: int, u: float) -> None:
    """A drawn connector, panel -> provider -> people.

    Two separate runs so the signal reads as travelling in one direction rather
    than as a single link appearing.
    """
    cy = PANEL_Y + PANEL_H / 2
    if which == 0:
        x0, x1 = PANEL_X + PANEL_W + 14, IDP_X - 74
        lift = 54.0
    else:
        x0, x1 = IDP_X + 74, GRID_X - 78
        lift = 62.0

    hull, (ex, ey, ang) = arc_arrow(x0, cy, x1, cy, lift=lift, width=4.6,
                                    seed=30 + which * 7, span=u)
    if not hull:
        return
    d.path(hull, fill=CORAL, opacity=0.95)
    # Head appears only once the run has essentially arrived.
    head_u = max(0.0, (u - 0.72) / 0.28)
    if head_u > 0.01:
        s = 22.0 * (0.7 + 0.3 * head_u)
        d.path(arrowhead(ex, ey, ang, s), fill=CORAL, opacity=head_u)


def _people(d: Doc, u: float, wave: float) -> None:
    """The grid, each disc filling as the front passes over it.

    The front is a single value travelling left to right; each disc reads it at
    its own position, which is what makes nine animations one sweep.
    """
    n = len(AVATARS)
    cols, rows = 3, 3
    dx, dy = 152.0, 152.0
    y0 = PANEL_Y + PANEL_H / 2 - dy

    # The front sweeps a little past the grid so the last disc completes.
    front = -0.45 + wave * 1.75

    for i, (initials, fill) in enumerate(AVATARS):
        col, row = i % cols, i // cols
        cx = GRID_X + col * dx
        cy = y0 + row * dy

        appear = seg(u, (i / max(n - 1, 1)) * 0.45, 0.55, "expo")
        if appear <= 0:
            continue

        # Where this disc sits along the sweep, normalised.
        pos = col / max(cols - 1, 1)
        # The gauge fills as the front approaches and holds for a beat; the check
        # only lands well behind it. Without that gap the fill is never visible —
        # it reads as discs turning straight into ticks, losing the brief's gauge.
        prog = _ramp(front, pos - 0.80, pos - 0.10)
        tick = _ramp(front, pos + 0.10, pos + 0.46)

        avatar(d, cx, cy, 44.0 * (0.8 + 0.2 * appear), initials, fill,
               progress=prog, check=tick, opacity=appear)


def _ramp(x: float, a: float, b: float) -> float:
    """Linear 0..1 as x crosses [a, b], clamped. Used for the travelling front."""
    if b <= a:
        return 1.0 if x >= b else 0.0
    return max(0.0, min(1.0, (x - a) / (b - a)))
