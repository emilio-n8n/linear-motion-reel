"""Reconstruction of Linear's app chrome, drawn from scratch.

Every element here is built from paths and text so it can be animated. That
means the fidelity depends on knowing the real design rather than on copying an
asset, so the values come from Linear's own public surfaces:

  - status workflow: Backlog > Todo > In Progress > Done > Canceled
    (linear.app/docs/configuring-workflows)
  - priorities: Urgent, High, Medium, Low, None
  - palette: their published tokens (see brand.py)

This is a reconstruction for a spec piece, not their asset. Nothing here is
extracted from, or substituted for, their product artwork.
"""

from __future__ import annotations

import math

from brand import (
    ACCENT,
    ACCENT_BRIGHT,
    CANVAS,
    HAIRLINE,
    HAIRLINE_SOFT,
    H,
    INK,
    SURFACE,
    TYPE_MONO,
    TYPE_UI,
    TYPE_UI_MED,
    TYPE_UI_REG,
    W,
)
from layout import cap_height, measure, svg_font
from svg import Doc, glow

# ---------------------------------------------------------------- status

# Their documented workflow order, with the colour each status renders in.
STATUS_BACKLOG = "backlog"
STATUS_TODO = "todo"
STATUS_PROGRESS = "progress"
STATUS_DONE = "done"
STATUS_CANCELED = "canceled"

STATUS_COLOR = {
    STATUS_BACKLOG: "#8a8f98",
    STATUS_TODO: "#d0d6e0",
    STATUS_PROGRESS: "#f2c94c",
    STATUS_DONE: ACCENT_BRIGHT,
    STATUS_CANCELED: "#62666d",
}

# Linear's own product team adds a review step between progress and done.
STATUS_REVIEW = "review"
STATUS_COLOR[STATUS_REVIEW] = "#b59aff"
STATUS_ORDER = [
    STATUS_BACKLOG,
    STATUS_TODO,
    STATUS_PROGRESS,
    STATUS_REVIEW,
    STATUS_DONE,
    STATUS_CANCELED,
]


def status_glyph(d: Doc, cx: float, cy: float, r: float, status: str, opacity: float = 1.0) -> None:
    """The status icon: a stroked circle whose treatment encodes the state.

    Backlog is dashed, Todo is an empty ring, In Progress is a half-disc, Done is
    a filled disc with a check, Canceled is a ring with a bar. That distinction
    has to survive being 14px wide, so it is carried by the fill pattern rather
    than by colour alone.
    """
    col = STATUS_COLOR.get(status, INK[3])
    if status == STATUS_BACKLOG:
        # Dashed ring: a ring of short arcs.
        seg = 10
        for i in range(seg):
            if i % 2:
                continue
            a0 = i / seg * math.tau
            a1 = (i + 0.82) / seg * math.tau
            d.path(
                f"M{cx + math.cos(a0) * r:.2f} {cy + math.sin(a0) * r:.2f} "
                f"A{r:.2f} {r:.2f} 0 0 1 "
                f"{cx + math.cos(a1) * r:.2f} {cy + math.sin(a1) * r:.2f}",
                stroke=col, width=max(1.0, r * 0.17), cap="butt", opacity=opacity,
            )
    elif status == STATUS_TODO:
        d.circle(cx, cy, r * 0.86, fill="none", stroke=col, stroke_width=max(1.0, r * 0.17), opacity=opacity)
    elif status == STATUS_PROGRESS:
        # Half disc, flat side down: reads as "underway" without needing motion.
        d.path(
            f"M{cx - r:.2f} {cy:.2f} A{r:.2f} {r:.2f} 0 0 1 {cx + r:.2f} {cy:.2f} Z",
            fill=col, opacity=opacity,
        )
    elif status == STATUS_REVIEW:
        d.circle(cx, cy, r * 0.86, fill="none", stroke=col, stroke_width=max(1.0, r * 0.17), opacity=opacity)
        d.circle(cx, cy, r * 0.34, fill=col, opacity=opacity)
    elif status == STATUS_DONE:
        d.circle(cx, cy, r * 0.9, fill=col, opacity=opacity)
        # Check, as a two-segment path so it scales with the radius.
        d.path(
            f"M{cx - r * 0.36:.2f} {cy + r * 0.02:.2f} "
            f"L{cx - r * 0.08:.2f} {cy + r * 0.30:.2f} "
            f"L{cx + r * 0.40:.2f} {cy - r * 0.28:.2f}",
            stroke=CANVAS, width=max(1.0, r * 0.19), cap="round", join="round", opacity=opacity,
        )
    else:  # canceled
        d.circle(cx, cy, r * 0.86, fill="none", stroke=col, stroke_width=max(1.0, r * 0.17), opacity=opacity)
        d.line(cx - r * 0.42, cy, cx + r * 0.42, cy, col, max(1.0, r * 0.17), opacity=opacity)


# -------------------------------------------------------------- priority

PRI_URGENT = "urgent"
PRI_HIGH = "high"
PRI_MEDIUM = "medium"
PRI_LOW = "low"
PRI_NONE = "none"

# Linear draws priority as a stack of bars whose count encodes the level.
PRI_BARS = {PRI_URGENT: 3, PRI_HIGH: 2, PRI_MEDIUM: 1, PRI_LOW: 1, PRI_NONE: 0}
PRI_COLOR = {
    PRI_URGENT: "#f2994a",
    PRI_HIGH: "#f2c94c",
    PRI_MEDIUM: "#5e6ad2",
    PRI_LOW: "#8a8f98",
    PRI_NONE: "#3e3e44",
}


def priority_glyph(d: Doc, x: float, cy: float, w: float, priority: str, opacity: float = 1.0) -> None:
    """Three ascending bars; the filled count reads as the level, in Linear's idiom.

    Tallest bar on the left and filled from the tallest down, so "urgent" reads
    as three filled bars and "low" as a single short one.
    """
    col = PRI_COLOR.get(priority, PRI_COLOR[PRI_NONE])
    bars = PRI_BARS.get(priority, 0)
    gap = 1.6
    bw = (w - gap * 2) / 3.0
    for i in range(3):
        h = (0.94 - 0.26 * i) * w
        bx = x + i * (bw + gap)
        filled = i < bars
        d.rect(
            bx, cy - h / 2, bw, h,
            fill=col if filled else "#2a2d31",
            opacity=opacity,
            rx=0.5,
        )


# ---------------------------------------------------------------- chrome

# Chrome proportions, matched to the real app's density: a narrow rail beside a
# dense content area, with tight rows.
SIDEBAR_W = 232.0
TOPBAR_H = 44.0
ROW_H = 36.0


# The window the film operates in — inset from frame, like a product shot.
APP_W = 1560.0
APP_H = 860.0
APP_X = (W - APP_W) / 2
APP_Y = (H - APP_H) / 2


def window_chrome(d: Doc, x: float, y: float, w: float, h: float, reveal: float = 1.0,
                  scale_from: float = 1.0) -> None:
    """The app frame: rounded window, sidebar, top bar.

    `reveal` wipes the chrome in from the left, which is how the film opens a
    scene — it reads as the app arriving rather than a hard cut.
    """
    r = 10.0
    if reveal <= 0.001:
        return
    cid = d.clip_rect(x, y, w * reveal, h, r)
    with d.group(clip=cid):
        d.rect(x, y, w, h, fill=SURFACE[0])
        # Sidebar is a step darker than the content surface, as in the real app.
        d.rect(x, y, SIDEBAR_W, h, fill="#0b0c0d")
        d.line(x + SIDEBAR_W, y, x + SIDEBAR_W, y + h, HAIRLINE, 1.0)
        d.line(x, y + TOPBAR_H, x + w, y + TOPBAR_H, HAIRLINE, 1.0)
    d.rect(x, y, w, h, fill="none", stroke=HAIRLINE, stroke_width=1.0, rx=r, opacity=reveal)


def sidebar(d: Doc, x: float, y: float, w: float, h: float, items: list[tuple[str, bool]],
            opacity: float = 1.0, active: int = 0) -> None:
    """Workspace switcher plus navigation items. `items` is (label, is_section)."""
    fam, weight = svg_font(TYPE_UI_MED)
    cy = y + 30
    # Workspace row: a mark plus the name.
    d.circle(x + 22, cy - 4, 9, fill=ACCENT, opacity=opacity)
    d.text(x + 40, cy, "Linear", 13.5, fam, weight, INK[1], opacity=opacity)
    cy += 34

    for i, (label, is_section) in enumerate(items):
        if is_section:
            cy += 14
            d.text(x + 18, cy, label.upper(), 10.5, *svg_font(TYPE_UI),
                   INK[4], tracking=0.7, opacity=opacity * 0.9)
            cy += 16
            continue
        sel = i == active
        if sel:
            d.rect(x + 10, cy - 12, w - 20, 26, fill="rgba(255,255,255,0.055)", rx=6, opacity=opacity)
        col = INK[1] if sel else INK[3]
        d.circle(x + 22, cy - 4, 3.2, fill=col if sel else INK[4], opacity=opacity)
        d.text(x + 36, cy, label, 13.0, fam, weight, col, opacity=opacity)
        cy += 28


def topbar(d: Doc, x: float, y: float, w: float, breadcrumb: str, right: str = "",
           opacity: float = 1.0, accent_rule: float = 0.0) -> None:
    """Breadcrumb left, a control cluster right."""
    if opacity <= 0.001:
        return
    cy = y + TOPBAR_H / 2
    fam, weight = svg_font(TYPE_UI_MED)
    d.text(x + 22, cy + 4.5, breadcrumb, 13.0, fam, weight, INK[2], opacity=opacity)

    if right:
        mfam, mweight = svg_font(TYPE_MONO)
        rw = measure(TYPE_MONO, 11.0, right, 0.4)
        d.text(x + w - 22 - rw, cy + 4, right, 11.0, mfam, mweight, INK[4], tracking=0.4, opacity=opacity)

    # New issue button: Linear's primary action.
    bw, bh = 84.0, 26.0
    bx, by = x + w - 22 - bw, cy - bh / 2
    d.rect(bx, by, bw, bh, fill=ACCENT, rx=6, opacity=opacity)
    d.text(bx + 14, cy + 4, "New issue", 12.0, *svg_font(TYPE_UI), INK[1], opacity=opacity)

    if accent_rule > 0:
        d.rect(x, y, w * accent_rule, 1.6, fill=ACCENT_BRIGHT, opacity=opacity)


# ------------------------------------------------------------------ rows

def issue_row(d: Doc, x: float, y: float, w: float, ident: str, title: str, status: str,
              priority: str, assignee: str = "", labels: list[str] | None = None,
              opacity: float = 1.0, h: float = ROW_H, clip_id: str | None = None) -> None:
    """One issue row: status, key, title, labels, priority, assignee.

    Built to survive being animated as a group, so nothing here depends on
    clipping unless it is given a clip id.
    """
    if opacity <= 0.01:
        return
    with d.group(clip=clip_id):
        cy = y + h / 2
        status_glyph(d, x + 16, cy, 6.4, status, opacity)

        mfam, mweight = svg_font(TYPE_MONO)
        d.text(x + 36, cy + 4, ident, 11.5, mfam, mweight, "#8a8f98", tracking=0.3, opacity=opacity)

        tx = x + 36 + 74
        tfam, tweight = svg_font(TYPE_UI_REG)
        d.text(tx, cy + 4.5, title, 13.0, tfam, tweight, INK[1], opacity=opacity)
        # Slightly brighter than Linear's own secondary step: the film is watched
        # at a distance, not read at arm's length.

        # Right cluster: labels, priority, assignee — laid out from the right in.
        rx = x + w - 20
        if assignee:
            initials = "".join(p[0] for p in assignee.split()[:2]).upper()
            d.circle(rx - 9, cy, 9, fill=ACCENT, opacity=opacity * 0.9)
            afam, aweight = svg_font(TYPE_UI)
            aw = measure(TYPE_UI, 9.0, initials)
            d.text(rx - 9 - aw / 2, cy + 3.4, initials, 9.0, afam, aweight, INK[1], opacity=opacity)
            rx -= 30
        priority_glyph(d, rx - 13, cy, 13, priority, opacity)
        rx -= 24

        for label in reversed(labels or []):
            lfam, lweight = svg_font(TYPE_UI_MED)
            lw = measure(TYPE_UI_MED, 10.5, label) + 14
            d.rect(rx - lw, cy - 8, lw, 16, fill="rgba(255,255,255,0.06)", rx=4, opacity=opacity)
            d.text(rx - lw + 7, cy + 3.6, label, 10.5, lfam, lweight, INK[3], opacity=opacity)
            rx -= lw + 6


def row_hairline(d: Doc, x: float, y: float, w: float, opacity: float = 1.0) -> None:
    d.line(x, y, x + w, y, HAIRLINE_SOFT, 1.0, opacity=opacity)


# Filler rows, so a scene's list reaches the bottom of the window instead of
# trailing off in the middle. Real content rather than placeholder bars, because
# a launch film is judged on whether the product looks in use.
FILLER = [
    ("ENG-463", "Cursor position across reloads", STATUS_TODO, PRI_MEDIUM, "Ravi K", []),
    ("ENG-459", "Darken attachment thumbnails", STATUS_TODO, PRI_LOW, "", ["Polish"]),
    ("ENG-455", "Idempotency keys on mutations", STATUS_BACKLOG, PRI_NONE, "Ada L", ["API"]),
    ("ENG-451", "Reduce sidebar jank on nav", STATUS_TODO, PRI_MEDIUM, "", ["Perf"]),
    ("ENG-448", "Sync presence over websocket", STATUS_BACKLOG, PRI_LOW, "Mira S", []),
    ("ENG-444", "Keyboard map: custom bindings", STATUS_TODO, PRI_HIGH, "Ada L", ["Feature"]),
    ("ENG-440", "Retry queue: dead letter", STATUS_TODO, PRI_MEDIUM, "", ["API"]),
    ("ENG-436", "Triage: bulk assign", STATUS_TODO, PRI_LOW, "Ravi K", []),
    ("ENG-432", "Search: typo tolerance", STATUS_TODO, PRI_MEDIUM, "", []),
    ("ENG-429", "Undo for destructive actions", STATUS_TODO, PRI_HIGH, "Mira S", ["Feature"]),
]


def filler_rows(start: int, count: int) -> list[tuple]:
    """`count` rows from the filler pool, wrapping, with keys counting down."""
    out = []
    for k in range(count):
        row = FILLER[(start + k) % len(FILLER)]
        ident, title, status, pri, who, labels = row
        num = int(ident.split("-")[1]) - (start + k) // len(FILLER)
        out.append((f"ENG-{num:03d}", title, status, pri, who, labels))
    return out


# ------------------------------------------------------------- chrome bits

def command_palette(d: Doc, cx: float, cy: float, w: float, query: str, items: list[str],
                    reveal: float = 1.0, caret: bool = True, highlight: int = 0) -> None:
    """The ⌘K palette: a floating panel with a search field and a result list.

    This is the clearest expression of Linear's speed claim, so the panel is
    drawn with real elevation rather than as a flat rectangle.
    """
    if reveal <= 0.005:
        return
    h = 68 + len(items) * 34
    x = cx - w / 2
    y = cy - h / 2
    r = 10.0
    scale = 0.96 + 0.04 * reveal
    ox, oy = cx, cy

    with d.group(transform=_tf(ox, oy, scale, w, h)):
        # Drop shadow, built from stacked offsets since rsvg has no feDropShadow.
        for i, k in enumerate((0.030, 0.018, 0.008)):
            d.rect(x - 1, y - 1 + i * 5, w + 2, h + 2, fill=f"rgba(0,0,0,{k})", rx=r)
        d.rect(x, y, w, h, fill="#141516", rx=r)
        d.rect(x, y, w, h, fill="none", stroke="rgba(255,255,255,0.10)", stroke_width=1.0, rx=r)

        # Search field.
        fy = y + 30
        d.circle(x + 26, fy - 4, 5.0, fill="none", stroke=INK[4], stroke_width=1.4)
        d.line(x + 30, fy, x + 34, fy + 4, INK[4], 1.4, cap="round")
        qfam, qweight = svg_font(TYPE_UI_REG)
        d.text(x + 44, fy + 4, query, 14.0, qfam, qweight, INK[1])
        if caret:
            qw = measure(TYPE_UI_REG, 14.0, query)
            d.rect(x + 47 + qw, fy - 9, 1.6, 18, fill=ACCENT_BRIGHT)
        d.line(x + 16, y + 52, x + w - 16, y + 52, HAIRLINE, 1.0)

        # Results.
        for i, label in enumerate(items):
            ry = y + 52 + 17 + i * 34
            sel = i == highlight
            if sel:
                d.rect(x + 8, ry - 15, w - 16, 30, fill="rgba(255,255,255,0.05)", rx=6)
            d.rect(x + 18, ry - 5, 20, 20, fill=ACCENT if sel else "#23252a", rx=5)
            d.text(x + 48, ry + 4, label, 13.0, *svg_font(TYPE_UI_REG), INK[1] if sel else INK[2])
            kfam, kweight = svg_font(TYPE_MONO)
            d.text(x + w - 40, ry + 4, "↵", 11.0, kfam, kweight, INK[4], anchor="end")


def _tf(ox: float, oy: float, scale: float, w: float, h: float) -> str:
    """Scale about the element's own centre."""
    return (
        f"translate({_n(ox)} {_n(oy)}) scale({_n(scale)}) "
        f"translate({_n(-ox)} {_n(-oy)})"
    )


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
