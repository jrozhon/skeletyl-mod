# Rev. 4 Platform — Glue-Free Seating Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework `rp2040zero_platform.py` so the RP2040-Zero snaps in with no glue (a rigid left lip and a PLA snap hook on the right), and the USB-C breakout (back side up) is held by a middle wall, a tail lip and a glue pocket that locks the glue in mechanically.

**Architecture:** One parametric FreeCAD script builds the platform from boxes and prisms fused into one solid. Rev. 4 replaces `make_serial_stops()` with three new builders: `make_shell_wall()`, `make_middle_wall()` and `make_glue_pocket()`. It adds `make_hook()`, a groove plus a local widening in `make_plate()`, and `make_coupon()` for a test print. Tests probe the solid with `isInside` at points derived from the parameters.

**Tech Stack:** Python 3, FreeCAD `Part` (run headless through `freecad_path.py`), `unittest`, numpy (`check_clearance.py`).

**Spec:** `docs/superpowers/specs/2026-10-02-skeletyl-platform-rev4-glue-free-design.md`

## Global Constraints

- Frame: origin at ring A, X toward ring B, Y toward the user (rear wall at −Y), Z up, Z 0 on the ring tops; plate top Z −3.75, plate bottom (print bed) Z −5.75.
- The case, pin map, firmware, breakout and cable do not change. Only `rp2040zero_platform/` files and the docs change.
- Printed in **PLA**: the snap hook's bending strain 1.5·t·δ/L² must stay ≤ 1.5 %.
- Measured breakout: `SER_SHELL_L` 8.5 (shell + bump), `SER_L` 14.0 overall, mounted **back side up** (wire pads up, at the tail end).
- Zero pads: pad *k* centre at `BOARD_Y0 + ZERO_PAD1_Y + (k − 1) · 2.54`, pad 4 ≈ 10.0 mm from the USB-end PCB edge.
- The part stays one valid solid with a single bed face, printable without supports.
- Run the tests from the repository root: `python3 -m unittest rp2040zero_platform.tests.test_platform -v`.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **The board shifted sideways within its play** (0.3 mm between the middle wall and the corner stop): the left lip and the hook must still overlap the PCB. Pinned by `test_board_cannot_slip_off_a_lip` (Task 2).
2. **The breakout's SMD part and leads on the underside:** nothing may rise into the 0.8 mm under the tail behind the dam, and the dam must stay clear of the bump. Pinned by `test_glue_pocket_floor_and_dam` (Task 1).
3. **The hook arm touching the ledge or the groove walls** would stiffen it and break the PLA strain budget. Pinned by `test_hook_groove` and `test_hook_strain_ok_for_pla` (Task 2).
4. **New features colliding with the case** (ring B near the hook, the left wall near the pocket). Pinned by the `check_clearance.py` run in Task 4.
5. **Lips covering pads that carry wires** (GP0, GP1, GP27, and the breakout's tail-end pads). Pinned by `test_left_lip_over_free_pads`, `test_hook_clear_of_used_pads` (Task 2) and `test_tail_lip` (Task 1).

---

## File Structure

- Modify `rp2040zero_platform/rp2040zero_platform.py`: parameters, derived values, builders, `build()`, `make_components()`, `export()`, `make_coupon()`.
- Modify `rp2040zero_platform/tests/test_platform.py`: remove the rev. 3 serial-stop tests, add tests for each rev. 4 feature.
- Modify `rp2040zero_platform/check_clearance.py`: two new XZ sections.
- Modify `rp2040zero_platform/README.md`: assembly, fit checks, print notes, coupon, clearance date.
- Regenerate `rp2040zero_platform/rp2040zero_platform.{FCStd,step,stl}`, the new `hook_coupon.stl` and `sec_*.png`.

---

### Task 1: Breakout — measured lengths, shell wall, middle wall with tail lip, glue pocket

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (parameters at lines 97–108, derived values at 138–154, `make_serial_stops` at 246–260, `build` at 271–274)
- Test: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Produces (used by Tasks 2–4): parameters `LIP_OVER`, `LIP_GAP`, `LIP_T`, `MID_WALL_TOP_Z`, `SHELL_WALL_T`, `SER_LIP_L`, `POCKET_WALL_T`, `POCKET_FLOOR_GAP`, `DAM_GAP`, `DAM_T`, `POCKET_KEY_D`, `POCKET_KEY_DX`; derived `SER_TAIL_Z0`, `SER_TAIL_Z1`, `SER_LIP_X0`, `SER_LIP_Y1`, `SER_LIP_Z0`, `MID_X0`, `MID_X1`, `MID_Y1`, `POCKET_X0`, `POCKET_FLOOR_Z`, `DAM_Y0`, `DAM_Y1`, `DAM_TOP_Z`, `POCKET_KEY_Y`; builders `make_shell_wall()`, `make_middle_wall()`, `make_glue_pocket()`, `make_pocket_keys()`, all returning `Part.Shape`. In this task `MID_Y1` is a plain number (−17.69); Task 2 replaces it with the Zero lip's end.

- [ ] **Step 1: Replace the rev. 3 serial-stop tests with the rev. 4 breakout tests**

In `tests/test_platform.py`, delete these four methods entirely: `test_serial_stops_hold_the_tail_end`, `test_serial_side_arms_locate_the_pcb_sideways`, `test_right_serial_stop_locates_the_rp2040_left_edge`, `test_serial_pcb_tail_is_free`.

In `test_extents`, change the ZMax line to:

```python
        self.assertAlmostEqual(bb.ZMax, rp.MID_WALL_TOP_Z, places=4)
```

Replace `test_only_ledges_pedestal_and_corner_stops_stand_above_the_plate` with:

```python
    def test_only_known_features_stand_above_the_plate(self):
        ledges = ((rp.LEDGE_X0, rp.LEDGE_X0 + rp.LEDGE_W), (rp.LEDGE_X1 - rp.LEDGE_W, rp.LEDGE_X1))
        corners = ((rp.BOARD_X0 - rp.CORNER_GAP - rp.CORNER_T, rp.BOARD_X0 + rp.CORNER_REACH),
                   (rp.BOARD_X1 - rp.CORNER_REACH, rp.BOARD_X1 + rp.CORNER_GAP + rp.CORNER_T))
        for x in [rp.LEFT_EDGE[0][0] + 0.25 + 0.5 * i for i in range(80)]:
            for y in [rp.PLATE_REAR_Y + 0.25 + 0.5 * j for j in range(60)]:
                if not inside(self.shape, x, y, rp.PLATE_Z1 + 0.3):
                    continue
                known = [
                    any(a <= x <= b for a, b in ledges) and y <= rp.LEDGE_Y1,
                    rp.SER_X0 - rp.SHELL_WALL_T <= x <= rp.SER_X1 and y <= rp.SER_SHELL_Y1,   # pedestal + shell wall
                    rp.MID_X0 <= x <= rp.MID_X1 and y <= rp.MID_Y1,                            # middle wall
                    (rp.POCKET_X0 - rp.POCKET_WALL_T <= x <= rp.MID_X0
                     and rp.SER_SHELL_Y1 <= y <= rp.SER_STOP_Y1),                              # glue pocket
                    (any(a <= x <= b for a, b in corners)
                     and rp.BOARD_Y1 - rp.CORNER_SIDE_L <= y <= rp.CORNER_Y1),
                ]
                self.assertTrue(any(known), (x, y))
```

Add these tests in the `# -- USB-C serial breakout` section:

```python
    def test_serial_measured_lengths(self):
        self.assertAlmostEqual(rp.SER_SHELL_L, 8.5)
        self.assertAlmostEqual(rp.SER_L, 14.0)
        self.assertAlmostEqual(rp.SER_SHELL_Y1 - rp.SER_FACE_Y, 8.5)

    def test_rev3_serial_stops_are_gone(self):
        self.assertFalse(hasattr(rp, "make_serial_stops"))

    def test_shell_side_wall_locates_the_shell(self):
        y = rp.SER_SHELL_Y1 - 1.0
        x = rp.SER_X0 - rp.SHELL_WALL_T / 2
        self.assertTrue(inside(self.shape, x, y, rp.SER_CZ - EPS))
        self.assertFalse(inside(self.shape, x, y, rp.SER_CZ + EPS))      # low enough to tilt the part in
        self.assertFalse(inside(self.shape, rp.SER_X0 + EPS, y, rp.SER_Z0 + 0.5))   # line-to-line

    def test_middle_wall_beside_the_shell_stays_at_ledge_height(self):
        x = (rp.MID_X0 + rp.MID_X1) / 2
        y = (rp.PLATE_REAR_Y + rp.SER_SHELL_Y1) / 2
        self.assertTrue(inside(self.shape, x, y, rp.PCB_Z0 - EPS))
        self.assertFalse(inside(self.shape, x, y, rp.PCB_Z0 + EPS))      # GP0/GP1 wires cross here

    def test_middle_wall_is_the_tails_right_side_wall(self):
        self.assertAlmostEqual(rp.MID_X0, rp.SER_X1)
        self.assertAlmostEqual(rp.MID_X1, rp.BOARD_X0 - rp.BOARD_SIDE_GAP)
        self.assertGreaterEqual(rp.MID_X0 - rp.SER_PCB_X1, 0.0)
        self.assertLessEqual(rp.MID_X0 - rp.SER_PCB_X1, 0.1)
        y = (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2
        self.assertTrue(inside(self.shape, rp.MID_X0 + EPS, y, rp.SER_CZ))
        self.assertTrue(inside(self.shape, rp.MID_X0 + EPS, y, rp.MID_WALL_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, rp.SER_PCB_X1 - 0.1, y, rp.SER_CZ))

    def test_tail_lip(self):
        self.assertAlmostEqual(rp.MID_X0 - rp.SER_LIP_X0, rp.LIP_OVER)
        self.assertAlmostEqual(rp.SER_LIP_Z0 - rp.SER_TAIL_Z1, rp.LIP_GAP)
        self.assertLessEqual(rp.SER_LIP_Y1, rp.SER_PCB_Y1 - 2.0)        # wire pads in the last 2 mm stay clear
        x = rp.SER_LIP_X0 + rp.LIP_OVER / 2
        y = rp.SER_SHELL_Y1 + rp.SER_LIP_L / 2
        self.assertTrue(inside(self.shape, x, y, rp.SER_LIP_Z0 + EPS))
        self.assertFalse(inside(self.shape, x, y, rp.SER_LIP_Z0 - EPS))
        self.assertFalse(inside(self.shape, x, y, rp.SER_LIP_Z0 + rp.LIP_T + EPS))
        self.assertFalse(inside(self.shape, x, rp.SER_LIP_Y1 + EPS, rp.SER_LIP_Z0 + EPS))

    def test_glue_pocket_floor_and_dam(self):
        self.assertAlmostEqual(rp.DAM_Y0 - rp.SER_SHELL_Y1, rp.DAM_GAP)
        self.assertAlmostEqual(rp.DAM_TOP_Z, rp.SER_TAIL_Z0 - rp.LIP_GAP)
        self.assertAlmostEqual(rp.SER_TAIL_Z0 - rp.POCKET_FLOOR_Z, rp.POCKET_FLOOR_GAP)
        self.assertGreaterEqual(rp.POCKET_FLOOR_GAP, 0.8)                 # the SMD part on the underside
        # the gap between the bump and the dam goes down to the plate
        self.assertFalse(inside(self.shape, rp.SER_CX, rp.SER_SHELL_Y1 + rp.DAM_GAP / 2, rp.PLATE_Z1 + EPS))
        ym = (rp.DAM_Y0 + rp.DAM_Y1) / 2
        self.assertTrue(inside(self.shape, rp.SER_CX, ym, rp.DAM_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, rp.SER_CX, ym, rp.DAM_TOP_Z + EPS))
        y = rp.POCKET_KEY_Y + rp.POCKET_KEY_D        # beside the keys
        self.assertTrue(inside(self.shape, rp.SER_CX, y, rp.POCKET_FLOOR_Z - EPS))
        self.assertFalse(inside(self.shape, rp.SER_CX, y, rp.POCKET_FLOOR_Z + EPS))

    def test_pocket_keys_go_through(self):
        for dx in (-rp.POCKET_KEY_DX, rp.POCKET_KEY_DX):
            x = rp.SER_CX + dx
            self.assertFalse(inside(self.shape, x, rp.POCKET_KEY_Y, rp.PLATE_Z0 + EPS), dx)
            self.assertFalse(inside(self.shape, x, rp.POCKET_KEY_Y, rp.POCKET_FLOOR_Z - EPS), dx)
            self.assertTrue(inside(self.shape, x + rp.POCKET_KEY_D / 2 + 0.2, rp.POCKET_KEY_Y,
                                   rp.POCKET_FLOOR_Z - EPS), dx)

    def test_pocket_walls(self):
        y = (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2
        top = rp.SER_STOP_TOP_Z
        x_left = rp.POCKET_X0 - rp.POCKET_WALL_T / 2
        self.assertTrue(inside(self.shape, x_left, y, top - EPS))
        self.assertFalse(inside(self.shape, x_left, y, top + EPS))
        self.assertFalse(inside(self.shape, rp.POCKET_X0 + 0.1, y, rp.SER_CZ))     # glue runs down the edge
        self.assertAlmostEqual(rp.SER_PCB_X0 - rp.POCKET_X0, rp.CORNER_GAP)
        # rear wall behind the tail end, closed across
        self.assertAlmostEqual(rp.SER_STOP_Y0 - rp.SER_PCB_Y1, rp.CORNER_GAP)
        ym = (rp.SER_STOP_Y0 + rp.SER_STOP_Y1) / 2
        for x in (rp.SER_PCB_X0 + 0.5, rp.SER_CX, rp.SER_PCB_X1 - 0.5):
            self.assertTrue(inside(self.shape, x, ym, top - EPS), x)
        self.assertFalse(inside(self.shape, rp.SER_CX, rp.SER_STOP_Y0 - EPS, rp.SER_CZ))

    def test_pocket_open_above_the_tail(self):
        y = (rp.DAM_Y1 + rp.SER_PCB_Y1) / 2
        for z in (rp.SER_CZ, rp.SER_TAIL_Z1 + EPS, rp.SER_STOP_TOP_Z + EPS):
            self.assertFalse(inside(self.shape, rp.SER_CX, y, z), z)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform -v 2>&1 | tail -30`
Expected: errors such as `AttributeError: module ... has no attribute 'MID_WALL_TOP_Z'`, plus failures in `test_serial_measured_lengths` and `test_rev3_serial_stops_are_gone`.

- [ ] **Step 3: Update the parameters**

In `rp2040zero_platform.py`, replace the serial breakout block (from `SER_W = 8.94` through `BOARD_SIDE_GAP = 0.1 ...`) with:

```python
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
LIP_T = 0.6                    # tail lip thickness
MID_WALL_TOP_Z = 2.15          # top of the middle wall, its RP2040 lip and the snap hook
SHELL_WALL_T = 1.2             # left side wall beside the serial shell
SER_LIP_L = 2.0                # tail lip length behind the bump (the wire pads are at the tail end)
POCKET_WALL_T = 0.8            # glue pocket left wall
POCKET_FLOOR_GAP = 0.8         # tail underside -> pocket floor (clears the SMD part, glue gets under the tail)
DAM_GAP = 0.2                  # bump's rear face -> dam
DAM_T = 1.2                    # dam thickness (Y); its rear face takes the unplug pull through the glue
POCKET_KEY_D = 1.5             # glue key holes through the floor and the plate
POCKET_KEY_DX = 2.5            # key holes at SER_CX +- this
```

- [ ] **Step 4: Update the derived values**

In the derived block, delete the lines defining `SER_ARM_X0` and `SER_ARM_X1` (they used the removed `SER_SIDE_GAP`). Keep `SER_STOP_Y0`, `SER_STOP_Y1`, `SER_STOP_TOP_Z` and `BOARD_STOP_X`. After `BOARD_STOP_X = ...` add:

```python
SER_TAIL_Z0 = SER_CZ - SER_PCB_T / 2.0       # tail underside (the photo side, now facing down)
SER_TAIL_Z1 = SER_CZ + SER_PCB_T / 2.0       # tail top (wire pads)
SER_LIP_X0 = SER_X1 - LIP_OVER               # tail lip, over the tail's right edge
SER_LIP_Y1 = SER_SHELL_Y1 + SER_LIP_L
SER_LIP_Z0 = SER_TAIL_Z1 + LIP_GAP
MID_X0 = SER_X1                              # middle wall: right side wall of the shell and the tail ...
MID_X1 = BOARD_STOP_X                        # ... and BOARD_SIDE_GAP off the RP2040's left edge
MID_Y1 = -17.69                              # front end of the middle wall (Task 2: the RP2040 lip's end)
POCKET_X0 = SER_PCB_X0 - CORNER_GAP          # glue pocket left wall, inner face
POCKET_FLOOR_Z = SER_TAIL_Z0 - POCKET_FLOOR_GAP
DAM_Y0 = SER_SHELL_Y1 + DAM_GAP
DAM_Y1 = DAM_Y0 + DAM_T
DAM_TOP_Z = SER_TAIL_Z0 - LIP_GAP
POCKET_KEY_Y = (DAM_Y1 + SER_STOP_Y0) / 2.0
```

- [ ] **Step 5: Replace `make_serial_stops` with the new builders**

Delete `make_serial_stops()` and add, after `make_pedestal()`:

```python
def make_shell_wall():
    """Low wall along the serial shell's left side, line-to-line, up to the
    shell's mid-height so the part can be tilted in."""
    return box(SER_X0 - SHELL_WALL_T, SER_X0, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, SER_CZ).common(make_keep())


def make_middle_wall():
    """Rigid wall between the breakout and the RP2040: the right side wall of
    the serial shell and tail, with a lip over the tail's right edge. Beside
    the shell it stays at ledge height so the GP0/GP1 wires cross it."""
    return fuse_all([
        box(MID_X0, MID_X1, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, PCB_Z0),
        box(MID_X0, MID_X1, SER_SHELL_Y1, MID_Y1, PLATE_Z0, MID_WALL_TOP_Z),
        box(SER_LIP_X0, MID_X0, SER_SHELL_Y1, SER_LIP_Y1, SER_LIP_Z0, SER_LIP_Z0 + LIP_T),
    ])


def make_glue_pocket():
    """Pocket around the breakout's tail, filled with hot glue from above:
    a raised floor under the tail, a dam behind the bump whose rear face
    takes the unplug pull through the glue, a left wall and a closed rear
    wall behind the tail end (the plug-in push). The middle wall is its
    right side."""
    x_out = POCKET_X0 - POCKET_WALL_T
    return fuse_all([
        box(POCKET_X0, MID_X0, DAM_Y0, SER_STOP_Y0, PLATE_Z0, POCKET_FLOOR_Z),
        box(POCKET_X0, MID_X0, DAM_Y0, DAM_Y1, PLATE_Z0, DAM_TOP_Z),
        box(x_out, POCKET_X0, SER_SHELL_Y1, SER_STOP_Y1, PLATE_Z0, SER_STOP_TOP_Z),
        box(x_out, MID_X0, SER_STOP_Y0, SER_STOP_Y1, PLATE_Z0, SER_STOP_TOP_Z),
    ])


def make_pocket_keys():
    """Two holes through the pocket floor and the plate that key the glue in."""
    return fuse_all([cyl(SER_CX + dx, POCKET_KEY_Y, POCKET_KEY_D, PLATE_Z0 - 1.0, POCKET_FLOOR_Z + 1.0)
                     for dx in (-POCKET_KEY_DX, POCKET_KEY_DX)])
```

Change `build()` to:

```python
def build():
    """Return the finished platform as a single solid."""
    shape = fuse_all([make_plate(), make_ledges(), make_corner_stops(), make_pedestal(),
                      make_shell_wall(), make_middle_wall(), make_glue_pocket()])
    return shape.cut(make_screw_cutters()).cut(make_pocket_keys()).removeSplitter()
```

In `make_components()`, change the docstring's last line to `serial USB-C shell (with the bump behind it) and its PCB tail.` The geometry already follows `SER_SHELL_Y1` and `SER_PCB_Y1`.

Update the module docstring's second paragraph to:

```python
"""...
A flat plate screwed from below against the underside of the case's two M4
controller rings. The RP2040-Zero (components down) rests on two ledges so
its USB-C sits in the case slot, held by a rigid lip and a snap hook; the
breakout's shell sits on a low pedestal in the new slot, its tail in a
glue pocket.
...
"""
```

(Keep the first and last paragraphs as they are.)

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform -v 2>&1 | tail -30`
Expected: all tests pass (ExportTest included). If `test_single_valid_solid` or `test_prints_flat_on_its_underside` fails, print `len(shape.Solids)` and the low faces before changing anything.

- [ ] **Step 7: Commit**

```bash
git add rp2040zero_platform/rp2040zero_platform.py rp2040zero_platform/tests/test_platform.py
git commit -m "Rev. 4 breakout: measured lengths, middle wall with tail lip, glue pocket

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Zero — left lip, PLA snap hook in a relief groove

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (new parameters, derived values, `prism_xz`, `make_plate`, `make_middle_wall`, `make_hook`, `build`)
- Test: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Consumes: `MID_X1`, `MID_WALL_TOP_Z`, `LIP_OVER`, `LIP_GAP`, `make_middle_wall()` from Task 1.
- Produces (used by Tasks 3–4): parameters `ZERO_PAD1_Y`, `ZERO_PAD_PITCH`, `ZERO_LIP_MARGIN`, `HOOK_PAD`, `HOOK_T`, `HOOK_W`, `HOOK_LIP`, `HOOK_GAP`, `HOOK_GROOVE_DEPTH`, `HOOK_PLATE_X1`; function `zero_pad_y(k) -> float`; derived `LIP_Z0`, `ZERO_LIP_X1`, `ZERO_LIP_Y0`, `ZERO_LIP_Y1`, `HOOK_YC`, `HOOK_Y0`, `HOOK_Y1`, `HOOK_X0`, `HOOK_X1`, `HOOK_TIP_X`, `HOOK_ROOT_Z`, `GROOVE_X0`, `GROOVE_X1`, `GROOVE_Y0`, `GROOVE_Y1`; builders `prism_xz(points, y0, y1)`, `make_hook()`, `make_hook_groove()`. `MID_Y1` becomes `ZERO_LIP_Y1`.

- [ ] **Step 1: Write the failing tests**

In `test_only_known_features_stand_above_the_plate`, add one more entry to the `known` list:

```python
                    rp.HOOK_X0 <= x <= rp.HOOK_X1 and rp.HOOK_Y0 <= y <= rp.HOOK_Y1,       # snap hook arm
```

Add a new section to `ShapeTest`:

```python
    # -- RP2040-Zero: left lip, snap hook (rev. 4) -------------------------
    def test_zero_pad_positions(self):
        self.assertAlmostEqual(rp.zero_pad_y(4) - rp.BOARD_Y0, 10.0, places=1)
        self.assertAlmostEqual(rp.zero_pad_y(5) - rp.zero_pad_y(4), 2.54)

    def test_left_lip_over_free_pads(self):
        self.assertAlmostEqual(rp.LIP_Z0 - rp.PCB_Z1, rp.LIP_GAP)
        self.assertAlmostEqual(rp.ZERO_LIP_X1 - rp.BOARD_X0, rp.LIP_OVER)
        self.assertAlmostEqual(rp.MID_Y1, rp.ZERO_LIP_Y1)
        x = rp.BOARD_X0 + rp.LIP_OVER / 2
        for k in (4, 5, 6):                                  # GP3, GP4, GP5: no wires
            self.assertTrue(inside(self.shape, x, rp.zero_pad_y(k), rp.LIP_Z0 + EPS), k)
            self.assertFalse(inside(self.shape, x, rp.zero_pad_y(k), rp.LIP_Z0 - EPS), k)
        self.assertFalse(inside(self.shape, x, rp.zero_pad_y(2), rp.LIP_Z0 + EPS))   # GP1 (serial D-)
        # >= 0.7 between the lip and GP1's pad (pads are ~1.5 long)
        self.assertGreaterEqual(rp.ZERO_LIP_Y0 - (rp.zero_pad_y(2) + 0.75), 0.7)

    def test_hook_arm_and_lip(self):
        y = rp.HOOK_YC
        self.assertAlmostEqual(y, rp.zero_pad_y(rp.HOOK_PAD))
        self.assertTrue(inside(self.shape, rp.HOOK_X0 + rp.HOOK_T / 2, y, rp.PLATE_Z1 + 1.0))
        self.assertFalse(inside(self.shape, rp.LEDGE_X1 + rp.HOOK_GAP / 2, y, rp.PLATE_Z1 + 1.0))  # free of the ledge
        self.assertTrue(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y, rp.LIP_Z0 + EPS))
        self.assertFalse(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y, rp.LIP_Z0 - EPS))
        self.assertFalse(inside(self.shape, rp.HOOK_TIP_X - EPS, y, rp.LIP_Z0 + EPS))
        # 45 deg ramp on top: solid just above the tip, empty at the top over the tip
        self.assertTrue(inside(self.shape, rp.HOOK_TIP_X + 0.1, y, rp.LIP_Z0 + 0.05))
        self.assertFalse(inside(self.shape, rp.HOOK_TIP_X + 0.1, y, rp.MID_WALL_TOP_Z - EPS))
        self.assertTrue(inside(self.shape, rp.HOOK_X0 + EPS, y, rp.MID_WALL_TOP_Z - EPS))
        # nothing of the hook outside its 2 mm
        self.assertFalse(inside(self.shape, rp.HOOK_X0 + rp.HOOK_T / 2, rp.HOOK_Y1 + EPS, rp.PLATE_Z1 + 1.0))

    def test_hook_groove(self):
        self.assertAlmostEqual(rp.HOOK_ROOT_Z, rp.PLATE_Z1 - rp.HOOK_GROOVE_DEPTH)
        self.assertGreaterEqual(rp.HOOK_ROOT_Z - rp.PLATE_Z0, 0.5)               # groove floor
        for x, y in ((rp.GROOVE_X0 + rp.HOOK_GAP / 2, rp.HOOK_YC),               # inner side
                     (rp.GROOVE_X1 - rp.HOOK_GAP / 2, rp.HOOK_YC),               # outer side
                     (rp.HOOK_X0 + rp.HOOK_T / 2, rp.GROOVE_Y0 + rp.HOOK_GAP / 2),   # wall side
                     (rp.HOOK_X0 + rp.HOOK_T / 2, rp.GROOVE_Y1 - rp.HOOK_GAP / 2)):  # front side
            self.assertFalse(inside(self.shape, x, y, rp.HOOK_ROOT_Z + EPS), (x, y))
            self.assertTrue(inside(self.shape, x, y, rp.HOOK_ROOT_Z - EPS), (x, y))
        # the plate is widened to carry the groove's outer side
        self.assertTrue(inside(self.shape, rp.GROOVE_X1 + 0.2, rp.HOOK_YC, rp.PLATE_Z1 - EPS))
        self.assertGreater(rp.HOOK_PLATE_X1, rp.GROOVE_X1 + 0.4)

    def test_hook_strain_ok_for_pla(self):
        length = rp.LIP_Z0 - rp.HOOK_ROOT_Z
        strain = 1.5 * rp.HOOK_T * rp.HOOK_LIP / length ** 2
        self.assertLessEqual(strain, 0.015)

    def test_hook_clear_of_used_pads(self):
        # GP27 (R4) is pad 6 on the right edge; GP29 (pad 4) is free
        self.assertGreaterEqual(rp.zero_pad_y(6) - 0.75 - rp.HOOK_Y1, 0.7)

    def test_hook_clear_of_ring_b(self):
        self.assertGreaterEqual(rp.GROOVE_Y0, rp.RING_B_FREE_Y - 0.5)   # ring B's flat face ends at Y -24
        self.assertGreaterEqual(rp.HOOK_Y0, rp.RING_B_FREE_Y)            # the arm stands where the case is free

    def test_board_cannot_slip_off_a_lip(self):
        # sideways play: middle wall (MID_X1) to the front-right corner stop (BOARD_X1 + CORNER_GAP)
        play = (rp.BOARD_X1 + rp.CORNER_GAP) - (rp.MID_X1 + rp.BOARD_W)
        self.assertAlmostEqual(play, rp.CORNER_GAP + rp.BOARD_SIDE_GAP)
        self.assertGreaterEqual(rp.ZERO_LIP_X1 - (rp.MID_X1 + play), 0.25)              # left lip
        self.assertGreaterEqual((rp.MID_X1 + rp.BOARD_W) - rp.HOOK_TIP_X, 0.25)        # hook
        # the hook's underside chamfer stays outside the PCB even with the board pushed right
        self.assertGreaterEqual(rp.LEDGE_X1, rp.BOARD_X1 + rp.CORNER_GAP)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform -v 2>&1 | tail -30`
Expected: `AttributeError: module ... has no attribute 'zero_pad_y'` (and `HOOK_X0` from the whitelist test).

- [ ] **Step 3: Add the parameters**

Append to the rev. 4 parameter block (after `POCKET_KEY_DX`):

```python
ZERO_PAD1_Y = 2.38             # USB-end PCB edge -> pad 1 centre along the long edges (user: pad 4 at ~10 mm)
ZERO_PAD_PITCH = 2.54
ZERO_LIP_MARGIN = 1.0          # the left lip covers pads 4-6 (GP3-GP5, no wires) and this much past them
HOOK_PAD = 5                   # right-edge pad under the snap hook (GP28, no wire)
HOOK_T = 0.8                   # hook arm thickness (X)
HOOK_W = 2.0                   # hook width (Y)
HOOK_LIP = 0.4                 # hook reach over the PCB edge = how far the arm bends
HOOK_GAP = 0.4                 # hook arm -> right ledge, and the relief groove's width around the arm
HOOK_GROOVE_DEPTH = 1.5        # relief groove into the 2 mm plate: the arm bends from its 0.5 floor
HOOK_PLATE_X1 = 32.5           # plate widened to here beside the hook (the case is free below the rings)
```

- [ ] **Step 4: Add the derived values**

Directly after `BOARD_Y1 = ...` add the pad function (it is used below):

```python
def zero_pad_y(k):
    """Y of pad k (1 at the USB end) along the RP2040-Zero's long edges."""
    return BOARD_Y0 + ZERO_PAD1_Y + (k - 1) * ZERO_PAD_PITCH
```

Replace the line `MID_Y1 = -17.69 ...` with:

```python
LIP_Z0 = PCB_Z1 + LIP_GAP                    # underside of the RP2040 lip and the hook
ZERO_LIP_X1 = BOARD_X0 + LIP_OVER
ZERO_LIP_Y0 = zero_pad_y(4) - ZERO_LIP_MARGIN
ZERO_LIP_Y1 = zero_pad_y(6) + ZERO_LIP_MARGIN
MID_Y1 = ZERO_LIP_Y1                         # the middle wall ends with the RP2040 lip
HOOK_YC = zero_pad_y(HOOK_PAD)
HOOK_Y0 = HOOK_YC - HOOK_W / 2.0
HOOK_Y1 = HOOK_YC + HOOK_W / 2.0
HOOK_X0 = LEDGE_X1 + HOOK_GAP                # arm inner face
HOOK_X1 = HOOK_X0 + HOOK_T
HOOK_TIP_X = BOARD_X1 - HOOK_LIP
HOOK_ROOT_Z = PLATE_Z1 - HOOK_GROOVE_DEPTH   # the arm bends from the groove floor
GROOVE_X0 = LEDGE_X1
GROOVE_X1 = HOOK_X1 + HOOK_GAP
GROOVE_Y0 = HOOK_Y0 - HOOK_GAP
GROOVE_Y1 = HOOK_Y1 + HOOK_GAP
```

- [ ] **Step 5: Add `prism_xz`, the groove, the plate widening, the RP2040 lip and the hook**

After `prism()` add:

```python
def prism_xz(points, y0, y1):
    """Prism over a closed XZ polygon, from y0 to y1."""
    pts = [Vector(x, y0, z) for x, z in points] + [Vector(points[0][0], y0, points[0][1])]
    return Part.Face(Part.makePolygon(pts)).extrude(Vector(0, y1 - y0, 0))
```

In `make_plate()`, add the widening to the fused list and cut the groove. Replace the last three lines of the function with:

```python
    pad_b = cyl(bx, by, 2 * RING_PAD_R, PLATE_Z0, PLATE_Z1)
    hook_pad = box(PLATE_RIGHT_X - 1.0, HOOK_PLATE_X1, GROOVE_Y0 - HOOK_GAP, GROOVE_Y1 + HOOK_GAP,
                   PLATE_Z0, PLATE_Z1)
    plate = fuse_all([body, pad_a, neck_a, pad_b, hook_pad])
    return plate.common(make_keep()).cut(make_window()).cut(make_hook_groove())


def make_hook_groove():
    """Relief groove around the snap hook's root, so the arm bends over the
    plate's thickness too."""
    return box(GROOVE_X0, GROOVE_X1, GROOVE_Y0, GROOVE_Y1, HOOK_ROOT_Z, PLATE_Z1 + 1.0)
```

In `make_middle_wall()`, add the RP2040 lip as a fourth box, and update the docstring:

```python
def make_middle_wall():
    """Rigid wall between the breakout and the RP2040: the right side wall of
    the serial shell and tail, with a lip over the tail's right edge and a
    lip over the RP2040's left edge (pads 4-6, no wires). Beside the shell
    it stays at ledge height so the GP0/GP1 wires cross it."""
    return fuse_all([
        box(MID_X0, MID_X1, PLATE_REAR_Y, SER_SHELL_Y1, PLATE_Z0, PCB_Z0),
        box(MID_X0, MID_X1, SER_SHELL_Y1, MID_Y1, PLATE_Z0, MID_WALL_TOP_Z),
        box(SER_LIP_X0, MID_X0, SER_SHELL_Y1, SER_LIP_Y1, SER_LIP_Z0, SER_LIP_Z0 + LIP_T),
        box(MID_X1, ZERO_LIP_X1, ZERO_LIP_Y0, ZERO_LIP_Y1, LIP_Z0, MID_WALL_TOP_Z),
    ])
```

After `make_glue_pocket()` / `make_pocket_keys()` add:

```python
def make_hook():
    """Snap hook over the RP2040's right edge: a vertical arm standing on the
    groove floor, flexing outward, with a lip that has a 45 deg ramp on top
    (the board pushes it aside) and a 45 deg chamfer under the part outside
    the PCB (shorter overhang)."""
    arm = box(HOOK_X0, HOOK_X1, HOOK_Y0, HOOK_Y1, HOOK_ROOT_Z, MID_WALL_TOP_Z)
    ramp_top_x = HOOK_TIP_X + (MID_WALL_TOP_Z - LIP_Z0)
    lip = prism_xz([(HOOK_TIP_X, LIP_Z0), (LEDGE_X1, LIP_Z0), (HOOK_X0, LIP_Z0 - HOOK_GAP),
                    (HOOK_X0, MID_WALL_TOP_Z), (ramp_top_x, MID_WALL_TOP_Z)], HOOK_Y0, HOOK_Y1)
    return arm.fuse(lip)
```

Add `make_hook()` to `build()`:

```python
    shape = fuse_all([make_plate(), make_ledges(), make_corner_stops(), make_pedestal(),
                      make_shell_wall(), make_middle_wall(), make_glue_pocket(), make_hook()])
```

Check before running: `ramp_top_x` = 29.60 + 0.70 = 30.30 = `LEDGE_X1`, so the lip outline is convex: (29.60, 1.45) → (30.30, 1.45) → (30.70, 1.05) → (30.70, 2.15) → (30.30, 2.15).

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform -v 2>&1 | tail -40`
Expected: all pass. `test_extents` still expects XMax `RING_B[0] + RING_PAD_R` (41.66); the widening stops at 32.5, so it is unaffected.

- [ ] **Step 7: Commit**

```bash
git add rp2040zero_platform/rp2040zero_platform.py rp2040zero_platform/tests/test_platform.py
git commit -m "Rev. 4 RP2040-Zero: rigid left lip, PLA snap hook in a relief groove

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Test coupon, export, clearance sections

**Files:**
- Modify: `rp2040zero_platform/rp2040zero_platform.py` (`export`, new `COUPON`, `make_coupon`, `write_stl`)
- Modify: `rp2040zero_platform/check_clearance.py:156-162` (the `views` list)
- Test: `rp2040zero_platform/tests/test_platform.py`

**Interfaces:**
- Consumes: `build()`, `HOOK_*`, `ZERO_LIP_*`, `POCKET_KEY_Y`, `HOOK_PLATE_X1` from Tasks 1–2.
- Produces: `COUPON = (x0, x1, y0, y1)`, `make_coupon(shape) -> Part.Shape`, `write_stl(shape, path)`; `export()` returns the dict keys `'fcstd'`, `'step'`, `'stl'`, `'coupon_stl'`.

- [ ] **Step 1: Write the failing tests**

Add to `ShapeTest`:

```python
    # -- test coupon -------------------------------------------------------
    def test_coupon_holds_the_lips_hook_and_pocket(self):
        coupon = rp.make_coupon(self.shape)
        self.assertTrue(coupon.isValid())
        self.assertEqual(len(coupon.Solids), 1)
        x0, x1, y0, y1 = rp.COUPON
        bb = coupon.BoundBox
        self.assertGreaterEqual(bb.XMin, x0 - 1e-6)
        self.assertLessEqual(bb.XMax, x1 + 1e-6)
        self.assertGreaterEqual(bb.YMin, y0 - 1e-6)
        self.assertLessEqual(bb.YMax, y1 + 1e-6)
        for p in ((rp.HOOK_X0 + rp.HOOK_T / 2, rp.HOOK_YC, rp.PLATE_Z1 + 1.0),                     # hook arm
                  (rp.BOARD_X0 + rp.LIP_OVER / 2, rp.zero_pad_y(5), rp.LIP_Z0 + EPS),             # RP2040 lip
                  (rp.SER_LIP_X0 + rp.LIP_OVER / 2, rp.SER_SHELL_Y1 + 1.0, rp.SER_LIP_Z0 + EPS),  # tail lip
                  (rp.SER_CX, (rp.DAM_Y0 + rp.DAM_Y1) / 2, rp.DAM_TOP_Z - EPS)):                  # dam
            self.assertTrue(inside(coupon, *p), p)
        self.assertAlmostEqual(bb.ZMin, rp.PLATE_Z0, places=4)
```

In `ExportTest`, replace `test_export_writes_three_files` with:

```python
    def test_export_writes_the_part_and_the_coupon(self):
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(rp.build(), d)
            self.assertEqual(set(paths), {'fcstd', 'step', 'stl', 'coupon_stl'})
            self.assertEqual(os.path.basename(paths['coupon_stl']), "hook_coupon.stl")
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform.ShapeTest.test_coupon_holds_the_lips_hook_and_pocket rp2040zero_platform.tests.test_platform.ExportTest -v 2>&1 | tail -15`
Expected: `AttributeError: ... no attribute 'make_coupon'` and the export key-set assertion fails.

- [ ] **Step 3: Implement the coupon and the export**

After `make_components()` add:

```python
COUPON = (0.5, HOOK_PLATE_X1, -27.5, -16.0)   # X0, X1, Y0, Y1 of the test print


def make_coupon(shape):
    """Cut-out of the platform with the RP2040 lip, the snap hook, the tail
    lip and the glue pocket, to try with the real parts before printing the
    whole platform."""
    x0, x1, y0, y1 = COUPON
    return shape.common(box(x0, x1, y0, y1, PLATE_Z0 - 1.0, MID_WALL_TOP_Z + 1.0)).removeSplitter()
```

Replace `export()` with:

```python
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
```

If `test_coupon_holds_the_lips_hook_and_pocket` reports 2 solids, print each solid's bounding box. A sliver at the box edge (for example the left corner stop's footing) means `COUPON` cuts through a feature. Move `COUPON[3]` from −16.0 to −15.0 and rerun before touching anything else.

- [ ] **Step 4: Add the two sections to `check_clearance.py`**

In `main()`, extend the `views` list and its comment:

```python
    # (file, axis, case plane, platform/component plane, u, v): Y-Z sections
    # through the rings and both USB-C centres; an X-Z "rear view" cut
    # inside the 2 mm wall showing both shells in their slots; X-Z cuts
    # through the snap hook (with the RP2040 lip) and the glue pocket.
    views = [
        ("sec_ringA.png", 0, ax, ax, 1, 2),
        ("sec_ringB.png", 0, bx, bx, 1, 2),
        ("sec_serial.png", 0, rp.SER_CX, rp.SER_CX, 1, 2),
        ("sec_usb.png", 0, rp.BOARD_CX, rp.BOARD_CX, 1, 2),
        ("sec_wall.png", 1, rp.WALL_OUTER_Y + 1.5, rp.WALL_OUTER_Y + 1.5, 0, 2),
        ("sec_hook.png", 1, rp.HOOK_YC, rp.HOOK_YC, 0, 2),
        ("sec_pocket.png", 1, rp.POCKET_KEY_Y, rp.POCKET_KEY_Y, 0, 2),
    ]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest rp2040zero_platform.tests.test_platform -v 2>&1 | tail -40`
Expected: all pass, including `ImportTest`.

- [ ] **Step 6: Commit**

```bash
git add rp2040zero_platform/rp2040zero_platform.py rp2040zero_platform/check_clearance.py rp2040zero_platform/tests/test_platform.py
git commit -m "Rev. 4: hook test coupon in the export, clearance sections through the hook and the pocket

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Regenerate, check against the case, README

**Files:**
- Regenerate: `rp2040zero_platform/rp2040zero_platform.{FCStd,step,stl}`, `rp2040zero_platform/hook_coupon.stl`, `rp2040zero_platform/sec_*.png`
- Modify: `rp2040zero_platform/README.md`

**Interfaces:**
- Consumes: everything above. Produces nothing used by code.

- [ ] **Step 1: Regenerate the part and the coupon**

Run: `cd rp2040zero_platform && python3 rp2040zero_platform.py`
Expected: `valid: True solids: 1`, bbox Z `-5.75..2.15`, and five `wrote ...` lines (fcstd, step, stl, coupon_stl). Delete any new `*.FCBak` backup that FreeCAD writes.

- [ ] **Step 2: Run the clearance check against the modified case**

Run: `cd rp2040zero_platform && python3 check_clearance.py`
Expected: exit code 0, no `COLLISION` lines, and seven `wrote sec_*.png` lines. If there are collisions, report their X/Y/Z and stop. Do not move features to make the check pass without asking the user.

- [ ] **Step 3: Look at the new sections**

Read `rp2040zero_platform/sec_hook.png` and `rp2040zero_platform/sec_pocket.png` with the Read tool. Check:
- *Hook section:* the arm stands in its groove, its lip is over the PCB edge with the ramp on top, the left lip is over the PCB's left edge, and the case (blue) stays clear.
- *Pocket section:* the floor is under the tail with the gap, the left wall and the middle wall are beside the tail, and the key holes go through.

- [ ] **Step 4: Update the README**

In `rp2040zero_platform/README.md`:

Replace the intro's last sentence `Both parts are positioned by the plate and fixed with hot glue.` with:

```markdown
The RP2040-Zero snaps in (a rigid lip on its left edge, a snap hook on its
right) with no glue; the breakout's tail sits in a glue pocket that locks
one blob of hot glue in mechanically.
```

Change the design-notes line to:

```markdown
Design notes and measurements: `docs/superpowers/specs/2026-10-02-skeletyl-platform-rev4-glue-free-design.md`
(rev. 4) on top of `docs/superpowers/specs/2026-09-25-skeletyl-usb-serial-design.md` (rev. 3) and
`docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.
```

In **Build**, change the platform line to `python3 rp2040zero_platform.py               # -> .FCStd / .step / .stl + hook_coupon.stl`.

In **Print**, add after the platform bullet:

```markdown
- **PLA** is fine: the snap hook bends about 1.1 % (it stands in a relief
  groove so it bends over 6.7 mm).
- **Test coupon first:** `hook_coupon.stl` is the part of the platform
  with the RP2040 lip, the snap hook, the tail lip and the glue pocket.
  Print it the same way and check that the Zero clicks in and the
  breakout's tail sits under its lip before printing the whole platform.
  If the hook is too stiff or too loose, change `HOOK_T` / `HOOK_LIP`.
```

Replace the whole **Assemble** list with:

```markdown
1. **Solder first.** Four wires to the breakout's pads (on its back, at
   the tail end) and all wires to the RP2040-Zero's pads.
2. **Breakout, back side up** (the side with the wire pads faces up, the
   leads and the small SMD part face the platform; USB-C works either way
   round). Set the shell on the pedestal with its right side against the
   middle wall, tilting it so the tail's right edge goes under the tail
   lip, then lower the left side. The bump behind the shell sits against
   the dam.
3. **Glue pocket.** Fill the pocket around the tail with hot glue, over
   the tail end, the solder joints and the first mm of wire, until glue
   shows in the two holes underneath. Trim anything that comes through
   flush with the underside. This one blob takes the pull when you unplug
   the link cable.
4. **Board.** Components down, USB-C toward the wall. Slide its left edge
   under the lip on the middle wall, then press the right edge down: it
   pushes the snap hook aside and clicks under it. No glue. To take it
   out, push the hook outward and lift the right edge.
5. **Into the case.** Tilt the platform in so both USB-C shells enter
   their slots, hold the plate against the ring faces and drive the two
   M4 × 8 screws from below.
6. BOOT/RESET face the bottom plate: remove it and press them through the
   window. Put `QK_BOOT` in the keymap as well.
```

In the **Fit checks** table, replace the rows for `SER_L / SER_PCB_W`, `SER_SIDE_GAP / BOARD_SIDE_GAP` and `SER_SHELL_L` with:

```markdown
| `SER_L` / `SER_SHELL_L` / `SER_PCB_W` | 14.0 / 8.5 / 8.9 | Breakout overall length, shell + bump length, PCB width (caliper); they place the dam, the tail lip and the pocket |
| `BOARD_SIDE_GAP` | 0.1 | RP2040 left edge → the middle wall |
| `LIP_OVER` / `LIP_GAP` | 0.5 / 0.1 | Rigid lips over the tail and the RP2040: reach over the edge, gap above the PCB |
| `HOOK_T` / `HOOK_LIP` / `HOOK_GAP` | 0.8 / 0.4 / 0.4 | Snap hook arm thickness, reach over the PCB (= its bend), gap to the ledge and groove width |
| `ZERO_PAD1_Y` | 2.38 | USB-end PCB edge → pad 1 centre (pad 4 ≈ 10 mm); places the left lip and the hook over unused pads |
| `POCKET_FLOOR_GAP` / `DAM_GAP` | 0.8 / 0.2 | Glue under the tail (clears the SMD part); bump → dam |
```

In **Clearance check**, replace the last line with the result from Step 2, in this form: `Last run: 2026-10-03 — <N> points on the Z −3.75 contact plane; no collisions.` Use the actual N that Step 2 printed (the sum of the "on a ring face" and "on other case faces" counts).

- [ ] **Step 5: Run the full test suite one last time**

Run: `python3 -m unittest discover -s rp2040zero_platform/tests -t . -v 2>&1 | tail -15`
Expected: `OK`. This includes `test_case_usb_serial.py`, which is unchanged and must still pass.

- [ ] **Step 6: Commit**

```bash
git add rp2040zero_platform/README.md rp2040zero_platform/rp2040zero_platform.FCStd rp2040zero_platform/rp2040zero_platform.step rp2040zero_platform/rp2040zero_platform.stl rp2040zero_platform/hook_coupon.stl rp2040zero_platform/sec_*.png
git commit -m "Rev. 4: regenerated part and test coupon, README assembly for the snap-in board and glue pocket

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
