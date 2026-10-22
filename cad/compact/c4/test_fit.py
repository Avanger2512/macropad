"""Physical-fit regression targets for the revised enclosure B-rep."""
import unittest
from build123d import Vector
from compact_model import top_shell, bottom_cover, oled_centers, OLED_BOTTOM, OLED_THICKNESS
from layout import KEY_CENTERS, HEIGHT, SWITCH_SEAT, COVER, OLED


class PrintedFitRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top = top_shell()
        cls.bottom = bottom_cover()

    def inside(self, x, y, z):
        return self.top.is_inside(Vector(x, y, z))

    def test_switch_throat_tightened_without_thickening_clip_seat(self):
        for x, y in KEY_CENTERS:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.assertFalse(self.inside(x + 6.98 * dx, y + 6.98 * dy, HEIGHT - 0.5))
                self.assertTrue(self.inside(x + 7.025 * dx, y + 7.025 * dy, HEIGHT - 0.5))
                self.assertFalse(self.inside(x + 7.025 * dx, y + 7.025 * dy,
                                             HEIGHT - SWITCH_SEAT - 0.05))
                self.assertTrue(self.inside(x + 7.025 * dx, y + 7.025 * dy,
                                            HEIGHT - SWITCH_SEAT + 0.05))

    def test_oled_is_supported_from_top_with_downward_pins(self):
        pcb_top = OLED_BOTTOM + OLED_THICKNESS
        for x, y in oled_centers():
            self.assertTrue(self.inside(x, y, OLED_BOTTOM - 0.2))
            self.assertTrue(self.inside(x + 1.5, y, pcb_top + 0.05))
            self.assertFalse(self.inside(x + 1.5, y, pcb_top - 0.05))
            self.assertFalse(self.inside(x, y, OLED_BOTTOM - 0.5))

    def test_shifted_glass_has_room_at_previously_blocked_edge(self):
        # Measured18.2 glass, 6/9 margin asymmetry: centerY47.5, edge38.4.
        self.assertFalse(self.inside(83, 38.4, 18.0))
        self.assertFalse(self.inside(83, 56.6, 18.0))
        self.assertTrue(self.inside(83, 37.95, 18.0))
        self.assertTrue(self.inside(83, 57.05, 18.0))

    def test_esp_slots_reach_both_ends_and_have_15mm_row_spacing(self):
        for x in (12.5, 27.5):
            for y in (2.9, 23.6):
                self.assertFalse(self.inside(x, y, 18.0))
            self.assertTrue(self.inside(x, 2.8, 18.0))
            self.assertTrue(self.inside(x, 23.7, 18.0))
            self.assertTrue(self.inside(x - 0.95, 13.25, 18.0))
            self.assertTrue(self.inside(x + 0.95, 13.25, 18.0))

    def test_bottom_is_flat_without_old_oled_columns(self):
        self.assertAlmostEqual(self.bottom.bounding_box().max.Z, COVER, places=5)
        self.assertEqual(len(self.bottom.solids()), 1)


if __name__ == '__main__':
    unittest.main()
