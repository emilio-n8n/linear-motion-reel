#!/usr/bin/env python3
"""Contact sheet builder: render a strip of frames side by side for look-dev.

Iterating on motion means looking at many frames at once, not one at a time.
This renders evenly spaced frames across a range and tiles them into a single
image, so timing problems (a beat that fires too early, a hold that is too long)
are visible in one glance.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from brand import H, SCENES, W  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".build", "check")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a contact sheet of frames.")
    ap.add_argument("--scene", default=None, help="scene name; default is the whole reel")
    ap.add_argument("--count", type=int, default=8, help="frames to sample")
    ap.add_argument("--from-frame", type=int, default=None, help="explicit first frame")
    ap.add_argument("--to-frame", type=int, default=None, help="explicit last frame")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=480, help="per-tile width in px")
    ap.add_argument("--out", default=os.path.join(OUT, "sheet.png"))
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    height = round(args.width * H / W)

    if args.from_frame is not None and args.to_frame is not None:
        start, end = args.from_frame, args.to_frame + 1
    elif args.scene:
        for name, a, b in SCENES:
            if name == args.scene:
                start, end = a, b
                break
        else:
            print(f"unknown scene {args.scene!r}", file=sys.stderr)
            return 2
    else:
        start, end = 0, SCENES[-1][2]

    import timeline

    frames = [
        start + int((end - start) * i / max(args.count - 1, 1))
        for i in range(args.count)
    ]

    tiles = []
    for i, f in enumerate(frames):
        svg_path = os.path.join(OUT, f"t{i:02d}_{f:05d}.svg")
        png_path = os.path.join(OUT, f"t{i:02d}_{f:05d}.png")
        with open(svg_path, "w") as fh:
            fh.write(timeline.render_frame(f))
        r = subprocess.run(
            ["rsvg-convert", "-w", str(args.width), "-h", str(height), svg_path, "-o", png_path],
            capture_output=True,
        )
        if r.returncode != 0:
            print(f"frame {f}: {r.stderr.decode()[:200]}", file=sys.stderr)
            return 1
        tiles.append(png_path)

    # Stack with hstack/vstack rather than xstack: xstack's layout syntax wants
    # 'layout=' prefixes, and nesting row-stacks is easier to get right.
    # Pad the last row by repeating its final input, so rows are equal width.
    rows: list[list[int]] = [list(range(i, min(i + args.cols, len(tiles)))) for i in range(0, len(tiles), args.cols)]
    for r in rows:
        while len(r) < args.cols:
            r.append(r[-1])

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for t in tiles:
        cmd += ["-i", t]
    idx = 0
    chains = []
    labels = []
    for row in rows:
        chains.append("".join(f"[{m}]" for m in row) + f"hstack=inputs={len(row)}[r{idx}]")
        labels.append(f"[r{idx}]")
        idx += 1
    if len(rows) == 1:
        chains.append(f"{labels[0]}null[out]")
    else:
        chains.append("".join(labels) + f"vstack=inputs={len(rows)}[out]")
    cmd += ["-filter_complex", ";".join(chains), "-map", "[out]", "-frames:v", "1", "-update", "1", args.out]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        print(r.stderr.decode()[:2000], file=sys.stderr)
        return 1

    for t in tiles:
        os.remove(t)
        os.remove(t.replace(".png", ".svg"))
    print(f"wrote {args.out}  frames={frames}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
