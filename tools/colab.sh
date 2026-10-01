#!/usr/bin/env bash
# One-shot driver: render on a Colab T4, commit the master back, pull it here.
#
# Splitting it this way means the long render is never sitting in a local
# terminal, and the local machine only ever does a git fetch.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTEBOOK="$REPO_DIR/colab_render.ipynb"
OUT="$REPO_DIR/out/linear-craft-45s.mp4"
SKIP_PULL=0

usage() {
  cat <<'EOF'
usage: ./tools/colab.sh [options]

  --notebook PATH   notebook to open (default: colab_render.ipynb)
  --skip-pull       do not pull the rendered MP4 when the run finishes
  -h, --help        show this help

Requires: a gh CLI logged in with repo scope, and a browser for the Colab
session. The notebook is opened in your default browser; execution is manual.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --notebook) NOTEBOOK="$2"; shift 2 ;;
    --skip-pull) SKIP_PULL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

cd "$REPO_DIR"

if [ ! -f "$NOTEBOOK" ]; then
  echo "no notebook at $NOTEBOOK" >&2
  exit 1
fi

if ! git diff --quiet || [ -n "$(git status --porcelain)" ]; then
  echo "warning: uncommitted changes in the repo; the render will use what is pushed" >&2
fi

echo "==> opening $NOTEBOOK in Colab"
gh browse --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner)" "colab_render.ipynb" 2>/dev/null \
  || xdg-open "https://colab.research.google.com/github/$(gh repo view --json nameWithOwner -q .nameWithOwner)/blob/main/colab_render.ipynb" \
  || echo "open the notebook manually: $NOTEBOOK"

cat <<'EOF'

In the notebook, run the cells top to bottom. The last cell commits the MP4 to
main using the GH_TOKEN Colab secret.

  - Create the secret: Colab -> Secrets -> Add new secret, name GH_TOKEN,
    value = a GitHub token with `repo` scope.
  - Generate a token: github.com/settings/tokens -> Generate new (classic),
    tick `repo`.

Then come back here and run this again to pull the result.
EOF

if [ "$SKIP_PULL" -eq 1 ]; then
  exit 0
fi

echo
read -r -p "Press Enter once the notebook has finished and pushed (or Ctrl-C to stop) " _

if [ -f "$OUT" ]; then
  echo "==> pulling"
  git pull --ff-only origin main
  ls -lh "$OUT"
  echo
  echo "done: $OUT"
else
  echo "no local master yet at $OUT" >&2
fi
