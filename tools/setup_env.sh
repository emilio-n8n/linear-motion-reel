#!/usr/bin/env bash
# Install everything the render pipeline needs on a Debian/Ubuntu image.
#
# Written for Google Colab, which ships Python and ffmpeg but none of the text
# or SVG stack this project depends on. Safe to re-run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> apt packages"
# librsvg2-bin        rsvg-convert, the per-frame rasteriser
# python3-gi + gir1.2  Pango/Cairo introspection, for exact text metrics
# libcairo2-dev        cairo headers, required by python3-gi's cairo backend
# fontconfig          family lookup, which the metrics layer relies on
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  librsvg2-bin \
  python3-gi \
  python3-gi-cairo \
  gir1.2-pango-1.0 \
  libcairo2-dev \
  libgirepository1.0-dev \
  fontconfig \
  ffmpeg \
  >/dev/null

echo "==> fonts"
# The renderer resolves font families by name through fontconfig, so the TTFs in
# assets/fonts have to be installed system-wide and the cache rebuilt. Without
# this, metrics silently fall back to a default face and every glyph position
# shifts.
mkdir -p /usr/share/fonts/truetype/motion-design
cp "$REPO_ROOT"/assets/fonts/*.ttf /usr/share/fonts/truetype/motion-design/
fc-cache -f >/dev/null

echo "==> python deps"
pip install --quiet --no-input numpy >/dev/null

echo "==> verifying"
python3 "$REPO_ROOT/tools/check_env.py"
