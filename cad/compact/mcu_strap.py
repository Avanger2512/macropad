"""Removable controller clamp, printed with its broad outer face on the bed."""

from compact_model import mcu_strap


def gen_step():
    return mcu_strap()
