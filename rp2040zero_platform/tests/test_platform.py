import math
import unittest
import os
import tempfile

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
        self.assertAlmostEqual(bb.XMin, -4.04, delta=0.05)
        self.assertAlmostEqual(bb.XMax, 37.57, delta=0.1)
        self.assertAlmostEqual(bb.YMax, 27.76, delta=0.1)

    def test_covers_both_rings_and_the_ports(self):
        for x, y in (rp.RING_A, rp.RING_B, (rp.JACK_AXIS_X, -25.0), (21.0, -25.0)):
            self.assertTrue(inside(self.plate, x, y, -3.0), (x, y))

    def test_tail_is_removed(self):
        # The USB daughterboard tail would be at Y > 28 (KiCad y > 137.8).
        self.assertFalse(inside(self.plate, 21.0, 35.0, -3.0))


class RingPocketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shape = rp.build()

    def test_single_valid_solid(self):
        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.shape.Solids), 1)

    def test_bore_is_open_around_each_case_ring(self):
        for (cx, cy), top in zip(rp.RING_CENTRES, rp.RING_TOP_Z):
            for r in (0.0, 4.9):                 # centre and just inside the Ø10 ring
                for z in (-3.7, -2.0, top - 0.05):   # whole ring height
                    self.assertFalse(inside(self.shape, cx + r, cy, z), (cx, cy, r, z))
            self.assertFalse(inside(self.shape, cx, cy - 4.9, -2.0))

    def test_boss_wall_exists_on_the_free_side(self):
        ax, ay = rp.RING_A
        self.assertTrue(inside(self.shape, ax + 5.8, ay, -2.0))          # 0 deg
        self.assertTrue(inside(self.shape, ax + 0.7, ay + 5.8, -2.0))    # just past X >= 0.5
        self.assertTrue(inside(self.shape, ax - 3.7, ay, 1.0))           # cap reaches X = -3.8
        self.assertTrue(inside(self.shape, ax - 2.9, ay + 5.02, 1.0))    # 120 deg, r 5.8: boss kept
        bx, by = rp.RING_B
        self.assertTrue(inside(self.shape, bx - 5.8, by, -2.0))          # 180 deg
        self.assertTrue(inside(self.shape, bx, by + 5.8, -2.0))          # 90 deg
        self.assertTrue(inside(self.shape, bx, by + 5.8, 1.0))

    def test_boss_removed_where_the_case_is(self):
        ax, ay = rp.RING_A
        self.assertFalse(inside(self.shape, ax - 5.8, ay, -2.0))         # case wall side
        self.assertFalse(inside(self.shape, ax - 2.0, ay + 5.5, -2.0))   # fillet zone
        self.assertFalse(inside(self.shape, ax + 0.3, ay + 5.8, -2.0))   # X < 0.5, below Z = 0
        self.assertFalse(inside(self.shape, ax - 5.02, ay + 2.9, 1.0))   # 150 deg, r 5.8: boss cut at X = -3.8
        self.assertFalse(inside(self.shape, ax - 5.8, ay, 1.0))
        bx, by = rp.RING_B
        self.assertFalse(inside(self.shape, bx + 5.8, by, -2.0))         # 0 deg: right wall
        self.assertFalse(inside(self.shape, bx + 5.8, by, 1.0))
        self.assertFalse(inside(self.shape, bx + 5.0, by - 2.9, -2.0))   # 330 deg: flare

    def test_screw_seat_is_a_full_disc(self):
        for (cx, cy), top in zip(rp.RING_CENTRES, rp.RING_TOP_Z):
            for ang in range(0, 360, 45):
                x = cx + 3.5 * math.cos(math.radians(ang))
                y = cy + 3.5 * math.sin(math.radians(ang))
                if y < rp.PLATE_REAR_Y:
                    continue                      # trimmed at the rear edge
                self.assertTrue(inside(self.shape, x, y, top + 0.1), (cx, cy, ang))
                self.assertTrue(inside(self.shape, x, y, rp.CAP_TOP_Z - 0.1), (cx, cy, ang))

    def test_screw_hole_goes_through_cap(self):
        for (cx, cy), top in zip(rp.RING_CENTRES, rp.RING_TOP_Z):
            for z in (top + 0.05, 1.0, 1.95):
                self.assertFalse(inside(self.shape, cx, cy, z))
                self.assertFalse(inside(self.shape, cx + 2.1, cy, z))
                self.assertTrue(inside(self.shape, cx + 2.4, cy, z))

    def test_bore_follows_ring_b_flat_face(self):
        bx, by = rp.RING_B
        self.assertFalse(inside(self.shape, rp.RING_B_FLAT_X - 0.1, -25.0, -2.0))  # along the flat
        self.assertTrue(inside(self.shape, rp.RING_B_FLAT_X - 0.1, -23.5, -2.0))   # rail above it
        self.assertFalse(inside(self.shape, bx + 4.0, by, rp.RING_B_TOP_Z - 0.05))  # bore to the top
        self.assertTrue(inside(self.shape, bx + 4.0, by, rp.RING_B_TOP_Z + 0.05))   # seat above it

    def test_ring_a_boss_clears_the_fillet_blob_top(self):
        ax, ay = rp.RING_A
        seam = rp.RING_A_TOP_Z + rp.RING_A_BLOB_GAP
        self.assertFalse(inside(self.shape, ax - 2.0, ay + 5.5, seam - 0.05))   # gap over the blob
        self.assertTrue(inside(self.shape, ax - 2.0, ay + 5.5, seam + 0.05))    # boss above it
        self.assertTrue(inside(self.shape, ax + 4.0, ay, rp.RING_A_TOP_Z + 0.05))  # seat still on the ring

    def test_nothing_behind_rear_trim(self):
        # Ring B's boss would otherwise reach Y = -34.7, into the case wall.
        self.assertAlmostEqual(self.shape.BoundBox.YMin, rp.PLATE_REAR_Y, places=4)


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
        x = bx - 4.3                              # inside the seat disc, inside the board footprint
        self.assertTrue(inside(self.shape, x, by, rp.PCB_BOTTOM_Z - rp.CAP_RELIEF - 0.1))
        self.assertFalse(inside(self.shape, x, by, rp.PCB_BOTTOM_Z - rp.CAP_RELIEF + 0.1))
        # Full-height cap remains where the screw head sits.
        self.assertTrue(inside(self.shape, bx + 3.0, by + 3.0, rp.CAP_TOP_Z - 0.1))


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


class ExportTest(unittest.TestCase):
    def test_export_writes_three_files(self):
        shape = rp.build()
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(shape, d)
            self.assertEqual(set(paths), {'fcstd', 'step', 'stl'})
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)


if __name__ == '__main__':
    unittest.main()
