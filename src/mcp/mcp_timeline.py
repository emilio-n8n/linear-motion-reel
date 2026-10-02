"""Timeline for the Claude / MCP film.

Seven scenes, 34.0s at 30fps, matching the brief's timings: 3 / 4 / 5 / 4 / 4 / 8 / 6.

Scene boundaries are frame counts, not seconds, so the timeline cannot drift.
"""

from __future__ import annotations

import importlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
for _p in (_SRC, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tokens import FPS, TOTAL_FRAMES  # noqa: E402

# (name, module, first_frame, last_frame_exclusive)
SCENES = [
    ("org", "m01_org", 0, 90),
    ("once", "m02_once", 90, 210),
    ("idp", "m03_idp", 210, 360),
    ("login", "m04_login", 360, 480),
    ("tools", "m05_tools", 480, 600),
    ("prompt", "m06_prompt", 600, 840),
    ("packshot", "m07_packshot", 840, 1020),
]

assert SCENES[-1][3] == TOTAL_FRAMES, (SCENES[-1][3], TOTAL_FRAMES)

MODULES = {name: mod for name, mod, _a, _b in SCENES}


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
    for i, (name, _mod, a, b) in enumerate(SCENES):
        if a <= frame < b:
            return Clock(i, name, a, b, frame)
    last = SCENES[-1]
    return Clock(len(SCENES) - 1, last[0], last[2], last[3], frame)


_CACHE: dict[str, object] = {}


def get_scene(name: str):
    if name not in _CACHE:
        _CACHE[name] = importlib.import_module(MODULES[name]).draw
    return _CACHE[name]


def render_frame(frame: int) -> str:
    clock = scene_for_frame(frame)
    return get_scene(clock.name)(clock)


def scene_span(name: str) -> tuple[int, int]:
    for n, _mod, a, b in SCENES:
        if n == name:
            return a, b
    raise KeyError(name)
