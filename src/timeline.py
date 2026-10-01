"""Frame clock and scene registry.

Every scene is a pure function of its own local frame index — no shared timeline
state — which is what makes frames independently renderable, parallelisable and
resumable. A scene that needed to remember frame 400 to draw frame 401 could not
be re-rendered out of order or on its own.
"""

from __future__ import annotations

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brand import FPS, SCENES, TOTAL_FRAMES  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCENE_DIR = os.path.join(_HERE, "scenes")
if _SCENE_DIR not in sys.path:
    sys.path.insert(0, _SCENE_DIR)

_MODULES = {
    "origin": "s01_origin",
    "display": "s02_display",
    "lattice": "s03_lattice",
    "field": "s04_field",
    "prism": "s05_prism",
    "monolith": "s06_monolith",
    "cascade": "s07_cascade",
    "signature": "s08_signature",
}


class Clock:
    """Local time for one scene, in frames and seconds."""

    __slots__ = ("u", "f", "t", "dur", "span", "index", "name")

    def __init__(self, index: int, name: str, start: int, end: int, frame: int):
        self.index = index
        self.name = name
        self.span = (start, end)
        self.dur = end - start
        self.f = frame - start
        self.u = self.f / self.dur if self.dur else 0.0
        self.t = self.f / FPS

    def __repr__(self) -> str:
        return f"<Clock {self.name} f={self.f}/{self.dur} u={self.u:.3f}>"


def scene_for_frame(frame: int) -> Clock:
    for i, (name, a, b) in enumerate(SCENES):
        if a <= frame < b:
            return Clock(i, name, a, b, frame)
    return Clock(len(SCENES) - 1, SCENES[-1][0], SCENES[-1][1], SCENES[-1][2], frame)


_SCENE_CACHE: dict[str, object] = {}


def get_scene(name: str):
    """Import a scene module on demand (each one pulls in a different toolkit)."""
    if name not in _SCENE_CACHE:
        mod = importlib.import_module(_MODULES[name])
        _SCENE_CACHE[name] = mod.draw
    return _SCENE_CACHE[name]


def render_frame(frame: int) -> str:
    clock = scene_for_frame(frame)
    return get_scene(clock.name)(clock)


__all__ = ["Clock", "scene_for_frame", "get_scene", "render_frame", "TOTAL_FRAMES", "FPS", "SCENES"]
