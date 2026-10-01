"""S3 LATTICE — 400+ elements on phase-offset wavefronts, then a synchronised
reorganisation into a rotating isometric structure.

This is the timing showpiece: nothing here is individually interesting, the
interest is entirely in hundreds of things agreeing on when to move.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_MONO, W
from easing import ez, seg
from layout import measure, svg_font
from stock import clamp, mix_hex, project_iso
from svg import Doc, glow

# Field extent and density.
NX, NY = 27, 17
SPACING_X = 62.0
SPACING_Y = 62.0
ORIGIN_X = W / 2 - (NX - 1) * SPACING_X / 2
ORIGIN_Y = H / 2 - (NY - 1) * SPACING_Y / 2

# Isometric target: a stack of rings.
RINGS = 5
PER_RING = 16
RING_R = 232.0
RING_GAP = 116.0

TOTAL = NX * NY


def draw(clock) -> str:
    d = Doc()
    # Phase 1 fills the screen with a wavefront. Phase 2 pulls everything into
    # the iso stack. Phase 3 holds it turning.
    pts = []
    for iy in range(NY):
        for ix in range(NX):
            pts.append(_node(d, clock, ix, iy))
    _caption(d, clock)
    return d.render()


def _hash01(i: int, salt: int) -> float:
    """Deterministic float in [0,1) from an index.

    Integer mixing, because a plain LCG's low bits correlate and would put nodes
    into visible diagonal stripes rather than filling the grid.
    """
    h = (i + 1) * 0x9E3779B1 + salt * 0x85EBCA6B
    h &= 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 0x7FEB352D) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x846CA68B) & 0xFFFFFFFF
    h ^= h >> 16
    return h / 0x100000000


def _wave_target(ix: int, iy: int) -> tuple[float, float]:
    return ORIGIN_X + ix * SPACING_X, ORIGIN_Y + iy * SPACING_Y


def _iso_target(ix: int, iy: int, rot: float) -> tuple[float, float, float]:
    """Assign each node to a ring, then project it into an iso stack.

    The mapping is spatial rather than index-based: a node's radius in the grid
    picks its ring, so the stack inherits the shape of the field it came from
    instead of looking arbitrarily assigned.
    """
    i = iy * NX + ix
    # Radius in grid units, normalised to 0..1.
    gx = (ix - (NX - 1) / 2.0) / ((NX - 1) / 2.0)
    gy = (iy - (NY - 1) / 2.0) / ((NY - 1) / 2.0)
    rad_grid = math.hypot(gx, gy)
    ring = min(RINGS - 1, int(rad_grid * RINGS))
    # Angle around the stack follows the node's own bearing.
    bearing = math.atan2(gy, gx)
    jitter = _hash01(i, 7) - 0.5

    rad = RING_R * (0.30 + 0.16 * ring) * (1.0 + jitter * 0.16)
    x = math.cos(bearing) * rad
    z = math.sin(bearing) * rad
    y = (ring - (RINGS - 1) / 2.0) * RING_GAP + jitter * 30.0

    ax = 0.62 + 0.10 * math.sin(rot * 0.5)
    sx, sy = project_iso(x, y, z, ax, rot * 0.5 + 0.5, 1.0, W / 2, H / 2 - 20)
    return sx, sy, y


def _node(d: Doc, c, ix: int, iy: int) -> None:
    i = iy * NX + ix
    wx, wy = _wave_target(ix, iy)
    rot = c.t * 0.42
    sx, sy, depth = _iso_target(ix, iy, rot)

    # Distance from the wave's origin, which sets the phase.
    dx, dy = ix - (NX - 1) / 2.0, iy - (NY - 1) / 2.0
    dist = math.hypot(dx, dy) / 12.0

    # Phase 1: a radial wavefront pulses outward.
    w1 = seg(c.u, 0.0, 0.42, "out")
    if w1 > 0:
        phase = (dist * 2.4 - c.t * 1.55) % 1.0
        # A narrow gaussian band, so the wavefront is a travelling ring rather
        # than a general brightening.
        pulse = math.exp(-((phase - 0.12) ** 2) / 0.006) if w1 > 0.2 else 0.0
        r = 2.6 + 7.0 * pulse * w1
        op = (0.34 + 0.60 * pulse) * w1
        col = ACCENT_BRIGHT if pulse > 0.45 else INK[3]
        d.circle(wx, wy, r, fill=col, opacity=min(op, 0.95))

    # Phase 2: reorganisation. Nodes take off from the grid and fly to the stack.
    fly = seg(c.u, 0.44, 0.44, "inout")
    if fly <= 0:
        return

    # Per-node delay ordered by distance from centre, so the collapse reads as
    # one implosion rather than 459 simultaneous jumps.
    order = dist * 0.34
    local = seg(fly, order, 0.66, "circ")
    # Lift the node up off the plane mid-flight.
    lift = math.sin(clamp(local) * math.pi) * 120.0

    x = wx + (sx - wx) * local
    y = wy + (sy - wy) * local - lift

    # Size and colour by depth once settled, so the stack has front and back.
    shade = clamp((depth + (RINGS - 1) * RING_GAP / 2) / ((RINGS - 1) * RING_GAP))
    r = 2.4 + 3.8 * local
    op = (0.42 + 0.52 * local) * (0.5 + 0.5 * shade)
    # Accent on a sparse subset, so the eye has anchors inside the structure.
    accent_node = (i % 11 == 0)
    col = mix_hex(ACCENT, ACCENT_BRIGHT, shade) if accent_node else mix_hex(INK[4], INK[2], shade)

    d.circle(x, y, r, fill=col, opacity=min(op, 0.95))

    if accent_node and local > 0.6:
        glow(d, x, y, 26 * local, ACCENT, 0.34 * local)


def _caption(d: Doc, c) -> None:
    u = seg(c.u, 0.50, 0.2, "out")
    if u <= 0:
        return
    mfam, mweight = svg_font(TYPE_MONO)
    label = f"{TOTAL} NODES  ·  ONE CLOCK"
    fs = 14.0
    tr = 3.4
    mw = measure(TYPE_MONO, fs, label, tr)
    d.text(W / 2 - mw / 2, 148, label, fs, mfam, mweight, INK[4], tracking=tr, opacity=0.85 * u)
