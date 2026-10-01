# Linear — 45s motion design reel

A 45-second, 1920×1080 @ 30fps motion graphics piece built as a craft reel for
[linear.app](https://linear.app). Abstract rather than a product demo: Linear's
actual design tokens and typography, eight studies that each demonstrate a
different technique.

```
t          scene       study
0.0 - 5.0  ORIGIN      a point becomes a hairline, the hairline a ground plane, the
                       plane a lattice; the camera settles
5.0 - 10.0 DISPLAY     type as the subject, three words, three reveal mechanics,
                       counter-tracking on every landing
10.0 - 15.5 LATTICE    459 nodes on phase-offset wavefronts, then a synchronised
                       reorganisation into a rotating isometric stack
15.5 - 21.0 FIELD      curl-noise vector field, 1500 particles with trails, a
                       comet threading through and displacing them
21.0 - 26.5 PRISM      a beam hits a spring-driven slat fan and refracts into a
                       violet spectrum
26.5 - 32.0 MONOLITH   display glyphs as slabs in 3D, quantised depth of field,
                       scatter and reassemble
32.0 - 38.0 CASCADE    nine panels collapse off in a diagonal wave — the timing
                       showpiece
38.0 - 45.0 SIGNATURE  a hand-built mark draws itself, statement type lands,
                       `linear.app`, and the grid breathes out
```

## How it works

No framework, no browser, no GPU. Every frame is a pure function of its index:

```python
def draw(clock) -> str:   # clock.f is the frame index within the scene
    ...                    # returns an SVG document
```

`render.py` turns each into a PNG with `rsvg-convert`; `encode.py` runs the
sequence through libx264. Because frames carry no shared state, they render in
any order, in parallel, and a run that is interrupted resumes from the first
missing frame.

```
src/brand.py       Linear's tokens, taken from linear.app's own stylesheet
src/easing.py      cubic-bezier solver + damped-spring integrator
src/layout.py      shaping-aware text metrics
src/svg.py         SVG builder, restricted to what rsvg actually renders
src/stock.py       pre-baked grain/vignette, geometry helpers
src/mark.py        the end-card mark, built from scratch
src/timeline.py    frame clock and scene registry
src/scenes/        s01…s08, one study each
src/render.py      SVG -> PNG, multiprocess, resumable
src/encode.py      PNG sequence -> H.264
tools/check_env.py environment verification
tools/sheet.py     contact sheet, for look-dev
tools/setup_env.sh dependency install (Debian/Ubuntu, used by Colab)
tools/colab.sh     drive a Colab T4 render and pull the result
```

## Rendering locally

```bash
bash tools/setup_env.sh      # once
python3 tools/check_env.py   # verify
make render                  # 1350 frames
make encode
```

`make preview` renders a decimated 960×540 pass in about 40s, which is the loop
to use while tuning timing.

## Rendering on a Colab T4

The frame generator is CPU-bound and parallel, and a T4 instance has many more
cores than a laptop, so the render is much faster there:

```bash
./tools/colab.sh
```

That opens `colab_render.ipynb`, which installs the dependencies, renders,
encodes, and commits the MP4 back to `main`. Pull it down with:

```bash
git pull origin main
open out/linear-craft-45s.mp4
```

The notebook needs a `GH_TOKEN` Colab secret with `repo` scope.

## Two things worth knowing

**Text metrics come from Pango, not a hand-rolled shaper.** librsvg shapes text
with Pango, so measuring through Pango is the only way the glyph positions
computed for kinetic type agree with what actually gets drawn. FreeType alone
returns no kerning for these fonts (their kerning lives in GPOS, and Inter has no
`kern` table at all).

**The SVG layer is restricted to what rsvg-convert supports.** It has no
`feTurbulence`, no `radialGradient`, and ignores `mix-blend-mode`. So the film
grain and vignette are pre-baked PNGs, glows are radial gradients rather than
stacked shapes, and the additive light in PRISM is built from layered
low-opacity fills. `svg.py` documents the full supported/unsupported split.

## Note on the mark

The end card uses a mark built from scratch in `mark.py` — it is not Linear's
logo asset, and the card is labelled *unofficial concept piece, not affiliated
with Linear*. Linear's brand guidelines ask that their marks not be altered or
used in a way implying endorsement, and that framing is what makes a lookalike
defensible.

## Licence

Inter and JetBrains Mono are both SIL Open Font License 1.1. The rest of the
source is yours to do as you like with.
