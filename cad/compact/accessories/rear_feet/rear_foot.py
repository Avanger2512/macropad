"""Four-pad retrofit: source datums follow C4; standalone output is print posed.

All dimensions mm. +Y points toward the front of the case. The mating plane
is Z0; assembled feet extend below it. Both feet types are thicker toward USB.
"""
from math import atan, cos, degrees, sin, tan
from pathlib import Path
from build123d import (Align, Axis, Color, Compound, Cylinder, Plane, Polygon,
                      Pos, Rot, Vector, chamfer, extrude, import_step)

PAD_DIAMETER = 10.0
PAD_THICKNESS = 2.0
POCKET_DIAMETER = 10.3
POCKET_DEPTH = 0.4
FOOT_RADIUS = 7.0
EDGE_CHAMFER = 0.25
FRONT_STACK = 3.2  # above Ø4 x2 screw heads even when tilted
REAR_RISE = 6.0
REAR_STACK = FRONT_STACK + REAR_RISE
REAR_Y = 10.0
FRONT_Y = 66.0
FOOT_X = (12.0, 94.0)
ANGLE = atan(REAR_RISE / (FRONT_Y - REAR_Y))
ANGLE_DEG = degrees(ANGLE)
C4 = Path(__file__).resolve().parents[2] / 'c4'
SCREWS = ((3.5, 3.5), (102.5, 3.5), (3.5, 70.5), (102.5, 70.5))


def stack(front=False):
    return FRONT_STACK if front else REAR_STACK


def seat_z(front=False):
    return -stack(front) + PAD_THICKNESS / cos(ANGLE)


def body_height(front=False):
    return stack(front) - (PAD_THICKNESS - POCKET_DEPTH) / cos(ANGLE)


def pad_plane_point(offset=0.0, front=False):
    return Vector(0, 0, seat_z(front)) + Vector(0, -sin(ANGLE), cos(ANGLE)) * offset


def foot_case_local(front=False):
    h, r, k = body_height(front), FOOT_RADIUS, tan(ANGLE)
    blank = Pos(0, 0, -h - r * k) * Cylinder(r, h + r * k,
                                            align=(Align.CENTER, Align.CENTER, Align.MIN))
    section = Plane.YZ * Polygon((-r, -h - r * k), (r, -h + r * k),
                                 (r, 0), (-r, 0), align=None)
    wedge = Pos(-r - 1, 0, 0) * extrude(section, amount=2 * r + 2)
    body = blank & wedge
    top = body.edges().filter_by_position(Axis.Z, 0, 0)
    body = chamfer(top, length=EDGE_CHAMFER)
    pocket = Pos(0, 0, seat_z(front)) * Rot(ANGLE_DEG, 0, 0) * Cylinder(
        POCKET_DIAMETER / 2, PAD_THICKNESS + 1,
        align=(Align.CENTER, Align.CENTER, Align.MAX))
    body = body - pocket
    body.label = ('Front low' if front else 'Rear raised') + ' wedge foot - adhesive mount D10 pad'
    body.color = Color(0.43, 0.45, 0.47)
    return body


def rubber_case_local(front=False):
    pad = Pos(0, 0, seat_z(front)) * Rot(ANGLE_DEG, 0, 0) * Cylinder(
        PAD_DIAMETER / 2, PAD_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MAX))
    pad.label = 'REFERENCE rubber pad - user measured D10 x2'
    pad.color = Color(0.08, 0.09, 0.10)
    return pad


def floor_transform(shape):
    elevation = sin(ANGLE) * FRONT_Y + cos(ANGLE) * FRONT_STACK
    return Pos(0, 0, elevation) * Rot(-ANGLE_DEG, 0, 0) * shape


def print_foot(front=False):
    return Pos(FOOT_RADIUS, FOOT_RADIUS, 0) * Rot(180, 0, 0) * foot_case_local(front)


def common_volume(a, b):
    result = a & b
    return abs(result.volume) if result is not None else 0.0


def assembled_parts(check=False):
    case = []
    for stem in ('top_shell', 'bottom_cover'):
        shape = import_step(C4 / (stem + '.step'))
        shape.label = 'REFERENCE existing C4 ' + stem
        shape.color = Color(0.43, 0.45, 0.47)
        case.append(shape)
    feet, pads = [], []
    for front, y in ((False, REAR_Y), (True, FRONT_Y)):
        for x in FOOT_X:
            foot = Pos(x, y, 0) * foot_case_local(front)
            foot.label += ' left' if x < 50 else ' right'
            feet.append(foot)
            pads.append(Pos(x, y, 0) * rubber_case_local(front))
    heads = []
    for x, y in SCREWS:
        head = Pos(x, y, 0) * Cylinder(2, 2, align=(Align.CENTER, Align.CENTER, Align.MAX))
        head.label = 'REFERENCE existing screw head D4 x2'
        head.color = Color(0.60, 0.62, 0.64)
        heads.append(head)
    pairs = [*case, *feet, *pads, *heads]
    collisions = []
    comparisons = 0
    if check:
        for i, a in enumerate(pairs):
            for b in pairs[i + 1:]:
                comparisons += 1
                volume = common_volume(a, b)
                if volume > 1e-5:
                    collisions.append({'a': a.label, 'b': b.label, 'volume_mm3': volume})
    world = [floor_transform(s) for s in pairs]
    support_z = [floor_transform(p).bounding_box().min.Z for p in pads]
    clearances = [foot.distance_to(head) for foot in feet for head in heads]
    report = {'angle_deg': ANGLE_DEG, 'differential_height_mm': REAR_RISE,
              'front_stack_mm': FRONT_STACK, 'rear_stack_mm': REAR_STACK,
              'support_min_z_mm': support_z,
              'screw_head_min_clearance_mm': min(clearances),
              'screw_head_floor_min_clearance_mm': min(floor_transform(h).bounding_box().min.Z for h in heads),
              'intersection_checks': comparisons, 'collisions': collisions,
              'printed_parts': 4, 'rubber_pads': 4}
    return world, report


def gen_step():
    return print_foot()
