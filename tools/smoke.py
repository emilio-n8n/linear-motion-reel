#!/usr/bin/env python3
"""Smoke test: render one frame from every scene and validate the SVG.

Cheaper and more reliable than looking at contact sheets when the question is
"does this scene run at all". It catches the failure modes that actually happen —
a wrong argument count, a division by zero, a NaN coordinate — and validates the
serialised document by rasterising it, so malformed XML is caught here rather
than 400 frames into a render.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from brand import SCENES  # noqa: E402

# Scene modules under test, as (module, local_frame_count).
LAUNCH = [
    ("l01_promise", 150),
    ("l02_planning", 165),
    ("l03_build", 165),
    ("l04_velocity", 150),
    ("l05_palette", 165),
    ("l06_agents", 165),
    ("l07_insights", 150),
    ("l08_launch", 180),
]

# Values that are always a bug if they reach the SVG.
BAD = re.compile(r"nan|inf|-0\.000|None")


class _Clock:
    def __init__(self, f: int, dur: int):
        self.f = f
        self.dur = dur
        self.u = f / dur if dur else 0.0
        self.t = self.f / 30.0
        self.index = 0
        self.name = "smoke"
        self.span = (0, dur)


def check_svg(svg: str) -> list[str]:
    """Structural checks that do not need a rasteriser."""
    problems = []
    if not svg.startswith("<svg"):
        problems.append("does not start with <svg")
    if not svg.rstrip().endswith("</svg>"):
        problems.append("does not end with </svg>")
    if svg.count("<g") != svg.count("</g>"):
        problems.append(f"unbalanced <g>: {svg.count('<g')} open vs {svg.count('</g>')} close")
    if svg.count("<defs>") != svg.count("</defs>"):
        problems.append("unbalanced <defs>")
    # Every url(#id) must resolve to a def that exists.
    refs = set(re.findall(r'url\(#([^)]+)\)', svg))
    defined = set(re.findall(r'<(?:linearGradient|radialGradient|filter|clipPath|mask)[^>]*id="([^"]+)"', svg))
    for r in sorted(refs - defined):
        problems.append(f"dangling reference url(#{r})")
    # Unused defs are wasted work, not an error, but a large count usually means
    # a filter is being re-created per element when it could be shared.
    m = BAD.search(svg)
    if m:
        problems.append(f"suspicious value near: ...{svg[max(0, m.start() - 40):m.start() + 20]}...")
    return problems


def main() -> int:
    scenes_dir = os.path.join(ROOT, "src", "launch")
    if scenes_dir not in sys.path:
        sys.path.insert(0, scenes_dir)

    only = sys.argv[1:] or None
    failures = 0
    checked = 0

    with tempfile.TemporaryDirectory() as tmp:
        for mod_name, dur in LAUNCH:
            if only and mod_name not in only:
                continue
            path = os.path.join(scenes_dir, f"{mod_name}.py")
            if not os.path.exists(path):
                print(f"  SKIP  {mod_name} (not written yet)")
                continue
            try:
                mod = importlib.import_module(mod_name)
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL  {mod_name}  import: {type(exc).__name__}: {exc}")
                failures += 1
                continue

            for frac in (0.02, 0.25, 0.5, 0.75, 0.98):
                frame = int(dur * frac)
                try:
                    svg = mod.draw(_Clock(frame, dur))
                except Exception as exc:  # noqa: BLE001
                    import traceback

                    print(f"  FAIL  {mod_name} f{frame}  draw: {type(exc).__name__}: {exc}")
                    traceback.print_exc()
                    failures += 1
                    break
                checked += 1
                problems = check_svg(svg)
                if problems:
                    print(f"  FAIL  {mod_name} f{frame}  svg: {'; '.join(problems)}")
                    failures += 1
                    break
                # Rasterise one frame per scene: this is what catches XML that
                # lxml would accept but librsvg rejects.
                if frac == 0.5:
                    sp = os.path.join(tmp, f"{mod_name}.svg")
                    pp = os.path.join(tmp, f"{mod_name}.png")
                    with open(sp, "w") as fh:
                        fh.write(svg)
                    r = subprocess.run(
                        ["rsvg-convert", "-w", "480", "-h", "270", sp, "-o", pp],
                        capture_output=True,
                    )
                    if r.returncode != 0:
                        print(f"  FAIL  {mod_name}  rsvg: {r.stderr.decode()[:180]}")
                        failures += 1
                        break
            else:
                print(f"  OK    {mod_name}  ({dur} frames)")

    print()
    if failures:
        print(f"{failures} scene(s) failed, {checked} frame(s) generated")
        return 1
    print(f"all {checked} sampled frames valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
