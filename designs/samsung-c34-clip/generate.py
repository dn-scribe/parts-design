"""
samsung-c34-clip - a hinged saddle + tail hanger that puts a swivel bird on a
thin, rounded, bezel-less monitor top edge without clamping or adhesive.

Measured on a Samsung C34H89x: the top edge is a ~14.5 mm deep rounded rail
and the body recedes immediately behind it - nothing to clamp, no square edge
to hook. So this does NOT clamp:

    <name>_clip    x1  ONE flat print - a saddle (lays over the top edge,
                       carries the swivel cup) joined by a printed LIVING
                       HINGE to a ~50 mm tail. After printing, fold the tail
                       down ~100 deg along the V-score; it then drapes down
                       the back of the monitor. Its weight (+ coins in the
                       pocket) plus the saddle's front overhang trap the
                       saddle on the rail by balance - at any spot along the
                       top edge, on any top thickness.
    <name>_puck    x1  the usual flat slotted disc (build_swivel_puck) - the
                       bird foot tab glues into its top slot; it spins in the
                       saddle cup.

Both parts print flat, cup-up, NO supports. The <name>.* / .FCStd outputs are
a posed preview (tail folded down on a grey block = the monitor top edge).

Build:  make samsung-c34-clip
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from freecad_common import (build_c34_folding_clip, build_swivel_puck, emit_c34_clip,
                            parse_outdir, C34, SCREEN_CLIP_FOOT)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screen-bird-perch"))
from generate import build_bird as build_demo_bird   # noqa: E402  (preview only)

# ---------------------------------------------------------------------------
# Parameters (mm) - measure your monitor and adjust. The rest (plate/tail
# thickness, living-hinge web, cup) is the `C34` dict in freecad_common.py.
# ---------------------------------------------------------------------------
RAIL_DEPTH = 14.5      # monitor top-edge front-to-back (the one number to get right)
TAIL_LEN = 50.0        # how far the tail drapes down the back
BIRD_THICKNESS = SCREEN_CLIP_FOOT["thickness"]

C34["rail_depth"] = RAIL_DEPTH
C34["tail_len"] = TAIL_LEN


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    emit_c34_clip(out_dir, "samsung-c34-clip",
                  build_c34_folding_clip(),
                  build_swivel_puck(foot_thickness=BIRD_THICKNESS),
                  demo_bird_upright=build_demo_bird())


if __name__ == "__main__":
    main()
