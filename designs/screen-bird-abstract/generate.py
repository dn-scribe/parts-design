"""
screen-bird-abstract - a minimal, faceted bird: a single swept dart of a body,
a wedge beak, one blade tail, and a round negative-space eye. Clips to the top
edge of a monitor.

One of the `screen-bird-*` family (see docs/agents-instructions.md and
scripts/freecad_common.py). Every pose in the family is the SAME two-part
mechanism:

    <name>_bird   x1   a flat silhouette, ~4 mm stock - here a straight-edged,
                       low-poly abstraction rather than a naturalistic bird -
                       ending in a rectangular foot tab.
    <name>_clip   x1   the shared flexible C-clip (build_screen_clip) that
                       grips a screen's top bezel and carries a through-slot
                       socket the foot tab drops into.

This folder is the ABSTRACT model: the fastest, lightest print in the set and
the one that most obviously wants two colours - the body is split by a clean
diagonal so a slicer colour-paint (or a single flat filament swap by layer)
reads as a deliberate two-tone graphic. Give the clip its own colour too.

Everything exports ready to print - no supports, no slicer rotation:
    <name>_bird   laid flat, largest face on z = 0.
    <name>_clip   stood on a profile end face (one clean extrusion).
The <name>.* / .FCStd outputs are a posed preview - not a printable body.

Build:  make screen-bird-abstract
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
SCALE = 0.85
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]
EYE_DIA = 9.0                   # round negative-space eye

BEZEL_NOMINAL = 9.0
CLIP_PRELOAD = 0.8
CLIP_WIDTH = 18.0

# The whole bird is ONE straight-edged polygon (upright frame: +X beak, +Z up).
BODY_POLY = [
    (44, 45),    # beak tip
    (24, 55),    # crown
    (2, 46),     # nape
    (-44, 41),   # tail top
    (-56, 24),   # tail point
    (-38, 24),   # tail underside
    (-10, 20),   # lower back
    (16, 15),    # belly
    (31, 29),    # throat
    (44, 39),    # jaw -> back up to the beak tip
]


def _circle(cx, cy, r, n=56):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _s(pts):
    return [(x * SCALE, z * SCALE) for x, z in pts]


def _solid(pts, scale=True):
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
    # one straight-edged body polygon + an absolute flat seat (z = 1) for the tab
    parts = [
        _solid([(-12, 24), (12, 24), (9, 1), (-11, 1)], scale=False),   # seat
        _solid(BODY_POLY),                                              # the whole bird
    ]
    bird = parts[0].fuse(parts[1:]).removeSplitter()
    assert len(bird.Solids) == 1, "abstract silhouette is %d solids" % len(bird.Solids)

    eye = _cut(_circle(27, 42, EYE_DIA / 2.0 / SCALE))
    wing = _cut([(2, 40), (-30, 38), (-6, 25)])                       # angular wing slot
    bird = bird.cut(eye.fuse(wing))

    bird = bird.fuse(build_foot_tab(BIRD_THICKNESS, CLIP_WIDTH)).removeSplitter()
    assert len(bird.Solids) == 1, "abstract bird is %d solids" % len(bird.Solids)
    return bird


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    clip = build_screen_clip(bezel_nominal=BEZEL_NOMINAL, preload=CLIP_PRELOAD,
                             width=CLIP_WIDTH, foot_thickness=BIRD_THICKNESS)
    emit_screen_bird(out_dir, "screen-bird-abstract", build_bird(), BIRD_THICKNESS, clip=clip)


if __name__ == "__main__":
    main()
