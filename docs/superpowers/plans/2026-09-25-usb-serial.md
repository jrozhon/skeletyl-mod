# USB-C Serial Link Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the TRRS jack with a mid-mount USB-C breakout: a modified Skeletyl V4 case STL with a USB-C slot where the jack hole was, and a simplified platform (plate, screw seats, window, two ledges, one pedestal).

**Architecture:** `rp2040zero_platform.py` stays the single source of truth for the platform frame and all case-interface numbers, including the new slot position. A new `case_usb_serial.py` imports those numbers, turns the case STL into an OCC solid in the platform frame, fuses a plug into the old hole, cuts the stadium slot and writes the STL back in case coordinates. `check_clearance.py` checks the platform against the *modified* case.

**Tech Stack:** FreeCAD 1.1 Python modules (`FreeCAD`, `Part`, `Mesh`, `MeshPart`) from the system python via `freecad_path`, numpy, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-25-skeletyl-usb-serial-design.md`

## Global Constraints

- Frame: origin ring A centre, X toward ring B, Y toward the user, Z up, Z 0 = ring tops. Case STL → platform: `X = x + 94.136`, `Y = z + 30.599`, `Z = y`.
- New slot: stadium 9.82 × 3.62, centre **X 6.60, Z −1.25** (X 1.69…11.51, Z −3.06…0.56), straight along Y through the wall; cutter Y −37.5…−33.5.
- Fill: Ø6.6 on the old hole axis X 5.10, Z −1.60, Y −36.02…−34.10.
- Breakout: shell 8.94 × 3.2 × 9.0 long, PCB 9.0 wide × 5.0 tail × ≤ 0.8, centred in the shell height; shell face 1.0 behind the wall's outer face (Y −35.07).
- Pedestal: X 2.13…11.07, Y −31.6…−26.07, Z −3.75…−2.85, clipped by the left-wall outline.
- Plate outline unchanged from rev. 2: X −4.6…31.8, Y −31.6…−8.47.
- Always `import FreeCAD` before `Mesh` / `MeshPart`: importing `Mesh` first segfaults under the system python.
- Generated files (`*.stl`, `*.step`, `*.FCStd`, `*.png`) are git-ignored and never committed.
- Run the tests from `rp2040zero_platform/`: `python3 -m unittest discover -s tests -t .. -v`.

## Review Focus

- The case STL is not a valid solid (14 self-intersecting facet pairs near platform X 40, a few non-manifold edges); OCC still produces one solid, but `isValid()` is False on input and output. Nothing outside the edit region may change → `test_nothing_changes_outside_the_edit_region` (Task 1).
- The plug's outer end must not stand proud where the wall's outer face curves into the corner → `test_plug_stays_inside_the_outer_face` (Task 1).
- A breakout PCB thinner than 0.8 mm, or with pads underneath, must still fit: nothing under the tail → `test_serial_pcb_tail_is_free` (Task 2).
- Removed rails/ribs must not linger as stray bits: only the ledges and the pedestal may stand above the plate → `test_only_ledges_and_pedestal_stand_above_the_plate` (Task 2).
- `refs/` not fetched: the case tests skip with a message, and the scripts exit with a clear error instead of a traceback → skip decorator (Task 1) and `main()` checks (Tasks 1, 3).

---

### Task 1: Case modification script

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (case-interface section: add the slot constants)
- Create: `rp2040zero_platform/case_usb_serial.py`
- Test: `rp2040zero_platform/tests/test_case_usb_serial.py`

**Interfaces:**
- Consumes: `rp.JACK_AXIS_X`, `rp.JACK_HOLE_Z`, `rp.JACK_HOLE_D`, `rp.WALL_OUTER_Y`, `rp.WALL_RECESS_Y`, `rp.USB_SLOT_X`, `rp.USB_SLOT_Z`; `check_clearance.load_stl`, `check_clearance.case_to_platform` (numpy, test only).
- Produces (in `rp2040zero_platform.py`): `CORNER_LUMP_X = 1.60`, `SER_SLOT_CX = 6.60`, `SER_SLOT_W`, `SER_SLOT_X` (tuple), `SER_SLOT_Z` (tuple).
- Produces (in `case_usb_serial.py`): `DEFAULT_CASE: str`, `OUT_PATH: str`, `EDIT_REGION: ((x0,x1),(y0,y1),(z0,z1))`, `load_case(path) -> Part.Solid` (platform frame), `make_plug() -> Part.Shape`, `make_slot_cutter() -> Part.Shape`, `modify(case) -> Part.Shape`, `export(shape, path) -> None` (writes the STL in case coordinates), `main(case_path=DEFAULT_CASE, out_path=OUT_PATH) -> int`.

- [ ] **Step 1: Add the slot constants to the platform script**

In `rp2040zero_platform.py`, change the jack-hole comments and add the new constants directly after `USB_SLOT_Z = (-3.06, 0.56)`:

```python
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
```

(The three `JACK_*` lines replace the existing ones; `USB_SLOT_X/Z` are unchanged and only shown for placement.)

- [ ] **Step 2: Write the failing tests**

Create `rp2040zero_platform/tests/test_case_usb_serial.py`:

```python
import os
import tempfile
import unittest

import numpy as np

from rp2040zero_platform import case_usb_serial as cs
from rp2040zero_platform import rp2040zero_platform as rp
from rp2040zero_platform.check_clearance import load_stl, case_to_platform

from FreeCAD import Vector

TOL = 1e-6


def inside(shape, x, y, z):
    return shape.isInside(Vector(x, y, z), TOL, True)


def vertex_keys(v):
    """Integer micrometre keys covering floor/ceil per axis, so a vertex that
    moved by float round-off (< 1 um) still matches."""
    lo = np.floor(v * 1000.0).astype(np.int64)
    keys = set()
    for d in np.ndindex(2, 2, 2):
        keys.update(map(tuple, lo + np.array(d)))
    return keys


@unittest.skipUnless(os.path.exists(cs.DEFAULT_CASE), "case STL missing: run refs/fetch.sh")
class CaseModTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = cs.load_case(cs.DEFAULT_CASE)
        cls.mod = cs.modify(cls.orig)

    def test_one_solid(self):
        self.assertEqual(len(self.mod.Solids), 1)

    def test_old_hole_filled_above_and_below_the_slot(self):
        for z in (rp.JACK_HOLE_Z + 2.3, rp.JACK_HOLE_Z - 2.3):   # 0.70 and -3.90: outside the slot
            for y in (-35.9, -35.1, -34.2):
                self.assertFalse(inside(self.orig, rp.JACK_AXIS_X, y, z), (y, z))
                self.assertTrue(inside(self.mod, rp.JACK_AXIS_X, y, z), (y, z))

    def test_slot_open_through_the_wall(self):
        x0, x1 = rp.SER_SLOT_X
        z0, z1 = rp.SER_SLOT_Z
        cz = (z0 + z1) / 2.0
        flat = (rp.SER_SLOT_W - (z1 - z0)) / 2.0     # half length of the straight part
        pts = [(x0 + 0.1, cz), (rp.SER_SLOT_CX, cz), (x1 - 0.1, cz),
               (rp.SER_SLOT_CX - flat, z0 + 0.1), (rp.SER_SLOT_CX + flat, z1 - 0.1)]
        for y in (rp.WALL_OUTER_Y + 0.05, -35.0, rp.WALL_RECESS_Y - 0.05):
            for x, z in pts:
                self.assertFalse(inside(self.mod, x, y, z), (x, y, z))

    def test_wall_solid_just_outside_the_slot(self):
        x0, x1 = rp.SER_SLOT_X
        z0, z1 = rp.SER_SLOT_Z
        cz = (z0 + z1) / 2.0
        for x, z in ((x0 - 0.1, cz), (x1 + 0.1, cz), (rp.SER_SLOT_CX, z1 + 0.1), (rp.SER_SLOT_CX, z0 - 0.1)):
            self.assertTrue(inside(self.mod, x, -35.0, z), (x, z))

    def test_rp2040_slot_and_web_untouched(self):
        self.assertFalse(inside(self.mod, sum(rp.USB_SLOT_X) / 2, -35.0, sum(rp.USB_SLOT_Z) / 2))
        web_x = (rp.SER_SLOT_X[1] + rp.USB_SLOT_X[0]) / 2
        self.assertTrue(inside(self.mod, web_x, -35.0, -1.25))

    def test_plug_stays_inside_the_outer_face(self):
        # Walk in from outside along +Y on a ring just outside the plug: the
        # original wall must start at or behind the plug's outer end.
        r = cs.PLUG_D / 2.0 + 0.05
        plug_y0 = rp.WALL_OUTER_Y + cs.PLUG_OUTER_GAP
        for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            x = rp.JACK_AXIS_X + r * np.cos(a)
            z = rp.JACK_HOLE_Z + r * np.sin(a)
            ys = np.arange(-38.0, -33.9, 0.01)
            first = next((y for y in ys if inside(self.orig, x, y, z)), None)
            self.assertIsNotNone(first, (x, z))
            self.assertLessEqual(first, plug_y0 + 0.01, (x, z))

    def test_volume_change_is_fill_minus_slot(self):
        # fill (hole + chamfer, ~+42) minus slot through 2 mm (~-65): measured -23.3
        self.assertAlmostEqual(self.mod.Volume - self.orig.Volume, -23.3, delta=2.0)

    def test_nothing_changes_outside_the_edit_region(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "case.stl")
            cs.export(self.mod, out)
            new = case_to_platform(load_stl(out)).reshape(-1, 3)
        old = case_to_platform(load_stl(cs.DEFAULT_CASE)).reshape(-1, 3)
        (x0, x1), (y0, y1), (z0, z1) = cs.EDIT_REGION
        outside = ~((new[:, 0] > x0) & (new[:, 0] < x1) & (new[:, 1] > y0) & (new[:, 1] < y1)
                    & (new[:, 2] > z0) & (new[:, 2] < z1))
        keys = vertex_keys(old)
        stray = [p for p in new[outside] if tuple(np.round(p * 1000.0).astype(np.int64)) not in keys]
        self.assertEqual(stray[:5], [])

    def test_export_is_in_case_coordinates(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "case.stl")
            cs.export(self.mod, out)
            new = load_stl(out).reshape(-1, 3)
        old = load_stl(cs.DEFAULT_CASE).reshape(-1, 3)
        np.testing.assert_allclose(new.min(0), old.min(0), atol=0.01)
        np.testing.assert_allclose(new.max(0), old.max(0), atol=0.01)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd rp2040zero_platform && python3 -m unittest tests.test_case_usb_serial -v`
Expected: ERROR — `ImportError: cannot import name 'case_usb_serial'`.

- [ ] **Step 4: Write the case script**

Create `rp2040zero_platform/case_usb_serial.py`:

```python
"""Skeletyl V4 case with the TRRS jack hole replaced by a USB-C slot.

Fills the old Ø5.2 jack hole in the rear wall and cuts a 9.82 x 3.62 stadium
slot (the same shape as the RP2040's USB slot) for a mid-mount USB-C
breakout, then writes the STL back in the case's own coordinates, so it
prints (and mirrors for the other half) exactly like the original.

The case STL is not a perfectly valid solid (a few self-intersecting facets
far from the rear-left corner); OCC still gives one solid and the tests check
that nothing outside EDIT_REGION changes.

Usage: python3 case_usb_serial.py [path/to/case_v4_103.stl]   (~90 s)
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
PLUG_OUTER_GAP = 0.05          # plug's outer end this far inside the wall's outer face
SLOT_CUT_Y = (-37.5, -33.5)    # slot cutter runs through the whole wall along Y
# Platform-frame box around the rear-left wall; the modification stays inside it.
EDIT_REGION = ((-1.0, 13.0), (-38.0, -33.0), (-6.0, 2.5))

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
    export(shape, out_path)
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd rp2040zero_platform && python3 -m unittest tests.test_case_usb_serial -v`
Expected: 9 tests OK (takes ~3 min: the case is loaded and cut once per class; the two export tests re-mesh it).

If `test_plug_stays_inside_the_outer_face` fails, the outer face curves inside the plug footprint: reduce `PLUG_D` toward 6.45 (still over the ≈Ø6.4 mouth) or increase `PLUG_OUTER_GAP`, and re-run.

- [ ] **Step 6: Run the script and the existing platform tests**

Run: `cd rp2040zero_platform && python3 case_usb_serial.py && python3 -m unittest tests.test_platform -v`
Expected: `solids: 1  volume change -23.3 mm^3`, `wrote .../case_v4_103_usb_serial.stl`; platform tests still pass (only constants were added).

- [ ] **Step 7: Commit**

```bash
git add rp2040zero_platform/rp2040zero_platform.py rp2040zero_platform/case_usb_serial.py rp2040zero_platform/tests/test_case_usb_serial.py
git commit -m "Case mod: fill the TRRS hole, cut a USB-C slot at X 6.60"
```

---

### Task 2: Simplified platform with the serial pedestal

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (docstring, parameters, derived values, frame/jack functions, `build`, `make_components`, `main`)
- Test: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Consumes: `SER_SLOT_CX`, `SER_SLOT_X`, `SER_SLOT_Z`, `CORNER_LUMP_X` (Task 1).
- Produces: parameters `SER_W, SER_H, SER_SHELL_L, SER_PCB_W, SER_PCB_L, SER_PCB_T, SER_RECESS, PLATE_MARGIN`; derived `SER_CX, SER_CZ, SER_X0, SER_X1, SER_Z0, SER_FACE_Y, SER_SHELL_Y1, SER_PCB_Y1, LEDGE_X0, LEDGE_X1, LEDGE_Y1`; functions `make_keep()`, `make_ledges()`, `make_pedestal()`; `make_components()` now returns [RP2040 PCB, RP2040 shell, serial shell, serial PCB tail]. Removed: every `JACK_*` parameter except the three case-interface ones, `RIB_*`, `RAIL_*`, `STOP_*`, `make_board_frame`, `make_jack_*`, `make_leg_slots`. `check_clearance.py` (Task 3) uses `SER_CX`, `WALL_OUTER_Y`, `BOARD_CX`.

- [ ] **Step 1: Rewrite the tests for the new platform**

In `tests/test_platform.py`:

1. In `test_extents`, replace `rp.RAIL_TOP_Z` with `rp.PCB_Z0` (the ledges are now the tallest feature).
2. Replace `test_clear_of_the_rear_wall` with:

```python
    def test_clear_of_the_rear_wall(self):
        self.assertGreaterEqual(rp.PLATE_REAR_Y, rp.WALL_INNER_Y + 0.3)
        # The board reaches into the wall recess, which is free from Z -5.5 to 3.
        self.assertGreater(rp.BOARD_Y0, rp.WALL_RECESS_Y + 0.2)
        self.assertLess(rp.PCB_Z1, 3.0)
```

3. Replace `test_clear_of_ring_b` with:

```python
    def test_clear_of_ring_b(self):
        self.assertLessEqual(rp.LEDGE_X1, rp.RING_B_FLAT_X - 0.5)
        self.assertLessEqual(rp.BOARD_X1, rp.RING_B_FLAT_X - 0.5)
```

4. Delete `test_rails_and_front_stop_stand_above_the_pcb` and the whole `# -- jack pocket` section (`test_jack_axis_matches_the_case_hole`, `test_jack_pocket_floor_between_the_slots`, `test_leg_slots_on_both_sides_open_at_the_rear`, `test_ribs_and_end_stop`).
5. Add, after `test_components_clear_the_plate`:

```python
    def test_only_ledges_and_pedestal_stand_above_the_plate(self):
        ledges = ((rp.LEDGE_X0, rp.LEDGE_X0 + rp.LEDGE_W), (rp.LEDGE_X1 - rp.LEDGE_W, rp.LEDGE_X1))
        for x in [rp.LEFT_EDGE[0][0] + 0.25 + 0.5 * i for i in range(80)]:
            for y in [rp.PLATE_REAR_Y + 0.25 + 0.5 * j for j in range(60)]:
                if not inside(self.shape, x, y, rp.PLATE_Z1 + 0.3):
                    continue
                in_ledge = any(a <= x <= b for a, b in ledges) and y <= rp.LEDGE_Y1
                in_pedestal = rp.SER_X0 <= x <= rp.SER_X1 and y <= rp.SER_SHELL_Y1
                self.assertTrue(in_ledge or in_pedestal, (x, y))

    def test_old_jack_features_gone(self):
        # plate is full thickness where the pocket and the leg slots were
        for x in (rp.JACK_AXIS_X - 2.6, rp.JACK_AXIS_X, rp.JACK_AXIS_X + 2.6):
            self.assertTrue(inside(self.shape, x, -26.0, rp.PLATE_Z0 + 0.1), x)
            self.assertTrue(inside(self.shape, x, -26.0, rp.PLATE_Z1 - 0.1), x)

    # -- USB-C serial breakout -----------------------------------------------
    def test_serial_shell_centred_in_the_new_slot(self):
        self.assertAlmostEqual(rp.SER_CZ, sum(rp.SER_SLOT_Z) / 2)
        self.assertAlmostEqual(rp.SER_CX, sum(rp.SER_SLOT_X) / 2)
        self.assertGreater(rp.SER_Z0, rp.SER_SLOT_Z[0])
        self.assertLess(rp.SER_Z0 + rp.SER_H, rp.SER_SLOT_Z[1])
        self.assertGreater(rp.SER_X0, rp.SER_SLOT_X[0])
        self.assertLess(rp.SER_X1, rp.SER_SLOT_X[1])
        self.assertLess(rp.SER_FACE_Y, rp.WALL_RECESS_Y)
        self.assertGreater(rp.SER_FACE_Y, rp.WALL_OUTER_Y)

    def test_serial_slot_clear_of_the_corner_and_the_usb_slot(self):
        self.assertGreater(rp.SER_SLOT_X[0], rp.CORNER_LUMP_X)
        self.assertGreaterEqual(rp.USB_SLOT_X[0] - rp.SER_SLOT_X[1], 3.0)   # web between the slots

    def test_serial_shell_clearances(self):
        self.assertGreaterEqual(rp.SER_X0 - rp.CORNER_LUMP_X, 0.4)
        self.assertGreaterEqual(rp.LEDGE_X0 - rp.SER_X1, 0.4)

    def test_pedestal_sets_the_shell_height(self):
        self.assertGreaterEqual(rp.SER_Z0 - rp.PLATE_Z1, 0.5)
        for y in (rp.PLATE_REAR_Y + 0.2, rp.SER_SHELL_Y1 - 0.2):
            self.assertTrue(inside(self.shape, rp.SER_CX, y, rp.SER_Z0 - EPS), y)
            self.assertFalse(inside(self.shape, rp.SER_CX, y, rp.SER_Z0 + EPS), y)
        self.assertFalse(inside(self.shape, rp.SER_CX, rp.SER_SHELL_Y1 + EPS, rp.PLATE_Z1 + EPS))

    def test_serial_pcb_tail_is_free(self):
        y = (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2
        for x in (rp.SER_CX - rp.SER_PCB_W / 2 + 0.1, rp.SER_CX, rp.SER_CX + rp.SER_PCB_W / 2 - 0.1):
            self.assertFalse(inside(self.shape, x, y, rp.PLATE_Z1 + EPS), x)
            self.assertFalse(inside(self.shape, x, y, rp.SER_CZ), x)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd rp2040zero_platform && python3 -m unittest tests.test_platform -v`
Expected: ERROR/FAIL — `AttributeError: module ... has no attribute 'LEDGE_X1'` (and `SER_*`), and `test_only_ledges_and_pedestal_stand_above_the_plate` fails on the rails/ribs.

- [ ] **Step 3: Update the parameters and derived values**

In `rp2040zero_platform.py`:

Module docstring, first paragraph →

```python
"""Platform for a Waveshare RP2040-Zero + a mid-mount USB-C breakout (the
half-to-half serial link) in a Skeletyl V4 case, replacing the Splinktegrated
PCB. The case's TRRS hole is replaced by a USB-C slot: see case_usb_serial.py.

A flat plate screwed from below against the underside of the case's two M4
controller rings. The RP2040-Zero (components down) rests on two ledges so
its USB-C sits in the case slot; the breakout's shell sits on a low pedestal
in the new slot. Both are fixed with hot glue.
```

(keep the Frame / Run paragraphs as they are).

In the RP2040 section, change the `BOARD_CLEAR` comment and replace the `RAIL_T`, `RAIL_ABOVE_PCB` lines:

```python
BOARD_CLEAR = 0.3              # PCB side/front edge -> ledge outer edge / ledge end
LEDGE_W = 1.2                  # ledge walls under the long PCB edges (their inner 0.9 mm carry the PCB)
PLATE_MARGIN = 1.5             # plate beyond the right ledge and in front of the ledges (rev. 2 outline)
```

Replace the whole `# PJ-320A TRRS jack` parameter section with:

```python
# ---------------------------------------------------------------------------
# USB-C serial breakout: mid-mount receptacle, PCB through the shell's middle
# ---------------------------------------------------------------------------
SER_W = 8.94                   # shell width (X)
SER_H = 3.2                    # shell height (the slot is 3.62: 0.21 mm each way)
SER_SHELL_L = 9.0              # shell length (Y)
SER_PCB_W = 9.0                # breakout PCB width
SER_PCB_L = 5.0                # PCB tail behind the shell (pads U, D+, D-, G)
SER_PCB_T = 0.8                # PCB thickness (thinner is fine: the tail is free)
SER_RECESS = 1.0               # shell front face this far behind the wall's outer face
```

In "Derived values", replace everything from `RAIL_X0 = ...` to the end of the section (`JACK_STOP_Y0 = ...`) with:

```python
LEDGE_X0 = BOARD_X0 - BOARD_CLEAR            # left ledge outer edge
LEDGE_X1 = BOARD_X1 + BOARD_CLEAR            # right ledge outer edge
LEDGE_Y1 = BOARD_Y1 + BOARD_CLEAR            # ledges end here
PLATE_FRONT_Y = LEDGE_Y1 + PLATE_MARGIN
PLATE_RIGHT_X = LEDGE_X1 + PLATE_MARGIN

SER_CX = SER_SLOT_CX
SER_CZ = (SER_SLOT_Z[0] + SER_SLOT_Z[1]) / 2.0
SER_X0 = SER_CX - SER_W / 2.0
SER_X1 = SER_CX + SER_W / 2.0
SER_Z0 = SER_CZ - SER_H / 2.0                # shell underside = pedestal top
SER_FACE_Y = WALL_OUTER_Y + SER_RECESS       # shell front face
SER_SHELL_Y1 = SER_FACE_Y + SER_SHELL_L      # shell rear = pedestal front
SER_PCB_Y1 = SER_SHELL_Y1 + SER_PCB_L        # end of the PCB tail
```

and delete `RAIL_TOP_Z = PCB_Z1 + RAIL_ABOVE_PCB`.

- [ ] **Step 4: Replace the geometry functions**

In `make_plate()`, replace the two `keep` lines with a call to a new helper, and add the helper above it:

```python
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
    plate = fuse_all([body, pad_a, neck_a, pad_b])
    return plate.common(make_keep()).cut(make_window())
```

Replace the `# Board frame` section and the whole `# Jack pocket` section (`make_board_frame`, `make_jack_ribs`, `make_jack_pocket`, `make_leg_slots`) with:

```python
# ---------------------------------------------------------------------------
# Supports
# ---------------------------------------------------------------------------
def make_ledges():
    """Ledges under the long PCB edges, plate to the PCB's component side."""
    return fuse_all([
        box(LEDGE_X0, LEDGE_X0 + LEDGE_W, PLATE_REAR_Y, LEDGE_Y1, PLATE_Z0, PCB_Z0),
        box(LEDGE_X1 - LEDGE_W, LEDGE_X1, PLATE_REAR_Y, LEDGE_Y1, PLATE_Z0, PCB_Z0),
    ])


def make_pedestal():
    """Block under the serial USB-C shell: puts it at the slot height."""
    return box(SER_X0, SER_X1, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, SER_Z0).common(make_keep())
```

Replace `build()` and `make_components()`:

```python
def build():
    """Return the finished platform as a single solid."""
    shape = make_plate().fuse(make_ledges()).fuse(make_pedestal())
    return shape.cut(make_screw_cutters()).removeSplitter()


def make_components():
    """The parts the platform holds, as one compound (for checks and drawings):
    RP2040 PCB and USB-C shell, serial USB-C shell and its PCB tail."""
    return Part.makeCompound([
        box(BOARD_X0, BOARD_X1, BOARD_Y0, BOARD_Y1, PCB_Z0, PCB_Z1),
        box(BOARD_CX - USB_W / 2, BOARD_CX + USB_W / 2, USB_FACE_Y, USB_FACE_Y + USB_L, USB_Z0, PCB_Z0),
        box(SER_X0, SER_X1, SER_FACE_Y, SER_SHELL_Y1, SER_Z0, SER_Z0 + SER_H),
        box(SER_CX - SER_PCB_W / 2, SER_CX + SER_PCB_W / 2, SER_SHELL_Y1, SER_PCB_Y1,
            SER_CZ - SER_PCB_T / 2, SER_CZ + SER_PCB_T / 2),
    ])
```

In `main()`, replace the second `print(...)` with:

```python
    print("USB-C shells Z %.2f..%.2f (RP2040) and %.2f..%.2f (serial) in slots %.2f..%.2f; head bottom Z %.2f (bottom plate %.2f)"
          % (USB_Z0, PCB_Z0, SER_Z0, SER_Z0 + SER_H, USB_SLOT_Z[0], USB_SLOT_Z[1], HEAD_BOTTOM_Z, BOTTOM_PLATE_Z))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd rp2040zero_platform && python3 -m unittest tests.test_platform -v`
Expected: all OK. Also `grep -nE "RAIL_|RIB_|STOP_|JACK_(BODY|NOSE|FACE|POCKET|LEG|STOP|FLOOR|X0|X1|Y0|Y1|AXIS_H|AXIS_Z)" rp2040zero_platform/*.py rp2040zero_platform/tests/*.py` prints nothing except `check_clearance.py` (fixed in Task 3).

- [ ] **Step 6: Build and eyeball the numbers**

Run: `cd rp2040zero_platform && python3 rp2040zero_platform.py`
Expected: `valid: True solids: 1`, bbox `X -4.60..41.66  Y -31.60..-8.47  Z -5.75..0.35`, serial shell `Z -2.85..0.35`.

- [ ] **Step 7: Commit**

```bash
git add rp2040zero_platform/rp2040zero_platform.py rp2040zero_platform/tests/test_platform.py
git commit -m "Rev. 3 platform: drop jack pocket, rails and stop; pedestal for the USB-C serial breakout"
```

---

### Task 3: Clearance check against the modified case, docs

**Files:**
- Modify: `rp2040zero_platform/check_clearance.py` (docstring, `DEFAULT_CASE`, `main`)
- Modify: `rp2040zero_platform/README.md`
- Modify: `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md` (one pointer line)

**Interfaces:**
- Consumes: `case_usb_serial.OUT_PATH` (Task 1), `rp.SER_CX`, `rp.BOARD_CX`, `rp.WALL_OUTER_Y` (Task 2).
- Produces: `check_clearance.main(case_path) -> int`, default case = the modified STL.

- [ ] **Step 1: Point the check at the modified case and update the views**

In `check_clearance.py`:

Replace the `DEFAULT_CASE = ...` line with:

```python
DEFAULT_CASE = os.path.join(HERE, "case_v4_103_usb_serial.stl")   # written by case_usb_serial.py
```

In the module docstring, change `Usage: python3 check_clearance.py [path/to/case_v4_103.stl]` to
`Usage: python3 check_clearance.py [path/to/case.stl]   (default: the modified case from case_usb_serial.py)`
and "Also writes five cross-section PNGs" stays five.

At the top of `main(case_path)` add:

```python
    if not os.path.exists(case_path):
        print("case STL not found: %s (run case_usb_serial.py first)" % case_path)
        return 1
```

Replace the `views` list and its comment, and the `phi` line, with:

```python
    # (file, axis, case plane, platform/component plane, u, v): Y-Z sections
    # through the rings and both USB-C centres; plus an X-Z "rear view" cut
    # inside the 2 mm wall showing both shells in their slots.
    views = [
        ("sec_ringA.png", 0, ax, ax, 1, 2),
        ("sec_ringB.png", 0, bx, bx, 1, 2),
        ("sec_serial.png", 0, rp.SER_CX, rp.SER_CX, 1, 2),
        ("sec_usb.png", 0, rp.BOARD_CX, rp.BOARD_CX, 1, 2),
        ("sec_wall.png", 1, rp.WALL_OUTER_Y + 1.5, rp.WALL_OUTER_Y + 1.5, 0, 2),
    ]
    plo = np.minimum(lo, [bb.XMin, rp.WALL_OUTER_Y - 1.0, bb.ZMin])
    phi = np.maximum(hi, [bb.XMax, bb.YMax, rp.PCB_Z1 + 2.0])
```

- [ ] **Step 2: Run the check**

Run: `cd rp2040zero_platform && python3 check_clearance.py; echo exit $?`
Expected: `case points inside the platform:` only on the Z −3.75 plane (ring faces + ring A fillet), no `COLLISION` lines, `exit 0`, five PNGs written. Open `sec_wall.png` and `sec_serial.png` (Read tool) and confirm: the serial shell (green) sits inside the new slot opening (blue) with a gap all round, the old round hole is gone, the pedestal (red) is under the shell's rear part. Note the "Last run" numbers for the README.

If there are collisions: stop and report them; do not tune geometry blindly.

- [ ] **Step 3: Rewrite the README**

Replace `rp2040zero_platform/README.md` with (fill `<N>` from Step 2's output):

```markdown
# RP2040-Zero + USB-C serial platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. A flat plate that
screws from below against the case's two M4 controller rings and holds a
Waveshare RP2040-Zero **components down** (USB-C in the case slot,
BOOT/RESET reachable through a window with the bottom plate off) and a
small mid-mount **USB-C breakout** for the half-to-half serial link, in a
USB-C slot that replaces the case's TRRS hole. Both parts are positioned by
the plate and fixed with hot glue.

Design notes and measurements: `docs/superpowers/specs/2026-09-25-skeletyl-usb-serial-design.md`
(rev. 3) on top of `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    ../refs/fetch.sh                             # the original case STL
    python3 case_usb_serial.py                   # -> case_v4_103_usb_serial.stl (~90 s)
    python3 rp2040zero_platform.py               # -> .FCStd / .step / .stl
    python3 -m unittest discover -s tests -t .. -v   # from this directory (~4 min)

`freecadcmd rp2040zero_platform.py` and opening it as a FreeCAD macro work
too.

## Print

- **Case:** `case_v4_103_usb_serial.stl` exactly like the original case
  (mirror it in the slicer for the other half). The only change is the rear
  wall: the round jack hole is filled and a 9.82 × 3.62 USB-C slot sits
  next to the RP2040's.
- **Platform:** underside (the face with the two screw counterbores) on the
  bed, no supports. 0.2 mm layers, 3 perimeters. Mirror for the other half.

## Assemble

The platform goes in from the bottom-plate side: the flat underside faces
the bottom plate, the ledges and pedestal point up toward the switches.

1. **Serial breakout.** Solder four wires to U, D+, D−, G first. Set the
   shell on the pedestal, push it into the new slot until its face is
   ~1 mm inside the wall, and hot-glue the shell to the pedestal. The PCB
   tail is free.
2. **Board.** Solder the wires to the RP2040-Zero's castellated pads first.
   Place it components down, USB-C toward the wall, long edges on the two
   ledges, push the connector into its slot, and hot-glue the PCB edges to
   the ledges.
3. Hold the plate against the ring faces and drive the two M4 × 8 screws
   from below.
4. BOOT/RESET face the bottom plate: remove it and press them through the
   window. Put `QK_BOOT` in the keymap as well.

## Fit checks before printing

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | RP2040 USB-C shell height; sets the board height |
| `BOARD_Z_SHIFT` / `BOARD_X_SHIFT` | 0.0 | Nudge the board if its shell catches in the slot |
| `SER_H` / `SER_W` | 3.2 / 8.94 | Serial shell; sets the pedestal height. The slot has 0.21 mm each way vertically, 0.44 sideways |
| `SER_SHELL_L` | 9.0 | Shell length; the pedestal ends under the shell's rear |
| `SER_RECESS` / `USB_RECESS` | 1.0 | Shell faces behind the wall's outer face (wall is 2 mm) |
| `HEAD_D` / `HEAD_H` | 8.0 / 2.5 | Screw head; sets the counterbore |

Both USB-C shells need rounded corners (≥ R0.8) to pass the slots'
full-radius ends.

## Clearance check

    python3 check_clearance.py            # against case_v4_103_usb_serial.stl

Reports any case surface sample inside the platform (only contact on the
rings' face plane is allowed) and writes `sec_*.png` cross-sections (case
blue, platform red, held parts green).
Last run: 2026-09-25 — <N> points on the Z −3.75 contact plane; no collisions.
```

- [ ] **Step 4: Point the rev. 2 spec at rev. 3**

In `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`, under the title line add:

```markdown
> Rev. 3 (2026-09-25, branch `usb-serial`) replaces the TRRS jack with a
> USB-C breakout and drops the rails and front stop: see
> `2026-09-25-skeletyl-usb-serial-design.md`.
```

- [ ] **Step 5: Full test run**

Run: `cd rp2040zero_platform && python3 -m unittest discover -s tests -t .. -v`
Expected: all tests OK, none skipped.

- [ ] **Step 6: Commit**

```bash
git add rp2040zero_platform/check_clearance.py rp2040zero_platform/README.md docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md
git commit -m "Clearance check against the modified case; README for rev. 3"
```
