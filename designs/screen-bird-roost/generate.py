"""
screen-bird-roost - a plump, sleeping bird, head tucked into its shoulders,
roosting on the top edge of a monitor.

One of the `screen-bird-*` family (see docs/agents-instructions.md and
scripts/freecad_common.py). Every pose in the family is the SAME two-part
mechanism:

    <name>_bird   x1   a flat side-profile silhouette, ~4 mm stock, ending in
                       a rectangular foot tab at the belly.
    <name>_clip   x1   the shared flexible C-clip (build_screen_clip) that
                       grips a screen's top bezel and carries a through-slot
                       socket the foot tab drops into.

This folder is the ROOST pose: a near-round puffed body, the head sunk back
and down into the back feathers with only the beak tip showing, a short tail,
and a closed (slot) eye. It is the most compact pose in the set - the fastest,
lightest print.

Colour: single colour = just the two objects. Multi-colour with no extra
parts and one plate = give the bird and the clip different filaments (they
are separate objects), and/or paint the beak / eye / folded-wing crescent in
the slicer. The bird prints flat, so a filament swap by layer tints the front
vs back face.

Everything exports ready to print - no supports, no slicer rotation:
    <name>_bird   laid flat, largest face on z = 0.
    <name>_clip   stood on a profile end face (one clean extrusion).
The <name>.* / .FCStd outputs are a posed preview - not a printable body.

Build:  make screen-bird-roost
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
SCALE = 0.9
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]

BEZEL_NOMINAL = 9.0
CLIP_PRELOAD = 0.8
CLIP_WIDTH = 18.0


def _circle(cx, cy, r, n=64, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


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
    # upright frame: beak points -X (tucked back over the shoulder), +Z up.
    # `belly` (absolute, unscaled) is the flat seat at z = 1 for the foot tab.
    parts = [
        _solid([(-13, 26), (13, 26), (9, 1), (-11, 1)], scale=False),   # belly / seat
        _solid(_circle(1, 24, 21, 80)),                                # puffed body
        _solid(_circle(-7, 35, 12.5, 64)),                             # puffed nape
        _solid(_circle(-9, 30, 9.5, 56)),                              # tucked head
        _solid([(-24, 30), (-15, 32.5), (-15, 27.5)]),                 # beak tip peeking out
        _solid([(14, 14), (33, 6), (31, -1), (12, 6)]),                # short down tail
    ]
    bird = parts[0].fuse(parts[1:]).removeSplitter()
    assert len(bird.Solids) == 1, "roost silhouette is %d solids" % len(bird.Solids)

    # closed (sleeping) eye = a short horizontal slot low on the tucked head;
    # folded-wing crescent (one disc minus an offset disc) set into the flank.
    eye = _cut([(-15, 29.5), (-9.5, 29.5), (-9.5, 28.2), (-15, 28.2)])
    crescent = _cut(_circle(6, 21, 7.0, 48)).cut(_cut(_circle(10, 22.5, 7.0, 48)))
    vent = _cut(_circle(-4, 14, 2.6, 28))
    bird = bird.cut(eye.fuse([crescent, vent]))

    bird = bird.fuse(build_foot_tab(BIRD_THICKNESS, CLIP_WIDTH)).removeSplitter()
    assert len(bird.Solids) == 1, "roost bird is %d solids" % len(bird.Solids)
    return bird


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    clip = build_screen_clip(bezel_nominal=BEZEL_NOMINAL, preload=CLIP_PRELOAD,
                             width=CLIP_WIDTH, foot_thickness=BIRD_THICKNESS)
    emit_screen_bird(out_dir, "screen-bird-roost", build_bird(), BIRD_THICKNESS, clip=clip)


if __name__ == "__main__":
    main()
