"""Shared helpers for designs/*/generate.py scripts.

Import from a design's generate.py via:

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    from freecad_common import parse_outdir, export_glb
"""

import argparse
import os
import sys

import FreeCAD as App
import Part


def parse_outdir(script_file):
    """--outdir, defaulting to ./outputs next to the calling script.

    Tolerates being invoked either as `freecadcmd script.py -- --outdir X`
    (freecadcmd's --pass-through convention) or with no `--` at all (e.g.
    when run via runpy, as the Makefile does)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=None)
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    args = parser.parse_args(argv)
    script_dir = os.path.dirname(os.path.abspath(script_file))
    return args.outdir or os.path.join(script_dir, "outputs")


def export_glb(stl_path, glb_path):
    """Convert an STL to GLB via trimesh.

    FreeCAD's own glTF exporter lives in the Gui module and is unavailable
    under headless freecadcmd, so this is the standard substitute - pure
    Python, no FreeCAD Gui needed. Returns False (non-fatal) if trimesh
    isn't importable in whatever Python freecadcmd embeds."""
    try:
        import trimesh
    except ImportError:
        print("WARNING: trimesh not importable, skipping GLB export "
              "(pip install trimesh into this Python to enable it)", file=sys.stderr)
        return False
    mesh = trimesh.load(stl_path)
    mesh.export(glb_path)
    return True


def build_knurled_cylinder(dia, height, flute_count, flute_width, flute_depth):
    """Cylinder with `flute_count` shallow radial flutes cut into its
    side, for hand grip on a printed knob. Local (0,0) is the cylinder's
    own AXIS (Part.makeCylinder's point argument is the base circle's
    center, unlike Part.makeBox which takes a corner) - built along +Z
    from local z=0; rotate the returned shape if a different axis is
    needed (e.g. `shape.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)`
    to reorient from +Z to +X). Shared by any design with a turnable
    knob - see designs/build-plate-corner-clamp and
    designs/build-plate-notch-bracket for two different diameters/uses."""
    cyl = Part.makeCylinder(dia / 2.0, height, App.Vector(0, 0, 0))
    for i in range(flute_count):
        angle = i * (360.0 / flute_count)
        flute = Part.makeBox(flute_depth + 2.0, flute_width, height + 1.0,
                              App.Vector(dia / 2.0 - flute_depth, -flute_width / 2.0, -0.5))
        flute.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        cyl = cyl.cut(flute)
    return cyl


def build_retainer_fingers(mount_radius, count, arm_width, arm_thickness, arm_clearance, lip_reach,
                            underside_z, groove_top_z, groove_bottom_z, center_x, center_y):
    """N snap-fit fingers, hanging down (-Z) from underside_z to
    groove_bottom_z, centered on (center_x, center_y) in the caller's
    local frame - built along Z; rotate the returned shape if the target
    knob's axis is different (e.g. for a horizontal knob, rotate 90 about
    Y first, same as build_knurled_cylinder, then recompute the caller's
    own underside/groove Z values in that rotated frame before calling).
    Each finger is an L-profile: a thin vertical arm (from underside_z to
    groove_top_z, clear of the target boss's smooth collar) plus an
    inward lip (from groove_top_z to groove_bottom_z, reaching further
    in) that engages the boss's retention groove once seated. For count=1
    (a single, generously-sized hook instead of several thin fingers -
    see designs/build-plate-corner-clamp revision 7), the single finger
    lands at angle 180 - i.e. on a FLAT EDGE direction, not a corner. A
    thin appendage rooted at a square part's corner has the least material
    depth to fuse into of anywhere on that part's silhouette - exactly the
    wrong place to attach something that needs to hold under load.

    `arm_clearance` is the same gap the caller uses to derive mount_radius
    (mount_radius = boss_radius + arm_clearance + arm_thickness) - passed
    in separately here so this function can recover the boss's actual
    physical collar radius (mount_radius - arm_thickness - arm_clearance)
    for the connector piece below, without hardcoding an assumption about
    how mount_radius was built up.

    REAL BUG, found by checking `shape.Solids` (not by eyeballing a
    render, and not by checking Part.common() interference volume either
    - that check alone missed this): the arm and the lip, as two plain
    boxes meeting where the arm's inner face (mount_radius - arm_thickness)
    lines up with the lip's outer face, do NOT share a face. The arm's
    footprint (in the radial x direction) is [mount_radius - arm_thickness,
    mount_radius]; the lip's is [mount_radius - arm_thickness - lip_reach,
    mount_radius - arm_thickness] - these two intervals are DISJOINT,
    touching only at the single boundary value. Combined with the two
    pieces sitting at different (also merely touching, not overlapping) Z
    ranges, the two boxes meet at exactly one point in cross-section (a
    single edge in 3D, running along the width) - not a face, not even
    close to one. `Part.fuse()` cannot merge that into one solid; it
    stayed 2 separate solids in the result compound, confirmed on both
    the old 4-finger version of this file and a later, bigger 1-hook
    version alike - so this was never a new bug, just never checked
    (verification here previously only checked the lip's radial
    interference against the boss, never solid connectivity). A
    multi-solid "part" isn't a valid single manufacturable body (STEP
    export treats each solid separately) even where a forgiving mesh
    slicer might tolerate the touching-only STL geometry.

    Fixed with a third box, `connector`, bridging the arm and the lip
    with GENUINE 3D volume overlap on both sides - not by nudging the
    arm or lip themselves inward (that risks a real collision with the
    boss's actual collar material, which sits right where the tempting
    "just extend it a bit" fix would reach). The connector's inner face
    stays fixed at the boss's true collar radius (never closer to the
    axis than that - collar material starts exactly there, so this is
    the real safety floor, not `mount_radius - arm_thickness`, which
    already has `arm_clearance` of intentional air gap built in and can
    safely be encroached on without touching anything) and spans a small
    Z-straddle across the arm/lip transition height - safe on the lip
    side (the groove there has already had all its material cut away out
    past the collar) and safe on the arm side (same open radius the arm
    itself already occupies). Verify with `shape.Solids == 1` after
    fusing into the caller's own body, not just that the interference
    volume against the boss looks like a reasonable small number - a
    single connected solid and a plausible interference number are two
    different checks and this bug passed the second while failing the
    first."""
    JOINT_OVERLAP = min(0.4, (groove_top_z - groove_bottom_z) / 3.0)  # Z-straddle for the
                                                                        # arm/lip connector
    TOP_OVERLAP = 0.5   # arm pokes this far up into the caller's own solid body past
                          # underside_z - same genuine-overlap logic, different joint
    x_outer = mount_radius
    x_arm_inner = mount_radius - arm_thickness
    collar_radius = x_arm_inner - arm_clearance   # boss's real physical surface - the
                                                     # actual safety floor for the connector
    x_lip_inner = x_arm_inner - lip_reach
    half_w = arm_width / 2.0
    fingers = None
    for i in range(count):
        angle = i * (360.0 / count) + (360.0 / count / 2.0)
        arm = Part.makeBox(arm_thickness, arm_width, underside_z + TOP_OVERLAP - groove_top_z,
                            App.Vector(x_arm_inner, -half_w, groove_top_z))
        lip = Part.makeBox(lip_reach, arm_width, groove_top_z - groove_bottom_z,
                            App.Vector(x_lip_inner, -half_w, groove_bottom_z))
        connector = Part.makeBox(x_outer - collar_radius, arm_width, 2.0 * JOINT_OVERLAP,
                                  App.Vector(collar_radius, -half_w, groove_top_z - JOINT_OVERLAP))
        finger = arm.fuse(lip).fuse(connector)
        finger.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        finger.translate(App.Vector(center_x, center_y, 0))
        fingers = finger if fingers is None else fingers.fuse(finger)
    return fingers.removeSplitter()
