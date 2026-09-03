"""
screen-bird-perch - an upright, alert little songbird that clips to the top
edge of a monitor.

One of the `screen-bird-*` family (see docs/agents-instructions.md and
scripts/freecad_common.py). Every pose in the family is the SAME two-part
mechanism:

    <name>_bird   x1   a flat side-profile silhouette, ~4 mm stock, with a
                       swept wing cut-out + a vent for weight, ending in a
                       rectangular foot tab at the belly.
    <name>_clip   x1   the shared flexible C-clip (build_screen_clip) that
                       grips a screen's top bezel and carries a through-slot
                       socket the foot tab drops into.

This folder is the PERCH pose: chest up, head high and slightly forward, a
long tail swept down and back so the bird's mass sits over the clip.

Colour: single colour = just the two objects. Multi-colour with no extra
parts and one plate = give the bird and the clip different filaments (they
are separate objects), and/or paint the beak / eye ring / wing cut-out edge
in the slicer (Bambu/Prusa/Orca "colour paint"). The bird prints flat, so a
filament swap by layer tints the front vs back face, not head vs body.

Everything exports ready to print - no supports, no slicer rotation:
    <name>_bird   laid flat, largest face on z = 0.
    <name>_clip   stood on a profile end face (one clean extrusion).
The <name>.* / .FCStd outputs are a posed preview (bird on the clip on a grey
slab standing in for the screen edge) - not a printable body.

Build:  make screen-bird-perch
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
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]   # plaque + foot-tab stock (4.0); socket tracks it
EYE_DIA = 3.2                   # eye hole

# Clip fit - forwarded to the shared C-clip. Tune BEZEL_NOMINAL to your screen
# (relaxed grip ~= BEZEL_NOMINAL - CLIP_PRELOAD; the arm flexes several mm more).
BEZEL_NOMINAL = 9.0
CLIP_PRELOAD = 0.8
CLIP_WIDTH = 18.0

def _circle(cx, cy, r, n=48, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _ellipse_rot(cx, cz, a, b, deg, n=48):
    t = math.radians(deg)
    ct, st = math.cos(t), math.sin(t)
    out = []
    for i in range(n):
        u = 2 * math.pi * i / n
        ex, ez = a * math.cos(u), b * math.sin(u)
        out.append((cx + ex * ct - ez * st, cz + ex * st + ez * ct))
    return out


# Lightening cut-outs, pre-SCALE frame, each (cx, cz, a, b, angle_deg) a rotated
# ellipse: one long "wing" sweep set into the body, one small round vent low.
LIGHTEN = [(0, 27, 12.5, 4.4, 16), (-1, 15, 3.4, 3.4, 0)]


def _s(pts):
    return [(x * SCALE, z * SCALE) for x, z in pts]


def _solid(pts, scale=True):
    """A silhouette polygon -> a thin solid plaque (extruded +/- along Y).
    Fusing thin SOLIDS is far more robust in OCC than merging coplanar faces."""
    p = _s(pts) if scale else pts
    s = xz_face(p).extrude(App.Vector(0, BIRD_THICKNESS, 0))
    s.translate(App.Vector(0, -BIRD_THICKNESS / 2.0, 0))
    return s


def _cut(pts, scale=True, pad=2.0):
    """Like _solid but oversized in Y, for boolean cuts through the plaque."""
    p = _s(pts) if scale else pts
    s = xz_face(p).extrude(App.Vector(0, BIRD_THICKNESS + 2 * pad, 0))
    s.translate(App.Vector(0, -BIRD_THICKNESS / 2.0 - pad, 0))
    return s


def build_bird():
    # --- silhouette parts, upright frame: +X beak, -X tail, +Z up -----------
    # `belly` (absolute coords, unscaled) tapers the lower body to a flat seat
    # at z = 1 that the foot tab fuses to - the bird then appears to perch
    # directly on the clip with no separate pedestal.
    parts = [
        _solid([(-13, 26), (13, 26), (9, 1), (-11, 1)], scale=False),   # belly / seat
        _solid(_circle(2, 31, 19, 72, ry=19.5)),                        # body
        _solid(_circle(18, 49, 10.0, 56)),                              # head
        _solid([(7, 42), (18, 38), (11, 22), (0, 25)]),                 # breast fill
        _solid([(33, 48), (23, 50.5), (23.5, 44.5)]),                   # beak
        _solid([(-6, 32), (-40, 21), (-58, 20), (-52, 14),
                (-40, 11), (-2, 15)]),                                  # tail
    ]
    bird = parts[0].fuse(parts[1:]).removeSplitter()
    assert len(bird.Solids) == 1, "perch silhouette is %d solids" % len(bird.Solids)

    cuts = [_cut(_ellipse_rot(cx, cz, a, b, d)) for cx, cz, a, b, d in LIGHTEN]
    cuts.append(_cut(_circle(20, 51, EYE_DIA / 2.0 / SCALE, 28)))
    bird = bird.cut(cuts[0].fuse(cuts[1:]))

    bird = bird.fuse(build_foot_tab(BIRD_THICKNESS, CLIP_WIDTH)).removeSplitter()
    assert len(bird.Solids) == 1, "perch bird is %d solids" % len(bird.Solids)
    return bird


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    clip = build_screen_clip(bezel_nominal=BEZEL_NOMINAL, preload=CLIP_PRELOAD,
                             width=CLIP_WIDTH, foot_thickness=BIRD_THICKNESS)
    emit_screen_bird(out_dir, "screen-bird-perch", build_bird(), BIRD_THICKNESS, clip=clip)


if __name__ == "__main__":
    main()
