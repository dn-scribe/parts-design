"""
avocado-musher - a small 2-part hand masher/muddler: a flat-bottomed disc
HEAD (ribbed top, blind center socket) plus a long handle STICK (tenon +
collar + knurled grip + domed top) that glues into it.

Parametric remake of a found reference model (kept in original/ for
comparison, see designs/avocado-musher/original/) - the overall scale
(head ~30 mm dia, handle ~165 mm long) matches the reference; the internal
joint (blind socket from the top + a flush collar, instead of the
reference's own, less-clean internal geometry) is this script's own design
so the two printed parts actually mate cleanly.

    <name>_head    x1   disc, flat mash face down, 6 ribs on top converging
                        on a raised hub that doubles as the handle's seat.
    <name>_stick   x1   tenon -> flush collar -> knurled grip shaft -> domed
                        top knob. Tenon glues into the head's blind socket;
                        the collar seats flush on the hub.
    <name>_assembly      posed preview (stick pushed home in the head) -
                        not printable, STL/GLB/FCStd only.

Both printed parts need NO supports: the head sits flat mash-face-down (the
ribs/hub/socket are all additive or a vertical-walled blind pocket, nothing
undercut); the stick prints lying on its side (long thin rod, axisymmetric
features only).

Build:  make avocado-musher
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from freecad_common import build_knurled_cylinder, export_glb, parse_outdir

import FreeCAD as App
import Part

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------

# Head (mash disc)
HEAD_DIA = 30.0        # overall disc diameter
HEAD_H = 13.0          # main disc thickness (flat mash face at z=0)
RIB_COUNT = 6          # radiating ribs on top, evenly spaced
RIB_WIDTH = 4.0        # rib cross-section diameter (half-round bead)
HUB_H = RIB_WIDTH / 2.0   # flat hub boss height above HEAD_H - matches rib peak height
# HUB_DIA doubles as the stick's FLANGE_DIA so the collar seats flush on the hub
# (shared structural number - see docs/agents-instructions.md on cross-importing
# this kind of fit dimension instead of duplicating it).
HUB_DIA = 18.0
BORE_DIA = 12.4       # blind socket diameter - TENON_DIA + clearance
BORE_DEPTH = 9.0      # blind socket depth, measured down from the hub top

HEAD_TOTAL_H = HEAD_H + HUB_H   # 15 mm - also the hub/bore top plane

# Stick (handle)
SHAFT_DIA = 12.0        # main grip shaft diameter
TENON_DIA = 11.6        # insertion tenon diameter - fits BORE_DIA with ~0.4 mm clearance
TENON_LEN = 8.0         # insertion depth, slightly less than BORE_DEPTH (glue pocket at the bottom)
TENON_CHAMFER = 1.5     # lead-in chamfer at the tenon tip, eases insertion
FLANGE_DIA = HUB_DIA    # collar diameter - flush with the head's hub
FLANGE_H = 5.0
SHAFT_LEN = 143.0       # straight knurled grip length
FLUTE_COUNT = 16
FLUTE_WIDTH = 2.0
FLUTE_DEPTH = 0.6
KNOB_TAPER_H = 6.0      # cone transition from shaft to knob diameter
KNOB_DIA = 20.0
KNOB_H = KNOB_DIA / 2.0  # cylinder height == fillet radius -> a full dome (capsule tip)


def build_head():
    disc = Part.makeCylinder(HEAD_DIA / 2.0, HEAD_H, App.Vector(0, 0, 0))

    hub = Part.makeCylinder(HUB_DIA / 2.0, HUB_H, App.Vector(0, 0, HEAD_H))
    shape = disc.fuse(hub)

    rib_len = HEAD_DIA / 2.0 - HUB_DIA / 2.0 + 2.0   # overlap into the hub, reach the rim
    for i in range(RIB_COUNT):
        rib = Part.makeCylinder(RIB_WIDTH / 2.0, rib_len,
                                 App.Vector(HUB_DIA / 2.0 - 2.0, 0, HEAD_H),
                                 App.Vector(1, 0, 0))
        rib.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), i * (360.0 / RIB_COUNT))
        shape = shape.fuse(rib)

    bore = Part.makeCylinder(BORE_DIA / 2.0, BORE_DEPTH + 0.5,
                              App.Vector(0, 0, HEAD_TOTAL_H - BORE_DEPTH))
    shape = shape.cut(bore)

    shape = shape.removeSplitter()
    assert len(shape.Solids) == 1, "head is %d solids" % len(shape.Solids)
    return shape


def build_stick():
    tenon_tip = Part.makeCone(0.1, TENON_DIA / 2.0, TENON_CHAMFER, App.Vector(0, 0, 0))
    tenon_body = Part.makeCylinder(TENON_DIA / 2.0, TENON_LEN - TENON_CHAMFER,
                                    App.Vector(0, 0, TENON_CHAMFER))
    shape = tenon_tip.fuse(tenon_body)

    flange = Part.makeCylinder(FLANGE_DIA / 2.0, FLANGE_H, App.Vector(0, 0, TENON_LEN))
    shape = shape.fuse(flange)

    shaft_z0 = TENON_LEN + FLANGE_H
    shaft = build_knurled_cylinder(SHAFT_DIA, SHAFT_LEN, FLUTE_COUNT, FLUTE_WIDTH, FLUTE_DEPTH)
    shaft.translate(App.Vector(0, 0, shaft_z0))
    shape = shape.fuse(shaft)

    taper_z0 = shaft_z0 + SHAFT_LEN
    taper = Part.makeCone(SHAFT_DIA / 2.0, KNOB_DIA / 2.0, KNOB_TAPER_H, App.Vector(0, 0, taper_z0))
    shape = shape.fuse(taper)

    knob_z0 = taper_z0 + KNOB_TAPER_H
    knob = Part.makeCylinder(KNOB_DIA / 2.0, KNOB_H, App.Vector(0, 0, knob_z0))
    try:
        top_edge = [e for e in knob.Edges
                    if abs(e.BoundBox.ZMin - (knob_z0 + KNOB_H)) < 1e-6
                    and abs(e.BoundBox.ZMax - (knob_z0 + KNOB_H)) < 1e-6]
        knob = knob.makeFillet(KNOB_H, top_edge)
    except Exception:  # noqa: BLE001 - domed tip is cosmetic, ship a flat-top knob rather than fail the build
        pass
    shape = shape.fuse(knob)

    shape = shape.removeSplitter()
    assert len(shape.Solids) == 1, "stick is %d solids" % len(shape.Solids)
    return shape


def _stick_print_pose(shape):
    """The stick is built standing up (+Z = its own length) for easy
    reasoning/assembly, but a ~172 mm rod printed standing on its 18 mm
    flange would need a tall raft/brim and is a tip-over risk - lay it on
    its side instead (the standard pose for a long thin rod), tucked to
    z >= 0."""
    flat = shape.copy()
    flat.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    bb = flat.BoundBox
    flat.translate(App.Vector(0, 0, -bb.ZMin))
    return flat


def _export_part(out_dir, pname, shape):
    shape.exportStep(os.path.join(out_dir, pname + ".step"))
    stl = os.path.join(out_dir, pname + ".stl")
    shape.exportStl(stl)
    export_glb(stl, os.path.join(out_dir, pname + ".glb"))
    bb = shape.BoundBox
    print("  %-24s %6.1f x %6.1f x %6.1f mm   vol %8.0f mm^3   solids %d"
          % (pname, bb.XLength, bb.YLength, bb.ZLength, shape.Volume, len(shape.Solids)))


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)
    name = "avocado-musher"

    head = build_head()
    stick = build_stick()

    # Check the joint fit in its ASSEMBLED position, not the raw unposed
    # exports (which both start at z=0 and would overlap meaninglessly) -
    # see docs/agents-instructions.md on verifying interference numerically.
    posed_for_check = stick.copy()
    posed_for_check.translate(App.Vector(0, 0, HEAD_TOTAL_H - TENON_LEN))
    interference = head.common(posed_for_check).Volume
    assert interference < 1.0, (
        "tenon collides with the socket wall (%.2f mm^3) - BORE_DIA/TENON_DIA clearance is wrong" % interference)
    print("head/stick interference volume: %.2f mm^3 (expect ~0 - clearance/glue fit, not a press fit)"
          % interference)

    stick_flat = _stick_print_pose(stick)

    print("Printable pieces (orientation as exported - drop straight on the bed, no supports):")
    doc = App.newDocument("avocado_musher")
    doc.addObject("Part::Feature", name.replace("-", "_") + "_head").Shape = head
    doc.addObject("Part::Feature", name.replace("-", "_") + "_stick").Shape = stick_flat
    _export_part(out_dir, name + "_head", head)
    _export_part(out_dir, name + "_stick", stick_flat)

    # ---- posed assembly preview (not printable) ----------------------------
    posed_stick = posed_for_check
    assembled = Part.makeCompound([head, posed_stick])

    asm = App.newDocument("avocado_musher_assembly")
    asm.addObject("Part::Feature", "Head").Shape = head
    asm.addObject("Part::Feature", "Stick").Shape = posed_stick
    asm.recompute()
    fcstd = os.path.join(out_dir, name + "_assembly.FCStd")
    asm.saveAs(fcstd)

    stl = os.path.join(out_dir, name + "_assembly.stl")
    assembled.exportStl(stl)
    export_glb(stl, os.path.join(out_dir, name + "_assembly.glb"))
    print("Wrote posed assembly preview (not printable):\n  %s\n  %s" % (fcstd, stl))


if __name__ == "__main__":
    main()
