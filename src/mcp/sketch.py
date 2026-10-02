"""Hand-drawn strokes.

The brief's signature element: felt-tip marks in terracotta that circle,
underline and connect things, to put a human hand back into a precise interface.

Emitting these as `<path stroke=...>` does not work — an SVG stroke has one
width for its whole length, so it reads as a vector line with a wobble, not as a
mark someone made. Instead each stroke is built as a **filled polygon** whose
width varies along its length, with a taper at both ends and a low-frequency
wobble in the centreline. That is what makes it read as ink.

Everything here is deterministic: given the same seed it draws the same mark on
every frame, which the pure-frame architecture requires.
"""

from __future__ import annotations

import math

from tokens import CORAL

# Points sampled along a stroke. Below ~40 the polygon facets become visible on
# long marks; above ~160 the SVG grows without changing the look.
SAMPLES = 96


def _noise(t: float, seed: int) -> float:
    """Smooth pseudo-noise in roughly [-1, 1].

    A sum of incommensurate sines rather than a random walk: it is deterministic,
    infinitely differentiable, and has the low-frequency character of a hand
    wobble. A random walk drifts and produces a stroke that visibly wanders off.
    """
    s = seed * 0.6180339887
    return (
        math.sin(t * 2.9 + s * 6.1) * 0.55
        + math.sin(t * 6.7 + s * 11.3) * 0.28
        + math.sin(t * 13.1 + s * 19.7) * 0.17
    )


def _taper(u: float, ends: float = 0.12) -> float:
    """Width multiplier: full through the middle, tapering to a point at each end.

    A felt tip does not start at full width — it lands. This is most of what
    separates a drawn mark from a stroked path.
    """
    if u < ends:
        return 0.35 + 0.65 * (u / ends) ** 0.7
    if u > 1.0 - ends:
        return 0.35 + 0.65 * ((1.0 - u) / ends) ** 0.7
    return 1.0


def _polygon(centre: list[tuple[float, float]], width: float, seed: int, waviness: float = 1.0) -> str:
    """Outline a centreline into a closed filled path with varying width."""
    n = len(centre)
    if n < 2:
        return ""
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(centre):
        u = i / (n - 1)
        # Tangent from neighbours, so the normal is correct through curves.
        px, py = centre[max(i - 1, 0)]
        nx, ny = centre[min(i + 1, n - 1)]
        tx, ty = nx - px, ny - py
        m = math.hypot(tx, ty) or 1.0
        # Normal, plus a little independent wobble in the width itself.
        ox, oy = -ty / m, tx / m
        w = width * _taper(u) * (1.0 + _noise(u * 3.1, seed + 5) * 0.16 * waviness)
        left.append((x + ox * w * 0.5, y + oy * w * 0.5))
        right.append((x - ox * w * 0.5, y - oy * w * 0.5))
    pts = left + right[::-1]
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for x, y in pts[1:]:
        d += f" L{x:.2f} {y:.2f}"
    return d + " Z"


def line(x0: float, y0: float, x1: float, y1: float, width: float = 5.0,
         seed: int = 0, wobble: float = 2.4, passes: int = 1,
         span: float = 1.0) -> list[str]:
    """A hand-drawn straight mark. Returns one path per pass.

    `span` < 1 draws only the leading fraction, so the mark can be animated on.
    The taper is applied across the *drawn* portion, so a half-drawn mark still
    has a proper landing and does not look like a line cut in half.
    """
    if span <= 0.001:
        return []
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    steps = max(4, int(SAMPLES * span))
    out = []
    for p in range(passes):
        centre = []
        for i in range(steps):
            u = (i / max(steps - 1, 1)) * span
            # Bow the line slightly, as a hand does, plus high-frequency wobble.
            n = _noise(u, seed + p * 17) * wobble
            bow = math.sin(u * math.pi) * wobble * 0.5 * _noise(0.5, seed + p * 3)
            centre.append((x0 + dx * u + nx * (n + bow), y0 + dy * u + ny * (n + bow)))
        out.append(_polygon(centre, width * (1.0 if p == 0 else 0.62), seed + p * 11))
    return out


def ring(cx: float, cy: float, rx: float, ry: float, width: float = 5.0,
         seed: int = 0, overshoot: float = 0.20, tilt: float = -0.03,
         passes: int = 2, span: float = 1.0) -> list[str]:
    """A hand-drawn loop around something.

    Two details do the work: the loop **overshoots** past its start rather than
    closing cleanly, and it is slightly tilted. A closed ellipse reads as a
    shape; an overshooting one reads as a gesture.

    `span` < 1 draws only the leading fraction, for animating the loop on.
    """
    out = []
    a0 = -0.42 * math.pi  # start at the lower left, as a right-hander would
    for p in range(passes):
        centre = []
        steps = max(8, int(SAMPLES * span))
        for i in range(steps):
            u = i / max(steps - 1, 1)
            # Overshoot: the arc runs past 2pi, then drifts outward slightly.
            a = a0 + (math.tau * (1.0 + overshoot * u * u)) * u
            ex = math.cos(a) * rx * (1.0 + 0.04 * u)
            ey = math.sin(a) * ry * (1.0 + 0.04 * u)
            # Rotate for the tilt, then add wobble.
            rx2 = ex * math.cos(tilt) - ey * math.sin(tilt)
            ry2 = ex * math.sin(tilt) + ey * math.cos(tilt)
            n = _noise(u, seed + p * 23) * width * 0.9
            centre.append((cx + rx2 + n * 0.6, cy + ry2 + n * 0.4))
        out.append(_polygon(centre, width * (1.0 if p == 0 else 0.7), seed + p * 13))
    return out


def stroke(points: list[tuple[float, float]], width: float = 5.0, seed: int = 0,
           wobble: float = 2.0, span: float = 1.0) -> str:
    """A hand-drawn mark through given points, for connectors and arrows."""
    steps = max(4, int(SAMPLES * span))
    n_src = len(points) - 1
    centre = []
    for i in range(steps):
        u = i / max(steps - 1, 1) * span
        # Sample the polyline at u.
        f = u * n_src
        k = min(int(f), n_src - 1)
        t = f - k
        x = points[k][0] + (points[k + 1][0] - points[k][0]) * t
        y = points[k][1] + (points[k + 1][1] - points[k][1]) * t
        n = _noise(u, seed) * wobble
        centre.append((x + n, y + n * 0.6))
    return _polygon(centre, width, seed)


def arc_arrow(x0: float, y0: float, x1: float, y1: float, lift: float = 90.0,
              width: float = 4.4, seed: int = 0, span: float = 1.0) -> tuple[str, tuple[float, float, float]]:
    """An arcing connector with an arrowhead.

    Returns (polygon for the shaft, (x, y, angle) for the head) so the head can be
    placed at the true end of the drawn portion rather than the nominal endpoint.
    """
    steps = max(6, int(SAMPLES * span))
    centre = []
    for i in range(steps):
        u = i / max(steps - 1, 1)
        uu = u * span
        x = x0 + (x1 - x0) * uu
        # Arc upward by `lift`, peaking mid-way.
        y = y0 + (y1 - y0) * uu - math.sin(uu * math.pi) * lift
        n = _noise(u, seed) * 1.8
        centre.append((x + n, y + n * 0.5))
    hull = _polygon(centre, width, seed)
    if len(centre) >= 2:
        (ax, ay), (bx, by) = centre[-2], centre[-1]
        ang = math.degrees(math.atan2(by - ay, bx - ax))
    else:
        ang = 0.0
    ex, ey = centre[-1] if centre else (x1, y1)
    return hull, (ex, ey, ang)


def arrowhead(x: float, y: float, angle_deg: float, size: float = 15.0,
              colour: str = CORAL) -> str:
    """A small filled triangle for the head of a drawn arrow."""
    a = math.radians(angle_deg)
    # Splay two barbs behind the tip.
    b1 = a + math.radians(152)
    b2 = a - math.radians(152)
    p1 = (x + math.cos(b1) * size, y + math.sin(b1) * size)
    p2 = (x + math.cos(b2) * size, y + math.sin(b2) * size)
    # Pull the tip slightly forward so the join with the shaft is hidden.
    tx, ty = x + math.cos(a) * size * 0.30, y + math.sin(a) * size * 0.30
    return (
        f"M{p1[0]:.2f} {p1[1]:.2f} L{tx:.2f} {ty:.2f} L{p2[0]:.2f} {p2[1]:.2f} "
        f"L{x + math.cos(a) * size * 0.05:.2f} {y + math.sin(a) * size * 0.05:.2f} Z"
    )
