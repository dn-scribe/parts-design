"""
Parametric bird - a VERY simple decorative flying-bird model, five flat
plaques that slot + glue into one spread-wing bird.

Inspired by a balsa/wire ornithopter skeleton: everything is FLAT stock,
nothing curved-in-3D, nothing that needs support.

Four printed pieces, one mechanism:

    bird_body        x1   side-profile silhouette - breast, neck, head,
                          pointed beak, tapered tail - pierced with a rib
                          lattice + eye hole. Its BACK is flattened into a
                          straight dorsal edge the connector rides on.
    bird_wing        x2   swept wing plaque with a rounded-square GRID
                          pattern (cells follow the planform so each row
                          runs parallel to the nearer edge) and a root
                          TONGUE that plugs into a connector slit. Print one
                          as modelled, print the second MIRRORED.
    bird_connector   x1   saddle bracket with a rounded (filleted) core. A
                          through slit in the bottom straddles the body's
                          flat back; two arms rise at a shallow angle - one
                          per side - each with a through slit that accepts
                          one wing tongue (perpendicular, in cross-section,
                          to the bottom slit). Bottom slit width tracks
                          BODY_THICKNESS, arm slit width tracks
                          WING_THICKNESS - real parametric fits.

Assembly: push the connector down onto the flat back just behind the head
(the bottom slit grips the 3 mm slab). Plug the right wing's tongue into the
+Y arm slit and the left wing's tongue into the -Y arm slit (mirror the
second wing). Both wings therefore share one station, X = const beside the
head. A drop of glue in the bottom slit and each arm slit locks it; the
wings' dihedral is set by the arm angle.

Sizing: the three *_SCALE factors at the top set the overall size. As shipped
(WING_SCALE 3.0) a wing is ~320 x 108 mm and all four pieces fit on one
350 x 350 Voron plate - the build prints each part's exported footprint. Set the
scales to 1.0 for the original palm-size bird.

Print orientation (all exported ready to print - no slicer rotation, no supports):
    bird_body, bird_wing - flat, largest face on the bed (z = 0).
    bird_connector       - the whole part is one profile extruded along the
                           spine; `generate.py` exports it already rolled 90 deg
                           so the spine axis stands vertical and a full profile
                           face lies on the bed. Every slit is then a vertical
                           channel - no overhang, no bridge.

The assembly `bird.*` / `bird.FCStd` outputs are an illustrative pose only.

Build via `make parametric-bird` from the repo root (freecadcmd does not
auto-execute a bare .py file - see docs/agents-instructions.md).

Outputs (default ./outputs relative to this script):
    bird_body.{step,stl,glb}         printable, flat
    bird_wing.{step,stl,glb}         printable, flat (print x2, one mirrored)
    bird_connector.{step,stl,glb}    printable, stand on a profile face (x1)
    bird.{stl,glb} + bird.FCStd      posed whole-bird preview (not printable)
"""

import math
import os
import sys

import FreeCAD as App
import Part

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from freecad_common import export_glb, parse_outdir

# ---------------------------------------------------------------------------
# Parameters (mm, degrees)
# ---------------------------------------------------------------------------
#
# Sized for a 350 mm Voron: WING_SCALE 3.0 gives a ~300 mm x ~100 mm wing, and
# the body / connector scale with it. All four pieces (2 wings + body +
# connector) fit on one 350 x 350 plate - the build prints each part's footprint
# so you can confirm the arrangement. To shrink the whole model back down, just
# lower the three *_SCALE factors (1.0 = the original palm-size bird).

WING_SCALE = 3.0
BODY_SCALE = 2.2
CONN_SCALE = 2.2

# --- Wing (one plaque; root edge on the Y axis, span +X, chord -Y) ----------
WING_SPAN = 100.0 * WING_SCALE      # root edge to wing tip  (~300 mm)
WING_ROOT_CHORD = 33.0 * WING_SCALE # front-to-back depth at the body  (~100 mm)
WING_TIP_CHORD = 5.0 * WING_SCALE   # front-to-back depth at the tip
WING_TIP_LE_DROP = 14.0 * WING_SCALE  # tip leading edge set-back (keeps the plaque narrow)
WING_LE_BOW = 10.0 * WING_SCALE     # forward bow of the leading edge at mid-span
WING_TE_BOW = 0.22                  # trailing-edge lift, fraction of WING_ROOT_CHORD
WING_THICKNESS = 3.2               # plaque thickness (also the tongue thickness) - not scaled
WING_BORDER = 3.5                  # solid rim kept around the pattern
WING_EDGE_R = 1.5                  # rounding on the wing / body outer edges

# Wing pattern: a rounded-square grid that follows the wing planform - rows run
# spanwise (so each row is roughly parallel to whichever of the leading/trailing
# edge it is nearer).
GRID_COLS = 8            # pattern cells along the span
GRID_ROWS = 4             # pattern cells across the chord
GRID_FILL = 0.90         # hole size as a fraction of the local cell pitch
GRID_CORNER = 2.5        # hole corner rounding radius, mm
GRID_MARGIN_SPAN = 0.08  # span fraction kept solid at root and tip
GRID_MARGIN_CHORD = 0.16 # chord fraction kept solid at the LE and TE

TONGUE_DEPTH = 9.0 * CONN_SCALE     # how far the wing tongue enters the arm slit
TONGUE_WIDTH = 26.0                 # tongue size along the root edge (<= CONN_SPINE)
TONGUE_CHORD_FRAC = 0.5             # tongue position along the root chord (0 = LE, 1 = TE)

# --- Body (side profile in XY: +X toward the beak, +Y up) ------------------
# "arrow" read: narrow shaft, long stretched head/neck out front, fletched tail.
BODY_LENGTH = 106.0 * BODY_SCALE   # body ellipse span (real beak-to-tail is longer)
BODY_HEIGHT = 20.0 * BODY_SCALE    # breast to back - small for a narrow shaft
BODY_THICKNESS = 3.8               # plaque thickness (bottom slit tracks this) - not scaled
BODY_BORDER = 4.0
HEAD_LENGTH = 34.0 * BODY_SCALE    # head stretched along the spine (an oval, not a ball)
HEAD_DIA = 13.0 * BODY_SCALE       # head depth across the spine
HEAD_REACH = 0.98         # head centre X as a fraction of the body semi-axis a
HEAD_DROP = 0.35          # head centre Y as a fraction of b (0 = spine line)
NECK_TAPER = 0.32         # neck root position along the head, fraction of HEAD_LENGTH
BEAK_LENGTH = 18.0 * BODY_SCALE
BEAK_ROOT = 6.0 * BODY_SCALE       # beak height where it meets the head
TAIL_LENGTH = 34.0 * BODY_SCALE
TAIL_SPREAD = 22.0 * BODY_SCALE    # tail height at its tip (the fletching)
EYE_DIA = 2.4 * BODY_SCALE
BODY_RIB_WIDTH = 1.7 * BODY_SCALE
BACK_FLAT_LEN = 40.0 * BODY_SCALE  # length of the straight dorsal edge (connector rides here)

# --- Connector (saddle; across = Y, up = Z, spine = X) --------------------
CONN_SPINE = 12.0 * CONN_SCALE     # extent along the bird's spine
SADDLE_HALF = 11.0 * CONN_SCALE    # half-width of the core in Y
CORE_H = 13.0 * CONN_SCALE         # core height in Z
STRADDLE_FIT = 0.5                 # added to BODY_THICKNESS for the bottom slit - not scaled
STRADDLE_DEPTH = 8.0 * CONN_SCALE  # how far the bottom slit rises from Z = 0
ARM_ELEV = 18.0                    # arm angle above horizontal = wing dihedral
ARM_LEN = 17.0 * CONN_SCALE        # arm length along its own axis
ARM_TZ = 6.0 * CONN_SCALE          # arm plate thickness (must exceed the wing slit width)
ARM_ROOT_Z = 5.0 * CONN_SCALE      # Z where the arm centreline leaves the core side
SLIT_FIT = 0.4                     # added to WING_THICKNESS for the arm slit - not scaled
SLIT_DEPTH = 11.0 * CONN_SCALE     # slit depth along the arm axis
CORE_FILLET = 1.4 * CONN_SCALE     # rounding on the connector core edges


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v(x, y):
    return App.Vector(x, y, 0)


def _bezier(p0, p1, p2, n):
    """n points along the quadratic Bezier p0->p2 with control p1 (ends incl.)."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def _circle_pts(cx, cy, r, n, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _poly_face(pts):
    """Planar face in the z = 0 plane from a list of (x, y); auto-closed."""
    vs = [_v(x, y) for x, y in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


def _yz_face(pts):
    """Planar face in the x = 0 plane from a list of (y, z); auto-closed."""
    vs = [App.Vector(0.0, y, z) for y, z in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


def _strut_face(a, b, width):
    """Thin rectangular face: the segment a->b thickened by `width`."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    h = width / 2.0
    return _poly_face([(a[0] + nx * h, a[1] + ny * h),
                       (b[0] + nx * h, b[1] + ny * h),
                       (b[0] - nx * h, b[1] - ny * h),
                       (a[0] - nx * h, a[1] - ny * h)])


def _as_face(shape):
    if isinstance(shape, Part.Face):
        return shape
    if getattr(shape, "Faces", None):
        return max(shape.Faces, key=lambda f: f.Area)
    return Part.Face(max(shape.Wires, key=lambda w: w.Length))


def _through(face, thickness, pad=2.0):
    """Extrude a z = 0 face into a prism that fully spans a `thickness`-thick
    plaque (from z = -pad/2 to z = thickness + pad/2), for boolean cuts."""
    solid = face.extrude(App.Vector(0, 0, thickness + pad))
    solid.translate(App.Vector(0, 0, -pad / 2.0))
    return solid


def _unit(vx, vy):
    n = math.hypot(vx, vy) or 1.0
    return (vx / n, vy / n)


def _rounded_rect_local(hx, hy, cr, seg=4):
    """Rounded-rectangle outline in local coords: half-extents hx, hy; corner
    radius cr; `seg` segments per 90 deg corner arc."""
    cr = max(0.0, min(cr, hx - 1e-3, hy - 1e-3))
    pts = []
    for cx, cy, a0 in ((hx - cr, hy - cr, 0.0), (-(hx - cr), hy - cr, 90.0),
                       (-(hx - cr), -(hy - cr), 180.0), (hx - cr, -(hy - cr), 270.0)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + cr * math.cos(a), cy + cr * math.sin(a)))
    return pts


def _soften(shape, r, min_len_mult=2.2, max_edges=64):
    """Fillet every edge longer than `min_len_mult * r`. Returns the shape
    unchanged (with a warning) if there are too many edges to be quick, or if
    the fillet fails or changes the solid count - a rounded edge is cosmetic,
    never worth a broken or slow build."""
    try:
        edges = [e for e in shape.Edges if e.Length > min_len_mult * r]
        if not edges:
            return shape
        if len(edges) > max_edges:
            print("WARNING: fillet r=%.2f skipped (%d edges > %d)"
                  % (r, len(edges), max_edges), file=sys.stderr)
            return shape
        out = shape.makeFillet(r, edges)
        if out.isValid() and len(out.Solids) == max(1, len(shape.Solids)):
            return out
        print("WARNING: fillet r=%.2f rejected (invalid or split)" % r, file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print("WARNING: fillet r=%.2f skipped (%s)" % (r, exc), file=sys.stderr)
    return shape


# ---------------------------------------------------------------------------
# Body
# ---------------------------------------------------------------------------

def _body_geo():
    a = 0.34 * BODY_LENGTH
    b = 0.5 * BODY_HEIGHT
    head_c = (HEAD_REACH * a, HEAD_DROP * b)
    head_rear_x = head_c[0] - HEAD_LENGTH / 2.0
    # dorsal flat sits on the body, behind the neck root
    back_x1 = min(0.52 * a, head_rear_x + NECK_TAPER * HEAD_LENGTH - 2.0)
    back_x0 = back_x1 - BACK_FLAT_LEN
    y_end = min(b * math.sqrt(max(0.0, 1.0 - (back_x0 / a) ** 2)),
                b * math.sqrt(max(0.0, 1.0 - (back_x1 / a) ** 2)))
    back_y = 0.97 * y_end
    return dict(a=a, b=b, head_c=head_c, head_len=HEAD_LENGTH, head_dia=HEAD_DIA,
                head_rear_x=head_rear_x, back_x0=back_x0, back_x1=back_x1, back_y=back_y)


def build_body():
    g = _body_geo()
    a, b, head_c = g["a"], g["b"], g["head_c"]
    hlx, hdy = HEAD_LENGTH / 2.0, HEAD_DIA / 2.0

    ellipse = _poly_face([(a * math.cos(t), b * math.sin(t))
                          for t in [2 * math.pi * i / 72 for i in range(72)]])
    # stretched oval head
    head = _poly_face(_circle_pts(head_c[0], head_c[1], hlx, 56, ry=hdy))

    # neck: a slim wedge bridging the body front to the underside of the head
    nx = head_c[0] - NECK_TAPER * HEAD_LENGTH
    neck = _poly_face([
        (0.36 * a, 0.42 * b),
        (nx, head_c[1] + 0.30 * HEAD_DIA),
        (nx, head_c[1] - 0.70 * HEAD_DIA),
        (0.46 * a, -0.60 * b),
    ])

    beak_base_x = head_c[0] + hlx * math.cos(math.radians(38))
    beak = _poly_face([
        (head_c[0] + hlx + BEAK_LENGTH, head_c[1]),
        (beak_base_x, head_c[1] + BEAK_ROOT / 2.0),
        (beak_base_x, head_c[1] - BEAK_ROOT / 2.0),
    ])
    tail = _poly_face([
        (-0.82 * a, 0.55 * b),
        (-a - TAIL_LENGTH, TAIL_SPREAD / 2.0),
        (-a - TAIL_LENGTH, -TAIL_SPREAD / 2.0),
        (-0.82 * a, -0.55 * b),
    ])

    blob = ellipse.fuse([neck, head, beak, tail]).removeSplitter()

    # flatten the back into a straight dorsal edge for the connector
    trim = _poly_face([(g["back_x0"], g["back_y"]), (g["back_x1"], g["back_y"]),
                       (g["back_x1"], b + HEAD_DIA + 10), (g["back_x0"], b + HEAD_DIA + 10)])
    blob = blob.cut(_through(trim, BODY_THICKNESS))
    outline = _as_face(blob)

    struts = []
    for sign in (1, -1):
        struts.append(_strut_face((-0.9 * a, sign * 0.35 * b),
                                  (0.6 * a, sign * 0.35 * b), BODY_RIB_WIDTH))
    for fx in (-0.45, 0.0, 0.35):
        struts.append(_strut_face((fx * a, -0.95 * b), (fx * a, 0.95 * b), BODY_RIB_WIDTH))

    panel = outline.extrude(App.Vector(0, 0, BODY_THICKNESS))
    inner = _as_face(outline.makeOffset2D(-BODY_BORDER))
    body = panel.cut(inner.extrude(App.Vector(0, 0, BODY_THICKNESS)))
    for strut in struts:
        clip = strut.extrude(App.Vector(0, 0, BODY_THICKNESS)).common(panel)
        if clip.Volume > 1e-6:
            body = body.fuse(clip)
    body = body.removeSplitter()

    body = body.cut(Part.makeCylinder(EYE_DIA / 2.0, BODY_THICKNESS + 2.0,
                                      App.Vector(head_c[0] + HEAD_LENGTH * 0.20,
                                                 head_c[1] + HEAD_DIA * 0.12, -1.0)))
    body = _soften(body, WING_EDGE_R)   # skipped automatically if the lattice has too many edges
    assert len(body.Solids) == 1, "body is %d solids" % len(body.Solids)
    return body


# ---------------------------------------------------------------------------
# Wing
# ---------------------------------------------------------------------------

def build_wing():
    root_le = (0.0, 0.0)
    root_te = (0.0, -WING_ROOT_CHORD)
    tip_le = (WING_SPAN, -WING_TIP_LE_DROP)
    tip_te = (WING_SPAN, -WING_TIP_LE_DROP - WING_TIP_CHORD)
    te_ctrl = (0.55 * WING_SPAN, -WING_TE_BOW * WING_ROOT_CHORD)

    n = 120
    le = _bezier(root_le, (0.5 * WING_SPAN, WING_LE_BOW), tip_le, n)
    te = _bezier(root_te, te_ctrl, tip_te, n)
    outline = _poly_face(le + list(reversed(te))[1:])
    wing = outline.extrude(App.Vector(0, 0, WING_THICKNESS))

    inner = _as_face(outline.makeOffset2D(-WING_BORDER))

    def inside(p):
        return inner.isInside(App.Vector(p[0], p[1], 0.0), 1e-4, True)

    def at(seq, u):
        return seq[min(n - 1, max(0, int(round(u * (n - 1)))))]

    def blend(u, v):
        pa, pb = at(le, u), at(te, u)
        return (pa[0] * (1.0 - v) + pb[0] * v, pa[1] * (1.0 - v) + pb[1] * v)

    # Rounded-square grid mapped onto the (span u, chord v) planform. A row of
    # constant v is the v-blend of the leading and trailing edge curves, so it
    # runs roughly parallel to whichever edge it is nearer; each hole's own axes
    # follow the local span tangent and the local chord direction.
    du = (1.0 - 2.0 * GRID_MARGIN_SPAN) / GRID_COLS
    dv = (1.0 - 2.0 * GRID_MARGIN_CHORD) / GRID_ROWS
    holes = []
    open_area = 0.0
    for c in range(GRID_COLS):
        u = GRID_MARGIN_SPAN + du * (c + 0.5)
        le_u, te_u = at(le, u), at(te, u)
        chord_len = math.hypot(te_u[0] - le_u[0], te_u[1] - le_u[1])
        ay = _unit(te_u[0] - le_u[0], te_u[1] - le_u[1])
        pp, pm = blend(min(u + du * 0.5, 1.0), 0.5), blend(max(u - du * 0.5, 0.0), 0.5)
        span_pitch = math.hypot(pp[0] - pm[0], pp[1] - pm[1])
        ax = _unit(pp[0] - pm[0], pp[1] - pm[1])
        hx = 0.5 * GRID_FILL * span_pitch
        hy = 0.5 * GRID_FILL * chord_len * dv
        local = _rounded_rect_local(hx, hy, GRID_CORNER)
        for r in range(GRID_ROWS):
            v = GRID_MARGIN_CHORD + dv * (r + 0.5)
            cx, cy = blend(u, v)
            poly = [(cx + ax[0] * lx + ay[0] * ly, cy + ax[1] * lx + ay[1] * ly)
                    for lx, ly in local]
            if all(inside(p) for p in poly):
                f = _poly_face(poly)
                holes.append(f)
                open_area += f.Area
    if holes:
        prisms = [_through(h, WING_THICKNESS) for h in holes]
        wing = wing.cut(prisms[0] if len(prisms) == 1 else prisms[0].fuse(prisms[1:]))

    # root tongue (overlaps 1 mm into the plaque so it fuses solidly)
    yc = -TONGUE_CHORD_FRAC * WING_ROOT_CHORD
    tongue = Part.makeBox(TONGUE_DEPTH + 1.0, TONGUE_WIDTH, WING_THICKNESS,
                          App.Vector(-TONGUE_DEPTH, yc - TONGUE_WIDTH / 2.0, 0.0))
    wing = wing.fuse(tongue).removeSplitter()

    print("  wing grid: %d holes, open ~%.0f%% of the plan area"
          % (len(holes), 100.0 * open_area / outline.Area))
    assert len(wing.Solids) == 1, "wing is %d solids" % len(wing.Solids)
    return wing


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

def _arm(sign):
    """(arm solid, slit solid, tip_yz) for the +Y (sign=1) or -Y (sign=-1) arm,
    built in the Y-Z plane and extruded along X."""
    e = math.radians(ARM_ELEV)
    dy, dz = sign * math.cos(e), math.sin(e)      # arm axis
    ny, nz = -sign * math.sin(e), math.cos(e)     # arm normal
    root = (sign * (SADDLE_HALF - 1.0), ARM_ROOT_Z)
    tip = (root[0] + ARM_LEN * dy, root[1] + ARM_LEN * dz)
    ht = ARM_TZ / 2.0
    quad = [(root[0] + ny * ht, root[1] + nz * ht),
            (tip[0] + ny * ht, tip[1] + nz * ht),
            (tip[0] - ny * ht, tip[1] - nz * ht),
            (root[0] - ny * ht, root[1] - nz * ht)]
    arm = _yz_face(quad).extrude(App.Vector(CONN_SPINE + 0.02, 0, 0))
    arm.translate(App.Vector(-(CONN_SPINE + 0.02) / 2.0, 0, 0))

    hs = (WING_THICKNESS + SLIT_FIT) / 2.0
    s0 = (tip[0] + dy * 1.0, tip[1] + dz * 1.0)          # just past the tip (open mouth)
    s1 = (tip[0] - dy * SLIT_DEPTH, tip[1] - dz * SLIT_DEPTH)
    slit_q = [(s0[0] + ny * hs, s0[1] + nz * hs),
              (s1[0] + ny * hs, s1[1] + nz * hs),
              (s1[0] - ny * hs, s1[1] - nz * hs),
              (s0[0] - ny * hs, s0[1] - nz * hs)]
    slit = _yz_face(slit_q).extrude(App.Vector(CONN_SPINE + 6.0, 0, 0))
    slit.translate(App.Vector(-(CONN_SPINE + 6.0) / 2.0, 0, 0))
    return arm, slit, tip


def build_connector():
    core = _yz_face([(-SADDLE_HALF, 0.0), (SADDLE_HALF, 0.0),
                     (SADDLE_HALF, CORE_H), (-SADDLE_HALF, CORE_H)])
    conn = core.extrude(App.Vector(CONN_SPINE, 0, 0))
    conn.translate(App.Vector(-CONN_SPINE / 2.0, 0, 0))
    conn = _soften(conn, CORE_FILLET)   # round the core cube

    slits = []
    for sign in (1, -1):
        arm, slit, _ = _arm(sign)
        conn = conn.fuse(arm)
        slits.append(slit)
    conn = conn.removeSplitter()

    # straddle slit: runs THROUGH the connector along the spine (X), thin in Y
    # (hugs the body slab), open at the bottom. Perpendicular in cross-section
    # to the wing slits. Because every connector feature - core, arms, both slit
    # families - is now a plain X-extrusion, the part prints as a single 2D
    # profile pulled 12 mm along X: stand it on a profile face and there is no
    # overhang or bridge anywhere, no supports.
    half = (BODY_THICKNESS + STRADDLE_FIT) / 2.0
    straddle = Part.makeBox(CONN_SPINE + 4.0, half * 2.0, STRADDLE_DEPTH + 1.0,
                            App.Vector(-(CONN_SPINE + 4.0) / 2.0, -half, -1.0))
    conn = conn.cut(straddle)
    for slit in slits:
        conn = conn.cut(slit)
    conn = conn.removeSplitter()
    conn = _soften(conn, 0.6)   # knock the remaining hard arm / mouth edges down

    assert len(conn.Solids) == 1, "connector is %d solids" % len(conn.Solids)
    return conn


# ---------------------------------------------------------------------------
# Assembly pose (preview only)
# ---------------------------------------------------------------------------

def _posed(body, wing, connector):
    O = App.Vector(0, 0, 0)
    X, Y, Z = App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)
    g = _body_geo()
    slab_mid_y = -BODY_THICKNESS / 2.0
    conn_z0 = g["back_y"] - STRADDLE_DEPTH     # connector local z=0 sits here so the
    #                                           straddle slot drops over the flat back

    body_p = body.copy()
    body_p.rotate(O, X, 90)   # profile XY -> vertical XZ slab (thickness now along -Y)

    # one connector, just behind the head - both wings hang off its two arms so
    # they share the same station (X = const, beside the head)
    st = g["back_x1"] - CONN_SPINE / 2.0 - 3.0

    conn = connector.copy()
    conn.translate(App.Vector(st, slab_mid_y, conn_z0))
    conns = {"main": conn}

    e = math.radians(ARM_ELEV)
    tcx = -TONGUE_DEPTH / 2.0                        # tongue centre, wing-local
    tcy = -TONGUE_CHORD_FRAC * WING_ROOT_CHORD
    tcz = WING_THICKNESS / 2.0

    def slit_centre(sign, st):
        """Mid-point of the arm slit, in the assembled frame."""
        _, _, tip = _arm(sign)
        dy, dz = sign * math.cos(e), math.sin(e)
        k = (1.0 - SLIT_DEPTH) / 2.0
        return App.Vector(st, tip[0] + dy * k + slab_mid_y, tip[1] + dz * k + conn_z0)

    def orient(shape_or_vec, mirror):
        s = shape_or_vec
        rots = ((X, 180.0),      # flip about the span (long) axis -> leading edge forward
                (Z, 90.0),       # span -> +Y outboard, chord -> X (nose-tail)
                (X, ARM_ELEV))   # dihedral = arm elevation
        for axis, ang in rots:
            if isinstance(s, App.Vector):
                s = App.Rotation(axis, ang).multVec(s)
            else:
                s.rotate(O, axis, ang)
        if mirror:
            if isinstance(s, App.Vector):
                s = App.Vector(s.x, -s.y, s.z)
            else:
                s = s.mirror(O, Y)
        return s

    wings = {}
    for side, sign, mirror in (("R", 1, False), ("L", -1, True)):
        w = orient(wing.copy(), mirror)
        tongue_c = orient(App.Vector(tcx, tcy, tcz), mirror)
        w.translate(slit_centre(sign, st) - tongue_c)
        wings[side] = w

    return body_p, wings, conns


# ---------------------------------------------------------------------------

def _print_pose(name, shape):
    """The connector is modelled spine-along-X; roll it 90 deg so the spine axis
    stands vertical and a full profile face lies on the bed. Every slit is then a
    vertical channel - no overhang, no bridge, no supports - and the exported STL
    needs no rotation in the slicer. Other parts export as-is (flat plaques
    already on z = 0)."""
    if name != "bird_connector":
        return shape
    s = shape.copy()
    s.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)   # spine X -> vertical
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))      # tuck into the +XYZ octant
    return s


def _export(out_dir, name, shape):
    shape.exportStep(os.path.join(out_dir, name + ".step"))
    shape.exportStl(os.path.join(out_dir, name + ".stl"))
    export_glb(os.path.join(out_dir, name + ".stl"), os.path.join(out_dir, name + ".glb"))
    bb = shape.BoundBox
    print("  %-16s %6.1f x %6.1f x %6.1f mm   vol %8.0f mm^3   solids %d"
          % (name, bb.XLength, bb.YLength, bb.ZLength, shape.Volume, len(shape.Solids)))


def main():
    out_dir = parse_outdir(__file__)
    os.makedirs(out_dir, exist_ok=True)

    doc = App.newDocument("ParametricBird")
    body = build_body()
    wing = build_wing()
    connector = build_connector()

    print("Printable pieces (footprint as exported, for a 350 x 350 Voron plate):")
    for name, shape in (("bird_body", body), ("bird_wing", wing), ("bird_connector", connector)):
        placed = _print_pose(name, shape)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = placed
        _export(out_dir, name, placed)
    print("  (need 2x bird_wing + 1x bird_body + 1x bird_connector on the plate)")
    doc.recompute()

    asm = App.newDocument("ParametricBirdAssembly")
    body_p, wings, conns = _posed(body, wing, connector)
    named = [("Body", body_p), ("Wing_R", wings["R"]), ("Wing_L", wings["L"]),
             ("Connector", conns["main"])]
    for name, shape in named:
        asm.addObject("Part::Feature", name).Shape = shape
    asm.recompute()
    fcstd_path = os.path.join(out_dir, "bird.FCStd")
    asm.saveAs(fcstd_path)

    compound = Part.makeCompound([s for _, s in named])
    bird_stl = os.path.join(out_dir, "bird.stl")
    compound.exportStl(bird_stl)
    export_glb(bird_stl, os.path.join(out_dir, "bird.glb"))

    print("Wrote posed preview:\n  %s\n  %s\n  %s"
          % (fcstd_path, bird_stl, os.path.join(out_dir, "bird.glb")))


if __name__ == "__main__":
    main()
