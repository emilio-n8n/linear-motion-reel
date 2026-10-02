"""L1 PROMISE — the film's cold open.

The window assembles out of nothing, the workspace fills with real work, and the
positioning lands. Nothing here is invented UI: every element comes from ui.py,
so the opening is already the product rather than a logo card.

Stated once, then handed to L2.
"""

from __future__ import annotations

from brand import ACCENT, ACCENT_BRIGHT, CANVAS, H, INK, TYPE_DISPLAY, TYPE_DISPLAY_XB, TYPE_MONO, TYPE_UI, W

CANVAS_DEEP = CANVAS
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from stock import clamp
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    PRI_LOW,
    PRI_MEDIUM,
    PRI_NONE,
    ROW_H,
    filler_rows,
    SIDEBAR_W,
    STATUS_DONE,
    STATUS_PROGRESS,
    STATUS_TODO,
    TOPBAR_H,
    issue_row,
    row_hairline,
    sidebar,
    topbar,
    window_chrome,
)

NAV = [
    ("Inbox", False),
    ("My Issues", False),
    ("Workspace", True),
    ("Planning", False),
    ("Projects", False),
    ("Views", False),
    ("Teams", True),
    ("Engineering", False),
    ("Design", False),
    ("Product", False),
]

# The work the workspace already contains. Real titles, real key format.
SEED_ROWS = [
    ("ENG-482", "Command palette fuzzy match", STATUS_PROGRESS, "high", "Ada L", ["Feature"]),
    ("ENG-481", "Batch edit via multi-select", STATUS_TODO, "urgent", "", ["Feature"]),
    ("ENG-479", "Reduce cold start on boot", STATUS_DONE, "medium", "Ravi K", []),
    ("ENG-477", "Webhook retry backoff", STATUS_TODO, "low", "", ["Bug"]),
    ("ENG-474", "Cycle rollup on project close", STATUS_TODO, "medium", "Mira S", []),
]

STATEMENT = "The system for product development"


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.02, 0.30, "expo")
    rows = seg(clock.u, 0.18, 0.34, "out")
    statement = seg(clock.u, 0.58, 0.24, "out")
    label = seg(clock.u, 0.34, 0.20, "out")

    _backdrop(d, clock)
    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        if chrome > 0.55:
            a = clamp((chrome - 0.55) / 0.45)
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=4)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Engineering", "ENG-482", opacity=a,
                   accent_rule=seg(clock.u, 0.10, 0.30, "expo"))
    if rows > 0:
        _rows(d, clock, rows)
    if statement > 0:
        _statement(d, statement)
    if label > 0:
        _beat_label(d, label, "01  ·  OVERVIEW")

    return d.render()


def _backdrop(d: Doc, c) -> None:
    """A slow accent wash behind the window, so the frame is never flat black."""
    u = seg(c.u, 0.0, 0.5, "out")
    if u <= 0:
        return
    glow(d, W / 2, H * 0.42, 900, ACCENT, 0.20 * u)
    glow(d, W * 0.78, H * 0.74, 520, ACCENT_BRIGHT, 0.10 * u)


def _rows(d: Doc, c, u: float) -> None:
    """Seed rows, staggered so the list fills like data arriving."""
    x = APP_X + SIDEBAR_W
    w = APP_W - SIDEBAR_W
    y0 = APP_Y + TOPBAR_H + 8
    n = len(SEED_ROWS)
    for i, row in enumerate(SEED_ROWS):
        local = seg(u, (i / max(n - 1, 1)) * 0.44, 0.56, "out")
        if local <= 0:
            continue
        y = y0 + i * ROW_H
        # Rows slide in from the left by a few px and fade, so it reads as a
        # populated list rather than a reveal.
        slide = (1.0 - local) * -18
        with d.group(transform=f"translate({_n(slide)} 0)"):
            issue_row(d, x, y, w, *row, opacity=local)
            row_hairline(d, x, y + ROW_H, w, opacity=local * 0.8)

    # Filler, so the list fills the window instead of trailing off mid-panel.
    extra = filler_rows(len(SEED_ROWS) + 2, 9)
    m = len(extra)
    for i, row in enumerate(extra):
        local = seg(u, 0.40 + (i / max(m - 1, 1)) * 0.34, 0.66, "out")
        if local <= 0:
            continue
        y = y0 + (n + i) * ROW_H
        slide = (1.0 - local) * -18
        with d.group(transform=f"translate({_n(slide)} 0)"):
            issue_row(d, x, y, w, *row, opacity=local * 0.92)
            row_hairline(d, x, y + ROW_H, w, opacity=local * 0.7)


def _statement(d: Doc, u: float) -> None:
    """The positioning line, per-glyph, over a dimmed app.

    Sits on a scrim so it stays legible over the window without hiding the
    product entirely.
    """
    # A strong scrim, then a soft band behind the text itself. The list has to
    # stop competing with the statement without the frame reading as a blackout.
    d.rect(0, 0, W, H, fill="#08090a", opacity=0.90 * u)
    band = d.linear_gradient(
        [(0.0, CANVAS_DEEP, 0.0), (0.5, CANVAS_DEEP, 0.85), (1.0, CANVAS_DEEP, 0.0)],
        x1=0, y1=H / 2 - 190, x2=0, y2=H / 2 + 190, units="userSpaceOnUse",
    )
    d.rect(0, H / 2 - 190, W, 380, fill=f"url(#{band})", opacity=u)

    fam, weight = svg_font(TYPE_DISPLAY_XB)
    # Sized so the line sits inside the window with a margin rather than running
    # to the frame edge.
    size = min(86.0, (APP_W - 200) / (measure(TYPE_DISPLAY_XB, 100.0, STATEMENT, -3.0) / 100.0))
    tight, open_ = -0.048 * size, -0.016 * size
    tracking = tight + (open_ - tight) * seg(u, 0.15, 0.85, "out")
    gl = glyphs(TYPE_DISPLAY_XB, size, STATEMENT, tracking)
    total = measure(TYPE_DISPLAY_XB, size, STATEMENT, tracking)
    x0 = W / 2 - total / 2
    base = H / 2 + cap_height(TYPE_DISPLAY_XB, size) / 2

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        local = seg(u, (i / max(n - 1, 1)) * 0.40, 0.60, "expo")
        if local <= 0:
            continue
        rise = (1.0 - local) * 26
        bl = (1.0 - local) * 5
        fid = d.blur(bl) if bl > 0.4 else None
        d.text(x0 + dx, base + rise, ch, size, fam, weight, INK[1], opacity=local, filt=fid)

    # A rule that draws to the statement's measured width.
    ru = seg(u, 0.30, 0.55, "expo")
    if ru > 0:
        d.line(x0, base + 54, x0 + total * ru, base + 54, ACCENT, 2.0, opacity=0.8 * u)


def _beat_label(d: Doc, u: float, text: str) -> None:
    """The corner slug naming the beat — the spine of a launch film."""
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
