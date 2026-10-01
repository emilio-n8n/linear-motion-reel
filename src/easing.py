"""Easing. Cubic-bezier solved numerically, plus a real damped-spring integrator."""

from __future__ import annotations

import math

from stock import clamp, smootherstep

# Named curves, expressed as cubic-bezier control points (CSS convention).
CURVES = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "out": (0.16, 1.0, 0.3, 1.0),
    "in": (0.55, 0.0, 0.85, 0.35),
    "inout": (0.65, 0.0, 0.35, 1.0),
    "expo": (0.19, 1.0, 0.22, 1.0),
    "quint": (0.22, 1.0, 0.36, 1.0),
    "circ": (0.0, 0.55, 0.45, 1.0),
    "back": (0.34, 1.56, 0.64, 1.0),
}

_BEZ_CACHE: dict[str, list[float]] = {}


def _sample_bezier(name: str) -> list[float]:
    """LUT of the bezier so the per-frame solve is a table lookup, not Newton iterations."""
    if name in _BEZ_CACHE:
        return _BEZ_CACHE[name]
    x1, y1, x2, y2 = CURVES[name]
    n = 257
    xs, ys = [0.0], [0.0]
    for i in range(1, n):
        u = i / (n - 1)
        # invert x(u) -> t via bisection (monotonic, cheap, and done once per curve)
        lo, hi = 0.0, 1.0
        for _ in range(28):
            t = (lo + hi) * 0.5
            x = 3 * t * (1 - t) ** 2 * x1 + 3 * t * t * (1 - t) * x2 + t**3
            if x < u:
                lo = t
            else:
                hi = t
        t = (lo + hi) * 0.5
        y = 3 * t * (1 - t) ** 2 * y1 + 3 * t * t * (1 - t) * y2 + t**3
        xs.append(u)
        ys.append(y)
    _BEZ_CACHE[name] = ys
    return ys


def ez(u: float, curve: str = "out") -> float:
    """Ease a normalised 0..1 input with a named curve (extrapolates past the ends)."""
    ys = _sample_bezier(curve)
    if u <= 0.0:
        # Re-evaluate the true tail so in/out curves start from the right place.
        return bezier_eval(clamp(u, -0.35, 0.0), *CURVES[curve])
    if u >= 1.0:
        return bezier_eval(clamp(u, 1.0, 1.35), *CURVES[curve])
    f = u * (len(ys) - 1)
    i = int(f)
    if i >= len(ys) - 1:
        return ys[-1]
    return ys[i] + (ys[i + 1] - ys[i]) * (f - i)


def bezier_eval(u: float, x1: float, y1: float, x2: float, y2: float) -> float:
    lo, hi = -0.5, 1.5
    for _ in range(32):
        t = (lo + hi) * 0.5
        x = 3 * t * (1 - t) ** 2 * x1 + 3 * t * t * (1 - t) * x2 + t**3
        if x < u:
            lo = t
        else:
            hi = t
    t = (lo + hi) * 0.5
    return 3 * t * (1 - t) ** 2 * y1 + 3 * t * t * (1 - t) * y2 + t**3


def seg(u: float, start: float, dur: float, curve: str = "out") -> float:
    """Ease u across the window [start, start+dur] in normalised progress units.

    Clamped to 0 before the window and 1 after it. ez() deliberately extrapolates
    past the ends of a curve so in/out curves start from the right value, but
    scene code wants a hard floor: a panel that has not started moving must be at
    exactly zero, not a large negative number.
    """
    if dur <= 0:
        return 1.0 if u >= start else 0.0
    t = (u - start) / dur
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return ez(t, curve)


class Spring:
    """Damped harmonic oscillator, integrated at a fixed sub-step.

    Integrated numerically rather than solved analytically so it can be retargeted
    mid-flight (each scene re-seeds it when the choreography changes).
    """

    __slots__ = ("x", "v", "target", "k", "c", "_settled")

    def __init__(self, x: float = 0.0, stiffness: float = 170.0, damping: float = 22.0):
        self.x = x
        self.v = 0.0
        self.target = x
        self.k = stiffness
        self.c = damping
        self._settled = True

    def reset(self, x: float, target: float | None = None) -> "Spring":
        self.x = x
        self.v = 0.0
        self.target = x if target is None else target
        self._settled = False
        return self

    def to(self, target: float) -> "Spring":
        if target != self.target:
            self.target = target
            self._settled = False
        return self

    def step(self, dt: float) -> float:
        """Advance the simulation by one fixed sub-step."""
        a = -self.k * (self.x - self.target) - self.c * self.v
        self.v += a * dt
        self.x += self.v * dt
        return self.x

    def at(self, t: float, dt: float = 1.0 / 240.0) -> float:
        """Value after t seconds of simulation from the last reset/to().

        Integrates in place, so repeated calls accumulate. Scenes that need a
        value as a pure function of time should re-integrate from zero rather
        than rely on this, but it is convenient for one-shot settling.
        """
        if self._settled:
            return self.x
        for _ in range(min(int(t / dt), 8192)):
            self.step(dt)
        if abs(self.x - self.target) < 1e-4 and abs(self.v) < 1e-3:
            self.x = self.target
            self.v = 0.0
            self._settled = True
        return self.x

    def velocity(self) -> float:
        return self.v


def bounce(u: float, times: float = 2.0, decay: float = 0.42) -> float:
    """Damped oscillation that starts and ends at rest — for discrete 'pop' beats."""
    u = clamp(u)
    if u <= 0.0 or u >= 1.0:
        return 0.0
    return math.sin(u * math.pi * times) * (1.0 - u) ** decay


def pulse(u: float) -> float:
    """0 -> 1 -> 0 hump."""
    u = clamp(u)
    return math.sin(u * math.pi) ** 1.4


def stagger(i: int, n: int, spread: float = 1.0, offset: float = 0.0) -> float:
    """Per-index delay fraction, front-loaded so a group resolves as one gesture."""
    if n <= 1:
        return offset
    return offset + (i / (n - 1)) * spread
