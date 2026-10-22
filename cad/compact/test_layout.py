"""Specification checks for the compact concept, not hardware fit tests."""

import unittest

from layout import (COVER, DEPTH, ENCODER, HEIGHT, MCU, OLED, PITCH,
                    OLED_HOLE_DIAMETER, OLED_HOLE_PITCH, OLED_PIN_DIAMETER,
                    ENABLE_OLED_PINS, ROOF, SWITCH_SEAT, WIDTH, key_rectangles, overlap)


class CompactLayoutSpec(unittest.TestCase):
    def test_six_caps_and_components_fit_without_xy_overlap(self):
        parts = (*key_rectangles(), MCU, ENCODER, OLED)
        self.assertEqual(len(key_rectangles()), 6)
        for i, part in enumerate(parts):
            self.assertGreaterEqual(part.x, 0)
            self.assertGreaterEqual(part.y, 0)
            self.assertLessEqual(part.right, WIDTH)
            self.assertLessEqual(part.front, DEPTH)
            for other in parts[i + 1:]:
                self.assertFalse(overlap(part, other))

    def test_standard_pitch_and_local_clip_seat(self):
        self.assertAlmostEqual(PITCH, 19.05)
        self.assertAlmostEqual(SWITCH_SEAT, 1.5)
        self.assertGreaterEqual(ROOF, SWITCH_SEAT)
        self.assertGreater(HEIGHT - COVER - ROOF, 10)

    def test_oled_key_gap(self):
        self.assertGreaterEqual(OLED.x - max(p.right for p in key_rectangles()), 3.5)

    def test_measured_oled_holes_and_clearance_pins(self):
        self.assertEqual(OLED_HOLE_PITCH, (31.0, 28.0))
        self.assertEqual(OLED_HOLE_DIAMETER, 2.5)
        self.assertTrue(ENABLE_OLED_PINS)
        self.assertAlmostEqual(OLED_HOLE_DIAMETER - OLED_PIN_DIAMETER, 0.3)


if __name__ == '__main__':
    unittest.main()
