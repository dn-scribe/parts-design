# Repo instructions

This file is the single source of truth for how this repository is organized and how designs
are built, documented, and validated. `CLAUDE.md` and `AGENTS.md` at the repo root both point
here — keep this file up to date rather than duplicating content in those files.

## What this repo is

A collection of mechanical parts designed primarily as FreeCAD Python scripts/macros. Each part
is parametric: running its script regenerates the model and exports fabrication-ready outputs
(STL, GLB).

## Layout

```
/
├── CLAUDE.md                  # pointer to this file
├── AGENTS.md                  # pointer to this file
├── README.md                  # top-level index of all parts (picture + link per part)
├── Makefile                   # `make <name>` builds a single design
├── docs/
│   └── agents-instructions.md # this file
├── scripts/
│   ├── render_preview.py      # STL -> static outputs/preview.png, called by the Makefile
│   └── freecad_common.py      # shared parse_outdir()/export_glb()/build_knurled_cylinder()/
│                               # build_retainer_fingers(), imported by every generate.py
└── designs/
    └── <design-name>/
        ├── README.md          # purpose, spec, parameters, usage, integration/BOM
        ├── generate.py        # FreeCAD python script/macro
        └── outputs/           # generated STL/GLB/preview.png (and any other export) files
```

Each design lives in its own folder under `designs/`. Do not mix multiple parts in one folder —
one folder is one printable part. When several parts form a physical assembly (e.g. a build
plate made of a corner clamp + a bracket + a bin), each still gets its own folder; cross-link the
sibling folders from each part's own README (a line near the top, plus a short mention in
"Integration / use" of how it fits with the others) rather than writing one combined README or
merging their `generate.py` scripts. `<design-name>` should be a short kebab-case slug (e.g.
`cable-clip`, `tripod-mount`); for a part that's one of several in a named assembly, prefix it
with the assembly name (e.g. `build-plate-corner-clamp`).

**Shared structural numbers across sibling designs** (e.g. one part's footprint has to fit inside
another's cavity) should be cross-imported, not duplicated as separately-maintained constants —
duplicated numbers drift, and a drifted number here means parts that don't physically fit
together, silently. `build-plate-catch-bin/generate.py` imports `TILE_SIZE`/`LEG_SIZE` directly
from `build-plate-corner-clamp/generate.py` (`sys.path` insert + `from generate import ...`) for
exactly this reason; it's safe because a design's own build only runs under
`if __name__ == "__main__"`, so importing another design's script as a module pulls in its
constants/functions without re-executing its `main()`.

## Per-design README requirements

Every `designs/<name>/README.md` must include, in this order:

1. **Purpose** — what the part is for and why it exists.
2. **Spec** — key dimensions/constraints the design must satisfy.
3. **Parameters** — every parametrized value exposed by `generate.py` (name, meaning, default,
   units).
4. **How to use** — instructions to regenerate the part. If it takes more than opening the file
   in FreeCAD, include a copy-pasteable command-line snippet (see "Building a design" below).
5. **Integration / use** — how the part is actually used/installed, including a BOM (bill of
   materials: this part plus any fasteners, hardware, or other purchased/printed items needed
   to put it to use).

Embed the generated STL/GLB from `outputs/` directly in the README as HTML so they're viewable
inline on GitHub, e.g.:

```html
<img src="outputs/preview.png" alt="cable-clip preview" width="400" />

<a href="outputs/cable-clip.stl">Download STL</a>
<a href="outputs/cable-clip.glb">Download GLB</a>
```

GitHub does not render interactive 3D viewers inline in READMEs (no `<model-viewer>`, no scripts
— markdown is sanitized) — link to the files (GitHub's own file viewer will render `.stl`/`.glb`
when the link is opened) and always include `outputs/preview.png`, a static render, for
at-a-glance viewing directly in the README. `make <name>` generates `preview.png` automatically
via `scripts/render_preview.py` (STL → matplotlib isometric render) — don't hand-draw it.

## The `generate.py` script contract

Each design's `generate.py`:

- Is runnable headless via `freecadcmd` (no GUI dependency).
- Exposes its parameters as clearly named constants/variables near the top of the file (or via
  argparse), matching what the README documents.
- Accepts an optional output directory (`--outdir`, argparse) so the Makefile/CI can redirect
  output. Default (no `--outdir`) writes to `designs/<name>/outputs/` relative to the script.
- Exports at minimum an `.stl` and a `.glb` into the output directory, named after the design.
- Exits non-zero on failure so CI can detect broken builds.
- **Must be 3D-printable in a stated natural orientation (FDM, no supports assumed).** "Builds
  headlessly" and "exports valid STLs" are necessary but not sufficient — a shape can be perfectly
  valid B-rep geometry and still be unprintable. Before calling a design done, state (in the
  README, and in your own head while modeling) which face sits on the bed, and check that nothing
  requires a support-needing overhang *as a consequence of a feature that only exists to attach to
  something else* (an undercut snap-fit, a hook reaching down and inward, a boss on the underside
  of an otherwise-flat part). This bit the corner clamp for real: an earlier revision's carriage
  had a retention hook hanging off its underside, meaning the FULL BODY of the part suddenly
  appeared above the hook's thin root a few layers into a natural tile-face-up print — a hard
  overhang baked into the feature itself, not something a slicer's auto-supports could cleanly
  reach (support material would have to thread through the same narrow snap-fit gap the hook
  needs to flex in) — see build-plate-corner-clamp revision 8 and the "prefer a fixed-screw"
  guidance below for how it was fixed. Printability isn't just "will this print" in the abstract —
  it's "will this print AS the part actually needs to sit to do its job."

A folder is one *mechanism*, not strictly one STL: when a design is inherently multiple parts
that only work as a set (e.g. a leveling foot that's a fixed leg + a riding carriage + a separate
cap installed after assembly - see `designs/build-plate-corner-clamp`), export each as its own
named STL/STEP/GLB triplet from the same `generate.py`, rather than forcing them into separate
top-level design folders or gluing them into one non-printable shape. Document each sub-part's
own qty/BOM/print notes in the shared README. Reach for separate folders (see the multi-part
cross-linking note above) when the parts are independently meaningful or reused elsewhere - not
when they're just inseparable pieces of one mechanism.

**Running it directly (not via `make`) — do not pass it to `freecadcmd` as a bare positional
argument.** Confirmed against FreeCAD 1.1.1: `freecadcmd` only auto-executes `.FCMacro`/`.FCStd`
files positionally — a plain `.py` file passed that way is silently never run (no error, no
output, no files written). Always go through `runpy`:

```bash
freecadcmd -c "import runpy, sys; sys.argv=['generate.py','--outdir','designs/<name>/outputs']; runpy.run_path('designs/<name>/generate.py', run_name='__main__')"
```

`make <name>` already does this — it's the Makefile's `$(DESIGNS)` recipe — so in practice just
use `make <name>`; the snippet above is for when you need to run a design's script standalone.

**GLB export note**: FreeCAD's glTF exporter lives in the Gui module and is unavailable under
headless `freecadcmd`. The standard pattern is: export STL natively via `Part`/`Mesh`, then
convert that STL to GLB with `trimesh` (pure Python, no FreeCAD Gui needed). `trimesh` is listed
in the root [`requirements.txt`](../requirements.txt). Note this may need installing into *two*
different Pythons: whatever `freecadcmd` embeds (needed inside `generate.py` itself — e.g. the
macOS Homebrew cask bundles its own conda-forge Python, separate from system `python3`) and
system `python3` (needed by `scripts/render_preview.py`, which `make` runs after `generate.py`).
`make install-freecad` installs `requirements.txt` into both when it can find FreeCAD's bundled
Python. Use `import trimesh` / `mesh.export(glb_path)` — see `export_glb()` in
`scripts/freecad_common.py` (shared by every `generate.py`, imported via a `sys.path` insert of
`../../scripts` relative to the design folder).

See the `freecad-python` skill for FreeCAD API patterns (object lifecycle, mesh/solid export,
batch-safe scripting) before writing or editing a `generate.py`.

**Turnable-knob pattern**: `build_knurled_cylinder()` (a fluted grip cylinder) in
`scripts/freecad_common.py` is shared by [designs/build-plate-corner-clamp](../designs/build-plate-corner-clamp/)
(vertical knob) and [designs/build-plate-notch-bracket](../designs/build-plate-notch-bracket/)
(horizontal knob — built along Z natively, then `shape.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)`
reorients the axis to X). Reuse it for any new design that needs a hand-turned knob.

**Prefer COTS hardware over a printed feature wherever a COTS part can do the same job more
reliably** — not just for turnable-knob retention (below), as a general default. Two proven
examples in this repo:

- **A fixed-screw-with-a-head instead of a boss/groove/snap-fit for capturing a part on a
  turnable knob.** Both build-plate designs went through several revisions of a boss+groove+hook
  mechanism (retention fingers hooking into an undercut groove on the knob) before dropping it
  entirely — see build-plate-corner-clamp revision 8 and build-plate-notch-bracket revision 4 for
  the full reasoning. Two concrete problems with that approach, not just theoretical concerns: an
  undercut snap-fit hanging off a part's underside makes it unprintable in its natural orientation
  (see the printability requirement above), and a boss narrow enough for a hook to reach around
  directly conflicts with a knob wide enough to grip comfortably by hand. The simpler, more robust
  alternative used now: a real screw WITH A HEAD (an SHCS, not a headless rod) has its head seat
  flush in a counterbore on whichever part is meant to stay fixed — a genuine bearing surface, not
  just loctite in a blind hole — and the part that's meant to float free (the carriage/slider) just
  gets a small plain clearance bore for the screw's tip, registration only, resting under gravity
  or pushed by direct face contact rather than captured by an undercut. `build_retainer_fingers()`
  (still in `scripts/freecad_common.py`) is kept as a utility for a future case where a snap-fit is
  genuinely the right call, but no current design uses it — read its docstring for the
  printability trade-offs before reaching for it again.
- **A COTS screw instead of a printed pin, captured by the surrounding assembly instead of a
  printed retention feature.** build-plate-notch-bracket's guide pin was originally printed
  integral to the flange (a plain plastic dowel); revision 5 replaced it with a real M3 SHCS,
  pushed through a plain clearance hole before the flange is bolted to its mounting surface, with
  its head simply trapped between the flange and that surface once assembled — no counterbore, no
  threadlocker, no printed feature at all beyond the hole itself. Worth considering whenever a
  design needs a fixed pin/dowel/anchor and there's an existing rigid surface nearby that assembly
  will bring into contact with it: the assembly sequence itself can be the retention feature.

**Verify a PREVIEW's placement numerically against the built document, not just its
math on paper — and don't trust a rotated shape's later `Placement =` to compose correctly.**
Two related, real bugs, both found the same way: opening the actual generated `.FCStd` and
checking one placed object's `Shape.BoundBox` against another's, not by re-deriving the transform
by hand and assuming it's right.

1. A leveling screw's reference geometry was anchored at the wrong point (an insert's deep end
   instead of the head's flush-seat point) and pointed the wrong way — the modeled shank plunged
   through the part it was supposed to be fixed to and out the *other* side, nowhere near the part
   it needed to reach. Preview-only (the real printable leg/knob/carriage geometry was
   unaffected), but a wrong preview actively misleads anyone using it to sanity-check the design.
2. Fixing #1 surfaced a second, sharper bug: `Part.Shape.rotate()`/`.translate()` store the
   transform as the shape's own `.Placement` property rather than baking it into raw vertex
   coordinates. Later assigning `Part::Feature.Placement = ...` on the document object doesn't
   COMPOSE with that — it fully REPLACES it, silently discarding whatever `.rotate()` did. The
   safe pattern: finish all positioning (`.rotate()` and `.translate()`, in that order if both are
   needed) directly on the raw `Part.Shape` *before* ever assigning it to `obj.Shape`, and don't
   also set `obj.Placement` afterward for that same object. If you must set `obj.Placement`
   separately, do it on a shape that was never `.rotate()`d/`.translate()`d directly (e.g. built
   fresh from `Part.makeBox`/`Part.makeCylinder` and only combined via `.fuse()`/`.cut()`, which do
   produce fresh, transform-free geometry).

See build-plate-corner-clamp's own revision 8 correction and build-plate-notch-bracket revision 5
(`build_flush_seated_screw` in that file's `generate.py`) for the fix pattern in practice.

**A thin, flexible cantilevered lip is a printable, parametric way to get a gentle grip feature**
without resorting to an undercut snap-fit. build-plate-notch-bracket's slider uses a pair of them
(top + bottom) to lightly clip onto a tile edge — see `SLIDER_CLIP_*` in that design's
`generate.py`. Keep the gripped dimension (the gap between the lips) as its own named parameter,
not just derived inline from whatever it's gripping, so it can be tuned directly against real
stock once measured, independent of any other assumption that dimension happens to be built from.

**Verify snap-fit/interference geometry numerically, not visually.** Several real bugs shipped in
this shared code before being caught — all invisible in rendered previews at this scale (a few
mm² of unintended overlap, or a knife-edge join, in a ~50mm part just doesn't show up) but obvious
once checked properly. Two checks matter, and they catch different bugs:

1. **Interference volume** — `shapeA.common(shapeB).Volume` (near-zero expected; a few mm³ is a
   legitimate small snap-fit preload, tens of mm³ means something is actually colliding).
2. **Solid connectivity** — `len(shape.Solids) == 1` after fusing all the pieces of what's supposed
   to be one printable part. A real bug here (found while reworking the retainer hook for
   `build-plate-corner-clamp` revision 7) had two boxes meant to form an L-profile only ever
   touching at a single point in cross-section — their footprints didn't actually overlap, so
   `Part.fuse()` silently left them as 2 separate solids. This passed every interference-volume
   check fine (the two pieces weren't colliding with anything) while still being a broken,
   unprintable joint. Check both, not just the first.

Before trusting a new knob/finger/groove geometry, build both halves in Python, translate them
into their assembled position, and check interference volume *and* solid count directly — see
`build_retainer_fingers`'s own docstring in `scripts/freecad_common.py` for the specific radii
that must clear and for how it builds genuine 3D overlap at every joint (never relying on two
shapes merely touching, even where that touching looks like a full shared face) — the fastest way
to avoid this class of bug in a new use is to reuse that pattern rather than gluing boxes together
by hand.

**Prefer one substantial retention feature over several thin ones**, if a single point of capture
is mechanically enough (e.g. a screw already controls axial position directly, and the retention
feature's only job is stopping accidental separation). `build_retainer_fingers(..., count=1, ...)`
places a single hook at a *flat-edge* direction on the caller's part, not a corner — a thin
appendage rooted at a square part's corner has the least surrounding material of anywhere on that
part's silhouette to fuse into, a real FDM weak point. Pass `arm_clearance` explicitly (it's a
required parameter, not derived) so the function can compute the target boss's true collar radius
for its internal connector geometry.

## Setup

```bash
make install-freecad
```

Detects the OS (`uname -s`) and installs FreeCAD + the Python build deps
(`requirements.txt`): Homebrew cask on macOS, `apt`/`dnf`/`pacman` on Linux. On Windows, do this
inside WSL2 (see "Platform support" below) — it's reported as Linux, same path applies.

**Ubuntu 24.04 (noble) and later: apt has no `freecad` candidate at all** — it was dropped from
the archive, not just moved behind a PPA/universe flag. `install-freecad`'s `apt` branch detects
this apt failure and falls back to `sudo snap install freecad`, symlinking the snap's CLI entry
point (`freecad.cmd`, not `freecadcmd`) to `/usr/local/bin/freecadcmd` so every other `freecadcmd`
reference in this repo (the Makefile's own build recipe, CI, docs) keeps working unmodified. CI
uses this same snap path directly (`.github/workflows/ci.yml`) since GitHub's `ubuntu-latest`
runners hit the identical apt gap.

## Platform support

Native targets are **macOS** and **Linux** — `install-freecad`, the rest of the Makefile, and CI
all assume a POSIX shell and GNU Make.

**Windows: use WSL2.** Install a WSL2 Ubuntu distro, then run everything (`make install-freecad`,
`make <name>`, etc.) inside it exactly as on Linux — no separate scripts to maintain, no
behavior drift from what CI runs. This is the only supported path; there is no native
`Makefile.win`/PowerShell build script, and none should be added — GNU Make isn't part of a
stock Windows install anyway (`make.exe` isn't there without WSL, Git Bash, or MSYS2), so a
"native Windows" build would mean maintaining a second, parallel build system just to avoid
installing WSL2, which is free, official, and already required for a first-class Docker/Linux
dev experience on Windows. If a contributor genuinely cannot use WSL2, they run `freecadcmd`
and `python3 scripts/render_preview.py` by hand per the commands documented in each design's
README — don't build tooling for this case unless it's actually blocking someone.

## Building a design

From repo root:

```bash
make <design-name>
```

Optionally override the output directory:

```bash
make <design-name> OUT=/path/to/output
```

`make all` (or plain `make`) builds every design in `designs/`. `make list` prints all
discoverable design names. The Makefile discovers designs automatically from
`designs/*/generate.py` — adding a new design folder with a `generate.py` is enough to make it
buildable; no Makefile edits needed. After `generate.py` runs, the Makefile also renders
`outputs/preview.png` from the first `.stl` it finds via `scripts/render_preview.py` — no
separate step needed.

## Opening a design in the FreeCAD GUI

```bash
make open-<design-name>
```

Builds the design (same as `make <design-name>`) then opens the most useful output in FreeCAD's
GUI: an `.FCStd` (assembly/preview document — full parts tree, richer than a single-shape STEP)
if the design produced one, else the `.step`. `$(OPEN_TARGETS)` is generated automatically from
`$(DESIGNS)`, same as the build targets — every design gets an `open-<name>` target with no
Makefile edits needed.

Tries `$(FREECAD_GUI)` (default `freecad`) on `PATH` first, then macOS's `open -a FreeCAD`, then
the Homebrew cask's known binary path directly — covers both a `PATH`-configured install and
a fresh `make install-freecad` where `freecad`/`freecadcmd` aren't on `PATH` yet.

## CI

CI (`.github/workflows/ci.yml`) builds only the designs whose files actually changed, by default —
it diffs the push/PR against its base commit and runs `make <name>` for each `designs/<name>/`
touched. A change to shared code (`Makefile`, `requirements.txt`, anything under `scripts/`)
invalidates that optimization and triggers a full `make all` instead, since those affect every
design. **`workflow_dispatch` (the "Run workflow" button in the Actions tab) is the manual
"build everything" trigger** — it always runs `make all` regardless of what changed, for
verifying the whole repo still builds (e.g. after a FreeCAD or Ubuntu runner update) without
needing to touch every design folder to force it. A design that fails to build fails CI. CI does
not diff or validate output geometry — it only verifies the script runs to completion and
produces the expected output files, for whichever designs were actually built on that run.

## Top-level README

`README.md` at repo root maintains an HTML `<table>` of every design (plain markdown tables
can't hold a multi-line cell cleanly) with one row per part:

- **Preview** — `outputs/preview.png`, linked to `designs/<name>/`
- **Part** — display name (linked) plus the literal folder name in a `` <code> `` span, so it's
  visible and selectable without opening the folder
- **Build** — the `make <name>` command in a `` <code> `` span. Note: GitHub sanitizes README
  HTML, so there is no working hover "copy" button inside a table cell (that only exists on
  standalone fenced code blocks) — `<code>` is the closest equivalent; the reader triple-clicks
  or double-clicks-and-drags to copy it.
- **Description** — one line.

Add a row there whenever a new design folder is added.

## Adding a new design — checklist

1. `mkdir -p designs/<name>/outputs`
2. Write `designs/<name>/generate.py` following the contract above.
3. Run `make <name>` locally, confirm it produces STL/GLB in `outputs/`.
4. Write `designs/<name>/README.md` covering purpose, spec, parameters, usage, integration/BOM,
   with the outputs embedded.
5. Add a row for the design in the root `README.md`.
6. Commit the script, README, and generated outputs (outputs are checked into git so they render
   on GitHub — they are not build artifacts to gitignore).
