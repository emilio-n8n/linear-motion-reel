"""M5 TOOLS — the connectors are already there.

The brief: push in on one employee's card, click the context button, and open a
menu showing every connector already active — the point being that nobody had to
authenticate anything individually. A thumbs-up confirms the state, and the menu
closes.

The craft is the push-in. It is a single camera move on a group transform, so
every element inside scales together; moving each element separately would make
the interface shear.
"""

from __future__ import annotations

import math

from camera import Z_BACKDROP, Z_BEHIND, Z_CONTROL, Z_NEAR, Z_RAISED, Z_SURFACE, Camera, Rig
from components import cursor_pointer, popover, tool_glyph, welcome_card
from easing import seg
from layout import measure, svg_font
from marks import CONNECTORS
from svg import Doc
from tokens import (
    BLUE,
    CARD,
    CARD_LINE,
    CORAL,
    CORAL_DEEP,
    H,
    INK,
    INK_2,
    INK_3,
    INK_4,
    PAPER,
    PAPER_DEEP,
    PAPER_LINE,
    SANS,
    SANS_MED,
    SANS_REG,
    SERIF,
    W,
)

CARD_W = 620.0
CARD_H = 232.0

# The card that pushes in, and the ones that recede around it.
FOCUS = ("Welcome,", "Chelsea", "Summarise this week's beta")

MENU_W = 300.0
# The first four connectors, as the brief lists them for this beat.
MENU_ITEMS = CONNECTORS[:6]


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    arrive = seg(clock.u, 0.02, 0.22, "expo")
    push = seg(clock.u, 0.16, 0.30, "inout")
    cursor_in = seg(clock.u, 0.42, 0.16, "out")
    press = seg(clock.u, 0.54, 0.10, "circ")
    menu = seg(clock.u, 0.62, 0.20, "back")
    ack = seg(clock.u, 0.80, 0.12, "out")
    close = seg(clock.u, 0.92, 0.08, "in")

    # The strongest move in the film: a real push-in toward the button, which is
    # what the beat is about. A true dolly, so the backdrop cards fall away while
    # the card and its control grow.
    cx, cy = _context_pos(W / 2 - CARD_W / 2, H / 2 - CARD_H / 2, CARD_W, CARD_H)
    dx, dy = Rig.drift(clock.u, amount=8.0, rate=1.0, phase=0.9)
    cam = Camera(
        x=W / 2 + dx + (cx - W / 2) * push * 0.55,
        y=H / 2 + dy + (cy - H / 2) * push * 0.55,
        push=1.0 + 0.85 * push - 0.10 * close,
    )

    if arrive > 0:
        # The other cards sit well behind, so the dolly separates them.
        with d.group(transform=cam.transform(Z_BEHIND), opacity=arrive):
            _backdrop_cards(d, push)

        with d.group(transform=cam.transform(Z_SURFACE), opacity=arrive):
            surface = cam.scale(Z_SURFACE)
            welcome_card(d, W / 2 - CARD_W / 2, H / 2 - CARD_H / 2, CARD_W, CARD_H,
                         FOCUS[0], FOCUS[1], suggestion=FOCUS[2], opacity=1.0,
                         depth=surface)
            _context_button(d, W / 2 - CARD_W / 2, H / 2 - CARD_H / 2, CARD_W, CARD_H,
                            press)

        # The menu and the cursor float above the card.
        if menu > 0.01:
            with d.group(transform=cam.transform(Z_CONTROL)):
                _menu(d, W / 2 - CARD_W / 2, H / 2 - CARD_H / 2, CARD_W, CARD_H,
                      menu, ack, close, cam.scale(Z_CONTROL))
        if cursor_in > 0 and close < 0.5:
            with d.group(transform=cam.transform(Z_NEAR)):
                _cursor(d, cam, cursor_in, press, close)

    return d.render()


def _backdrop_cards(d: Doc, push: float) -> None:
    """A hint of the other cards, fading as the camera commits to one."""
    op = (1.0 - push) * 0.5
    if op <= 0.01:
        return
    for i, (gx, gy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x = W / 2 + gx * 700 - 250
        y = H / 2 + gy * 300 - 95
        d.rect(x, y, 500, 190, fill=CARD, rx=14, opacity=op)
        d.rect(x, y, 500, 190, fill="none", stroke=CARD_LINE, width=1.0, rx=14, opacity=op)


def _context_button(d: Doc, x: float, y: float, w: float, h: float, press: float) -> None:
    """The + inside the composer, which the cursor is about to hit."""
    bx = x + 46
    by = y + h - 38
    # Slightly bluer on press, so the control responds to the click.
    d.circle(bx, by, 15, fill=PAPER_DEEP, opacity=1.0)
    if press > 0.01:
        d.circle(bx, by, 15, fill=BLUE, opacity=press * 0.9)
    col = "#FFFFFF" if press > 0.5 else INK_3
    d.path(
        f"M{bx - 7:.1f} {by:.1f} L{bx + 7:.1f} {by:.1f} "
        f"M{bx:.1f} {by - 7:.1f} L{bx:.1f} {by + 7:.1f}",
        stroke=col, width=1.8, cap="round", opacity=1.0,
    )
    return


def _context_pos(x: float, y: float, w: float, h: float) -> tuple[float, float]:
    return x + 46, y + h - 38


def _cursor(d: Doc, cam, u: float, press: float, close: float) -> None:
    """Cursor travels to the button, clicks, then leaves as the menu closes.

    The button lives on the surface layer, so its screen position is projected
    from there and unprojected onto the near layer the cursor is drawn on.
    """
    x = W / 2 - CARD_W / 2
    y = H / 2 - CARD_H / 2
    bx, by = _context_pos(x, y, CARD_W, CARD_H)
    bx, by = cam.point(bx, by, Z_SURFACE)
    bx, by = cam.unproject(bx, by, Z_NEAR)
    approach = seg(u, 0.0, 0.7, "out")
    cx = bx + 150 * (1.0 - approach) + 60 * close
    cy = by + 110 * (1.0 - approach) + 40 * close
    ripple = max(0.0, math.sin(min(press / 0.7, 1.0) * math.pi)) if 0 < press < 0.72 else 0.0
    cursor_pointer(d, cx, cy, min(u * 4.0, 1.0), ripple, size=27)


def _menu(d: Doc, cx: float, cy: float, w: float, h: float,
          menu: float, ack: float, close: float, depth: float = 1.0) -> None:
    """The connector menu, opening upward from the button.

    Positioned from the button it belongs to, so it stays anchored if the card
    or the composer moves.
    """
    bx, by = _context_pos(cx, cy, w, h)
    mh = 58 + len(MENU_ITEMS) * 38
    mx = bx - 18
    my = by - mh - 18
    # Grows upward from the button, as a menu anchored to it should.
    s = 0.92 + 0.08 * menu
    op = menu * (1.0 - close)
    if op <= 0.01:
        return

    with d.group(
        transform=(
            f"translate({bx:.2f} {by:.2f}) scale({s:.4f}) "
            f"translate({-bx:.2f} {-my - mh:.2f})"
        ),
        opacity=op,
    ):
        popover(d, mx, my, MENU_W, mh, 1.0, depth=depth)
        fam, weight = svg_font(SANS)
        d.text(mx + 20, my + 28, "Context", 13.0, fam, weight, INK, tracking=0.2)
        _thumbs_up(d, mx + MENU_W - 30, my + 23, min(ack * 1.6, 1.0))
        d.line(mx + 18, my + 44, mx + MENU_W - 18, my + 44, PAPER_LINE, 1.0)

        for i, (key, name) in enumerate(MENU_ITEMS):
            local = seg(menu, 0.15 + i * 0.10, 0.5, "out")
            if local <= 0:
                continue
            ry = my + 44 + 19 + i * 38
            tool_glyph(d, key, mx + 34, ry, 20, local)
            d.text(mx + 56, ry + 5, name, 14.0, *svg_font(SANS_REG), INK_2, opacity=local)
            # Already connected: a small filled dot, not a switch. The point is
            # that there is nothing left to do, so no control is offered.
            d.circle(mx + MENU_W - 32, ry, 5.5, fill=BLUE, opacity=local)
            _tick(d, mx + MENU_W - 32, ry, local)


def _tick(d: Doc, cx: float, cy: float, u: float) -> None:
    if u <= 0.01:
        return
    d.path(
        f"M{cx - 2.4:.1f} {cy:.1f} L{cx - 0.7:.1f} {cy + 1.8:.1f} L{cx + 2.6:.1f} {cy - 2.0:.1f}",
        stroke="#FFFFFF", width=1.5, cap="round", join="round", opacity=u,
    )


def _thumbs_up(d: Doc, cx: float, cy: float, u: float) -> None:
    """The acknowledgement mark: everything was already authorised."""
    if u <= 0.01:
        return
    d.circle(cx, cy, 13, fill="rgba(37,99,235,0.12)", opacity=u)
    d.path(
        f"M{cx - 5:.1f} {cy + 6:.1f} L{cx - 5:.1f} {cy - 1:.1f} "
        f"M{cx - 3.4:.1f} {cy + 6:.1f} L{cx - 3.4:.1f} {cy - 1.5:.1f} "
        f"C{cx - 3.4:.1f} {cy - 5.5:.1f} {cx - 1:.1f} {cy - 7:.1f} {cx + 0.4:.1f} {cy - 4:.1f} "
        f"L{cx + 1.6:.1f} {cy - 0.6:.1f} L{cx + 4.6:.1f} {cy - 0.6:.1f} "
        f"C{cx + 6.4:.1f} {cy - 0.6:.1f} {cx + 6.6:.1f} {cy + 1.4:.1f} {cx + 5.6:.1f} {cy + 2.4:.1f} "
        f"L{cx + 3.4:.1f} {cy + 6:.1f} Z",
        stroke=BLUE, width=1.5, cap="round", join="round", opacity=u,
    )
