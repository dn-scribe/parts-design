"""
screen-bird-peek - a curious little bird craning its head down over the top
edge of a monitor, as if peering at the screen.

One of the `screen-bird-*` family (see docs/agents-instructions.md and
scripts/freecad_common.py). Every pose in the family is the SAME two-part
mechanism:

    <name>_bird   x1   a flat side-profile silhouette, ~4 mm stock, with a
                       wing cut-out + a vent for weight, ending in a
                       rectangular foot tab at the belly.
    <name>_clip   x1   the shared flexible C-clip (build_screen_clip) that
                       grips a screen's top bezel and carries a through-slot
                       socket the foot tab drops into.

This folder is the PEEK pose: body leaning forward, an S-curved neck dropping
the head low and forward, beak angled down, tail cocked up as a counterweight.

Colour: single colour = just the two objects. Multi-colour with no extra
parts and one plate = give the bird and the clip different filaments (they
are separate objects), and/or paint the beak / eye ring / wing edge in the
slicer. The bird prints flat, so a filament swap by layer tints the front vs
back face, not head vs body.

Everything exports ready to print - no supports, no slicer rotation:
    <name>_bird   laid flat, largest face on z = 0.
    <name>_clip   stood on a profile end face (one clean extrusion).
The <name>.* / .FCStd outputs are a posed preview (bird on the clip on a grey
slab standing in for the screen edge) - not a printable body.

Build:  make screen-bird-peek
"""

import math
import os
import sys

import FreeCAD as App

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from freecad_common import (build_foot_tab, build_screen_clip, emit_screen_bird,
                            parse_outdir, xz_face, SCREEN_CLIP_FOOT)

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------
SCALE = 0.85                    # multiplies every silhouette length below (not the foot/clip)
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]
EYE_DIA = 3.0

BEZEL_NOMINAL = 9.0
CLIP_PRELOAD = 0.8
CLIP_WIDTH = 18.0

# Lightening cut-outs, pre-SCALE frame: (cx, cz, a, b, angle_deg) rotated ellipses.
LIGHTEN = [(-3, 30, 11.5, 4.2, -24), (-6, 16, 3.2, 3.2, 0)]


def _circle(cx, cy, r, n=48, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _ellipse_rot(cx, cz, a, b, deg, n=56):
    t = math.radians(deg)
    ct, st = math.cos(t), math.sin(t)
    return [(cx + a * math.cos(2 * math.pi * i / n) * ct - b * math.sin(2 * math.pi * i / n) * st,
             cz + a * math.cos(2 * math.pi * i / n) * st + b * math.sin(2 * math.pi * i / n) * ct)
            for i in range(n)]


def _s(pts):
    return [(x * SCALE, z * SCALE) for x, z in pts]


def _solid(pts, scale=True):
    """A silhouette polygon -> a thin solid plaque. Fusing thin SOLIDS is far
    more robust in OCC than merging coplanar faces."""
    p = _s(pts) if scale else pts
    s = xz_face(p).extrude(App.Vector(0, BIRD_THICKNESS, 0))
    s.translate(App.Vector(0, -BIRD_THICKNESS / 2.0, 0))
    return s


def _cut(pts, scale=True, pad=2.0):
    p = _s(pts) if scale else pts
    s = xz_face(p).extrude(App.Vector(0, BIRD_THICKNESS + 2 * pad, 0))
    s.translate(App.Vector(0, -BIRD_THICKNESS / 2.0 - pad, 0))
    return s


def build_bird():
    # upright frame: +X = the way the bird faces, +Z up. It leans forward.
    # `belly` (absolute, unscaled) tapers the lower body to a flat seat at z = 1
    # for the foot tab - the bird then appears to grip the clip directly.
    parts = [
        _solid([(-13, 26), (12, 26), (8, 1), (-11, 1)], scale=False),   # belly / seat
        _solid(_ellipse_rot(-2, 28, 20, 16.5, -22, 72)),               # body (leaning)
        _solid([(4, 42), (14, 36), (21, 22), (24, 12), (17, 12),
                (11, 22), (2, 33)]),                                    # S-neck
        _solid(_circle(23, 12.5, 8.5, 52)),                             # head (low, forward)
        _solid([(31, 1.5), (23.5, 10), (18.5, 6.5)]),                   # beak (angled down)
        _solid([(-14, 33), (-38, 53), (-33, 44), (-30, 40), (-15, 27)]),  # cocked tail
    ]
    bird = parts[0].fuse(parts[1:]).removeSplitter()
    assert len(bird.Solids) == 1, "peek silhouette is %d solids" % len(bird.Solids)

    cuts = [_cut(_ellipse_rot(cx, cz, a, b, d)) for cx, cz, a, b, d in LIGHTEN]
    cuts.append(_cut(_circle(24, 14, EYE_DIA / 2.0 / SCALE, 24)))
    bird = bird.cut(cuts[0].fuse(cuts[1:]))

    bird = bird.fuse(build_foot_tab(BIRD_THICKNESS, CLIP_WIDTH)).removeSplitter()
    assert len(bird.Solids) == 1, "peek bird is %d solids" % len(bird.Solids)
    return bird


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    clip = build_screen_clip(bezel_nominal=BEZEL_NOMINAL, preload=CLIP_PRELOAD,
                             width=CLIP_WIDTH, foot_thickness=BIRD_THICKNESS)
    emit_screen_bird(out_dir, "screen-bird-peek", build_bird(), BIRD_THICKNESS, clip=clip)


if __name__ == "__main__":
    main()
