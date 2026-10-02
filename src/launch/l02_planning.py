"""L2 PLANNING — projects and initiatives, per Linear's own feature taxonomy.

Linear's pitch for planning is "set the product direction with projects and
initiatives", so the beat shows a project overview: progress rollup, a timeline
of scoped work, and a health indicator. The craft is in the scrub — the timeline
is a real time axis that the playhead crosses, not a decorative bar chart.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, COOL, H, INK, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
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
    PRI_NONE,
    ROW_H,
    SIDEBAR_W,
    STATUS_DONE,
    STATUS_PROGRESS,
    STATUS_REVIEW,
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
    ("Projects", False),
    ("Views", False),
    ("Initiatives", False),
    ("Teams", True),
    ("Engineering", False),
    ("Design", False),
]

PROJECT = "Release 2.4"

# (label, start, end, progress) on a 0..1 time axis.
BARS = [
    ("Schema migration", 0.04, 0.30, 1.00),
    ("New issue editor", 0.16, 0.52, 0.82),
    ("Command palette v2", 0.30, 0.66, 0.45),
    ("Insights rebuild", 0.48, 0.84, 0.18),
    ("Mobile parity", 0.62, 0.97, 0.00),
]

MILESTONES = [(0.30, "Beta"), (0.66, "RC"), (0.97, "GA")]

ISSUES = [
    ("ENG-471", "Backfill relation rows", STATUS_DONE, "medium", "Ravi K", []),
    ("ENG-468", "Virtualise long lists", STATUS_REVIEW, "medium", "Ada L", ["Perf"]),
    ("ENG-465", "Editor: slash commands", STATUS_PROGRESS, "high", "Mira S", ["Feature"]),
    ("ENG-461", "Cycle burndown cache", STATUS_TODO, "low", "", []),
]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.24, "expo")
    head = seg(clock.u, 0.10, 0.26, "out")
    bars = seg(clock.u, 0.18, 0.42, "out")
    play = seg(clock.u, 0.34, 0.52, "inout")
    issues = seg(clock.u, 0.62, 0.32, "out")
    label = seg(clock.u, 0.04, 0.16, "out")

    glow(d, W / 2, H * 0.4, 820, ACCENT, 0.16 * seg(clock.u, 0, 0.4, "out"))

    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=3)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Projects", "Release 2.4", opacity=a,
                   accent_rule=seg(clock.u, 0.06, 0.26, "expo"))
            if head > 0:
                _project_head(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, head, play)
            if bars > 0:
                _timeline(d, APP_X + SIDEBAR_W, APP_Y + 250, APP_W - SIDEBAR_W, bars, play)
            if issues > 0:
                _issue_list(d, APP_X + SIDEBAR_W, APP_Y + 548, APP_W - SIDEBAR_W, issues)
    if label > 0:
        _beat_label(d, label, "02  ·  PLANNING")

    return d.render()


def _project_head(d: Doc, x: float, y: float, w: float, u: float, play: float) -> None:
    """Project title, health chip, and a progress rollup that counts up."""
    cy = y + TOPBAR_H + 42
    d.text(x + 26, cy, PROJECT, 22.0, *svg_font(TYPE_UI), INK[1])

    # Health chip, Linear's "on track" state.
    chip_w, chip_h = 92.0, 22.0
    cx1 = x + 26 + measure(TYPE_UI, 22.0, PROJECT) + 18
    d.rect(cx1, cy - 15, chip_w, chip_h, fill="rgba(76,201,240,0.12)", rx=11)
    d.circle(cx1 + 14, cy - 4, 3.4, fill=COOL)
    d.text(cx1 + 24, cy, "On track", 11.5, *svg_font(TYPE_UI_MED), INK[2])

    # Rollup: 42 of 68 issues done, counted up.
    ru = seg(play, 0.0, 0.55, "out")
    if ru > 0:
        done = int(42 * ru)
        label = f"{done} of 68 issues"
        d.text(x + w - 26 - measure(TYPE_UI_MED, 13.0, label), cy, label, 13.0,
               *svg_font(TYPE_UI_MED), INK[3])
        # Progress bar under the header.
        bw = 320.0
        bx = x + w - 26 - bw
        by = cy + 16
        d.rect(bx, by, bw, 3, fill="#23252a", rx=1.5)
        p = (done / 68.0) * ru
        d.rect(bx, by, bw * p, 3, fill=ACCENT_BRIGHT, rx=1.5)
    d.line(x + 26, cy + 40, x + w - 26, cy + 40, "#23252a", 1.0, opacity=u)


def _timeline(d: Doc, x: float, y: float, w: float, u: float, play: float) -> None:
    """Scoped work on a real time axis, with a playhead crossing it.

    Each bar's width is its actual span, so overlapping work reads as a schedule
    rather than a bar chart.
    """
    left = x + 190.0
    # Leave room on the right for the milestone labels, which are centred on
    # their tick and would otherwise clip at the frame edge.
    axis = w - 190.0 - 92.0
    n = len(BARS)
    row_h = 44.0

    # Month gridlines.
    for k in range(1, 6):
        gx = left + axis * k / 6.0
        d.line(gx, y, gx, y + n * row_h, "#1a1c1e", 1.0, opacity=0.9 * u)

    for i, (label, s0, s1, prog) in enumerate(BARS):
        local = seg(u, (i / max(n - 1, 1)) * 0.42, 0.58, "expo")
        if local <= 0:
            continue
        ry = y + i * row_h + row_h / 2
        d.text(x + 26, ry + 4, label, 12.5, *svg_font(TYPE_UI_MED), INK[2], opacity=local)

        bx = left + axis * s0
        bw = axis * (s1 - s0) * local
        by = ry - 4
        # Track, then the filled portion. Thin bars: Linear's timeline reads as
        # a schedule of hairlines, not a Gantt with slabs.
        d.rect(bx, by, axis * (s1 - s0), 8, fill="#16181a", rx=4, opacity=local)
        fill = bw * (0.15 + 0.85 * prog) * local
        col = ACCENT if prog >= 1.0 else (ACCENT_BRIGHT if prog > 0.2 else "#3e3e44")
        d.rect(bx, by, max(fill, 3), 8, fill=col, rx=4, opacity=local)

        # Milestone ticks under the axis.
    for mx, mlabel in MILESTONES:
        local = seg(u, 0.55, 0.3, "out")
        if local <= 0:
            continue
        gx = left + axis * mx
        d.line(gx, y, gx, y + n * row_h, COOL, 1.0, opacity=0.35 * local)
        d.text(gx, y + n * row_h + 20, mlabel, 10.5, *svg_font(TYPE_MONO), INK[4],
               anchor="middle", tracking=0.8, opacity=0.9 * local)

    # Playhead: a vertical rule with a head, crossing the whole schedule.
    if play > 0 and play < 1:
        hx = left + axis * (0.04 + 0.93 * play)
        d.line(hx, y - 14, hx, y + n * row_h + 8, INK[1], 1.2, opacity=0.55 * u)
        d.circle(hx, y - 14, 3.4, fill=INK[1], opacity=u)
        glow(d, hx, y - 14, 60, ACCENT_BRIGHT, 0.5 * u)


def _issue_list(d: Doc, x: float, y: float, w: float, u: float) -> None:
    """The issues underneath the project — the link between plan and build."""
    tfam, tweight = svg_font(TYPE_UI)
    d.text(x + 26, y, "IN THIS PROJECT", 10.5, tfam, tweight, INK[4], tracking=0.9, opacity=0.9 * u)
    ry = y + 14
    n = len(ISSUES)
    for i, row in enumerate(ISSUES):
        local = seg(u, (i / max(n - 1, 1)) * 0.40, 0.6, "out")
        if local <= 0:
            continue
        with d.group(transform=f"translate(0 {_n((1 - local) * 14)})"):
            issue_row(d, x, ry + i * ROW_H, w, *row, opacity=local)
            row_hairline(d, x, ry + (i + 1) * ROW_H, w, opacity=local * 0.6)


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
