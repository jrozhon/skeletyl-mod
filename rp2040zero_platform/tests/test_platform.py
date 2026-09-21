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
        bb = self.shape.BoundBox
        self.assertAlmostEqual(bb.YMin, rp.PLATE_REAR_Y, places=4)
        self.assertAlmostEqual(bb.ZMax, rp.RAIL_TOP_Z, places=4)
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

    def test_screw_hole_and_counterbore(self):
        for cx, cy in (rp.RING_A, rp.RING_B):
            self.assertFalse(inside(self.shape, cx, cy, rp.PLATE_Z1 - EPS))
            # counterbore: open from below up to its floor, solid above it
            r = rp.HEAD_D / 2 + rp.HEAD_CLEAR - EPS
            self.assertFalse(inside(self.shape, cx + r, cy, rp.PLATE_Z0 + rp.COUNTERBORE_DEPTH - EPS))
            self.assertTrue(inside(self.shape, cx + r, cy, rp.PLATE_Z0 + rp.COUNTERBORE_DEPTH + EPS))
            self.assertTrue(inside(self.shape, cx + r + 2 * EPS, cy, rp.PLATE_Z0 + EPS))

    def test_screw_head_clears_the_bottom_plate(self):
        self.assertGreaterEqual(rp.HEAD_BOTTOM_Z, rp.BOTTOM_PLATE_Z + 0.3)
        self.assertGreaterEqual(rp.SEAT_FLOOR_T, 0.8)

    # -- case clearances (numbers measured from the V4 STL) ---------------
    def test_clear_of_the_rear_wall(self):
        self.assertGreaterEqual(rp.PLATE_REAR_Y, rp.WALL_INNER_Y + 0.3)
        # The board and jack reach into the wall recess, which is free from Z -5.5 to 3.
        self.assertGreater(rp.BOARD_Y0, rp.WALL_RECESS_Y + 0.2)
        self.assertGreater(rp.JACK_Y0, rp.WALL_RECESS_Y)
        self.assertLess(rp.RAIL_TOP_Z, 3.0)

    def test_clear_of_ring_b(self):
        # Right ledge (all Y) stays off ring B's flat face; right rail starts in front of the blob.
        self.assertLessEqual(rp.RAIL_X1, rp.RING_B_FLAT_X - 0.5)
        self.assertTrue(inside(self.shape, rp.RAIL_X1 + rp.RAIL_T / 2, rp.RING_B_FREE_Y + 0.5, rp.PLATE_Z1 + 1.0))
        self.assertFalse(inside(self.shape, rp.RAIL_X1 + rp.RAIL_T / 2, rp.RING_B_FREE_Y - 0.5, rp.PLATE_Z1 + 1.0))
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

    def test_rails_and_front_stop_stand_above_the_pcb(self):
        y = rp.BOARD_Y1 - 2.0
        for x in (rp.RAIL_X0 - rp.RAIL_T / 2, rp.RAIL_X1 + rp.RAIL_T / 2):
            self.assertTrue(inside(self.shape, x, y, rp.RAIL_TOP_Z - EPS))
            self.assertFalse(inside(self.shape, x, y, rp.RAIL_TOP_Z + EPS))
        self.assertTrue(inside(self.shape, rp.BOARD_CX, rp.STOP_Y0 + rp.RAIL_T / 2, rp.RAIL_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, rp.BOARD_CX, rp.STOP_Y0 - EPS, rp.PCB_Z1))
        self.assertGreaterEqual(rp.RAIL_TOP_Z, rp.PCB_Z1 + 1.0)

    def test_window_under_the_board_is_open_to_the_rear(self):
        for y in (rp.PLATE_REAR_Y + 0.1, rp.BOARD_Y0 + 3.0, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP - 0.1):
            self.assertFalse(inside(self.shape, rp.BOARD_CX, y, rp.PLATE_Z1 - 1.0), y)
        self.assertTrue(inside(self.shape, rp.BOARD_CX, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP + 0.1, rp.PLATE_Z1 - 1.0))
        # the strips under the ledges remain
        self.assertTrue(inside(self.shape, rp.BOARD_X0 + rp.WINDOW_INSET - 0.1, rp.BOARD_Y0 + 3.0, rp.PLATE_Z1 - 1.0))

    def test_components_clear_the_plate(self):
        self.assertGreaterEqual(rp.USB_Z0 - rp.PLATE_Z1, 0.5)

    # -- jack pocket ------------------------------------------------------
    def test_jack_axis_matches_the_case_hole(self):
        self.assertAlmostEqual(rp.JACK_AXIS_Z, rp.JACK_HOLE_Z)
        self.assertLess(rp.JACK_NOSE_D, rp.JACK_HOLE_D)
        self.assertLessEqual(rp.JACK_Y0 - rp.JACK_NOSE_L, rp.WALL_OUTER_Y + 0.5)
        # pocket floor below the plate top, but a sensible floor remains
        self.assertGreater(rp.PLATE_Z1 - rp.JACK_FLOOR_Z, 0.0)
        self.assertGreaterEqual(rp.JACK_FLOOR_Z - rp.PLATE_Z0, 1.0)

    def test_jack_pocket_floor_between_the_slots(self):
        y = rp.JACK_Y0 + 5.0
        for yy in (y, rp.JACK_Y1 - 0.3):
            self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, yy, rp.JACK_FLOOR_Z - EPS))
            self.assertFalse(inside(self.shape, rp.JACK_AXIS_X, yy, rp.JACK_FLOOR_Z + EPS))
        # pocket walls just outside the body, in front of the leg slots
        yw = rp.JACK_POCKET_Y1 - 0.3
        for x in (rp.JACK_X0 - rp.JACK_POCKET_CLEAR - EPS, rp.JACK_X1 + rp.JACK_POCKET_CLEAR + EPS):
            self.assertTrue(inside(self.shape, x, yw, rp.PLATE_Z1 - EPS), x)
        self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, rp.JACK_POCKET_Y1 + EPS, rp.PLATE_Z1 - EPS))
        self.assertFalse(inside(self.shape, rp.JACK_AXIS_X, rp.JACK_POCKET_Y1 - EPS, rp.PLATE_Z1 - EPS))

    def test_leg_slots_on_both_sides_open_at_the_rear(self):
        for xs, out in ((rp.JACK_X0, -1), (rp.JACK_X1, 1)):
            for x in (xs + out * (rp.JACK_LEG_OUT - 0.1), xs, xs - out * (rp.JACK_LEG_IN - 0.1)):
                for y in (rp.PLATE_REAR_Y + 0.1, rp.JACK_Y0 + rp.JACK_LEG_Y0 + rp.JACK_LEG_L - 0.1):
                    self.assertFalse(inside(self.shape, x, y, rp.PLATE_Z1 - 1.0), (x, y))
            self.assertTrue(inside(self.shape, xs, rp.JACK_Y0 + rp.JACK_LEG_Y0 + rp.JACK_LEG_L + 0.1,
                                   rp.PLATE_Z1 - 1.0))

    def test_ribs_and_end_stop(self):
        y = rp.JACK_Y1 - 1.0
        for x in (rp.RIB_L_X0 + rp.RIB_T / 2, rp.RIB_R_X0 + 0.5):
            self.assertTrue(inside(self.shape, x, y, rp.RIB_TOP_Z - EPS), x)
            self.assertFalse(inside(self.shape, x, y, rp.RIB_TOP_Z + EPS), x)
        self.assertTrue(inside(self.shape, rp.JACK_AXIS_X, rp.JACK_STOP_Y0 + rp.RIB_T / 2, rp.RIB_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, rp.JACK_AXIS_X, rp.JACK_STOP_Y0 - EPS, rp.PLATE_Z1 + 1.0))
        # the right rib runs into the board's left rail: no gap between them
        self.assertTrue(inside(self.shape, rp.RIB_R_X1 - EPS, y, rp.RIB_TOP_Z - EPS))
        self.assertTrue(inside(self.shape, rp.RIB_R_X1 + EPS, y, rp.RIB_TOP_Z - EPS))


class ExportTest(unittest.TestCase):
    def test_export_writes_three_files(self):
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(rp.build(), d)
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)


if __name__ == "__main__":
    unittest.main()
