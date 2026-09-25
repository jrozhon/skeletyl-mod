"""Skeletyl V4 case with the TRRS jack hole replaced by a USB-C slot.

Fills the old Ø5.2 jack hole in the rear wall and cuts a 9.82 x 3.62 stadium
slot (the same shape as the RP2040's USB slot) for a mid-mount USB-C
breakout, then writes the STL back in the case's own coordinates, so it
prints (and mirrors for the other half) exactly like the original.

The case STL is not a perfectly valid solid (a few self-intersecting facets
far from the rear-left corner); OCC still gives one solid and the tests check
that nothing outside EDIT_REGION changes.

Usage: python3 case_usb_serial.py [path/to/case_v4_103.stl]   (~3 min)
"""
import os
import sys

try:  # imported as a package member (tests)
    from . import freecad_path  # noqa: F401
    from . import rp2040zero_platform as rp
except ImportError:  # run as a script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import freecad_path  # noqa: F401
    import rp2040zero_platform as rp

import FreeCAD  # noqa: F401  (must come before Mesh: importing Mesh first segfaults)
import Mesh
import MeshPart
import Part
from FreeCAD import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CASE = os.path.join(HERE, "..", "refs", "Skeletyl", "V4", "case_v4_103.stl")
OUT_PATH = os.path.join(HERE, "case_v4_103_usb_serial.stl")

PLUG_D = 6.6                   # fills the Ø5.2 hole and its ~Ø6.4 chamfered mouth
PLUG_OUTER_GAP = 0.15          # plug's outer end this far inside the outer face (it curves into the corner: -35.95 at X 1.8)
SLOT_CUT_Y = (-37.5, -33.5)    # slot cutter runs through the whole wall along Y
# Platform-frame box around the rear-left wall; the modification stays inside it.
EDIT_REGION = ((-1.0, 13.0), (-38.0, -33.0), (-6.0, 2.5))
EXPECTED_DV = -23.8            # volume change of a good run: fill minus slot, mm^3
DV_TOL = 5.0

# case (x, y, z) -> platform (x + 94.136, z + 30.599, y)
CASE_TO_PLATFORM = Matrix(1, 0, 0, 94.136,
                          0, 0, 1, 30.599,
                          0, 1, 0, 0,
                          0, 0, 0, 1)


def load_case(path):
    """The case STL as an OCC solid in the platform frame."""
    mesh = Mesh.Mesh(path)
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.05)
    return Part.Solid(Part.Shell(shape.Faces)).transformGeometry(CASE_TO_PLATFORM)


def make_plug():
    """Cylinder filling the old jack hole within the wall thickness."""
    y0 = rp.WALL_OUTER_Y + PLUG_OUTER_GAP
    return Part.makeCylinder(PLUG_D / 2.0, rp.WALL_RECESS_Y - y0,
                             Vector(rp.JACK_AXIS_X, y0, rp.JACK_HOLE_Z), Vector(0, 1, 0))


def make_slot_cutter():
    """Stadium (full-radius ends) along Y, same size as the RP2040 slot."""
    z0, z1 = rp.SER_SLOT_Z
    r = (z1 - z0) / 2.0
    cz = z0 + r
    xa, xb = rp.SER_SLOT_X[0] + r, rp.SER_SLOT_X[1] - r   # end-circle centres
    y0, y1 = SLOT_CUT_Y
    length = y1 - y0
    middle = Part.makeBox(xb - xa, length, 2 * r, Vector(xa, y0, z0))
    ends = [Part.makeCylinder(r, length, Vector(x, y0, cz), Vector(0, 1, 0)) for x in (xa, xb)]
    return middle.fuse(ends)


def modify(case):
    """Fill the jack hole, cut the USB-C slot."""
    return case.fuse(make_plug()).cut(make_slot_cutter())


def check(case, shape):
    """None if `shape` looks like a good modification of `case`, else why not.
    Guards against a boolean that silently did nothing or fell apart."""
    if len(shape.Solids) != 1:
        return "expected 1 solid, got %d" % len(shape.Solids)
    dv = shape.Volume - case.Volume
    if abs(dv - EXPECTED_DV) > DV_TOL:
        return "volume change %.1f mm^3, expected %.1f +- %.1f" % (dv, EXPECTED_DV, DV_TOL)
    return None


def export(shape, path):
    """Write `shape` (platform frame) as an STL in case coordinates."""
    back = shape.transformGeometry(CASE_TO_PLATFORM.inverse())
    mesh = MeshPart.meshFromShape(Shape=back, LinearDeflection=0.01, AngularDeflection=0.05)
    mesh.write(path)


def main(case_path=DEFAULT_CASE, out_path=OUT_PATH):
    if not os.path.exists(case_path):
        print("case STL not found: %s (run refs/fetch.sh)" % case_path)
        return 1
    case = load_case(case_path)
    shape = modify(case)
    print("solids: %d  volume change %.1f mm^3" % (len(shape.Solids), shape.Volume - case.Volume))
    problem = check(case, shape)
    if problem:
        print("NOT written, the boolean went wrong: %s" % problem)
        return 1
    export(shape, out_path)
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
