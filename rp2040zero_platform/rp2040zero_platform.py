"""Platform for a Waveshare RP2040-Zero + a mid-mount USB-C breakout (the
half-to-half serial link) in a Skeletyl V4 case, replacing the Splinktegrated
PCB. The case's TRRS hole is replaced by a USB-C slot: see case_usb_serial.py.

A flat plate screwed from below against the underside of the case's two M4
controller rings. The RP2040-Zero (components down) rests on two ledges so
its USB-C sits in the case slot, held by a rigid lip and a snap hook; the
breakout's shell sits on a low pedestal in the new slot, its tail in a
glue pocket.

Frame: origin = centre of case ring A, X toward ring B, Y toward the user
(rear wall at negative Y), Z up with Z = 0 on the ring tops. The rings'
free (insert) faces are at Z = -3.75; the bottom plate is at Z = -8.

Run headless:   freecadcmd rp2040zero_platform.py   (exports FCStd/STEP/STL)
Or in FreeCAD:  open as a macro; the part is added to the active document.
"""
import math
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
JACK_AXIS_X = 5.10             # old TRRS jack hole axis (filled by case_usb_serial.py)
JACK_HOLE_Z = -1.60            # old jack hole axis height
JACK_HOLE_D = 5.2              # old jack hole through the 2 mm wall (its mouth is chamfered to ~6.4)
USB_SLOT_X = (16.09, 25.91)    # case USB slot extents (through the 2 mm wall)
USB_SLOT_Z = (-3.06, 0.56)
CORNER_LUMP_X = 1.60           # rear-left corner: case material up to this X for Y -34..-32, Z >= -1.5
SER_SLOT_CX = 6.60             # USB-C serial slot cut by case_usb_serial.py in place of the jack hole
SER_SLOT_W = USB_SLOT_X[1] - USB_SLOT_X[0]   # same stadium as the RP2040 slot: 9.82 x 3.62
SER_SLOT_X = (SER_SLOT_CX - SER_SLOT_W / 2.0, SER_SLOT_CX + SER_SLOT_W / 2.0)
SER_SLOT_Z = USB_SLOT_Z
RING_B_FLAT_X = 30.93          # case ring B has a flat face toward the board at this X, Y <= -24, Z <= 1
RING_B_FREE_Y = -22.5          # in front of this Y the case is clear right of the board (up to X 38)
RING_B_HOOK_Y = RING_B[1] + RING_FACE_OD / 2.0   # ring B's front-most point (-22.97); in front of it the case is
RING_B_HOOK_X = 38.9           # clear right of the board up to this X, at every height (probed 2026-10-03)
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
HEAD_D = 8.0                   # countersunk (conical) head diameter
HEAD_H = 2.5                   # head height (measured on the kit's M4 x 8 Torx screws)
CSK_ANGLE = 90.0               # countersink included angle (ISO countersunk heads are 90 deg)
CSK_DEPTH = 1.2                # countersink depth; a full-depth seat would not fit the 2 mm plate

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
BOARD_CLEAR = 0.3              # PCB side/front edge -> ledge outer edge / ledge end
LEDGE_W = 1.2                  # ledge walls under the long PCB edges (their inner 0.9 mm carry the PCB)
PLATE_MARGIN = 1.5             # plate beyond the right ledge and in front of the ledges (rev. 2 outline)
CORNER_GAP = 0.2               # PCB front/side edge -> corner stop
CORNER_T = 2.5                 # corner stop arm thickness (takes the cable's push)
CORNER_REACH = 2.5             # front arm reaches this far in from each PCB side edge
CORNER_SIDE_L = 3.0            # side arm runs this far back from the PCB front edge
CORNER_ABOVE_PCB = 0.5         # stops stand this far above the PCB top (drop-in lip, glue here)
WINDOW_INSET = 1.5             # floor window inset from the PCB side edges
WINDOW_FRONT_GAP = 2.0         # floor window ends this far before the PCB front edge
BAND_W = 4.0                   # band across the window's rear end, under the USB-C shell: ties the two sides together

# ---------------------------------------------------------------------------
# USB-C serial breakout: mid-mount receptacle, PCB through the shell's middle
# ---------------------------------------------------------------------------
SER_W = 8.94                   # shell width (X)
SER_H = 3.2                    # shell height (the slot is 3.62: 0.21 mm each way)
SER_L = 14.0                   # overall length, shell face to PCB end (caliper, rev. 4; the datasheet says 14.6)
SER_SHELL_L = 8.5              # shell + the leads/body bump behind it, as long as the pedestal (caliper)
SER_PCB_W = 8.9                # breakout PCB width (caliper: just under 9.0; the datasheet 9.8 printed loose)
SER_PCB_T = 0.8                # PCB thickness
SER_RECESS = 0.8               # shell front face this far behind the wall's outer face (1.0 sat too deep)
BOARD_SIDE_GAP = 0.1           # RP2040 PCB left edge -> the middle wall

# ---------------------------------------------------------------------------
# Rev. 4: lips, middle wall and glue pocket (the breakout is mounted back
# side up: wire pads up at the tail end, leads and the SMD part facing down)
# ---------------------------------------------------------------------------
LIP_OVER = 0.5                 # the rigid lips reach this far over a PCB edge
LIP_GAP = 0.1                  # lip underside above the PCB top
MID_WALL_TOP_Z = 4.0           # top of the middle wall and its RP2040 lip (2.55 thick; the case is clear to Z 12 above)
SHELL_WALL_T = 1.2             # left side wall beside the serial shell
SHELL_WALL_GAP = 0.15          # shell -> left side wall (line-to-line made the breakout hard to put in)
SHELL_WALL_Y0 = -30.4          # it starts here: further back the plate outline (case corner) clips it to a sliver
POCKET_WALL_T = 1.2            # glue pocket left wall and the trough's back wall
RIB_T = 1.2                    # glue rib behind the tail end: the glue on top wraps over it into the trough
TROUGH_L = 2.0                 # glue trough behind the rib (Y)
ZERO_PAD1_Y = 2.38             # USB-end PCB edge -> pad 1 centre along the long edges (user: pad 4 at ~10 mm)
ZERO_PAD_PITCH = 2.54
ZERO_LIP_PADS = (3, 5)         # the left lip covers pads 3-5: GP2-GP4 (right half), 3V3/GP29/GP28 (left half),
                               # all free in the hand-wired build (pad 3 is RGB DIN/VCC in the flex build)
ZERO_LIP_MARGIN = 1.0          # ... and this much past them
                               # (GP3/GP4 on the right; the Zero is not mirrored, so GP29/GP28 on the left)
# The snap hook is a solid head (the catch) on the free end of a horizontal
# leaf spring. Both stand on the bed in a slot through the plate. The leaf
# runs forward outside the front-right corner stop to its root near the
# plate's front edge. It flexes outward in X, so it bends along its printed
# lines, not across the layers (rev. 4's upright arm, and then a 1.2 column
# on a leaf, snapped along a layer). The head is rigid: nothing thin stands
# up. The leaf stays below the PCB, so the right-edge wires are free.
HOOK_T = 1.6                   # leaf thickness (X): four 0.4 lines
HOOK_W = 2.4                   # head length (Y), ending with the left lip over pads 4-5 (GP29/GP28, no wires);
                               # it starts 0.3 in front of ring B (RING_B_HOOK_Y)
HOOK_LIP = 0.7                 # catch reach over the PCB edge = how far the head moves aside (>= 0.6 grip with the board's play)
HOOK_LAND = 0.4                # vertical face at the lip's tip (two 0.2 layers) before the ramp starts
HOOK_GAP = 0.4                 # head -> right ledge, leaf -> corner stop, and the slot's margin past the travel
HOOK_SLOT_M = 1.7              # plate strip outside the slot (closes a frame around it; the case is free below the rings)

# ---------------------------------------------------------------------------
# Derived values (do not edit)
# ---------------------------------------------------------------------------
PLATE_Z1 = RING_FACE_Z                       # plate top on the ring faces
PLATE_Z0 = PLATE_Z1 - PLATE_T                # plate bottom (print bed)
CSK_D = SCREW_HOLE_D + 2 * CSK_DEPTH * math.tan(math.radians(CSK_ANGLE / 2))   # at the underside
# Worst case: the head's narrow end sits no deeper than the top of the cone,
# so the head hangs at most HEAD_H - CSK_DEPTH below the plate.
HEAD_BOTTOM_Z = PLATE_Z0 + CSK_DEPTH - HEAD_H

USB_CENTER_Z = (USB_SLOT_Z[0] + USB_SLOT_Z[1]) / 2.0
USB_Z0 = USB_CENTER_Z - USB_H / 2.0 + BOARD_Z_SHIFT   # shell underside
PCB_Z0 = USB_Z0 + USB_H                      # component side (faces down) = ledge top
PCB_Z1 = PCB_Z0 + BOARD_T                    # flat solder side (faces up)
BOARD_CX = (USB_SLOT_X[0] + USB_SLOT_X[1]) / 2.0 + BOARD_X_SHIFT
BOARD_X0 = BOARD_CX - BOARD_W / 2.0
BOARD_X1 = BOARD_CX + BOARD_W / 2.0
USB_FACE_Y = WALL_OUTER_Y + USB_RECESS
BOARD_Y0 = USB_FACE_Y + USB_OVERHANG         # rear (USB) edge
BOARD_Y1 = BOARD_Y0 + BOARD_L                # front edge


def zero_pad_y(k):
    """Y of pad k (1 at the USB end) along the RP2040-Zero's long edges."""
    return BOARD_Y0 + ZERO_PAD1_Y + (k - 1) * ZERO_PAD_PITCH


LEDGE_X0 = BOARD_X0 - BOARD_CLEAR            # left ledge outer edge
LEDGE_X1 = BOARD_X1 + BOARD_CLEAR            # right ledge outer edge
LEDGE_Y1 = BOARD_Y1 + BOARD_CLEAR            # ledges end here
CORNER_Y0 = BOARD_Y1 + CORNER_GAP            # front arms' inner face
CORNER_Y1 = CORNER_Y0 + CORNER_T
CORNER_TOP_Z = PCB_Z1 + CORNER_ABOVE_PCB
PLATE_FRONT_Y = LEDGE_Y1 + PLATE_MARGIN
PLATE_RIGHT_X = LEDGE_X1 + PLATE_MARGIN

SER_CX = SER_SLOT_CX
SER_CZ = (SER_SLOT_Z[0] + SER_SLOT_Z[1]) / 2.0
SER_X0 = SER_CX - SER_W / 2.0
SER_X1 = SER_CX + SER_W / 2.0
SER_Z0 = SER_CZ - SER_H / 2.0                # shell underside = pedestal top
SER_FACE_Y = WALL_OUTER_Y + SER_RECESS       # shell front face
SER_SHELL_Y1 = SER_FACE_Y + SER_SHELL_L      # shell rear = pedestal front
SER_PCB_Y1 = SER_FACE_Y + SER_L              # end of the PCB tail (pads U, D+, D-, G)
SER_PCB_X0 = SER_CX - SER_PCB_W / 2.0
SER_PCB_X1 = SER_CX + SER_PCB_W / 2.0
SER_STOP_Y0 = SER_PCB_Y1 + CORNER_GAP        # stops behind the PCB end
RIB_Y1 = SER_STOP_Y0 + RIB_T
TROUGH_Y1 = RIB_Y1 + TROUGH_L
POCKET_Y1 = TROUGH_Y1 + POCKET_WALL_T        # back of the trough's back wall
SER_STOP_TOP_Z = SER_CZ + SER_PCB_T / 2.0 + CORNER_ABOVE_PCB
BOARD_STOP_X = BOARD_X0 - BOARD_SIDE_GAP     # right serial stop's face against the RP2040's left edge
SER_TAIL_Z0 = SER_CZ - SER_PCB_T / 2.0       # tail underside (the photo side, now facing down)
SER_TAIL_Z1 = SER_CZ + SER_PCB_T / 2.0       # tail top (wire pads)
MID_X0 = SER_X1                              # middle wall: right side wall of the shell and the tail ...
MID_X1 = BOARD_STOP_X                        # ... and BOARD_SIDE_GAP off the RP2040's left edge
LIP_Z0 = PCB_Z1 + LIP_GAP                    # underside of the RP2040 lip and the hook
ZERO_LIP_X1 = BOARD_X0 + LIP_OVER
ZERO_LIP_Y0 = zero_pad_y(ZERO_LIP_PADS[0]) - ZERO_LIP_MARGIN
ZERO_LIP_Y1 = zero_pad_y(ZERO_LIP_PADS[1]) + ZERO_LIP_MARGIN
MID_Y1 = ZERO_LIP_Y1                         # the middle wall ends with the RP2040 lip
HOOK_Y1 = ZERO_LIP_Y1                        # clear of GP27 (pad 6) like the left lip
HOOK_Y0 = HOOK_Y1 - HOOK_W
HOOK_YC = (HOOK_Y0 + HOOK_Y1) / 2.0
HOOK_X0 = LEDGE_X1 + HOOK_GAP                # head inner face
LEAF_X0 = BOARD_X1 + CORNER_GAP + CORNER_T + HOOK_GAP   # leaf inner face, outside the corner stop's side arm
LEAF_X1 = LEAF_X0 + HOOK_T
HOOK_X1 = LEAF_X1                            # head and leaf outer face
HOOK_TIP_X = BOARD_X1 - HOOK_LIP
HOOK_TOP_Z = LIP_Z0 + HOOK_LAND + (LEDGE_X1 - HOOK_TIP_X)   # 45 deg ramp from the land to the catch
LEAF_ROOT_Y = CORNER_Y1 + 0.3                # the leaf is rooted in the plate here, past the corner stop
LEAF_TOP_Z = PCB_Z0                          # leaf top: the ledge height, below the PCB
SLOT_X0 = LEDGE_X1                           # slot through the plate around the head and the leaf
SLOT_X1 = HOOK_X1 + HOOK_LIP + HOOK_GAP      # room for the full travel outward, plus HOOK_GAP
SLOT_Y0 = HOOK_Y0 - HOOK_GAP
HOOK_PLATE_X1 = SLOT_X1 + HOOK_SLOT_M        # plate widened to here along the slot
POCKET_X0 = SER_PCB_X0 - CORNER_GAP          # glue pocket left wall, inner face
LAYER_H = 0.2                                # print layer height
RIB_TOP_Z = SER_TAIL_Z1 - LAYER_H            # rib a layer under the tail top: the wires lie flat over it
TROUGH_FLOOR_Z = RIB_TOP_Z - 1.6             # trough 1.6 deep below the rib top
SHELL_WALL_X1 = SER_X0 - SHELL_WALL_GAP      # left side wall's inner face

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


def prism_xz(points, y0, y1):
    """Prism over a closed XZ polygon, from y0 to y1."""
    pts = [Vector(x, y0, z) for x, z in points] + [Vector(points[0][0], y0, points[0][1])]
    return Part.Face(Part.makePolygon(pts)).extrude(Vector(0, y1 - y0, 0))


def fuse_all(shapes):
    shape = shapes[0]
    for s in shapes[1:]:
        shape = shape.fuse(s)
    return shape


# ---------------------------------------------------------------------------
# Plate
# ---------------------------------------------------------------------------
def make_keep():
    """Everything right of the left-wall outline and in front of the rear edge."""
    return prism(LEFT_EDGE + ((100.0, PLATE_REAR_Y), (100.0, 50.0)), -20.0, 20.0)


def make_plate():
    """Body + ring pads, clipped along the left wall, with the board window."""
    ax, ay = RING_A
    bx, by = RING_B
    body = box(LEFT_EDGE[0][0], PLATE_RIGHT_X, PLATE_REAR_Y, PLATE_FRONT_Y, PLATE_Z0, PLATE_Z1)
    pad_a = cyl(ax, ay, 2 * RING_PAD_R, PLATE_Z0, PLATE_Z1)
    neck_a = box(LEFT_EDGE[0][0], ax + RING_PAD_R, RING_A_PAD_Y0, ay, PLATE_Z0, PLATE_Z1)
    pad_b = cyl(bx, by, 2 * RING_PAD_R, PLATE_Z0, PLATE_Z1)
    m = HOOK_SLOT_M                               # same margin behind the slot and in front of the root
    hook_pad = box(PLATE_RIGHT_X - 1.0, HOOK_PLATE_X1, SLOT_Y0 - m, LEAF_ROOT_Y + m, PLATE_Z0, PLATE_Z1)
    plate = fuse_all([body, pad_a, neck_a, pad_b, hook_pad])
    return plate.common(make_keep()).cut(make_window()).cut(make_hook_slot())


def make_hook_slot():
    """Slot through the plate around the hook's head and leaf, with room for
    the full travel outward, from behind the head to the leaf's root."""
    return fuse_all([
        box(SLOT_X0, SLOT_X1, SLOT_Y0, HOOK_Y1 + HOOK_GAP, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0),
        box(LEAF_X0 - HOOK_GAP, SLOT_X1, SLOT_Y0, LEAF_ROOT_Y, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0),
    ])


def make_window():
    """Floor window under the board (BOOT/RESET), closed toward the rear edge
    by a band under the USB-C shell so the plate's two sides can't spread or
    squeeze."""
    return box(BOARD_X0 + WINDOW_INSET, BOARD_X1 - WINDOW_INSET,
               PLATE_REAR_Y + BAND_W, BOARD_Y1 - WINDOW_FRONT_GAP, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0)


def make_screw_cutters():
    """M4 through hole plus a countersink for the conical head, from below."""
    t = math.tan(math.radians(CSK_ANGLE / 2))
    z_top = PLATE_Z0 + CSK_DEPTH
    cutters = []
    for cx, cy in (RING_A, RING_B):
        cutters.append(cyl(cx, cy, SCREW_HOLE_D, PLATE_Z0 - 1.0, PLATE_Z1 + 1.0))
        # the cone starts 1 mm below the underside so it cuts cleanly through it
        cutters.append(Part.makeCone(SCREW_HOLE_D / 2 + (CSK_DEPTH + 1.0) * t, SCREW_HOLE_D / 2,
                                     CSK_DEPTH + 1.0, Vector(cx, cy, PLATE_Z0 - 1.0)))
    return fuse_all(cutters)


# ---------------------------------------------------------------------------
# Supports
# ---------------------------------------------------------------------------
def make_ledges():
    """Ledges under the long PCB edges, plate to the PCB's component side."""
    return fuse_all([
        box(LEDGE_X0, LEDGE_X0 + LEDGE_W, PLATE_REAR_Y, LEDGE_Y1, PLATE_Z0, PCB_Z0),
        box(LEDGE_X1 - LEDGE_W, LEDGE_X1, PLATE_REAR_Y, LEDGE_Y1, PLATE_Z0, PCB_Z0),
    ])


def make_corner_stops():
    """An L at each front corner of the board: the front arm stops it when a
    cable is pushed in, the side arm locates it sideways. Each L stands on
    its own footing from the bed, past the plate edge where needed."""
    ls = []
    for edge, out in ((BOARD_X0, -1.0), (BOARD_X1, 1.0)):
        x_in = edge + out * CORNER_GAP                  # side arm inner face
        x_out = x_in + out * CORNER_T                   # side arm outer face
        ls.append(box(x_out, x_in, BOARD_Y1 - CORNER_SIDE_L, CORNER_Y1, PLATE_Z0, CORNER_TOP_Z))
        ls.append(box(x_out, edge - out * CORNER_REACH, CORNER_Y0, CORNER_Y1, PLATE_Z0, CORNER_TOP_Z))
    return fuse_all(ls)


def make_pedestal():
    """Block under the serial USB-C shell: puts it at the slot height."""
    return box(SER_X0, SER_X1, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, SER_Z0).common(make_keep())


def make_shell_wall():
    """Low wall along the serial shell's left side, SHELL_WALL_GAP off it, up
    to the shell's mid-height."""
    return box(SHELL_WALL_X1 - SHELL_WALL_T, SHELL_WALL_X1, SHELL_WALL_Y0, SER_SHELL_Y1, PLATE_Z0, SER_CZ)


def make_middle_wall():
    """Rigid wall between the breakout and the RP2040: the right side wall of
    the serial shell and tail, with a lip over the RP2040's left edge
    (pads 3-5, unwired on both halves). Nothing reaches over the tail, so
    the breakout drops straight in. Beside the shell it stays at ledge
    height so the GP0/GP1 wires cross it. Only 0.83 fits between the shell
    and the RP2040; below the PCB it is fused with the left ledge (1.83).
    Past the lip it carries on, low (below the RP2040's PCB), as the glue
    trough's right side."""
    return fuse_all([
        box(MID_X0, MID_X1, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, PCB_Z0),
        box(MID_X0, MID_X1, MID_Y1 - 1.0, POCKET_Y1, PLATE_Z0, SER_STOP_TOP_Z),
        box(MID_X0, MID_X1, min(SER_SHELL_Y1, ZERO_LIP_Y0), MID_Y1, PLATE_Z0, MID_WALL_TOP_Z),
        box(MID_X1, ZERO_LIP_X1, ZERO_LIP_Y0, ZERO_LIP_Y1, LIP_Z0, MID_WALL_TOP_Z),
    ])


def make_glue_pocket():
    """Glue from the top only. Nothing under the tail (the shell alone sets
    the breakout's level on the pedestal); a left wall beside the tail; a
    rib behind the tail end, level with its top (the plug-in push; the wires
    lie flat over it), and behind the rib a trough.
    The glue goes over the tail end, the solder joints and the rib into the
    trough, so the unplug pull hooks the glue behind the rib. The middle
    wall is the right side."""
    x_out = POCKET_X0 - POCKET_WALL_T
    return fuse_all([
        box(x_out, POCKET_X0, SER_SHELL_Y1, POCKET_Y1, PLATE_Z0, SER_STOP_TOP_Z),
        box(x_out, MID_X0, SER_STOP_Y0, RIB_Y1, PLATE_Z0, RIB_TOP_Z),
        box(x_out, MID_X0, RIB_Y1, TROUGH_Y1, PLATE_Z0, TROUGH_FLOOR_Z),
        box(x_out, MID_X0, TROUGH_Y1, POCKET_Y1, PLATE_Z0, SER_STOP_TOP_Z),
    ])


def make_hook():
    """Snap hook over the RP2040's right edge: one straight solid head on
    the bed (the same profile end to end), on the free end of a leaf that
    runs forward to its root, flexing outward. The head's lip has a
    vertical land at its tip, a 45 deg ramp above it (the board pushes it
    aside) and a 45 deg chamfer under the part outside the PCB (shorter
    overhang)."""
    leaf = box(LEAF_X0, LEAF_X1, HOOK_Y1 - 0.5, LEAF_ROOT_Y + 0.5, PLATE_Z0, LEAF_TOP_Z)
    post = box(HOOK_X0, HOOK_X1, HOOK_Y0, HOOK_Y1, PLATE_Z0, HOOK_TOP_Z)
    lip = prism_xz([(HOOK_TIP_X, LIP_Z0), (LEDGE_X1, LIP_Z0), (HOOK_X0, LIP_Z0 - HOOK_GAP),
                    (HOOK_X0, HOOK_TOP_Z), (LEDGE_X1, HOOK_TOP_Z), (HOOK_TIP_X, LIP_Z0 + HOOK_LAND)],
                   HOOK_Y0, HOOK_Y1)
    return fuse_all([leaf, post, lip])


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    """Return the finished platform as a single solid."""
    shape = fuse_all([make_plate(), make_ledges(), make_corner_stops(), make_pedestal(),
                      make_shell_wall(), make_middle_wall(), make_glue_pocket(), make_hook()])
    return shape.cut(make_screw_cutters()).removeSplitter()


def make_components():
    """The parts the platform holds, as one compound (for checks and drawings):
    RP2040 PCB and USB-C shell, serial USB-C shell (with the bump behind it)
    and its PCB tail."""
    return Part.makeCompound([
        box(BOARD_X0, BOARD_X1, BOARD_Y0, BOARD_Y1, PCB_Z0, PCB_Z1),
        box(BOARD_CX - USB_W / 2, BOARD_CX + USB_W / 2, USB_FACE_Y, USB_FACE_Y + USB_L, USB_Z0, PCB_Z0),
        box(SER_X0, SER_X1, SER_FACE_Y, SER_SHELL_Y1, SER_Z0, SER_Z0 + SER_H),
        box(SER_CX - SER_PCB_W / 2, SER_CX + SER_PCB_W / 2, SER_SHELL_Y1, SER_PCB_Y1,
            SER_CZ - SER_PCB_T / 2, SER_CZ + SER_PCB_T / 2),
    ])


COUPON = (0.5, HOOK_PLATE_X1, PLATE_REAR_Y, CORNER_Y1 + 3.0)   # X0, X1, Y0, Y1 of the test print: the whole
                                                               # pedestal, the board window and the hook's leaf root


def make_coupon(shape):
    """Cut-out of the platform with the RP2040 lip, the snap hook, the band,
    the pedestal and the glue pocket, to try with the real parts before printing the
    whole platform."""
    x0, x1, y0, y1 = COUPON
    z1 = max(HOOK_TOP_Z, MID_WALL_TOP_Z, CORNER_TOP_Z) + 1.0
    return shape.common(box(x0, x1, y0, y1, PLATE_Z0 - 1.0, z1)).removeSplitter()


# ---------------------------------------------------------------------------
# Export / entry points
# ---------------------------------------------------------------------------
NAME = "rp2040zero_platform"


def write_stl(shape, path):
    import MeshPart

    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1)
    mesh.write(path)


def export(shape, out_dir):
    """Write FCStd, STEP and STL for `shape`, plus the hook test coupon's STL,
    into out_dir; return the paths."""
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        'fcstd': os.path.join(out_dir, NAME + ".FCStd"),
        'step': os.path.join(out_dir, NAME + ".step"),
        'stl': os.path.join(out_dir, NAME + ".stl"),
        'coupon_stl': os.path.join(out_dir, "hook_coupon.stl"),
    }
    doc = FreeCAD.newDocument(NAME)
    obj = doc.addObject("Part::Feature", "Platform")
    obj.Shape = shape
    doc.recompute()
    doc.saveAs(paths['fcstd'])
    shape.exportStep(paths['step'])
    write_stl(shape, paths['stl'])
    write_stl(make_coupon(shape), paths['coupon_stl'])
    FreeCAD.closeDocument(doc.Name)
    return paths


def main():
    shape = build()
    print("valid:", shape.isValid(), "solids:", len(shape.Solids),
          "volume mm^3: %.1f" % shape.Volume)
    bb = shape.BoundBox
    print("bbox X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f"
          % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    print("USB-C shells Z %.2f..%.2f (RP2040) and %.2f..%.2f (serial) in slots %.2f..%.2f; head bottom Z %.2f (bottom plate %.2f)"
          % (USB_Z0, PCB_Z0, SER_Z0, SER_Z0 + SER_H, USB_SLOT_Z[0], USB_SLOT_Z[1], HEAD_BOTTOM_Z, BOTTOM_PLATE_Z))
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
