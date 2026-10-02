"""M7 PACKSHOT — the close.

The brief: the tasks clear, the end title lands centred and restrained — a thin
outlined [ BETA ] badge above "Enterprise-managed authorization for MCP
connectors" — and the terracotta asterisk grows slightly before the word Claude
resolves beside it.

The craft is the hold. The last second barely moves, which is what makes the film
feel finished rather than cut off.
"""

from __future__ import annotations

import math

from components import asterisk, badge
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from sketch import line
from svg import Doc
from tokens import (
    CORAL,
    CORAL_DEEP,
    H,
    INK,
    INK_3,
    INK_4,
    PAPER,
    SANS,
    SANS_MED,
    SANS_REG,
    SERIF,
    W,
)

BADGE = "BETA"
TITLE_1 = "Enterprise-managed authorization"
TITLE_2 = "for MCP connectors"
WORDMARK = "Claude"


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    clear = seg(clock.u, 0.0, 0.16, "in")
    badge_in = seg(clock.u, 0.10, 0.20, "expo")
    title_in = seg(clock.u, 0.22, 0.26, "out")
    rule = seg(clock.u, 0.52, 0.22, "expo")
    mark = seg(clock.u, 0.62, 0.22, "expo")
    word = seg(clock.u, 0.80, 0.16, "out")
    # A barely-perceptible settle, so the closing frame is alive but still.
    settle = seg(clock.u, 0.90, 0.10, "out")

    _rules(d, clear, settle)
    if badge_in > 0:
        _badge(d, badge_in)
    if title_in > 0:
        _title(d, title_in)
    if rule > 0:
        _rule(d, rule)
    if mark > 0:
        _signature(d, clock, mark, word, settle)

    return d.render()


def _rules(d: Doc, clear: float, settle: float) -> None:
    """A whisper of the interface's grid remaining behind the title."""
    op = (1.0 - clear) * 0.5
    if op <= 0.01:
        return
    for i in range(1, 6):
        y = H * i / 6.0
        d.line(W * 0.18, y, W * 0.82, y, "#EFEBE3", 1.0, opacity=op)


def _badge(d: Doc, u: float) -> None:
    """The thin outlined badge, sitting above the title."""
    fam, weight = svg_font(SANS)
    tw = measure(SANS, 12.0, BADGE, 2.0)
    w = tw + 34
    x = W / 2 - w / 2
    y = H * 0.30
    # Draws open from the centre, so it reads as a stamp rather than a fade.
    s = 0.9 + 0.1 * u
    with d.group(
        transform=f"translate({W / 2:.2f} {y + 15:.2f}) scale({s:.3f}) translate({-W / 2:.2f} {-(y + 15):.2f})",
        opacity=min(u * 1.4, 1.0),
    ):
        badge(d, x, y, BADGE, opacity=1.0)


def _title(d: Doc, u: float) -> None:
    """Two serif lines, centred, settling into tight tracking."""
    fam, weight = svg_font(SERIF)
    size = 92.0
    base = H * 0.50
    for k, text in enumerate((TITLE_1, TITLE_2)):
        local = seg(u, k * 0.24, 0.76, "out")
        if local <= 0:
            continue
        tracking = -1.0 + 1.2 * (1.0 - local)
        rise = (1.0 - local) * 20
        tw = measure(SERIF, size, text, tracking)
        d.text(W / 2 - tw / 2, base + k * 88 + rise, text, size, fam, weight, INK,
               tracking=tracking, opacity=local)


def _rule(d: Doc, u: float) -> None:
    """A drawn hairline between the title and the signature."""
    y = H * 0.685
    half = 150.0 * u
    d.line(W / 2 - half, y, W / 2 + half, y, "#DDD6CA", 1.2, opacity=0.9)


def _signature(d: Doc, c, mark: float, word: float, settle: float) -> None:
    """The asterisk, then the wordmark resolving beside it.

    The mark grows slightly and the word slides out from it, which reads as the
    mark producing the name rather than the two arriving together.
    """
    y = H * 0.795
    base_r = 30.0
    # Grows a touch as the word arrives, so the pair feels joined.
    r = base_r * (1.0 + 0.10 * word) * (1.0 + 0.012 * math.sin(settle * math.pi))
    if word <= 0.01:
        asterisk(d, W / 2, y, r, mark, CORAL)
        return

    fam, weight = svg_font(SERIF)
    size = 84.0
    tw = measure(SERIF, size, WORDMARK, -1.4)
    gap = 22.0
    total = base_r * 1.32 * 2 + gap + tw
    x0 = W / 2 - total / 2

    asterisk(d, x0 + base_r * 1.32, y, r, mark, CORAL)
    # The word slides out of the mark.
    wx = x0 + base_r * 1.32 * 2 + gap + (1.0 - word) * -26
    d.text(wx, y + cap_height(SERIF, size) / 2, WORDMARK, size, fam, weight, INK,
           tracking=-1.4, opacity=word)
