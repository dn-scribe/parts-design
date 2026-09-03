"""Shared helpers for designs/*/generate.py scripts.

Import from a design's generate.py via:

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    from freecad_common import parse_outdir, export_glb
"""

import argparse
import math
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


# ===========================================================================
# Screen-top bird family: a shared flexible monitor clip + the foot socket
# that every `designs/screen-bird-*` pose plugs into.
#
# Used by designs/screen-bird-perch, screen-bird-peek, screen-bird-roost and
# screen-bird-abstract - each of those is one *pose* (its own folder, its own
# README, its own row in the root README), but they are all the SAME 2-part
# mechanism: a thin flat bird silhouette whose belly ends in a rectangular
# foot tab, and this C-clip that grips the top edge of a monitor and carries
# a matching through-slot socket on its back. Sharing the clip + the foot
# numbers here (rather than re-deriving them in four generate.py files) is the
# same rule the build-plate designs follow for TILE_SIZE/LEG_SIZE: a drifted
# socket number means a bird that does not sit on its clip.
# ===========================================================================

def xz_face(pts, y=0.0):
    """Planar face in the y = const plane from a list of (x, z); auto-closed.
    The natural plane for a bird side-profile silhouette (X = beak-to-tail,
    Z = up); extrude it +Y by the plaque thickness."""
    vs = [App.Vector(x, y, z) for x, z in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


# Foot tab / socket contract (mm). The tab is FULL clip width in X so it is
# captured in Y and Z by the through-slot and only needs centering + a dab of
# glue in X. `fit` is the total Y slack of the slot over the plaque thickness
# (halved per face). These are absolute - they do not scale with a bird's size.
SCREEN_CLIP_FOOT = dict(
    thickness=4.0,   # nominal bird-plaque thickness the socket is cut for (Y)
    height=9.0,      # how far the tab plugs down into the socket slot (Z)
    fit=0.4,         # total Y clearance, slot width = plaque thickness + fit
    overlap=2.0,     # how far the tab runs up into the bird body, for a solid fuse
)

# Assembled-frame Z of the socket-slot floor, i.e. where a foot tab's tip
# (local Z = -SCREEN_CLIP_FOOT['height']) lands, for the DEFAULT clip
# (wall = 3, boss_extra = 3). build_screen_clip() asserts it matches, so a
# tweak to those defaults that would move the seat can't slip through silently.
SCREEN_CLIP_SEAT_Z = 6.0


def build_foot_tab(plaque_thickness, clip_width, height=None, overlap=None):
    """The rectangular plug at a bird's belly, in the bird's UPRIGHT frame
    (X = beak-to-tail, Y = plaque thickness centred on 0, Z = up). Spans the
    full clip width in X; sits centred on Y = 0; runs from Z = -height (tab
    tip) up to Z = +overlap (buried in the body so the fuse is solid).

    Pair every bird silhouette with this and pair the clip's socket slot with
    the same `plaque_thickness` / `clip_width` so the three always agree."""
    height = SCREEN_CLIP_FOOT["height"] if height is None else height
    overlap = SCREEN_CLIP_FOOT["overlap"] if overlap is None else overlap
    return Part.makeBox(
        clip_width, plaque_thickness, height + overlap,
        App.Vector(-clip_width / 2.0, -plaque_thickness / 2.0, -height),
    )


def build_screen_clip(bezel_nominal=9.0, wall=3.0, width=18.0,
                      back_len=30.0, front_len=18.0, preload=0.8, hook=1.8,
                      boss_wall=3.0, boss_extra=3.0,
                      foot_thickness=None, foot_height=None, foot_fit=None,
                      fillet=0.8, socket="slot"):
    """A flexible C-clip that grips the top bezel of a stationary monitor.

    Built in the ASSEMBLED frame:
        X  screen-width  (the clip is one profile extruded this way)
        Y  front / back  (-Y = behind the screen, +Y = the viewer's side)
        Z  up            (mouth opens toward -Z; socket opens toward +Z)

    `socket="slot"` (default) tops the bridge with a raised boss carrying a
    THROUGH-slot socket for a bird foot tab: the whole part is then a single
    Y-Z profile pulled `width` along X, so it prints with no supports and no
    bridges stood on an X-end face (every slot / the grip tooth is a vertical
    channel). `socket=None` leaves the bridge bare - used by
    `build_swivel_clip()`, which fuses its own round pivot boss on top.

    Flex / range: `back_len` is a long cantilever spring; `preload` narrows
    the relaxed mouth so it grips; `hook` is a 45-deg-ramped tooth on the
    front lip that catches under the bezel. Nominal grip ~= bezel_nominal -
    preload, and the arm flexes several mm past that. A stick-on foam pad
    (see each README's BOM) extends the low end and protects the screen.

    Returns one solid (asserted)."""
    ft = SCREEN_CLIP_FOOT["thickness"] if foot_thickness is None else foot_thickness
    fh = SCREEN_CLIP_FOOT["height"] if foot_height is None else foot_height
    fit = SCREEN_CLIP_FOOT["fit"] if foot_fit is None else foot_fit

    g = bezel_nominal
    y_back_out = -(g / 2.0) - wall
    y_back_in = -(g / 2.0)
    y_front_in = (g / 2.0) - preload
    y_front_out = (g / 2.0) + wall
    z_bridge_top = wall
    z_back_bot = -back_len
    z_front_bot = -front_len

    y_boss_l = -(ft / 2.0 + boss_wall)
    y_boss_r = (ft / 2.0 + boss_wall)
    # socket floor sits `boss_extra` above the bridge top so there is real
    # material under the tab; boss is tall enough to bury the whole tab.
    z_slot_floor = z_bridge_top + boss_extra
    z_boss_top = z_slot_floor + fh + 1.0
    sw = ft + fit                      # socket slot width in Y
    if socket == "slot" and abs(z_slot_floor - SCREEN_CLIP_SEAT_Z) > 1e-6:
        print("WARNING: screen-clip seat Z = %.2f, SCREEN_CLIP_SEAT_Z = %.2f - "
              "bird poses import the constant; update it or the wall/boss_extra "
              "defaults so they agree." % (z_slot_floor, SCREEN_CLIP_SEAT_Z),
              file=sys.stderr)

    # inward grip tooth on the front lip (a shallow triangle: ramp on top so a
    # bezel cams the lip open on the way in, flat catch on the bottom)
    z_tooth = z_front_bot + 1.2

    top = [
        (y_boss_l, z_bridge_top),
        (y_boss_l, z_boss_top),
        (-sw / 2.0, z_boss_top),
        (-sw / 2.0, z_slot_floor),
        (sw / 2.0, z_slot_floor),
        (sw / 2.0, z_boss_top),
        (y_boss_r, z_boss_top),
        (y_boss_r, z_bridge_top),
    ] if socket == "slot" else []

    pts = [
        (y_back_out, z_back_bot),
        (y_back_out, z_bridge_top),
        *top,
        (y_front_out, z_bridge_top),
        (y_front_out, z_front_bot),
        (y_front_in, z_front_bot),
        (y_front_in, z_tooth),
        (y_front_in - hook, z_tooth + hook),          # tooth apex (points into the mouth)
        (y_front_in, z_tooth + 2.0 * hook + 0.6),     # 45-deg ramp back to the lip face
        (y_front_in, 0.0),
        (y_back_in, 0.0),
        (y_back_in, z_back_bot),
    ]
    wire = Part.makePolygon([App.Vector(0.0, y, z) for y, z in pts] +
                            [App.Vector(0.0, pts[0][0], pts[0][1])])
    face = Part.Face(wire)
    clip = face.extrude(App.Vector(width, 0.0, 0.0))
    clip.translate(App.Vector(-width / 2.0, 0.0, 0.0))

    # Break the long edges that run along the extrusion (X) - the ones a hand
    # actually touches. Cosmetic only: if OCC can't fillet the set at either
    # radius, ship the clip sharp rather than fail the build.
    for r in (fillet, fillet * 0.5) if fillet and fillet > 0.0 else ():
        try:
            cand = [e for e in clip.Edges
                    if e.Length > 2.2 * r
                    and abs(abs(e.tangentAt(e.FirstParameter).x) - 1.0) < 1e-3]
            out = clip.makeFillet(r, cand)
            if out.isValid() and len(out.Solids) == 1:
                clip = out
                break
        except Exception:  # noqa: BLE001
            continue

    assert len(clip.Solids) == 1, "screen clip is %d solids" % len(clip.Solids)
    return clip


def screen_clip_print_pose(clip):
    """Roll the clip 90 deg about Y so its extrusion axis (assembled X) stands
    vertical and a full Y-Z profile face lies on the bed, then tuck it into the
    +XYZ octant. In this pose every slot / tooth is a vertical channel - no
    overhang, no bridge, no supports - and the STL needs no slicer rotation."""
    s = clip.copy()
    s.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


# ---------------------------------------------------------------------------
# Swivel mount: a variant clip whose bird can be turned to ANY facing and left
# there. The bird is unchanged. Its foot tab plugs (+ glue) into a round PUCK
# ("a thick ring with a notch"). The puck just DROPS into a shallow open CUP on
# top of the clip and spins there - the cup wall stops it sliding off sideways,
# gravity (the bird's weight) keeps it seated. No snap lip, no capture: lift
# the bird straight up to take it off. The puck rests on a thin raised ring on
# the cup floor, so it turns with almost no friction.
#
# Everything prints legs-down in the USE orientation with NO supports and NO
# steep overhangs: the mouth ceiling is a 45-deg tent (the legs meet at a ridge
# instead of needing a bridge across the mouth), the leg->cup step is a 45-deg
# cone flare, the cup wall is a short vertical ring, the cup floor and its spin
# ring face straight up. The puck is a plain flat-bottomed slotted disc.
# See designs/screen-bird-clip-swivel.
# ---------------------------------------------------------------------------

SCREEN_SWIVEL = dict(
    puck_od=26.0,       # puck outer diameter, mm (>= bird tab width + side webs)
    puck_h=12.0,        # puck height, mm
    seat_fit=0.7,       # cup bore = puck_od + this -> radial clearance (free spin)
    cup_wall=3.0,       # cup wall thickness, mm
    cup_h=4.5,          # cup wall height above the floor, mm (just enough to trap it)
    spin_ring_w=1.4,    # width of the raised ring on the cup floor the puck rides on
    spin_ring_h=0.6,    # its height, mm
)


def _circle_prism(radius, z0, z1, n=72):
    wire = Part.makePolygon(
        [App.Vector(radius * math.cos(2 * math.pi * i / n),
                    radius * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
        + [App.Vector(radius, 0.0, z0)])
    return Part.Face(wire).extrude(App.Vector(0, 0, z1 - z0))


def _yz_prism(pts_yz, x_len):
    """Extrude a Y-Z polygon +/- x_len/2 along X (a cross-section pulled the
    screen-width way, like build_screen_clip's own profile)."""
    wire = Part.makePolygon([App.Vector(0.0, y, z) for y, z in pts_yz]
                            + [App.Vector(0.0, pts_yz[0][0], pts_yz[0][1])])
    s = Part.Face(wire).extrude(App.Vector(x_len, 0, 0))
    s.translate(App.Vector(-x_len / 2.0, 0, 0))
    return s


def _swivel_cup_out(wall):
    sw = SCREEN_SWIVEL
    return (sw["puck_od"] + sw["seat_fit"]) / 2.0 + sw["cup_wall"]


def _swivel_flare_base_r(wall, width, bezel_nominal):
    """Radius of the cone flare where it meets the legs. Capped to the largest
    circle that fits inside the leg footprint (width x 2*y_out) so the flare
    never overhangs the leg tops."""
    return min(width / 2.0, bezel_nominal / 2.0 + wall) - 0.5


def swivel_cage_floor_z(wall=5.0, width=18.0, bezel_nominal=9.0):
    """Assembled-frame Z of the cup floor (where the puck rests): the top of the
    cone flare that lifts the wide cup clear of the narrow clip legs."""
    cup_out = _swivel_cup_out(wall)
    base_r = _swivel_flare_base_r(wall, width, bezel_nominal)
    return wall + max(cup_out - base_r + 2.5, 2.0)       # flare well under 45 deg


def build_swivel_clip(bezel_nominal=9.0, wall=5.0, width=18.0, fillet=0.6,
                      **screen_clip_kwargs):
    """The screen clip topped with a shallow open **cup** the puck drops into
    and turns in. Assembled frame = print frame (legs down): same axes as
    build_screen_clip, mouth toward -Z, cup opening toward +Z. One solid."""
    sw = SCREEN_SWIVEL
    preload = screen_clip_kwargs.get("preload", 0.8)
    # equal-length legs so BOTH sit on the bed when the clip prints legs-down
    # (the default clip's short front lip would otherwise float ~12 mm up)
    screen_clip_kwargs.setdefault("back_len", 26.0)
    screen_clip_kwargs.setdefault("front_len", 26.0)
    body = build_screen_clip(bezel_nominal=bezel_nominal, wall=wall, width=width,
                             fillet=fillet, socket=None, **screen_clip_kwargs)

    g = bezel_nominal
    y_back_in, y_front_in = -(g / 2.0), (g / 2.0) - preload
    y_out = g / 2.0 + wall
    y_mid = (y_back_in + y_front_in) / 2.0                      # tent ridge, centred
    tent_over = 0.6                                            # cut runs this far past each mouth edge
    tent_base_half = (y_front_in - y_back_in) / 2.0 + tent_over
    # deep enough that both slopes are ~37 deg from vertical (1/tan37 ~= 1.33);
    # capped so >=1 mm of bridge stays above the ridge
    tent_h = min(wall - 1.0, 1.33 * tent_base_half)

    seat_r = (sw["puck_od"] + sw["seat_fit"]) / 2.0
    cup_out = _swivel_cup_out(wall)
    floor_z = swivel_cage_floor_z(wall, width, bezel_nominal)
    cup_top = floor_z + sw["cup_h"]

    # 1. tent the mouth ceiling: cut a V so the two legs meet at a ridge instead
    #    of needing a bridge across the mouth when printed legs-down (both slopes
    #    kept under 45 deg -> self-supporting). The cut runs a hair past each
    #    mouth edge and dips below z=0 so no sliver of the old flat ceiling is
    #    left along the edges.
    clip = body.cut(_yz_prism(
        [(y_back_in - tent_over, -0.6), (y_front_in + tent_over, -0.6),
         (y_mid, tent_h)], width + 2.0))

    # 2. CONE flare from the leg tops up to the cup radius. Round -> no corners
    #    to overhang; base radius fits inside the leg footprint so its underside
    #    never hangs over the leg edges; rise chosen for < 40 deg from vertical.
    base_r = _swivel_flare_base_r(wall, width, bezel_nominal)
    flare = Part.makeCone(base_r, cup_out, floor_z - wall + 0.01,
                          App.Vector(0, 0, wall - 0.01))
    clip = clip.fuse(flare).removeSplitter()

    # 3 + 4. the cup: a short vertical wall bored for the puck (open top, NO lip
    #    - the puck just lifts out) + a thin raised ring the puck rides on so
    #    friction is near zero. Both face up -> no overhang.
    clip = clip.fuse(build_swivel_cup(floor_z)).removeSplitter()

    assert len(clip.Solids) == 1, "swivel clip is %d solids" % len(clip.Solids)
    return clip


def swivel_cup_outer_r():
    """Outer radius of the open cup / spin platform (public for layout math)."""
    return _swivel_cup_out(5.0)


def build_swivel_cup(floor_z):
    """The shallow open cup a swivel puck drops into and turns in: a short
    vertical wall bored to the seat radius (open top, no lip), plus a thin
    raised ring on the floor the puck actually rides on. Its floor sits at
    `floor_z`; the caller supplies solid material under it. Both features face
    straight up -> prints with no support. Returns one solid."""
    sw = SCREEN_SWIVEL
    seat_r = (sw["puck_od"] + sw["seat_fit"]) / 2.0
    cup_out = _swivel_cup_out(5.0)
    cup_top = floor_z + sw["cup_h"]
    cup = Part.makeCylinder(cup_out, cup_top - floor_z, App.Vector(0, 0, floor_z))
    cup = cup.cut(_circle_prism(seat_r, floor_z + 0.01, cup_top + 1.0))
    ring_r = seat_r - 3.0
    spin = _circle_prism(ring_r + sw["spin_ring_w"] / 2.0,
                         floor_z, floor_z + sw["spin_ring_h"]).cut(
        _circle_prism(ring_r - sw["spin_ring_w"] / 2.0,
                      floor_z - 1.0, floor_z + sw["spin_ring_h"] + 1.0))
    return cup.fuse(spin).removeSplitter()


def build_swivel_puck(width=18.0, foot_thickness=None):
    """The "thick ring with a notch" that turns in build_swivel_clip()'s cup.
    A plain flat-bottomed disc with the standard `SCREEN_CLIP_FOOT` THROUGH-slot
    across the top for an unchanged bird foot tab. Prints slot-up, flat on the
    bed - the slot is open at both X ends so there is no ceiling. One solid."""
    sw = SCREEN_SWIVEL
    ft = SCREEN_CLIP_FOOT["thickness"] if foot_thickness is None else foot_thickness
    fit = SCREEN_CLIP_FOOT["fit"]
    fh = SCREEN_CLIP_FOOT["height"]

    r = sw["puck_od"] / 2.0
    h = sw["puck_h"]
    puck = Part.makeCylinder(r, h, App.Vector(0, 0, 0))
    puck = puck.cut(Part.makeBox(width + 6.0, ft + fit, fh + 1.0,
                                 App.Vector(-(width + 6.0) / 2.0,
                                            -(ft + fit) / 2.0, h - fh)))

    assert len(puck.Solids) == 1, "swivel puck is %d solids" % len(puck.Solids)
    return puck


def _swivel_tuck(shape):
    """Print pose for both swivel parts: no rotation (they are modelled in the
    print orientation - clip legs down, puck slot up), just tuck into +XYZ."""
    s = shape.copy()
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def emit_swivel_mount(out_dir, name, clip, puck, wall=5.0, demo_bird_upright=None,
                      demo_turn_deg=35.0, screen_ref_bezel=7.0, export_step=True):
    """Output plumbing for designs/screen-bird-clip-swivel. Writes:

        <name>_clip.{step,stl,glb}   the cage clip, legs-down (print as-is)
        <name>_puck.{step,stl,glb}   the turn puck, slot-up (print as-is)
        <name>.{stl,glb} + .FCStd    posed preview - clip on a grey screen-edge
                                     slab, puck seated in the cage, and (if
                                     given) a demo bird turned `demo_turn_deg`
                                     off-axis to show the swivel. Not printable.
    """
    doc = App.newDocument("screen_bird_clip_swivel")

    def _export(pname, shape):
        if export_step:
            shape.exportStep(os.path.join(out_dir, pname + ".step"))
        stl = os.path.join(out_dir, pname + ".stl")
        shape.exportStl(stl)
        export_glb(stl, os.path.join(out_dir, pname + ".glb"))
        bb = shape.BoundBox
        print("  %-24s %6.1f x %6.1f x %6.1f mm   vol %8.0f mm^3   solids %d"
              % (pname, bb.XLength, bb.YLength, bb.ZLength, shape.Volume, len(shape.Solids)))

    print("Printable pieces (footprint as exported - drop straight on the bed, no supports):")
    clip_flat = _swivel_tuck(clip)
    puck_flat = _swivel_tuck(puck)
    doc.addObject("Part::Feature", name + "_clip").Shape = clip_flat
    doc.addObject("Part::Feature", name + "_puck").Shape = puck_flat
    _export(name + "_clip", clip_flat)
    _export(name + "_puck", puck_flat)
    print("  (print 1x clip + 1x puck; then re-use any screen-bird-* bird unchanged)")

    # ---- posed preview -------------------------------------------------------
    floor_z = swivel_cage_floor_z(wall) + SCREEN_SWIVEL["spin_ring_h"]   # puck rides the ring
    posed_puck = puck.copy()
    posed_puck.translate(App.Vector(0, 0, floor_z))

    cb = clip.BoundBox
    slab = Part.makeBox(cb.XLength + 16.0, screen_ref_bezel, 22.0,
                        App.Vector(-(cb.XLength + 16.0) / 2.0, -screen_ref_bezel / 2.0, -21.0))
    shapes, names = [slab, clip, posed_puck], ["ScreenEdge_ref", "Clip", "Puck"]

    if demo_bird_upright is not None:
        slot_floor = floor_z + (SCREEN_SWIVEL["puck_h"] - SCREEN_CLIP_FOOT["height"])
        bird = demo_bird_upright.copy()
        bird.translate(App.Vector(0, 0, slot_floor + SCREEN_CLIP_FOOT["height"]))
        bird.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), demo_turn_deg)
        shapes.append(bird)
        names.append("Bird_turned")

    asm = App.newDocument("screen_bird_clip_swivel_posed")
    for nm, sh in zip(names, shapes):
        asm.addObject("Part::Feature", nm).Shape = sh
    asm.recompute()
    fcstd = os.path.join(out_dir, name + ".FCStd")
    asm.saveAs(fcstd)

    stl = os.path.join(out_dir, name + ".stl")
    Part.makeCompound(shapes).exportStl(stl)
    export_glb(stl, os.path.join(out_dir, name + ".glb"))
    print("Wrote posed preview (grey slab = screen edge; bird turned %g deg off-axis):\n  %s\n  %s"
          % (demo_turn_deg, fcstd, stl))


# ---------------------------------------------------------------------------
# samsung-c34-clip: a hinged saddle-and-tail hanger for a thin, rounded,
# bezel-less monitor top edge (measured on a Samsung C34H89x: ~14.5 mm deep
# rounded rail, body recedes immediately behind it - nothing to clamp).
#
# It does NOT clamp. A SADDLE lays over the top edge and carries the swivel
# cup; a ~50 mm TAIL hinges off its back and drapes down the back of the
# monitor. The tail's weight (plus optional coins in its pocket) plus the
# saddle's own front edge trap the saddle on the rail by balance, at ANY
# spot along the top edge and on any top thickness - the hinge lets the tail
# find its own angle against whatever the back looks like.
#
# All three printed parts lie flat / cup-up and print with NO support.
# See designs/samsung-c34-clip.
# ---------------------------------------------------------------------------

C34 = dict(
    rail_depth=14.5,      # monitor top-edge front-to-back (measured) - the FRONT fold line
    plate_t=4.0,          # saddle plate thickness, mm
    plate_back_extra=2.0, # gap between the cup back and the back fold line, mm
    tail_len=50.0,        # BACK tail length (down the monitor back), mm
    tail_w=24.0,          # back tail width along X, mm
    tail_t=6.0,           # tail / flap thickness, mm
    front_flap_len=12.0,  # FRONT flap length (folds down over the front edge as a backstop), mm
    front_flap_w=18.0,    # front flap width along X, mm
    web_t=1.0,            # living-hinge web thickness, mm (bottom-aligned)
    web_span=5.0,         # BACK web bend allowance along Y, mm
    front_web_span=3.0,   # FRONT web bend allowance (tiny), mm
    web_score=0.5,        # V-score depth from a web top -> ~(web_t - web_score) at the fold
    coin_pocket=(2.6, 20.0, 22.0),  # (depth into the tail top face, width X, length Y) weight slot
)


def _rounded_box(dx, dy, dz, origin, r):
    """makeBox + a safe fillet on the vertical (Z) edges; falls back to the raw
    box if OCC won't fillet."""
    b = Part.makeBox(dx, dy, dz, App.Vector(*origin))
    if r and r > 0:
        try:
            ez = [e for e in b.Edges
                  if abs(abs(e.tangentAt(e.FirstParameter).z) - 1.0) < 1e-3]
            out = b.makeFillet(min(r, dx / 2.0 - 0.1, dy / 2.0 - 0.1), ez)
            if out.isValid() and len(out.Solids) == 1:
                return out
        except Exception:  # noqa: BLE001
            pass
    return b


def _c34_layout():
    """Y positions of the two fold lines and the cup centre. The FRONT fold is
    at the rail's front edge; the cup sits entirely behind it (so it is not on
    the front flap); the BACK fold is just behind the cup."""
    c = C34
    cr = _swivel_cup_out(5.0)
    y_front_fold = c["rail_depth"]
    cup_y = y_front_fold - cr - 0.5            # cup front edge = the front fold line
    y_back_fold = cup_y - cr - c["plate_back_extra"]
    return dict(cr=cr, cup_y=cup_y, y_front_fold=y_front_fold, y_back_fold=y_back_fold)


def _c34_cup_y():
    return _c34_layout()["cup_y"]


def _c34_web(y_at, span, tw, into_minus, into_plus, web_t, score, plate_side):
    """A bottom-aligned living-hinge web centred on the fold line y_at: a thin
    strip spanning `span` (+ `into_minus`/`into_plus` overlap into the parts it
    joins). The V-score is offset `into_the pure web` AWAY from the plate
    (`plate_side` = +1 plate at +Y, -1 plate at -Y) so it never bites the thick
    plate. Returns (web_solid, score_solid)."""
    y0 = y_at - span / 2.0 - into_minus
    web = Part.makeBox(tw, span + into_minus + into_plus, web_t,
                       App.Vector(-tw / 2.0, y0, 0.0))
    ys = y_at - plate_side * 1.8
    sc = _yz_prism([(ys - 1.2, web_t + 0.5), (ys + 1.2, web_t + 0.5),
                    (ys, web_t - score)], tw - 1.0)        # stays inside the web
    return web, sc


def build_c34_folding_clip():
    """Saddle + TWO living hinges + two tails, as ONE flat print. Frame:
    X = screen width (fold axis), +Y = toward the screen front, Z up.

        [ back tail 50 ]-[ web ]-[ saddle plate + cup ]-[ tiny web ]-[ front flap 12 ]

    all coplanar on z = 0..stock. After printing:
      * fold the BACK tail down ~100 deg  -> it drapes down the monitor back
        (counterweight, stops the bird tipping the saddle forward);
      * fold the FRONT flap down ~110 deg -> it hangs over the rail's front
        edge and stops the saddle sliding backward off the rail.
    Prints with no support - webs are bottom-aligned strips, scores are
    top-face grooves, the cup opens up, the coin pocket opens to an end.
    One solid (asserted)."""
    c = C34
    pt, tt = c["plate_t"], c["tail_t"]
    lay = _c34_layout()
    cr, cup_y = lay["cr"], lay["cup_y"]
    yF, yB = lay["y_front_fold"], lay["y_back_fold"]
    sw = 2.0 * cr + 10.0
    tw, fw = c["tail_w"], c["front_flap_w"]

    # saddle plate (back fold line -> front fold line) + cup
    plate = _rounded_box(sw, yF - yB, pt, (-sw / 2.0, yB, 0.0), 3.0)
    cup = build_swivel_cup(pt)
    cup.translate(App.Vector(0.0, cup_y, 0.0))
    clip = plate.fuse(cup).removeSplitter()

    # ---- back: web + tail (plate is at +Y of this fold) ------------------
    web_b, score_b = _c34_web(yB, c["web_span"], tw, 1.0, 1.0, c["web_t"], c["web_score"], +1)
    y_bar_front = yB - c["web_span"] / 2.0 - 1.0
    bar = _rounded_box(tw, c["tail_len"] + 1.0, tt,
                       (-tw / 2.0, y_bar_front - c["tail_len"], 0.0), 2.0)
    clip = clip.fuse(web_b).fuse(bar).cut(score_b).removeSplitter()

    # ---- front: tiny web + short flap (plate is at -Y of this fold) -----
    web_f, score_f = _c34_web(yF, c["front_web_span"], fw, 1.0, 1.0, c["web_t"], c["web_score"], -1)
    y_flap0 = yF + c["front_web_span"] / 2.0 + 1.0
    flap = _rounded_box(fw, c["front_flap_len"] + 1.0, tt,
                        (-fw / 2.0, y_flap0 - 1.0, 0.0), 2.0)
    clip = clip.fuse(web_f).fuse(flap).cut(score_f).removeSplitter()

    # ---- coin / nut weight pocket in the back tail top face --------------
    cd, cwid, clen = c["coin_pocket"]
    clip = clip.cut(Part.makeBox(
        cwid, clen, cd + 0.2,
        App.Vector(-cwid / 2.0, y_bar_front - 4.0 - clen, tt - cd))).removeSplitter()

    assert len(clip.Solids) == 1, "c34 folding clip is %d solids" % len(clip.Solids)
    return clip


def _c34_fold_for_preview(clip):
    """Cut the flat clip into saddle / back-tail / front-flap and fold the two
    tails down about their fold lines, for the posed preview."""
    c = C34
    lay = _c34_layout()
    yF, yB = lay["y_front_fold"], lay["y_back_fold"]
    big = 500.0

    behind = Part.makeBox(big, big, big, App.Vector(-big / 2.0, yB - big, -big / 2.0))
    ahead = Part.makeBox(big, big, big, App.Vector(-big / 2.0, yF, -big / 2.0))
    back_tail = clip.common(behind)
    front_flap = clip.common(ahead)
    saddle = clip.cut(behind).cut(ahead)

    back_tail.rotate(App.Vector(0.0, yB, c["web_t"] / 2.0), App.Vector(1, 0, 0), 100.0)
    front_flap.rotate(App.Vector(0.0, yF, c["web_t"] / 2.0), App.Vector(1, 0, 0), -110.0)
    return saddle, back_tail, front_flap


def emit_c34_clip(out_dir, name, clip, puck, demo_bird_upright=None,
                  demo_turn_deg=30.0, export_step=True):
    """Output plumbing for designs/samsung-c34-clip. Writes <name>_clip (the
    one flat saddle+hinge+tail print) and <name>_puck, plus a posed preview
    (tail folded down, on a grey block standing in for the monitor top edge)."""
    doc = App.newDocument("samsung_c34_clip")

    def _export(pname, shape):
        if export_step:
            shape.exportStep(os.path.join(out_dir, pname + ".step"))
        stl = os.path.join(out_dir, pname + ".stl")
        shape.exportStl(stl)
        export_glb(stl, os.path.join(out_dir, pname + ".glb"))
        bb = shape.BoundBox
        print("  %-22s %6.1f x %6.1f x %6.1f mm   vol %8.0f mm^3   solids %d"
              % (pname, bb.XLength, bb.YLength, bb.ZLength, shape.Volume, len(shape.Solids)))

    print("Printable pieces (as exported - flat, cup-up on the bed, no supports):")
    puck_p = _swivel_tuck(puck)
    for pn, sh in ((name + "_clip", _swivel_tuck(clip)), (name + "_puck", puck_p)):
        doc.addObject("Part::Feature", pn).Shape = sh
        _export(pn, sh)
    print("  (print flat; fold the BACK tail down ~100 deg and the FRONT flap "
          "down ~110 deg along their V-scores; add coins to the tail pocket)")

    # ---- posed preview: both tails folded, on a grey top-edge block ---------
    c = C34
    saddle, back_tail, front_flap = _c34_fold_for_preview(clip)
    edge = Part.makeBox(clip.BoundBox.XLength + 20.0, c["rail_depth"], 26.0,
                        App.Vector(-(clip.BoundBox.XLength + 20.0) / 2.0, 0.0, -26.0))
    floor_z = c["plate_t"] + SCREEN_SWIVEL["spin_ring_h"]
    cup_y = _c34_cup_y()
    posed_puck = puck.copy()
    posed_puck.translate(App.Vector(0, cup_y, floor_z))
    shapes = [edge, saddle, back_tail, front_flap, posed_puck]
    names = ["MonitorTopEdge_ref", "Saddle", "BackTail_folded", "FrontFlap_folded", "Puck"]
    if demo_bird_upright is not None:
        b = demo_bird_upright.copy()
        b.translate(App.Vector(0, cup_y, floor_z + SCREEN_SWIVEL["puck_h"]))
        b.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), demo_turn_deg)
        shapes.append(b)
        names.append("Bird")

    asm = App.newDocument("samsung_c34_clip_posed")
    for nm, sh in zip(names, shapes):
        asm.addObject("Part::Feature", nm).Shape = sh
    asm.recompute()
    fcstd = os.path.join(out_dir, name + ".FCStd")
    asm.saveAs(fcstd)
    stl = os.path.join(out_dir, name + ".stl")
    Part.makeCompound(shapes).exportStl(stl)
    export_glb(stl, os.path.join(out_dir, name + ".glb"))
    print("Wrote posed preview (grey block = monitor top edge):\n  %s\n  %s" % (fcstd, stl))


def _bird_print_pose(bird):
    """Lay an upright bird silhouette (built in the X-Z plane, extruded +Y by
    the plaque thickness) flat on the bed: rotate -90 deg about X so a large
    plaque face is on z = 0, then tuck into the +XYZ octant. The foot tab stays
    in-plane. No supports - it is a flat plaque."""
    s = bird.copy()
    s.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90.0)
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def emit_screen_bird(out_dir, name, bird_upright, thickness,
                     clip=None, screen_ref_bezel=7.0, export_step=True):
    """Shared output plumbing for the `screen-bird-*` poses.

    `bird_upright` is the finished bird solid in the UPRIGHT frame (X beak-to-
    tail, Y = plaque thickness centred on 0, Z up, belly region straddling the
    foot tab). `clip` defaults to build_screen_clip(). Writes, into out_dir:

        <name>_bird.{step,stl,glb}   the bird, laid flat, ready to print
        <name>_clip.{step,stl,glb}   the clip, stood on end, ready to print
        <name>.{stl,glb} + .FCStd    posed preview: bird clipped to a short
                                     grey slab standing in for the screen edge
                                     (reference only - NOT a printable body).
                                     Named to sort first so it becomes preview.png.

    Returns the posed-compound shape."""
    assert len(bird_upright.Solids) == 1, "%s bird is %d solids" % (name, len(bird_upright.Solids))
    if clip is None:
        clip = build_screen_clip(foot_thickness=thickness)

    doc = App.newDocument("screen_bird_" + name.replace("-", "_"))

    def _export(pname, shape):
        if export_step:
            shape.exportStep(os.path.join(out_dir, pname + ".step"))
        stl = os.path.join(out_dir, pname + ".stl")
        shape.exportStl(stl)
        export_glb(stl, os.path.join(out_dir, pname + ".glb"))
        bb = shape.BoundBox
        print("  %-18s %6.1f x %6.1f x %6.1f mm   vol %8.0f mm^3   solids %d"
              % (pname, bb.XLength, bb.YLength, bb.ZLength, shape.Volume, len(shape.Solids)))

    print("Printable pieces (footprint as exported - drop straight on the bed, no supports):")
    bird_flat = _bird_print_pose(bird_upright)
    clip_flat = screen_clip_print_pose(clip)
    doc.addObject("Part::Feature", name + "_bird").Shape = bird_flat
    doc.addObject("Part::Feature", name + "_clip").Shape = clip_flat
    _export(name + "_bird", bird_flat)
    _export(name + "_clip", clip_flat)
    print("  (print 1x bird + 1x clip; a second colour on the clip or a filament")
    print("   swap by height on the bird are both optional - see the README)")

    # ---- posed preview -----------------------------------------------------
    lift = SCREEN_CLIP_SEAT_Z + SCREEN_CLIP_FOOT["height"]
    posed_bird = bird_upright.copy()
    posed_bird.translate(App.Vector(0, 0, lift))
    cb = clip.BoundBox
    slab = Part.makeBox(cb.XLength + 16.0, screen_ref_bezel, 22.0,
                        App.Vector(-(cb.XLength + 16.0) / 2.0, -screen_ref_bezel / 2.0, -21.0))

    asm = App.newDocument("screen_bird_" + name.replace("-", "_") + "_posed")
    asm.addObject("Part::Feature", "ScreenEdge_ref").Shape = slab
    asm.addObject("Part::Feature", "Clip").Shape = clip
    asm.addObject("Part::Feature", "Bird").Shape = posed_bird
    asm.recompute()
    fcstd = os.path.join(out_dir, name + ".FCStd")
    asm.saveAs(fcstd)

    compound = Part.makeCompound([slab, clip, posed_bird])
    stl = os.path.join(out_dir, name + ".stl")
    compound.exportStl(stl)
    export_glb(stl, os.path.join(out_dir, name + ".glb"))
    print("Wrote posed preview (grey slab = screen edge, reference only):\n  %s\n  %s"
          % (fcstd, stl))
    return compound

