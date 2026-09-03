"""
screen-bird-clip-swivel - a turn-to-aim mount for the screen-bird-* set.

Same idea as the fixed clip in every screen-bird-* pose folder, but the bird
can be **rotated to any facing and left there**. Two printed parts, and the
bird itself is UNCHANGED:

    <name>_clip   x1   the flexible C-clip that grips a monitor's top bezel,
                       topped with a shallow open **cup** (a short wall + a
                       flat floor with a thin raised spin ring).
    <name>_puck   x1   a plain flat-bottomed round puck ("thick ring with a
                       notch") - just the standard `SCREEN_CLIP_FOOT`
                       through-slot on top for an unchanged bird foot tab.

Turn: the puck just drops into the cup and rests on the spin ring. The cup
wall stops it skating off; gravity (the bird's weight) keeps it seated - lift
the bird straight up to remove it. It rides on ~90 mm^2 of ring, so it turns
with a fingertip. No lip, no snap, no screw, no key.

Everything exports ready to print in the USE orientation, legs-down, NO
supports (PLA or PETG): the mouth ceiling is a ~37-deg tent (the legs meet at
a ridge - no bridge across the mouth), the leg->cup step is a ~37-deg cone
flare (base sized to fit inside the leg footprint), the cup wall is a short
vertical ring, the floor + spin ring face straight up. A round bore is just a
vertical hole - roundness never needs support. Overhang scan of the STLs:
0 mm^2 needs support on either part. See print-orientation.png.
    <name>_clip   legs down on the bed, cup opening up.
    <name>_puck   slot up, flat on the bed.
The <name>.* / .FCStd outputs are a posed preview (clip on a grey screen-edge
slab, puck seated, a demo bird turned off-axis) - not a printable body.

Build:  make screen-bird-clip-swivel
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from freecad_common import (build_swivel_clip, build_swivel_puck, emit_swivel_mount,
                            parse_outdir, SCREEN_CLIP_FOOT)

# a real screen-bird-* bird for the preview only (never built/exported here)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screen-bird-perch"))
from generate import build_bird as build_demo_bird   # noqa: E402

# ---------------------------------------------------------------------------
# Parameters (mm / degrees)
# ---------------------------------------------------------------------------
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]   # matches the birds; slot tracks it

# Clip fit - same knobs as the fixed clip. Relaxed grip ~= BEZEL_NOMINAL - CLIP_PRELOAD.
BEZEL_NOMINAL = 9.0
CLIP_PRELOAD = 0.8
CLIP_WIDTH = 18.0
CLIP_WALL = 7.0        # thick bridge: carries the cup + leaves room for a <40 deg mouth tent
# Cage / puck geometry (puck_od, lip, lift_fit, ...) is SCREEN_SWIVEL in
# scripts/freecad_common.py. Raise lift_fit for a looser turn, lower it to snug.


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)

    clip = build_swivel_clip(bezel_nominal=BEZEL_NOMINAL, preload=CLIP_PRELOAD,
                             width=CLIP_WIDTH, wall=CLIP_WALL,
                             foot_thickness=BIRD_THICKNESS)
    puck = build_swivel_puck(width=CLIP_WIDTH, foot_thickness=BIRD_THICKNESS)

    emit_swivel_mount(out_dir, "screen-bird-clip-swivel", clip, puck, wall=CLIP_WALL,
                      demo_bird_upright=build_demo_bird(), demo_turn_deg=35.0)


if __name__ == "__main__":
    main()
