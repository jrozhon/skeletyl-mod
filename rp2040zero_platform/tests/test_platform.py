import os
import tempfile
import unittest

from rp2040zero_platform import rp2040zero_platform as rp

from FreeCAD import Vector

# Slightly inside a face is what we probe; 1e-6 is FreeCAD's isInside tolerance.
TOL = 1e-6
EPS = 0.05


def inside(shape, x, y, z):
    return shape.isInside(Vector(x, y, z), TOL, True)


class ShapeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shape = rp.build()

    # -- whole part -------------------------------------------------------
    def test_single_valid_solid(self):
        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.shape.Solids), 1)

    def test_prints_flat_on_its_underside(self):
        bb = self.shape.BoundBox
        self.assertAlmostEqual(bb.ZMin, rp.PLATE_Z0, places=4)
        # Every face on the bed is the plate underside: nothing hangs lower.
        low = [f for f in self.shape.Faces if f.BoundBox.ZMax < rp.PLATE_Z0 + EPS]
        self.assertTrue(low)
        self.assertEqual(len(low), 1)

    def test_extents(self):
        bb = self.shape.optimalBoundingBox(True, False)   # the fast box is loose around curved edges
        self.assertAlmostEqual(bb.YMin, rp.PLATE_REAR_Y, places=4)
        self.assertAlmostEqual(bb.ZMax, rp.CORNER_TOP_Z, places=4)
        self.assertAlmostEqual(bb.XMin, rp.LEFT_EDGE[0][0], places=4)
        self.assertAlmostEqual(bb.XMax, rp.RING_B[0] + rp.RING_PAD_R, places=4)

    def test_no_splinktegrated_tail(self):
        # Nothing in front of the board's end stop except the ring A pad.
        self.assertFalse(inside(self.shape, 21.0, rp.PLATE_FRONT_Y + 1.0, rp.PLATE_Z1 - 1.0))
        self.assertFalse(inside(self.shape, 21.0, 15.0, rp.PLATE_Z1 - 1.0))

    def test_held_components_do_not_intersect_the_platform(self):
        for solid in rp.make_components().Solids:
            self.assertLess(solid.common(self.shape).Volume, 1e-6)

    # -- ring seats -------------------------------------------------------
    def test_plate_top_meets_the_ring_faces(self):
        self.assertAlmostEqual(rp.PLATE_Z1, rp.RING_FACE_Z)
        for cx, cy in (rp.RING_A, rp.RING_B):
            for r in (rp.RING_BORE_D / 2 + 0.3, rp.RING_FACE_OD / 2 - 0.3):
                for dx, dy in ((r, 0), (0, r), (0, -r)):
                    # The -X side of ring A is the wall side and the rear of ring B's
                    # face lies behind the plate's rear edge: the plate is clipped there.
                    if cy + dy < rp.PLATE_REAR_Y:
                        continue
                    self.assertTrue(inside(self.shape, cx + dx, cy + dy, rp.PLATE_Z1 - EPS), (cx, cy, dx, dy))

    def test_screw_hole_and_countersink(self):
        for cx, cy in (rp.RING_A, rp.RING_B):
            self.assertFalse(inside(self.shape, cx, cy, rp.PLATE_Z1 - EPS))
            # 90 deg cone from Ø CSK_D at the underside down to the Ø4.5 hole
            for z, r in ((rp.PLATE_Z0 + EPS, rp.CSK_D / 2 - EPS),
                         (rp.PLATE_Z0 + rp.CSK_DEPTH / 2, (rp.CSK_D + rp.SCREW_HOLE_D) / 4)):
                self.assertFalse(inside(self.shape, cx + r - 0.1, cy, z), (cx, z))
                self.assertTrue(inside(self.shape, cx + r + 0.1, cy, z), (cx, z))
            # straight hole above the cone
            z = rp.PLATE_Z0 + rp.CSK_DEPTH + EPS
            self.assertFalse(inside(self.shape, cx + rp.SCREW_HOLE_D / 2 - 0.1, cy, z))
            self.assertTrue(inside(self.shape, cx + rp.SCREW_HOLE_D / 2 + 0.1, cy, z))

    def test_screw_head_clears_the_bottom_plate(self):
        self.assertGreaterEqual(rp.HEAD_BOTTOM_Z, rp.BOTTOM_PLATE_Z + 0.5)
        self.assertGreaterEqual(rp.PLATE_T - rp.CSK_DEPTH, 0.6)

    # -- case clearances (numbers measured from the V4 STL) ---------------
    def test_clear_of_the_rear_wall(self):
        self.assertGreaterEqual(rp.PLATE_REAR_Y, rp.WALL_INNER_Y + 0.3)
        # The board reaches into the wall recess, which is free from Z -5.5 to 3.
        self.assertGreater(rp.BOARD_Y0, rp.WALL_RECESS_Y + 0.2)
        self.assertLess(rp.PCB_Z1, 3.0)

    def test_clear_of_ring_b(self):
        self.assertLessEqual(rp.LEDGE_X1, rp.RING_B_FLAT_X - 0.5)
        self.assertLessEqual(rp.BOARD_X1, rp.RING_B_FLAT_X - 0.5)

    def test_clipped_along_the_left_wall(self):
        for (x, y) in rp.LEFT_EDGE[1:]:
            self.assertFalse(inside(self.shape, x - 0.2, y, rp.PLATE_Z1 - 1.0), (x, y))
            self.assertTrue(inside(self.shape, x + 0.5, y + 0.2, rp.PLATE_Z1 - 1.0), (x, y))

    # -- board frame ------------------------------------------------------
    def test_usb_c_centred_in_the_case_slot(self):
        self.assertAlmostEqual((rp.USB_Z0 + rp.PCB_Z0) / 2 - rp.BOARD_Z_SHIFT, sum(rp.USB_SLOT_Z) / 2)
        self.assertAlmostEqual(rp.BOARD_CX - rp.BOARD_X_SHIFT, sum(rp.USB_SLOT_X) / 2)
        self.assertGreater(rp.USB_Z0, rp.USB_SLOT_Z[0])
        self.assertLess(rp.PCB_Z0, rp.USB_SLOT_Z[1])
        self.assertGreater(rp.BOARD_CX - rp.USB_W / 2, rp.USB_SLOT_X[0])
        self.assertLess(rp.BOARD_CX + rp.USB_W / 2, rp.USB_SLOT_X[1])
        # face inside the wall, so a plug seats fully
        self.assertLess(rp.USB_FACE_Y, rp.WALL_RECESS_Y)
        self.assertGreater(rp.USB_FACE_Y, rp.WALL_OUTER_Y)

    def test_ledges_carry_the_pcb_edges(self):
        y = (rp.BOARD_Y0 + rp.BOARD_Y1) / 2
        for x in (rp.BOARD_X0 + 0.4, rp.BOARD_X1 - 0.4):
            self.assertTrue(inside(self.shape, x, y, rp.PCB_Z0 - EPS))      # ledge under the edge
            self.assertFalse(inside(self.shape, x, y, rp.PCB_Z0 + EPS))     # PCB space
            self.assertTrue(inside(self.shape, x, rp.PLATE_REAR_Y + 0.2, rp.PCB_Z0 - EPS))  # full length
        self.assertFalse(inside(self.shape, rp.BOARD_X0 + rp.LEDGE_W, y, rp.PCB_Z0 - EPS))

    def test_window_under_the_board_is_open_to_the_rear(self):
        for y in (rp.PLATE_REAR_Y + 0.1, rp.BOARD_Y0 + 3.0, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP - 0.1):
            self.assertFalse(inside(self.shape, rp.BOARD_CX, y, rp.PLATE_Z1 - 1.0), y)
        self.assertTrue(inside(self.shape, rp.BOARD_CX, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP + 0.1, rp.PLATE_Z1 - 1.0))
        # the strips under the ledges remain
        self.assertTrue(inside(self.shape, rp.BOARD_X0 + rp.WINDOW_INSET - 0.1, rp.BOARD_Y0 + 3.0, rp.PLATE_Z1 - 1.0))

    def test_components_clear_the_plate(self):
        self.assertGreaterEqual(rp.USB_Z0 - rp.PLATE_Z1, 0.5)

    def test_only_ledges_pedestal_and_corner_stops_stand_above_the_plate(self):
        ledges = ((rp.LEDGE_X0, rp.LEDGE_X0 + rp.LEDGE_W), (rp.LEDGE_X1 - rp.LEDGE_W, rp.LEDGE_X1))
        # corner stops: the bounding boxes of the two Ls
        corners = ((rp.BOARD_X0 - rp.CORNER_GAP - rp.CORNER_T, rp.BOARD_X0 + rp.CORNER_REACH),
                   (rp.BOARD_X1 - rp.CORNER_REACH, rp.BOARD_X1 + rp.CORNER_GAP + rp.CORNER_T))
        for x in [rp.LEFT_EDGE[0][0] + 0.25 + 0.5 * i for i in range(80)]:
            for y in [rp.PLATE_REAR_Y + 0.25 + 0.5 * j for j in range(60)]:
                if not inside(self.shape, x, y, rp.PLATE_Z1 + 0.3):
                    continue
                in_ledge = any(a <= x <= b for a, b in ledges) and y <= rp.LEDGE_Y1
                in_pedestal = rp.SER_X0 <= x <= rp.SER_X1 and y <= rp.SER_SHELL_Y1
                in_corner = (any(a <= x <= b for a, b in corners)
                             and rp.BOARD_Y1 - rp.CORNER_SIDE_L <= y <= rp.CORNER_Y1)
                self.assertTrue(in_ledge or in_pedestal or in_corner, (x, y))

    def test_old_jack_features_gone(self):
        # plate is full thickness where the pocket and the leg slots were
        for x in (rp.JACK_AXIS_X - 2.6, rp.JACK_AXIS_X, rp.JACK_AXIS_X + 2.6):
            self.assertTrue(inside(self.shape, x, -26.0, rp.PLATE_Z0 + 0.1), x)
            self.assertTrue(inside(self.shape, x, -26.0, rp.PLATE_Z1 - 0.1), x)

    # -- corner stops at the board's front (cable push, positioning) -------
    def test_corner_stops_are_sturdy(self):
        self.assertGreaterEqual(rp.CORNER_T, 2.0)
        self.assertGreaterEqual(rp.CORNER_TOP_Z, rp.PCB_Z1 + 0.3)
        self.assertLess(rp.CORNER_TOP_Z, 3.0)

    def test_front_arms_stop_the_board_at_both_corners(self):
        ym = rp.CORNER_Y0 + rp.CORNER_T / 2
        for x in (rp.BOARD_X0 + 1.0, rp.BOARD_X1 - 1.0):
            self.assertTrue(inside(self.shape, x, ym, rp.CORNER_TOP_Z - EPS), x)
            self.assertFalse(inside(self.shape, x, ym, rp.CORNER_TOP_Z + EPS), x)
            self.assertTrue(inside(self.shape, x, ym, rp.PLATE_Z0 + EPS), x)      # stands on its own footing
            self.assertFalse(inside(self.shape, x, rp.CORNER_Y0 - EPS, rp.PCB_Z1), x)   # gap to the PCB edge
        self.assertAlmostEqual(rp.CORNER_Y0 - rp.BOARD_Y1, rp.CORNER_GAP)
        # only the corners: the middle of the front edge stays open
        self.assertFalse(inside(self.shape, rp.BOARD_CX, ym, rp.PCB_Z0))

    def test_side_arms_locate_the_board_sideways(self):
        y = rp.BOARD_Y1 - 1.0
        for x_arm, x_gap in ((rp.BOARD_X0 - rp.CORNER_GAP - rp.CORNER_T / 2, rp.BOARD_X0 - rp.CORNER_GAP / 2),
                             (rp.BOARD_X1 + rp.CORNER_GAP + rp.CORNER_T / 2, rp.BOARD_X1 + rp.CORNER_GAP / 2)):
            self.assertTrue(inside(self.shape, x_arm, y, rp.CORNER_TOP_Z - EPS), x_arm)
            self.assertFalse(inside(self.shape, x_gap, y, rp.PCB_Z1), x_gap)
            self.assertFalse(inside(self.shape, x_arm, rp.BOARD_Y1 - rp.CORNER_SIDE_L - EPS, rp.PCB_Z1), x_arm)

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


class ImportTest(unittest.TestCase):
    def test_check_clearance_uses_the_platform_module_inside_the_package(self):
        from rp2040zero_platform import check_clearance
        self.assertTrue(hasattr(check_clearance.rp, "build"))


class ExportTest(unittest.TestCase):
    def test_export_writes_three_files(self):
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(rp.build(), d)
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)


if __name__ == "__main__":
    unittest.main()
