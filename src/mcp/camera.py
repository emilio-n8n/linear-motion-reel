"""A perspective camera, faked for a renderer with no 3D.

rsvg has no 3D pipeline, so depth is produced by projecting each element myself
and emitting an ordinary 2D transform. That is enough for the effect that
matters: on a dolly, near elements grow and far elements shrink, which is the
parallax cue the eye reads as depth.

The model is a pinhole camera on the +Z axis looking at the `z = 0` plane.

    s(z) = (d / k) / (d / k - z)

where `d` is the resting camera distance and `k` is the dolly factor. Two
properties fall out of that and both matter:

  - at `z = 0` the scale is exactly 1 regardless of `k`, so the focus plane
    never moves and everything else parallaxes around it;
  - increasing `k` grows near layers and shrinks far ones, because the camera is
    moving *through* the scene rather than simply zooming.

Layers are grouped by depth and each gets one transform, so a scene pays for a
handful of transforms rather than one per element.
"""

from __future__ import annotations

import math

from tokens import H, W

# Resting camera distance. Larger flattens the perspective; smaller exaggerates
# it. Around 1200–1600 reads as a long lens, which is what product films use.
DEFAULT_DISTANCE = 1400.0


class Camera:
    """A camera with a focus point and a dolly factor.

    `x`/`y` are the point the camera looks at, in the same coordinate space the
    scenes are authored in. Animating them is a pan; animating `push` is a dolly;
    both together is the move that reads as cinematic.
    """

    __slots__ = ("d", "x", "y", "push", "focus_z")

    def __init__(self, x: float = W / 2, y: float = H / 2, push: float = 1.0,
                 distance: float = DEFAULT_DISTANCE, focus_z: float = 0.0):
        self.d = distance
        self.x = x
        self.y = y
        self.push = push
        self.focus_z = focus_z

    # ------------------------------------------------------------- projection

    def scale(self, z: float) -> float:
        """Scale for a layer at depth `z`. Exactly 1 at the focus plane."""
        dolly = self.d / max(self.push, 0.05)
        denom = dolly - z
        # Guard against a layer crossing the lens, which would invert the image.
        if denom < dolly * 0.12:
            denom = dolly * 0.12
        return dolly / denom

    def transform(self, z: float = 0.0) -> str:
        """An SVG transform that places a layer authored at `z = 0` onto depth `z`.

        A group whose children are authored in screen coordinates gets

            translate(W/2 - cam_x*s, H/2 - cam_y*s) scale(s)

        which maps world (x, y) to (W/2 + s(x - cam_x), H/2 + s(y - cam_y)) —
        the pinhole projection, for the cost of one transform per layer.
        """
        s = self.scale(z)
        tx = W / 2 - self.x * s
        ty = H / 2 - self.y * s
        return f"translate({tx:.2f} {ty:.2f}) scale({s:.5f})"

    def point(self, x: float, y: float, z: float = 0.0) -> tuple[float, float]:
        """Project a single point. Use for anything that must land exactly on a
        layer — a cursor, or an arrowhead at the end of a drawn connector."""
        s = self.scale(z)
        return W / 2 + s * (x - self.x), H / 2 + s * (y - self.y)

    def unproject(self, sx: float, sy: float, z: float = 0.0) -> tuple[float, float]:
        """Inverse of `point`: the world coordinate on layer `z` that lands on
        screen position (sx, sy).

        This is what lets an element on one layer align with something on
        another — a cursor on the near layer pointing at a control that lives on
        the surface. Without it, anything crossing layers drifts by exactly the
        parallax amount, which is the bug that makes a pointer miss its target.
        """
        s = self.scale(z)
        return self.x + (sx - W / 2) / s, self.y + (sy - H / 2) / s

    # ------------------------------------------------------------------ depth

    def blur(self, z: float, strength: float = 1.0, max_blur: float = 6.0) -> float:
        """Blur radius in px for a layer at depth `z`, from its distance to focus.

        This is the depth-of-field cue, and it wants to stay subtle: on a flat
        design, heavy defocus reads as mud rather than as depth. Linear in
        distance, capped low.

        Quantise the result into a few levels when creating filters — one filter
        per distinct blur, not per element, or the document bloats and rasterising
        slows for no visible gain.
        """
        return min(abs(z - self.focus_z) / 110.0 * strength, max_blur)

    def blur_levels(self, depths: list[float], strength: float = 1.0) -> list[float]:
        """Blur radii for a set of depths, quantised to whole levels.

        Rounding to 0.5px steps means a handful of layers share one filter
        definition instead of each creating its own.
        """
        return [round(self.blur(z, strength) * 2.0) / 2.0 for z in depths]

    def shadow(self, z: float) -> tuple[float, float]:
        """(spread, offset) for a shadow cast by an element at depth `z`.

        Nearer elements cast larger, further-offset shadows, which is most of what
        makes them read as detached from the plane rather than painted on it.
        """
        s = self.scale(z)
        spread = 16.0 * s
        offset = 5.0 * s
        return spread, offset

    def copy(self, **kw) -> "Camera":
        c = Camera(self.x, self.y, self.push, self.d, self.focus_z)
        for k, v in kw.items():
            setattr(c, k, v)
        return c


# --------------------------------------------------------------------- rigs


class Rig:
    """A named camera move, evaluated as a pure function of scene progress.

    Scenes should not hand-roll camera maths: a rig keeps every scene's move on
    the same vocabulary, so the film's camera language stays consistent.
    """

    @staticmethod
    def dolly_in(u: float, start: float = 0.0, dur: float = 1.0, amount: float = 0.35,
                 ease: str = "inout") -> float:
        """Push toward the focus point. The default is small: 0.35 is already a
        strong move on a 1080p frame, and overshooting it reads as a zoom."""
        from easing import seg

        return 1.0 + amount * seg(u, start, dur, ease)

    @staticmethod
    def drift(u: float, amount: float = 14.0, rate: float = 1.0, phase: float = 0.0) -> tuple[float, float]:
        """A continuous, slow float for the look-at point.

        Every scene should be moving a little even when nothing else is: a
        perfectly static frame in a film reads as a still, not as a held shot.
        """
        return (
            math.sin(u * math.tau * rate + phase) * amount,
            math.cos(u * math.tau * rate * 0.7 + phase) * amount * 0.6,
        )

    @staticmethod
    def track(from_x: float, to_x: float, u: float, start: float = 0.0,
              dur: float = 1.0, ease: str = "inout") -> float:
        """Lateral move toward a subject — used when the eye should follow a
        signal travelling across the frame."""
        from easing import seg

        return from_x + (to_x - from_x) * seg(u, start, dur, ease)


# Depth layers. A small vocabulary, used consistently, is what makes a film look
# like it has a world rather than a pile of effects. Roughly: the backdrop sits
# far behind, surfaces at the focus plane, controls float in front.
Z_BACKDROP = -420.0
Z_BEHIND = -170.0
Z_SURFACE = 0.0
Z_RAISED = 70.0
Z_CONTROL = 130.0
Z_NEAR = 210.0
