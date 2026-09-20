# RP2040-Zero + TRRS platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A parametric FreeCAD script that builds, tests and exports the 3D-printed platform holding a Waveshare RP2040-Zero (components down) and a PJ-320A TRRS jack in a Skeletyl V4 case, replacing the Splinktegrated PCB.

**Architecture:** One pure-`Part` FreeCAD module (`rp2040zero_platform.py`) with a parameter block on top and one builder function per feature group (plate, ring pockets, board pocket, jack pocket) that `build()` fuses/cuts in a fixed order. The Splinktegrated outline lives in its own data module. Tests are stdlib `unittest` probes (`Shape.isInside`) run with system Python + FreeCAD's lib path. A separate numpy/FreeCAD script checks clearance against the case STL.

**Tech Stack:** FreeCAD 1.1.3 (`Part`, `Mesh` modules, importable via `sys.path.append('/usr/lib/freecad/lib')`), Python 3 stdlib `unittest`, numpy 2.x. No pytest, no CadQuery.

**Spec:** `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`

## Global Constraints

- Platform frame: origin = case ring A centre, X toward ring B, Y toward the user (rear wall at Y = −31.8), Z up with Z = 0 at the ring tops. Units mm.
- Case STL → platform frame: `X = x_case + 94.136`, `Y = z_case + 30.599`, `Z = y_case`.
- KiCad → platform frame: translate H1 `(131.60262, 109.99266)` to origin, rotate by `Δ = atan2(-28.267, 34.660) − atan2(-27.9, 34.587)` (≈ −0.3075°). No axis flip.
- Every dimension is a module-level UPPER_CASE parameter with a one-line comment; builders only use parameters and values derived from them.
- The final shape must satisfy `shape.isValid()` and `len(shape.Solids) == 1`.
- Nothing may extend below Z = −5.25 (bottom plate is at Z = −8; zip ties need the gap) or behind Y = −31.3.
- Commit after every task; commit messages in imperative mood, ending with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Reference sources (Bastardkb repos) are cloned into `refs/` which is git-ignored; never commit them (CC BY-NC-SA / CERN-OHL content).

## File structure

```
skeletyl_hardware/
├── README.md                              # (exists) repo index; Task 6 adds usage
├── .gitignore                             # (exists) add refs/, exports
├── refs/fetch.sh                          # Task 6: clones the two Bastardkb repos into refs/
└── rp2040zero_platform/
    ├── README.md                          # Task 6: parameters, printing, assembly
    ├── __init__.py                        # Task 1: empty; makes the folder a package for the tests
    ├── freecad_path.py                    # Task 1: makes `import FreeCAD` work from system python
    ├── outline_kicad.py                   # Task 1: OUTLINE_KICAD data + H1/H2 constants
    ├── rp2040zero_platform.py             # Tasks 1–6: params, builders, build(), main()
    ├── check_clearance.py                 # Task 7: case-STL clearance check + section PNGs
    └── tests/
        ├── __init__.py
        ├── test_outline.py                # Task 1
        └── test_platform.py               # Tasks 2–5 (one TestCase per feature group)
```

Run tests from the repo root with: `python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`

---

### Task 1: Scaffolding, outline data and the KiCad → platform transform

**Files:**
- Create: `rp2040zero_platform/freecad_path.py`
- Create: `rp2040zero_platform/outline_kicad.py`
- Create: `rp2040zero_platform/rp2040zero_platform.py` (parameter block + transform only)
- Create: `rp2040zero_platform/__init__.py` (empty)
- Create: `rp2040zero_platform/tests/__init__.py` (empty)
- Create: `rp2040zero_platform/tests/test_outline.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `outline_kicad.OUTLINE_KICAD: list[tuple[str, (x,y), (x,y)|None, (x,y)]]` — ordered, open chain of `'line'`/`'arc'` segments in KiCad mm; first start `(152.481974, 137.792361)`, last end `(141.506975, 137.792362)`; closed by a straight line from last end to first start.
- Produces: `outline_kicad.H1 = (131.60262, 109.99266)`, `outline_kicad.H2 = (166.19, 82.09266)`.
- Produces: `rp2040zero_platform.kicad_to_local(p: tuple[float,float]) -> tuple[float,float]`.
- Produces: `rp2040zero_platform.RING_A`, `RING_B` and every parameter listed in Step 3.

- [ ] **Step 1: Create the FreeCAD path helper and ignore rules**

`rp2040zero_platform/freecad_path.py`:
```python
"""Import this before FreeCAD so the system python finds FreeCAD's modules.

Arch installs FreeCAD's python modules under /usr/lib/freecad/lib; when the
script runs inside freecadcmd/FreeCAD itself the import already works and
this is a no-op.
"""
import sys

FREECAD_LIB = "/usr/lib/freecad/lib"

if FREECAD_LIB not in sys.path:
    sys.path.append(FREECAD_LIB)
```

Append to `.gitignore`:
```
refs/
*.stl
*.step
*.FCStd
*.png
```

- [ ] **Step 2: Create the outline data module**

`rp2040zero_platform/outline_kicad.py`:
```python
"""Splinktegrated head + neck outline, extracted from Edge.Cuts of
Bastardkb/splinktegrated splinktegrated.kicad_pcb (commit of 2023-12-11).

Coordinates are KiCad mm (y grows downward on screen; we do not flip it).
The chain is open: it starts and ends on the snap-off line of the USB
daughterboard (y = 137.792) and is closed with a straight segment.
Each entry is (kind, start, mid, end); mid is None for lines and the arc's
mid-point for arcs.
"""

# M4 mounting holes (MountingHole_4mm_Pad_Via footprints H1, H2).
H1 = (131.60262, 109.99266)
H2 = (166.19, 82.09266)

OUTLINE_KICAD = [
    ('line', (152.481974, 137.792361), None, (158.116408, 137.8)),
    ('arc', (158.116408, 137.799999), (159.15003, 137.338505), (159.569767, 136.287233)),
    ('line', (159.569767, 136.287233), None, (159.5, 112.2)),
    ('arc', (159.5, 112.2), (159.919728, 111.148725), (160.95335, 110.687233)),
    ('line', (160.95335, 110.687233), None, (161.628436, 110.662767)),
    ('arc', (161.628436, 110.662767), (162.662058, 110.201275), (163.081786, 109.15)),
    ('line', (163.081786, 109.15), None, (163.070005, 96.441645)),
    ('line', (163.070005, 96.441645), None, (163.049866, 91.682957)),
    ('arc', (163.049866, 91.682957), (163.784703, 88.976476), (165.880646, 87.113133)),
    ('arc', (165.880646, 87.113132), (168.388521, 85.27585), (169.320602, 82.31)),
    ('arc', (169.320602, 82.31), (168.466149, 79.896675), (166.145648, 78.815303)),
    ('line', (166.145648, 78.815303), None, (161.4, 78.8)),
    ('line', (161.4, 78.8), None, (161.05, 78.0)),
    ('line', (161.05, 78.0), None, (137.0, 78.0)),
    ('arc', (137.0, 78.0), (136.176129, 78.554067), (135.384492, 77.954846)),
    ('line', (135.384492, 77.954846), None, (133.621486, 77.993749)),
    ('arc', (133.621486, 77.993749), (132.594912, 78.431278), (132.171486, 79.463749)),
    ('line', (132.171486, 79.463749), None, (132.181486, 102.583749)),
    ('arc', (132.181486, 102.583749), (131.553926, 104.859213), (129.841486, 106.483749)),
    ('arc', (129.841486, 106.483749), (127.68637, 111.206774), (131.783471, 114.395074)),
    ('line', (131.783471, 114.395074), None, (135.613949, 114.386051)),
    ('arc', (135.613949, 114.386051), (137.41, 115.13), (138.153949, 116.926051)),
    ('line', (138.153949, 116.926051), None, (138.142824, 136.343393)),
    ('arc', (138.142824, 136.343393), (138.578474, 137.373379), (139.615358, 137.792362)),
    ('line', (139.615358, 137.792362), None, (141.506975, 137.792362)),
]
```

- [ ] **Step 3: Write the failing transform test**

`rp2040zero_platform/__init__.py` and `rp2040zero_platform/tests/__init__.py`: empty files.

`rp2040zero_platform/tests/test_outline.py`:
```python
import math
import unittest

from rp2040zero_platform import outline_kicad as ok
from rp2040zero_platform import rp2040zero_platform as rp


class OutlineDataTest(unittest.TestCase):
    def test_chain_is_connected(self):
        for prev, cur in zip(ok.OUTLINE_KICAD, ok.OUTLINE_KICAD[1:]):
            self.assertAlmostEqual(prev[3][0], cur[1][0], places=3)
            self.assertAlmostEqual(prev[3][1], cur[1][1], places=3)

    def test_chain_ends_on_snap_line(self):
        self.assertAlmostEqual(ok.OUTLINE_KICAD[0][1][1], 137.7924, places=3)
        self.assertAlmostEqual(ok.OUTLINE_KICAD[-1][3][1], 137.7924, places=3)

    def test_arcs_have_mid_lines_do_not(self):
        for kind, _s, mid, _e in ok.OUTLINE_KICAD:
            self.assertEqual(kind == 'arc', mid is not None)


class TransformTest(unittest.TestCase):
    def test_h1_maps_to_origin(self):
        x, y = rp.kicad_to_local(ok.H1)
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_h2_maps_onto_ring_b_direction(self):
        x, y = rp.kicad_to_local(ok.H2)
        # Same direction as RING_B; pitch differs by 0.29 mm (PCB 44.44 vs case 44.73).
        ang_pcb = math.atan2(y, x)
        ang_case = math.atan2(rp.RING_B[1], rp.RING_B[0])
        self.assertAlmostEqual(ang_pcb, ang_case, places=6)
        self.assertAlmostEqual(math.hypot(x, y), 44.438, places=2)

    def test_jack_footprint_lands_near_case_hole(self):
        # J11 axis: footprint anchor (133.89, 86.31) + 2.75 mm body half-width.
        x, _y = rp.kicad_to_local((136.64, 86.31))
        self.assertAlmostEqual(x, rp.JACK_AXIS_X, delta=0.15)

    def test_rear_edge_is_behind_trim_line(self):
        _x, y = rp.kicad_to_local((137.0, 78.0))
        self.assertLess(y, rp.PLATE_REAR_Y)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'rp2040zero_platform.rp2040zero_platform'`.

- [ ] **Step 5: Create the module with the parameter block and transform**

`rp2040zero_platform/rp2040zero_platform.py`:
```python
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
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 7 tests, `OK`.

- [ ] **Step 7: Commit**

```bash
cd /home/loki/skeletyl_hardware
git add .gitignore rp2040zero_platform/
git commit -m "Add outline data, parameters and KiCad-to-platform transform

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Base plate from the Splinktegrated outline

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (append builders)
- Create: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Produces: `make_outline_face() -> Part.Face` (in platform frame, Z = 0, untrimmed).
- Produces: `make_plate() -> Part.Solid` — outline extruded Z `PLATE_Z0..PLATE_Z1`, trimmed to `Y >= PLATE_REAR_Y`.
- Produces: `build() -> Part.Shape` — for now returns `make_plate()`; later tasks extend it.
- Produces: helper `box(x0, x1, y0, y1, z0, z1) -> Part.Solid` and `cyl(cx, cy, d, z0, z1) -> Part.Solid` used by every later builder.

- [ ] **Step 1: Write the failing plate tests**

`rp2040zero_platform/tests/test_platform.py`:
```python
import unittest

from rp2040zero_platform import rp2040zero_platform as rp

from FreeCAD import Vector

# Slightly inside a face is what we probe; 1e-6 is FreeCAD's isInside tolerance.
TOL = 1e-6


def inside(shape, x, y, z):
    return shape.isInside(Vector(x, y, z), TOL, True)


class PlateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plate = rp.make_plate()

    def test_is_single_valid_solid(self):
        self.assertTrue(self.plate.isValid())
        self.assertEqual(len(self.plate.Solids), 1)

    def test_thickness_and_rear_trim(self):
        bb = self.plate.BoundBox
        self.assertAlmostEqual(bb.ZMin, rp.PLATE_Z0, places=4)
        self.assertAlmostEqual(bb.ZMax, rp.PLATE_Z1, places=4)
        self.assertAlmostEqual(bb.YMin, rp.PLATE_REAR_Y, places=4)

    def test_extent_matches_splinktegrated_head(self):
        bb = self.plate.BoundBox
        # Head is ~41.6 mm wide, head+neck ~59 mm tall before the rear trim.
        self.assertAlmostEqual(bb.XMin, -3.92, delta=0.05)
        self.assertAlmostEqual(bb.XMax, 37.7, delta=0.1)
        self.assertAlmostEqual(bb.YMax, 27.8, delta=0.1)

    def test_covers_both_rings_and_the_ports(self):
        for x, y in (rp.RING_A, rp.RING_B, (rp.JACK_AXIS_X, -25.0), (21.0, -25.0)):
            self.assertTrue(inside(self.plate, x, y, -3.0), (x, y))

    def test_tail_is_removed(self):
        # The USB daughterboard tail would be at Y > 28 (KiCad y > 137.8).
        self.assertFalse(inside(self.plate, 21.0, 35.0, -3.0))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest rp2040zero_platform.tests.test_platform -v`
Expected: ERROR `AttributeError: module ... has no attribute 'make_plate'`.

- [ ] **Step 3: Implement the primitives, outline face and plate**

Append to `rp2040zero_platform/rp2040zero_platform.py`:
```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 12 tests, `OK`. If `test_extent_matches_splinktegrated_head` fails by more than the delta, print `rp.make_plate().BoundBox` and verify against the KiCad extents (x 127.686…169.321, y 77.955…137.8 → local X −3.9…37.7, Y −32.0…27.8) before touching the test.

- [ ] **Step 5: Commit**

```bash
cd /home/loki/skeletyl_hardware
git add rp2040zero_platform/
git commit -m "Build the base plate from the Splinktegrated outline

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Ring pockets

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py`
- Modify: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Produces: `make_ring_pocket_outer(cx, cy) -> Part.Solid` — Ø`POCKET_OD` cylinder Z `PLATE_Z0..CAP_TOP_Z`.
- Produces: `make_ring_cutters(cx, cy) -> Part.Shape` — compound of the bore (Ø`POCKET_BORE_D`, Z `PLATE_Z0-1 .. 0`) and the screw hole (Ø`SCREW_HOLE_D`, through the cap). **Cut last** in `build()` so rails crossing a ring stay open around the case ring.
- Produces: `RING_CENTRES = (RING_A, RING_B)`.
- `build()` now: plate + outers − cutters.

- [ ] **Step 1: Add the failing ring tests**

Append to `rp2040zero_platform/tests/test_platform.py` (above `if __name__`):
```python
class RingPocketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shape = rp.build()

    def test_single_valid_solid(self):
        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.shape.Solids), 1)

    def test_bore_is_open_around_each_case_ring(self):
        for cx, cy in rp.RING_CENTRES:
            for r in (0.0, 4.9):                 # centre and just inside the Ø10 ring
                for z in (-3.7, -2.0, -0.05):    # whole ring height
                    self.assertFalse(inside(self.shape, cx + r, cy, z), (cx, cy, r, z))
            self.assertFalse(inside(self.shape, cx, cy - 4.9, -2.0))

    def test_pocket_wall_and_cap_ring_exist(self):
        for cx, cy in rp.RING_CENTRES:
            self.assertTrue(inside(self.shape, cx + 5.8, cy, -2.0))   # wall (r 5.2..6.4)
            self.assertTrue(inside(self.shape, cx, cy + 5.8, -2.0))
            self.assertTrue(inside(self.shape, cx + 3.0, cy, 1.0))    # cap ring (r 2.25..6.4)
            self.assertTrue(inside(self.shape, cx - 3.0, cy, 0.5))
            self.assertFalse(inside(self.shape, cx + 3.0, cy, rp.CAP_TOP_Z + 0.05))

    def test_screw_hole_goes_through_cap(self):
        for cx, cy in rp.RING_CENTRES:
            for z in (0.05, 1.0, 1.95):
                self.assertFalse(inside(self.shape, cx, cy, z))
                self.assertFalse(inside(self.shape, cx + 2.1, cy, z))
                self.assertTrue(inside(self.shape, cx + 2.4, cy, z))

```

- [ ] **Step 2: Run to verify failure**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest rp2040zero_platform.tests.test_platform.RingPocketTest -v`
Expected: ERROR `AttributeError: ... 'RING_CENTRES'`.

- [ ] **Step 3: Implement the ring pockets and wire them into build()**

Insert before the `# Assembly` section in `rp2040zero_platform.py`:
```python
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
```

Replace `build()`:
```python
def build():
    """Return the finished platform as a single solid."""
    shape = make_plate()
    for cx, cy in RING_CENTRES:
        shape = shape.fuse(make_ring_pocket_outer(cx, cy))
    # Cut ring bores and screw holes last: anything fused over a ring must
    # stay open where the case ring sits.
    for cx, cy in RING_CENTRES:
        shape = shape.cut(make_ring_cutters(cx, cy))
    return shape.removeSplitter()
```

- [ ] **Step 4: Run all tests**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 16 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/loki/skeletyl_hardware
git add rp2040zero_platform/
git commit -m "Add ring pockets that slip over the case controller rings

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: RP2040-Zero pocket (components down)

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py`
- Modify: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Produces derived constants (module level, after the parameters):
  `USB_CENTER_Z`, `USB_BOTTOM_Z`, `PCB_BOTTOM_Z`, `PCB_TOP_Z`, `BOARD_CX`, `BOARD_X0`, `BOARD_X1`, `BOARD_Y0` (rear edge), `BOARD_Y1` (front edge), `RAIL_X0` (inner face of the left rail = `BOARD_X0 - BOARD_CLEAR`), `RAIL_X1` (inner face of the right rail).
- Produces: `make_board_additions() -> Part.Solid` (rails, end-stop, cradle, corner seats fused).
- Produces: `make_board_cutters() -> Part.Shape` (floor window + zip-tie slots fused).
- Produces: `make_cap_relief() -> Part.Solid` — box covering the board pocket footprint above `PCB_BOTTOM_Z - CAP_RELIEF`; cut from each ring pocket outer only.
- `build()` order: plate − board cutters; + ring outers (each minus cap relief); + board additions; − ring cutters.

- [ ] **Step 1: Add the failing board-pocket tests**

Append to `tests/test_platform.py`:
```python
class BoardPocketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shape = rp.build()
        cls.cx = rp.BOARD_CX

    def test_single_valid_solid(self):
        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.shape.Solids), 1)

    def test_derived_heights_put_usb_c_in_the_slot_centre(self):
        slot_c = (rp.USB_SLOT_Z[0] + rp.USB_SLOT_Z[1]) / 2
        self.assertAlmostEqual(rp.USB_CENTER_Z, slot_c, places=6)
        self.assertAlmostEqual(rp.PCB_BOTTOM_Z, rp.USB_BOTTOM_Z + rp.USB_H, places=6)
        self.assertAlmostEqual(rp.PCB_TOP_Z, rp.PCB_BOTTOM_Z + rp.BOARD_T, places=6)
        self.assertAlmostEqual(rp.BOARD_CX, (rp.USB_SLOT_X[0] + rp.USB_SLOT_X[1]) / 2 + rp.BOARD_X_SHIFT)
        self.assertAlmostEqual(rp.BOARD_Y0, rp.WALL_INNER_Y - rp.USB_INTO_WALL + rp.USB_OVERHANG)

    def test_board_and_connector_volumes_are_empty(self):
        cx = self.cx
        for y in (rp.BOARD_Y0 + 0.5, (rp.BOARD_Y0 + rp.BOARD_Y1) / 2, rp.BOARD_Y1 - 0.5):
            for x in (rp.BOARD_X0 + 0.2, cx, rp.BOARD_X1 - 0.2):
                self.assertFalse(inside(self.shape, x, y, rp.PCB_BOTTOM_Z + 0.5), (x, y))
        # USB-C shell volume.
        for z in (rp.USB_BOTTOM_Z + 0.1, rp.USB_CENTER_Z, rp.PCB_BOTTOM_Z - 0.1):
            self.assertFalse(inside(self.shape, cx, rp.BOARD_Y0 - 0.5, z))
            self.assertFalse(inside(self.shape, cx - rp.USB_W / 2 + 0.1, rp.BOARD_Y0 + 2.0, z))

    def test_cradle_supports_usb_c_shell(self):
        cx = self.cx
        y = rp.PLATE_REAR_Y + rp.CRADLE_L / 2
        self.assertTrue(inside(self.shape, cx, y, rp.USB_BOTTOM_Z - 0.1))
        self.assertTrue(inside(self.shape, cx, y, rp.PLATE_Z1 + 0.5))
        self.assertFalse(inside(self.shape, cx, y, rp.USB_BOTTOM_Z + 0.1))
        self.assertFalse(inside(self.shape, cx + rp.CRADLE_W / 2 + 0.3, y, rp.PLATE_Z1 + 0.5))

    def test_corner_seats_support_far_corners(self):
        y = rp.BOARD_Y1 - rp.SEAT_L / 2
        for x in (rp.BOARD_X0 + 1.0, rp.BOARD_X1 - 1.0):
            self.assertTrue(inside(self.shape, x, y, rp.PCB_BOTTOM_Z - 0.1))
            self.assertFalse(inside(self.shape, x, y, rp.PCB_BOTTOM_Z + 0.1))
        # Nothing under the pad rows between the seats.
        self.assertFalse(inside(self.shape, self.cx, y, rp.PCB_BOTTOM_Z - 0.1))

    def test_rails_and_end_stop(self):
        # Y = -15 lies between the two zip-tie slots (-21..-16 and -14..-9).
        for x in (rp.RAIL_X0 - 0.2, rp.RAIL_X1 + 0.2):
            for z in (rp.PLATE_Z1 + 0.1, 0.0, rp.RAIL_TOP_Z - 0.1):
                self.assertTrue(inside(self.shape, x, -15.0, z), (x, z))
            self.assertFalse(inside(self.shape, x, -15.0, rp.RAIL_TOP_Z + 0.1))
        y_stop = rp.BOARD_Y1 + rp.BOARD_CLEAR + rp.RAIL_T / 2
        self.assertTrue(inside(self.shape, self.cx, y_stop, rp.RAIL_TOP_Z - 0.1))
        self.assertFalse(inside(self.shape, self.cx, rp.BOARD_Y1 + 0.1, rp.PCB_TOP_Z))

    def test_floor_window_under_the_board(self):
        for z in (rp.PLATE_Z0 + 0.1, rp.PLATE_Z1 - 0.1):
            self.assertFalse(inside(self.shape, self.cx, -20.0, z))
            self.assertFalse(inside(self.shape, rp.BOARD_X0 + 1.0, -12.0, z))
        # Plate survives outside the window.
        self.assertTrue(inside(self.shape, rp.BOARD_X0 - 3.0, -20.0, rp.PLATE_Z1 - 0.1))
        self.assertTrue(inside(self.shape, self.cx, rp.BOARD_Y1 + 3.0, rp.PLATE_Z1 - 0.1))

    def test_zip_tie_slots_go_through_plate_and_rails(self):
        for y0 in rp.ZIP_SLOT_Y0:
            y = y0 + rp.ZIP_SLOT_L / 2
            for x in (rp.BOARD_X0 - rp.ZIP_SLOT_W / 2, rp.BOARD_X1 + rp.ZIP_SLOT_W / 2):
                for z in (rp.PLATE_Z0 + 0.1, 0.0, rp.RAIL_TOP_Z - 0.1):
                    self.assertFalse(inside(self.shape, x, y, z), (x, y, z))
            # Rail is solid just beyond the slot ends.
            self.assertTrue(inside(self.shape, rp.RAIL_X0 - 0.2, y0 - 0.5, 0.0))
            self.assertTrue(inside(self.shape, rp.RAIL_X0 - 0.2, y0 + rp.ZIP_SLOT_L + 0.5, 0.0))

    def test_ring_b_cap_is_relieved_under_the_board(self):
        bx, by = rp.RING_B
        x = rp.BOARD_X1 - 0.3                     # inside the board footprint, inside the cap
        self.assertTrue(inside(self.shape, x, by, rp.PCB_BOTTOM_Z - rp.CAP_RELIEF - 0.1))
        self.assertFalse(inside(self.shape, x, by, rp.PCB_BOTTOM_Z - rp.CAP_RELIEF + 0.1))
        # Full-height cap remains where the screw head sits.
        self.assertTrue(inside(self.shape, bx + 3.0, by + 3.0, rp.CAP_TOP_Z - 0.1))
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest rp2040zero_platform.tests.test_platform.BoardPocketTest -v`
Expected: ERROR `AttributeError: ... 'BOARD_CX'`.

- [ ] **Step 3: Implement derived constants, board builders, and the new build order**

Insert right after the `kicad_to_local` function in `rp2040zero_platform.py`:
```python
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
```

Insert before the `# Assembly` section:
```python
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
```

Replace `build()`:
```python
def build():
    """Return the finished platform as a single solid."""
    shape = make_plate().cut(make_window())
    relief = make_cap_relief()
    for cx, cy in RING_CENTRES:
        shape = shape.fuse(make_ring_pocket_outer(cx, cy).cut(relief))
    shape = shape.fuse(make_board_additions())
    shape = shape.cut(make_zip_slots())
    # Cut ring bores and screw holes last: anything fused over a ring must
    # stay open where the case ring sits.
    for cx, cy in RING_CENTRES:
        shape = shape.cut(make_ring_cutters(cx, cy))
    return shape.removeSplitter()
```

Order matters: the window is cut from the bare plate *before* the cradle and seats are fused (they overlap the window's footprint and must survive), the zip-tie slots are cut *after* the rails are fused (they must interrupt the rails), and the ring cutters come last.

- [ ] **Step 4: Run all tests**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 25 tests, `OK`. If `test_single_valid_solid` reports more than one solid, the cradle or a seat got detached by the window — check `make_window()` Y range against `PLATE_REAR_Y + CRADLE_L` (cradle must overlap the plate strip) and `BOARD_Y1 - SEAT_L` vs `BOARD_Y1 - WINDOW_FRONT_GAP`.

- [ ] **Step 5: Commit**

```bash
cd /home/loki/skeletyl_hardware
git add rp2040zero_platform/
git commit -m "Add the components-down RP2040-Zero pocket

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: PJ-320A jack pocket

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py`
- Modify: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Produces derived constants: `JACK_SHELF_Z = JACK_HOLE_Z - JACK_AXIS_H`, `JACK_BLOCK_Z0 = JACK_SHELF_Z - JACK_FLOOR_T`, `JACK_WALL_TOP_Z = JACK_SHELF_Z + JACK_BODY_H`, `JACK_X0/JACK_X1` (body side faces), `JACK_Y0 = WALL_INNER_Y + JACK_FACE_GAP` (body front face), `JACK_Y1 = JACK_Y0 + JACK_BODY_L` (body rear face).
- Produces: `make_jack_block() -> Part.Solid` (shelf + walls, solid), `make_jack_cutters() -> Part.Shape` (pocket cavity open toward the wall + two leg slots).
- `build()`: `+ jack block − jack cutters` inserted before the zip-slot cut.

- [ ] **Step 1: Add the failing jack tests**

Append to `tests/test_platform.py`:
```python
class JackPocketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shape = rp.build()

    def test_single_valid_solid_and_floor_limit(self):
        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.shape.Solids), 1)
        self.assertAlmostEqual(self.shape.BoundBox.ZMin, rp.JACK_BLOCK_Z0, places=4)
        self.assertGreaterEqual(self.shape.BoundBox.ZMin, -5.25)

    def test_barrel_axis_matches_case_hole(self):
        self.assertAlmostEqual(rp.JACK_SHELF_Z + rp.JACK_AXIS_H, rp.JACK_HOLE_Z, places=6)
        self.assertAlmostEqual((rp.JACK_X0 + rp.JACK_X1) / 2, rp.JACK_AXIS_X, places=6)

    def test_body_volume_is_empty_and_open_toward_wall(self):
        ym = (rp.JACK_Y0 + rp.JACK_Y1) / 2
        for x in (rp.JACK_X0 + 0.1, rp.JACK_AXIS_X, rp.JACK_X1 - 0.1):
            for z in (rp.JACK_SHELF_Z + 0.1, rp.JACK_HOLE_Z, rp.JACK_WALL_TOP_Z - 0.1):
                self.assertFalse(inside(self.shape, x, ym, z), (x, z))
        # Nothing between the body front face and the plate's rear edge.
        self.assertFalse(inside(self.shape, rp.JACK_AXIS_X, rp.PLATE_REAR_Y + 0.1, rp.JACK_HOLE_Z))

    def test_shelf_walls_and_end_stop(self):
        ym = (rp.JACK_Y0 + rp.JACK_Y1) / 2
        self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, ym, rp.JACK_SHELF_Z - 0.5))
        self.assertFalse(inside(self.shape, rp.JACK_AXIS_X, ym, rp.JACK_BLOCK_Z0 - 0.1))
        for x in (rp.JACK_X0 - rp.JACK_CLEAR_SIDE - 0.5, rp.JACK_X1 + rp.JACK_CLEAR_SIDE + 0.5):
            self.assertTrue(inside(self.shape, x, ym, rp.JACK_WALL_TOP_Z - 0.1), x)
            self.assertFalse(inside(self.shape, x, ym, rp.JACK_WALL_TOP_Z + 0.1), x)
        y_stop = rp.JACK_Y1 + rp.JACK_CLEAR_LEN + rp.JACK_WALL_T / 2
        self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, y_stop, rp.JACK_WALL_TOP_Z - 0.1))

    def test_leg_slots_on_both_sides(self):
        y = rp.JACK_Y0 + rp.JACK_LEG_SLOT_START + rp.JACK_LEG_SLOT_L / 2
        for x in (rp.JACK_X0 + rp.JACK_LEG_INSET, rp.JACK_X1 - rp.JACK_LEG_INSET):
            for z in (rp.JACK_BLOCK_Z0 + 0.1, rp.JACK_SHELF_Z - 0.1):
                self.assertFalse(inside(self.shape, x, y, z), (x, z))
        # Shelf centre between the slots is solid.
        self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, y, rp.JACK_SHELF_Z - 0.5))
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest rp2040zero_platform.tests.test_platform.JackPocketTest -v`
Expected: ERROR `AttributeError: ... 'JACK_BLOCK_Z0'`.

- [ ] **Step 3: Implement the jack pocket**

Insert after the board-derived constants in `rp2040zero_platform.py`:
```python
# Jack placement derived from the case hole: the jack sits on a shelf
# JACK_AXIS_H below the hole axis, body face JACK_FACE_GAP from the wall.
JACK_SHELF_Z = JACK_HOLE_Z - JACK_AXIS_H
JACK_BLOCK_Z0 = JACK_SHELF_Z - JACK_FLOOR_T
JACK_WALL_TOP_Z = JACK_SHELF_Z + JACK_BODY_H
JACK_X0 = JACK_AXIS_X - JACK_BODY_W / 2.0
JACK_X1 = JACK_AXIS_X + JACK_BODY_W / 2.0
JACK_Y0 = WALL_INNER_Y + JACK_FACE_GAP       # body front face (toward the wall)
JACK_Y1 = JACK_Y0 + JACK_BODY_L              # body rear face
```

Insert before the `# Assembly` section:
```python
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
```

Replace `build()`:
```python
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
    # Ring B sits 3.5 mm from the rear wall (the case ring merges into the
    # wall), so trim everything, not just the plate, at the rear edge.
    keep = box(-100, 100, PLATE_REAR_Y, 100, -100, 100)
    return shape.common(keep).removeSplitter()
```

(The whole-part trim was added by a controller ruling during execution: ring B's Ø12.8 boss otherwise reaches Y = −34.7. `RingPocketTest.test_nothing_behind_rear_trim` asserts `BoundBox.YMin == PLATE_REAR_Y`.)

- [ ] **Step 4: Run all tests**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 30 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/loki/skeletyl_hardware
git add rp2040zero_platform/
git commit -m "Add the PJ-320A jack pocket with leg slots

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Headless export, GUI entry point, README, reference fetch script

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (add `export()` / `main()`)
- Create: `rp2040zero_platform/README.md`
- Create: `refs/fetch.sh`
- Modify: `README.md` (usage pointer)
- Modify: `rp2040zero_platform/tests/test_platform.py` (export smoke test)

**Interfaces:**
- Produces: `export(shape, out_dir) -> dict[str, str]` writing `rp2040zero_platform.FCStd`, `.step`, `.stl` and returning their paths.
- Produces: running `freecadcmd rp2040zero_platform/rp2040zero_platform.py` from the repo root exports next to the script; opening the file as a macro in the FreeCAD GUI adds a `Platform` object to the active document.

- [ ] **Step 1: Add the failing export test**

Append to `tests/test_platform.py`:
```python
import os
import tempfile


class ExportTest(unittest.TestCase):
    def test_export_writes_three_files(self):
        shape = rp.build()
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(shape, d)
            self.assertEqual(set(paths), {'fcstd', 'step', 'stl'})
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest rp2040zero_platform.tests.test_platform.ExportTest -v`
Expected: ERROR `AttributeError: ... 'export'`.

- [ ] **Step 3: Implement export and the entry points**

Append to `rp2040zero_platform.py`:
```python
# ---------------------------------------------------------------------------
# Export / entry points
# ---------------------------------------------------------------------------
NAME = "rp2040zero_platform"


def export(shape, out_dir):
    """Write FCStd, STEP and STL for `shape` into out_dir; return the paths."""
    import Mesh
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
    if FreeCAD.GuiUp:
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument(NAME)
        obj = doc.addObject("Part::Feature", "Platform")
        obj.Shape = shape
        doc.recompute()
    else:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        for kind, path in export(shape, out_dir).items():
            print("wrote", kind, path)


if __name__ == "__main__":
    main()
```

`freecadcmd` executes the file with `__name__ == "__main__"` (the import fallback from Task 1 handles the missing package), so `main()` runs and exports. In the GUI, `Macro → Macros… → Execute` runs it the same way with `FreeCAD.GuiUp` true.

- [ ] **Step 4: Run tests and the headless build**

Run: `cd /home/loki/skeletyl_hardware && python3 -m unittest discover -s rp2040zero_platform/tests -t . -v`
Expected: 31 tests, `OK`.

Run: `cd /home/loki/skeletyl_hardware && freecadcmd rp2040zero_platform/rp2040zero_platform.py`
Expected output includes `valid: True solids: 1`, a bbox with `Y -31.30..27.8`, `Z -5.22..4.50`, and three `wrote` lines. Confirm `ls rp2040zero_platform/*.stl` exists (git-ignored).

- [ ] **Step 5: Write the reference fetch script and READMEs**

`refs/fetch.sh`:
```bash
#!/bin/sh
# Clone the reference sources next to this script (git-ignored).
set -e
cd "$(dirname "$0")"
[ -d splinktegrated ] || git clone --depth 1 https://github.com/Bastardkb/splinktegrated
[ -d Skeletyl ] || git clone --depth 1 https://github.com/Bastardkb/Skeletyl
echo "case STL: $(pwd)/Skeletyl/V4/case_v4_103.stl"
```
`chmod +x refs/fetch.sh`. Because `refs/` is git-ignored, force-add just the script: `git add -f refs/fetch.sh`.

`rp2040zero_platform/README.md`:
```markdown
# RP2040-Zero + TRRS platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. Holds a Waveshare
RP2040-Zero **components down** (USB-C in the case's USB slot, BOOT/RESET
reachable from below) and a PJ-320A TRRS jack in the case's jack hole. Bolts
to the two existing M4 heat-set rings with M4 × 6–8 mm button-head screws.

Design notes and measurements: `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    freecadcmd rp2040zero_platform.py        # writes .FCStd / .step / .stl here
    python3 -m unittest discover -s tests -t .. -v   # from this directory

Or open `rp2040zero_platform.py` in FreeCAD as a macro; a `Platform` object is
added to the active document.

## Print

Flat, pockets up, no supports. 0.2 mm layers, 3+ perimeters. Mirror the STL in
the slicer for the other half, exactly like the case.

## Assemble

1. Drop the PJ-320A into its pocket, nose toward the wall; legs hang through
   the slots (either orientation). Solder its wires from underneath.
2. Place the RP2040-Zero upside down: USB-C toward the wall resting on the
   cradle, far corners on the two seats. Wire it on the flat (label) side,
   which faces up. Zip-tie through the slots (under the plate, over the board).
3. Slip the ring pockets over the case rings, screw down.
4. BOOT/RESET face the bottom plate: remove the plate and press through the
   floor window with a toothpick. Put `QK_BOOT` in the keymap; the Splinky
   `RP2040_BOOTLOADER_DOUBLE_TAP_RESET*` settings do not apply.

## Before printing, check on your parts

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | Sets the board height; USB-C must land in the 7 mm slot |
| `USB_OVERHANG` | 1.3 | How far the shell sticks past the PCB edge |
| `BOARD_X_SHIFT` | 0.0 | Sideways nudge if the USB-C is off-centre in the slot |
| `JACK_AXIS_H` | 2.5 | Barrel axis height above the jack's mounting face |
| `JACK_AXIS_X` | 5.0 | Sideways nudge for the jack |

All other dimensions are in the parameter block at the top of the script.
```

Replace `README.md` at the repo root with:
```markdown
# Skeletyl hardware

3D-printed parts for a hand-wired Bastardkb Skeletyl (V4 case).

- `rp2040zero_platform/` — platform holding a Waveshare RP2040-Zero and a
  PJ-320A TRRS jack in place of the Splinktegrated PCB. See its README.
- `docs/superpowers/` — design specs and implementation plans.
- `refs/fetch.sh` — clones the Bastardkb reference repos (case STL, PCB) into
  the git-ignored `refs/` folder; needed only for `check_clearance.py`.

Requires FreeCAD ≥ 1.0 (`freecadcmd` on the PATH) and numpy.
```

- [ ] **Step 6: Commit**

```bash
cd /home/loki/skeletyl_hardware
chmod +x refs/fetch.sh
git add -f refs/fetch.sh
git add README.md rp2040zero_platform/
git commit -m "Add headless export, entry points and documentation

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Clearance check against the case STL

**Files:**
- Create: `rp2040zero_platform/check_clearance.py`
- Modify: `rp2040zero_platform/README.md` (results section)

**Interfaces:**
- Consumes: `rp2040zero_platform.build()`, the case STL from `refs/Skeletyl/V4/case_v4_103.stl`, the frame mapping from Global Constraints.
- Produces: `check_clearance.py [case.stl]` prints the number of sampled case-surface points that fall inside the platform solid, grouped by distance to the nearest ring centre, and writes `sec_ringA.png`, `sec_ringB.png`, `sec_jack.png`, `sec_usb.png` (platform in red over case in blue) next to the script. Exit status 1 if any offending point lies farther than `RING_OD/2 + 0.35` from both ring centres (i.e. anything but the intentional ring/bore proximity).

- [ ] **Step 1: Fetch the references and write the check script**

Run: `cd /home/loki/skeletyl_hardware && ./refs/fetch.sh`

`rp2040zero_platform/check_clearance.py`:
```python
"""Check the platform against the Skeletyl V4 case STL.

Usage: python3 check_clearance.py [path/to/case_v4_103.stl]

Samples the case surface inside the platform's bounding box and reports
sample points that fall inside the platform solid. Only points hugging a
case ring (the Ø10.4 bore around the Ø10 ring) are tolerated. Also writes
four cross-section PNGs (platform red, case blue) for eyeballing.
"""
import os
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freecad_path  # noqa: F401,E402
import rp2040zero_platform as rp  # noqa: E402

import MeshPart  # noqa: E402
from FreeCAD import Vector  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CASE = os.path.join(HERE, "..", "refs", "Skeletyl", "V4", "case_v4_103.stl")
SAMPLE_STEP = 0.25     # mm between surface samples
RING_TOL = 0.35        # tolerated radial proximity to a case ring


def load_stl(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    rec = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    return np.frombuffer(d[84:84 + n * 50], dtype=rec)['v'].astype(float)


def case_to_platform(tris):
    """(x, y, z)_case -> (x + 94.136, z + 30.599, y)."""
    out = np.empty_like(tris)
    out[..., 0] = tris[..., 0] + 94.136
    out[..., 1] = tris[..., 2] + 30.599
    out[..., 2] = tris[..., 1]
    return out


def sample_surface(tris, step):
    """Points on every triangle on a barycentric grid of spacing <= step."""
    out = []
    for a, b, c in tris:
        longest = max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b))
        n = max(1, int(np.ceil(longest / step)))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        u, v = i[m] / n, j[m] / n
        out.append(a + u[:, None] * (b - a) + v[:, None] * (c - a))
    return np.vstack(out)


def platform_mesh(shape):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1)
    return np.array([[list(p) for p in f.Points] for f in m.Facets])


def section(tris, axis, val, u_axis, v_axis):
    """Polyline segments of the mesh cut by the plane axis=val, as (u, v) pairs."""
    segs = []
    for tri in tris:
        a = tri[:, axis]
        if a.min() > val or a.max() < val:
            continue
        pts = []
        for i in range(3):
            p, q = tri[i], tri[(i + 1) % 3]
            if (p[axis] - val) * (q[axis] - val) <= 0 and p[axis] != q[axis]:
                s = (val - p[axis]) / (q[axis] - p[axis])
                pts.append(p + s * (q - p))
        if len(pts) >= 2:
            segs.append(((pts[0][u_axis], pts[0][v_axis]), (pts[1][u_axis], pts[1][v_axis])))
    return segs


def write_png(fn, layers, lo, hi, res=0.05):
    """layers: list of (segments, rgb). Grid every 1 mm, bold every 5 mm."""
    W = int((hi[0] - lo[0]) / res) + 1
    H = int((hi[1] - lo[1]) / res) + 1
    img = np.full((H, W, 3), 255, np.uint8)
    for g in np.arange(np.ceil(lo[0]), hi[0], 1.0):
        i = int((g - lo[0]) / res)
        img[:, i] = [140, 140, 140] if g % 5 == 0 else [225, 225, 225]
    for g in np.arange(np.ceil(lo[1]), hi[1], 1.0):
        j = int((g - lo[1]) / res)
        img[j, :] = [140, 140, 140] if g % 5 == 0 else [225, 225, 225]
    for segs, rgb in layers:
        for (u0, v0), (u1, v1) in segs:
            n = int(np.hypot(u1 - u0, v1 - v0) / res) + 2
            for k in np.linspace(0, 1, n):
                i = int((u0 + k * (u1 - u0) - lo[0]) / res)
                j = int((v0 + k * (v1 - v0) - lo[1]) / res)
                if 0 <= i < W and 0 <= j < H:
                    img[j, i] = rgb
    img = img[::-1]
    raw = b''.join(b'\x00' + img[i].tobytes() for i in range(H))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    open(fn, 'wb').write(png)


def main(case_path):
    shape = rp.build()
    bb = shape.BoundBox
    case = case_to_platform(load_stl(case_path))
    lo = np.array([bb.XMin, bb.YMin, bb.ZMin]) - 1.0
    hi = np.array([bb.XMax, bb.YMax, bb.ZMax]) + 1.0
    tmin, tmax = case.min(axis=1), case.max(axis=1)
    near = case[(tmax >= lo).all(1) & (tmin <= hi).all(1)]
    print("case triangles near the platform:", len(near))

    pts = sample_surface(near, SAMPLE_STEP)
    pts = pts[((pts >= lo) & (pts <= hi)).all(1)]
    print("sampled case surface points:", len(pts))
    bad = np.array([p for p in pts if shape.isInside(Vector(*p), 1e-6, True)])
    print("case points inside the platform:", len(bad))

    fatal = 0
    if len(bad):
        rings = np.array(rp.RING_CENTRES)
        d = np.min(np.linalg.norm(bad[:, None, :2] - rings[None, :, :], axis=2), axis=1)
        ring_ok = d <= rp.RING_OD / 2 + RING_TOL
        print("  within %.2f mm of a ring (expected, bore clearance): %d" % (rp.RING_OD / 2 + RING_TOL, ring_ok.sum()))
        others = bad[~ring_ok]
        fatal = len(others)
        for p in others[:40]:
            print("  COLLISION at X %.2f Y %.2f Z %.2f" % tuple(p))
        if fatal > 40:
            print("  ... and %d more" % (fatal - 40))

    plat = platform_mesh(shape)
    ax, ay = rp.RING_A
    bx, by = rp.RING_B
    # (file, axis, case plane, platform plane, u, v): Y-Z sections through the
    # rings, the jack axis and the USB centre; plus an X-Z "rear view" that
    # overlays the wall openings (cut inside the wall) with the platform's
    # rearmost features (cut just inside its rear edge).
    views = [
        ("sec_ringA.png", 0, ax, ax, 1, 2),
        ("sec_ringB.png", 0, bx, bx, 1, 2),
        ("sec_jack.png", 0, rp.JACK_AXIS_X, rp.JACK_AXIS_X, 1, 2),
        ("sec_usb.png", 0, rp.BOARD_CX, rp.BOARD_CX, 1, 2),
        ("sec_wall.png", 1, rp.WALL_INNER_Y - 0.5, rp.PLATE_REAR_Y + 0.5, 0, 2),
    ]
    for fn, axis, case_val, plat_val, u, v in views:
        layers = [(section(case, axis, case_val, u, v), (40, 90, 220)),
                  (section(plat, axis, plat_val, u, v), (220, 30, 30))]
        write_png(os.path.join(HERE, fn), layers, lo[[u, v]], hi[[u, v]])
        print("wrote", fn)
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CASE))
```

- [ ] **Step 2: Run the check**

Run: `cd /home/loki/skeletyl_hardware && python3 rp2040zero_platform/check_clearance.py`  (takes a minute or two)
Expected: prints counts, `case points inside the platform:` small (ring-proximity only), no `COLLISION` lines, exit status 0, five PNGs written. Open each PNG (Read tool) and confirm: red bore encloses the blue ring with a visible gap; jack pocket walls clear the wall; USB cradle/rails clear the wall; nothing red crosses blue.

If `COLLISION` lines appear: cluster them by (X, Y) and identify the feature (rail, ring pocket outer, jack wall, plate outline). Fix by adjusting the relevant parameter in the spec's spirit (e.g. `POCKET_OD`, `PLATE_REAR_Y`, rail extents) — never by loosening the check — and note the change in the spec's Geometry section.

- [ ] **Step 3: Record the result and commit**

Append to `rp2040zero_platform/README.md`:
```markdown
## Clearance check

    ./refs/fetch.sh
    python3 rp2040zero_platform/check_clearance.py

Samples the case surface and reports any sample inside the platform (only
bore/ring proximity is allowed) and writes `sec_*.png` cross-sections.
Last run: <date> — <N> points inside, all within the ring bores; no collisions.
```
Fill in the date and count from the run.

```bash
cd /home/loki/skeletyl_hardware
git add rp2040zero_platform/check_clearance.py rp2040zero_platform/README.md
git commit -m "Add clearance check against the Skeletyl V4 case STL

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Execution notes (rulings made while running this plan)

- Task 2: bbox test expectations corrected to the real geometry (XMin −4.04, XMax 37.57, YMax 27.76); the plan's estimates ignored the −0.31° rotation.
- Task 4: the rail test probed inside a zip-tie slot; probe moved to Y = −15 (between the slots). Spec slot positions kept.
- Task 6: ring B's boss reached Y = −34.7 (into the case wall) — `build()` now intersects the whole part with Y ≥ `PLATE_REAR_Y`; `RingPocketTest.test_nothing_behind_rear_trim` pins it.
- Task 7: the clearance check found the bare-cylinder ring pockets colliding with the case. The case rings are not free-standing: ring A hangs off a slanted wall at X ≈ −4.2…−5.1 with fillets filling the X < 0 side below Z = 0 (their top face flush with the ring top); ring B is a blob with a flat face at X = 30.9, top at Z = +0.25, free only in the 15°…195° sector, with the rear wall 3.5 mm from the screw axis. Task 3's ring-pocket code was replaced by: full Ø9.2 seat discs (`CAP_SEAT_D`), bosses kept only in the measured free regions (`make_ring_keep`: ring A X ≥ −3.8 and X ≥ 0.5 below Z = 0.1; ring B a half-space 0.5 mm past the centre toward 105°), per-ring tops (`RING_TOP_Z`), a flat-face cutter for ring B, and `RING_A_BLOB_GAP = 0.1` so the boss clears the blob's flush top face. Screw heads must be ≤ Ø7 (DIN 912). `check_clearance.py` is exactly the Task 7 code; final run: 13486 sampled case points inside the part, all ring-top/bore contact, 0 collisions, exit 0.
- Final review: the jack shelf floor sat 1.22 mm below the plate (unprintable flat) and the right rail stood in ring B's screw-head footprint. Plate bottom is now derived from the jack shelf (`PLATE_Z0 = JACK_BLOCK_Z0`, `JACK_FLOOR_T = 1.0` → Z −4.72), the right rail starts at `RING_B_FLAT_Y_TOP + RAIL_R_GAP`, `WINDOW_INSET_X = 1.5`, ring A's boss exists only for X ≥ 0.5 (seat disc carries the head), `HEAD_D = 7.0` with a head-sweep test and a bed-contact test. Clearance re-run: 13476 contact points, 0 collisions.
- Post-review: `freecadcmd file.py` runs the file with `__name__` = basename, so `main()` never ran; `_run_as_script()` now also detects that case.
