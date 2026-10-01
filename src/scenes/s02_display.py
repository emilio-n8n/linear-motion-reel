"""S2 DISPLAY — type as the subject, and three different reveal mechanics
across three words.

The through-line: each word arrives by a different route, but all three settle
with the same counter-tracking (the letters open from -0.06em to -0.01em as they
land) so the scene reads as one system.
"""

from __future__ import annotations

import math

from brand import ACCENT, ACCENT_BRIGHT, H, INK, TYPE_DISPLAY, TYPE_DISPLAY_XB, TYPE_MONO, W
from easing import ez, seg
from layout import cap_height, glyphs, measure, svg_font
from stock import clamp, mix_hex
from svg import Doc, glow, transform

SIZE = 232.0


def draw(clock) -> str:
    d = Doc()
    # Three words, each with its own reveal, evenly divided across the scene.
    beats = [
        (0.00, 0.30, "PRECISE", "wipe"),
        (0.30, 0.60, "WEIGHTED", "iris"),
        (0.60, 0.92, "ALIVE", "letter"),
    ]
    for start, end, word, mode in beats:
        local = (clock.u - start) / (end - start)
        if local < -0.06 or local > 1.10:
            continue
        if mode == "wipe":
            _wipe(d, clock, word, local)
        elif mode == "iris":
            _iris(d, clock, word, local)
        else:
            _per_letter(d, clock, word, local)
    return d.render()


def _tracking(local: float) -> float:
    """Counter-tracking: tight on arrival, opening as it settles."""
    tight, open_ = -0.062 * SIZE, -0.012 * SIZE
    return tight + (open_ - tight) * seg(local, 0.25, 0.75, "out")


def _base_y(size: float) -> float:
    return H / 2 + cap_height(TYPE_DISPLAY, size) / 2


# ------------------------------------------------------------------ wipe-up
def _wipe(d: Doc, c, word: str, u: float) -> None:
    """A soft-edged rule sweeps up and the text is revealed behind it."""
    if u <= 0:
        return
    fam, weight = svg_font(TYPE_DISPLAY)
    size = SIZE
    tr = _tracking(max(u, 0.0))
    gl = glyphs(TYPE_DISPLAY, size, word, tr)
    total = measure(TYPE_DISPLAY, size, word, tr)
    x0 = W / 2 - total / 2
    base = _base_y(size)

    # The reveal edge, with a gradient so it does not read as a hard wipe.
    p = seg(u, 0.0, 0.62, "expo")
    edge = base + cap_height(TYPE_DISPLAY, size) * (1.0 - 2.0 * clamp(p))
    soft = 130.0

    gid = d.linear_gradient(
        [(0.0, ACCENT, 0.0), (0.55, ACCENT_BRIGHT, 0.85), (0.78, INK[1], 0.0)],
        x1=0, y1=edge - soft, x2=0, y2=edge + 10, units="userSpaceOnUse",
    )
    d.rect(
        0, edge - soft, W, soft + 10,
        fill=f"url(#{gid})",
        extra=f' clip-path="url(#{d.clip_text(x0, base, word, size, fam, weight)})"',
    )
    # Leading edge line itself.
    d.line(0, edge, W, edge, INK[1], 1.2, opacity=0.75)
    glow(d, W / 2, edge, 340, ACCENT_BRIGHT, 0.35)

    # The settled word, fading up under the sweep.
    op = seg(u, 0.30, 0.45, "out")
    if op > 0:
        d.text(x0, base, word, size, fam, weight, INK[1], tracking=tr, opacity=op)


# --------------------------------------------------------------------- iris
def _iris(d: Doc, c, word: str, u: float) -> None:
    """A circular mask opens past the type, then the mask itself dissolves."""
    if u <= 0:
        return
    fam, weight = svg_font(TYPE_DISPLAY_XB)
    size = SIZE * 0.86
    tr = _tracking(max(u, 0.0))
    gl = glyphs(TYPE_DISPLAY_XB, size, word, tr)
    total = measure(TYPE_DISPLAY_XB, size, word, tr)
    x0 = W / 2 - total / 2
    base = _base_y(size)
    cap = cap_height(TYPE_DISPLAY_XB, size)

    # Iris radius grows past the word's own diagonal.
    need = math.hypot(total, cap) * 0.62
    r = need * 1.18 * seg(u, 0.0, 0.70, "expo")

    cid = d.clip_circle(W / 2, base - cap / 2, r)
    d.add(f'<g clip-path="url(#{cid})">')
    # Fill with a vertical accent ramp so the reveal has colour, not just alpha.
    gid = d.linear_gradient(
        [(0.0, INK[1], 1.0), (0.55, INK[1], 1.0), (1.0, ACCENT_BRIGHT, 1.0)],
        x1=0, y1=base - cap, x2=0, y2=base, units="userSpaceOnUse",
    )
    d.text(x0, base, word, size, fam, weight, f"url(#{gid})", tracking=tr)
    d.add("</g>")

    # The iris rim, thinning as it opens.
    rim = 1.0 - seg(u, 0.25, 0.65, "in")
    if rim > 0.01:
        d.circle(W / 2, base - cap / 2, r, fill="none", stroke=ACCENT_BRIGHT, stroke_width=1.4, opacity=0.5 * rim)

    # After the iris passes, add a bloom that peaks with it.
    peak = 1.0 - abs(u - 0.55) / 0.45
    if peak > 0:
        glow(d, W / 2, base - cap / 2, r * 0.8, ACCENT, 0.22 * max(peak, 0))


# ----------------------------------------------------------------- per-letter
def _per_letter(d: Doc, c, word: str, u: float) -> None:
    """Each glyph rises out of its own slice and overshoots into place."""
    if u <= 0:
        return
    fam, weight = svg_font(TYPE_DISPLAY)
    size = SIZE
    tr = _tracking(max(u, 0.0))
    gl = glyphs(TYPE_DISPLAY, size, word, tr)
    total = measure(TYPE_DISPLAY, size, word, tr)
    x0 = W / 2 - total / 2
    base = _base_y(size)
    cap = cap_height(TYPE_DISPLAY, size)

    n = len(gl)
    for i, (dx, ch, adv) in enumerate(gl):
        # Stagger from the centre outward, so the word opens like a seam.
        centre = (n - 1) / 2.0
        order = abs(i - centre) / max(centre, 1.0)
        local = seg(u, order * 0.30, 0.62, "back")
        if local <= 0:
            continue
        rise = (1.0 - local) * cap * 0.9
        bl = max(0.0, (1.0 - local) * 9.0)
        fid = d.blur(bl) if bl > 0.5 else None
        op = clamp(local * 1.4)
        d.text(x0 + dx, base + rise, ch, size, fam, weight, INK[1], opacity=op, filt=fid)

    # A rule under the word that draws to its measured width.
    ru = seg(u, 0.35, 0.5, "expo")
    if ru > 0:
        d.line(x0, base + 62, x0 + total * ru, base + 62, ACCENT, 2.0, opacity=0.8)

    # Small mono annotation — the label Linear would put on a spec.
    au = seg(u, 0.62, 0.3, "out")
    if au > 0:
        mfam, mweight = svg_font(TYPE_MONO)
        label = "EVERY GLYPH INDEPENDENT"
        fs = 14.0
        mw = measure(TYPE_MONO, fs, label, 3.2)
        d.text(W / 2 - mw / 2, base + 116, label, fs, mfam, mweight, INK[4], tracking=3.2, opacity=0.8 * au)
