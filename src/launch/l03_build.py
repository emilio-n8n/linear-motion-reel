"""L3 BUILD — issue tracking and triage, Linear's core loop.

This is the beat that has to feel fastest, because issue tracking is the product.
The craft is a coordinated re-sort: eight rows change priority and the list
re-orders itself in a single snap, which is the clearest possible statement of
what Linear means by speed.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
from easing import Spring, seg
from layout import measure, svg_font
from stock import clamp
from svg import Doc, glow
from ui import (
    APP_H,
    APP_W,
    APP_X,
    APP_Y,
    PRI_HIGH,
    PRI_LOW,
    PRI_MEDIUM,
    PRI_NONE,
    PRI_URGENT,
    ROW_H,
    SIDEBAR_W,
    STATUS_BACKLOG,
    STATUS_CANCELED,
    STATUS_DONE,
    STATUS_PROGRESS,
    STATUS_TODO,
    TOPBAR_H,
    command_palette,
    filler_rows,
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
]

# (key, title, status, priority, assignee, labels, triage_flag)
# triage_flag marks the rows that get triaged in this beat.
ROWS = [
    ("ENG-482", "Command palette fuzzy match", STATUS_PROGRESS, PRI_HIGH, "Ada L", ["Feature"], False),
    ("ENG-481", "Batch edit via multi-select", STATUS_TODO, PRI_URGENT, "", ["Feature"], True),
    ("ENG-479", "Reduce cold start on boot", STATUS_DONE, PRI_MEDIUM, "Ravi K", [], False),
    ("ENG-477", "Webhook retry backoff", STATUS_TODO, PRI_LOW, "", ["Bug"], True),
    ("ENG-474", "Cycle rollup on project close", STATUS_TODO, PRI_MEDIUM, "Mira S", [], False),
    ("ENG-470", "Archive cancelled on close", STATUS_BACKLOG, PRI_NONE, "", [], True),
    ("ENG-468", "Virtualise long lists", STATUS_DONE, PRI_MEDIUM, "Ada L", ["Perf"], False),
    ("ENG-465", "Editor: slash commands", STATUS_PROGRESS, PRI_HIGH, "Mira S", ["Feature"], False),
]

# Where each row ends up after triage: urgent to the top, done to the bottom.
# Kept as an explicit permutation so the re-sort is a designed order, not a
# side effect of a sort call.
TRIAGED_ORDER = [1, 2, 0, 3, 4, 7, 6, 5]

TRIAGE_ACTIONS = [
    ("Set priority", "Urgent"),
    ("Set status", "In Progress"),
    ("Assign to", "Ada Lovelace"),
]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.22, "expo")
    rows = seg(clock.u, 0.08, 0.30, "out")
    sort_u = seg(clock.u, 0.34, 0.10, "circ")
    back = seg(clock.u, 0.70, 0.16, "circ")
    label = seg(clock.u, 0.04, 0.16, "out")

    glow(d, W / 2, H * 0.44, 760, ACCENT, 0.14 * seg(clock.u, 0, 0.4, "out"))

    if chrome > 0:
        window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=a, active=4)
            topbar(d, APP_X + SIDEBAR_W, APP_Y, APP_W - SIDEBAR_W, "Engineering / Triage", "8 issues",
                   opacity=a, accent_rule=seg(clock.u, 0.05, 0.24, "expo"))
            if rows > 0:
                _list(d, clock, rows, sort_u, back)

    if label > 0:
        _beat_label(d, label, "03  ·  ISSUE TRACKING")

    return d.render()


def _row_y(order: list[int], i: int, sort_u: float) -> float:
    """Interpolate a row's vertical position through the re-sort.

    Each row remembers where it was and where it is going, so the move is one
    continuous gesture rather than a cut — the whole list moving at once is what
    sells the speed.

    Rows that only shift a short distance take a detour through a small
    overshoot instead, so no two rows occupy the same y mid-flight. A plain
    linear interpolation makes them slide through each other, which reads as a
    glitch rather than as a list being re-prioritised.
    """
    y0 = APP_Y + TOPBAR_H + 12 + i * ROW_H
    if sort_u <= 0:
        return y0
    dest = order.index(i)
    y1 = APP_Y + TOPBAR_H + 12 + dest * ROW_H
    delta = dest - i
    if delta == 0:
        return y0
    # Bows the trajectory out of the straight line, scaled by how far it travels.
    bow = math.sin(sort_u * math.pi) * delta * ROW_H * 0.34
    return y0 + (y1 - y0) * sort_u + bow


def _list(d: Doc, c, u: float, sort_u: float, back: float) -> None:
    """Draw the whole list, then the triage caption, then nothing else.

    The caption is the last thing drawn and is fully cleared by 0.64 so the scene
    ends on the list rather than on an annotation.
    """
    x = APP_X + SIDEBAR_W
    w = APP_W - SIDEBAR_W
    n = len(ROWS)

    for i, row in enumerate(ROWS):
        # Rows stagger in, but the re-sort overrides the stagger — a reordering
        # list that is still fading in reads as two effects fighting.
        local = seg(u, (i / max(n - 1, 1)) * 0.34, 0.62, "out")
        if local <= 0:
            continue
        y = _row_y(TRIAGED_ORDER, i, sort_u)
        op = local * (1.0 - back)
        if op <= 0.01:
            continue
        slide = (1.0 - local) * 20

        with d.group(transform=f"translate(0 {_n(slide)})"):
            issue_row(d, x, y, w, row[0], row[1], row[2], row[3], row[4], row[5], opacity=op)
            row_hairline(d, x, y + ROW_H, w, opacity=op * 0.6)

        # The rows that got triaged get a brief accent edge, so the cause of the
        # re-sort is visible rather than mysterious.
        if row[6] and sort_u > 0.01 and sort_u < 0.99:
            edge = math.sin(sort_u * math.pi)
            if edge > 0.02:
                d.rect(x, y, 2, ROW_H, fill=ACCENT_BRIGHT, opacity=0.85 * edge)

    # Filler rows below the triaged set, at lower emphasis. They hold still
    # during the re-sort: only the triaged set moves, and having everything
    # shuffle at once would read as noise rather than as a deliberate re-prioritise.
    extra = filler_rows(len(ROWS) + 4, 8)
    m = len(extra)
    for i, row in enumerate(extra):
        local = seg(u, 0.20 + (i / max(m - 1, 1)) * 0.34, 0.62, "out")
        if local <= 0:
            continue
        y = APP_Y + TOPBAR_H + 12 + (n + i) * ROW_H
        op = local * 0.9 * (1.0 - back)
        if op <= 0.01:
            continue
        slide = (1.0 - local) * 20
        with d.group(transform=f"translate(0 {_n(slide)})"):
            issue_row(d, x, y, w, *row, opacity=op)
            row_hairline(d, x, y + ROW_H, w, opacity=op * 0.55)

    # Caption appears only while the re-sort is in flight, then clears so the
    # scene ends on the list itself.
    cu = seg(c.u, 0.30, 0.08, "out") * (1.0 - seg(c.u, 0.52, 0.12, "in"))
    if cu > 0.01:
        _triage_caption(d, x, APP_Y + APP_H - 40, cu)


def _triage_caption(d: Doc, x: float, y: float, u: float) -> None:
    """The three bulk actions, ticked off as the re-sort lands."""
    mfam, mweight = svg_font(TYPE_MONO)
    tx = x + 26
    for i, (verb, target) in enumerate(TRIAGE_ACTIONS):
        local = seg(u, i * 0.10, 0.5, "out")
        if local <= 0:
            continue
        # Tick mark draws itself in.
        lx = tx
        d.path(
            f"M{lx} {y - 4} L{lx + 4 * local} {y} L{lx + 11 * local} {y - 9 * local}",
            stroke=ACCENT_BRIGHT, width=1.8, cap="round", join="round", opacity=local,
        )
        label = f"{verb} → {target}"
        d.text(lx + 20, y, label, 11.5, mfam, mweight, INK[3], tracking=0.5, opacity=local * 0.95)
        tx += 20 + measure(TYPE_MONO, 11.5, label, 0.5) + 34


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
