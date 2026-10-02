#!/usr/bin/env python3
"""Rewrite the notebook's render/encode cells in place.

Editing a .ipynb by hand means fighting JSON string escaping, so this script
owns those two cells. Everything else in the notebook is left alone.
"""

from __future__ import annotations

import json
import os
import sys

NB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "colab_render.ipynb")

RENDER_SRC = '''import os, sys, subprocess, time

# The apt install in the previous cell put python3-gi in Debian's dist-packages
# tree, which this interpreter does not search. Harmless if already on the path.
p = "/usr/lib/python3/dist-packages"
if os.path.isdir(p) and p not in sys.path:
    sys.path.append(p)

CORES = os.cpu_count() or 4
JOBS = max(1, CORES)          # rsvg is single-threaded per frame
TOTAL = 1350
print(f"{CORES} cores -> {JOBS} workers", flush=True)

# Streamed rather than captured, so progress appears as it happens and Ctrl-C is
# not swallowed waiting on a full pipe buffer.
proc = subprocess.Popen(
    ["python3", "src/render.py", "--width", "1920", "--jobs", str(JOBS)],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
)

start = time.time()
for line in proc.stdout:
    line = line.strip()
    if not line:
        continue
    print(line, flush=True)
    if "/1350" in line:
        try:
            done = int(line.split("/")[0].split()[-1])
            el = time.time() - start
            rate = done / el if el else 0
            eta = (TOTAL - done) / rate if rate else 0
            print(f"    -> {100.0 * done / TOTAL:5.1f}%  {rate:5.1f} fps  "
                  f"elapsed {el / 60:4.1f}m  eta {eta / 60:4.1f}m", flush=True)
        except (ValueError, IndexError):
            pass

proc.wait()
if proc.returncode != 0:
    raise SystemExit(f"render failed: {proc.returncode}")
'''

ENCODE_SRC = '''subprocess.run(
    ["python3", "src/encode.py", "--crf", "17", "--preset", "slow"],
    check=True,
)
'''


def main() -> int:
    with open(NB) as fh:
        nb = json.load(fh)

    render_i = encode_i = None
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "src/render.py" in src and render_i is None:
            render_i = i
        elif "src/encode.py" in src and encode_i is None:
            encode_i = i

    if render_i is None:
        print("could not find the render cell", file=sys.stderr)
        return 1
    if encode_i is None:
        print("could not find the encode cell", file=sys.stderr)
        return 1

    for idx, body in ((render_i, RENDER_SRC), (encode_i, ENCODE_SRC)):
        cell = nb["cells"][idx]
        cell["source"] = body.splitlines(keepends=True)
        cell["outputs"] = []
        cell["execution_count"] = None

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1)
        fh.write("\n")

    print(f"rewrote cell {render_i} (render) and cell {encode_i} (encode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
