# Render + encode. Two films share this engine:
#   reel    the abstract craft reel
#   launch  the product launch film
# Frames are cached per film, so these are all safe to re-run.

PY      ?= python3
FILM    ?= launch
WIDTH   ?= 1920
JOBS    ?= 2
CRF     ?= 17
PRESET  ?= slow
PREVIEW_WIDTH ?= 756
PREVIEW = --preview

ifeq ($(FILM),launch)
OUT     ?= out/linear-launch-45s.mp4
else
OUT     ?= out/linear-craft-45s.mp4
endif

.PHONY: help env check render preview encode all sheet smoke clean distclean

help:
	@echo "make env        install dependencies (Debian/Ubuntu)"
	@echo "make check      verify the environment"
	@echo "make smoke      render one frame per scene and validate the SVG"
	@echo "make preview    fast decimated pass for timing work"
	@echo "make render     full render (1350 frames)"
	@echo "make encode     encode to \$$OUT"
	@echo "make all        render + encode"
	@echo "make sheet      contact sheet of the whole film"
	@echo ""
	@echo "  make render FILM=reel          the abstract craft reel"
	@echo "  make render FILM=launch        the product launch film (default)"
	@echo "  make render JOBS=4             more parallel workers"
	@echo "  make render scene=build        a single scene by name"
	@echo "  make preview FILM=launch       low-res, half the frames"

env:
	bash tools/setup_env.sh

check:
	$(PY) tools/check_env.py

smoke:
	$(PY) tools/smoke.py

render:
	$(PY) src/render.py --film $(FILM) --width $(WIDTH) --jobs $(JOBS) $(if $(scene),--scene $(scene),)

preview:
	$(PY) src/render.py --film $(FILM) --width $(PREVIEW_WIDTH) --jobs $(JOBS) $(if $(scene),--scene $(scene),)

encode:
	$(PY) src/encode.py --film $(FILM) --crf $(CRF) --preset $(PRESET) --out $(OUT)

all: render encode

sheet:
	$(PY) tools/sheet.py --count 16 --cols 4 --width 460

# Drop rendered frames for both films. The MP4s are kept.
clean:
	rm -rf .build/frames .build/svg .build/check .build/lsheet .build/review .build/review2 .build/review3

distclean: clean
	rm -rf out
