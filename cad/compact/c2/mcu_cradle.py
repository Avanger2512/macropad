"""Separate provisional ESP32 seat, allowing the shell to print face-down."""

from compact_model import mcu_cradle


def gen_step():
    return mcu_cradle()
