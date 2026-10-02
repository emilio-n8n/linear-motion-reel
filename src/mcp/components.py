"""Interface primitives for the Claude / MCP film.

Everything is drawn on a light ground, which means depth comes from **shadows**,
not from light. On the dark reel, depth was stacked additive passes; here it is a
soft shadow under each raised surface. `shadow()` is the primitive that does it,
since rsvg has no feDropShadow.

Panels are white on cream with a 1px warm hairline and a soft shadow, matching the
brief's "macOS/Web épuré" register.
"""

from __future__ import annotations

import math

from layout import cap_height, measure, svg_font
from marks import asterisk, tool_glyph
from svg import Doc
from tokens import (
    BLUE,
    CARD,
    CARD_LINE,
    CORAL,
    CORAL_DEEP,
    CORAL_SOFT,
    INK,
    INK_2,
    INK_3,
    INK_4,
    MONO,
    PAPER,
    PAPER_DEEP,
    PAPER_LINE,
    SANS,
    SANS_BOLD,
    SANS_MED,
    SANS_REG,
    SERIF,
    SERIF_REG,
    TOGGLE_OFF,
    TOGGLE_ON,
)

RADIUS = 12.0


# ------------------------------------------------------------------ depth


def shadow(d: Doc, x: float, y: float, w: float, h: float, r: float = RADIUS,
           lift: float = 1.0, opacity: float = 1.0, depth: float = 1.0) -> None:
    """A soft shadow under a surface.

    Built from three offset rounded rects at decreasing opacity rather than a
    filter: on a light background a blurred black rect at low opacity reads
    correctly, and it costs one element per layer instead of a filter definition
    per surface. rsvg has no feDropShadow, so this is the only way to get real
    elevation.

    `depth` scales the shadow's spread and offset. Elements on the camera's
    near layers pass their projected scale here, which is what makes them read as
    floating above the surface rather than painted on it: a shadow that does not
    grow with proximity reads as a drop shadow filter, not as height.
    """
    if lift <= 0.001 or opacity <= 0.001:
        return
    layers = (
        (0.0, 3.0, 10.0, 0.055),
        (0.0, 8.0, 26.0, 0.045),
        (0.0, 18.0, 50.0, 0.030),
    )
    for dy, spread, _blur, alpha in layers:
        sp = spread * lift * depth
        d.rect(
            x - sp, y - sp + dy * lift * depth,
            w + sp * 2, h + sp * 2,
            fill=f"rgba(31,30,29,{alpha * opacity:.4f})", rx=r + sp,
        )


# ----------------------------------------------------------------- toggle


def toggle(d: Doc, x: float, y: float, w: float, h: float, on: float,
           opacity: float = 1.0) -> None:
    """A pill switch: grey at rest, blue when engaged, knob eased across.

    `on` is 0..1 so the transition can be animated rather than snapped. The knob
    is inset by half its height and travels the pill's width minus its diameter.
    """
    if opacity <= 0.001:
        return
    r = h / 2.0
    # Cross-fade the track colour rather than switching it.
    d.rect(x, y, w, h, fill=TOGGLE_OFF, rx=r, opacity=opacity)
    if on > 0.001:
        d.rect(x, y, w, h, fill=TOGGLE_ON, rx=r, opacity=on * opacity)
    kx = x + r + (w - h) * on
    # A soft contact shadow under the knob.
    d.circle(kx, y + r + 1.2, r - 1.0, fill="rgba(31,30,29,0.13)", opacity=opacity)
    d.circle(kx, y + r, r - 2.2, fill="#FFFFFF", opacity=opacity)


# ----------------------------------------------------------------- panels


def popover(d: Doc, x: float, y: float, w: float, h: float, reveal: float = 1.0,
            lift: float = 1.0, depth: float = 1.0) -> None:
    """A raised surface. `reveal` wipes it open from the top edge.

    `depth` is the projected scale of the layer this sits on, so its shadow can
    respond to the camera.
    """
    if reveal <= 0.001:
        return
    shadow(d, x, y, w, h, RADIUS, lift, reveal, depth)
    cid = d.clip_rect(x, y - 40, w, h * reveal + 40, RADIUS)
    with d.group(clip=cid):
        d.rect(x, y, w, h, fill=CARD, rx=RADIUS)
    d.rect(x, y, w, h, fill="none", stroke=CARD_LINE, stroke_width=1.0, rx=RADIUS, opacity=reveal)


def connector_row(d: Doc, x: float, y: float, w: float, key: str, name: str,
                  on: float, opacity: float = 1.0, h: float = 46.0,
                  depth: float = 1.0) -> None:
    """One integration: glyph, name, and its own toggle.

    The toggle gets a small local shadow so it reads as sitting on the surface
    rather than being printed into it. That is the elevation cue — not a separate
    depth layer, which would slide it out of alignment with the row.
    """
    if opacity <= 0.01:
        return
    cy = y + h / 2
    tool_glyph(d, key, x + 26, cy, 21, opacity)
    d.text(x + 50, cy + 5.5, name, 15.0, *svg_font(SANS_MED), INK_2, opacity=opacity)
    _control_shadow(d, x + w - 74, cy - 11, 44, 22, 11, opacity, depth)
    toggle(d, x + w - 74, cy - 11, 44, 22, on, opacity)


def _control_shadow(d: Doc, x: float, y: float, w: float, h: float, r: float,
                    opacity: float, depth: float = 1.0) -> None:
    """A tight contact shadow for a small control.

    Two passes only, much tighter than `shadow()`: a control sits on a surface,
    not above the scene, so it needs a contact shadow rather than a cast one.
    """
    if opacity <= 0.01:
        return
    for spread, alpha in ((2.0, 0.05), (5.0, 0.035)):
        sp = spread * depth
        d.rect(x - sp, y - sp + 1.2 * depth, w + sp * 2, h + sp * 2,
               fill=f"rgba(31,30,29,{alpha * opacity:.4f})", rx=r + sp)


def master_row(d: Doc, x: float, y: float, w: float, label: str, on: float,
               opacity: float = 1.0, h: float = 58.0, depth: float = 1.0) -> None:
    """The organisation-wide switch at the top of the panel."""
    if opacity <= 0.01:
        return
    cy = y + h / 2
    d.text(x + 26, cy + 5.5, label, 15.5, *svg_font(SANS), INK, opacity=opacity)
    _control_shadow(d, x + w - 80, cy - 13, 52, 26, 13, opacity, depth)
    toggle(d, x + w - 80, cy - 13, 52, 26, on, opacity)


# ----------------------------------------------------------------- cursor


def cursor_pointer(d: Doc, x: float, y: float, u: float = 1.0, press: float = 0.0,
                   size: float = 26.0) -> None:
    """The arrow cursor, with a click ripple.

    `size` is the cursor's height in px. The path below is authored in a 0..18.2
    unit box, so it is normalised by that rather than scaled by an arbitrary
    factor — otherwise the cursor comes out hundreds of pixels tall.
    """
    if u <= 0.01:
        return
    if press > 0.01:
        d.circle(x, y, size * 0.7 + size * 1.1 * press, fill="none", stroke=CORAL,
                 stroke_width=2.0, opacity=(1.0 - press) * 0.7)
    s = size / 18.2
    with d.group(transform=f"translate({x:.2f} {y:.2f}) scale({s:.4f})", opacity=u):
        d.path(
            "M0 0 L0 15.5 L4.1 11.8 L6.9 18.2 L9.6 16.9 L6.8 10.6 L11.8 10.4 Z",
            fill="#FFFFFF", stroke=INK, width=1.15 / s * 1.0, join="round",
        )


def cursor_hand(d: Doc, x: float, y: float, u: float = 1.0, press: float = 0.0,
                size: float = 28.0) -> None:
    """The pointing hand, for when the brief wants a hand rather than an arrow.

    Authored in a ~0..18.2 unit box like the pointer, and normalised the same way.
    """
    if u <= 0.01:
        return
    if press > 0.01:
        d.circle(x, y, size * 0.65 + size * 0.95 * press, fill="none", stroke=CORAL,
                 stroke_width=2.0, opacity=(1.0 - press) * 0.6)
    s = size / 18.2
    with d.group(transform=f"translate({x:.2f} {y:.2f}) scale({s:.4f})", opacity=u):
        # Palm and three knuckles, with the index extended.
        d.path(
            "M2.2 3.4 C2.2 1.9 3.3 0.9 4.5 0.9 C5.7 0.9 6.8 1.9 6.8 3.4 "
            "L6.8 8.4 L8.6 8.4 C10.9 8.4 12.6 9.6 12.6 11.9 L12.6 13.4 "
            "C12.6 16.3 10.6 18.2 7.7 18.2 L6.4 18.2 C3.9 18.2 2.2 16.6 2.2 14.1 Z",
            fill="#FFFFFF", stroke=INK, width=1.15 / s, join="round",
        )
        d.path("M2.2 9.2 L6.8 9.2", stroke=INK, width=1.0 / s, opacity=0.35)


# ----------------------------------------------------------------- avatars


def _arc(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    """An SVG arc path from angle a0 to a1, in radians, sweeping clockwise.

    Angles are measured from twelve o'clock so a progress ring starts at the top,
    which is what the eye expects.
    """
    x0 = cx + math.sin(a0) * r
    y0 = cy - math.cos(a0) * r
    x1 = cx + math.sin(a1) * r
    y1 = cy - math.cos(a1) * r
    large = 1 if (a1 - a0) > math.pi else 0
    return f"M{x0:.2f} {y0:.2f} A{r:.2f} {r:.2f} 0 {large} 1 {x1:.2f} {y1:.2f}"


def avatar(d: Doc, cx: float, cy: float, r: float, initials: str, fill: str,
           progress: float = 0.0, check: float = 0.0, opacity: float = 1.0) -> None:
    """A person: coloured disc, initials, and a ring that becomes a check.

    The ring is a real arc from twelve o'clock, filling clockwise like a gauge.
    When it completes, a coral disc wipes over it and the check draws on — so the
    validation reads as one continuous event rather than two overlapping states.
    """
    if opacity <= 0.01:
        return

    fam, weight = svg_font(SANS_MED)
    label = initials
    tw = measure(SANS_MED, r * 0.82, label)

    # Contact shadow, so the discs sit on the paper rather than in it.
    d.circle(cx, cy + 1.5, r, fill="rgba(31,30,29,0.06)", opacity=opacity)
    d.circle(cx, cy, r, fill=fill, opacity=opacity)
    d.text(cx - tw / 2, cy + r * 0.30, label, r * 0.82, fam, weight, "#FFFFFF", opacity=opacity)

    # Progress ring, only while the check has not taken over. Inset slightly and
    # narrow, so it sits on the disc's edge instead of straddling it.
    ring_r = r * 0.93
    ring_w = max(2.0, r * 0.14)
    if progress > 0.001 and check < 0.02:
        sweep = math.tau * min(progress, 1.0)
        d.circle(cx, cy, ring_r, fill="none", stroke="rgba(217,107,67,0.20)",
                 stroke_width=ring_w, opacity=opacity)
        if sweep > 0.02:
            d.path(_arc(cx, cy, ring_r, 0.0, min(sweep, math.tau - 1e-4)),
                   stroke=CORAL_DEEP, width=ring_w, cap="butt", opacity=opacity)

    if check > 0.001:
        c = min(check * 1.8, 1.0)
        d.circle(cx, cy, r * (1.0 + 0.06 * (1.0 - c)), fill=CORAL_DEEP, opacity=opacity)
        # Tick draws on by growing its arms, which avoids a dash-length guess.
        d.path(
            f"M{cx - r * 0.36:.2f} {cy + r * 0.02:.2f} "
            f"L{cx - r * 0.08:.2f} {cy + r * 0.30 * c:.2f} "
            f"L{cx + r * 0.38 * c:.2f} {cy - r * 0.30 * c:.2f}",
            stroke="#FFFFFF", width=max(1.8, r * 0.19), cap="round", join="round",
            opacity=opacity,
        )


# ------------------------------------------------------------------ cards


def welcome_card(d: Doc, x: float, y: float, w: float, h: float, greeting: str,
                 name: str, lift: float = 1.0, opacity: float = 1.0,
                 suggestion: str = "", prompt: str = "", caret: bool = False,
                 depth: float = 1.0) -> None:
    """An employee's first-login card: greeting, asterisk, suggestion, composer.

    Laid out tight. A card with only a heading and a composer leaves a void in the
    middle that reads as a mockup rather than a product, so a suggested prompt
    fills it — which is also what a real first-login screen shows.
    """
    if opacity <= 0.01:
        return
    shadow(d, x, y, w, h, 14.0, lift, opacity, depth)
    d.rect(x, y, w, h, fill=CARD, rx=14.0, opacity=opacity)
    d.rect(x, y, w, h, fill="none", stroke=CARD_LINE, width=1.0, rx=14.0, opacity=opacity)

    # Greeting and name, baseline-aligned on one line.
    gsize = 26.0
    d.text(x + 24, y + 46, greeting, gsize, *svg_font(SERIF_REG), INK_3, opacity=opacity)
    gw = measure(SERIF_REG, gsize, greeting + " ")
    d.text(x + 24 + gw, y + 46, name, gsize, *svg_font(SERIF), INK, opacity=opacity)

    # The Claude asterisk, small, top right.
    asterisk(d, x + w - 34, y + 34, 9.5, opacity, CORAL)

    # A suggested prompt, as a quiet pill. This is what stops the card reading
    # as empty space between the heading and the composer.
    if suggestion:
        sy = y + 68
        sw = w - 48
        d.rect(x + 24, sy, sw, 34, fill=PAPER_DEEP, rx=8, opacity=opacity * 0.85)
        asterisk(d, x + 40, sy + 17, 5.0, opacity * 0.9, CORAL)
        d.text(x + 54, sy + 22, suggestion, 12.5, *svg_font(SANS_REG), INK_3,
               opacity=opacity * 0.95)

    # Composer at the foot.
    by = y + h - 60
    d.rect(x + 20, by, w - 40, 44, fill=PAPER_DEEP, rx=10.0, opacity=opacity)
    if prompt:
        d.text(x + 38, by + 28, prompt, 14.0, *svg_font(SANS_REG), INK_2, opacity=opacity)
    else:
        d.text(x + 38, by + 28, "Ask anything…", 14.0, *svg_font(SANS_REG), INK_4, opacity=opacity)
    if caret:
        pw = measure(SANS_REG, 14.0, prompt)
        d.rect(x + 41 + pw, by + 13, 1.6, 18, fill=INK_2, opacity=opacity)
    d.circle(x + w - 42, by + 22, 13, fill=INK, opacity=opacity * 0.9)
    d.path(
        f"M{x + w - 47:.1f} {by + 22:.1f} L{x + w - 37:.1f} {by + 22:.1f} "
        f"M{x + w - 42:.1f} {by + 17.5:.1f} L{x + w - 37:.1f} {by + 22:.1f} "
        f"L{x + w - 42:.1f} {by + 26.5:.1f}",
        stroke="#FFFFFF", width=1.7, cap="round", join="round", opacity=opacity,
    )


# ------------------------------------------------------------------ prompt


def prompt_bar(d: Doc, x: float, y: float, w: float, h: float, text: str,
               caret: bool = False, opacity: float = 1.0, sending: float = 0.0,
               depth: float = 1.0) -> None:
    """The main composer: text, context button, send button."""
    if opacity <= 0.01:
        return
    shadow(d, x, y, w, h, h / 2, 1.0, opacity, depth)
    d.rect(x, y, w, h, fill=CARD, rx=h / 2, opacity=opacity)
    d.rect(x, y, w, h, fill="none", stroke=CARD_LINE, stroke_width=1.0, rx=h / 2, opacity=opacity)

    # Context / connector button.
    bx, by = x + 26, y + h / 2
    d.circle(bx, by, 15, fill=PAPER_DEEP, opacity=opacity)
    d.path(
        f"M{bx - 7:.1f} {by:.1f} L{bx + 7:.1f} {by:.1f} M{bx:.1f} {by - 7:.1f} L{bx:.1f} {by + 7:.1f}",
        stroke=INK_3, width=1.8, cap="round", opacity=opacity,
    )

    tw = measure(SANS_REG, 17.0, text)
    d.text(x + 58, y + h / 2 + 6, text, 17.0, *svg_font(SANS_REG), INK, opacity=opacity)
    if caret:
        d.rect(x + 61 + tw, y + h / 2 - 11, 1.8, 22, fill=CORAL_DEEP, opacity=opacity)

    # Send button: scales down slightly on press.
    sx = x + w - 40
    s = 1.0 - 0.12 * sending
    d.circle(sx, by, 17 * s, fill=INK, opacity=opacity * (1.0 - 0.25 * sending))
    d.path(
        f"M{sx - 6:.1f} {by:.1f} L{sx + 6:.1f} {by:.1f} "
        f"M{sx + 1:.1f} {by - 5:.1f} L{sx + 6:.1f} {by:.1f} L{sx + 1:.1f} {by + 5:.1f}",
        stroke="#FFFFFF", width=1.9, cap="round", join="round", opacity=opacity,
    )


def action_row(d: Doc, x: float, y: float, w: float, key: str, label: str, detail: str,
               state: float, opacity: float = 1.0, h: float = 52.0,
               depth: float = 1.0) -> None:
    """One parallel tool action: glyph, verb, and a state that resolves.

    `state` 0..1 drives the whole row: it fades up, the glyph spins up, and a
    check replaces the spinner at the end. Keeping one driver per row is what
    makes four rows read as four concurrent jobs rather than a sequence.
    """
    if opacity <= 0.01:
        return
    cy = y + h / 2
    spin = min(state / 0.72, 1.0)
    done = max(0.0, (state - 0.72) / 0.28)

    # A subtle bar rather than a card, so the list stays light on paper. It still
    # gets a shadow: a row with no elevation reads as part of the background.
    shadow(d, x, y, w, h, 12.0, 0.9, opacity * min(state * 3.0, 1.0), depth)
    d.rect(x, y, w, h, fill=CARD, rx=12.0, opacity=opacity * min(state * 3.0, 1.0))
    d.rect(x, y, w, h, fill="none", stroke=CARD_LINE, stroke_width=1.0, rx=12.0,
           opacity=opacity * min(state * 3.0, 1.0))

    tool_glyph(d, key, x + 34, cy, 22, min(state * 3.0, 1.0))

    lw = measure(SANS_MED, 15.5, label)
    full = label + " " + detail
    fw = measure(SANS_REG, 15.5, full)
    # Reveal the detail by clipping to a widening window, so it reads as arriving.
    cid = d.clip_rect(x + 58, cy - 16, (lw + 6) + (fw - lw) * spin, 32)
    with d.group(clip=cid, opacity=opacity * min(state * 3.0, 1.0)):
        d.text(x + 58, cy + 5.5, label, 15.5, *svg_font(SANS_MED), INK)
        d.text(x + 58 + lw + 6, cy + 5.5, detail, 15.5, *svg_font(SANS_REG), INK_3)

    # State indicator: an arc that turns, then a check.
    ix = x + w - 34
    if done < 0.999:
        d.circle(ix, cy, 9, fill="none", stroke=PAPER_LINE, stroke_width=2.2, opacity=opacity * 0.9)
        # Partial arc, rotating.
        a0 = spin * math.tau * 2.0
        a1 = a0 + 1.5
        d.path(
            f"M{ix + math.cos(a0) * 9:.2f} {cy + math.sin(a0) * 9:.2f} "
            f"A9 9 0 0 1 {ix + math.cos(a1) * 9:.2f} {cy + math.sin(a1) * 9:.2f}",
            stroke=CORAL, width=2.2, cap="round", opacity=opacity * 0.95,
        )
    else:
        d.circle(ix, cy, 9, fill=BLUE, opacity=opacity * 0.95)
        d.path(
            f"M{ix - 4:.1f} {cy:.1f} L{ix - 1.2:.1f} {cy + 3:.1f} L{ix + 4.2:.1f} {cy - 3.2:.1f}",
            stroke="#FFFFFF", width=2.0, cap="round", join="round", opacity=opacity,
        )


# ------------------------------------------------------------------- misc


def overline(d: Doc, x: float, y: float, text: str, opacity: float = 1.0,
             colour: str = INK_4) -> float:
    """A small letter-spaced label above a heading. Returns its width."""
    fam, weight = svg_font(SANS)
    total = measure(SANS, 11.5, text, 2.2)
    d.text(x, y, text, 11.5, fam, weight, colour, tracking=2.2, opacity=opacity)
    return total


def badge(d: Doc, x: float, y: float, text: str, opacity: float = 1.0) -> float:
    """An outlined pill, as the brief's [ BETA ] badge."""
    fam, weight = svg_font(SANS)
    tw = measure(SANS, 12.0, text, 2.0)
    w = tw + 34
    h = 30.0
    d.rect(x, y, w, h, fill="none", stroke=CORAL_DEEP, stroke_width=1.4, rx=h / 2, opacity=opacity)
    d.text(x + 17, y + h / 2 + 4.4, text, 12.0, fam, weight, CORAL_DEEP, tracking=2.0, opacity=opacity)
    return w
