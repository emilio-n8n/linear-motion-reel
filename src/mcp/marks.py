"""Tool glyphs and the Claude mark, constructed rather than borrowed.

Every mark here is built from primitives so it can be animated (drawn on, scaled,
morphed) and so nothing is a downloaded asset. They are deliberately abstract
geometric forms that read as "a tool" at 20px on a cream panel, not reproductions
of anyone's trademark.

The Claude asterisk is a radial burst assembled from tapered spokes: the intent is
a recognisable silhouette in the same family as the real mark without copying its
outline. See the README on why the film is labelled an unofficial concept piece.
"""

from __future__ import annotations

import math

from tokens import CORAL, CORAL_DEEP, INK

# ------------------------------------------------------------------- shapes


def asterisk(d, cx: float, cy: float, r: float, u: float = 1.0,
             colour: str = CORAL, petals: int = 6) -> None:
    """The Claude-family burst: tapered spokes radiating from a centre.

    Each petal is a quadratic with a narrowed waist, so the mark reads as organic
    rather than as a gear. `u` scales the petals out from the centre, which is the
    draw-on.
    """
    if u <= 0.001:
        return
    for i in range(petals):
        a = i / petals * math.tau - math.pi / 2
        tip_x = cx + math.cos(a) * r * 1.32 * u
        tip_y = cy + math.sin(a) * r * 1.32 * u
        # Shoulders set the petal width; they sit close in so the form tapers.
        s1 = a + 0.30
        s2 = a - 0.30
        w = r * 0.30 * u
        p1x = cx + math.cos(s1) * w * 0.5
        p1y = cy + math.sin(s1) * w * 0.5
        p2x = cx + math.cos(s2) * w * 0.5
        p2y = cy + math.sin(s2) * w * 0.5
        d.path(
            f"M{p1x:.2f} {p1y:.2f} Q{tip_x:.2f} {tip_y:.2f} {p2x:.2f} {p2y:.2f} "
            f"Q{cx:.2f} {cy:.2f} {p1x:.2f} {p1y:.2f} Z",
            fill=colour, opacity=u,
        )
    # Centre disc, so the petals resolve into one mark rather than a starburst.
    d.circle(cx, cy, r * 0.20 * u, fill=colour, opacity=u)


def tool_glyph(d, key: str, cx: float, cy: float, size: float, u: float = 1.0) -> None:
    """A distinct 20px-ish geometric mark per tool.

    Abstract on purpose: each is a recognisable *shape language* rather than a
    logo. Distinct silhouettes matter more than accuracy here, because the eye
    only needs to see that they are different tools.
    """
    if u <= 0.001:
        return
    s = size
    with d.group(opacity=u, transform=f"translate({cx - s / 2:.2f} {cy - s / 2:.2f}) scale({u:.3f})"):
        if key == "figma":
            d.circle(s * 0.30, s * 0.26, s * 0.22, fill="#8B6CF0")
            d.circle(s * 0.30, s * 0.74, s * 0.22, fill="#8B6CF0", opacity=0.75)
            d.rect(s * 0.52, s * 0.06, s * 0.42, s * 0.40, fill="#C4B5FD", rx=s * 0.20)
            d.rect(s * 0.52, s * 0.54, s * 0.42, s * 0.40, fill="#C4B5FD", rx=s * 0.20, opacity=0.7)
        elif key == "canva":
            d.circle(cx=s / 2, cy=s / 2, r=s * 0.46, fill="#06B6D4", opacity=0.85)
            d.path(
                f"M{s * 0.28:.1f} {s * 0.60:.1f} Q{s * 0.50:.1f} {s * 0.10:.1f} {s * 0.72:.1f} {s * 0.60:.1f}",
                stroke="#FFFFFF", width=s * 0.13, cap="round", fill="none",
            )
        elif key == "linear":
            # Two stacked bars at an angle: reads as velocity.
            for k in range(3):
                y = s * (0.26 + k * 0.24)
                d.rect(s * (0.16 + k * 0.10), y, s * (0.54 - k * 0.10), s * 0.13,
                       fill="#5E6AD2", rx=s * 0.06, opacity=1.0 - k * 0.22)
        elif key == "asana":
            d.circle(s * 0.50, s * 0.32, s * 0.21, fill="#F06A6A")
            d.circle(s * 0.28, s * 0.68, s * 0.21, fill="#F06A6A", opacity=0.85)
            d.circle(s * 0.72, s * 0.68, s * 0.21, fill="#F06A6A", opacity=0.7)
        elif key == "atlassian":
            d.path(
                f"M{s * 0.10:.1f} {s * 0.86:.1f} L{s * 0.42:.1f} {s * 0.14:.1f} "
                f"Q{s * 0.50:.1f} {s * 0.02:.1f} {s * 0.58:.1f} {s * 0.14:.1f} "
                f"L{s * 0.90:.1f} {s * 0.86:.1f} L{s * 0.58:.1f} {s * 0.86:.1f} "
                f"L{s * 0.44:.1f} {s * 0.52:.1f} L{s * 0.30:.1f} {s * 0.86:.1f} Z",
                fill="#2684FF",
            )
        elif key == "supabase":
            d.path(
                f"M{s * 0.50:.1f} {s * 0.06:.1f} L{s * 0.50:.1f} {s * 0.52:.1f} "
                f"L{s * 0.10:.1f} {s * 0.52:.1f} Z",
                fill="#3ECF8E",
            )
            d.path(
                f"M{s * 0.50:.1f} {s * 0.94:.1f} L{s * 0.50:.1f} {s * 0.48:.1f} "
                f"L{s * 0.90:.1f} {s * 0.48:.1f} Z",
                fill="#3ECF8E", opacity=0.65,
            )
        elif key == "github":
            d.circle(s * 0.5, s * 0.5, s * 0.44, fill="#24292F")
            d.circle(s * 0.5, s * 0.52, s * 0.22, fill="#FBF9F5")
        elif key == "slack":
            cols = ("#36C5F0", "#2EB67D", "#ECB22E", "#E01E5A")
            for k in range(4):
                a = k / 4 * math.tau + math.pi / 4
                d.rect(
                    s * 0.5 + math.cos(a) * s * 0.22 - s * 0.09,
                    s * 0.5 + math.sin(a) * s * 0.22 - s * 0.09,
                    s * 0.18, s * 0.18, fill=cols[k], rx=s * 0.05,
                )
        elif key == "okta":
            d.circle(s * 0.5, s * 0.5, s * 0.42, fill="none", stroke="#0F6DB5", stroke_width=s * 0.14)
        else:
            d.circle(s * 0.5, s * 0.5, s * 0.38, fill=INK, opacity=0.25)


# Tools in the connector list, in the brief's order.
CONNECTORS = [
    ("asana", "Asana"),
    ("atlassian", "Atlassian"),
    ("canva", "Canva"),
    ("figma", "Figma"),
    ("linear", "Linear"),
    ("supabase", "Supabase"),
    ("github", "GitHub"),
    ("slack", "Slack"),
]
