"""L6 AGENTS — Linear's current front foot.

Their site leads with "purpose-built for planning and building products with AI
agents", so this is the beat that matters most for the film's relevance, and the
hardest one to make credible. It stays grounded: an agent picks up an issue,
works it, opens a coding session, and returns a diff for review. No magic, no
sparkles — the only claim is that the work moves while you are not watching.

The craft is the status transition and the diff reveal, both drawn from real UI
rather than invented ornament.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, ACCENT_HOVER, COOL, H, INK, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
from easing import seg
from layout import measure, svg_font
from stock import clamp
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    PRI_HIGH,
    PRI_MEDIUM,
    ROW_H,
    SIDEBAR_W,
    STATUS_BACKLOG,
    STATUS_DONE,
    STATUS_PROGRESS,
    STATUS_REVIEW,
    STATUS_TODO,
    TOPBAR_H,
    issue_row,
    row_hairline,
    sidebar,
    status_glyph,
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
    ("Agents", False),
    ("Teams", True),
    ("Engineering", False),
]

TARGET = ("ENG-512", "Flaky auth refresh in Safari", PRI_HIGH)

# The agent's steps, each with the second it lands.
STEPS = [
    ("Reading issue and linked threads", 0.14),
    ("Reproducing on WebKit", 0.30),
    ("Opening coding session", 0.46),
    ("Editing 3 files", 0.62),
    ("Running test suite", 0.78),
]

# The diff the agent proposes.
DIFF = [
    ("-", "if (!token.expiresAt) return refresh()", 1),
    ("+", "if (!token?.expiresAt) {", 2),
    ("+", "  await refresh({ skewMs: 5_000 })", 3),
    ("+", "}", 4),
]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.20, "expo")
    panel = seg(clock.u, 0.10, 0.24, "expo")
    steps = seg(clock.u, 0.16, 0.72, "linear")
    diff = seg(clock.u, 0.60, 0.30, "out")
    review = seg(clock.u, 0.84, 0.14, "circ")
    label = seg(clock.u, 0.04, 0.16, "out")

    glow(d, W / 2, H * 0.42, 780, ACCENT, 0.16 * seg(clock.u, 0, 0.4, "out"))

    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=6)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Engineering / Agents", "ENG-512",
                   opacity=a, accent_rule=seg(clock.u, 0.05, 0.24, "expo"))
            if panel > 0:
                _agent_panel(d, clock, panel, steps, diff, review)
    if label > 0:
        _beat_label(d, label, "06  ·  AGENTS")

    return d.render()


def _agent_panel(d: Doc, c, u: float, steps: float, diff: float, review: float) -> None:
    """Left: the issue and its agent trail. Right: the proposed diff.

    Two columns rather than one, because the point is that the agent works
    *inside* the issue rather than in a separate tool.
    """
    x = APP_X + SIDEBAR_W + 26
    y = APP_Y + TOPBAR_H + 18
    col_w = (APP_W - SIDEBAR_W - 26 * 3) / 2

    _issue_card(d, x, y, col_w, u, steps, review)
    _diff_card(d, x + col_w + 26, y, col_w, seg(u, 0.4, 0.6, "out") * (diff > 0), diff, review)


def _issue_card(d: Doc, x: float, y: float, w: float, u: float, steps: float, review: float) -> None:
    """The issue, with an agent assigned and a live trail of what it has done."""
    h = 452.0
    d.rect(x, y, w, h, fill="#101112", rx=8, opacity=u)
    d.rect(x, y, w, h, fill="none", stroke="rgba(255,255,255,0.07)", stroke_width=1.0, rx=8, opacity=u)

    # Header: key, then the title.
    mfam, mweight = svg_font(TYPE_MONO)
    ident, title, pri = TARGET
    d.text(x + 22, y + 34, ident, 11.5, mfam, mweight, INK[4], tracking=0.3, opacity=u)
    d.text(x + 22, y + 62, title, 17.0, *svg_font(TYPE_UI), INK[1], opacity=u)

    # Status pill: moves through states as the agent works, which is the beat's
    # whole narrative in one element.
    sy = y + 96
    if review > 0.4:
        state, col = STATUS_REVIEW, "#b59aff"
        label = "In Review"
    elif steps > 0.5:
        state, col = STATUS_PROGRESS, "#f2c94c"
        label = "In Progress"
    else:
        state, col = STATUS_TODO, "#d0d6e0"
        label = "Todo"
    pw = measure(TYPE_UI_MED, 11.0, label) + 46
    d.rect(x + 22, sy - 13, pw, 26, fill="rgba(255,255,255,0.05)", rx=13, opacity=u)
    status_glyph(d, x + 36, sy, 6.0, state, u)
    d.text(x + 50, sy + 4, label, 11.0, *svg_font(TYPE_UI_MED), INK[2], opacity=u)

    # Assignee: the agent.
    ax = x + 22 + pw + 12
    d.rect(ax, sy - 13, 132, 26, fill="rgba(94,106,210,0.14)", rx=13, opacity=u)
    _agent_glyph(d, ax + 16, sy, 6.0, u)
    d.text(ax + 30, sy + 4, "Agent · Dev", 11.0, *svg_font(TYPE_UI_MED), ACCENT_HOVER, opacity=u)

    d.line(x + 22, y + 126, x + w - 22, y + 126, "#23252a", 1.0, opacity=u)

    # The trail.
    d.text(x + 22, y + 152, "AGENT ACTIVITY", 10.0, *svg_font(TYPE_UI), INK[4],
           tracking=0.9, opacity=0.9 * u)
    ty = y + 178
    for i, (label, at) in enumerate(STEPS):
        local = seg(steps, at, 0.16, "out")
        if local <= 0:
            continue
        done = local >= 1.0
        active = 0.0 < local < 1.0
        col = INK[2] if done else (INK[1] if active else INK[4])
        # Marker: filled when done, a ring while running.
        if done:
            d.circle(x + 30, ty, 4.2, fill=ACCENT_BRIGHT, opacity=local)
            d.path(
                f"M{x + 28.2:.1f} {ty:.1f} L{x + 29.6:.1f} {ty + 1.6:.1f} L{x + 32:.1f} {ty - 1.8:.1f}",
                stroke="#08090a", width=1.4, cap="round", join="round", opacity=local,
            )
        else:
            d.circle(x + 30, ty, 4.2, fill="none", stroke=col, stroke_width=1.4, opacity=local)
            if active:
                d.circle(x + 30, ty, 8.6 * (0.6 + 0.4 * local), fill="none",
                         stroke=ACCENT, stroke_width=1.0, opacity=0.5 * local)

        d.text(x + 46, ty + 4, label, 12.5, *svg_font(TYPE_UI_MED), col, opacity=local)
        if done:
            d.text(x + w - 22, ty + 4, "done", 10.5, mfam, mweight, INK[4],
                   anchor="end", opacity=0.8 * local)
        elif active:
            d.text(x + w - 22, ty + 4, "running", 10.5, mfam, mweight, ACCENT_HOVER,
                   anchor="end", opacity=0.9 * local)
        # Connector, so the trail reads as a sequence.
        if i < len(STEPS) - 1:
            d.line(x + 30, ty + 8, x + 30, ty + 20, "#23252a", 1.0, opacity=local * 0.9)
        ty += 28

    # Elapsed counter at the foot of the card.
    el = seg(steps, 0.1, 0.7, "out")
    if el > 0:
        secs = 4 + int(el * 128)
        d.text(x + 22, y + h - 20, f"elapsed {secs // 60}:{secs % 60:02d}", 11.0,
               mfam, mweight, INK[4], tracking=0.4, opacity=u)


def _agent_glyph(d: Doc, cx: float, cy: float, r: float, u: float) -> None:
    """A small mark for the agent: a ringed dot with an orbit, not a robot icon."""
    d.circle(cx, cy, r * 0.42, fill=ACCENT_HOVER, opacity=u)
    d.circle(cx, cy, r, fill="none", stroke=ACCENT_HOVER, stroke_width=1.3, opacity=0.85 * u)
    # Orbit dot.
    d.circle(cx + math.cos(-0.6) * r, cy + math.sin(-0.6) * r, r * 0.30,
             fill=ACCENT_HOVER, opacity=0.9 * u)


def _diff_card(d: Doc, x: float, y: float, w: float, u: float, diff: float, review: float) -> None:
    """The proposed change, as a diff with added lines drawing in."""
    if u <= 0.01:
        return
    h = 452.0
    d.rect(x, y, w, h, fill="#0d0e0f", rx=8, opacity=u)
    d.rect(x, y, w, h, fill="none", stroke="rgba(255,255,255,0.07)", stroke_width=1.0, rx=8, opacity=u)

    mfam, mweight = svg_font(TYPE_MONO)
    d.text(x + 22, y + 30, "auth/refresh.ts", 11.5, mfam, mweight, INK[3], opacity=u)
    d.text(x + w - 22, y + 30, "+3 −1", 11.0, mfam, mweight, "#4cb782", anchor="end", opacity=u)
    d.line(x + 22, y + 48, x + w - 22, y + 48, "#23252a", 1.0, opacity=u)

    # Diff rows, staggered in.
    ty = y + 76
    for i, (kind, text, at) in enumerate(DIFF):
        local = seg(diff, i * 0.14, 0.5, "out")
        if local <= 0:
            continue
        added = kind == "+"
        if added:
            d.rect(x + 14, ty - 14, w - 28, 24, fill="rgba(76,183,130,0.09)", rx=3,
                   opacity=local)
        else:
            d.rect(x + 14, ty - 14, w - 28, 24, fill="rgba(242,153,74,0.07)", rx=3,
                   opacity=local)
        d.text(x + 24, ty + 3, kind, 12.5, mfam, mweight,
               "#4cb782" if added else "#f2994a", opacity=local)
        d.text(x + 42, ty + 3, text, 12.5, mfam, mweight,
               INK[2] if added else INK[3], opacity=local)
        ty += 28

    if diff > 0.9:
        d.line(x + 22, y + h - 128, x + w - 22, y + h - 128, "#23252a", 1.0, opacity=u)
        d.text(x + 22, y + h - 102, "TESTS", 10.0, *svg_font(TYPE_UI), INK[4],
               tracking=0.9, opacity=0.9 * u)
        ok = seg(diff, 0.6, 0.35, "out")
        if ok > 0:
            d.path(
                f"M{x + 26} {y + h - 80} L{x + 30} {y + h - 75.5 * ok} L{x + 38 * ok} {y + h - 85 * ok}",
                stroke="#4cb782", width=1.8, cap="round", join="round", opacity=ok,
            )
            d.text(x + 46, y + h - 81, "142 passed", 12.0, *svg_font(TYPE_UI_MED), INK[2], opacity=ok)

    # Review actions, appearing once the agent is done.
    ru = seg(review, 0.2, 0.5, "out")
    if ru > 0.01:
        by = y + h - 52
        d.rect(x + 22, by, 92, 30, fill=ACCENT, rx=6, opacity=ru)
        d.text(x + 22 + 46 - measure(TYPE_UI_MED, 12.5, "Approve") / 2, by + 19.5, "Approve",
               12.5, *svg_font(TYPE_UI_MED), INK[1], opacity=ru)
        d.rect(x + 124, by, 104, 30, fill="rgba(255,255,255,0.05)", rx=6, opacity=ru)
        d.text(x + 124 + 52 - measure(TYPE_UI_MED, 12.5, "Request") / 2, by + 19.5, "Request",
               12.5, *svg_font(TYPE_UI_MED), INK[2], opacity=ru)


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)
