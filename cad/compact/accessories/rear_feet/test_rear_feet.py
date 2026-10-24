"""Spec-driven B-rep checks for the retrofit, including contact and clearances."""
import unittest
from build123d import Vector
from rear_foot import (foot_case_local, rubber_case_local, floor_transform,
                       assembled_parts, pad_plane_point, PAD_DIAMETER,
                       POCKET_DIAMETER, POCKET_DEPTH, FOOT_RADIUS)


class RearFeetFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foot = foot_case_local()
        cls.pad = rubber_case_local()

    def test_one_closed_foot_and_pad_size(self):
        self.assertTrue(self.foot.is_valid)
        self.assertEqual(len(self.foot.solids()), 1)
        self.assertGreater(self.foot.volume, 0)
        bb = self.foot.bounding_box()
        self.assertAlmostEqual(bb.size.X, FOOT_RADIUS * 2, places=5)
        self.assertAlmostEqual(POCKET_DIAMETER - PAD_DIAMETER, 0.3, places=5)

    def test_pad_pocket_is_open_with_material_behind_the_seat(self):
        self.assertFalse(self.foot.is_inside(pad_plane_point(-0.2)))
        self.assertTrue(self.foot.is_inside(pad_plane_point(0.2)))
        overlap = self.foot & self.pad
        self.assertLess(abs(overlap.volume) if overlap is not None else 0, 1e-5)

    def test_seat_depth_is_measured_normal_to_sloped_face(self):
        floor = pad_plane_point(0)
        rim = pad_plane_point(-POCKET_DEPTH)
        self.assertAlmostEqual((floor - rim).length, 0.4, places=5)

    def test_contacts_and_screw_clearances_in_assembled_pose(self):
        report = assembled_parts(check=True)[1]
        self.assertFalse(report['collisions'])
        self.assertAlmostEqual(report['differential_height_mm'], 6.0, places=5)
        for height in report['support_min_z_mm']:
            self.assertAlmostEqual(height, 0, places=4)
        self.assertGreater(report['screw_head_min_clearance_mm'], 0.4)
        self.assertGreater(report['screw_head_floor_min_clearance_mm'], 0.4)


if __name__ == '__main__':
    unittest.main()
