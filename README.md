# Linear — 45s motion films

Two 45-second films built on one engine: a pure-Python frame generator that emits
SVG per frame, rasterises with `rsvg-convert`, and encodes with libx264. No
framework, no browser, no GPU.

| film | what it is |
|---|---|
| **`launch`** | the product launch film. Eight beats walking Linear's own feature taxonomy: overview, planning, issue tracking, cycles, command palette, agents, insights, release. |
| **`reel`** | the abstract craft reel. Eight motion studies — no product UI — used to demonstrate range. |

Both are 1920×1080 @ 30fps, 1350 frames, 45.0s.

## The launch film

| t | beat | what it shows |
|---|---|---|
| 0–5 | **OVERVIEW** | the workspace assembles, then the positioning lands |
| 5–10.5 | **PLANNING** | project `Release 2.4`: health, a scoped timeline with a playhead, progress rollup |
| 10.5–16 | **ISSUE TRACKING** | triage — eight issues change priority and the list re-sorts in one snap |
| 16–21 | **CYCLES** | a burndown drawing itself to zero, velocity counting up, issues striking off |
| 21–26.5 | **COMMAND PALETTE** | the app defocuses, `⌘K` drops, a query types itself, a command executes |
| 26.5–32 | **AGENTS** | an agent picks up an issue, works it, opens a coding session, returns a diff for review |
| 32–37 | **INSIGHTS** | throughput columns, a rolling trend, time-in-status breakdown |
| 37–45 | **RELEASE** | the app recedes, the mark traces on, the statement lands, `linear.app` |

The design values are Linear's own, taken from their public surfaces rather than
eyeballed — the palette from their stylesheet and `theme-color`, the status
workflow (`Backlog > Todo > In Progress > Done > Canceled`) from their docs,
and Inter Variable 4.1, the version their site actually serves.

## The craft reel

Abstract studies in the same visual language: `ORIGIN` (a point becomes a ground
plane), `DISPLAY` (three type reveal mechanics), `LATTICE` (459 nodes on
phase-offset wavefronts re-organising into an isometric stack), `FIELD` (a
curl-noise vector field with 1500 trailing particles), `PRISM` (a beam refracting
through a spring-driven slat fan), `MONOLITH` (3D type with quantised depth of
field), `CASCADE` (nine panels collapsing in a diagonal wave), `SIGNATURE`.

## How it works

Every frame is a pure function of its index:

```python
def draw(clock) -> str:   # clock.f is the frame index within the scene
    ...                    # returns an SVG document
```

That is the whole architectural bet. Because frames share no state, they render
in any order, in parallel, and an interrupted run resumes from the first missing
frame. Two scenes need simulation — the PRISM slat springs and the FIELD particle
advection — and both are re-integrated from `t=0` on every frame rather than
carrying state, which is what keeps the property true at a cost of a few thousand
sub-steps per frame.

```
src/brand.py          design tokens
src/ui.py             reconstructed app chrome, built from paths
src/easing.py         cubic-bezier solver + damped-spring integrator
src/layout.py         shaping-aware text metrics
src/svg.py            SVG builder, restricted to what rsvg renders
src/stock.py          pre-baked grain/vignette, geometry helpers
src/scenes/           the craft reel, s01…s08
src/timeline.py       the craft reel's clock and scene registry
src/launch/           the launch film, l01…l08 + launch_timeline.py
src/render.py         SVG -> PNG, multiprocess, resumable, --film selects the film
src/encode.py         PNG sequence -> H.264
tools/smoke.py        render one frame per scene and validate the SVG
tools/sheet.py        contact sheet, for look-dev
tools/check_env.py    environment verification
tools/setup_env.sh    dependency install (Debian/Ubuntu, used by Colab)
tools/colab.sh        drive a Colab render and pull the result
```

## Rendering

```bash
bash tools/setup_env.sh      # once
python3 tools/check_env.py   # verify
make smoke                   # one frame per scene, validated

make render FILM=launch      # 1350 frames, ~3 min on 2 cores
make encode FILM=launch
```

`FILM=reel` renders the craft reel instead; `launch` is the default. Frames are
cached per film under `.build/frames/<film>/`, so the two never invalidate each
other.

`make render WIDTH=756 JOBS=4` is the loop to use while tuning timing: a
third of the pixels, and the per-scene structure means a bad beat is visible
from a contact sheet long before a full render.

## Rendering on Colab

The generator is CPU-bound and parallel, so a Colab instance with more cores is
faster than a laptop. **The GPU is not used, on purpose** — neither the geometry
nor `rsvg-convert` has a GPU path, so a GPU runtime changes nothing. What matters
is core count.

```bash
./tools/colab.sh
```

That opens `colab_render.ipynb`, which installs the dependencies, renders,
encodes, and commits the MP4 back to `main`. Then:

```bash
git pull origin main
open out/linear-launch-45s.mp4
```

The notebook needs a `GH_TOKEN` Colab secret with `repo` scope. Set `FILM` in the
first cell to switch films.

Note that Colab's storage is ephemeral: a runtime restart discards the clone and
every cached frame.

## Three things worth knowing

**Text metrics come from Pango, not a hand-rolled shaper.** librsvg shapes text
with Pango, so measuring through Pango is the only way the glyph positions
computed for kinetic type agree with what actually gets drawn. FreeType alone
returns no kerning for these fonts — their kerning lives in GPOS, and Inter has
no `kern` table at all.

**The SVG layer is restricted to what rsvg-convert supports.** It has no
`feTurbulence`, no `radialGradient`, and ignores `mix-blend-mode`. So the grain
and vignette are pre-baked PNGs, glows are radial gradients rather than stacked
shapes, and the additive light in PRISM is layered low-opacity fills. `svg.py`
documents the full supported/unsupported split.

**The app UI is a reconstruction, and the film says so.** The chrome in
`src/ui.py` is drawn from paths using Linear's published tokens and documented
workflow; no asset is taken from their product. On the end card the film labels
itself an unofficial concept piece, and it uses a mark built from scratch in
`src/launch/l08_launch.py` rather than their logo. Linear's brand guidelines ask
that their marks not be altered or used to imply endorsement, and that framing is
what keeps a spec piece on the right side of that line.

## Licensing

Inter and JetBrains Mono are both SIL Open Font License 1.1. The rest of the
source is yours to do as you like with.
