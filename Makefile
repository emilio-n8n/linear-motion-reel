# Render + encode the reel. Frames are cached, so these are safe to re-run.

PY      ?= python3
WIDTH   ?= 1920
JOBS    ?= 2
CRF     ?= 17
PRESET  ?= slow
OUT     ?= out/linear-craft-45s.mp4

.PHONY: help env check render preview encode sheet all clean distclean

help:
	@echo "make env       install dependencies (Debian/Ubuntu)"
	@echo "make check     verify the environment"
	@echo "make preview   fast decimated pass for timing work (~40s)"
	@echo "make render    full $(WIDTH)px render (1350 frames)"
	@echo "make encode    encode to $(OUT)"
	@echo "make all       render + encode"
	@echo "make sheet     contact sheet of the whole reel"
	@echo ""
	@echo "  make render JOBS=4      more parallel workers"
	@echo "  make render scene=field  render a single scene"

env:
	bash tools/setup_env.sh

check:
	$(PY) tools/check_env.py

render:
	$(PY) src/render.py --width $(WIDTH) --jobs $(JOBS) $(if $(scene),--scene $(scene),)

preview:
	$(PY) src/render.py --preview --jobs $(JOBS) $(if $(scene),--scene $(scene),)

encode:
	$(PY) src/encode.py --crf $(CRF) --preset $(PRESET) --out $(OUT)

all: render encode

sheet:
	$(PY) tools/sheet.py --count 16 --cols 4 --width 460

# Drop rendered frames. The MP4 is kept.
clean:
	rm -rf .build/frames .build/svg .build/check

distclean: clean
	rm -rf out
