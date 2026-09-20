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
# Assembly
# ---------------------------------------------------------------------------
def build():
    """Return the finished platform as a single solid."""
    return make_plate()
