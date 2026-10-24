"""Spec checks for integral cover, independent of export tessellation."""
import unittest
from build123d import Align, Compound, Cylinder, Pos, Vector, import_step
from bottom_cover_with_feet import cover_case_local, gen_step
from rear_foot import C4, SCREWS, common_volume, assembled_parts


class IntegratedCoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cover = cover_case_local()
        cls.original = import_step(C4 / 'bottom_cover.step')

    def test_connected_and_original_preserved(self):
        self.assertTrue(self.cover.is_valid)
        self.assertEqual(len(self.cover.solids()), 1)
        self.assertAlmostEqual(common_volume(self.cover, self.original), self.original.volume, places=5)
        added = self.cover - self.original
        self.assertLessEqual(Compound(children=list(added)).bounding_box().max.Z, 1e-6)

    def test_original_screw_access_preserved(self):
        for x, y in SCREWS:
            tool = Pos(x, y, -12) * Cylinder(1.19, 16, align=(Align.CENTER, Align.CENTER, Align.MIN))
            self.assertLess(common_volume(tool, self.cover), 1e-6)
            head = Pos(x, y, 0) * Cylinder(2, 2, align=(Align.CENTER, Align.CENTER, Align.MAX))
            self.assertLess(common_volume(head, self.cover), 1e-6)

    def test_bases_flare_out_toward_plate(self):
        for y in (10, 66):
            for x in (12, 94):
                self.assertTrue(self.cover.is_inside(Vector(x + 7.1, y, -0.1)))

    def test_print_pose(self):
        shape = gen_step()
        bounds = shape.bounding_box()
        self.assertAlmostEqual(bounds.min.Z, 0, places=6)
        self.assertAlmostEqual(bounds.size.X, 106, places=5)
        self.assertAlmostEqual(bounds.size.Y, 74, places=5)

    def test_support_plane(self):
        _, report = assembled_parts()
        self.assertTrue(all(abs(z) < 1e-6 for z in report['support_min_z_mm']))
        self.assertGreater(report['screw_head_floor_min_clearance_mm'], .4)


if __name__ == '__main__':
    unittest.main()
