# samsung-c34-clip

<img src="outputs/preview.png" alt="samsung-c34-clip posed preview" width="420" />

*(grey block = the monitor's top edge — reference only, not a printed part)*

**Part of the `screen-bird-*` set** — a mount for a monitor whose top edge is
too thin, too rounded and too slick to clip onto. Measured on a **Samsung
C34H89x**: a ~14.5 mm deep rounded bullnose rail with the body receding
immediately behind it — nothing to clamp, no square edge to hook.

For ordinary bezels use the fixed clip ([screen-bird-perch](../screen-bird-perch/)
etc.) or the turntable ([screen-bird-clip-swivel](../screen-bird-clip-swivel/));
the bird / puck are shared and interchangeable.

## Purpose

It does **not** clamp and uses **no adhesive**. It balances, and it prints as
**one flat piece** with **two living hinges** — no pin, no assembly:

| Piece | Qty | Notes |
|---|---|---|
| `samsung-c34-clip_clip` | 1 | one flat print: `[ back tail 50 ]—[ web ]—[ saddle + cup ]—[ tiny web ]—[ front flap 12 ]`, all coplanar. V-scores mark both fold lines. |
| `samsung-c34-clip_puck` | 1 | the usual flat slotted disc (`build_swivel_puck`) — the bird foot tab glues into its top slot; it spins in the saddle cup. |

**After printing, fold both tails down:**

- the **back tail ~100°** → drapes down the monitor back. Counterweight —
  stops the (rear-biased) bird load tipping the saddle, and its bulk behind
  the rear edge blocks the saddle sliding backward.
- the **front flap ~110°** → folds over the rail's rounded front edge and
  **stops the saddle sliding backward off the rail** (the thing you asked
  for). Short, so it barely covers the screen.

Between them the saddle is trapped on the rail — at **any spot along the top
edge**, on **any top thickness**. Once folded, the webs stay compliant enough
that each tail still finds its own angle against the monitor.

## Spec

- **Fit**: the one number to measure is the top-edge front-to-back depth
  (`RAIL_DEPTH`, default 14.5) — it *is* the front fold line. The cup sits
  entirely behind it; the back fold is just behind the cup.
- **Living hinges**: `web_t` = 1.0 mm bottom-aligned strips, `web_span` = 5 mm
  (back) / `front_web_span` = 3 mm (front), each with a `web_score` = 0.5 mm
  V-groove in the top → ~0.5 mm at the fold. Fold each **once, slowly**; warm
  with a hair-dryer if it's stiff PLA. **PETG folds better than PLA** here.
- **Balance**: bird + cup ≈ 15 g, centred ~2 mm behind the rear edge (so the
  load already leans back — the front flap holds the front down). The back
  tail is ≈ 7 g of PLA with a coin pocket (≈ 2.6 × 20 × 22 mm, opens toward
  the monitor once folded) — add coins / an M8–M10 nut until the saddle sits
  firmly. Thin foam pads on the flat undersides for grip / protection.
- **Bird ↔ puck**: unchanged — foot tab into the puck's through-slot + glue.
  Any `screen-bird-*` bird fits.
- Both printable pieces are one solid (`len(shape.Solids) == 1`, asserted).
- `samsung-c34-clip.*` / `.FCStd` are a posed preview (both tails folded) —
  not a printable body.

### Print orientation — flat, cup-up, no supports (PLA or PETG)

Lay it on the bed as exported and slice. Overhang scan of the STL: the clip
has only ~36 mm² of sub-millimetre facets right at the two score lines (about
to be creased anyway) — no support needed; the puck is **0 mm²**. Webs are
bottom-aligned strips, scores are top-face grooves, the cup opens up, the
coin pocket opens to an end.

> Slicer tip for the living hinges: print the web regions with **no top/bottom
> layer gap** and, if your slicer supports it, extra flow — you want the 2–3
> layers there fully fused.

## Parameters

`generate.py` surfaces the two you'll touch:

| Name | Meaning | Default |
|---|---|---|
| `RAIL_DEPTH` | monitor top-edge front-to-back (measure this) — the front fold line | 14.5 |
| `TAIL_LEN` | how far the back tail drapes down the back | 50.0 |

Everything else is the `C34` dict in
[`scripts/freecad_common.py`](../../scripts/freecad_common.py): `plate_t` 4,
`plate_back_extra` 2, `tail_w` 24, `tail_t` 6, `front_flap_len` 12,
`front_flap_w` 18, `web_t` 1.0, `web_span` 5, `front_web_span` 3,
`web_score` 0.5, `coin_pocket` (2.6, 20, 22). Cup / puck geometry is
`SCREEN_SWIVEL` (shared with the swivel clip).

## How to use

From the repo root:

```bash
make samsung-c34-clip
```

Needs FreeCAD (`make install-freecad` if missing). Standalone:

```bash
freecadcmd -c "import runpy, sys; sys.argv=['generate.py','--outdir','designs/samsung-c34-clip/outputs']; runpy.run_path('designs/samsung-c34-clip/generate.py', run_name='__main__')"
```

GUI preview: `make open-samsung-c34-clip`.

## Integration / use

1. **Print** `..._clip` and `..._puck` — both flat, cup-up, no supports. PETG
   preferred for the clip (the living hinges); PLA works if you fold it gently.
2. **Fold** the back tail down ~100° and the front flap down ~110°, each once,
   along its V-score. They should stay folded; gravity does the rest.
3. **Bird → puck**: foot tab into the puck's top slot + a drop of glue.
4. **On the monitor**: set the saddle over the top edge anywhere you like —
   the front flap hangs over the front edge, the back tail drapes down the
   back. Drop the puck (with bird) into the cup.
5. **Balance**: if the saddle rocks or creeps forward, add coins to the tail
   pocket and/or stick foam pads on the saddle underside and the tail tip.

### BOM

| Item | Qty | Notes |
|---|---|---|
| `samsung-c34-clip_clip` / `_puck` (printed) | 1 each | this design |
| any `screen-bird-*` bird (printed) | 1 | unchanged |
| Cyanoacrylate / plastic cement | — | puck slot |
| Coins or an M8–M10 nut | a few | tail counterweight, as needed |
| Self-adhesive foam/felt pads, 1–2 mm | 2–3 | saddle underside + tail tip |

## Outputs

<a href="outputs/samsung-c34-clip_clip.stl">samsung-c34-clip_clip.stl</a> ·
<a href="outputs/samsung-c34-clip_clip.glb">.glb</a> ·
<a href="outputs/samsung-c34-clip_clip.step">.step</a>

<a href="outputs/samsung-c34-clip_puck.stl">samsung-c34-clip_puck.stl</a> ·
<a href="outputs/samsung-c34-clip_puck.glb">.glb</a> ·
<a href="outputs/samsung-c34-clip_puck.step">.step</a>

Posed preview (not printable):
<a href="outputs/samsung-c34-clip.stl">samsung-c34-clip.stl</a> ·
<a href="outputs/samsung-c34-clip.glb">.glb</a> ·
<a href="outputs/samsung-c34-clip.FCStd">.FCStd</a>
