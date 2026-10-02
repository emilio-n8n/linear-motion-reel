#!/usr/bin/env python3
"""Frame renderer: SVG -> PNG via rsvg-convert, in parallel, resumable.

Frames are written under .build/frames/. Rendering is embarrassingly parallel and
skip-if-present, so an interrupted run continues where it stopped and a single
scene can be re-rendered without touching the rest.

Two films share this driver: the craft reel (src/timeline.py) and the launch film
(src/launch/launch_timeline.py). They differ only in their scene list, so
`--film` picks which one supplies the frames. Frame directories are namespaced
per film so rendering one never invalidates the other's cache.
"""

from __future__ import annotations

import argparse
import importlib
import multiprocessing as mp
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
# Scene module dirs, so any film's scenes can be imported by bare name.
for _p in (_HERE, os.path.join(_HERE, "launch"), os.path.join(_HERE, "mcp")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brand import FPS, H, TOTAL_FRAMES, W  # noqa: E402  (W/H shared by all films)
from stock import ensure_assets  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSVG = "rsvg-convert"

FILMS = ("reel", "launch", "mcp")


def frame_dir(film: str, width: int) -> str:
    """Frames are cached per film *and* per width.

    Keying on the film alone means a 756px run silently satisfies a later 1920px
    request, and the encode then produces a master at the wrong resolution with no
    error anywhere. The width is part of the identity of a frame.
    """
    return os.path.join(ROOT, ".build", "frames", film, str(width))


def svg_dir(film: str, width: int) -> str:
    return os.path.join(ROOT, ".build", "svg", film, str(width))


# film -> (timeline module, scene count). The MCP film is shorter, so it carries
# its own total rather than using the shared 1350.
FILM_MODULES = {
    "reel": ("timeline", 1350),
    "launch": ("launch_timeline", 1350),
    "mcp": ("mcp_timeline", 1020),
}


def scene_list(film: str) -> list[tuple[str, int, int]]:
    """(name, start, end) triples for any film."""
    if film == "reel":
        from brand import SCENES

        return [(n, a, b) for n, a, b in SCENES]
    mod = importlib.import_module(FILM_MODULES[film][0])
    return [(n, a, b) for n, _mod, a, b in mod.SCENES]


def film_frames(film: str) -> int:
    return FILM_MODULES[film][1]


def frame_module(film: str) -> str:
    return FILM_MODULES[film][0]


def frame_path(film: str, width: int, i: int) -> str:
    return os.path.join(frame_dir(film, width), f"frame_{i:05d}.png")


def svg_path(film: str, width: int, i: int) -> str:
    return os.path.join(svg_dir(film, width), f"frame_{i:05d}.svg")


def _render_one(args: tuple[str, int, int, bool]) -> tuple[int, float, str]:
    """Worker: build the SVG for one frame and rasterise it."""
    film, frame, width, keep_svg = args
    t0 = time.time()
    try:
        # Imported in the worker so each process pays the shaping/font cost once,
        # and so the module is chosen per film rather than fixed at startup.
        module = importlib.import_module(frame_module(film))
        svg = module.render_frame(frame)
    except Exception as exc:  # noqa: BLE001
        return frame, 0.0, f"ERR build {frame}: {type(exc).__name__}: {exc}"

    if keep_svg:
        with open(svg_path(film, width, frame), "w") as fh:
            fh.write(svg)

    out = frame_path(film, width, frame)
    tmp = out + ".tmp.png"
    cmd = [RSVG, "-w", str(width), "-h", str(round(width * H / W)), "-o", tmp, "-"]
    try:
        proc = subprocess.run(cmd, input=svg.encode(), capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return frame, 0.0, f"ERR timeout {frame}"
    if proc.returncode != 0:
        return frame, 0.0, f"ERR rsvg {frame}: {proc.stderr.decode()[:200]}"
    os.replace(tmp, out)
    return frame, time.time() - t0, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Render frames for a Linear motion film.")
    ap.add_argument("--film", choices=FILMS, default="reel", help="which film to render")
    ap.add_argument("--preview", action="store_true", help="960x540, every 2nd frame (timing check)")
    ap.add_argument("--width", type=int, default=W, help="output width in px")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None, help="defaults to the film's length")
    ap.add_argument("--scene", type=str, default=None, help="render only this scene by name")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--keep-svg", action="store_true", help="also write the SVG for each frame")
    ap.add_argument("--force", action="store_true", help="re-render frames that already exist")
    args = ap.parse_args()

    film = args.film
    scenes = scene_list(film)

    ensure_assets()

    width = 960 if args.preview else args.width
    step = 2 if args.preview else 1

    os.makedirs(frame_dir(film, width), exist_ok=True)
    if args.keep_svg:
        os.makedirs(svg_dir(film, width), exist_ok=True)

    # The film's own length wins: the MCP film is 34s, the others 45s.
    total = film_frames(film)
    start = args.start
    end = min(args.end if args.end is not None else total, total)

    if args.scene:
        for name, a, b in scenes:
            if name == args.scene:
                start, end = a, b
                break
        else:
            print(f"unknown scene {args.scene!r}; have {[s[0] for s in scenes]}", file=sys.stderr)
            return 2

    frames = list(range(start, end, step))
    todo = [f for f in frames if args.force or not os.path.exists(frame_path(film, width, f))]
    skipped = len(frames) - len(todo)

    label = "preview" if args.preview else f"{width}px"
    print(f"[{film}] {label}: {len(frames)} of {total} in range, {skipped} cached at "
          f"{width}px, {len(todo)} to render on {args.jobs} workers", flush=True)

    if not todo:
        print("nothing to do")
        return 0

    t0 = time.time()
    done = 0
    errors: list[str] = []
    with mp.Pool(args.jobs) as pool:
        for frame, dt, err in pool.imap_unordered(
            _render_one, [(film, f, width, args.keep_svg) for f in todo], chunksize=4
        ):
            done += 1
            if err:
                errors.append(err)
                if len(errors) <= 8:
                    print(f"  {err}", file=sys.stderr)
            if done % 60 == 0 or done == len(todo):
                rate = done / max(time.time() - t0, 1e-6)
                left = (len(todo) - done) / max(rate, 1e-6)
                print(f"  {done}/{len(todo)}  {rate:.1f} fps  eta {left:5.1f}s", flush=True)

    total = time.time() - t0
    print(f"done in {total:.1f}s ({len(todo) / max(total, 1e-6):.1f} fps)")
    if errors:
        print(f"{len(errors)} frame(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
