"""L8 LAUNCH — the close.

The app recedes, the statement lands, and the lockup holds. Everything the film
has shown is already established by this point, so the last beat's job is to stop
cleanly rather than to add anything.

The layering: the window falls away, the wordmark draws itself, the statement
lands, and `linear.app` sits under a rule. Then a long, nearly still hold — that
stillness is what makes the film feel finished instead of cut off.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY_XB, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from stock import clamp
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    SIDEBAR_W,
    TOPBAR_H,
    window_chrome,
)

STATEMENT = "Plan the present."
STATEMENT_2 = "Build the future."
SIGNATURE = "linear.app"

# The mark, built from scratches rather than any asset: a rounded square with a
# rising diagonal form, drawn as strokes so it can trace itself on.
MARK_RADIUS = 0.22


def draw(clock) -> str:
    d = Doc()
    recede = seg(clock.u, 0.0, 0.30, "inout")
    mark = seg(clock.u, 0.16, 0.30, "expo")
    line1 = seg(clock.u, 0.34, 0.22, "out")
    line2 = seg(clock.u, 0.46, 0.22, "out")
    sig = seg(clock.u, 0.66, 0.22, "expo")
    label = seg(clock.u, 0.04, 0.14, "out")

    _backdrop(d, clock, recede)
    _app_receding(d, recede)
    if mark > 0:
        _mark(d, clock, mark, recede)
    if line1 > 0:
        _statement(d, statement_line(STATEMENT), clock, line1, H * 0.615)
    if line2 > 0:
        _statement(d, statement_line(STATEMENT_2), clock, line2, H * 0.735, accent=True)
    if sig > 0:
        _signature(d, sig)
    if sig > 0.3:
        _disclaimer(d, seg(sig, 0.3, 0.5, "out"))
    if label > 0:
        _beat_label(d, label, "08  ·  RELEASE")

    return d.render()


def statement_line(text: str) -> str:
    return text


def _backdrop(d: Doc, c, recede: float) -> None:
    """The wash settles to a single centred light as the app goes."""
    u = seg(c.u, 0.0, 0.5, "out")
    if u > 0:
        # Pulls in and dims as the frame empties.
        r = 900 - 260 * recede
        glow(d, W / 2, H * 0.44, r, ACCENT, (0.20 - 0.06 * recede) * u)
    # A quiet grid, breathing.
    g = seg(c.u, 0.10, 0.4, "out")
    if g > 0:
        breathe = 1.0 + math.sin(c.t * 0.8) * 0.007
        lines = []
        for i in range(1, 10):
            x = W * i / 10.0
            lines.append(f"M{x} {H * 0.5 - 340 * g * breathe} L{x} {H * 0.5 + 340 * g * breathe}")
        for i in range(1, 7):
            y = H * i / 7.0
            lines.append(f"M{W * 0.5 - 720 * g * breathe} {y} L{W * 0.5 + 720 * g * breathe} {y}")
        d.path(" ".join(lines), stroke=INK[4], width=1.0, opacity=0.09 * g)


def _app_receding(d: Doc, u: float) -> None:
    """The app lifts and fades, so the film closes on the brand not the UI."""
    if u <= 0.001:
        return
    dx, dy = 60 * u, -70 * u
    fade = 1.0 - u
    if fade <= 0.01:
        return
    with d.group(transform=f"translate({_n(dx)} {_n(dy)})", opacity=(1.0 - u) ** 1.6):
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=1.0)
        d.rect(APP_X, APP_Y, SIDEBAR_W, APP_H, fill="#0b0c0d")
        d.rect(APP_X + SIDEBAR_W, APP_Y + TOPBAR_H, APP_W - SIDEBAR_W, APP_H - TOPBAR_H,
               fill="#0f1011")
        # A few rows, to keep it reading as the product rather than a grey box.
        for i in range(7):
            y = APP_Y + TOPBAR_H + 26 + i * 36
            d.rect(APP_X + SIDEBAR_W + 30, y - 6, 60, 8, fill="#23252a", rx=2)
            d.rect(APP_X + SIDEBAR_W + 110, y - 6, 260 - i * 18, 8, fill="#1b1d1f", rx=2)
            d.rect(APP_X + SIDEBAR_W + 30, y + 8, APP_W - SIDEBAR_W - 90, 1, fill="#18191a")


def _mark(d: Doc, c, u: float, recede: float) -> None:
    """The mark traces itself on, then breathes."""
    size = 132.0
    cx, cy = W / 2, H * 0.335
    pulse = 0.5 + 0.5 * math.sin(c.t * 1.0)

    # Container: eases in ahead of the glyph.
    box_u = min(u / 0.5, 1.0)
    if box_u > 0:
        s = 0.92 + 0.08 * box_u
        r = size * MARK_RADIUS
        d.add(
            f'<g transform="translate({_n(cx - size / 2 + size / 2)} {_n(cy)}) '
            f'scale({_n(s)}) translate({_n(-size / 2)} {_n(-size / 2)})">'
            f'<path d="{_rounded_square(size, r)}" '
            f'fill="rgba(255,255,255,{0.05 * box_u:.3f})" '
            f'stroke="rgba(255,255,255,0.16)" stroke-width="1.2"/></g>'
        )

    # The inner form: two wedges that trace on in sequence.
    glyph_u = max(0.0, (u - 0.35) / 0.65)
    if glyph_u > 0:
        for i, (path, approx) in enumerate(_wedge_paths(size)):
            local = min(max((glyph_u - i * 0.42) / 0.72, 0.0), 1.0)
            if local <= 0:
                continue
            shown = approx * local
            col = ACCENT_BRIGHT if i == 0 else INK[1]
            d.add(
                f'<g transform="translate({_n(cx - size / 2)} {_n(cy - size / 2)})">'
                f'<path d="{path}" fill="none" stroke="{col}" '
                f'stroke-width="{_n(size * 0.078)}" stroke-linejoin="round" stroke-linecap="round" '
                f'stroke-dasharray="{_n(approx)} {_n(approx)}" '
                f'stroke-dashoffset="{_n(approx - shown)}" '
                f'opacity="{_n(0.6 + 0.4 * local)}"/></g>'
            )

    if glyph_u >= 1.0:
        glow(d, cx, cy, size * 1.15, ACCENT, 0.12 + 0.05 * pulse)


def _rounded_square(size: float, r: float) -> str:
    """A rounded square as an explicit path, so it can be dash-animated later."""
    s = size
    return (
        f"M{_n(r)} 0 L{_n(s - r)} 0 Q{_n(s)} 0 {_n(s)} {_n(r)} "
        f"L{_n(s)} {_n(s - r)} Q{_n(s)} {_n(s)} {_n(s - r)} {_n(s)} "
        f"L{_n(r)} {_n(s)} Q0 {_n(s)} 0 {_n(s - r)} "
        f"L0 {_n(r)} Q0 0 {_n(r)} 0 Z"
    )


def _wedge_paths(size: float) -> list[tuple[str, float]]:
    """The inner form, as (closed path, approximate perimeter)."""
    s = size
    main = (
        f"M{_n(s * 0.20)} {_n(s * 0.78)} L{_n(s * 0.56)} {_n(s * 0.78)} "
        f"L{_n(s * 0.84)} {_n(s * 0.34)} L{_n(s * 0.50)} {_n(s * 0.34)} Z"
    )
    counter = (
        f"M{_n(s * 0.20)} {_n(s * 0.52)} L{_n(s * 0.44)} {_n(s * 0.52)} "
        f"L{_n(s * 0.50)} {_n(s * 0.34)} L{_n(s * 0.20)} {_n(s * 0.34)} Z"
    )
    return [(main, s * 1.02), (counter, s * 0.58)]


def _statement(d: Doc, text: str, c, u: float, base: float, accent: bool = False) -> None:
    """A statement line, per-glyph, settling into tight tracking."""
    fam, weight = svg_font(TYPE_DISPLAY_XB)
    size = 78.0
    tight, open_ = -0.052 * size, -0.018 * size
    tracking = tight + (open_ - tight) * seg(u, 0.15, 0.85, "out")
    gl = glyphs(TYPE_DISPLAY_XB, size, text, tracking)
    total = measure(TYPE_DISPLAY_XB, size, text, tracking)
    x0 = W / 2 - total / 2

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        local = seg(u, (i / max(n - 1, 1)) * 0.40, 0.60, "expo")
        if local <= 0:
            continue
        rise = (1.0 - local) * 22
        bl = (1.0 - local) * 4.5
        fid = d.blur(bl) if bl > 0.4 else None
        col = ACCENT_BRIGHT if accent else INK[1]
        d.text(x0 + dx, base + rise, ch, size, fam, weight, col, opacity=local, filt=fid)


def _signature(d: Doc, u: float) -> None:
    """A rule draws out, then `linear.app` lands under it."""
    base = H * 0.855
    fam, weight = svg_font(TYPE_UI)
    size = 26.0
    text = SIGNATURE
    total = measure(TYPE_UI, size, text, -0.3)
    x0 = W / 2 - total / 2

    # Rule from the centre out.
    ru = seg(u, 0.0, 0.5, "expo")
    if ru > 0:
        d.line(W / 2 - (total / 2 + 44) * ru, base - 34,
               W / 2 + (total / 2 + 44) * ru, base - 34, ACCENT, 1.6, opacity=0.75 * u)

    su = seg(u, 0.28, 0.5, "out")
    if su > 0:
        d.text(x0, base, text, size, fam, weight, INK[2], tracking=-0.3, opacity=su)
        glow(d, W / 2, base - 12, 200 * su, ACCENT, 0.16 * su)


def _disclaimer(d: Doc, u: float) -> None:
    """The unofficial-concept line.

    Small and quiet, but it has to be on screen and legible: the film reconstructs
    a product's interface and uses a mark in its likeness, which is only
    defensible as a clearly-labelled spec piece.
    """
    mfam, mweight = svg_font(TYPE_MONO)
    text = "UNOFFICIAL CONCEPT PIECE  ·  NOT AFFILIATED WITH LINEAR"
    fs = 11.0
    tracking = 2.4
    total = measure(TYPE_MONO, fs, text, tracking)
    d.text(W / 2 - total / 2, H - 64, text, fs, mfam, mweight, INK[4],
           tracking=tracking, opacity=0.6 * u)


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
