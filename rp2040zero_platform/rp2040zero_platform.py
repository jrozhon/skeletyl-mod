"""Platform for a Waveshare RP2040-Zero + PJ-320A TRRS jack in a Skeletyl V4
case, replacing the Splinktegrated PCB.

A flat plate screwed from below against the underside of the case's two M4
controller rings. The jack lies on the plate; the RP2040-Zero (components
down) rests on two ledges above it so its USB-C sits in the case slot.

Frame: origin = centre of case ring A, X toward ring B, Y toward the user
(rear wall at negative Y), Z up with Z = 0 on the ring tops. The rings'
free (insert) faces are at Z = -3.75; the bottom plate is at Z = -8.

Run headless:   freecadcmd rp2040zero_platform.py   (exports FCStd/STEP/STL)
Or in FreeCAD:  open as a macro; the part is added to the active document.
"""
import os
import sys

try:  # imported as a package member (tests, check_clearance)
    from . import freecad_path  # noqa: F401  (adds FreeCAD's lib dir to sys.path)
except ImportError:  # run as a script / macro
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import freecad_path  # noqa: F401

import FreeCAD
import Part
from FreeCAD import Vector

# ---------------------------------------------------------------------------
# Case interface (measured from Skeletyl V4 case_v4_103.stl)
# ---------------------------------------------------------------------------
RING_A = (0.0, 0.0)            # controller ring nearer the jack (frame origin)
RING_B = (34.660, -28.267)     # second controller ring
RING_FACE_Z = -3.75            # rings' free face (heat-set insert side), toward the bottom plate
RING_FACE_OD = 10.6            # outer diameter of that face
RING_BORE_D = 5.5              # insert bore
BOTTOM_PLATE_Z = -8.0          # top face of the bottom plate
WALL_OUTER_Y = -36.07          # rear wall outer face
WALL_INNER_Y = -32.0           # rear wall inner face below Z = -5.5 (and above 3.0)
WALL_RECESS_Y = -34.1          # inner face between Z -5.5 and 3.0 (wall thinned to 2 mm for the connectors)
JACK_AXIS_X = 5.10             # case jack hole axis
JACK_HOLE_Z = -1.60            # case jack hole axis height
JACK_HOLE_D = 5.2              # case jack hole through the 2 mm wall (its mouth is chamfered wider)
USB_SLOT_X = (16.09, 25.91)    # case USB slot extents (through the 2 mm wall)
USB_SLOT_Z = (-3.06, 0.56)
RING_B_FLAT_X = 30.93          # case ring B has a flat face toward the board at this X, Y <= -24, Z <= 1
RING_B_FREE_Y = -22.5          # in front of this Y the case is clear right of the board (up to X 38)
# Inner face of the slanted left wall (X as a function of Y) plus the rear
# corner, offset 0.5 mm into the free space; the last point is on the rear
# edge. The plate is clipped to the right of this polyline.
LEFT_EDGE = ((-4.6, 50.0), (-4.6, 0.0), (-3.4, -10.0), (-1.2, -28.3), (-0.1, -30.0), (3.0, -31.6))

# ---------------------------------------------------------------------------
# Plate
# ---------------------------------------------------------------------------
PLATE_T = 2.0                  # plate thickness; top face sits on the ring faces
PLATE_REAR_Y = -31.6           # rear edge (0.4 mm from the wall)
RING_PAD_R = 7.0               # plate radius kept around each ring
RING_A_PAD_Y0 = -10.0          # ring A pad joins the body with a strip from here to the ring centre
SCREW_HOLE_D = 4.5             # M4 clearance
HEAD_D = 8.0                   # screw head diameter
HEAD_H = 2.5                   # screw head height (measured on the kit's M4 x 8 Torx screws)
HEAD_CLEAR = 0.3               # counterbore radial clearance
SEAT_FLOOR_T = 1.2             # plate left under the head (counterbore depth = PLATE_T - this)

# ---------------------------------------------------------------------------
# RP2040-Zero, components down, USB-C toward the rear wall
# ---------------------------------------------------------------------------
BOARD_W = 18.0                 # PCB width (X)
BOARD_L = 23.5                 # PCB length (Y)
BOARD_T = 1.0                  # PCB thickness
USB_W = 8.94                   # USB-C shell width
USB_H = 3.2                    # USB-C shell height (sets the board height: measure yours!)
USB_L = 7.35                   # USB-C shell length
USB_OVERHANG = 1.3             # shell protrudes past the PCB edge by this
USB_RECESS = 1.0               # shell front face this far behind the wall's outer face
BOARD_X_SHIFT = 0.0            # nudge the board sideways relative to the slot
BOARD_Z_SHIFT = 0.0            # nudge the board up/down (the shell has 0.2 mm each way in the slot)
BOARD_CLEAR = 0.3              # side clearance PCB edge -> rail
LEDGE_W = 1.2                  # ledge walls under the long PCB edges (their inner 0.9 mm carry the PCB)
RAIL_T = 1.5                   # rails outside the ledges, and the front stop
RAIL_ABOVE_PCB = 1.0           # rails stand this far above the PCB top (glue here)
WINDOW_INSET = 1.5             # floor window inset from the PCB side edges
WINDOW_FRONT_GAP = 2.0         # floor window ends this far before the PCB front edge

# ---------------------------------------------------------------------------
# PJ-320A TRRS jack, lying in a shallow pocket in the plate top
# ---------------------------------------------------------------------------
JACK_BODY_W = 6.0              # body width (X)
JACK_BODY_L = 12.0             # body length (Y), nose excluded
JACK_BODY_H = 5.0              # body height
JACK_AXIS_H = 2.5              # barrel axis above the mounting face
JACK_NOSE_D = 5.0              # nose (barrel) diameter
JACK_NOSE_L = 2.0              # nose length
JACK_FACE_GAP = 0.2            # body front face to the recessed wall face
JACK_POCKET_CLEAR = 0.2        # pocket clearance per side and behind the body
JACK_LEG_IN = 1.4              # leg slot reaches this far inside each body side face ...
JACK_LEG_OUT = 0.6             # ... and this far outside it (legs may be either)
JACK_LEG_Y0 = 1.0              # leg slot starts this far behind the body front face
JACK_LEG_L = 10.0              # leg slot length (Y)
RIB_T = 1.5                    # jack ribs / end stop thickness
RIB_H = 2.5                    # jack ribs / end stop height above the plate
RIB_L_Y0 = -29.6               # left rib starts here (the left wall is too close further back)
JACK_STOP_GAP = 0.3            # end stop behind the body rear face

# ---------------------------------------------------------------------------
# Derived values (do not edit)
# ---------------------------------------------------------------------------
PLATE_Z1 = RING_FACE_Z                       # plate top on the ring faces
PLATE_Z0 = PLATE_Z1 - PLATE_T                # plate bottom (print bed)
COUNTERBORE_DEPTH = PLATE_T - SEAT_FLOOR_T
HEAD_BOTTOM_Z = PLATE_Z0 + COUNTERBORE_DEPTH - HEAD_H

USB_CENTER_Z = (USB_SLOT_Z[0] + USB_SLOT_Z[1]) / 2.0
USB_Z0 = USB_CENTER_Z - USB_H / 2.0 + BOARD_Z_SHIFT   # shell underside
PCB_Z0 = USB_Z0 + USB_H                      # component side (faces down) = ledge top
PCB_Z1 = PCB_Z0 + BOARD_T                    # flat solder side (faces up)
RAIL_TOP_Z = PCB_Z1 + RAIL_ABOVE_PCB
BOARD_CX = (USB_SLOT_X[0] + USB_SLOT_X[1]) / 2.0 + BOARD_X_SHIFT
BOARD_X0 = BOARD_CX - BOARD_W / 2.0
BOARD_X1 = BOARD_CX + BOARD_W / 2.0
USB_FACE_Y = WALL_OUTER_Y + USB_RECESS
BOARD_Y0 = USB_FACE_Y + USB_OVERHANG         # rear (USB) edge
BOARD_Y1 = BOARD_Y0 + BOARD_L                # front edge
RAIL_X0 = BOARD_X0 - BOARD_CLEAR             # left rail inner face / left ledge outer edge
RAIL_X1 = BOARD_X1 + BOARD_CLEAR             # right rail inner face / right ledge outer edge
STOP_Y0 = BOARD_Y1 + BOARD_CLEAR             # front stop inner face
STOP_Y1 = STOP_Y0 + RAIL_T
PLATE_FRONT_Y = STOP_Y1
PLATE_RIGHT_X = RAIL_X1 + RAIL_T

JACK_X0 = JACK_AXIS_X - JACK_BODY_W / 2.0
JACK_X1 = JACK_AXIS_X + JACK_BODY_W / 2.0
JACK_Y0 = WALL_RECESS_Y + JACK_FACE_GAP      # body front face
JACK_Y1 = JACK_Y0 + JACK_BODY_L              # body rear face
JACK_FLOOR_Z = JACK_HOLE_Z - JACK_AXIS_H     # pocket floor: puts the barrel on the hole axis
JACK_AXIS_Z = JACK_FLOOR_Z + JACK_AXIS_H
JACK_POCKET_Y1 = JACK_Y1 + JACK_POCKET_CLEAR
RIB_TOP_Z = PLATE_Z1 + RIB_H
RIB_L_X0 = JACK_X0 - JACK_LEG_OUT - RIB_T    # left rib, outside the left leg slot
RIB_R_X0 = JACK_X1 + JACK_LEG_OUT            # right rib, outside the right slot ...
RIB_R_X1 = RAIL_X0 - RAIL_T                  # ... merged into the board's left rail
JACK_STOP_Y0 = JACK_Y1 + JACK_STOP_GAP


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box given by its extents (any order per axis)."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def cyl(cx, cy, d, z0, z1):
    """Vertical cylinder of diameter d from z0 to z1 centred on (cx, cy)."""
    z0, z1 = sorted((z0, z1))
    return Part.makeCylinder(d / 2.0, z1 - z0, Vector(cx, cy, z0))


def prism(points, z0, z1):
    """Vertical prism over a closed XY polygon."""
    pts = [Vector(x, y, z0) for x, y in points] + [Vector(points[0][0], points[0][1], z0)]
    return Part.Face(Part.makePolygon(pts)).extrude(Vector(0, 0, z1 - z0))


def fuse_all(shapes):
    shape = shapes[0]
    for s in shapes[1:]:
        shape = shape.fuse(s)
    return shape


# ---------------------------------------------------------------------------
# Plate
# ---------------------------------------------------------------------------
def make_plate():
    """Body + ring pads, clipped along the left wall, with the board window."""
    ax, ay = RING_A
    bx, by = RING_B
    body = box(LEFT_EDGE[0][0], PLATE_RIGHT_X, PLATE_REAR_Y, PLATE_FRONT_Y, PLATE_Z0, PLATE_Z1)
    pad_a = cyl(ax, ay, 2 * RING_PAD_R, PLATE_Z0, PLATE_Z1)
    neck_a = box(LEFT_EDGE[0][0], ax + RING_PAD_R, RING_A_PAD_Y0, ay, PLATE_Z0, PLATE_Z1)
    pad_b = cyl(bx, by, 2 * RING_PAD_R, PLATE_Z0, PLATE_Z1)
    plate = fuse_all([body, pad_a, neck_a, pad_b])
    # Everything right of the left edge and in front of the rear edge.
    keep = prism(LEFT_EDGE + ((100.0, PLATE_REAR_Y), (100.0, 50.0)), PLATE_Z0 - 1, PLATE_Z1 + 1)
    return plate.common(keep).cut(make_window())


def make_window():
    """Floor window under the board, open toward the rear edge."""
    return box(BOARD_X0 + WINDOW_INSET, BOARD_X1 - WINDOW_INSET,
               PLATE_REAR_Y - 1.0, BOARD_Y1 - WINDOW_FRONT_GAP, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0)


def make_screw_cutters():
    """M4 through hole plus the counterbore for the head, from below."""
    cutters = []
    for cx, cy in (RING_A, RING_B):
        cutters.append(cyl(cx, cy, SCREW_HOLE_D, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0))
        cutters.append(cyl(cx, cy, HEAD_D + 2 * HEAD_CLEAR, PLATE_Z0 - 1.0, PLATE_Z0 + COUNTERBORE_DEPTH))
    return fuse_all(cutters)


# ---------------------------------------------------------------------------
# Board frame
# ---------------------------------------------------------------------------
def make_board_frame():
    """Ledges under the long PCB edges, rails outside them, front stop."""
    return fuse_all([
        box(RAIL_X0, RAIL_X0 + LEDGE_W, PLATE_REAR_Y, STOP_Y0, PLATE_Z0, PCB_Z0),
        box(RAIL_X1 - LEDGE_W, RAIL_X1, PLATE_REAR_Y, STOP_Y0, PLATE_Z0, PCB_Z0),
        box(RAIL_X0 - RAIL_T, RAIL_X0, PLATE_REAR_Y, STOP_Y1, PLATE_Z0, RAIL_TOP_Z),
        box(RAIL_X1, RAIL_X1 + RAIL_T, RING_B_FREE_Y, STOP_Y1, PLATE_Z0, RAIL_TOP_Z),
        box(RAIL_X0 - RAIL_T, RAIL_X1 + RAIL_T, STOP_Y0, STOP_Y1, PLATE_Z0, RAIL_TOP_Z),
    ])


# ---------------------------------------------------------------------------
# Jack pocket
# ---------------------------------------------------------------------------
def make_jack_ribs():
    """Side ribs outside the leg slots and the end stop behind the body."""
    return fuse_all([
        box(RIB_L_X0, RIB_L_X0 + RIB_T, RIB_L_Y0, JACK_STOP_Y0 + RIB_T, PLATE_Z0, RIB_TOP_Z),
        box(RIB_R_X0, RIB_R_X1, PLATE_REAR_Y, JACK_STOP_Y0 + RIB_T, PLATE_Z0, RIB_TOP_Z),
        box(RIB_L_X0, RIB_R_X1, JACK_STOP_Y0, JACK_STOP_Y0 + RIB_T, PLATE_Z0, RIB_TOP_Z),
    ])


def make_jack_pocket():
    """Shallow pocket in the plate top: sets the jack height, guides the body."""
    return box(JACK_X0 - JACK_POCKET_CLEAR, JACK_X1 + JACK_POCKET_CLEAR,
               PLATE_REAR_Y - 1.0, JACK_POCKET_Y1, JACK_FLOOR_Z, PLATE_Z1 + 1.0)


def make_leg_slots():
    """One slot through the plate along each body side, open at the rear."""
    y0 = JACK_Y0 + JACK_LEG_Y0
    return fuse_all([
        box(JACK_X0 - JACK_LEG_OUT, JACK_X0 + JACK_LEG_IN, PLATE_REAR_Y - 1.0, y0 + JACK_LEG_L,
            PLATE_Z0 - 1.0, PLATE_Z1 + 1.0),
        box(JACK_X1 - JACK_LEG_IN, JACK_X1 + JACK_LEG_OUT, PLATE_REAR_Y - 1.0, y0 + JACK_LEG_L,
            PLATE_Z0 - 1.0, PLATE_Z1 + 1.0),
    ])


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    """Return the finished platform as a single solid."""
    shape = make_plate().fuse(make_board_frame()).fuse(make_jack_ribs())
    shape = shape.cut(make_jack_pocket()).cut(make_leg_slots()).cut(make_screw_cutters())
    return shape.removeSplitter()


def make_components():
    """The parts the platform holds, as one compound (for checks and drawings):
    PCB, USB-C shell, jack body and nose, at their design positions."""
    nose = Part.makeCylinder(JACK_NOSE_D / 2.0, JACK_NOSE_L, Vector(JACK_AXIS_X, JACK_Y0, JACK_AXIS_Z),
                             Vector(0, -1, 0))
    return Part.makeCompound([
        box(BOARD_X0, BOARD_X1, BOARD_Y0, BOARD_Y1, PCB_Z0, PCB_Z1),
        box(BOARD_CX - USB_W / 2, BOARD_CX + USB_W / 2, USB_FACE_Y, USB_FACE_Y + USB_L, USB_Z0, PCB_Z0),
        box(JACK_X0, JACK_X1, JACK_Y0, JACK_Y1, JACK_FLOOR_Z, JACK_FLOOR_Z + JACK_BODY_H),
        nose,
    ])


# ---------------------------------------------------------------------------
# Export / entry points
# ---------------------------------------------------------------------------
NAME = "rp2040zero_platform"


def export(shape, out_dir):
    """Write FCStd, STEP and STL for `shape` into out_dir; return the paths."""
    import MeshPart

    os.makedirs(out_dir, exist_ok=True)
    paths = {
        'fcstd': os.path.join(out_dir, NAME + ".FCStd"),
        'step': os.path.join(out_dir, NAME + ".step"),
        'stl': os.path.join(out_dir, NAME + ".stl"),
    }
    doc = FreeCAD.newDocument(NAME)
    obj = doc.addObject("Part::Feature", "Platform")
    obj.Shape = shape
    doc.recompute()
    doc.saveAs(paths['fcstd'])
    shape.exportStep(paths['step'])
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1)
    mesh.write(paths['stl'])
    FreeCAD.closeDocument(doc.Name)
    return paths


def main():
    shape = build()
    print("valid:", shape.isValid(), "solids:", len(shape.Solids),
          "volume mm^3: %.1f" % shape.Volume)
    bb = shape.BoundBox
    print("bbox X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f"
          % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    print("USB-C shell Z %.2f..%.2f in slot %.2f..%.2f; jack pocket %.2f deep; head bottom Z %.2f (bottom plate %.2f)"
          % (USB_Z0, PCB_Z0, USB_SLOT_Z[0], USB_SLOT_Z[1], PLATE_Z1 - JACK_FLOOR_Z, HEAD_BOTTOM_Z, BOTTOM_PLATE_Z))
    if FreeCAD.GuiUp:
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument(NAME)
        obj = doc.addObject("Part::Feature", "Platform")
        obj.Shape = shape
        doc.recompute()
    else:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        for kind, path in export(shape, out_dir).items():
            print("wrote", kind, path)


def _run_as_script():
    """True when executed directly (`python3 file.py`, GUI macro) or via
    `freecadcmd file.py`, which runs the file with __name__ set to its
    basename instead of "__main__"."""
    if __name__ == "__main__":
        return True
    argv = sys.argv
    return (len(argv) > 1
            and os.path.basename(argv[0]).lower().startswith("freecad")
            and os.path.abspath(argv[-1]) == os.path.abspath(__file__))


if _run_as_script():
    main()
