"""S7 CASCADE — nine panels collapse off in a diagonal wave, each with its own
spring, rotation and blur trail, revealing a slowly turning form underneath.

The timing showpiece. The craft is in the offsets: no two panels leave on the
same frame, and the diagonal has to read as one gesture rather than a queue.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY, TYPE_DISPLAY_XB, TYPE_MONO, W
from easing import Spring, seg
from layout import cap_height, glyphs, measure, svg_font
from stock import clamp, mix_hex, project_iso
from svg import Doc, glow

PANELS = 9
COLS, ROWS = 3, 3
PANEL_GAP = 26.0
FIELD_W = 1180.0
FIELD_H = 700.0
FIELD_X = W / 2 - FIELD_W / 2
FIELD_Y = H / 2 - FIELD_H / 2


def draw(clock) -> str:
    d = Doc()
    _reveal_form(d, clock)

    pw = (FIELD_W - PANEL_GAP * (COLS - 1)) / COLS
    ph = (FIELD_H - PANEL_GAP * (ROWS - 1)) / ROWS
    for idx in range(PANELS):
        col, row = idx % COLS, idx // COLS
        _panel(
            d, clock, idx,
            FIELD_X + col * (pw + PANEL_GAP),
            FIELD_Y + row * (ph + PANEL_GAP),
            pw, ph,
        )
    return d.render()


def _panel(d: Doc, c, idx: int, x: float, y: float, w: float, h: float) -> None:
    """One panel: flies in, holds, then springs away on a diagonal."""
    col, row = idx % COLS, idx // COLS
    # Fly in on the same diagonal the exit uses, reversed — the grid assembles
    # from the corner it will later collapse from.
    # Rows stagger slightly more than columns, so the entry reads as a wave
    # sweeping in rather than nine panels arriving at once.
    in_order = (col * 0.45 + row * 1.0) / (COLS * 0.45 + ROWS - 1)
    appear = seg(c.u, in_order * 0.09, 0.17, "expo")
    if appear <= 0:
        return

    # Diagonal wavefront. The exit order is the transpose of the entry order, so
    # the wave crosses back the other way and the two diagonals read as one
    # continuous movement. The spread across the nine is wide enough that the
    # panels visibly hand off to each other rather than all departing at once.
    wave = (row * 0.45 + col * 1.0) / (COLS - 1 + ROWS * 0.45)
    leave_t = 0.30 + wave * 0.30
    p = seg(c.u, leave_t, 0.40, "circ")

    if p >= 1.0:
        return

    # Direction: away from the grid centre, so panels flee outward, with a
    # consistent rightward-and-up drift so the field clears as one gesture
    # rather than nine panels scattering in nine directions.
    cx = W / 2
    cy = H / 2
    vx, vy = (x + w / 2) - cx, (y + h / 2) - cy
    vm = math.hypot(vx, vy) or 1.0
    ux = vx / vm * 0.55 + 0.72
    uy = vy / vm * 0.55 - 0.58
    um = math.hypot(ux, uy) or 1.0
    ux, uy = ux / um, uy / um

    travel = 1500.0
    ox = ux * travel * p
    oy = uy * travel * p
    rot = 14.0 * p
    # Panels recede as they leave, so the field looks like it is being pulled
    # away from the viewer rather than sliding sideways across it.
    scale = 1.0 - 0.30 * p

    lvl = min(2, int(p * 3))
    fid = (None, d.blur(2.4), d.blur(6.5))[lvl]

    # Fade across the whole flight rather than only at the end, so a panel that
    # leaves early has actually gone by the time the last one starts moving.
    opacity = appear * (1.0 - seg(p, 0.10, 0.85, "in"))
    if opacity <= 0.01:
        return

    # The panel starts offset and settles, so `appear` reads as a fly-in rather
    # than a fade: offset is the inverse of the exit direction.
    entry = (1.0 - appear) * 260.0
    with d.group(
        transform=_tf(x - ux * entry, y - uy * entry + (1.0 - appear) * 30,
                      rot, scale * (0.94 + 0.06 * appear), w, h),
        opacity=opacity, filt=fid,
    ):
        d.rect(0, 0, w, h, fill="rgba(255,255,255,0.045)", rx=2)
        d.rect(0, 0, w, h, fill="none", stroke="rgba(255,255,255,0.16)", stroke_width=1.0, rx=2)
        _panel_content(d, idx, w, h)


def _panel_content(d: Doc, idx: int, w: float, h: float) -> None:
    """Abstract content per panel: a rule count, a figure, or a glyph. No UI."""
    kind = idx % 3
    mfam, mweight = svg_font(TYPE_MONO)

    if kind == 0:
        # A stack of rules of decreasing length — a bar chart, abstracted.
        for k in range(7):
            yy = 26 + k * 15
            ln = w * (0.24 + 0.62 * ((idx * 3 + k * 5) % 11) / 10.0)
            col = ACCENT if k == idx % 7 else INK[3]
            d.line(22, yy, 22 + ln, yy, col, 1.4, opacity=0.55)
    elif kind == 1:
        # A figure, counting.
        num = f"{(idx + 1) * 137:03d}"
        d.text(22, 54, num, 34, mfam, mweight, INK[2], tracking=1.0, opacity=0.8)
        d.line(22, 68, 22 + w - 44, 68, INK[4], 1.0, opacity=0.4)
        # A small sparkline.
        pts = []
        for k in range(9):
            xx = 22 + (w - 44) * k / 8.0
            yy = 68 + 18 + math.sin(k * 0.9 + idx) * 9
            pts.append(f"{xx:.1f} {yy:.1f}")
        d.path("M" + " L".join(pts), stroke=ACCENT_BRIGHT, width=1.4, opacity=0.7)
    else:
        # A single large glyph, cropped by the panel.
        word = "ORD", "SPC", "VEL", "LUX", "PTC", "FLX", "TRC", "GRD", "SUB"
        fam, weight = svg_font(TYPE_DISPLAY_XB)
        d.text(18, h - 26, word[idx % len(word)], 96, fam, weight, INK[2], opacity=0.30)


def _reveal_form(d: Doc, c) -> None:
    """The form underneath: a slowly turning iso structure.

    Held back until the panels are most of the way gone, so it reads as being
    uncovered rather than sitting behind the grid the whole time.
    """
    # Held until the last panels are well clear, so it reads as uncovered.
    u = seg(c.u, 0.74, 0.20, "out")
    if u <= 0:
        return
    rot = c.t * 0.5
    layers = 5
    for li in range(layers):
        z = (li - (layers - 1) / 2.0) * 66.0
        pts = []
        n = 7
        for k in range(n):
            a = k / n * math.tau + rot
            x = math.cos(a) * (168 - li * 8)
            y = math.sin(a) * (100 - li * 5)
            sx, sy = project_iso(x, y, z, 0.60, rot * 0.6, 1.0, W / 2, H / 2)
            pts.append(f"{sx:.1f} {sy:.1f}")
        pts.append(pts[0])
        col = ACCENT if li == layers // 2 else INK[3]
        d.path("M" + " L".join(pts), stroke=col, width=1.3, opacity=0.5 * u)

    glow(d, W / 2, H / 2, 300, ACCENT, 0.30 * u)


def _tf(x: float, y: float, rot: float, scale: float, w: float, h: float) -> str:
    """Panel transform: move to the panel's centre, then rotate and scale about it."""
    return (
        f"translate({_n(x + w / 2)} {_n(y + h / 2)}) rotate({_n(rot)}) "
        f"scale({_n(scale)}) translate({_n(-w / 2)} {_n(-h / 2)})"
    )


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
