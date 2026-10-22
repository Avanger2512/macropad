"""Measured and provisional compact-layout envelopes, in mm.

XY origin: rear-left corner; +Y toward the user, +Z upward.
No physical fit claim is made for the provisional electronics.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    depth: float

    @property
    def right(self):
        return self.x + self.width

    @property
    def front(self):
        return self.y + self.depth


WIDTH = 106.0
DEPTH = 74.0
HEIGHT = 18.8
WALL = 2.0
COVER = 2.4
ROOF = 2.4
PITCH = 19.05
KEYCAP = 18.0
SWITCH_HOLE = 14.1
SWITCH_SEAT = 1.5
OLED = Rect(65, 32, 36, 34)
# Controller moved rearward versus the sketch to give USB direct rear access.
MCU = Rect(8, 1, 24, 20)
ENCODER = Rect(70, 4.5, 26, 19)
ENCODER_AXIS = (83.0, 14.0)
ENCODER_HOLE = 7.4
SCREWS = ((3.5, 3.5), (102.5, 3.5), (3.5, 70.5), (102.5, 70.5))
KEY_CENTERS = tuple(
    (14 + col * PITCH, 39 + row * PITCH)
    for row in range(2) for col in range(3)
)
# User-measured 2026-10-22. Pattern centered on PCB is still an assumption.
OLED_HOLE_PITCH = (31.0, 28.0)
OLED_HOLE_DIAMETER = 2.5
OLED_PIN_DIAMETER = 2.2
OLED_PIN_LEAD_HEIGHT = 0.4
OLED_PCB_THICKNESS = 1.6
OLED_GLASS_HEIGHT = 2.4
OLED_GLASS_WIDTH = 34.5
OLED_GLASS_DEPTH = 18.5
OLED_GLASS_RECESS = 0.0
OLED_WINDOW_CLEARANCE = 0.2
OLED_ROOF_CLEARANCE = 0.2
OLED_CRADLE_THICKNESS = 1.2
OLED_PIN_PROJECTION = 0.0
OLED_SUPPORT_RADIUS = 2.2
OLED_SUPPORT_KEY_RADIUS = 1.0
OLED_SUPPORT_KEY_HEIGHT = 0.6
OLED_SUPPORT_POCKET_RADIUS = 1.15
OLED_SUPPORT_POCKET_DEPTH = 0.7
ENABLE_OLED_PINS = True


def key_rectangles():
    return tuple(Rect(x - KEYCAP / 2, y - KEYCAP / 2, KEYCAP, KEYCAP)
                 for x, y in KEY_CENTERS)


def overlap(a, b):
    return (min(a.right, b.right) > max(a.x, b.x)
            and min(a.front, b.front) > max(a.y, b.y))
