"""S1 ORIGIN — one point becomes a hairline, the hairline becomes a plane,
the plane becomes a lattice, and the camera settles.

The reel's thesis: everything that follows is the same system at higher density.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY, TYPE_MONO, W
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from svg import Doc, glow

# Ground-plane geometry.
ROWS, COLS = 13, 25
VP_X, VP_Y = W / 2, H * 0.5


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def draw(clock) -> str:
    d = Doc()

    _opening_point(d, clock)
    _plane(d, clock)
    _lattice(d, clock)
    _horizon(d, clock)
    _title(d, clock)

    return d.render()


# ----------------------------------------------------------------- 0.0 - 0.9s
def _opening_point(d: Doc, c) -> None:
    """A single point, breathing. The only thing on screen for the first frames."""
    appear = seg(c.u, 0.0, 0.10, "out")
    if appear <= 0:
        return
    r = 3.0 + 1.2 * math.sin(c.t * 2.2) * 0.5
    d.circle(VP_X, VP_Y, r * appear, fill=INK[1], opacity=0.95 * appear)
    glow(d, VP_X, VP_Y, 46 * appear, ACCENT_BRIGHT, 0.5 * appear)

    # A hairline snaps out of the point once it has settled.
    line_u = seg(c.u, 0.16, 0.20, "expo")
    if line_u > 0:
        w = 640 * line_u
        d.line(VP_X - w / 2, VP_Y, VP_X + w / 2, VP_Y, INK[3], 1.0, opacity=0.5 * line_u)


# ---------------------------------------------------------------- 0.5 - 2.2s
def _plane(d: Doc, c) -> None:
    """The hairline splits into depth rows, which then tilt back into a ground plane.

    Built as a real perspective construction: a row's half-width is linear in its
    depth, so rows converge toward the horizon and the columns drawn on top of
    them meet at a genuine vanishing point. Squaring the depth for y is what makes
    the spacing compress with distance the way a floor actually does.
    """
    t0 = 0.17
    u = seg(c.u, t0, 0.30, "expo")
    if u <= 0:
        return

    tilt = seg(c.u, t0 + 0.10, 0.42, "inout")
    # Half-width of the nearest row once the plane has fully tilted back.
    near_half = 1500.0

    rows: list[str] = []
    for i in range(ROWS):
        # depth 0 at the horizon, 1 nearest the viewer
        depth = i / (ROWS - 1)
        # Rows unfurl from the centre line outward, alternating.
        centre_out = 1.0 - abs(depth - 0.5) * 2.0
        local = seg(u, (1.0 - centre_out) * 0.26, 0.66, "expo")
        if local <= 0:
            continue
        dpt = depth * tilt
        half = near_half * dpt * local
        y = VP_Y + (dpt ** 2) * 330.0
        rows.append(f"M{_n(VP_X - half)} {_n(y)} L{_n(VP_X + half)} {_n(y)}")
    if rows:
        d.path(" ".join(rows), stroke=INK[4], width=1.0, opacity=0.5)


# ---------------------------------------------------------------- 1.2 - 3.4s
def _lattice(d: Doc, c) -> None:
    """Column members rise from the plane, converging on the vanishing point.

    Each column runs from the horizon down to the near edge of the plane at a
    fixed lateral position, which is what makes them read as one surface rather
    than a set of leaning lines.
    """
    t0 = 0.30
    u = seg(c.u, t0, 0.36, "expo")
    if u <= 0:
        return

    push = seg(c.u, 0.46, 0.54, "circ")
    tilt = seg(c.u, 0.27, 0.42, "inout")
    near_half = 1500.0

    cols: list[str] = []
    acc: list[str] = []
    for j in range(COLS):
        # lateral position in [-1, 1]
        lat = (j - (COLS - 1) / 2.0) / ((COLS - 1) / 2.0)
        # Columns arrive from the centre outward.
        local = seg(u, abs(lat) * 0.30, 0.62, "expo")
        if local <= 0:
            continue
        # At the horizon every column converges on the centre; near the viewer it
        # is at its full lateral offset.
        x_top = VP_X + lat * near_half * 0.10 * tilt
        x_bot = VP_X + lat * near_half * tilt * local
        # The camera push-in scales the whole plane about the vanishing point.
        s = 1.0 + push * 0.10
        x_top = VP_X + (x_top - VP_X) * s
        x_bot = VP_X + (x_bot - VP_X) * s
        y_top = VP_Y
        y_bot = VP_Y + (tilt ** 2) * 330.0 * local

        seg_d = f"M{_n(x_top)} {_n(y_top)} L{_n(x_bot)} {_n(y_bot)}"
        (acc if j % 6 == 0 else cols).append(seg_d)

    if cols:
        d.path(" ".join(cols), stroke=INK[4], width=1.0, opacity=0.32)
    if acc:
        d.path(" ".join(acc), stroke=ACCENT, width=1.4, opacity=0.6)

    glow(d, VP_X, VP_Y, 380 * u, ACCENT, 0.22 * u)


# ---------------------------------------------------------------- 2.4 - 4.0s
def _horizon(d: Doc, c) -> None:
    """A bright rule finds the vanishing point and the system gets a name."""
    u = seg(c.u, 0.58, 0.22, "expo")
    if u <= 0:
        return
    w = 1500 * u
    d.line(VP_X - w / 2, VP_Y, VP_X + w / 2, VP_Y, ACCENT_BRIGHT, 3.0, opacity=0.55 * u, filt=d.blur(10))
    d.line(VP_X - w / 2, VP_Y, VP_X + w / 2, VP_Y, INK[1], 1.0, opacity=0.85 * u)

    # Two travelling highlights, as if light were running along the rule.
    for k, delay in enumerate((0.05, 0.13)):
        p = seg(c.u, 0.62 + delay, 0.30, "inout")
        if p <= 0 or p >= 1:
            continue
        hx = VP_X - w / 2 + w * p
        d.circle(hx, VP_Y, 2.6, fill=INK[1], opacity=0.9)
        glow(d, hx, VP_Y, 30, ACCENT_BRIGHT, 0.5)


# ---------------------------------------------------------------- 3.2 - 5.0s
def _title(d: Doc, c) -> None:
    """The wordmark, letter by letter, out of the lattice."""
    u = seg(c.u, 0.72, 0.24, "out")
    if u <= 0:
        return

    word = "ORDER"
    size = 168.0
    fam, weight = svg_font(TYPE_DISPLAY)
    tracking = -7.0
    gl = glyphs(TYPE_DISPLAY, size, word, tracking)
    total = measure(TYPE_DISPLAY, size, word, tracking)
    x0 = W / 2 - total / 2
    cap = cap_height(TYPE_DISPLAY, size)
    baseline = VP_Y + cap / 2

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        # Front-loaded stagger: the word resolves as one gesture, not a ripple.
        local = seg(u, (i / max(n - 1, 1)) * 0.42, 0.58, "expo")
        if local <= 0:
            continue
        rise = (1.0 - local) * 46
        blur = (1.0 - local) * 7
        op = local
        fid = d.blur(blur) if blur > 0.4 else None
        d.text(
            x0 + dx, baseline + rise, ch, size, fam, weight, INK[1],
            opacity=op, filt=fid,
        )

    # A caption in mono, the way Linear labels things.
    cap_u = seg(c.u, 0.88, 0.12, "out")
    if cap_u > 0:
        label = "A SYSTEM, FROM ONE LINE"
        fs = 15.0
        mfam, mweight = svg_font(TYPE_MONO)
        mw = measure(TYPE_MONO, fs, label, 3.4)
        d.text(
            W / 2 - mw / 2, baseline + 84, label, fs, mfam, mweight, INK[3],
            tracking=3.4, opacity=0.0 + 0.75 * cap_u,
        )
