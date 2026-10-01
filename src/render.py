#!/usr/bin/env python3
"""Frame renderer: SVG -> PNG via rsvg-convert, in parallel, resumable.

Frames are written to .build/frames/frame_%05d.png. Rendering is embarrassingly
parallel and skip-if-present, so an interrupted run continues where it stopped
and a single scene can be re-rendered without touching the rest.
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brand import FPS, H, SCENES, TOTAL_FRAMES, W  # noqa: E402
from stock import ensure_assets  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(ROOT, ".build", "frames")
SVG_DIR = os.path.join(ROOT, ".build", "svg")
RSVG = "rsvg-convert"


def frame_path(i: int) -> str:
    return os.path.join(FRAME_DIR, f"frame_{i:05d}.png")


def svg_path(i: int) -> str:
    return os.path.join(SVG_DIR, f"frame_{i:05d}.svg")


def _render_one(args: tuple[int, int, bool]) -> tuple[int, float, str]:
    """Worker: build the SVG for one frame and rasterise it."""
    frame, width, keep_svg = args
    t0 = time.time()
    try:
        # Imported in the worker so each process pays the shaping/font cost once.
        import timeline

        svg = timeline.render_frame(frame)
    except Exception as exc:  # noqa: BLE001
        return frame, 0.0, f"ERR build {frame}: {type(exc).__name__}: {exc}"

    if keep_svg:
        with open(svg_path(frame), "w") as fh:
            fh.write(svg)

    out = frame_path(frame)
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
    ap = argparse.ArgumentParser(description="Render frames for the Linear craft reel.")
    ap.add_argument("--preview", action="store_true", help="960x540, every 2nd frame (timing check)")
    ap.add_argument("--width", type=int, default=W, help="output width in px")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=TOTAL_FRAMES)
    ap.add_argument("--scene", type=str, default=None, help="render only this scene by name")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--keep-svg", action="store_true", help="also write the SVG for each frame")
    ap.add_argument("--force", action="store_true", help="re-render frames that already exist")
    args = ap.parse_args()

    ensure_assets()
    os.makedirs(FRAME_DIR, exist_ok=True)
    if args.keep_svg:
        os.makedirs(SVG_DIR, exist_ok=True)

    width = 960 if args.preview else args.width
    step = 2 if args.preview else 1
    start, end = args.start, min(args.end, TOTAL_FRAMES)

    if args.scene:
        for name, a, b in SCENES:
            if name == args.scene:
                start, end = a, b
                break
        else:
            print(f"unknown scene {args.scene!r}; have {[s[0] for s in SCENES]}", file=sys.stderr)
            return 2

    frames = list(range(start, end, step))
    todo = [f for f in frames if args.force or not os.path.exists(frame_path(f))]
    skipped = len(frames) - len(todo)

    label = "preview" if args.preview else f"{width}px"
    print(f"{label}: {len(frames)} frames in range, {skipped} cached, {len(todo)} to render on {args.jobs} workers")

    if not todo:
        print("nothing to do")
        return 0

    t0 = time.time()
    done = 0
    errors: list[str] = []
    with mp.Pool(args.jobs) as pool:
        for frame, dt, err in pool.imap_unordered(
            _render_one, [(f, width, args.keep_svg) for f in todo], chunksize=4
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
