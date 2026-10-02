"""M1 ORG — the organisation-wide switch.

The brief's cold open: a Connectors panel with a master switch off and every
integration dark. A hand clicks the master, it goes blue, and the whole list
cascades on behind it. Then the panel eases left and the proposition lands in
serif.

The craft is the cascade. Each row's toggle is driven by its own delayed
progress, and the delay is front-loaded so the list resolves as one gesture
rather than a staircase.
"""

from __future__ import annotations

import math

from camera import Z_BACKDROP, Z_BEHIND, Z_CONTROL, Z_NEAR, Z_SURFACE, Camera, Rig
from components import connector_row, cursor_hand, master_row, popover
from easing import seg
from layout import measure, svg_font
from marks import CONNECTORS
from svg import Doc
from tokens import (
    CORAL_DEEP,
    H1,
    INK,
    MARGIN,
    PAPER,
    PAPER_LINE,
    SANS,
    SANS_MED,
    SERIF,
    SANS_REG,
    W,
    H,
)

PANEL_W = 540.0
PANEL_X = 168.0
PANEL_Y = 214.0
ROW_H = 52.0

# Panel geometry is derived from its content rather than hard-coded, so adding a
# connector cannot leave dead space at the bottom or clip the last row.
HEAD_H = 68.0        # title band
MASTER_H = 68.0      # organisation switch
LIST_TOP = HEAD_H + MASTER_H + 8.0
PANEL_H = LIST_TOP + len(CONNECTORS) * ROW_H + 18.0

STATEMENT_1 = "Authorize MCP connectors"
STATEMENT_2 = "for your entire organization"

# Frames within this scene.
CLICK_AT = 0.30
CASCADE_AT = 0.36
SLIDE_AT = 0.62


def draw(clock) -> str:
    d = Doc(bg=PAPER)

    panel_in = seg(clock.u, 0.02, 0.22, "expo")
    press = seg(clock.u, CLICK_AT - 0.04, 0.10, "circ")
    master_on = seg(clock.u, CLICK_AT, 0.10, "expo")
    cascade = seg(clock.u, CASCADE_AT, 0.26, "expo")
    slide = seg(clock.u, SLIDE_AT, 0.24, "inout")
    text_in = seg(clock.u, SLIDE_AT + 0.10, 0.26, "out")

    # The panel eases left to make room for the statement, and lifts slightly.
    px = PANEL_X - 108.0 * slide
    py = PANEL_Y - 14.0 * slide

    # --- camera -------------------------------------------------------------
    # A slow dolly that deepens as the master switch is thrown, plus a drift so
    # the frame is never still. The look-at point moves toward the toggle because
    # that is what the beat is about.
    dx, dy = Rig.drift(clock.u, amount=11.0, rate=0.8, phase=0.4)
    cam = Camera(
        x=W / 2 + dx - 250.0 * slide + 140.0 * press,
        y=H / 2 + dy - 90.0 * press,
        push=Rig.dolly_in(clock.u, 0.06, 0.62, 0.30, "inout"),
    )

    if panel_in > 0:
        # Backdrop wash, far behind everything.
        with d.group(transform=cam.transform(Z_BACKDROP)):
            d.rect(-200, -200, W + 400, H + 400, fill="#F6F2EA",
                   opacity=0.9 * panel_in)
            for i in range(1, 7):
                x = W * i / 7.0
                d.line(x, -200, x, H + 200, "#EFEAE0", 1.0, opacity=0.7 * panel_in)

        # The panel and everything on it share one layer. Depth is carried by the
        # panel's own shadow lifting it off the backdrop, and by the camera dolly
        # moving the backdrop against it — not by separating a control from the
        # surface it is drawn on, which slides the control out of alignment.
        with d.group(transform=cam.transform(Z_SURFACE)):
            surface = cam.scale(Z_SURFACE)
            popover(d, px, py, PANEL_W, PANEL_H, panel_in, depth=surface)
            d.text(px + 26, py + 38, "Connectors", 17.0, *svg_font(SANS), INK,
                   opacity=panel_in)
            d.line(px + 24, py + HEAD_H, px + PANEL_W - 24, py + HEAD_H, PAPER_LINE,
                   1.0, opacity=panel_in)
            d.line(px + 24, py + HEAD_H + MASTER_H, px + PANEL_W - 24,
                   py + HEAD_H + MASTER_H, PAPER_LINE, 1.0, opacity=panel_in)

            _master(d, px, py + HEAD_H, panel_in, master_on, press, surface)
            n = len(CONNECTORS)
            for i, (key, name) in enumerate(CONNECTORS):
                # Front-loaded stagger: the last row starts before the first ends.
                local = seg(cascade, (i / max(n - 1, 1)) * 0.55, 0.45, "expo")
                connector_row(d, px, py + LIST_TOP + i * ROW_H, PANEL_W, key, name,
                              local, opacity=panel_in, depth=surface)

    # The cursor is the nearest thing in the frame. It is unprojected onto its own
    # layer so it still lands on the switch, which lives on the surface.
    if panel_in > 0 and press > 0:
        with d.group(transform=cam.transform(Z_NEAR)):
            _cursor(d, cam, px, py, press)

    if text_in > 0:
        with d.group(transform=cam.transform(Z_BEHIND)):
            _statement(d, text_in, slide)

    return d.render()


def _master(d: Doc, px: float, py: float, opacity: float, on: float, press: float,
            depth: float = 1.0) -> None:
    """The master switch. The cursor is drawn separately, on the near layer."""
    master_row(d, px, py, PANEL_W, "Enable for organization", on, opacity, depth)


def _cursor_pos(px: float, py: float, on: float) -> tuple[float, float]:
    """Where the knob is, from master_row's own layout rather than by eye."""
    track_x = px + PANEL_W - 80
    track_y = py + 29
    return track_x + 13 + (52 - 26) * on, track_y


def _cursor(d: Doc, cam, px: float, py: float, press: float) -> None:
    """The hand, approaching the master switch and settling on it.

    The switch lives on the surface layer, so its screen position is projected
    from there and then unprojected onto the near layer the cursor is drawn on.
    Skipping that step is what makes a pointer miss the control it is aiming at.
    """
    wx, wy = _cursor_pos(px, py + HEAD_H, 0.0)
    sx, sy = cam.point(wx, wy, Z_SURFACE)
    cx, cy = cam.unproject(sx, sy, Z_NEAR)

    approach = seg(press, 0.0, 0.75, "out")
    x = cx + (1.0 - approach) * 52
    y = cy - 16 + (1.0 - approach) * 58
    # The ripple peaks just before the toggle moves.
    ripple = max(0.0, math.sin(min(press / 0.7, 1.0) * math.pi)) if press < 0.72 else 0.0
    cursor_hand(d, x, y, min(press * 6.0, 1.0), ripple, size=27)


def _statement(d: Doc, u: float, slide: float) -> None:
    """The proposition, in serif, arriving as the panel makes room."""
    fam, weight = svg_font(SERIF)
    size = H1
    x = PANEL_X + PANEL_W + 130 - 60 * slide
    base = H * 0.5 - 52

    for k, text in enumerate((STATEMENT_1, STATEMENT_2)):
        local = seg(u, k * 0.22, 0.78, "out")
        if local <= 0:
            continue
        # Lines rise into place, slightly tracked open, settling tight.
        tracking = -0.4 + 0.6 * (1.0 - local)
        rise = (1.0 - local) * 22
        ink = INK if k == 0 else CORAL_DEEP
        d.text(x, base + k * 106 + rise, text, size, fam, weight, ink,
               tracking=tracking, opacity=local)
        # A hairline that draws under the second line.
        if k == 1:
            tw = measure(SERIF, size, text, tracking)
            ru = seg(local, 0.55, 0.45, "expo")
            if ru > 0:
                d.line(x, base + k * 106 + 34, x + tw * ru, base + k * 106 + 34,
                       CORAL_DEEP, 2.0, opacity=0.5 * ru)


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
