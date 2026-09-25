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


def first_hit_y(tris, x, z, y_start):
    """Smallest Y > y_start where the ray from (x, y_start, z) along +Y meets a
    triangle (Moller-Trumbore), or None. Much faster than isInside() stepping
    on the 55k-face case solid."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    near = ((np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) <= x)
            & (np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) >= x)
            & (np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]) <= z)
            & (np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2]) >= z))
    a, b, c = a[near], b[near], c[near]
    d = np.array([0.0, 1.0, 0.0])
    e1, e2 = b - a, c - a
    h = np.cross(d, e2)
    det = (e1 * h).sum(1)
    ok = np.abs(det) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = np.array([x, y_start, z]) - a
    u = f * (s * h).sum(1)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * (e2 * q).sum(1)
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return y_start + t[hit].min() if hit.any() else None


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
        # Rays along +Y on a ring just outside the plug: the original wall's
        # outer face must be at or behind the plug's outer end.
        tris = case_to_platform(load_stl(cs.DEFAULT_CASE))
        r = cs.PLUG_D / 2.0 + 0.05
        plug_y0 = rp.WALL_OUTER_Y + cs.PLUG_OUTER_GAP
        for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            x = rp.JACK_AXIS_X + r * np.cos(a)
            z = rp.JACK_HOLE_Z + r * np.sin(a)
            first = first_hit_y(tris, x, z, -38.0)
            self.assertIsNotNone(first, (x, z))
            self.assertLessEqual(first, plug_y0 + 0.01, (x, z))

    def test_volume_change_is_fill_minus_slot(self):
        # fill (hole + chamfer, ~+42) minus slot through 2 mm (~-65): measured -23.3
        self.assertAlmostEqual(self.mod.Volume - self.orig.Volume, -23.3, delta=2.0)

    def test_check_accepts_the_modified_case(self):
        self.assertIsNone(cs.check(self.orig, self.mod))

    def test_check_rejects_a_failed_boolean(self):
        # an unchanged case (boolean silently did nothing) and a split result
        self.assertIsNotNone(cs.check(self.orig, self.orig))
        self.assertIsNotNone(cs.check(self.orig, self.mod.fuse(cs.make_slot_cutter().translate(Vector(0, 0, 50)))))

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
