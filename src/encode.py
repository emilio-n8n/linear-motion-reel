#!/usr/bin/env python3
"""Encoder: PNG sequence -> H.264 MP4.

The installed ffmpeg has no -pattern_type glob, so frames are read through the
image2 demuxer with an explicit zero-padded sequence starting at 0.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brand import FPS, H, TOTAL_FRAMES, W  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(ROOT, ".build", "frames")
SVG_DIR = os.path.join(ROOT, ".build", "svg")
OUT_DIR = os.path.join(ROOT, "out")


def probe() -> int:
    missing = []
    for i in range(TOTAL_FRAMES):
        if not os.path.exists(os.path.join(FRAME_DIR, f"frame_{i:05d}.png")):
            missing.append(i)
    if missing:
        print(f"{len(missing)} of {TOTAL_FRAMES} frames missing, first: {missing[:10]}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Encode the frame sequence to MP4.")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "linear-craft-45s.mp4"))
    ap.add_argument("--crf", type=int, default=17, help="quality; lower is better")
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--every", type=int, default=1,
                    help="keep 1 frame in N; 3 gives a 10fps pass from 30fps source")
    ap.add_argument("--width", type=int, default=W)
    ap.add_argument("--from-svg", action="store_true", help="encode from .build/svg instead of PNG frames")
    args = ap.parse_args()

    if probe():
        return 1
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    width = 960 if args.width == W else args.width
    height = round(width * H / W)
    # yuv420p needs even dimensions.
    width += width % 2
    height += height % 2

    if args.from_svg:
        if not os.path.isdir(SVG_DIR):
            print("no .build/svg directory; re-render with --keep-svg", file=sys.stderr)
            return 1
        src = os.path.join(SVG_DIR, "frame_%05d.svg")
    else:
        src = os.path.join(FRAME_DIR, "frame_%05d.png")

    # Read the sequence at its authored rate, then drop frames in the filter.
    # Decimating with `select` rather than by lowering -framerate matters: a lower
    # input rate makes ffmpeg *play* the existing files slower, which would give a
    # 135s file instead of a 45s one.
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(FPS),
        "-start_number", "0",
        "-i", src,
    ]

    filters = []
    if args.every > 1:
        filters.append(f"select=not(mod(n\\,{args.every}))")
    filters.append(f"scale={width}:{height}:flags=lanczos")
    # Give the decimated stream a clean frame rate; without setpts the output
    # inherits the input timestamps and the duration comes out wrong.
    filters.append(f"fps={args.fps}")

    cmd += [
        "-vf", ",".join(filters),
        "-c:v", "libx264",
        "-preset", args.preset,
        "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-r", str(args.fps),
        args.out,
    ]

    print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        print(proc.stderr.decode()[:4000], file=sys.stderr)
        return proc.returncode

    size = os.path.getsize(args.out) / 1e6
    print(f"wrote {args.out}  {width}x{height} @ {args.fps}fps  {size:.1f} MB")

    # Report what was actually produced rather than what was asked for: the
    # frame count and duration are where a decimation mistake shows up.
    probe_out = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames,codec_name,pix_fmt",
         "-show_entries", "format=duration",
         "-of", "default=nw=1", args.out],
        capture_output=True,
    )
    print(probe_out.stdout.decode().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
