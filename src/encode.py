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
OUT_DIR = os.path.join(ROOT, "out")

# Default output name per film, so the two never collide in out/.
DEFAULT_OUT = {
    "reel": "linear-craft-45s.mp4",
    "launch": "linear-launch-45s.mp4",
    "mcp": "claude-mcp-34s.mp4",
}

# film -> total frames. MCP is a 34s film, the others 45s.
FILM_FRAMES = {"reel": 1350, "launch": 1350, "mcp": 1020}


def frame_dir(film: str, width: int) -> str:
    """Matches render.py: frames are cached per film and per source width."""
    return os.path.join(ROOT, ".build", "frames", film, str(width))


def svg_dir(film: str, width: int) -> str:
    return os.path.join(ROOT, ".build", "svg", film, str(width))


def source_widths(film: str) -> list[int]:
    """Widths that have a frame directory for this film, largest first."""
    base = os.path.join(ROOT, ".build", "frames", film)
    if not os.path.isdir(base):
        return []
    out = []
    for name in os.listdir(base):
        if name.isdigit() and os.path.isdir(os.path.join(base, name)):
            out.append(int(name))
    return sorted(out, reverse=True)


def probe(film: str, width: int) -> int:
    """Check the frame set is complete for the film's own length."""
    total = FILM_FRAMES.get(film, TOTAL_FRAMES)
    missing = []
    d = frame_dir(film, width)
    for i in range(total):
        if not os.path.exists(os.path.join(d, f"frame_{i:05d}.png")):
            missing.append(i)
    if missing:
        avail = source_widths(film)
        hint = f" (frames exist at: {avail})" if avail else ""
        print(f"{len(missing)} of {total} frames missing at {width}px{hint}, "
              f"first: {missing[:6]}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Encode a frame sequence to MP4.")
    ap.add_argument("--film", choices=("reel", "launch", "mcp"), default="reel",
                    help="which film to encode")
    ap.add_argument("--out", default=None, help="output path (default depends on --film)")
    ap.add_argument("--crf", type=int, default=17, help="quality; lower is better")
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--every", type=int, default=1,
                    help="keep 1 frame in N; 3 gives a 10fps pass from 30fps source")
    ap.add_argument("--width", type=int, default=W, help="output width")
    ap.add_argument("--source-width", type=int, default=None,
                    help="width the frames were rendered at; default is the newest set present")
    ap.add_argument("--from-svg", action="store_true", help="encode from .build/svg instead of PNG frames")
    args = ap.parse_args()

    film = args.film
    if args.out is None:
        args.out = os.path.join(OUT_DIR, DEFAULT_OUT[film])

    # The frames were rendered at some width; find it rather than assuming the
    # encode width matches, because the two are independent knobs.
    src_width = args.source_width
    if src_width is None:
        avail = source_widths(film)
        if not avail:
            print(f"no rendered frames for film {film!r}", file=sys.stderr)
            return 1
        src_width = avail[0]
        print(f"[{film}] using frames at {src_width}px")

    if probe(film, src_width):
        return 1
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    # Output size is exactly what was asked for. (A previous version forced 960
    # whenever --width equalled the frame width, which silently produced a
    # half-size master for a full-size request.)
    width = args.width
    height = round(width * H / W)
    # yuv420p needs even dimensions. ffmpeg exits 187 on odd output, with an
    # error that is easy to miss, so both are forced even here rather than being
    # left to the caller to get right.
    width -= width % 2
    height -= height % 2
    if width < 2 or height < 2:
        print(f"width {args.width} is too small", file=sys.stderr)
        return 2

    if args.from_svg:
        if not os.path.isdir(svg_dir(film, src_width)):
            print("no .build/svg directory; re-render with --keep-svg", file=sys.stderr)
            return 1
        src = os.path.join(svg_dir(film, src_width), "frame_%05d.svg")
    else:
        src = os.path.join(frame_dir(film, src_width), "frame_%05d.png")

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

    print(f"[{film}] " + " ".join(cmd), flush=True)
    # stderr is streamed rather than captured: ffmpeg's real error message is
    # what tells you why a build failed, and swallowing it behind a bare exit
    # code makes failures undiagnosable from a notebook.
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        print(f"ffmpeg exited {proc.returncode}", file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        else:
            print("(ffmpeg produced no stderr; check dimensions and the codec)", file=sys.stderr)
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
