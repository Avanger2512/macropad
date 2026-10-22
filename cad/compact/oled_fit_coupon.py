"""OLED frame fitting sample, grounded at Z0 for printing pins upward."""

from build123d import Pos

from compact_model import oled_cradle
from layout import HEIGHT, OLED


def gen_step():
    return Pos(-OLED.x, -OLED.y, -(HEIGHT - 0.4)) * oled_cradle()
