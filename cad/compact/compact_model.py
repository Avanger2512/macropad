"""C1 enclosure and explicit, simplified hardware envelopes.

No old Fusion file is modified. OLED locating pins use the measured 31 x 28 pattern.
Every placement uses the rear-left enclosure datum from layout.py.
"""

from build123d import (Align, Axis, Box, Color, Compound, Cone, Cylinder, Pos,
                      RectangleRounded, chamfer, extrude)

from layout import (COVER, DEPTH, ENABLE_OLED_PINS, ENCODER, ENCODER_AXIS,
                    ENCODER_HOLE, HEIGHT, KEY_CENTERS, KEYCAP, MCU, OLED,
                    OLED_HOLE_DIAMETER, OLED_HOLE_PITCH, OLED_PIN_DIAMETER,
                    OLED_PIN_LEAD_HEIGHT,
                    ROOF, SCREWS, SWITCH_HOLE, SWITCH_SEAT, WALL, WIDTH)

SHELL_COLOR = (0.43, 0.45, 0.47)
CAP_COLOR = (0.83, 0.84, 0.82)
BOARD_COLOR = (0.10, 0.32, 0.28)
GLASS_COLOR = (0.07, 0.10, 0.13)
METAL_COLOR = (0.68, 0.69, 0.70)
OLED_BOTTOM = HEIGHT + 0.8
OLED_THICKNESS = 1.6
MCU_BOTTOM = HEIGHT + 0.8
ENCODER_BOARD_BOTTOM = HEIGHT - ROOF - 9.5


def box(x, y, z, width, depth, height):
    return Pos(x, y, z) * Box(width, depth, height, align=(Align.MIN,) * 3)


def cylinder(x, y, z, radius, height):
    return Pos(x, y, z) * Cylinder(radius, height,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN))


def rounded(x, y, z, width, depth, height, radius):
    return Pos(x + width / 2, y + depth / 2, z) * extrude(
        RectangleRounded(width, depth, radius), amount=height)


def finish(shape, label, color):
    shape.label = label
    shape.color = Color(*color)
    return shape


def oled_centers():
    dx, dy = OLED_HOLE_PITCH
    cx, cy = OLED.x + OLED.width / 2, OLED.y + OLED.depth / 2
    return tuple((cx + sx * dx / 2, cy + sy * dy / 2)
                 for sx in (-1, 1) for sy in (-1, 1))


def top_shell():
    outer = rounded(0, 0, COVER, WIDTH, DEPTH, HEIGHT - COVER, 4)
    # Apply the cosmetic edge before any functional hole exists.
    top_edges = outer.edges().filter_by_position(Axis.Z, HEIGHT, HEIGHT)
    outer = chamfer(top_edges, length=0.6)
    inner = rounded(WALL, WALL, COVER - 0.1,
                    WIDTH - 2 * WALL, DEPTH - 2 * WALL,
                    HEIGHT - ROOF - COVER + 0.1, 2)
    shell = outer - inner
    for x, y in KEY_CENTERS:
        shell = shell - box(x - SWITCH_HOLE / 2, y - SWITCH_HOLE / 2,
                            HEIGHT - ROOF - 0.1,
                            SWITCH_HOLE, SWITCH_HOLE, ROOF + 0.2)
        # Relief leaves exactly 1.5 mm around each switch's clip plane.
        shell = shell - box(x - 8.3, y - 8.3, HEIGHT - ROOF - 0.1,
                            16.6, 16.6, ROOF - SWITCH_SEAT + 0.1)
    ex, ey = ENCODER_AXIS
    shell = shell - cylinder(ex, ey, HEIGHT - ROOF - 0.1,
                              ENCODER_HOLE / 2, ROOF + 0.2)
    # Central wire access; the PCB sits on four supported perimeter pads.
    shell = shell - box(OLED.x + 4, OLED.y + 4, HEIGHT - ROOF - 0.1,
                        OLED.width - 8, OLED.depth - 8, ROOF + 0.2)
    # Separate flat-print cradles sit in 0.4 mm shallow locating pockets.
    for pcb in (OLED, MCU):
        shell = shell - box(pcb.x - 0.2, pcb.y - 0.2, HEIGHT - 0.4,
                            pcb.width + 0.4, pcb.depth + 0.4, 0.5)
    # Two long open slots allow short header pins or directly soldered wires.
    for px in (MCU.x + 0.4, MCU.right - 2.2):
        shell = shell - box(px, MCU.y + 2, HEIGHT - ROOF - 0.1,
                            1.8, MCU.depth - 4, ROOF + 0.2)
    # Underside electronics clearance, open only between support rails.
    shell = shell - box(MCU.x + 4, MCU.y + 4, HEIGHT - ROOF - 0.1,
                        MCU.width - 8, MCU.depth - 8, ROOF + 0.2)
    # Open rear USB throat, extending to the exposed board connector.
    shell = shell - box(MCU.x + 5, -0.1, HEIGHT - 0.5, 14, 5.2, 3)
    for x, y in SCREWS:
        shell = shell + cylinder(x, y, COVER, 3, HEIGHT - ROOF - COVER + 0.1)
        shell = shell - cylinder(x, y, COVER - 0.1, 1.6, 4.6)
    # M2 heat-set bosses below the roof, keeping the exterior print face flat.
    for px in (MCU.x + 3, MCU.right - 3):
        shell = shell + cylinder(px, MCU.front + 3, HEIGHT - ROOF - 4.5, 3.25, 4.6)
        shell = shell - cylinder(px, MCU.front + 3, HEIGHT - 4.5, 1.6, 4.6)
    return finish(shell, 'C1 top shell - provisional electronics seats', SHELL_COLOR)


def bottom_cover():
    cover = rounded(0, 0, 0, WIDTH, DEPTH, COVER, 4)
    bottom_edges = cover.edges().filter_by_position(Axis.Z, 0, 0)
    cover = chamfer(bottom_edges, length=0.4)
    for x, y in SCREWS:
        cover = cover - cylinder(x, y, -0.1, 1.2, COVER + 0.2)
    return finish(cover, 'C1 removable lower cover - M2 clearance', SHELL_COLOR)


def reference_parts():
    parts = []
    for i, (x, y) in enumerate(KEY_CENTERS, 1):
        body = box(x - 7, y - 7, HEIGHT - 8.5, 14, 14, 8.5)
        body = body + box(x - 7.75, y - 7.75, HEIGHT, 15.5, 15.5, 1)
        body = body + box(x - 2.5, y - 2.5, HEIGHT + 0.9, 5, 5, 4.3)
        parts.append(finish(body, f'REFERENCE MX {i} - assumed depth', GLASS_COLOR))
        parts.append(finish(box(x - KEYCAP / 2, y - KEYCAP / 2,
                                HEIGHT + 5.2, KEYCAP, KEYCAP, 7),
                            f'REFERENCE cap {i} - 18 mm measured footprint', CAP_COLOR))
        # Conservative individual pin/wire envelope, not actual contact geometry.
        for dx in (-3, 3):
            parts.append(finish(cylinder(x + dx, y, HEIGHT - 11.5, 0.6, 3),
                                f'REFERENCE switch {i} solder pin', METAL_COLOR))
    pcb = box(OLED.x, OLED.y, OLED_BOTTOM, OLED.width, OLED.depth, OLED_THICKNESS)
    if ENABLE_OLED_PINS:
        for x, y in oled_centers():
            pcb = pcb - cylinder(x, y, OLED_BOTTOM - 0.1,
                                  OLED_HOLE_DIAMETER / 2, OLED_THICKNESS + 0.2)
    parts.append(finish(pcb, 'REFERENCE OLED PCB - measured holes 31x28 diameter 2.5', BOARD_COLOR))
    parts.append(finish(box(OLED.x + 0.75, OLED.y + 7.75,
                            OLED_BOTTOM + OLED_THICKNESS, 34.5, 18.5, 2.4),
                        'REFERENCE OLED glass - offset provisional', GLASS_COLOR))
    parts.append(finish(box(MCU.x, MCU.y, MCU_BOTTOM, MCU.width, MCU.depth, 1.6),
                        'REFERENCE ESP32-S3 SuperMini - provisional outline', BOARD_COLOR))
    parts.append(finish(box(MCU.x + 7, MCU.y + 7, MCU_BOTTOM + 1.6, 10, 10, 2.5),
                        'REFERENCE ESP32 components - provisional', GLASS_COLOR))
    parts.append(finish(box(MCU.x + 7.5, MCU.y - 1, MCU_BOTTOM + 1.6, 9, 6, 3.2),
                        'REFERENCE USB connector - provisional', METAL_COLOR))
    for px in (MCU.x + 1.3, MCU.right - 1.3):
        parts.append(finish(box(px - 0.3, MCU.y + 2, MCU_BOTTOM - 5, 0.6, 16, 5),
                            'REFERENCE MCU downward pins - provisional', METAL_COLOR))
    ex, ey = ENCODER_AXIS
    parts.append(finish(box(ENCODER.x, ENCODER.y, ENCODER_BOARD_BOTTOM,
                            ENCODER.width, ENCODER.depth, 1.6),
                        'REFERENCE KY040 PCB - centered axis provisional', BOARD_COLOR))
    parts.append(finish(box(ex - 6, ey - 6, ENCODER_BOARD_BOTTOM + 1.6,
                            12, 12, 7.9), 'REFERENCE encoder body - assumed', METAL_COLOR))
    parts.append(finish(cylinder(ex, ey, HEIGHT - ROOF, 3.5, 7),
                        'REFERENCE measured encoder bushing diameter 7 length 7', METAL_COLOR))
    parts.append(finish(cylinder(ex, ey, HEIGHT - ROOF + 7, 3, 2.6),
                        'REFERENCE encoder shaft - provisional', METAL_COLOR))
    parts.append(finish(cylinder(ex, ey, HEIGHT + 5, 10,
                                 ENCODER_BOARD_BOTTOM + 29 - HEIGHT - 5),
                        'REFERENCE encoder knob - diameter provisional', GLASS_COLOR))
    for x, y in ((11, 9), (95, 9), (11, 66), (95, 66)):
        parts.append(finish(cylinder(x, y, -2.8, 4, 2.8),
                            'REFERENCE rubber foot - effective height 2.8', GLASS_COLOR))
    return tuple(parts)


def mcu_strap():
    # The toe overlaps the front 1 mm of the assumed PCB edge. Verify components.
    strap = box(MCU.x + 0.5, MCU.front - 1, MCU_BOTTOM + 1.85,
                MCU.width - 1, 6.5, 1.6)
    for px in (MCU.x + 3, MCU.right - 3):
        strap = strap + box(px - 2.5, MCU.front + 0.5, HEIGHT,
                            5, 5, MCU_BOTTOM + 1.85 - HEIGHT + 0.1)
        strap = strap - cylinder(px, MCU.front + 3, HEIGHT - 0.1,
                                  1.2, MCU_BOTTOM + 3.55 - HEIGHT)
    # Stop tied into the removable legs, opposing USB insertion force.
    strap = strap + box(MCU.x + 4, MCU.front + 0.2, HEIGHT,
                        MCU.width - 8, 1.2, 2.2)
    return finish(strap, 'C1 removable MCU strap - edge clearance provisional', SHELL_COLOR)


def pcb_cradle(pcb, label, pin_slots=False):
    cradle = box(pcb.x, pcb.y, HEIGHT - 0.4, pcb.width, pcb.depth, 1.2)
    cradle = cradle - box(pcb.x + 4, pcb.y + 4, HEIGHT - 0.5,
                          pcb.width - 8, pcb.depth - 8, 1.4)
    if pin_slots:
        # Open notches remove fragile 0.4 mm exterior webs. The remaining
        # interior side rails are 1.8 mm wide, joined by the end rails.
        for px in (pcb.x - 0.1, pcb.right - 2.2):
            cradle = cradle - box(px, pcb.y + 2, HEIGHT - 0.5,
                                  2.3, pcb.depth - 4, 1.4)
    elif ENABLE_OLED_PINS:
        for x, y in oled_centers():
            shaft_height = OLED_THICKNESS + 0.8 - OLED_PIN_LEAD_HEIGHT
            shaft = cylinder(x, y, OLED_BOTTOM - 0.1,
                             OLED_PIN_DIAMETER / 2, shaft_height)
            lead = Pos(x, y, OLED_BOTTOM - 0.1 + shaft_height) * Cone(
                OLED_PIN_DIAMETER / 2, OLED_PIN_DIAMETER / 2 - 0.3,
                OLED_PIN_LEAD_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
            cradle = cradle + shaft + lead
    return finish(cradle, label, SHELL_COLOR)


def oled_cradle():
    return pcb_cradle(OLED, 'C1 OLED cradle - 31x28 locating pins diameter 2.2')


def mcu_cradle():
    return pcb_cradle(MCU, 'C1 replaceable MCU cradle - provisional', pin_slots=True)


def mx_coupon():
    coupon = rounded(0, 0, 0, 44, 25, SWITCH_SEAT, 2)
    for x, hole in ((12, 14.1), (32, 14.2)):
        coupon = coupon - box(x - hole / 2, 12.5 - hole / 2, -0.1,
                              hole, hole, SWITCH_SEAT + 0.2)
    # Small edge notch identifies the 14.1 mm opening after rotating the print.
    coupon = coupon - cylinder(12, 0, -0.1, 0.9, SWITCH_SEAT + 0.2)
    return finish(coupon, 'MX fit coupon - left 14.1 right 14.2 seat 1.5', SHELL_COLOR)


def gen_step():
    return Compound(children=[top_shell(), bottom_cover(), mcu_strap(),
                              oled_cradle(), mcu_cradle(), *reference_parts()],
                    label='C1 compact concept - hardware envelopes NOT fit validated')
