# Parametric Bird

<img src="outputs/preview.png" alt="parametric-bird posed preview" width="400" />

## Purpose

A deliberately **very simple** decorative spread-wing bird, inspired by
balsa-and-wire ornithopter skeletons: every piece is flat stock, and the bird is
a few flat plaques that **slot together** (plus a drop of glue).

It is an ornament / learning model, not a mechanism — nothing moves. The point is
a clean parametric silhouette that prints without supports and assembles by
plugging wing tongues into connector slits.

## Two knobs

Everything is driven by **two master parameters** at the top of `generate.py`:

| Param | Meaning | Default |
|---|---|---|
| `WING_LENGTH` | wing span, root edge to tip (mm) — sets the whole model's size | 300.0 |
| `THICKNESS` | plaque / tongue / body-slab thickness for **every** part (mm) | 3.2 |

`WING_LENGTH` derives internal `WING_SCALE`/`BODY_SCALE`/`CONN_SCALE` (base wing
span is 100 mm at scale 1.0; body & connector keep a fixed 0.73 : 1 ratio to the
wing). `WING_LENGTH 300` → ~320 × 108 mm wing, all pieces fit one **350 × 350
Voron plate**. `WING_LENGTH ≈ 95` → the original palm-size bird. Clearances
(`*_FIT`) stay absolute — they do not scale.

## Body pose

Two body versions are **always exported**, so you can print either:

| Output | Pose |
|---|---|
| `bird_body` | **level** — arrow flying straight |
| `bird_body_diving` | **head down** — neck + head + beak swung down `DIVE_ANGLE` (38°) about the neck root, aiming at food on the floor |

Everything aft of the neck root (body, tail, the dorsal flat the connector rides
on) is identical in both, so the connector / wing assembly is unchanged.
`BODY_POSE` (`"level"` / `"diving"`) only picks which body the `bird.*` preview
shows.

## Spec

| Piece | Qty | Notes |
|---|---|---|
| `bird_body` *or* `bird_body_diving` | 1 | narrow arrow-ish side profile — slim shaft, long stretched oval head + pointed beak, fletched tail — + rib lattice + eye hole. Back flattened into a straight dorsal edge `BACK_FLAT_LEN` long. |
| `bird_wing` | 2 | swept plaque, **rounded-square grid pattern** (cells follow the planform so each row is roughly parallel to the nearer edge), **root tongue** that plugs into a connector arm slit. **Print the second one mirrored.** |
| `bird_connector` | 1 | **slim saddle** — the core is now just the two straddle legs (its width no longer scales up faster than the slit it holds), and each arm is a thin plate whose thickness tracks the wing slit. ~¼ the volume of the old block. A through slit in the bottom straddles the flat back; two arms rise at `ARM_ELEV`, each with a through slit for one wing tongue. |

- **Parametric fits** (absolute clearances — they do **not** scale):
  | joint | slot width | plaque | clearance |
  |---|---|---|---|
  | wing tongue ↔ arm slit | `THICKNESS + SLIT_FIT` = 3.6 | `THICKNESS` = 3.2 | 0.4 (0.2/side) |
  | body back ↔ bottom slit | `THICKNESS + STRADDLE_FIT` = 3.6 | `THICKNESS` = 3.2 | 0.4 (0.2/side) |

  For a snug press fit drop `SLIT_FIT` / `STRADDLE_FIT`.
- **Wing dihedral** in the assembled bird = the connector's `ARM_ELEV` (18°).
- Every printable piece is one connected solid (asserted in `generate.py`).
- `bird.*` / `bird.FCStd` are an **illustrative pose only** — not a printable body.

### Print orientation (all exported ready to print — no slicer rotation, no supports)

| Piece | On the bed |
|---|---|
| `bird_body` / `bird_body_diving` / `bird_wing` | as exported — largest face flat (z = 0) |
| `bird_connector` | as exported — `generate.py` rolls it 90° so the spine axis is vertical and a full profile face sits on the bed; every slit is then a vertical channel — no overhang, no bridge |

## Parameters

All in `generate.py` near the top. Below the two master knobs, sizes are written
`base × *_SCALE` — the **Base** column is the value at `WING_LENGTH` 100.

### Wing
| Name | Meaning | Base / value |
|---|---|---|
| `WING_ROOT_CHORD` | depth at the body | `33 × WING_SCALE` |
| `WING_TIP_CHORD` | depth at the tip | `5 × WING_SCALE` |
| `WING_TIP_LE_DROP` | tip leading-edge set-back | `14 × WING_SCALE` |
| `WING_LE_BOW` | forward bow of the leading edge | `10 × WING_SCALE` |
| `WING_TE_BOW` | trailing-edge lift, fraction of root chord | 0.22 |
| `WING_BORDER` | solid rim around the pattern | `0.035 × WING_ROOT_CHORD` |
| `WING_EDGE_R` | outer-edge rounding (auto-skipped if too many edges) | `0.5 × WING_SCALE` |
| `GRID_COLS` / `GRID_ROWS` | pattern cells along span / chord | 8 / 4 |
| `GRID_FILL` | hole size as a fraction of cell pitch (build prints actual open %) | 0.90 |
| `GRID_CORNER` | hole corner rounding radius | `0.8 × WING_SCALE` |
| `GRID_MARGIN_SPAN` / `GRID_MARGIN_CHORD` | solid margin at root+tip / LE+TE | 0.08 / 0.16 |
| `TONGUE_DEPTH` | how far the tongue enters the arm slit | `9 × CONN_SCALE` |
| `TONGUE_WIDTH` | tongue size along the root edge | `0.85 × CONN_SPINE` |
| `TONGUE_CHORD_FRAC` | tongue position along the root chord | 0.5 |

### Body
| Name | Meaning | Base / value |
|---|---|---|
| `BODY_LENGTH` | body-ellipse span (real beak-to-tail is longer) | `106 × BODY_SCALE` |
| `BODY_HEIGHT` | breast to back (small = narrow shaft) | `20 × BODY_SCALE` |
| `BODY_BORDER` | solid rim around the lattice | `0.09 × BODY_HEIGHT` |
| `HEAD_LENGTH` / `HEAD_DIA` | head oval, along / across the spine | `34` / `13 × BODY_SCALE` |
| `HEAD_REACH` / `HEAD_DROP` | head-centre X (frac of `a`) / Y (frac of `b`) | 0.98 / 0.35 |
| `NECK_TAPER` | neck-root position along the head | 0.32 |
| `DIVE_ANGLE` | head-down swing for `bird_body_diving` | 38.0 |
| `BEAK_LENGTH` / `BEAK_ROOT` | beak projection / height at the head | `18` / `6 × BODY_SCALE` |
| `TAIL_LENGTH` / `TAIL_SPREAD` | tail projection / tip height (fletching) | `34` / `22 × BODY_SCALE` |
| `EYE_DIA` | eye hole diameter | `2.4 × BODY_SCALE` |
| `BODY_RIB_WIDTH` | lattice vein thickness | `1.7 × BODY_SCALE` |
| `BACK_FLAT_LEN` | length of the straight dorsal edge | `40 × BODY_SCALE` |

### Connector (across = Y, up = Z, spine = X)
| Name | Meaning | Base / value |
|---|---|---|
| `CONN_SPINE` | extent along the spine (= arm / slit width) | `12 × CONN_SCALE` |
| `STRADDLE_DEPTH` | how far the bottom slit rises from z = 0 | `6 × CONN_SCALE` |
| `SADDLE_HALF` | half core width — now just the straddle leg | `(THICKNESS + STRADDLE_FIT)/2 + 4.5` |
| `CORE_H` | core height | `STRADDLE_DEPTH + 6` |
| `ARM_ELEV` | arm angle above horizontal = wing dihedral | 18.0 |
| `ARM_LEN` | arm length | `17 × CONN_SCALE` |
| `ARM_TZ` | arm plate thickness — tracks the slit, not scaled | `THICKNESS + SLIT_FIT + 3.4` |
| `ARM_ROOT_Z` | Z where the arm leaves the core side | `STRADDLE_DEPTH × 0.55` |
| `SLIT_DEPTH` | arm slit depth along the arm | `11 × CONN_SCALE` |
| `CORE_FILLET` | rounding on the connector core edges | `1.0 × CONN_SCALE` |
| `STRADDLE_FIT` / `SLIT_FIT` | bottom / arm slit clearance (absolute) | 0.4 / 0.4 |

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

1. Print **1 body** (`bird_body` level, or `bird_body_diving` head-down),
   **2 × `bird_wing`** (slice the second one mirrored), **1 × `bird_connector`**.
   All export ready to print — drop them on the plate, no rotation, no supports.
   At `WING_LENGTH` 300 they fit one 350 × 350 Voron bed. 3+ perimeters makes the
   thin grid webs solid.
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
| body (printed) | 1 | `bird_body` or `bird_body_diving` |
| `bird_wing` (printed) | 2 | one mirrored |
| `bird_connector` (printed) | 1 | |
| Cyanoacrylate or plastic cement | — | slot + slit joints |
| Stand wire (~1.5–2 mm steel) | opt. | if displaying upright |

## Outputs

<a href="outputs/bird_body.stl">bird_body.stl</a> ·
<a href="outputs/bird_body.glb">.glb</a> ·
<a href="outputs/bird_body.step">.step</a>

<a href="outputs/bird_body_diving.stl">bird_body_diving.stl</a> ·
<a href="outputs/bird_body_diving.glb">.glb</a> ·
<a href="outputs/bird_body_diving.step">.step</a>

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
