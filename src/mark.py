"""Hand-built mark for the end card.

This is an original construction, not Linear's logo file. Their brand guidelines
ask that the mark not be altered or used in a way implying endorsement, so the
geometry here is my own: a rounded square holding a rising diagonal form, drawn
as stroke paths so it can be animated with stroke-dashoffset.

The end card labels the piece as an unofficial concept, which is what makes a
lookalike defensible.
"""

from __future__ import annotations

import math

BOX = 168.0  # mark box size in px
RADIUS = 0.22  # corner radius as a fraction of the box


def _box_path(size: float, r: float) -> str:
    """Rounded square as an explicit path, so it can be dash-animated."""
    s = size
    return (
        f"M{_n(r)} 0 L{_n(s - r)} 0 "
        f"Q{_n(s)} 0 {_n(s)} {_n(r)} "
        f"L{_n(s)} {_n(s - r)} "
        f"Q{_n(s)} {_n(s)} {_n(s - r)} {_n(s)} "
        f"L{_n(r)} {_n(s)} "
        f"Q0 {_n(s)} 0 {_n(s - r)} "
        f"L0 {_n(r)} "
        f"Q0 0 {_n(r)} 0 Z"
    )


def _glyph_paths(size: float) -> list[tuple[str, float]]:
    """The inner form, as (path, approximate_length) pairs.

    Two elements: a wedge rising from the lower left, and a shorter counter-wedge
    above it. Lengths are approximate and only feed the dash animation, which
    self-corrects because the drawn length is clamped to 1.
    """
    s = size
    # Main wedge: from the lower-left, rising to the upper-right.
    main = (
        f"M{_n(s * 0.20)} {_n(s * 0.78)} "
        f"L{_n(s * 0.56)} {_n(s * 0.78)} "
        f"L{_n(s * 0.84)} {_n(s * 0.34)} "
        f"L{_n(s * 0.50)} {_n(s * 0.34)} Z"
    )
    # Counter-wedge, offset above, the negative-space echo.
    counter = (
        f"M{_n(s * 0.20)} {_n(s * 0.52)} "
        f"L{_n(s * 0.44)} {_n(s * 0.52)} "
        f"L{_n(s * 0.50)} {_n(s * 0.34)} "
        f"L{_n(s * 0.20)} {_n(s * 0.34)} Z"
    )
    return [(main, s * 0.95), (counter, s * 0.52)]


def draw_mark(d, cx: float, cy: float, size: float, draw: float, stroke: str, accent: str,
              box_opacity: float = 0.10) -> None:
    """Draw the mark at `draw` in 0..1, as if a stroke were tracing it on.

    Each subpath is dash-animated independently with a stagger, so the form
    assembles rather than simply scaling up.
    """
    if draw <= 0.001:
        return
    x = cx - size / 2
    y = cy - size / 2
    r = size * RADIUS

    # The container, easing in ahead of the glyph. The scale is applied about the
    # box centre via an explicit translate pair — rsvg does not honour
    # transform-origin, so it cannot be left implicit.
    box_u = min(draw / 0.45, 1.0)
    if box_u > 0:
        s = 0.94 + 0.06 * box_u
        d.add(
            f'<g transform="translate({_n(x)} {_n(y)})">'
            f'<g transform="translate({_n(size / 2)} {_n(size / 2)}) scale({_n(s)}) '
            f'translate({_n(-size / 2)} {_n(-size / 2)})">'
            f'<path d="{_box_path(size, r)}" fill="rgba(255,255,255,{box_opacity * box_u:.3f})" '
            f'stroke="rgba(255,255,255,0.16)" stroke-width="1.2"/>'
            f"</g></g>"
        )

    for i, (path, approx_len) in enumerate(_glyph_paths(size)):
        # Each subpath starts after the one before it has mostly drawn.
        start = 0.30 + i * 0.26
        local = (draw - start) / 0.62
        if local <= 0:
            continue
        local = min(local, 1.0)
        shown = approx_len * local
        col = accent if i == 0 else stroke
        d.add(
            f'<g transform="translate({_n(x)} {_n(y)})">'
            f'<path d="{path}" fill="none" stroke="{col}" stroke-width="{_n(size * 0.075)}" '
            f'stroke-linejoin="round" stroke-linecap="round" '
            f'stroke-dasharray="{_n(approx_len)} {_n(approx_len)}" '
            f'stroke-dashoffset="{_n(approx_len - shown)}" '
            f'opacity="{_n(0.55 + 0.45 * local)}"/>'
            f"</g>"
        )


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
