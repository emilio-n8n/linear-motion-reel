"""Text layout: exact, shaping-aware metrics.

rsvg lays text out as a single centred or left-aligned run — it cannot be driven
glyph by glyph, which is the whole basis of the kinetic type in this reel. So the
positions are computed here and each glyph is emitted as its own positioned
element.

Metrics come from Pango, which is what librsvg itself uses to shape text. That
matters: it means the x positions computed here agree with what rsvg will actually
draw, including GPOS kerning and any ligature substitution, rather than being an
approximation from a different shaper. Ink extents (for cap height) are measured
the same way, so display type can be optically centred.
"""

from __future__ import annotations

import math
import os
from functools import lru_cache

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONTS = os.path.join(ASSETS, "fonts")

PANGO_SCALE = 1024

# (family, weight) as Pango/fontconfig see them. Families come from the font
# files installed into the local fontconfig dir by `make install-fonts`.
FACES = {
    "Inter-Regular": ("Inter", Pango.Weight.NORMAL),
    "Inter-Medium": ("Inter", Pango.Weight.MEDIUM),
    "Inter-SemiBold": ("Inter", Pango.Weight.SEMIBOLD),
    "Inter-Bold": ("Inter", Pango.Weight.BOLD),
    "Inter-ExtraBold": ("Inter", Pango.Weight.HEAVY),
    "Inter-Black": ("Inter", Pango.Weight.ULTRAHEAVY),
    "InterDisplay-Regular": ("Inter Display", Pango.Weight.NORMAL),
    "InterDisplay-Medium": ("Inter Display", Pango.Weight.MEDIUM),
    "InterDisplay-SemiBold": ("Inter Display", Pango.Weight.SEMIBOLD),
    "InterDisplay-Bold": ("Inter Display", Pango.Weight.BOLD),
    "InterDisplay-ExtraBold": ("Inter Display", Pango.Weight.HEAVY),
    "InterDisplay-Black": ("Inter Display", Pango.Weight.ULTRAHEAVY),
    "JetBrainsMono-Regular": ("JetBrains Mono", Pango.Weight.NORMAL),
    "JetBrainsMono-Medium": ("JetBrains Mono", Pango.Weight.MEDIUM),
    "JetBrainsMono-Bold": ("JetBrains Mono", Pango.Weight.BOLD),
}

# SVG font-weight values, for the <text> elements themselves.
SVG_WEIGHT = {
    Pango.Weight.NORMAL: 400,
    Pango.Weight.MEDIUM: 500,
    Pango.Weight.SEMIBOLD: 600,
    Pango.Weight.BOLD: 700,
    Pango.Weight.HEAVY: 800,
    Pango.Weight.ULTRAHEAVY: 900,
}

_surface = cairo.ImageSurface(cairo.FORMAT_A8, 8, 8)
_cairo = cairo.Context(_surface)
_ctx = PangoCairo.create_context(_cairo)


def _font_desc(face: str, size: float) -> Pango.FontDescription:
    fam, weight = FACES[face]
    fd = Pango.FontDescription(fam)
    fd.set_weight(weight)
    fd.set_absolute_size(size * PANGO_SCALE)
    return fd


@lru_cache(maxsize=1 << 14)
def _layout(face: str, size: float, text: str) -> Pango.Layout:
    lay = Pango.Layout.new(_ctx)
    lay.set_font_description(_font_desc(face, size))
    lay.set_text(text)
    return lay


def positions(face: str, size: float, text: str) -> list[float]:
    """Left edge of each character, in px, with kerning applied."""
    if not text:
        return []
    lay = _layout(face, size, text)
    return [lay.index_to_pos(i).x / PANGO_SCALE for i in range(len(text))]


def measure(face: str, size: float, text: str, tracking: float = 0.0) -> float:
    """Advance width in px. Tracking is added per character, matching SVG letter-spacing."""
    if not text:
        return 0.0
    lay = _layout(face, size, text)
    total = lay.index_to_pos(len(text)).x / PANGO_SCALE
    return total + tracking * len(text)


def glyphs(face: str, size: float, text: str, tracking: float = 0.0) -> list[tuple[float, str, float]]:
    """[(x_px, char, advance_px), ...].

    Spaces are dropped — they have no ink to animate — but still consume advance,
    so the run stays correctly spaced. A character whose shaping produced no ink
    (a control character) is dropped for the same reason.
    """
    lay = _layout(face, size, text)
    xs = [lay.index_to_pos(i).x / PANGO_SCALE for i in range(len(text) + 1)]
    out: list[tuple[float, str, float]] = []
    for i, ch in enumerate(text):
        adv = (xs[i + 1] - xs[i]) + tracking
        if ch.strip():
            out.append((xs[i] + tracking * i, ch, adv))
    return out


def ascent(face: str, size: float) -> float:
    fam, weight = FACES[face]
    fd = Pango.FontDescription(fam)
    fd.set_weight(weight)
    fd.set_absolute_size(size * PANGO_SCALE)
    font = PangoCairo.FontMap.get_default().load_font(_ctx, fd)
    return font.get_metrics().get_ascent() / PANGO_SCALE


def descent(face: str, size: float) -> float:
    fam, weight = FACES[face]
    fd = Pango.FontDescription(fam)
    fd.set_weight(weight)
    fd.set_absolute_size(size * PANGO_SCALE)
    font = PangoCairo.FontMap.get_default().load_font(_ctx, fd)
    return font.get_metrics().get_descent() / PANGO_SCALE


@lru_cache(maxsize=None)
def _ink_height(face: str, ch: str, size_q: int) -> float:
    """Ink height of one glyph at a quantised size, in px.

    Display type must be optically centred, and cap height is neither a fixed
    fraction of point size nor constant across the weights used here.
    """
    lay = Pango.Layout.new(_ctx)
    lay.set_font_description(_font_desc(face, size_q))
    lay.set_text(ch)
    ink, _logical = lay.get_pixel_extents()
    return float(ink.height)


def cap_height(face: str, size: float) -> float:
    return _ink_height(face, "H", max(1, round(size)))


def x_height(face: str, size: float) -> float:
    return _ink_height(face, "x", max(1, round(size)))


def svg_font(face: str) -> tuple[str, int]:
    fam, weight = FACES[face]
    return fam, SVG_WEIGHT[weight]


def type_on_arc(
    face: str,
    size: float,
    text: str,
    cx: float,
    cy: float,
    radius: float,
    mid_deg: float,
    tracking: float = 0.0,
) -> list[tuple[float, float, float, str]]:
    """Place glyphs along a circular arc — rsvg has no textPath, so we do it here.

    Returns [(x, y, rotation_deg, char), ...] with the run centred on mid_deg.
    """
    gl = glyphs(face, size, text, tracking)
    if not gl:
        return []
    total = sum(g[2] for g in gl)
    start = math.radians(mid_deg) - (total / max(radius, 1e-6)) / 2.0
    out = []
    pos = 0.0
    for _dx, ch, adv in gl:
        ang = start + (pos + adv / 2.0) / max(radius, 1e-6)
        out.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang), math.degrees(ang) + 90.0, ch))
        pos += adv
    return out
