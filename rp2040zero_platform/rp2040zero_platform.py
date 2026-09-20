"""Platform for a Waveshare RP2040-Zero + PJ-320A TRRS jack in a Skeletyl V4
case, replacing the Splinktegrated PCB.

Frame: origin = centre of case ring A, X toward ring B, Y toward the user
(rear wall at negative Y), Z up with Z = 0 on the ring tops.

Run headless:   freecadcmd rp2040zero_platform.py   (exports FCStd/STEP/STL)
Or in FreeCAD:  open as a macro; the part is added to the active document.
"""
import math
import os

try:  # imported as a package member (tests, check_clearance)
    from . import freecad_path  # noqa: F401  (adds FreeCAD's lib dir to sys.path)
    from .outline_kicad import H1, H2, OUTLINE_KICAD
except ImportError:  # run as a script / macro: import siblings by path
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import freecad_path  # noqa: F401
    from outline_kicad import H1, H2, OUTLINE_KICAD

import FreeCAD
import Part
from FreeCAD import Vector

# ---------------------------------------------------------------------------
# Case interface (measured from Skeletyl V4 case_v4_103.stl)
# ---------------------------------------------------------------------------
RING_A = (0.0, 0.0)            # controller ring nearer the jack (frame origin)
RING_B = (34.660, -28.267)     # second controller ring
RING_OD = 10.0                 # case ring outer diameter
RING_H = 3.75                  # rings hang from Z = -RING_H to 0
WALL_INNER_Y = -31.8           # rear wall inner face
JACK_AXIS_X = 5.0              # case jack hole axis
JACK_HOLE_Z = -1.22            # case jack hole axis height
USB_SLOT_X = (15.64, 26.47)    # case USB slot extents
USB_SLOT_Z = (-3.06, 4.0)      # case USB slot extents

# ---------------------------------------------------------------------------
# Base plate
# ---------------------------------------------------------------------------
PLATE_Z0 = -4.0                # plate bottom
PLATE_Z1 = -2.0                # plate top
PLATE_REAR_Y = -31.3           # outline trimmed here (0.5 mm from the wall)

# ---------------------------------------------------------------------------
# Ring pockets (slip over the case rings, M4 screw from above into insert)
# ---------------------------------------------------------------------------
POCKET_BORE_D = 10.4           # bore around the Ø10 ring
POCKET_OD = 12.8               # pocket outer diameter
CAP_TOP_Z = 2.0                # top of the screw cap (cap is Z 0..CAP_TOP_Z)
SCREW_HOLE_D = 4.5             # M4 clearance

# ---------------------------------------------------------------------------
# RP2040-Zero, mounted components down, USB-C toward the rear wall
# ---------------------------------------------------------------------------
BOARD_W = 18.0                 # PCB width (X)
BOARD_L = 23.5                 # PCB length (Y)
BOARD_T = 1.0                  # PCB thickness
USB_W = 8.94                   # USB-C shell width
USB_H = 3.2                    # USB-C shell height (sets the board height!)
USB_L = 7.35                   # USB-C shell length
USB_OVERHANG = 1.3             # shell protrudes past the PCB edge by this
USB_INTO_WALL = 1.0            # shell front face goes this far into the slot
BOARD_X_SHIFT = 0.0            # nudge the board sideways relative to the slot
BOARD_CLEAR = 0.4              # side clearance PCB edge -> rail
RAIL_T = 1.5                   # rail / end-stop thickness
RAIL_TOP_Z = 4.5               # rails and end-stop top
CRADLE_W = 6.0                 # block under the USB-C shell (X)
CRADLE_L = 4.0                 # block under the USB-C shell (Y, from rear edge)
SEAT_W = 3.0                   # corner seats under the far PCB corners (X)
SEAT_L = 1.0                   # corner seats (Y)
WINDOW_INSET_X = 0.45          # floor window inset from the PCB side edges
WINDOW_REAR_GAP = 2.0          # floor window starts this far from the PCB rear edge
WINDOW_FRONT_GAP = 1.5         # floor window ends this far from the PCB front edge
CAP_RELIEF = 0.6               # ring cap lowered to PCB underside minus this, under the board
ZIP_SLOT_W = 2.0               # zip-tie slot width (X), directly outside the PCB edge
ZIP_SLOT_L = 5.0               # zip-tie slot length (Y)
ZIP_SLOT_Y0 = (-21.0, -14.0)   # Y start of each slot pair (kept clear of ring B's pocket)

# ---------------------------------------------------------------------------
# PJ-320A TRRS jack
# ---------------------------------------------------------------------------
JACK_BODY_W = 6.0              # body width (X)
JACK_BODY_L = 12.0             # body length (Y), nose excluded
JACK_BODY_H = 5.0              # body height
JACK_AXIS_H = 2.5              # barrel axis above the mounting face
JACK_CLEAR_SIDE = 0.2          # pocket clearance per side
JACK_CLEAR_LEN = 0.3           # pocket clearance in length
JACK_WALL_T = 1.5              # pocket wall thickness
JACK_FLOOR_T = 1.5             # shelf thickness under the jack
JACK_FACE_GAP = 0.2            # body front face to wall inner face
JACK_LEG_INSET = 0.8           # leg row inboard of the body side face
JACK_LEG_SLOT_W = 1.6          # leg slot width (X), one on each side
JACK_LEG_SLOT_L = 10.0         # leg slot length (Y)
JACK_LEG_SLOT_START = 1.0      # leg slot starts this far behind the body front face

# ---------------------------------------------------------------------------
# Derived values (do not edit)
# ---------------------------------------------------------------------------
_DELTA = math.atan2(RING_B[1], RING_B[0]) - math.atan2(H2[1] - H1[1], H2[0] - H1[0])


def kicad_to_local(p):
    """Map a KiCad (x, y) point of the Splinktegrated onto the platform frame."""
    x, y = p[0] - H1[0], p[1] - H1[1]
    c, s = math.cos(_DELTA), math.sin(_DELTA)
    return (x * c - y * s, x * s + y * c)


# Board placement derived from the USB slot: the connector centre sits on the
# slot centre; with the board upside down the PCB is USB_H above the shell.
USB_CENTER_Z = (USB_SLOT_Z[0] + USB_SLOT_Z[1]) / 2.0
USB_BOTTOM_Z = USB_CENTER_Z - USB_H / 2.0
PCB_BOTTOM_Z = USB_BOTTOM_Z + USB_H          # component side (faces down)
PCB_TOP_Z = PCB_BOTTOM_Z + BOARD_T           # flat solder side (faces up)
BOARD_CX = (USB_SLOT_X[0] + USB_SLOT_X[1]) / 2.0 + BOARD_X_SHIFT
BOARD_X0 = BOARD_CX - BOARD_W / 2.0
BOARD_X1 = BOARD_CX + BOARD_W / 2.0
BOARD_Y0 = WALL_INNER_Y - USB_INTO_WALL + USB_OVERHANG   # rear (USB) edge
BOARD_Y1 = BOARD_Y0 + BOARD_L                            # front edge
RAIL_X0 = BOARD_X0 - BOARD_CLEAR             # inner face of the left rail
RAIL_X1 = BOARD_X1 + BOARD_CLEAR             # inner face of the right rail

# Jack placement derived from the case hole: the jack sits on a shelf
# JACK_AXIS_H below the hole axis, body face JACK_FACE_GAP from the wall.
JACK_SHELF_Z = JACK_HOLE_Z - JACK_AXIS_H
JACK_BLOCK_Z0 = JACK_SHELF_Z - JACK_FLOOR_T
JACK_WALL_TOP_Z = JACK_SHELF_Z + JACK_BODY_H
JACK_X0 = JACK_AXIS_X - JACK_BODY_W / 2.0
JACK_X1 = JACK_AXIS_X + JACK_BODY_W / 2.0
JACK_Y0 = WALL_INNER_Y + JACK_FACE_GAP       # body front face (toward the wall)
JACK_Y1 = JACK_Y0 + JACK_BODY_L              # body rear face

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


# ---------------------------------------------------------------------------
# Base plate
# ---------------------------------------------------------------------------
def make_outline_face():
    """Splinktegrated head + neck outline as a planar face at Z = 0."""
    def v(p):
        x, y = kicad_to_local(p)
        return Vector(x, y, 0.0)

    edges = []
    prev_end = None
    for kind, start, mid, end in OUTLINE_KICAD:
        a = prev_end if prev_end is not None else v(start)  # snap tiny gaps
        b = v(end)
        if kind == 'line':
            edges.append(Part.LineSegment(a, b).toShape())
        else:
            edges.append(Part.Arc(a, v(mid), b).toShape())
        prev_end = b
    # Close along the daughterboard snap-off line.
    edges.append(Part.LineSegment(prev_end, edges[0].Vertexes[0].Point).toShape())
    wire = Part.Wire(edges)
    if not wire.isClosed():
        raise RuntimeError("outline wire is not closed")
    return Part.Face(wire)


def make_plate():
    """Outline extruded to the plate thickness and trimmed at the rear."""
    face = make_outline_face()
    face.translate(Vector(0, 0, PLATE_Z0))
    plate = face.extrude(Vector(0, 0, PLATE_Z1 - PLATE_Z0))
    keep = box(-100, 100, PLATE_REAR_Y, 100, PLATE_Z0 - 1, PLATE_Z1 + 1)
    return plate.common(keep)


# ---------------------------------------------------------------------------
# Ring pockets
# ---------------------------------------------------------------------------
RING_CENTRES = (RING_A, RING_B)


def make_ring_pocket_outer(cx, cy):
    """Solid boss that slips over a case ring; bore and hole are cut later."""
    return cyl(cx, cy, POCKET_OD, PLATE_Z0, CAP_TOP_Z)


def make_ring_cutters(cx, cy):
    """Bore for the case ring (open at the bottom) plus the M4 screw hole."""
    bore = cyl(cx, cy, POCKET_BORE_D, PLATE_Z0 - 1.0, 0.0)
    hole = cyl(cx, cy, SCREW_HOLE_D, -1.0, CAP_TOP_Z + 1.0)
    return bore.fuse(hole)


# ---------------------------------------------------------------------------
# RP2040-Zero pocket
# ---------------------------------------------------------------------------
def make_board_additions():
    """Rails, front end-stop, USB-C cradle and the two far corner seats."""
    stop_y0 = BOARD_Y1 + BOARD_CLEAR
    stop_y1 = stop_y0 + RAIL_T
    parts = [
        box(RAIL_X0 - RAIL_T, RAIL_X0, PLATE_REAR_Y, stop_y1, PLATE_Z0, RAIL_TOP_Z),
        box(RAIL_X1, RAIL_X1 + RAIL_T, PLATE_REAR_Y, stop_y1, PLATE_Z0, RAIL_TOP_Z),
        box(RAIL_X0 - RAIL_T, RAIL_X1 + RAIL_T, stop_y0, stop_y1, PLATE_Z0, RAIL_TOP_Z),
        # Cradle: the USB-C shell rests on this and sets the connector height.
        box(BOARD_CX - CRADLE_W / 2, BOARD_CX + CRADLE_W / 2,
            PLATE_REAR_Y, PLATE_REAR_Y + CRADLE_L, PLATE_Z0, USB_BOTTOM_Z),
        # Corner seats under the pad-free far corners of the PCB.
        box(BOARD_X0, BOARD_X0 + SEAT_W, BOARD_Y1 - SEAT_L, BOARD_Y1, PLATE_Z0, PCB_BOTTOM_Z),
        box(BOARD_X1 - SEAT_W, BOARD_X1, BOARD_Y1 - SEAT_L, BOARD_Y1, PLATE_Z0, PCB_BOTTOM_Z),
    ]
    shape = parts[0]
    for p in parts[1:]:
        shape = shape.fuse(p)
    return shape


def make_window():
    """Floor window under the board (button access, component clearance)."""
    return box(BOARD_X0 + WINDOW_INSET_X, BOARD_X1 - WINDOW_INSET_X,
               BOARD_Y0 + WINDOW_REAR_GAP, BOARD_Y1 - WINDOW_FRONT_GAP,
               PLATE_Z0 - 1.0, PLATE_Z1 + 1.0)


def make_zip_slots():
    """Zip-tie slots just outside the PCB edges, through plate and rails."""
    shape = None
    for y0 in ZIP_SLOT_Y0:
        for x0 in (BOARD_X0 - ZIP_SLOT_W, BOARD_X1):
            slot = box(x0, x0 + ZIP_SLOT_W, y0, y0 + ZIP_SLOT_L,
                       PLATE_Z0 - 1.0, RAIL_TOP_Z + 1.0)
            shape = slot if shape is None else shape.fuse(slot)
    return shape


def make_board_cutters():
    """Window + zip-tie slots (convenience; build() applies them separately)."""
    return make_window().fuse(make_zip_slots())


def make_cap_relief():
    """Volume above the board-pocket footprint that ring caps must not enter."""
    return box(RAIL_X0, RAIL_X1, PLATE_REAR_Y - 1.0, BOARD_Y1 + 1.0,
               PCB_BOTTOM_Z - CAP_RELIEF, CAP_TOP_Z + 1.0)


# ---------------------------------------------------------------------------
# PJ-320A jack pocket
# ---------------------------------------------------------------------------
def make_jack_block():
    """Solid block for the jack: shelf, two side walls and the end stop."""
    x0 = JACK_X0 - JACK_CLEAR_SIDE - JACK_WALL_T
    x1 = JACK_X1 + JACK_CLEAR_SIDE + JACK_WALL_T
    y1 = JACK_Y1 + JACK_CLEAR_LEN + JACK_WALL_T
    return box(x0, x1, PLATE_REAR_Y, y1, JACK_BLOCK_Z0, JACK_WALL_TOP_Z)


def make_jack_cutters():
    """Body cavity (open toward the wall) and one leg slot on each side."""
    cavity = box(JACK_X0 - JACK_CLEAR_SIDE, JACK_X1 + JACK_CLEAR_SIDE,
                 PLATE_REAR_Y - 1.0, JACK_Y1 + JACK_CLEAR_LEN,
                 JACK_SHELF_Z, JACK_WALL_TOP_Z + 1.0)
    y0 = JACK_Y0 + JACK_LEG_SLOT_START
    slots = None
    for xc in (JACK_X0 + JACK_LEG_INSET, JACK_X1 - JACK_LEG_INSET):
        slot = box(xc - JACK_LEG_SLOT_W / 2, xc + JACK_LEG_SLOT_W / 2,
                   y0, y0 + JACK_LEG_SLOT_L, JACK_BLOCK_Z0 - 1.0, JACK_SHELF_Z + 0.5)
        slots = slot if slots is None else slots.fuse(slot)
    return cavity.fuse(slots)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    """Return the finished platform as a single solid."""
    shape = make_plate().cut(make_window())
    relief = make_cap_relief()
    for cx, cy in RING_CENTRES:
        shape = shape.fuse(make_ring_pocket_outer(cx, cy).cut(relief))
    shape = shape.fuse(make_board_additions())
    shape = shape.fuse(make_jack_block()).cut(make_jack_cutters())
    shape = shape.cut(make_zip_slots())
    # Cut ring bores and screw holes last: anything fused over a ring must
    # stay open where the case ring sits.
    for cx, cy in RING_CENTRES:
        shape = shape.cut(make_ring_cutters(cx, cy))
    return shape.removeSplitter()
