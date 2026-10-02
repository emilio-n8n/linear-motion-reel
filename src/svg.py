"""SVG document builder.

rsvg-convert supports a useful subset of SVG but not all of it, so this layer
sticks to what actually renders (verified against the installed rsvg):

  works  clipPath (including clip-to-<text>), feGaussianBlur, feDisplacementMap,
         linearGradient/radialGradient on fills *and* strokes, fill on <text>,
         letter-spacing, text-anchor, stroke-only text, rx, nested transforms
  broken feTurbulence, textPath, gradient-filled <mask>, mix-blend-mode

`stock.py` covers the broken ones with pre-baked PNGs or computed geometry.
"""

from __future__ import annotations

import os

from brand import CANVAS, H, W
from stock import rgba

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class Doc:
    """Accumulates defs + body, then serialises one frame."""

    def __init__(self, width: int = W, height: int = H, bg: str = CANVAS):
        self.w = width
        self.h = height
        self.bg = bg
        self.defs: list[str] = []
        self.body: list[str] = []
        self._uid = 0

    def uid(self, stem: str = "u") -> str:
        self._uid += 1
        return f"{stem}{self._uid}"

    # ------------------------------------------------------------------ defs

    def linear_gradient(
        self,
        stops: list[tuple[float, str, float]],
        x1: float = 0.0,
        y1: float = 0.0,
        x2: float = 1.0,
        y2: float = 0.0,
        units: str = "objectBoundingBox",
        gid: str | None = None,
    ) -> str:
        gid = gid or self.uid("lg")
        s = "".join(
            f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a < 1 else "") + "/>"
            for o, c, a in stops
        )
        self.defs.append(
            f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="{units}">{s}</linearGradient>'
        )
        return gid

    def radial_gradient(
        self,
        stops: list[tuple[float, str, float]],
        cx: float = 0.5,
        cy: float = 0.5,
        r: float = 0.5,
        units: str = "objectBoundingBox",
        gid: str | None = None,
    ) -> str:
        gid = gid or self.uid("rg")
        s = "".join(
            f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a < 1 else "") + "/>"
            for o, c, a in stops
        )
        self.defs.append(
            f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="{units}">{s}</radialGradient>'
        )
        return gid

    def blur(self, std: float, gid: str | None = None) -> str:
        """Gaussian blur filter. rsvg needs an explicit region or it clips the blur."""
        gid = gid or self.uid("bl")
        pad = std * 3.2 + 4
        self.defs.append(
            f'<filter id="{gid}" x="-{pad}" y="-{pad}" width="{pad * 2}" height="{pad * 2}" '
            f'filterUnits="userSpaceOnUse" primitiveUnits="userSpaceOnUse">'
            f'<feGaussianBlur stdDeviation="{std}"/></filter>'
        )
        return gid

    def displace(self, scale: float, freq: str = "0.008 0.02", seed: int = 3, gid: str | None = None) -> str:
        """Turbulent displacement — used for heat-haze and liquid edges."""
        gid = gid or self.uid("dp")
        self.defs.append(
            f'<filter id="{gid}" x="-20%" y="-30%" width="140%" height="160%" color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" seed="{seed}" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}" '
            f'xChannelSelector="R" yChannelSelector="G"/></filter>'
        )
        return gid

    def clip_rect(self, x: float, y: float, w: float, h: float, rx: float = 0.0, gid: str | None = None) -> str:
        gid = gid or self.uid("cr")
        r = f' rx="{rx}"' if rx else ""
        self.defs.append(f'<clipPath id="{gid}"><rect x="{x}" y="{y}" width="{max(w, 0)}" height="{max(h, 0)}"{r}/></clipPath>')
        return gid

    def clip_circle(self, cx: float, cy: float, r: float, gid: str | None = None) -> str:
        gid = gid or self.uid("cc")
        self.defs.append(f'<clipPath id="{gid}"><circle cx="{cx}" cy="{cy}" r="{max(r, 0)}"/></clipPath>')
        return gid

    def clip_poly(self, pts: list[tuple[float, float]], gid: str | None = None) -> str:
        gid = gid or self.uid("cp")
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        self.defs.append(f'<clipPath id="{gid}"><polygon points="{p}"/></clipPath>')
        return gid

    def clip_text(self, x: float, y: float, text: str, size: float, family: str, weight: int, gid: str | None = None) -> str:
        """Clip to the silhouette of a text run — the wipe-reveal primitive."""
        gid = gid or self.uid("ct")
        self.defs.append(
            f'<clipPath id="{gid}"><text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="#fff">{_esc(text)}</text></clipPath>'
        )
        return gid

    def clip_path(self, d: str, gid: str | None = None) -> str:
        gid = gid or self.uid("cd")
        self.defs.append(f'<clipPath id="{gid}"><path d="{d}"/></clipPath>')
        return gid

    def mask(self, inner: str, gid: str | None = None) -> str:
        """Luminance mask. rsvg's gradient-in-mask support is unreliable, so
        callers pass explicit geometry rather than a gradient fill."""
        gid = gid or self.uid("mk")
        self.defs.append(f'<mask id="{gid}" maskUnits="userSpaceOnUse">{inner}</mask>')
        return gid

    # ------------------------------------------------------------------ body

    def add(self, s: str) -> None:
        self.body.append(s)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "none",
        rx: float | None = None,
        opacity: float | None = None,
        stroke: str | None = None,
        stroke_width: float | None = None,
        opacity_attr: str | None = None,
        transform: str | None = None,
        filt: str | None = None,
        extra: str = "",
        width: float | None = None,
    ) -> str:
        # `width` accepted as an alias for `stroke_width`; see the note on line().
        stroke_width = width if width is not None else stroke_width
        a = [f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(max(w, 0))}" height="{_n(max(h, 0))}" fill="{fill}"']
        if rx:
            a.append(f' rx="{_n(rx)}"')
        if opacity is not None:
            a.append(f' {opacity_attr or "opacity"}="{_n(opacity)}"')
        if stroke:
            a.append(f' stroke="{stroke}"')
        if stroke_width:
            a.append(f' stroke-width="{_n(stroke_width)}"')
        if transform:
            a.append(f' transform="{transform}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        if extra:
            a.append(extra)
        a.append("/>")
        s = "".join(a)
        self.add(s)
        return s

    def circle(self, cx: float, cy: float, r: float, fill: str = "none", opacity: float | None = None,
               stroke: str | None = None, stroke_width: float | None = None, filt: str | None = None,
               width: float | None = None) -> str:
        # `width` accepted as an alias for `stroke_width`; see the note on line().
        stroke_width = width if width is not None else stroke_width
        a = [f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(max(r, 0))}" fill="{fill}"']
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        if stroke:
            a.append(f' stroke="{stroke}"')
        if stroke_width:
            a.append(f' stroke-width="{_n(stroke_width)}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        a.append("/>")
        s = "".join(a)
        self.add(s)
        return s

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str,
             width: float | None = None, opacity: float | None = None, cap: str = "butt",
             filt: str | None = None, stroke_width: float | None = None) -> str:
        # Both names accepted: `stroke_width` matches rect/circle, `width` reads
        # better for a line. Having only one of them on each primitive is how you
        # end up writing `width=` on a rect and getting a TypeError.
        width = stroke_width if stroke_width is not None else (1.0 if width is None else width)
        a = [
            f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" '
            f'stroke="{stroke}" stroke-width="{_n(width)}" stroke-linecap="{cap}"'
        ]
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        a.append("/>")
        s = "".join(a)
        self.add(s)
        return s

    def path(self, d: str, fill: str = "none", stroke: str | None = None, width: float | None = None,
             opacity: float | None = None, cap: str = "butt", join: str = "miter", filt: str | None = None,
             dash: str | None = None, extra: str = "", stroke_width: float | None = None) -> str:
        # `stroke_width` accepted as an alias for `width`; see the note on line().
        width = stroke_width if stroke_width is not None else width
        a = [f'<path d="{d}" fill="{fill}"']
        if stroke:
            a.append(f' stroke="{stroke}"')
        if width:
            a.append(f' stroke-width="{_n(width)}"')
        if dash:
            a.append(f' stroke-dasharray="{dash}"')
        if cap != "butt":
            a.append(f' stroke-linecap="{cap}"')
        if join != "miter":
            a.append(f' stroke-linejoin="{join}"')
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        if extra:
            a.append(extra)
        a.append("/>")
        s = "".join(a)
        self.add(s)
        return s

    def group(self, transform: str | None = None, opacity: float | None = None,
              filt: str | None = None, clip: str | None = None, mask: str | None = None) -> "Group":
        g = Group(self)
        a = ["<g"]
        if transform:
            a.append(f' transform="{transform}"')
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        if clip:
            a.append(f' clip-path="url(#{clip})"')
        if mask:
            a.append(f' mask="url(#{mask})"')
        a.append(">")
        g.open = "".join(a)
        return g

    def text(self, x: float, y: float, text: str, size: float, family: str, weight: int, fill: str,
             anchor: str | None = None, tracking: float | None = None, opacity: float | None = None,
             filt: str | None = None, stroke: str | None = None, stroke_width: float | None = None) -> str:
        a = [
            f'<text x="{_n(x)}" y="{_n(y)}" font-family="{family}" font-size="{_n(size)}" '
            f'font-weight="{weight}" fill="{fill}"'
        ]
        if anchor:
            a.append(f' text-anchor="{anchor}"')
        if tracking is not None:
            a.append(f' letter-spacing="{_n(tracking)}"')
        if stroke:
            a.append(f' stroke="{stroke}"')
        if stroke_width:
            a.append(f' stroke-width="{_n(stroke_width)}"')
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        if filt:
            a.append(f' filter="url(#{filt})"')
        a.append(f">{_esc(text)}</text>")
        s = "".join(a)
        self.add(s)
        return s

    def image(self, href: str, x: float, y: float, w: float, h: float, opacity: float | None = None,
              preserve: str = "none") -> str:
        a = [
            f'<image x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" '
            f'preserveAspectRatio="{preserve}" xlink:href="{href}"'
        ]
        if opacity is not None:
            a.append(f' opacity="{_n(opacity)}"')
        a.append("/>")
        s = "".join(a)
        self.add(s)
        return s

    def use_href(self, rel: str) -> str:
        return os.path.join(ASSETS, rel)

    # ------------------------------------------------------------- finishing

    def render(self) -> str:
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
            f"{defs}"
            f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>'
            f"{''.join(self.body)}"
            f"{GRAIN_AND_VIGNETTE}"
            f"</svg>"
        )


# The last thing in every frame: a fine grain tile and a corner vignette.
# linear.app runs its own Grain layer, so this is in the brand's visual language
# rather than decoration — and it also hides banding in the dark gradients.
GRAIN_AND_VIGNETTE = (
    f'<image x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none" '
    f'xlink:href="{os.path.join(ASSETS, "grain.png")}" opacity="0.035"/>'
    f'<image x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none" '
    f'xlink:href="{os.path.join(ASSETS, "vignette.png")}" opacity="0.9"/>'
)


class Group:
    """Context manager so nested transform stacks read like markup."""

    def __init__(self, doc: Doc):
        self.doc = doc
        self.open = "<g>"
        self.closed = False

    def __enter__(self) -> "Group":
        self.doc.add(self.open)
        return self

    def __exit__(self, *exc) -> None:
        self.doc.add("</g>")
        self.closed = True


def _n(v: float) -> str:
    """Number formatting for SVG — 3dp is well under a pixel at 1080p."""
    v = round(float(v), 3)
    if v == 0:
        return "0"
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def transform(x: float = 0.0, y: float = 0.0, scale: float | None = None, rotate: float | None = None,
              origin: tuple[float, float] | None = None, skew_x: float | None = None) -> str:
    parts = []
    if x or y:
        parts.append(f"translate({_n(x)} {_n(y)})")
    if rotate:
        ox, oy = origin or (0.0, 0.0)
        parts.append(f"rotate({_n(rotate)} {_n(ox)} {_n(oy)})")
    if skew_x:
        parts.append(f"skewX({_n(skew_x)})")
    if scale is not None and scale != 1.0:
        if origin:
            ox, oy = origin
            parts.append(f"translate({_n(ox)} {_n(oy)}) scale({_n(scale)}) translate({_n(-ox)} {_n(-oy)})")
        else:
            parts.append(f"scale({_n(scale)})")
    return " ".join(parts)


def matrix3d(a: float, b: float, cc: float, d: float, e: float, f: float) -> str:
    return f"matrix({_n(a)},{_n(b)},{_n(cc)},{_n(d)},{_n(e)},{_n(f)})"


def glow(doc: Doc, cx: float, cy: float, r: float, color: str, strength: float = 0.5) -> None:
    """Additive-looking light on the near-black canvas.

    rsvg ignores mix-blend-mode, so brightness comes from a radial gradient that
    falls off to zero — one element, and a smooth falloff. Stacked flat discs were
    tried first and read as visible concentric rings rather than as light.
    """
    if strength <= 0.001 or r <= 0.5:
        return
    stops = [
        (0.00, color, 0.95 * strength),
        (0.10, color, 0.72 * strength),
        (0.26, color, 0.44 * strength),
        (0.46, color, 0.22 * strength),
        (0.68, color, 0.085 * strength),
        (0.86, color, 0.022 * strength),
        (1.00, color, 0.0),
    ]
    gid = doc.radial_gradient(stops, cx=cx, cy=cy, r=r, units="userSpaceOnUse")
    doc.circle(cx, cy, r, fill=f"url(#{gid})")
