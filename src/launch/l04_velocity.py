"""L4 VELOCITY — cycles and the pace of shipping.

Linear's build story is "issue tracking and cycle planning", and the cycle is
where that becomes measurable. The beat shows a cycle closing: a burndown that
draws itself down to zero, a velocity figure that ticks up, and completed issues
striking off.

The draw-on is the craft — the burndown is a real polyline revealed by
progressive length, not a fade.
"""

from __future__ import annotations

import math

from brand import (
    ACCENT,
    ACCENT_BRIGHT,
    COOL,
    H,
    INK,
    TYPE_DISPLAY,
    TYPE_MONO,
    TYPE_UI,
    TYPE_UI_MED,
    TYPE_UI_REG,
    W,
)
from easing import seg
from layout import measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    PRI_MEDIUM,
    ROW_H,
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
    ("Cycles", False),
    ("Teams", True),
    ("Engineering", False),
    ("Design", False),
]

CYCLE = "Cycle 24"

# Ideal burndown for a 14-day cycle: a straight line from scope to zero.
DAYS = 14
SCOPE = 68.0

# Issues closing during the beat, in the order they land.
CLOSED = [
    ("ENG-479", "Reduce cold start on boot", "Ravi K", "Perf"),
    ("ENG-468", "Virtualise long lists", "Ada L", "Perf"),
    ("ENG-461", "Cycle burndown cache", "Ravi K", "API"),
    ("ENG-455", "Idempotency keys on mutations", "Ada L", "API"),
    ("ENG-444", "Keyboard map: custom bindings", "Ada L", "Feature"),
]

STILL_OPEN = [
    ("ENG-465", "Editor: slash commands", STATUS_PROGRESS, "Mira S", ["Feature"]),
    ("ENG-477", "Webhook retry backoff", STATUS_TODO, "", ["Bug"]),
    ("ENG-463", "Cursor position across reloads", STATUS_TODO, "Ravi K", []),
    ("ENG-451", "Reduce sidebar jank on nav", STATUS_TODO, "", ["Perf"]),
]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.22, "expo")
    head = seg(clock.u, 0.08, 0.24, "out")
    drawline = seg(clock.u, 0.16, 0.52, "circ")
    closes = seg(clock.u, 0.30, 0.50, "out")
    label = seg(clock.u, 0.04, 0.16, "out")

    glow(d, W / 2, H * 0.42, 780, ACCENT, 0.15 * seg(clock.u, 0, 0.4, "out"))

    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=5)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Cycles", CYCLE, opacity=a,
                   accent_rule=seg(clock.u, 0.05, 0.24, "expo"))
            if head > 0:
                _cycle_head(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, head, closes)
            if drawline > 0:
                _burndown(d, APP_X + SIDEBAR_W, APP_Y + 218, APP_W - SIDEBAR_W, drawline)
            if closes > 0:
                _lists(d, APP_X + SIDEBAR_W, APP_Y + 566, APP_W - SIDEBAR_W, closes)
    if label > 0:
        _beat_label(d, label, "04  ·  CYCLES")

    return d.render()


def _cycle_head(d: Doc, x: float, y: float, w: float, u: float, closes: float) -> None:
    """Cycle title, progress, and a velocity figure that counts up as issues land."""
    cy = y + TOPBAR_H + 44
    d.text(x + 26, cy, CYCLE, 22.0, *svg_font(TYPE_UI), INK[1], opacity=u)

    # Day counter.
    day = int(14 * (0.28 + 0.72 * closes))
    days = f"Day {min(day, DAYS)} of {DAYS}"
    d.text(x + 26 + measure(TYPE_UI, 22.0, CYCLE) + 16, cy, days, 12.5,
           *svg_font(TYPE_UI_MED), INK[4], opacity=u)

    # Velocity: the number that makes a cycle worth looking at.
    vel = int((31 + len(CLOSED) * 3.4) * (0.35 + 0.65 * seg(closes, 0.1, 0.8, "out")))
    vx = x + w - 26
    vlabel = "velocity"
    vw = measure(TYPE_UI_MED, 13.0, vlabel)
    d.text(vx - vw, cy, vlabel, 13.0, *svg_font(TYPE_UI_MED), INK[4], opacity=u)

    vnum = f"{vel}"
    numw = measure(TYPE_DISPLAY, 34.0, vnum)
    d.text(vx - numw, cy + 40, vnum, 34.0, *svg_font(TYPE_DISPLAY), INK[1], opacity=u)

    # A one-day delta, green when up — the small signal that closes a cycle.
    du = seg(closes, 0.35, 0.5, "out")
    if du > 0:
        d.text(vx - numw - 54, cy + 40, "+4", 14.0, *svg_font(TYPE_UI), "#4cb782", opacity=du)

    d.line(x + 26, cy + 56, x + w - 26, cy + 56, "#23252a", 1.0, opacity=u)


def frac_at(u: float) -> float:
    """Remaining scope at draw progress `u`, matching the burndown's own curve."""
    t = clamp(u)
    return (1.0 - t) ** 1.15


def _burndown(d: Doc, x: float, y: float, w: float, u: float) -> None:
    """The cycle burndown, drawn on.

    Revealed by trimming the polyline's drawn length rather than clipping a
    group, so the stroke ends on a real vertex instead of a hard vertical edge.
    """
    left = x + 92.0
    right = x + w - 56.0
    top = y
    bottom = y + 214.0
    pw = right - left
    ph = bottom - top

    # Frame and gridlines.
    d.text(x + 26, y + 4, "BURNDOWN", 10.5, *svg_font(TYPE_UI), INK[4], tracking=0.9, opacity=u)
    for k in range(5):
        gy = top + ph * k / 4.0
        d.line(left, gy, right, gy, "#1a1c1e", 1.0, opacity=0.85 * u)
    d.line(left, top, left, bottom, "#23252a", 1.0, opacity=u)
    d.line(left, bottom, right, bottom, "#23252a", 1.0, opacity=u)

    # Ideal line: straight from scope to zero.
    ideal = f"M{left:.1f} {top:.1f} L{right:.1f} {bottom:.1f}"
    d.path(ideal, stroke="#3e3e44", width=1.2, dash="4 4", opacity=0.7 * u)
    d.text(right - 96, top + 16, "ideal", 10.0, *svg_font(TYPE_MONO), INK[4], opacity=0.7 * u)

    # Actual. A burndown descends: y goes top -> bottom as scope is closed, so
    # `frac` is the *remaining* fraction and is subtracted from the top.
    pts = []
    for day in range(DAYS + 1):
        t = day / DAYS
        # Remaining fraction of scope. The exponent makes the early days burn
        # slowly, which is how a real cycle actually goes.
        frac = (1.0 - t) ** 1.15
        # Runs a touch above the ideal (i.e. slower) until the last third.
        lag = 0.16 * math.sin(t * math.pi) * (1.0 - t)
        pts.append((left + pw * t, top + ph * (1.0 - frac + lag)))

    poly = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    # Total path length, for the draw-on trim.
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    shown = total * u

    gid = d.linear_gradient(
        [(0.0, ACCENT, 0.95), (0.7, ACCENT_BRIGHT, 0.95), (1.0, COOL, 1.0)],
        x1=left, y1=top, x2=right, y2=bottom, units="userSpaceOnUse",
    )
    d.path(
        poly, stroke=f"url(#{gid})", width=2.4, cap="round", join="round",
        dash=f"{shown:.1f} {total + 10:.1f}", opacity=u,
    )

    # Soft companion for a little glow under the line.
    d.path(
        poly, stroke=f"url(#{gid})", width=9.0, cap="round", join="round",
        dash=f"{shown:.1f} {total + 10:.1f}", opacity=0.10 * u, filt=d.blur(12),
    )

    # The head, with a value callout.
    hx, hy = pts[min(int(u * DAYS), DAYS)]
    d.circle(hx, hy, 3.6, fill=INK[1], opacity=u)
    glow(d, hx, hy, 64, ACCENT_BRIGHT, 0.45 * u)
    # Remaining scope tracks the drawn curve, so the callout agrees with the line.
    remaining = int(SCOPE * frac_at(u))
    rlab = f"{remaining} open"
    d.text(hx + 12, hy - 10, rlab, 11.0, *svg_font(TYPE_MONO), INK[3], tracking=0.4, opacity=u)

    # Day ticks.
    for day in (0, 7, DAYS):
        tx = left + pw * day / DAYS
        d.text(tx, bottom + 18, f"{day}", 10.0, *svg_font(TYPE_MONO), INK[4],
               anchor="middle", opacity=0.8 * u)


def _lists(d: Doc, x: float, y: float, w: float, u: float) -> None:
    """Closed issues strike off; open ones stay, so the cycle's balance is visible."""
    half = (w - 48) / 2

    # Closed column.
    tfam, tweight = svg_font(TYPE_UI)
    d.text(x + 26, y, "COMPLETED", 10.5, tfam, tweight, INK[4], tracking=0.9, opacity=0.9 * u)
    n = len(CLOSED)
    for i, (ident, title, who, label) in enumerate(CLOSED):
        local = seg(u, (i / max(n - 1, 1)) * 0.56, 0.44, "expo")
        if local <= 0:
            continue
        ry = y + 16 + i * ROW_H
        row_op = 1.0
        # Title strikes through as it closes.
        strike = seg(local, 0.5, 0.4, "out")
        mfam, mweight = svg_font(TYPE_MONO)
        d.text(x + 26, ry + 16, ident, 11.0, mfam, mweight, INK[4], tracking=0.3, opacity=local)
        tw = measure(TYPE_UI_REG, 12.5, title)
        d.text(x + 100, ry + 16, title, 12.5, *svg_font(TYPE_UI_MED), INK[2], opacity=local)
        if strike > 0:
            d.line(x + 100, ry + 12, x + 100 + tw * strike, ry + 12, INK[4], 1.0, opacity=local)
        if local >= 1.0:
            # The tick sits at the row's right edge, so the column of closed
            # issues has a visible terminator.
            done_tick(d, x + 26 + half - 52, ry + 12, local)
        row_hairline(d, x + 26, ry + ROW_H, half - 40, opacity=0.4 * local)

    # Open column.
    ox = x + half + 24
    d.text(ox + 26, y, "STILL OPEN", 10.5, tfam, tweight, INK[4], tracking=0.9, opacity=0.9 * u)
    m = len(STILL_OPEN)
    for i, (ident, title, status, who, labels) in enumerate(STILL_OPEN):
        local = seg(u, 0.30 + (i / max(m - 1, 1)) * 0.40, 0.6, "out")
        if local <= 0:
            continue
        issue_row(d, ox, y + 16 + i * ROW_H, half, ident, title, status, PRI_MEDIUM, who, labels,
                  opacity=local)
        row_hairline(d, ox, y + 16 + (i + 1) * ROW_H, half, opacity=local * 0.5)


def done_tick(d: Doc, cx: float, cy: float, u: float) -> None:
    """A compact done tick, placed inline rather than via the row primitive."""
    d.circle(cx, cy, 7, fill=ACCENT_BRIGHT, opacity=0.95 * u)
    d.path(
        f"M{cx - 2.6:.1f} {cy:.1f} L{cx - 0.6:.1f} {cy + 2.2:.1f} L{cx + 2.8:.1f} {cy - 2.4:.1f}",
        stroke="#08090a", width=1.7, cap="round", join="round", opacity=u,
    )


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)
