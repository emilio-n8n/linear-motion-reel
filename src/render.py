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
for _p in (_HERE, os.path.join(_HERE, "launch")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brand import FPS, H, TOTAL_FRAMES, W  # noqa: E402
from stock import ensure_assets  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSVG = "rsvg-convert"

FILMS = ("reel", "launch")


def frame_dir(film: str, width: int) -> str:
    """Frames are cached per film *and* per width.

    Keying on the film alone means a 756px run silently satisfies a later 1920px
    request, and the encode then produces a master at the wrong resolution with no
    error anywhere. The width is part of the identity of a frame.
    """
    sub = "reel" if film == "reel" else film
    return os.path.join(ROOT, ".build", "frames", sub, str(width))


def svg_dir(film: str, width: int) -> str:
    sub = "reel" if film == "reel" else film
    return os.path.join(ROOT, ".build", "svg", sub, str(width))


def scene_list(film: str) -> list[tuple[str, int, int]]:
    """(name, start, end) triples for either film."""
    if film == "reel":
        from brand import SCENES

        return [(n, a, b) for n, a, b in SCENES]
    mod = importlib.import_module("launch_timeline")
    return [(n, a, b) for n, _mod, a, b in mod.SCENES]


def frame_module(film: str) -> str:
    return "timeline" if film == "reel" else "launch_timeline"


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
    ap.add_argument("--end", type=int, default=TOTAL_FRAMES)
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

    start, end = args.start, min(args.end, TOTAL_FRAMES)

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
    print(f"[{film}] {label}: {len(frames)} in range, {skipped} cached at {width}px, "
          f"{len(todo)} to render on {args.jobs} workers", flush=True)

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
