"""Timeline for the launch film.

A second film over the same engine as the craft reel. Both share render.py,
encode.py, svg.py and layout.py; only the scene list and the modules differ, so
this file is the whole of the difference.

Scene boundaries are frame counts, not seconds, so the timeline cannot drift.
Total is 45.0s at 30fps, matching the reel.
"""

from __future__ import annotations

import importlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
_LAUNCH = _HERE

for p in (_SRC, _LAUNCH):
    if p not in sys.path:
        sys.path.insert(0, p)

from brand import FPS, TOTAL_FRAMES  # noqa: E402

# (name, module, first_frame, last_frame_exclusive)
SCENES = [
    ("promise", "l01_promise", 0, 150),
    ("planning", "l02_planning", 150, 315),
    ("build", "l03_build", 315, 480),
    ("velocity", "l04_velocity", 480, 630),
    ("palette", "l05_palette", 630, 795),
    ("agents", "l06_agents", 795, 960),
    ("insights", "l07_insights", 960, 1110),
    ("launch", "l08_launch", 1110, 1350),
]

assert SCENES[-1][3] == TOTAL_FRAMES, (SCENES[-1][3], TOTAL_FRAMES)

_NAMES = [s[0] for s in SCENES]


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
        for n, mod, _a, _b in SCENES:
            if n == name:
                _CACHE[name] = importlib.import_module(mod).draw
                break
        else:
            raise KeyError(name)
    return _CACHE[name]


def render_frame(frame: int) -> str:
    clock = scene_for_frame(frame)
    return get_scene(clock.name)(clock)


def scene_span(name: str) -> tuple[int, int]:
    for n, _m, a, b in SCENES:
        if n == name:
            return a, b
    raise KeyError(name)
