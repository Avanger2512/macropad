"""C4 retention sample, flat roof face on bed and clip relief upward."""
from build123d import Pos, Rot
from compact_model import mx_coupon
from layout import ROOF

def gen_step():
    return Pos(0, 24, ROOF) * Rot(180, 0, 0) * mx_coupon()
