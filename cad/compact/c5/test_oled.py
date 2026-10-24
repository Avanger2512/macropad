"""Complete OLED fit regressions using measured full envelope and stack."""
import unittest
from build123d import Pos, Vector
from compact_model import top_shell, reference_parts, oled_centers, OLED_BOTTOM, box
from layout import OLED, HEIGHT, OLED_GLASS_HEIGHT, OLED_PCB_THICKNESS, SCREWS, COVER


class FullOledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = top_shell()
        cls.parts = reference_parts()
        cls.glass = next(p for p in cls.parts if p.label.startswith('REFERENCE full OLED'))
        cls.pcb = next(p for p in cls.parts if p.label.startswith('REFERENCE OLED PCB'))

    def test_five_mm_insert_depth(self):
        for x,y in SCREWS:
            self.assertFalse(self.shell.is_inside(Vector(x,y,COVER+5.49)))
            self.assertTrue(self.shell.is_inside(Vector(x,y,COVER+5.51)))

    def test_connected(self):
        self.assertTrue(self.shell.is_valid)
        self.assertEqual(len(self.shell.solids()), 1)

    def test_measured_envelope_flush(self):
        b = self.glass.bounding_box()
        self.assertAlmostEqual(b.size.X, 34.5)
        self.assertAlmostEqual(b.size.Y, 23)
        self.assertAlmostEqual(b.min.Y - OLED.y, 6)
        self.assertAlmostEqual(OLED.front - b.max.Y, 4.6)
        self.assertAlmostEqual(b.max.Z, HEIGHT)
        self.assertAlmostEqual(b.size.Z, 2)

    def test_glass_and_pcb_clear(self):
        for part in (self.glass, self.pcb):
            common = self.shell & part
            self.assertLess(abs(common.volume) if common else 0, 1e-6)

    def test_entire_insertion_path_clear(self):
        for dz in (0, -0.5, -1, -2, -4, -8):
            common = self.shell & (Pos(0,0,dz)*self.glass)
            self.assertLess(abs(common.volume) if common else 0, 1e-6)

    def test_nominal_window_throat(self):
        tool = box(65.55,38.0,16.8,34.9,23.4,2.01)
        common = self.shell & tool
        self.assertLess(abs(common.volume) if common else 0, 1e-6)

if __name__ == '__main__':
    unittest.main()
