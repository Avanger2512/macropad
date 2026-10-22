"""C2 hidden OLED frame translated flat to Z0 for checking the short pins."""

from build123d import Pos

from compact_model import OLED_FRAME_BOTTOM, oled_cradle
from layout import OLED


def gen_step():
    return Pos(-OLED.x, -OLED.y, -OLED_FRAME_BOTTOM) * oled_cradle()
