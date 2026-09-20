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
