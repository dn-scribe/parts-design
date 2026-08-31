# Parametric Bird

<img src="outputs/preview.png" alt="parametric-bird posed preview" width="400" />

## Purpose

A deliberately **very simple** decorative spread-wing bird, inspired by
balsa-and-wire ornithopter skeletons: every piece is flat stock, and the bird is
four flat plaques that **slot together** (plus a drop of glue).

It is an ornament / learning model, not a mechanism — nothing moves. The point is
a clean parametric silhouette that prints without supports and assembles by
plugging wing tongues into connector slits.

**Size:** the three `*_SCALE` factors at the top of `generate.py` set the overall
size. As shipped (`WING_SCALE` 3.0, `BODY_SCALE` 2.2, `CONN_SCALE` 2.2) a wing is
~320 × 108 mm and **all four pieces fit on one 350 × 350 Voron plate** (2 × wing +
body + connector). The build prints each part's exported footprint so you can
confirm the layout. Set every scale to `1.0` for the original palm-size bird.

## Spec

| Piece | Qty | Notes |
|---|---|---|
| `bird_body` | 1 | narrow arrow-like side profile — slim shaft, long stretched oval head + pointed beak up front, fletched tail — + rib lattice + eye hole. Its **back is flattened** into a straight dorsal edge `BACK_FLAT_LEN` long. |
| `bird_wing` | 2 | swept plaque, **rounded-square grid pattern** (cells follow the planform so each row is roughly parallel to the nearer edge), **root tongue** that plugs into a connector arm slit. **Print the second one mirrored.** |
| `bird_connector` | 1 | **saddle** with a rounded (filleted) core. A through slit in the bottom straddles the flat back; two arms rise at `ARM_ELEV` — one per side — each with a through slit sized to the wing tongue. The bottom slit is perpendicular (in cross-section) to the arm slits. Both wings hang off this one connector, so they share one station (X = const, beside the head). |

- **Parametric fits** (absolute clearances — they do **not** scale):
  | joint | slot width | plaque | clearance |
  |---|---|---|---|
  | wing tongue ↔ arm slit | `WING_THICKNESS + SLIT_FIT` = 3.6 | `WING_THICKNESS` = 3.2 | 0.4 (0.2/side) |
  | body back ↔ bottom slit | `BODY_THICKNESS + STRADDLE_FIT` = 4.3 | `BODY_THICKNESS` = 3.8 | 0.5 (0.25/side) |

  Change a plaque thickness and the matching slot tracks it. For a snug press
  fit drop `SLIT_FIT` / `STRADDLE_FIT`.
- **Wing dihedral** in the assembled bird = the connector's `ARM_ELEV` (18°).
- Every printable piece is one connected solid (asserted in `generate.py`:
  `len(shape.Solids) == 1`).
- `bird.*` / `bird.FCStd` are an **illustrative pose only** — not a printable body.

### Print orientation (all exported ready to print — no slicer rotation, no supports)

| Piece | On the bed | Overhang check |
|---|---|---|
| `bird_body` | as exported — largest face flat (z = 0) | none — flat plaque |
| `bird_wing` | as exported — largest face flat (z = 0) | none — flat plaque; tongue is in-plane |
| `bird_connector` | as exported — `generate.py` rolls it 90° so the spine axis is vertical and a full profile face sits on the bed | the whole part is one profile extruded along the spine, so every slit is a vertical channel — no overhang, no bridge |

## Parameters

All in `generate.py` near the top, mm / degrees.

### Scale
| Name | Meaning | Default |
|---|---|---|
| `WING_SCALE` | multiplies every wing length (`1.0` = original ~95 mm span) | 3.0 |
| `BODY_SCALE` | multiplies every body length | 2.2 |
| `CONN_SCALE` | multiplies every connector length | 2.2 |

Lengths below are written `base × *_SCALE` in the file; the **Base** column is the
`1.0`-scale value. Thicknesses, clearances (`*_FIT`), angles, fractions and counts
are **not** scaled.

### Wing
| Name | Meaning | Base |
|---|---|---|
| `WING_SPAN` | root edge to tip (`×WING_SCALE` → ~300) | 100.0 |
| `WING_ROOT_CHORD` | depth at the body (`×WING_SCALE` → ~100) | 33.0 |
| `WING_TIP_CHORD` | depth at the tip | 5.0 |
| `WING_TIP_LE_DROP` | tip leading-edge set-back | 14.0 |
| `WING_LE_BOW` | forward bow of the leading edge | 10.0 |
| `WING_TE_BOW` | trailing-edge lift, fraction of root chord | 0.22 |
| `WING_THICKNESS` | plaque + tongue thickness (not scaled) | 3.2 |
| `WING_BORDER` | solid rim around the pattern (not scaled) | 3.5 |
| `WING_EDGE_R` | rounding on the wing / body outer edges (auto-skipped if too many edges) | 1.5 |
| `GRID_COLS` | pattern cells along the span | 8 |
| `GRID_ROWS` | pattern cells across the chord | 4 |
| `GRID_FILL` | hole size as a fraction of the local cell pitch (build prints the actual open %) | 0.90 |
| `GRID_CORNER` | hole corner rounding radius (not scaled) | 2.5 |
| `GRID_MARGIN_SPAN` | span fraction kept solid at root and tip | 0.08 |
| `GRID_MARGIN_CHORD` | chord fraction kept solid at LE and TE | 0.16 |
| `TONGUE_DEPTH` | how far the tongue enters the arm slit (`×CONN_SCALE`) | 9.0 |
| `TONGUE_WIDTH` | tongue size along the root edge (≤ `CONN_SPINE`, not scaled) | 26.0 |
| `TONGUE_CHORD_FRAC` | tongue position along the root chord | 0.5 |

### Body — "arrow" read: narrow shaft, long stretched head/beak, fletched tail (`×BODY_SCALE` unless noted)
| Name | Meaning | Base |
|---|---|---|
| `BODY_LENGTH` | body-ellipse span (real beak-to-tail is longer) | 106.0 |
| `BODY_HEIGHT` | breast to back (small = narrow shaft) | 20.0 |
| `BODY_THICKNESS` | plaque thickness, bottom slit tracks this (not scaled) | 3.8 |
| `BODY_BORDER` | solid rim around the lattice (not scaled) | 4.0 |
| `HEAD_LENGTH` | head stretched along the spine (an oval) | 34.0 |
| `HEAD_DIA` | head depth across the spine | 13.0 |
| `HEAD_REACH` | head-centre X as a fraction of body semi-axis `a` (not scaled) | 0.98 |
| `HEAD_DROP` | head-centre Y as a fraction of `b` (not scaled) | 0.35 |
| `NECK_TAPER` | neck-root position along the head (not scaled) | 0.32 |
| `BEAK_LENGTH` | beak projection past the head | 18.0 |
| `BEAK_ROOT` | beak height at the head | 6.0 |
| `TAIL_LENGTH` | tail projection past the body | 34.0 |
| `TAIL_SPREAD` | tail height at its tip (the fletching) | 22.0 |
| `EYE_DIA` | eye hole diameter | 2.4 |
| `BODY_RIB_WIDTH` | lattice vein thickness | 1.7 |
| `BACK_FLAT_LEN` | length of the straight dorsal edge | 40.0 |

### Connector (across = Y, up = Z, spine = X; `×CONN_SCALE` unless noted)
| Name | Meaning | Base |
|---|---|---|
| `CONN_SPINE` | extent along the bird's spine | 12.0 |
| `SADDLE_HALF` | half-width of the core in Y | 11.0 |
| `CORE_H` | core height in Z | 13.0 |
| `STRADDLE_FIT` | added to `BODY_THICKNESS` for the bottom slit (not scaled) | 0.5 |
| `STRADDLE_DEPTH` | how far the bottom slit rises from z = 0 | 8.0 |
| `ARM_ELEV` | arm angle above horizontal = wing dihedral | 18.0 |
| `ARM_LEN` | arm length | 17.0 |
| `ARM_TZ` | arm plate thickness (> slit width) | 6.0 |
| `ARM_ROOT_Z` | Z where the arm leaves the core side | 5.0 |
| `SLIT_FIT` | added to `WING_THICKNESS` for the arm slit (not scaled) | 0.4 |
| `SLIT_DEPTH` | arm slit depth along the arm | 11.0 |
| `CORE_FILLET` | rounding on the connector core edges | 1.4 |

`ARM_ELEV` (18°, the wing dihedral) is an angle — not scaled.

## How to use

From the repo root:

```bash
make parametric-bird
```

Needs FreeCAD (`make install-freecad` if `freecadcmd` isn't found). Standalone
(see `docs/agents-instructions.md` for the `runpy` wrapper):

```bash
freecadcmd -c "import runpy, sys; sys.argv=['generate.py','--outdir','designs/parametric-bird/outputs']; runpy.run_path('designs/parametric-bird/generate.py', run_name='__main__')"
```

Open the posed preview in the FreeCAD GUI:

```bash
make open-parametric-bird
```

## Integration / use

1. Print **1 × `bird_body`**, **2 × `bird_wing`** (slice the second one mirrored),
   **1 × `bird_connector`**. All four export ready to print — drop them straight
   on the plate, no rotation, no supports. They fit together on one 350 × 350
   Voron bed (2 wings ~320 × 108 stacked, body along one edge, connector in a
   corner). 3+ perimeters makes the thin grid webs solid.
2. Push the connector down onto the flat back just behind the head. The bottom
   slit grips the body slab — a dab of glue in it locks it.
3. Plug the right wing's tongue into the connector's right-hand (+Y) arm slit,
   the left wing's tongue into the left-hand (−Y) arm slit (the wings are mirror
   images). Glue in each slit. Both wings end up at the same station.
4. The arm angle gives the wings their dihedral. Optional: a stiff wire through
   the body (drill the belly) for a display stand.

### BOM

| Item | Qty | Notes |
|---|---|---|
| `bird_body` (printed) | 1 | this design |
| `bird_wing` (printed) | 2 | this design — one mirrored |
| `bird_connector` (printed) | 1 | this design |
| Cyanoacrylate or plastic cement | — | slot + slit joints |
| Stand wire (~1.5–2 mm steel) | opt. | if displaying upright |

## Outputs

<a href="outputs/bird_body.stl">bird_body.stl</a> ·
<a href="outputs/bird_body.glb">.glb</a> ·
<a href="outputs/bird_body.step">.step</a>

<a href="outputs/bird_wing.stl">bird_wing.stl</a> ·
<a href="outputs/bird_wing.glb">.glb</a> ·
<a href="outputs/bird_wing.step">.step</a>

<a href="outputs/bird_connector.stl">bird_connector.stl</a> ·
<a href="outputs/bird_connector.glb">.glb</a> ·
<a href="outputs/bird_connector.step">.step</a>

Posed whole-bird preview (not printable):
<a href="outputs/bird.stl">bird.stl</a> ·
<a href="outputs/bird.glb">bird.glb</a> ·
<a href="outputs/bird.FCStd">bird.FCStd</a>
