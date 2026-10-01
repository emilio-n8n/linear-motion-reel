"""S8 SIGNATURE — the mark draws itself, the statement lands, and the grid
breathes out.

Closes on a held frame: the last second is nearly still, which is what makes the
piece feel finished rather than cut off.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY, TYPE_DISPLAY_XB, TYPE_MONO, TYPE_UI, W
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from mark import draw_mark
from stock import clamp
from svg import Doc, glow

STATEMENT = "ORDER AT THE SPEED OF THOUGHT"


def draw(clock) -> str:
    d = Doc()
    _grid(d, clock)
    _mark(d, clock)
    _statement(d, clock)
    _signature(d, clock)
    _disclaimer(d, clock)
    return d.render()


def _grid(d: Doc, c) -> None:
    """A quiet grid that breathes — the system still running under the end card."""
    u = seg(c.u, 0.0, 0.30, "out")
    if u <= 0:
        return
    # Slow breathing scale, so the frame is alive without moving.
    breathe = 1.0 + math.sin(c.t * 0.9) * 0.006
    lines = []
    for i in range(1, 12):
        x = W * i / 12.0
        lines.append(f"M{x} {H * 0.5 - 300 * u * breathe} L{x} {H * 0.5 + 300 * u * breathe}")
    for i in range(1, 8):
        y = H * i / 8.0
        lines.append(f"M{W * 0.5 - 700 * u * breathe} {y} L{W * 0.5 + 700 * u * breathe} {y}")
    d.path(" ".join(lines), stroke=INK[4], width=1.0, opacity=0.10 * u)

    glow(d, W / 2, H * 0.44, 520, ACCENT, 0.16 * u)


def _mark(d: Doc, c) -> None:
    """The mark traces itself on, then holds with a slow glow pulse."""
    draw_u = seg(c.u, 0.06, 0.34, "expo")
    if draw_u <= 0:
        return
    size = 148.0
    cy = H * 0.40
    pulse = 0.5 + 0.5 * math.sin(c.t * 1.1)
    draw_mark(d, W / 2, cy, size, draw_u, INK[1], ACCENT_BRIGHT, box_opacity=0.055)
    if draw_u >= 1.0:
        glow(d, W / 2, cy, size * 1.15, ACCENT, 0.13 + 0.05 * pulse)


def _statement(d: Doc, c) -> None:
    """Statement type, per-glyph, with the counter-tracking settle."""
    u = seg(c.u, 0.30, 0.30, "out")
    if u <= 0:
        return
    fam, weight = svg_font(TYPE_DISPLAY_XB)
    size = 74.0
    tight, open_ = -0.055 * size, -0.014 * size
    tracking = tight + (open_ - tight) * seg(u, 0.2, 0.8, "out")

    gl = glyphs(TYPE_DISPLAY_XB, size, STATEMENT, tracking)
    total = measure(TYPE_DISPLAY_XB, size, STATEMENT, tracking)
    x0 = W / 2 - total / 2
    base = H * 0.635
    cap = cap_height(TYPE_DISPLAY_XB, size)

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        local = seg(u, (i / max(n - 1, 1)) * 0.46, 0.54, "expo")
        if local <= 0:
            continue
        rise = (1.0 - local) * 30
        bl = (1.0 - local) * 6
        fid = d.blur(bl) if bl > 0.4 else None
        d.text(x0 + dx, base + rise, ch, size, fam, weight, INK[1], opacity=local, filt=fid)


def _signature(d: Doc, c) -> None:
    """linear.app, plus the rule that arrives with it."""
    u = seg(c.u, 0.56, 0.24, "expo")
    if u <= 0:
        return
    fam, weight = svg_font(TYPE_UI)
    size = 30.0
    tracking = -0.4
    text = "linear.app"
    total = measure(TYPE_UI, size, text, tracking)
    x0 = W / 2 - total / 2
    base = H * 0.735

    # A rule that draws out from the centre to the width of the signature.
    d.line(W / 2 - total * u / 2, base - 40, W / 2 + total * u / 2, base - 40, ACCENT, 1.6, opacity=0.7 * u)
    d.text(x0, base, text, size, fam, weight, INK[2], tracking=tracking, opacity=u)

    glow(d, W / 2, base - 14, 190 * u, ACCENT, 0.18 * u)


def _disclaimer(d: Doc, c) -> None:
    """The unofficial-concept line. Small, quiet, and on screen long enough to read."""
    u = seg(c.u, 0.72, 0.16, "out")
    if u <= 0:
        return
    mfam, mweight = svg_font(TYPE_MONO)
    text = "UNOFFICIAL CONCEPT PIECE  ·  NOT AFFILIATED WITH LINEAR"
    fs = 12.0
    tracking = 2.6
    total = measure(TYPE_MONO, fs, text, tracking)
    d.text(W / 2 - total / 2, H - 96, text, fs, mfam, mweight, INK[4], tracking=tracking, opacity=0.55 * u)
