"""S4 FIELD — a curl-noise vector field with ~2000 particles orbiting a moving
attractor, and an indigo comet threading through that displaces them.

The one scene whose motion is genuinely simulated rather than keyframed. Because
each frame is a pure function of its index, the whole trajectory is reproducible
from a seed with no integration state carried between frames.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, COOL, H, INK, TYPE_MONO, W
from easing import seg
from layout import measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow

# Particle budget. Particles are batched into a few <path> elements per lane
# rather than emitted individually: rsvg renders thousands of separate elements
# far more slowly than the same geometry in a handful of paths.
COUNT = 1500
# Sub-steps of advection per particle; also the trail length.
TRAIL_STEPS = 13
LANES = 5  # depth lanes, drawn back to front

# Vector field.
FIELD_SCALE = 1.0 / 620.0
CURL_T = 0.055


def draw(clock) -> str:
    d = Doc()
    t = clock.t

    attractor = _attractor(t)
    comet = _comet(t)

    _streamlines(d, t, attractor)
    _particles(d, clock, t, attractor, comet)
    _comet_head(d, t, comet)
    _labels(d, clock, attractor)

    return d.render()


def _attractor(t: float) -> tuple[float, float]:
    """Lissajous drift — never repeats within the scene, never leaves frame."""
    x = W / 2 + math.sin(t * 0.62) * 300 + math.sin(t * 0.23) * 110
    y = H / 2 + math.cos(t * 0.47) * 150 + math.cos(t * 0.31) * 70
    return x, y


def _comet(t: float) -> tuple[float, float, float]:
    """Comet on a wide arc, entering left and exiting right.

    Crosses the attractor near the middle of the scene, so the wake it leaves is
    the thing that reveals the field's structure rather than a passing distraction.
    """
    p = (t / 5.5) % 1.0
    x = -260 + (W + 520) * p
    y = H * 0.5 + math.sin(p * math.tau) * 150
    return x, y, p


def _hash01(i: int, salt: int) -> float:
    """Deterministic float in [0,1) from an index. Integer mixing, so no drift."""
    h = (i + 1) * 0x9E3779B1 + salt * 0x85EBCA6B
    h &= 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 0x7FEB352D) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x846CA68B) & 0xFFFFFFFF
    h ^= h >> 16
    return h / 0x100000000


def _field(x: float, y: float, t: float) -> tuple[float, float]:
    """Divergence-free field from the curl of a scalar noise potential.

    Sampling a scalar and taking its perpendicular derivative gives a field that
    swirls without the sources-and-sinks look of a plain gradient field.
    """
    a = math.sin(x * FIELD_SCALE + t * CURL_T) * math.cos(y * FIELD_SCALE * 1.3 - t * CURL_T * 0.8)
    b = math.cos(x * FIELD_SCALE * 1.1 - t * CURL_T * 0.6) * math.sin(y * FIELD_SCALE * 0.9 + t * CURL_T)
    # Curl of (a, b) in 2D.
    dx = -b * FIELD_SCALE * 0.9
    dy = a * FIELD_SCALE * 1.1
    m = math.hypot(dx, dy) or 1.0
    return dx / m, dy / m


def _streamlines(d: Doc, t: float, attractor: tuple[float, float]) -> None:
    """Faint flow lines, integrated forward, showing the field's structure."""
    u = seg(t / 5.5, 0.04, 0.22, "out")
    if u <= 0:
        return
    ax, ay = attractor
    lines = []
    for k in range(34):
        seed_a = k / 34.0 * math.tau + (k % 3) * 0.11
        x = ax + math.cos(seed_a) * 900
        y = ay + math.sin(seed_a) * 520
        pts = []
        for _ in range(52):
            fx, fy = _field(x, y, t)
            # Bend the flow toward the attractor so the lines read as a system.
            tx, ty = ax - x, ay - y
            tm = math.hypot(tx, ty) or 1.0
            fx += tx / tm * 0.55
            fy += ty / tm * 0.55
            fm = math.hypot(fx, fy) or 1.0
            x += fx / fm * 26
            y += fy / fm * 26
            pts.append(f"{x:.1f} {y:.1f}")
            if not (-400 < x < W + 400 and -400 < y < H + 400):
                break
        if len(pts) > 2:
            lines.append("M" + " L".join(pts))
    d.path(" ".join(lines), stroke=INK[4], width=1.0, opacity=0.22 * u)


def _particles(d: Doc, c, t: float, attractor: tuple[float, float], comet: tuple[float, float, float]) -> None:
    """Particles advected through the field, each drawn with a short trail.

    Every particle is integrated forward from its own seed for a per-particle
    number of steps, so position *and* trail come out of one deterministic pass.
    The step count advances with time, which is what makes the field read as
    flowing rather than as a static starfield.
    """
    u = seg(c.u, 0.0, 0.16, "out")
    if u <= 0:
        return
    ax, ay = attractor
    cx, cy, _ = comet

    lanes: list[list[str]] = [[] for _ in range(LANES)]

    for i in range(COUNT):
        r1 = _hash01(i, 0)
        r2 = _hash01(i, 1)
        r3 = _hash01(i, 2)
        lane = i % LANES
        speed = 5.0 + r3 * 7.0

        # Seed on a wide ring around the attractor, so the field has structure to
        # organise rather than starting from uniform noise.
        seed_a = r1 * math.tau
        seed_r = 180.0 + r2 * 900.0
        px = ax + math.cos(seed_a) * seed_r
        py = ay + math.sin(seed_a) * seed_r * 0.62

        # Life cycles: each particle loops on its own phase, so the field turns
        # over continuously instead of emptying or piling up. The step count
        # advances with time, which is what makes this read as flow.
        # Life cycles: each particle loops on its own phase, so the field turns
        # over continuously instead of emptying or piling up. The step count
        # advances with time, which is what makes this read as flow.
        life = (t * 0.16 + r3) % 1.0
        steps = int(life * TRAIL_STEPS) + 2

        trail: list[tuple[float, float]] = []
        bt = t - life * 0.9
        for _s in range(steps):
            bt += 0.011
            fx, fy = _field(px, py, bt)
            ddx, ddy = ax - px, ay - py
            dm = math.hypot(ddx, ddy) or 1.0
            pull = clamp(620.0 / dm) * 0.9
            fx += ddx / dm * pull
            fy += ddy / dm * pull
            cdx, cdy = px - cx, py - cy
            cm = math.hypot(cdx, cdy) or 1.0
            if cm < 300:
                shove = (1.0 - cm / 300.0) ** 2 * 2.6
                fx += cdx / cm * shove
                fy += cdy / cm * shove
            fm = math.hypot(fx, fy) or 1.0
            px += fx / fm * speed
            py += fy / fm * speed
            if not (-260 < px < W + 260 and -260 < py < H + 260):
                break
            trail.append((px, py))

        if not trail:
            continue
        hx, hy = trail[-1]
        # Opacity by distance to the attractor: bright where the system is dense.
        near = clamp(1.0 - math.hypot(hx - ax, hy - ay) / 760.0)
        op = (0.24 + 0.60 * near) * u
        cm = math.hypot(hx - cx, hy - cy)
        if cm < 300:
            op += (1.0 - cm / 300.0) ** 1.6 * 0.5
        if op <= 0.02:
            continue

        # Thin long trails so the geometry stays light, always keeping the head.
        head = len(trail) - 1
        if head > 3:
            pts = trail[::2]
            if pts[-1] != trail[-1]:
                pts.append(trail[-1])
            d_str = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        else:
            d_str = f"M{hx:.1f} {hy:.1f}h0.01"

        r = 1.5 + near * 2.0
        col = mix_hex(INK[2], ACCENT_BRIGHT, lane / (LANES - 1))
        # Streak behind a brighter head, so direction of travel is legible.
        lanes[lane].append(
            f'<path d="{d_str}" stroke="{col}" stroke-width="{r:.2f}" '
            f'stroke-linecap="round" fill="none" opacity="{min(op * 0.75, 0.9):.3f}"/>'
        )
        lanes[lane].append(
            f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{r * 0.95:.2f}" fill="{col}" '
            f'opacity="{min(op * 1.2, 0.95):.3f}"/>'
        )

    # Draw the deepest lanes first so the bright ones read on top.
    for lane in range(LANES - 1, -1, -1):
        if lanes[lane]:
            d.add("".join(lanes[lane]))


def _comet_head(d: Doc, t: float, comet: tuple[float, float, float]) -> None:
    x, y, p = comet
    u = seg(min(p * 3.0, 1.0), 0.0, 0.2, "out")
    fade = 1.0 - seg(p, 0.86, 0.14, "in")
    if u * fade <= 0.01:
        return
    glow(d, x, y, 120 * u, ACCENT_BRIGHT, 0.55 * u * fade)
    d.circle(x, y, 4.2, fill=INK[1], opacity=u * fade)
    # A short tail behind the head, along its direction of travel.
    dx = math.cos(p * math.tau) * 150
    dy = -math.sin(p * math.tau) * 60
    gid = d.linear_gradient(
        [(0.0, ACCENT_BRIGHT, 0.0), (1.0, COOL, 0.9)],
        x1=x - dx, y1=y - dy, x2=x, y2=y, units="userSpaceOnUse",
    )
    d.path(f"M{x - dx:.1f} {y - dy:.1f} L{x:.1f} {y:.1f}", stroke=f"url(#{gid})", width=2.4, cap="round", opacity=0.8 * u * fade)


def _labels(d: Doc, c, attractor: tuple[float, float]) -> None:
    u = seg(c.u, 0.10, 0.2, "out")
    if u <= 0:
        return
    mfam, mweight = svg_font(TYPE_MONO)
    for label, px, py in (
        ("CURL FIELD", 168, 152),
        (f"{COUNT} PARTICLES", 168, 152 + 30),
    ):
        d.text(px, py, label, 14.0, mfam, mweight, INK[4], tracking=3.2, opacity=0.8 * u)

    # A hairline reticle on the attractor.
    ax, ay = attractor
    r = 26
    d.circle(ax, ay, r, fill="none", stroke=ACCENT, stroke_width=1.0, opacity=0.5 * u)
    for a in (0, 90, 180, 270):
        d.line(
            ax + math.cos(math.radians(a)) * r * 0.55, ay + math.sin(math.radians(a)) * r * 0.55,
            ax + math.cos(math.radians(a)) * r * 1.5, ay + math.sin(math.radians(a)) * r * 1.5,
            ACCENT, 1.0, opacity=0.45 * u,
        )
