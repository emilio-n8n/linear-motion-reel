"""S5 PRISM — a beam enters, hits a fan of spring-driven slats, and refracts into
a violet spectrum that sweeps the frame.

Additive light is faked with stacked low-opacity shapes because rsvg ignores
mix-blend-mode; on a near-black canvas that is visually equivalent to 'screen'.
"""

from __future__ import annotations

import math
from functools import lru_cache

from brand import ACCENT, ACCENT_BRIGHT, ACCENT_HOVER, COOL, H, INK, TYPE_DISPLAY, TYPE_MONO, W
from easing import Spring, seg
from layout import measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow

SLATS = 15
SLAT_X0 = W * 0.34
SLAT_GAP = 27.0
BEAM_Y = H * 0.5


def draw(clock) -> str:
    d = Doc()
    t = clock.t

    rot = _slat_angle(clock.f)
    _incoming_beam(d, clock)
    _slats(d, clock, rot)
    _spectrum(d, clock, rot)
    _prism_body(d, clock, rot)
    _caption(d, clock)

    return d.render()


def _target_at(t: float) -> float:
    return math.sin(t * 0.9) * 0.5 + math.sin(t * 0.37) * 0.28


@lru_cache(maxsize=1 << 12)
def _slat_angle(q: int) -> float:
    """Spring-driven slat angle, integrated from t=0 so it stays a pure function.

    A scene is a pure function of its frame index, so the spring cannot be carried
    as state between frames. It is integrated from the start of the scene and
    memoised per frame, which keeps any frame renderable on its own and in any
    order while only ever simulating the spring once per frame.

    Integrated numerically rather than eased, so the slats carry momentum through
    each retarget instead of restarting their curve.
    """
    s = Spring(0.0, stiffness=120.0, damping=13.0)
    dt = 1.0 / 240.0
    for i in range(q + 1):
        s.to(_target_at(i * dt))
        s.step(dt)
    return s.x


def _incoming_beam(d: Doc, c) -> None:
    u = seg(c.u, 0.0, 0.20, "out")
    if u <= 0:
        return
    y = BEAM_Y
    x0 = -200
    x1 = SLAT_X0 - 40
    gid = d.linear_gradient(
        [(0.0, COOL, 0.0), (0.35, COOL, 0.55), (1.0, INK[1], 0.95)],
        x1=x0, y1=y, x2=x1, y2=y, units="userSpaceOnUse",
    )
    soft = d.blur(9)
    d.path(f"M{x0} {y} L{x1} {y}", stroke=f"url(#{gid})", width=2.0, cap="round", opacity=0.9 * u)
    d.path(f"M{x0} {y} L{x1} {y}", stroke=f"url(#{gid})", width=16.0, cap="round", opacity=0.30 * u, filt=soft)
    d.path(f"M{x0} {y} L{x1} {y}", stroke=f"url(#{gid})", width=52.0, cap="round", opacity=0.12 * u, filt=d.blur(30))


def _prism_body(d: Doc, c, rot: float) -> None:
    """The entry face: a rotated quad the beam appears to strike."""
    u = seg(c.u, 0.06, 0.22, "out")
    if u <= 0:
        return
    cx, cy = SLAT_X0 + 30, BEAM_Y
    w, h = 150.0, 470.0
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    a = math.radians(rot * 26.0)
    ca, sa = math.cos(a), math.sin(a)
    rot_pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    d.add(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in rot_pts)}" fill="rgba(255,255,255,0.028)"/>')
    d.add(
        f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in rot_pts)}" '
        f'fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="1"/>'
    )


def _slats(d: Doc, c, rot: float) -> None:
    """The slat fan. Each slat is a thin bar whose tilt lags the prism."""
    u = seg(c.u, 0.10, 0.26, "out")
    if u <= 0:
        return
    for i in range(SLATS):
        # Slats nearer the pivot move more, like a real diffraction fan.
        f = i / (SLATS - 1)
        lag = rot * (0.5 + f * 0.9) * 26.0
        x = SLAT_X0 + 66 + i * SLAT_GAP
        local = seg(u, f * 0.25, 0.7, "expo")
        if local <= 0:
            continue
        ln = 300.0 * local
        a = math.radians(lag)
        dx, dy = math.sin(a) * ln, math.cos(a) * ln
        bright = 0.20 + 0.55 * (1.0 - abs(f - 0.5) * 1.4)
        d.line(x, BEAM_Y - dy / 2, x, BEAM_Y + dy / 2, INK[2], 1.6, opacity=max(0.08, bright) * local * 0.8)


def _spectrum(d: Doc, c, rot: float) -> None:
    """Refracted fan. Each output ray is a gradient beam with a soft companion."""
    u = seg(c.u, 0.24, 0.40, "expo")
    if u <= 0:
        return
    ox, oy = SLAT_X0 + 66, BEAM_Y
    spread = math.radians(-38.0 + rot * 20.0)

    for i in range(SLATS):
        f = i / (SLATS - 1)
        local = seg(u, f * 0.30, 0.62, "expo")
        if local <= 0:
            continue
        # Refraction angle spread across the fan.
        ang = spread * (f - 0.5) * 2.0
        reach = 1500.0 * local
        ex = ox + math.cos(ang) * reach
        ey = oy + math.sin(ang) * reach

        # The ramp runs accent -> cool, the only place two hues meet.
        col = mix_hex(ACCENT_BRIGHT, COOL, f)
        gid = d.linear_gradient(
            [(0.0, col, 0.95), (0.30, col, 0.5), (1.0, col, 0.0)],
            x1=ox, y1=oy, x2=ex, y2=ey, units="userSpaceOnUse",
        )
        wdt = 2.0 + 2.2 * math.sin(f * math.pi)
        d.path(f"M{ox} {oy} L{ex:.1f} {ey:.1f}", stroke=f"url(#{gid})", width=wdt, cap="round", opacity=0.85 * local)
        # Soft companion pass, stacked low-opacity to fake additive.
        d.path(
            f"M{ox} {oy} L{ex:.1f} {ey:.1f}",
            stroke=f"url(#{gid})", width=wdt * 7.0, cap="round",
            opacity=0.085 * local, filt=d.blur(24),
        )

    glow(d, ox, oy, 220 * u, ACCENT_BRIGHT, 0.42 * u)


def _caption(d: Doc, c) -> None:
    u = seg(c.u, 0.34, 0.2, "out")
    if u <= 0:
        return
    mfam, mweight = svg_font(TYPE_MONO)
    label = "ONE IN  ·  MANY OUT"
    fs = 14.0
    tr = 3.4
    mw = measure(TYPE_MONO, fs, label, tr)
    d.text(W / 2 - mw / 2, H - 148, label, fs, mfam, mweight, INK[4], tracking=tr, opacity=0.8 * u)
