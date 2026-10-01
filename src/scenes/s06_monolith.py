"""S6 MONOLITH — display glyphs as slabs in 3D space, scattered and reassembled,
with depth-of-field and a specular edge catching the accent light.

Depth of field is quantised into a handful of blur levels: rsvg has no cheap way
to vary a filter per element, and six levels is indistinguishable from continuous
at this scale.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY, TYPE_MONO, W
from easing import seg
from layout import cap_height, glyphs, measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow

WORD = "MONOLITH"
SIZE = 300.0
BASE_Y = H * 0.56

# Depth-of-field blur levels, in px.
DOF_LEVELS = (0.0, 1.4, 3.0, 5.2, 8.0, 12.0)


def draw(clock) -> str:
    d = Doc()
    fam, weight = svg_font(TYPE_DISPLAY)
    size = SIZE
    tracking = -11.0
    gl = glyphs(TYPE_DISPLAY, size, WORD, tracking)
    total = measure(TYPE_DISPLAY, size, WORD, tracking)
    x0 = W / 2 - total / 2
    cap = cap_height(TYPE_DISPLAY, size)

    # Filters for the DOF levels, created once and referenced by index.
    dof = [d.blur(s) if s > 0.05 else None for s in DOF_LEVELS]

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        _slab(d, clock, i, n, ch, x0 + dx, BASE_Y, size, fam, weight, cap, dof)

    _floor(d, clock)
    _caption(d, clock)
    return d.render()


def _scatter(i: int, n: int, t: float) -> tuple[float, float, float, float]:
    """(dx, dy, dz, spin) for a glyph while the word is scattered.

    Bounded so the slabs stay legible: the point is depth and reorganisation, not
    dispersal off the edges of the frame.
    """
    # Golden angle around the centre, so the scatter never looks gridded.
    ang = i * 2.399963 + t * 0.42
    r = 0.55 + ((i * 7919) % 7) / 7.0 * 0.45
    dx = math.cos(ang) * 250 * r
    dy = math.sin(ang) * 110 * r
    dz = math.sin(ang * 0.7 + i) * 900
    spin = math.sin(t * 0.8 + i * 0.7) * 18
    return dx, dy, dz, spin


def _slab(d: Doc, c, i: int, n: int, ch: str, x: float, y: float, size: float,
          fam: str, weight: int, cap: float, dof: list) -> None:
    appear = seg(c.u, 0.0, 0.22, "out")
    if appear <= 0:
        return

    # The word assembles, holds, then pulls apart again before settling.
    assemble = seg(c.u, 0.04, 0.34, "expo")
    scatter_phase = seg(c.u, 0.44, 0.30, "inout")
    return_phase = seg(c.u, 0.74, 0.26, "expo")

    # Depth offset, staggered so the word resolves back-to-front.
    order = (i / max(n - 1, 1)) * 0.22
    asm = seg(assemble, order, 0.78, "expo")
    ret = seg(return_phase, order, 0.78, "expo")

    sdx, sdy, sdz, sspin = _scatter(i, n, c.t)

    # Blend: assembled -> scattered -> assembled.
    t_out = scatter_phase
    t_back = return_phase
    dx = sdx * t_out * (1.0 - t_back)
    dy = sdy * t_out * (1.0 - t_back)
    dz = sdz * t_out * (1.0 - t_back)
    spin = sspin * t_out * (1.0 - t_back)

    # Perspective: further from the viewer, smaller and dimmer.
    persp = 1.0 / (1.0 + dz / 2600.0)
    sc = (0.80 + 0.20 * persp) * asm
    gx = x + dx
    gy = y + dy

    op = appear * asm * (0.62 + 0.38 * persp)

    # Depth of field by |dz|, quantised to the level list.
    lvl = min(range(len(DOF_LEVELS)), key=lambda k: abs(DOF_LEVELS[k] - abs(dz) / 260.0))
    fid = dof[lvl]

    # The slab face, plus an offset dark copy behind it for thickness.
    with d.group(transform=_tf(gx, gy, sc, spin)) as _:
        # Depth face: a sheared copy reading as the slab's side.
        skew = clamp(dz / 2400.0) * 26
        d.add(
            f'<g transform="translate({_n(0.5 * skew)} {_n(-0.35)})">'
            f'<text x="0" y="0" font-family="{fam}" font-size="{_n(size)}" font-weight="{weight}" '
            f'fill="rgba(255,255,255,0.055)">{_esc(ch)}</text></g>'
        )
        # Front face, tinted by depth.
        col = mix_hex(INK[1], ACCENT, clamp(0.30 - dz / 5200.0))
        d.text(0, 0, ch, size, fam, weight, col, opacity=op, filt=fid)
        # Specular edge: a bright hairline along the top-left of the glyph.
        spec = clamp((1.0 - dz / 2400.0)) * 0.7
        if spec > 0.05:
            d.text(
                0, 0, ch, size, fam, weight, "none",
                stroke=ACCENT_BRIGHT, stroke_width=1.6, opacity=spec * 0.5, filt=fid,
            )

    if lvl >= 4 and asm > 0.5:
        glow(d, gx, gy - cap / 2, 60 * sc, ACCENT, 0.22 * op)


def _floor(d: Doc, c) -> None:
    """A soft reflection plane, so the slabs have something to sit above."""
    u = seg(c.u, 0.10, 0.3, "out")
    if u <= 0:
        return
    y = BASE_Y + 210
    blur = d.blur(34)
    gid = d.linear_gradient(
        [(0.0, ACCENT, 0.16), (0.5, ACCENT, 0.05), (1.0, ACCENT, 0.0)],
        x1=0, y1=y, x2=0, y2=y + 200, units="userSpaceOnUse",
    )
    d.rect(W * 0.12, y, W * 0.76, 200, fill=f"url(#{gid})", filt=blur, opacity=u)


def _caption(d: Doc, c) -> None:
    u = seg(c.u, 0.30, 0.24, "out")
    if u <= 0:
        return
    mfam, mweight = svg_font(TYPE_MONO)
    label = "DEPTH  ·  SIX LEVELS OF FOCUS"
    fs = 14.0
    tr = 3.4
    mw = measure(TYPE_MONO, fs, label, tr)
    d.text(W / 2 - mw / 2, 150, label, fs, mfam, mweight, INK[4], tracking=tr, opacity=0.8 * u)


def _tf(x: float, y: float, scale: float, spin: float) -> str:
    return (
        f"translate({_n(x)} {_n(y)}) rotate({_n(spin)}) scale({_n(scale)}) translate(0 0)"
    )


def _n(v: float) -> str:
    s = f"{round(float(v), 3):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
