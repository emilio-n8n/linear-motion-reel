"""L5 PALETTE — the command palette, Linear's clearest claim to speed.

One keystroke, every action. The beat is deliberately almost static: the app dims
and blurs, the palette drops, a query types itself, results narrow, and a command
executes. Restraint here is the point — after three busy scenes, a beat that
only moves where it must reads as confidence.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_MONO, TYPE_UI, TYPE_UI_MED, W
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
    STATUS_DONE,
    STATUS_PROGRESS,
    STATUS_TODO,
    TOPBAR_H,
    command_palette,
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

# Query types itself one character at a time.
QUERY = "assign to me"

# Results narrow as the query grows: each is (label, visible_from_char_index).
RESULTS = [
    ("Ada Lovelace", 0),
    ("Assign to…", 2),
    ("Assign to project", 4),
    ("Assign sub-issues to…", 8),
    ("Assign to cycle", 11),
]

# The state after the command runs: assignee and status both change, so the
# palette's effect is visible in the product and not only in the overlay.
AFTER = [
    ("ENG-482", "Command palette fuzzy match", STATUS_PROGRESS, PRI_HIGH, "Ada L", ["Feature"]),
    ("ENG-465", "Editor: slash commands", STATUS_PROGRESS, PRI_HIGH, "Ada L", ["Feature"]),
    ("ENG-444", "Keyboard map: custom bindings", STATUS_PROGRESS, PRI_HIGH, "Ada L", ["Feature"]),
    ("ENG-429", "Undo for destructive actions", STATUS_PROGRESS, PRI_HIGH, "Ada L", ["Feature"]),
]

BEFORE = [
    ("ENG-482", "Command palette fuzzy match", STATUS_PROGRESS, PRI_HIGH, "Mira S", ["Feature"]),
    ("ENG-465", "Editor: slash commands", STATUS_PROGRESS, PRI_HIGH, "Mira S", ["Feature"]),
    ("ENG-444", "Keyboard map: custom bindings", STATUS_TODO, PRI_MEDIUM, "", ["Feature"]),
    ("ENG-429", "Undo for destructive actions", STATUS_TODO, PRI_MEDIUM, "Mira S", ["Feature"]),
]


def draw(clock) -> str:
    d = Doc()
    chrome = seg(clock.u, 0.0, 0.20, "expo")
    # The app dims and defocuses as the palette takes over.
    defocus = seg(clock.u, 0.12, 0.16, "circ")
    palette = seg(clock.u, 0.14, 0.20, "back")
    typing = seg(clock.u, 0.28, 0.30, "linear")
    execute = seg(clock.u, 0.72, 0.10, "circ")
    label = seg(clock.u, 0.04, 0.16, "out")

    if chrome > 0:
        a = clamp((chrome - 0.55) / 0.45)
        if a > 0:
            _app(d, clock, a, defocus, execute)
    if palette > 0:
        _palette(d, clock, palette, typing, execute)
    if label > 0:
        _beat_label(d, label, "05  ·  COMMAND PALETTE")

    return d.render()


def _app(d: Doc, c, chrome: float, defocus: float, execute: float) -> None:
    """The app behind the palette, blurring and dimming as the overlay arrives."""
    x = APP_X + SIDEBAR_W
    w = APP_W - SIDEBAR_W
    window_chrome(d, APP_X, APP_Y, APP_W, APP_H, reveal=chrome)
    sidebar(d, APP_X, APP_Y, SIDEBAR_W, APP_H, NAV, opacity=chrome, active=4)
    topbar(d, x, APP_Y, w, "Engineering / My Issues", "4 issues", opacity=chrome)

    # The rows behind: assignee changes when the command executes, so the
    # palette's effect is visible in the product rather than only in the overlay.
    y0 = APP_Y + TOPBAR_H + 14
    for i in range(len(BEFORE)):
        row_after = AFTER[i]
        row_before = BEFORE[i]
        slide = (1.0 - execute) * 0
        op = 0.34 + 0.66 * (1.0 - defocus)
        with d.group(transform=f"translate(0 {_n(slide)})"):
            # Cross-fade to the after-state, keyed on which fields change.
            issue_row(d, x, y0 + i * ROW_H, w, *row_before, opacity=op * (1.0 - execute * 0.85))
            if execute > 0.02:
                issue_row(d, x, y0 + i * ROW_H, w, *row_after, opacity=op * execute * 0.85)
            row_hairline(d, x, y0 + (i + 1) * ROW_H, w, opacity=op * 0.5)

    # Dim and defocus the whole app as the palette takes focus.
    if defocus > 0:
        d.rect(APP_X, APP_Y, APP_W, APP_H, fill="#08090a", opacity=0.62 * defocus)
        if defocus > 0.3:
            d.rect(APP_X, APP_Y, APP_W, APP_H, fill="none",
                   filt=d.blur(6.0 * defocus), opacity=0.0)

    # The keystroke badge, bottom right: ⌘K.
    ku = seg(c.u, 0.06, 0.14, "back")
    if ku > 0.01:
        _keycap(d, APP_X + APP_W - 76, APP_Y + APP_H - 60, ku * (1.0 - seg(c.u, 0.24, 0.1, "in")))


def _keycap(d: Doc, cx: float, cy: float, u: float) -> None:
    """A small ⌘K badge — the film's one on-screen keyboard affordance."""
    if u <= 0.01:
        return
    w, h = 46.0, 26.0
    s = 0.9 + 0.1 * u
    with d.group(transform=f"translate({_n(cx)} {_n(cy)}) scale({_n(s)}) translate({_n(-w / 2)} {_n(-h / 2)})"):
        d.rect(0, 0, w, h, fill="rgba(255,255,255,0.05)", rx=6, opacity=u)
        d.rect(0, 0, w, h, fill="none", stroke="rgba(255,255,255,0.10)", stroke_width=1.0, rx=6, opacity=u)
        kfam, kweight = svg_font(TYPE_MONO)
        d.text(w / 2 - 9, h / 2 + 4, "⌘", 12.0, kfam, kweight, INK[3], anchor="middle", opacity=u)
        d.text(w / 2 + 9, h / 2 + 4, "K", 12.0, kfam, kweight, INK[3], anchor="middle", opacity=u)


def _palette(d: Doc, c, u: float, typing: float, execute: float) -> None:
    """The overlay: query types, results narrow, selection executes and closes."""
    visible = [r for r in RESULTS if typing * (len(QUERY) + 1) >= r[1]]
    typed = QUERY[: max(1, int(typing * (len(QUERY) + 1)))]

    # Result list rebuilds as the query narrows; the panel height follows it, so
    # the panel must be drawn after we know how many rows it holds.
    shown = visible[:4] if execute <= 0.4 else visible[:3]
    panel_h = 68 + len(shown) * 34
    px = W / 2 - 300.0
    py = H / 2 - panel_h / 2

    # Dim the frame behind the overlay.
    d.rect(0, 0, W, H, fill="#08090a", opacity=0.5 * u)

    # A soft accent bloom behind the panel, so it reads as lit.
    glow(d, W / 2, H / 2, 320 * u, ACCENT, 0.22 * u)

    panel_u = u * (1.0 - seg(execute, 0.5, 0.5, "in"))
    if panel_u > 0.01:
        command_palette(d, W / 2, H / 2, 600, typed, [r[0] for r in shown],
                        reveal=panel_u, caret=(execute < 0.5),
                        highlight=0 if execute < 0.5 else 0)

    # Confirming chip, so the command reads as having run.
    eu = seg(execute, 0.35, 0.5, "out")
    if eu > 0.01:
        _confirm(d, W / 2, H / 2 + panel_h / 2 + 44, eu, f"Assigned to Ada Lovelace")


def _confirm(d: Doc, cx: float, cy: float, u: float, text: str) -> None:
    """A small confirmation chip, drawn on rather than popped."""
    mfam, mweight = svg_font(TYPE_UI_MED)
    tw = measure(TYPE_UI_MED, 12.5, text)
    w = tw + 46
    x = cx - w / 2
    rise = (1.0 - u) * 8
    with d.group(transform=f"translate(0 {_n(rise)})"):
        d.rect(x, cy - 15, w, 30, fill="rgba(76,201,240,0.10)", rx=15, opacity=u)
        d.rect(x, cy - 15, w, 30, fill="none", stroke="rgba(76,201,240,0.28)", stroke_width=1.0, rx=15, opacity=u)
        # Tick draws itself.
        d.path(
            f"M{x + 18} {cy} L{x + 22} {cy + 4.5 * u} L{x + 30 * u} {cy - 5 * u}",
            stroke="#4cb782", width=1.8, cap="round", join="round", opacity=u,
        )
        d.text(x + 38, cy + 4.5, text, 12.5, mfam, mweight, INK[2], opacity=u)


def _beat_label(d: Doc, u: float, text: str) -> None:
    mfam, mweight = svg_font(TYPE_MONO)
    total = measure(TYPE_MONO, 12.0, text, 2.6)
    d.text(APP_X, APP_Y - 28, text, 12.0, mfam, mweight, INK[4], tracking=2.6, opacity=0.9 * u)
    d.line(APP_X + total + 18, APP_Y - 32, APP_X + APP_W, APP_Y - 32, "#23252a", 1.0, opacity=0.8 * u)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
