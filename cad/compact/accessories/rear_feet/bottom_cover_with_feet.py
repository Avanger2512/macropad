"""C4 cover with integral feet for four D10x2 pads; dimensions in mm.

Original interior and screw pattern retained. Print inner flat face on bed,
feet up. Existing support datums preserve 6 mm rear rise (6.1155 degrees).
"""
from build123d import Align, Cone, Pos, Rot, import_step
from rear_foot import C4, FOOT_X, REAR_Y, FRONT_Y, foot_case_local


REAR_BASE_CHAMFER = 1.2
FRONT_BASE_CHAMFER = 0.4  # low front feet: retain original pad pocket floor


def cover_case_local():
    cover = import_step(C4 / 'bottom_cover.step')
    for front, y in ((False, REAR_Y), (True, FRONT_Y)):
        for x in FOOT_X:
            width = FRONT_BASE_CHAMFER if front else REAR_BASE_CHAMFER
            flare = Pos(0, 0, -width) * Cone(7, 7 + width, width,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
            foot = foot_case_local(front).fuse(flare)
            cover = cover.fuse(Pos(x, y, 0) * foot)
    cover = cover.clean()
    cover.label = 'C4 lower cover with four integral D10 pad feet'
    return cover


def gen_step():
    cover = Rot(180, 0, 0) * cover_case_local()
    bounds = cover.bounding_box()
    return Pos(-bounds.min.X, -bounds.min.Y, -bounds.min.Z) * cover
