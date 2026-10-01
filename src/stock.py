"""Pre-baked assets and small math/geometry helpers.

rsvg-convert has no feTurbulence and no radialGradient, so the film grain and the
vignette are generated here as PNGs once and tiled into every frame.
"""

from __future__ import annotations

import math
import os
import struct
import zlib

import numpy as np

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


# --------------------------------------------------------------------------- png


def write_png(path: str, arr: np.ndarray) -> None:
    """Write an (h, w, 3|4) uint8 array as a PNG."""
    h, w, ch = arr.shape
    color_type = 6 if ch == 4 else 2
    rows = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)))
        fh.write(chunk(b"IDAT", zlib.compress(rows, 9)))
        fh.write(chunk(b"IEND", b""))


# ---------------------------------------------------------------------- baking


def bake_grain(size: int = 512, seed: int = 17) -> np.ndarray:
    """Tileable monochrome film grain, mid-grey biased so it darkens as much as it lifts."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0.0, 1.0, (size, size))
    # Wrap-blur once so the tile has no hard seam when repeated.
    # Separable 7-tap blur, wrapped with np.roll so the tile has no seam.
    k = np.array([0.06, 0.12, 0.2, 0.24, 0.2, 0.12, 0.06])
    for axis in (0, 1):
        n = sum(np.roll(n, int(i - 3), axis) * w for i, w in enumerate(k))
    n /= max(n.std(), 1e-6)
    v = np.clip(128.0 + n * 26.0, 0, 255)
    grain = np.repeat(v[:, :, None], 3, axis=2).astype(np.uint8)
    write_png(os.path.join(ASSETS, "grain.png"), grain)
    return grain


def bake_vignette(w: int = 1920, h: int = 1080) -> np.ndarray:
    """RGBA corner-darkening vignette (radialGradient stand-in)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    r = np.sqrt(nx * nx * 0.92 + ny * ny) / 1.02
    a = np.clip((r - 0.42) / 0.58, 0.0, 1.0) ** 1.7 * 205.0
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 3] = a.astype(np.uint8)
    write_png(os.path.join(ASSETS, "vignette.png"), rgba)
    return rgba


def ensure_assets() -> None:
    if not os.path.exists(os.path.join(ASSETS, "grain.png")):
        bake_grain()
    if not os.path.exists(os.path.join(ASSETS, "vignette.png")):
        bake_vignette()


# --------------------------------------------------------------------- geometry


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def smoothstep(u: float) -> float:
    u = clamp(u)
    return u * u * (3.0 - 2.0 * u)


def smootherstep(u: float) -> float:
    u = clamp(u)
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def ease_range(u: float, start: float, end: float) -> float:
    """Normalise u from the [start,end] window into 0..1 (eased, no linear edges)."""
    if end <= start:
        return 0.0
    return smootherstep((u - start) / (end - start))


def mix_hex(c0: str, c1: str, u: float) -> str:
    """Blend two #rrggbb strings."""
    u = clamp(u)
    a = (int(c0[1:3], 16), int(c0[3:5], 16), int(c0[5:7], 16))
    b = (int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16))
    return "#%02x%02x%02x" % tuple(int(round(lerp(x, y, u))) for x, y in zip(a, b))


def rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{max(0.0, min(1.0, alpha)):.4f})"


def project_iso(x: float, y: float, z: float, ax: float, ay: float, scale: float, ox: float, oy: float):
    """Rotate about X then Y, then project orthographically. Returns (sx, sy)."""
    ca, sa = math.cos(ax), math.sin(ax)
    ya, yb = y * ca - z * sa, y * sa + z * ca
    cb, sb = math.cos(ay), math.sin(ay)
    x2, z2 = x * cb + ya * sb, -x * sb + ya * cb
    return ox + x2 * scale, oy + z2 * scale
