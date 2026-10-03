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
        self.assertAlmostEqual(bb.ZMax, max(rp.HOOK_TOP_Z, rp.MID_WALL_TOP_Z), places=4)
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

    def test_window_under_the_board_closed_by_the_band(self):
        for y in (rp.PLATE_REAR_Y + 0.1, rp.PLATE_REAR_Y + rp.BAND_W - 0.1):     # band under the USB-C shell
            self.assertTrue(inside(self.shape, rp.BOARD_CX, y, rp.PLATE_Z1 - 1.0), y)
        self.assertGreaterEqual(rp.BAND_W, 4.0)
        self.assertGreaterEqual(rp.USB_Z0 - rp.PLATE_Z1, 0.5)                     # the shell clears it
        for y in (rp.PLATE_REAR_Y + rp.BAND_W + 0.1, rp.BOARD_Y0 + 8.0, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP - 0.1):
            self.assertFalse(inside(self.shape, rp.BOARD_CX, y, rp.PLATE_Z1 - 1.0), y)
        self.assertTrue(inside(self.shape, rp.BOARD_CX, rp.BOARD_Y1 - rp.WINDOW_FRONT_GAP + 0.1, rp.PLATE_Z1 - 1.0))
        # the strips under the ledges remain
        self.assertTrue(inside(self.shape, rp.BOARD_X0 + rp.WINDOW_INSET - 0.1, rp.BOARD_Y0 + 3.0, rp.PLATE_Z1 - 1.0))

    def test_components_clear_the_plate(self):
        self.assertGreaterEqual(rp.USB_Z0 - rp.PLATE_Z1, 0.5)

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
                    (rp.SHELL_WALL_X1 - rp.SHELL_WALL_T <= x <= rp.SER_X1
                     and y <= rp.SER_SHELL_Y1),                                                # pedestal + shell wall
                    rp.MID_X0 <= x <= rp.MID_X1 and y <= rp.POCKET_Y1,                         # middle wall
                    (rp.POCKET_X0 - rp.POCKET_WALL_T <= x <= rp.MID_X0
                     and rp.SER_SHELL_Y1 <= y <= rp.POCKET_Y1),                                # glue pocket
                    (any(a <= x <= b for a, b in corners)
                     and rp.BOARD_Y1 - rp.CORNER_SIDE_L <= y <= rp.CORNER_Y1),
                    rp.HOOK_X0 <= x <= rp.HOOK_X1 and rp.HOOK_Y0 <= y <= rp.LEAF_ROOT_Y + 0.5,   # snap hook head + leaf
                ]
                self.assertTrue(any(known), (x, y))

    def test_serial_shell_face_0_8_behind_the_wall(self):
        self.assertAlmostEqual(rp.SER_FACE_Y - rp.WALL_OUTER_Y, 0.8)

    def test_serial_breakout_overall_length(self):
        self.assertAlmostEqual(rp.SER_PCB_Y1 - rp.SER_FACE_Y, rp.SER_L)

    def test_serial_pcb_clears_the_rp2040_ledge(self):
        self.assertGreaterEqual(rp.LEDGE_X0 - rp.SER_PCB_X1, 0.15)

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

    # -- RP2040-Zero: left lip, snap hook (rev. 4) -------------------------
    def test_zero_pad_positions(self):
        self.assertAlmostEqual(rp.zero_pad_y(4) - rp.BOARD_Y0, 10.0, places=1)
        self.assertAlmostEqual(rp.zero_pad_y(5) - rp.zero_pad_y(4), 2.54)

    def test_left_lip_over_free_pads(self):
        self.assertAlmostEqual(rp.LIP_Z0 - rp.PCB_Z1, rp.LIP_GAP)
        self.assertAlmostEqual(rp.ZERO_LIP_X1 - rp.BOARD_X0, rp.LIP_OVER)
        self.assertAlmostEqual(rp.MID_Y1, rp.ZERO_LIP_Y1)
        x = rp.BOARD_X0 + rp.LIP_OVER / 2
        self.assertEqual(rp.ZERO_LIP_PADS, (3, 5))
        for k in (3, 4, 5):                                  # free on both halves (hand-wired): GP2-GP4 (right), 3V3/GP29/GP28 (left)
            self.assertTrue(inside(self.shape, x, rp.zero_pad_y(k), rp.LIP_Z0 + EPS), k)
            self.assertFalse(inside(self.shape, x, rp.zero_pad_y(k), rp.LIP_Z0 - EPS), k)
        self.assertFalse(inside(self.shape, x, rp.zero_pad_y(2), rp.LIP_Z0 + EPS))   # GP1 (serial D-)
        # >= 0.7 between the lip and GP1's pad (pads are ~1.5 long)
        self.assertGreaterEqual(rp.ZERO_LIP_Y0 - (rp.zero_pad_y(2) + 0.75), 0.7)

    def test_left_lip_clear_of_pad6_on_the_mirrored_half(self):
        # The RP2040-Zero is not mirrored for the left half: there the lip's edge
        # carries 5V..GP27, and pad 6 is GP27 (R4, wired). Keep >= 0.7 off its pad.
        x = rp.BOARD_X0 + rp.LIP_OVER / 2
        self.assertFalse(inside(self.shape, x, rp.zero_pad_y(6), rp.LIP_Z0 + EPS))
        self.assertGreaterEqual((rp.zero_pad_y(6) - 0.75) - rp.ZERO_LIP_Y1, 0.7)
        # nor the high middle wall beside it
        self.assertFalse(inside(self.shape, rp.MID_X1 - EPS, rp.zero_pad_y(6), rp.PCB_Z1))

    def test_hook_catch_has_a_land(self):
        # The board, pushed against the middle wall by the ramp, ends at MID_X1 + BOARD_W.
        # The lip must overlap it by >= 0.25 over HOOK_LAND (>= 2 layers), not only at a knife edge.
        self.assertGreaterEqual(rp.HOOK_LAND, 0.4)
        edge = rp.MID_X1 + rp.BOARD_W
        for z in (rp.LIP_Z0 + 0.05, rp.LIP_Z0 + rp.HOOK_LAND - 0.05):
            self.assertTrue(inside(self.shape, edge - 0.25, rp.HOOK_YC, z), z)
            self.assertTrue(inside(self.shape, rp.HOOK_TIP_X + EPS, rp.HOOK_YC, z), z)
        self.assertLessEqual(rp.HOOK_TOP_Z, 3.35 - 0.3)       # case probed clear to Z 3.35 there

    def test_hook_arm_and_lip(self):
        y = rp.HOOK_YC
        self.assertAlmostEqual(rp.HOOK_Y1, rp.ZERO_LIP_Y1)
        # the catch covers pad 5 (GP28 here, GP4 on the mirrored half)
        for dy in (-0.75, 0.0, 0.75):
            y_pad = rp.zero_pad_y(5) + dy
            self.assertTrue(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y_pad, rp.LIP_Z0 + EPS), dy)
            self.assertFalse(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y_pad, rp.LIP_Z0 - EPS), dy)
        self.assertGreaterEqual(rp.HOOK_W, 2.4)
        self.assertTrue(inside(self.shape, rp.HOOK_X0 + rp.HOOK_T / 2, y, rp.PLATE_Z1 + 1.0))
        self.assertFalse(inside(self.shape, rp.LEDGE_X1 + rp.HOOK_GAP / 2, y, rp.PLATE_Z1 + 1.0))  # free of the ledge
        self.assertTrue(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y, rp.LIP_Z0 + EPS))
        self.assertFalse(inside(self.shape, rp.BOARD_X1 - rp.HOOK_LIP / 2, y, rp.LIP_Z0 - EPS))
        self.assertFalse(inside(self.shape, rp.HOOK_TIP_X - EPS, y, rp.LIP_Z0 + EPS))
        # 45 deg ramp on top: solid just above the tip, empty at the top over the tip
        self.assertTrue(inside(self.shape, rp.HOOK_TIP_X + 0.1, y, rp.LIP_Z0 + 0.05))
        self.assertFalse(inside(self.shape, rp.HOOK_TIP_X + 0.1, y, rp.HOOK_TOP_Z - EPS))
        self.assertTrue(inside(self.shape, rp.HOOK_X0 + EPS, y, rp.HOOK_TOP_Z - EPS))
        # one straight head: the same profile at both ends, nothing past them above the leaf
        for y_end in (rp.HOOK_Y0 + 0.05, rp.HOOK_Y1 - 0.05):
            self.assertTrue(inside(self.shape, rp.HOOK_TIP_X + 0.1, y_end, rp.LIP_Z0 + 0.05), y_end)
            self.assertTrue(inside(self.shape, rp.HOOK_X1 - EPS, y_end, rp.HOOK_TOP_Z - EPS), y_end)
        for y_out in (rp.HOOK_Y0 - 0.05, rp.HOOK_Y1 + 0.05):
            for x in (rp.HOOK_TIP_X + 0.1, rp.HOOK_X0 + 0.5):
                self.assertFalse(inside(self.shape, x, y_out, rp.LEAF_TOP_Z + EPS), (x, y_out))

    def test_hook_leaf_free_in_its_slot(self):
        # A solid head on the free end of a leaf; both stand on the bed in a slot
        # through the plate, the leaf outside the front-right corner stop.
        self.assertAlmostEqual(rp.LEAF_X0, rp.BOARD_X1 + rp.CORNER_GAP + rp.CORNER_T + rp.HOOK_GAP)
        xm = (rp.LEAF_X0 + rp.LEAF_X1) / 2
        ym = (rp.HOOK_Y1 + rp.LEAF_ROOT_Y) / 2
        for z in (rp.PLATE_Z0 + EPS, rp.LEAF_TOP_Z - EPS):
            self.assertTrue(inside(self.shape, xm, ym, z), z)
        self.assertFalse(inside(self.shape, xm, ym, rp.LEAF_TOP_Z + EPS))           # below the PCB: wires stay free
        self.assertLessEqual(rp.LEAF_TOP_Z, rp.PCB_Z0)
        for x, y in ((rp.LEAF_X0 - rp.HOOK_GAP / 2, ym),                             # beside the corner stop
                     (rp.LEAF_X1 + 0.1, ym),                                         # outside
                     (rp.SLOT_X0 + rp.HOOK_GAP / 2, rp.HOOK_YC),                     # head, inner side
                     (rp.HOOK_X0 + 0.5, rp.SLOT_Y0 + rp.HOOK_GAP / 2),               # behind the head
                     (rp.HOOK_X0 + 0.5, rp.HOOK_Y1 + rp.HOOK_GAP / 2)):              # in front of the head
            for z in (rp.PLATE_Z0 + EPS, rp.PLATE_Z1 - EPS):
                self.assertFalse(inside(self.shape, x, y, z), (x, y, z))
        # rooted in the plate
        self.assertTrue(inside(self.shape, xm, rp.LEAF_ROOT_Y + 0.2, rp.PLATE_Z1 - EPS))
        # the plate is widened to carry the slot's outer side
        self.assertTrue(inside(self.shape, rp.SLOT_X1 + 0.2, ym, rp.PLATE_Z1 - EPS))

    def test_hook_head_has_room_for_its_full_travel(self):
        # The previous slot left 0.4 outside a 0.7 travel: the head hit the
        # plate and the board bent the column above it until it snapped.
        self.assertGreaterEqual(rp.SLOT_X1 - rp.HOOK_X1, rp.HOOK_LIP + 0.3)
        for y in (rp.HOOK_Y0 + 0.1, rp.HOOK_YC, rp.HOOK_Y1 + 0.1, (rp.HOOK_Y1 + rp.LEAF_ROOT_Y) / 2):
            for z in (rp.PLATE_Z0 + EPS, rp.PLATE_Z1 - EPS):
                self.assertFalse(inside(self.shape, rp.HOOK_X1 + rp.HOOK_LIP + 0.1, y, z), (y, z))

    def test_hook_head_is_solid(self):
        # nothing thin stands up: the head is HOOK_X1 - HOOK_X0 thick from the bed to the catch
        self.assertGreaterEqual(rp.HOOK_X1 - rp.HOOK_X0, 3.5)
        for z in (rp.PLATE_Z0 + EPS, rp.PLATE_Z1 + 1.0, rp.LIP_Z0 - EPS, rp.HOOK_TOP_Z - EPS):
            for x in (rp.HOOK_X0 + EPS, rp.HOOK_X1 - EPS):
                self.assertTrue(inside(self.shape, x, rp.HOOK_YC, z), (x, z))

    def test_hook_strain_ok_for_pla(self):
        # the leaf bends along its printed lines (stress along Y, within each layer)
        length = rp.LEAF_ROOT_Y - rp.HOOK_Y1                 # the head is rigid: the leaf bends from it
        strain = 1.5 * rp.HOOK_T * rp.HOOK_LIP / length ** 2
        self.assertLessEqual(strain, 0.02)                 # PLA along the extrusions, opened now and then
        self.assertGreaterEqual(rp.HOOK_T, 1.6)

    def test_hook_clear_of_used_pads(self):
        # GP27 (R4) is pad 6 on the right edge; GP29 (pad 4) is free
        self.assertGreaterEqual(rp.zero_pad_y(6) - 0.75 - rp.HOOK_Y1, 0.7)

    def test_hook_clear_of_ring_b(self):
        # in front of RING_B_HOOK_Y ring B's curved side is beyond RING_B_HOOK_X: >= 0.3 off
        # the leaf's free end bent outward (a bit more than the catch: x 1.25)
        self.assertGreaterEqual(rp.HOOK_Y0, rp.RING_B_HOOK_Y + 0.3)
        self.assertLessEqual(rp.HOOK_X1 + 1.25 * rp.HOOK_LIP, rp.RING_B_HOOK_X - 0.3)

    @unittest.skipUnless(os.path.exists(os.path.join(os.path.dirname(rp.__file__), "case_v4_103_usb_serial.stl")),
                         "modified case STL missing: run case_usb_serial.py")
    def test_hook_clear_of_the_case_when_pushed_aside(self):
        # With the hook shifted outward by its full travel it stays >= 0.2 off
        # the case (ring B is just behind the head).
        import Part
        from rp2040zero_platform.check_clearance import load_stl, case_to_platform
        tris = case_to_platform(load_stl(os.path.join(os.path.dirname(rp.__file__), "case_v4_103_usb_serial.stl")))
        hook = rp.make_hook()
        hook.translate(Vector(rp.HOOK_LIP, 0, 0))
        hook = hook.common(rp.box(28.0, 40.0, rp.HOOK_Y0 - 1.0, rp.HOOK_Y1 + 1.0, rp.PLATE_Z1 + 0.05, 5.0))
        bb = hook.BoundBox
        near = [t for t in tris if t[:, 0].max() > bb.XMin - 1 and t[:, 0].min() < bb.XMax + 1
                and t[:, 1].max() > bb.YMin - 1 and t[:, 1].min() < bb.YMax + 1
                and t[:, 2].max() > bb.ZMin - 1 and t[:, 2].min() < bb.ZMax + 1]
        self.assertTrue(near)
        faces = [Part.Face(Part.makePolygon([Vector(*p) for p in t] + [Vector(*t[0])])) for t in near]
        self.assertGreaterEqual(hook.distToShape(Part.makeCompound(faces))[0], 0.2)

    def test_board_cannot_slip_off_a_lip(self):
        # sideways play: middle wall (MID_X1) to the front-right corner stop (BOARD_X1 + CORNER_GAP)
        play = (rp.BOARD_X1 + rp.CORNER_GAP) - (rp.MID_X1 + rp.BOARD_W)
        self.assertAlmostEqual(play, rp.CORNER_GAP + rp.BOARD_SIDE_GAP)
        self.assertGreaterEqual(rp.ZERO_LIP_X1 - (rp.MID_X1 + play), 0.25)              # left lip
        self.assertGreaterEqual((rp.MID_X1 + rp.BOARD_W) - rp.HOOK_TIP_X, 0.55)        # hook
        # the hook's underside chamfer stays outside the PCB even with the board pushed right
        self.assertGreaterEqual(rp.LEDGE_X1, rp.BOARD_X1 + rp.CORNER_GAP)

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

    # -- minimum wall thickness (PLA, 0.4 nozzle) --------------------------
    def test_middle_wall_fused_with_the_ledge_below_the_pcb(self):
        # Between the shell and the RP2040 the wall can only be 0.83; below the
        # PCB it is one with the left ledge, so only Z 0.35..3.0 is that thin.
        y = rp.zero_pad_y(4)
        for x in (rp.MID_X0 + EPS, rp.MID_X1 + 0.1, rp.LEDGE_X0 + rp.LEDGE_W - EPS):
            self.assertTrue(inside(self.shape, x, y, rp.PCB_Z0 - EPS), x)
        self.assertGreaterEqual(rp.LEDGE_X0 + rp.LEDGE_W - rp.MID_X0, 1.8)
        self.assertGreaterEqual(rp.MID_WALL_TOP_Z - rp.LIP_Z0, 2.5)       # the RP2040 lip is 2.5+ thick

    def test_pocket_left_wall_thick_enough(self):
        self.assertGreaterEqual(rp.POCKET_WALL_T, 1.2)

    def test_strip_outside_the_hook_slot_thick_enough(self):
        self.assertGreaterEqual(rp.HOOK_PLATE_X1 - rp.SLOT_X1, 1.2)
        self.assertTrue(inside(self.shape, rp.HOOK_PLATE_X1 - 0.1, rp.HOOK_YC, rp.PLATE_Z1 - EPS))
        # and behind the slot / in front of the root, so the strip is a closed frame
        for y in (rp.SLOT_Y0 - 1.15, rp.LEAF_ROOT_Y + 1.15):
            self.assertTrue(inside(self.shape, rp.SLOT_X1 + 0.3, y, rp.PLATE_Z1 - EPS), y)   # past the body (X 31.8)

    def test_shell_side_wall_has_no_sliver_at_the_corner(self):
        # the plate outline clips the wall diagonally along the case's rear-left corner:
        # the wall starts where its full thickness fits
        x0 = rp.SHELL_WALL_X1 - rp.SHELL_WALL_T
        z = rp.SER_CZ - EPS
        self.assertFalse(inside(self.shape, rp.SHELL_WALL_X1 - 0.1, rp.SHELL_WALL_Y0 - 0.1, z))
        self.assertTrue(inside(self.shape, x0 + 0.05, rp.SHELL_WALL_Y0 + 0.05, z))
        self.assertTrue(inside(self.shape, rp.SHELL_WALL_X1 - 0.05, rp.SHELL_WALL_Y0 + 0.05, z))

    def test_serial_measured_lengths(self):
        self.assertAlmostEqual(rp.SER_SHELL_L, 8.5)
        self.assertAlmostEqual(rp.SER_L, 14.0)
        self.assertAlmostEqual(rp.SER_SHELL_Y1 - rp.SER_FACE_Y, 8.5)

    def test_rev3_serial_stops_are_gone(self):
        self.assertFalse(hasattr(rp, "make_serial_stops"))

    def test_shell_side_wall_locates_the_shell(self):
        y = rp.SER_SHELL_Y1 - 1.0
        x = rp.SHELL_WALL_X1 - rp.SHELL_WALL_T / 2
        self.assertTrue(inside(self.shape, x, y, rp.SER_CZ - EPS))
        self.assertFalse(inside(self.shape, x, y, rp.SER_CZ + EPS))      # low enough to tilt the part in
        self.assertAlmostEqual(rp.SER_X0 - rp.SHELL_WALL_X1, 0.15)      # a little play: easy to put in
        self.assertFalse(inside(self.shape, rp.SHELL_WALL_X1 + EPS, y, rp.SER_Z0 + 0.5))

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

    def test_breakout_drops_straight_in(self):
        # nothing overhangs the breakout's footprint (shell and tail), up to well above it
        for x in (rp.SER_X0 + 0.05, rp.SER_CX, rp.SER_X1 - 0.05):
            for y in (rp.SER_SHELL_Y1 - 0.5, rp.SER_SHELL_Y1 + 0.5, (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2,
                      rp.SER_PCB_Y1 - 0.1):
                for z in (rp.SER_TAIL_Z1 + EPS, rp.SER_Z0 + rp.SER_H + EPS, rp.MID_WALL_TOP_Z + 1.0):
                    self.assertFalse(inside(self.shape, x, y, z), (x, y, z))

    def test_nothing_under_the_tail(self):
        # the shell on the pedestal alone sets the level: no rib under the tail to seesaw on
        for x in (rp.SER_PCB_X0 + 0.5, rp.SER_CX, rp.SER_PCB_X1 - 0.5):
            for y in (rp.SER_SHELL_Y1 + 0.1, (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2, rp.SER_PCB_Y1 - 0.1):
                self.assertFalse(inside(self.shape, x, y, rp.PLATE_Z1 + EPS), (x, y))
        self.assertFalse(hasattr(rp, "make_pocket_keys"))                 # no glue through to the underside

    def test_glue_rib_and_trough(self):
        x = rp.SER_CX
        ym = (rp.SER_STOP_Y0 + rp.RIB_Y1) / 2
        self.assertAlmostEqual(rp.RIB_TOP_Z, rp.SER_TAIL_Z1 - 0.2)           # a layer under the tail top: wires lie flat
        self.assertTrue(inside(self.shape, x, ym, rp.RIB_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, x, ym, rp.RIB_TOP_Z + EPS))
        yt = (rp.RIB_Y1 + rp.TROUGH_Y1) / 2
        self.assertTrue(inside(self.shape, x, yt, rp.TROUGH_FLOOR_Z - EPS))
        self.assertFalse(inside(self.shape, x, yt, rp.TROUGH_FLOOR_Z + EPS))
        self.assertGreaterEqual(rp.RIB_TOP_Z - rp.TROUGH_FLOOR_Z, 1.5)       # deep enough to hook the glue
        yb = (rp.TROUGH_Y1 + rp.POCKET_Y1) / 2
        self.assertTrue(inside(self.shape, x, yb, rp.SER_STOP_TOP_Z - EPS))
        # the trough is closed on both sides; on the right it stays below the RP2040's PCB
        self.assertTrue(inside(self.shape, rp.POCKET_X0 - EPS, yt, rp.SER_STOP_TOP_Z - EPS))
        self.assertTrue(inside(self.shape, rp.MID_X0 + EPS, yt, rp.SER_STOP_TOP_Z - EPS))
        self.assertFalse(inside(self.shape, rp.MID_X0 + EPS, yt, rp.SER_STOP_TOP_Z + EPS))

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
        ym = (rp.SER_STOP_Y0 + rp.RIB_Y1) / 2
        for x in (rp.SER_PCB_X0 + 0.5, rp.SER_CX, rp.SER_PCB_X1 - 0.5):
            self.assertTrue(inside(self.shape, x, ym, rp.RIB_TOP_Z - EPS), x)
        self.assertFalse(inside(self.shape, rp.SER_CX, rp.SER_STOP_Y0 - EPS, rp.SER_CZ))

    def test_pocket_open_above_the_tail(self):
        y = (rp.SER_SHELL_Y1 + rp.SER_PCB_Y1) / 2
        for z in (rp.SER_CZ, rp.SER_TAIL_Z1 + EPS, rp.SER_STOP_TOP_Z + EPS):
            self.assertFalse(inside(self.shape, rp.SER_CX, y, z), z)


    # -- test coupon -------------------------------------------------------
    def test_coupon_holds_the_lips_hook_and_pocket(self):
        coupon = rp.make_coupon(self.shape)
        self.assertTrue(coupon.isValid())
        self.assertEqual(len(coupon.Solids), 1)
        x0, x1, y0, y1 = rp.COUPON
        bb = coupon.optimalBoundingBox(True, False)   # the fast box is loose around the ring B pad
        self.assertGreaterEqual(bb.XMin, x0 - 1e-6)
        self.assertLessEqual(bb.XMax, x1 + 1e-6)
        self.assertGreaterEqual(bb.YMin, y0 - 1e-6)
        self.assertLessEqual(bb.YMax, y1 + 1e-6)
        for p in ((rp.HOOK_X0 + rp.HOOK_T / 2, rp.HOOK_YC, rp.PLATE_Z1 + 1.0),                     # hook arm
                  (rp.BOARD_X0 + rp.LIP_OVER / 2, rp.zero_pad_y(5), rp.LIP_Z0 + EPS),             # RP2040 lip
                  (rp.SER_CX, (rp.SER_STOP_Y0 + rp.RIB_Y1) / 2, rp.RIB_TOP_Z - EPS),         # glue rib
                  (rp.BOARD_CX, rp.PLATE_REAR_Y + rp.BAND_W / 2, rp.PLATE_Z1 - EPS)):             # band
            self.assertTrue(inside(coupon, *p), p)
        self.assertAlmostEqual(bb.ZMin, rp.PLATE_Z0, places=4)
        # the whole pedestal and shell wall, so the breakout can be tried on it
        self.assertAlmostEqual(y0, rp.PLATE_REAR_Y)
        self.assertTrue(inside(coupon, rp.SER_CX, rp.PLATE_REAR_Y + 0.5, rp.SER_Z0 - EPS))

class ImportTest(unittest.TestCase):
    def test_check_clearance_uses_the_platform_module_inside_the_package(self):
        from rp2040zero_platform import check_clearance
        self.assertTrue(hasattr(check_clearance.rp, "build"))


class ExportTest(unittest.TestCase):
    def test_export_writes_the_part_and_the_coupon(self):
        with tempfile.TemporaryDirectory() as d:
            paths = rp.export(rp.build(), d)
            self.assertEqual(set(paths), {'fcstd', 'step', 'stl', 'coupon_stl'})
            self.assertEqual(os.path.basename(paths['coupon_stl']), "hook_coupon.stl")
            for p in paths.values():
                self.assertTrue(os.path.exists(p), p)
                self.assertGreater(os.path.getsize(p), 1000, p)

if __name__ == "__main__":
    unittest.main()
