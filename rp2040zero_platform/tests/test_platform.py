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
        self.assertAlmostEqual(bb.XMin, -4.04, delta=0.05)
        self.assertAlmostEqual(bb.XMax, 37.57, delta=0.1)
        self.assertAlmostEqual(bb.YMax, 27.76, delta=0.1)

    def test_covers_both_rings_and_the_ports(self):
        for x, y in (rp.RING_A, rp.RING_B, (rp.JACK_AXIS_X, -25.0), (21.0, -25.0)):
            self.assertTrue(inside(self.plate, x, y, -3.0), (x, y))

    def test_tail_is_removed(self):
        # The USB daughterboard tail would be at Y > 28 (KiCad y > 137.8).
        self.assertFalse(inside(self.plate, 21.0, 35.0, -3.0))


if __name__ == '__main__':
    unittest.main()
