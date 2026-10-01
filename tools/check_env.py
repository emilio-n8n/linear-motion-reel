#!/usr/bin/env python3
"""Environment check for the render pipeline.

Run this before rendering (locally or on Colab) to confirm the three things the
pipeline needs that are not part of a default Python install:

  1. rsvg-convert   - rasterises the per-frame SVG
  2. Pango + cairo  - text metrics, via python3-gi
  3. ffmpeg         - encodes the PNG sequence

It also verifies the fonts are visible to fontconfig, because the metrics layer
resolves families by name and a missing family silently falls back to a
different face, which would shift every glyph position.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

REQUIRED_BINARIES = ["rsvg-convert", "ffmpeg", "fc-list"]
REQUIRED_FAMILIES = ["Inter", "Inter Display", "JetBrains Mono"]


def check_binaries() -> bool:
    ok = True
    for b in REQUIRED_BINARIES:
        path = shutil.which(b)
        print(f"  {'OK ' if path else 'MISSING'}  {b:14} {path or ''}")
        ok = ok and bool(path)
    return ok


def check_python_deps() -> bool:
    try:
        import gi  # noqa: F401

        gi.require_version("Pango", "1.0")
        gi.require_version("PangoCairo", "1.0")
        from gi.repository import Pango, PangoCairo  # noqa: F401

        print(f"  OK    gi/Pango     {Pango.version_string()}")
    except Exception as exc:  # noqa: BLE001
        print(f"  MISSING  gi/Pango     {type(exc).__name__}: {exc}")
        return False
    try:
        import numpy  # noqa: F401

        print(f"  OK    numpy        {numpy.__version__}")
    except Exception as exc:  # noqa: BLE001
        print(f"  MISSING  numpy        {exc}")
        return False
    return True


def check_fonts() -> bool:
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    families = {line.strip() for line in out.splitlines()}
    ok = True
    for f in REQUIRED_FAMILIES:
        hit = f in families
        print(f"  {'OK ' if hit else 'MISSING'}  {f}")
        ok = ok and hit
    return ok


def check_metrics() -> bool:
    try:
        import layout as L

        w = L.measure("InterDisplay-Black", 200, "Ship faster.")
        cap = L.cap_height("InterDisplay-Black", 200)
        sane = 800 < w < 1600 and 120 < cap < 170
        print(f"  {'OK ' if sane else 'BAD '}  metrics    width={w:.0f} cap={cap:.0f}")
        return sane
    except Exception as exc:  # noqa: BLE001
        print(f"  BAD   metrics    {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    print("binaries:")
    a = check_binaries()
    print("python deps:")
    b = check_python_deps()
    print("fonts:")
    c = check_fonts()
    print("shaping:")
    d = check_metrics()
    print()
    if all((a, b, c, d)):
        print("all checks passed")
        return 0
    print("environment incomplete — see above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
