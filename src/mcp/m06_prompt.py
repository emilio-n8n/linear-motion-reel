"""M6 PROMPT — the ask, and four tools answering at once.

The brief's centrepiece. The question types itself into the composer, the send
arrow is pressed, the Claude asterisk pulses, and four parallel actions animate
in with their tools' marks — showing that the answer is being assembled from
every connected system rather than from one.

The craft is the parallelism. Each row runs on its own clock and they overlap
heavily; if they were staggered end-to-end it would read as a sequence of four
tasks instead of four jobs happening at once.
"""

from __future__ import annotations

import math

from components import action_row, asterisk, cursor_pointer, prompt_bar, tool_glyph
from easing import seg
from layout import measure, svg_font
from svg import Doc
from tokens import (
    CORAL,
    H2,
    LEAD,
    CORAL_DEEP,
    H,
    INK,
    INK_2,
    INK_3,
    INK_4,
    PAPER,
    PAPER_DEEP,
    SANS,
    SANS_MED,
    SANS_REG,
    SERIF,
    W,
)

QUERY = "How's the beta going? Put together an update and file tickets for the top customer requests."

# (tool key, verb, detail, start, duration) — the four parallel jobs. The windows
# overlap deliberately: that overlap is what makes them read as concurrent.
ACTIONS = [
    ("figma", "Fetching", "active users and conversions…", 0.030, 0.46),
    ("slack", "Checking", "customer calls…", 0.070, 0.44),
    ("linear", "Filing tickets", "for top requests…", 0.105, 0.50),
    ("canva", "Writing", "beta update…", 0.140, 0.52),
]

BAR_W = 1180.0
BAR_X = (W - BAR_W) / 2


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    arrive = seg(clock.u, 0.01, 0.14, "out")
    typing = seg(clock.u, 0.05, 0.26, "linear")
    send = seg(clock.u, 0.335, 0.05, "circ")
    # The composer contracts and lifts to make room for the action list.
    clear = seg(clock.u, 0.42, 0.16, "inout")
    pulse = seg(clock.u, 0.40, 0.52, "inout")
    done = seg(clock.u, 0.90, 0.09, "out")

    typed = QUERY[: max(0, int(typing * (len(QUERY) + 1)))]

    if arrive > 0:
        _heading(d, arrive, clear)
        _composer(d, typed, typing, send, clear, arrive)

    if pulse > 0 and clear > 0.02:
        _centre_mark(d, clock, pulse, clear)

    if clear > 0.05:
        _actions(d, clear, done)

    return d.render()


def _heading(d: Doc, u: float, clear: float) -> None:
    """A quiet line above the composer, which the composer then replaces."""
    op = u * (1.0 - seg(clear, 0.0, 0.6, "in"))
    if op <= 0.01:
        return
    fam, weight = svg_font(SERIF)
    text = "One question. Every system."
    size = H2
    tw = measure(SERIF, size, text, -0.6)
    d.text(W / 2 - tw / 2, H * 0.30, text, size, fam, weight, INK,
           tracking=-0.6, opacity=op)


def _composer(d: Doc, typed: str, typing: float, send: float, clear: float, arrive: float) -> None:
    """The composer, centred while typing then lifting clear of the results."""
    # Lifts and shrinks as the action list arrives, so the frame has room.
    y = H * 0.56 - 150.0 * clear
    s = 1.0 - 0.06 * clear
    op = arrive * (1.0 - seg(clear, 0.55, 0.45, "in"))
    if op <= 0.01:
        return

    # Two lines of text: measure and wrap by hand, because the renderer will not.
    lines = _wrap(typed, SANS_REG, 17.0, BAR_W - 190)
    with d.group(
        transform=(
            f"translate({W / 2:.2f} {y:.2f}) scale({s:.4f}) translate({-W / 2:.2f} {-y:.2f})"
        ),
        opacity=op,
    ):
        h = 62.0
        if len(lines) > 1:
            prompt_bar(d, BAR_X, y - (h - 62), BAR_W, h, "", opacity=1.0)
            # Whichever line is last carries the caret while typing.
            last = lines[-1]
            for i, ln in enumerate(lines):
                d.text(BAR_X + 58, y + 6 + i * 24, ln, 17.0, *svg_font(SANS_REG), INK, opacity=1.0)
            if typing < 1.0:
                lw = measure(SANS_REG, 17.0, last)
                d.rect(BAR_X + 61 + lw, y - 6 + (len(lines) - 1) * 24, 1.8, 22,
                       fill=CORAL_DEEP, opacity=1.0)
        else:
            prompt_bar(d, BAR_X, y - 31, BAR_W, h, typed,
                       caret=typing < 1.0 and typed != "", opacity=1.0, sending=send)

    # Cursor arrives on the send button and clicks.
    if send > 0.01 and clear < 0.4:
        sx = BAR_X + BAR_W - 40
        sy = y
        approach = seg(send, 0.0, 0.6, "out")
        cx = sx + 90 * (1.0 - approach)
        cy = sy + 70 * (1.0 - approach)
        ripple = max(0.0, math.sin(min(send / 0.8, 1.0) * math.pi)) if send < 0.8 else 0.0
        cursor_pointer(d, cx, cy, min(send * 5.0, 1.0), ripple, size=26)


def _wrap(text: str, face: str, size: float, max_w: float) -> list[str]:
    """Greedy wrap on measured width.

    The renderer lays text as a single run, so a composer holding a long sentence
    has to be broken into lines here or it overflows the field.
    """
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if measure(face, size, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _centre_mark(d: Doc, c, pulse: float, clear: float) -> None:
    """The asterisk pulsing between the composer and the results.

    It rises as the composer lifts, holds at the centre while the jobs run, then
    settles back as the list completes.
    """
    op = min(pulse * 2.4, 1.0) * (1.0 - seg(pulse, 0.82, 0.18, "in"))
    if op <= 0.01:
        return
    # Sits slightly above centre while the list is on screen.
    y = H * 0.40 - 30.0 * clear
    r = 30.0 + 5.0 * math.sin(c.t * 5.2) * pulse
    # A soft halo, so the pulse reads even at small radius.
    for k in range(3):
        d.circle(W / 2, y, r * (1.5 + k * 0.55), fill=CORAL, opacity=0.035 * op)
    asterisk(d, W / 2, y, r, op, CORAL)


def _actions(d: Doc, clear: float, done: float) -> None:
    """The four parallel jobs, then a closing line once they land."""
    n = len(ACTIONS)
    list_y = H * 0.50
    row_h = 64.0
    w = 900.0
    x = W / 2 - w / 2

    latest = 0.0
    for i, (key, verb, detail, start, dur) in enumerate(ACTIONS):
        local = seg(clear, start, dur, "out")
        latest = max(latest, local)
        if local <= 0:
            continue
        # Rows fade in from the left, as if being added to a list.
        op = clear * min(local * 3.0, 1.0)
        with d.group(transform=f"translate({(1.0 - min(local * 3.0, 1.0)) * -26:.2f} 0)"):
            action_row(d, x, list_y + i * row_h, w, key, verb, detail, local, opacity=op)

    # A closing line, so the beat resolves rather than just stopping.
    if done > 0.01 and latest > 0.6:
        text = "Four systems. No setup."
        fam, weight = svg_font(SERIF)
        size = LEAD
        tw = measure(SERIF, size, text, -0.4)
        d.text(W / 2 - tw / 2, list_y + n * row_h + 46, text, size, fam, weight, INK,
               tracking=-0.4, opacity=done)
