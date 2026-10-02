"""L7 INSIGHTS — analytics over any stream of work.

Linear's Insights is "instant analytics for any stream of work", and the beat
that follows agents should be the one that looks *backward*: what shipped, how
fast, where the time went. So the scene is calm by design — the motion is in
data appearing, not in the frame moving.

The craft is the chart set: a stacked throughput column chart, a rolling trend
line, and a breakdown bar, all drawn from the same numbers so they agree.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, COOL, H, INK, TYPE_DISPLAY, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
from easing import seg
from layout import measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    ROW_H,
    SIDEBAR_W,
    TOPBAR_H,
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
    ("Insights", False),
    ("Teams", True),
    ("Engineering", False),
]

# 12 weeks of throughput. `shipped` and `carried` are stacked; the trend line
# runs over the total. Numbers are fixed so every chart agrees.
WEEKS = [
    (18, 6), (22, 5), (17, 9), (25, 4), (28, 7),
    (24, 8), (31, 5), (29, 6), (34, 4), (30, 7),
    (38, 5), (41, 3),
]

# Time-in-status breakdown, which is where Insights gets interesting.
BREAKDOWN = [
    ("In Progress", 0.44, ACCENT),
    ("In Review", 0.21, COOL),
    ("Todo", 0.19, "#62666d"),
    ("Backlog", 0.16, "#3e3e44"),
]

STATS = [("Cycle time", "2.4d", "-0.6d"), ("Throughput", "41/wk", "+7"), ("Efficiency", "94%", "+3%")]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.20, "expo")
    head = seg(clock.u, 0.08, 0.22, "out")
    cols = seg(clock.u, 0.16, 0.44, "out")
    trend = seg(clock.u, 0.46, 0.30, "circ")
    bd = seg(clock.u, 0.62, 0.24, "out")
    label = seg(clock.u, 0.04, 0.16, "out")

    glow(d, W / 2, H * 0.42, 800, ACCENT, 0.13 * seg(clock.u, 0, 0.4, "out"))

    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=6)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Insights", "Last 12 weeks",
                   opacity=a, accent_rule=seg(clock.u, 0.05, 0.22, "expo"))
            if head > 0:
                _stat_row(d, APP_X + SIDEBAR_W + 26, APP_Y + TOPBAR_H + 22,
                          APP_W - SIDEBAR_W - 52, head)
            if cols > 0:
                _throughput(d, APP_X + SIDEBAR_W + 26, APP_Y + 208,
                            APP_W - SIDEBAR_W - 52, cols, trend)
            if bd > 0:
                _breakdown(d, APP_X + SIDEBAR_W + 26, APP_Y + 588,
                           APP_W - SIDEBAR_W - 52, bd)
    if label > 0:
        _beat_label(d, label, "07  ·  INSIGHTS")

    return d.render()


def _stat_row(d: Doc, x: float, y: float, w: float, u: float) -> None:
    """Three headline figures, each counting up to its final value."""
    n = len(STATS)
    cw = (w - 24 * (n - 1)) / n
    for i, (label, value, delta) in enumerate(STATS):
        local = seg(u, (i / max(n - 1, 1)) * 0.4, 0.6, "out")
        if local <= 0:
            continue
        cx = x + i * (cw + 24)
        d.rect(cx, y, cw, 96, fill="#101112", rx=8, opacity=local)
        d.rect(cx, y, cw, 96, fill="none", stroke="rgba(255,255,255,0.06)", stroke_width=1.0,
               rx=8, opacity=local)
        d.text(cx + 20, y + 30, label.upper(), 10.0, *svg_font(TYPE_UI), INK[4],
               tracking=0.9, opacity=0.9 * local)
        # Value scales up slightly as it lands, so it reads as arriving.
        vs = 1.0 + (1.0 - local) * 0.10
        d.text(cx + 20, y + 66, value, 30.0, *svg_font(TYPE_DISPLAY), INK[1], opacity=local)
        d.text(cx + 20 + measure(TYPE_DISPLAY, 30.0, value) * vs + 12, y + 66, delta, 13.0,
               *svg_font(TYPE_UI_MED), "#4cb782", opacity=local)


def _throughput(d: Doc, x: float, y: float, w: float, u: float, trend: float) -> None:
    """Stacked weekly columns with a rolling total over the top."""
    left = x + 54.0
    right = x + w - 20.0
    top = y
    bottom = y + 236.0
    pw = right - left
    ph = bottom - top

    d.text(x, y - 14, "THROUGHPUT", 10.5, *svg_font(TYPE_UI), INK[4], tracking=0.9, opacity=u)

    peak = max(s + c for s, c in WEEKS) * 1.15
    # Horizontal gridlines with value labels.
    for k in range(5):
        gy = bottom - ph * k / 4.0
        d.line(left, gy, right, gy, "#1a1c1e", 1.0, opacity=0.85 * u)
        val = int(peak * k / 4.0)
        d.text(left - 12, gy + 4, f"{val}", 10.0, *svg_font(TYPE_MONO), INK[4],
               anchor="end", opacity=0.75 * u)

    n = len(WEEKS)
    gap = 0.34
    bw = pw / n * (1.0 - gap)
    totals = []
    for i, (shipped, carried) in enumerate(WEEKS):
        local = seg(u, (i / max(n - 1, 1)) * 0.5, 0.5, "expo")
        if local <= 0:
            totals.append(None)
            continue
        bx = left + pw * (i + 0.5) / n - bw / 2
        sh = ph * (shipped / peak) * local
        ch = ph * (carried / peak) * local
        # Carried sits on top of shipped, in a muted tone: the stacked read is
        # "this much went out, this much rolled over".
        d.rect(bx, bottom - sh, bw, sh, fill=ACCENT, rx=2, opacity=u)
        d.rect(bx, bottom - sh - ch, bw, ch, fill="#2f3446", rx=2, opacity=u)
        totals.append(bottom - sh - ch)

    # Trend line over the column totals.
    pts = [(left + pw * (i + 0.5) / n, t) for i, t in enumerate(totals) if t is not None]
    if len(pts) > 1 and trend > 0:
        shown = int(len(pts) * trend) + 1
        seg_pts = pts[:shown]
        poly = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in seg_pts)
        length = sum(
            math.hypot(seg_pts[i + 1][0] - seg_pts[i][0], seg_pts[i + 1][1] - seg_pts[i][1])
            for i in range(len(seg_pts) - 1)
        )
        drawn = length * min(trend * 3.2, 1.0)
        d.path(poly, stroke=INK[1], width=1.8, cap="round", join="round",
               dash=f"{drawn:.1f} {length + 20:.1f}", opacity=0.85 * u)
        # Leading dot.
        hx, hy = seg_pts[-1]
        if trend > 0.05:
            d.circle(hx, hy, 3.2, fill=INK[1], opacity=u)
            glow(d, hx, hy, 46, ACCENT_BRIGHT, 0.4 * u)

    # Axis labels: first and last week.
    for i in (0, n - 1):
        d.text(left + pw * (i + 0.5) / n, bottom + 18, f"W{i + 1}", 10.0,
               *svg_font(TYPE_MONO), INK[4], anchor="middle", opacity=0.8 * u)


def _breakdown(d: Doc, x: float, y: float, w: float, u: float) -> None:
    """A single stacked bar of time-in-status, with a legend.

    One bar rather than four: the proportion is the message, and four bars would
    need a second axis to say the same thing.
    """
    d.text(x, y - 14, "TIME IN STATUS", 10.5, *svg_font(TYPE_UI), INK[4],
           tracking=0.9, opacity=0.9 * u)

    bar_y = y + 4
    bar_h = 12.0
    bar_w = w - 300.0
    cx = x
    for i, (label, frac, col) in enumerate(BREAKDOWN):
        local = seg(u, i * 0.12, 0.5, "out")
        if local <= 0:
            continue
        seg_w = bar_w * frac * local
        d.rect(cx, bar_y, seg_w, bar_h, fill=col, rx=2, opacity=u)
        cx += seg_w

    # Legend laid out sequentially rather than positioned from cumulative
    # fractions, so entries can never overlap however the segments divide.
    lx = x
    for label, frac, col in BREAKDOWN:
        local = seg(u, 0.25, 0.4, "out")
        if local <= 0:
            continue
        d.rect(lx, bar_y + 30, 8, 8, fill=col, rx=2, opacity=local)
        d.text(lx + 14, bar_y + 38, label, 11.0, *svg_font(TYPE_UI_MED), INK[3], opacity=local)
        pct = f"{int(frac * 100)}%"
        d.text(lx + 14, bar_y + 56, pct, 11.0, *svg_font(TYPE_MONO), INK[4], opacity=local)
        lx += 14 + max(measure(TYPE_UI_MED, 11.0, label), measure(TYPE_MONO, 11.0, pct)) + 46


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)
