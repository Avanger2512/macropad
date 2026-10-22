"""C4 enclosure and explicit, simplified hardware envelopes.

No old Fusion file is modified. Integral downward pins use measured31x28pattern.
Every placement uses the rear-left enclosure datum from layout.py.
"""

from build123d import (Align, Axis, Box, Color, Compound, Cone, Cylinder, Pos,
                      RectangleRounded, chamfer, extrude)

from layout import (COVER, DEPTH, ENABLE_OLED_PINS, ENCODER, ENCODER_AXIS,
                    ENCODER_HOLE, HEIGHT, KEY_CENTERS, KEYCAP, MCU, OLED,
                    OLED_HOLE_DIAMETER, OLED_HOLE_PITCH, OLED_PIN_DIAMETER,
                    OLED_PIN_LEAD_HEIGHT,
                    OLED_PCB_THICKNESS, OLED_GLASS_HEIGHT, OLED_GLASS_WIDTH,
                    OLED_GLASS_DEPTH, OLED_GLASS_RECESS, OLED_WINDOW_CLEARANCE,
                    OLED_ROOF_CLEARANCE, OLED_CRADLE_THICKNESS, OLED_PIN_PROJECTION,
                    OLED_SUPPORT_RADIUS, OLED_SUPPORT_KEY_RADIUS,
                    OLED_SUPPORT_KEY_HEIGHT, OLED_SUPPORT_POCKET_RADIUS,
                    OLED_SUPPORT_POCKET_DEPTH,
                    ROOF, SCREWS, SWITCH_HOLE, SWITCH_SEAT, WALL, WIDTH,
                    MCU_PIN_ROW_SPACING, MCU_PIN_ROW_LENGTH, MCU_SLOT_WIDTH,
                    MCU_SLOT_END_CLEARANCE, MCU_SLOT_CENTER_Y,
                    OLED_GLASS_OFFSET_Y, OLED_WINDOW_DEPTH, OLED_MOUNT_RADIUS,
                    OLED_MOUNT_OVERLAP, OLED_PIN_PROTRUSION_BELOW_PCB)

SHELL_COLOR = (0.43, 0.45, 0.47)
CAP_COLOR = (0.83, 0.84, 0.82)
BOARD_COLOR = (0.10, 0.32, 0.28)
GLASS_COLOR = (0.07, 0.10, 0.13)
METAL_COLOR = (0.68, 0.69, 0.70)
OLED_BOTTOM = HEIGHT - OLED_GLASS_RECESS - OLED_GLASS_HEIGHT - OLED_PCB_THICKNESS
OLED_THICKNESS = OLED_PCB_THICKNESS
OLED_FRAME_BOTTOM = OLED_BOTTOM - OLED_CRADLE_THICKNESS
MCU_BOTTOM = HEIGHT
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
    # Only the glass window is visible; the whole OLED PCB remains underneath.
    wx = OLED.x + (OLED.width - OLED_GLASS_WIDTH) / 2 - OLED_WINDOW_CLEARANCE
    wy = OLED.y + OLED.depth / 2 + OLED_GLASS_OFFSET_Y - OLED_WINDOW_DEPTH / 2
    ww = OLED_GLASS_WIDTH + 2 * OLED_WINDOW_CLEARANCE
    wd = OLED_WINDOW_DEPTH
    shell = shell - box(wx, wy, HEIGHT - ROOF - 0.1, ww, wd, ROOF + 0.2)
    # A shallow underside PCB relief leaves 0.2 mm clearance above its edges.
    shell = shell - box(OLED.x - 0.2, OLED.y - 0.2, HEIGHT - ROOF - 0.1,
                        OLED.width + 0.4, OLED.depth + 0.4,
                        OLED_BOTTOM + OLED_THICKNESS + OLED_ROOF_CLEARANCE
                        - (HEIGHT - ROOF - 0.1))
    window_edges = [e for e in shell.edges().filter_by_position(Axis.Z, HEIGHT, HEIGHT)
                    if wx - 0.01 <= e.center().X <= wx + ww + 0.01
                    and wy - 0.01 <= e.center().Y <= wy + wd + 0.01]
    shell = chamfer(window_edges, length=0.3)
    # Bare PCB rests directly on the roof; only two pin slots penetrate it.
    # Adhesive is applied from inside after installing the board (user assembly).
    slot_length = MCU_PIN_ROW_LENGTH + 2 * MCU_SLOT_END_CLEARANCE
    for px in mcu_pin_row_centers():
        shell = shell - box(px - MCU_SLOT_WIDTH / 2,
                            MCU_SLOT_CENTER_Y - slot_length / 2,
                            HEIGHT - ROOF - 0.1, MCU_SLOT_WIDTH,
                            slot_length, ROOF + 0.2)
    # PCB slides upward from inside onto the downward pins. Collars stop at
    # the PCB's upper face; adhesive is applied at the exposed underside.
    pcb_top = OLED_BOTTOM + OLED_THICKNESS
    roof_relief_z = pcb_top + OLED_ROOF_CLEARANCE
    pin_tip_z = OLED_BOTTOM - OLED_PIN_PROTRUSION_BELOW_PCB
    for x, y in oled_centers():
        collar = cylinder(x, y, pcb_top, OLED_MOUNT_RADIUS,
                          roof_relief_z + OLED_MOUNT_OVERLAP - pcb_top)
        shaft = cylinder(x, y, pin_tip_z + OLED_PIN_LEAD_HEIGHT,
                         OLED_PIN_DIAMETER / 2,
                         pcb_top + 0.1 - pin_tip_z - OLED_PIN_LEAD_HEIGHT)
        lead = Pos(x, y, pin_tip_z) * Cone(
            OLED_PIN_DIAMETER / 2 - 0.3, OLED_PIN_DIAMETER / 2,
            OLED_PIN_LEAD_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
        shell = shell + collar + shaft + lead
    for x, y in SCREWS:
        shell = shell + cylinder(x, y, COVER, 3, HEIGHT - ROOF - COVER + 0.1)
        shell = shell - cylinder(x, y, COVER - 0.1, 1.6, 4.6)
    return finish(shell, 'C4 top shell - integral OLED glue pins', SHELL_COLOR)


def bottom_cover():
    cover = rounded(0, 0, 0, WIDTH, DEPTH, COVER, 4)
    bottom_edges = cover.edges().filter_by_position(Axis.Z, 0, 0)
    cover = chamfer(bottom_edges, length=0.4)
    for x, y in SCREWS:
        cover = cover - cylinder(x, y, -0.1, 1.2, COVER + 0.2)
    return finish(cover, 'C4 removable lower cover - M2 clearance', SHELL_COLOR)


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
    parts.append(finish(box(OLED.x + (OLED.width - OLED_GLASS_WIDTH) / 2,
                            OLED.y + (OLED.depth - OLED_GLASS_DEPTH) / 2 + OLED_GLASS_OFFSET_Y,
                            OLED_BOTTOM + OLED_THICKNESS,
                            OLED_GLASS_WIDTH, OLED_GLASS_DEPTH, OLED_GLASS_HEIGHT),
                        'REFERENCE OLED glass - short edge18.2 offset-1.5 from measured margin asymmetry', GLASS_COLOR))
    parts.append(finish(box(MCU.x, MCU.y, MCU_BOTTOM, MCU.width, MCU.depth, 1.6),
                        'REFERENCE ESP32-S3 SuperMini - provisional outline', BOARD_COLOR))
    parts.append(finish(box(MCU.x + 7, MCU.y + 7, MCU_BOTTOM + 1.6, 10, 10, 2.5),
                        'REFERENCE ESP32 components - provisional', GLASS_COLOR))
    parts.append(finish(box(MCU.x + 7.5, MCU.y - 1, MCU_BOTTOM + 1.6, 9, 6, 3.2),
                        'REFERENCE USB connector - provisional', METAL_COLOR))
    for px in mcu_pin_row_centers():
        parts.append(finish(box(px - 0.3, MCU_SLOT_CENTER_Y - MCU_PIN_ROW_LENGTH / 2,
                                MCU_BOTTOM - 5, 0.6, MCU_PIN_ROW_LENGTH, 5),
                            'REFERENCE MCU downward pins - measured row spacing15 length20.5', METAL_COLOR))
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


def mx_coupon():
    """Three apertures, left-to-right13.9/14.0/14.1, same clip relief as case."""
    coupon = rounded(0, 0, 0, 66, 24, ROOF, 2)
    for index, hole in enumerate((13.9, 14.0, 14.1)):
        x, y = 12 + 21 * index, 12
        coupon = coupon - box(x - hole / 2, y - hole / 2, -0.1,
                              hole, hole, ROOF + 0.2)
        coupon = coupon - box(x - 8.3, y - 8.3, -0.1,
                              16.6, 16.6, ROOF - SWITCH_SEAT + 0.1)
        # One/two/three shallow edge notches identify the sample.
        for mark in range(index + 1):
            coupon = coupon - cylinder(x + (mark - index / 2) * 2, 0,
                                        -0.1, 0.5, ROOF + 0.2)
    return finish(coupon, 'C4 MX fit sample - 1mark13.9 2marks14.0 3marks14.1', SHELL_COLOR)


def mcu_pin_row_centers():
    center = MCU.x + MCU.width / 2
    return (center - MCU_PIN_ROW_SPACING / 2,
            center + MCU_PIN_ROW_SPACING / 2)


def gen_step():
    return Compound(children=[top_shell(), bottom_cover(),
                              *reference_parts()],
                    label='C4 compact concept - physical fit corrections - roof OLED mounts')
