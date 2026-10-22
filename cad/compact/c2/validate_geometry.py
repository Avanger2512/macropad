"""Validate actual B-reps against concept datums and explicit reference solids."""

import json
from pathlib import Path

from compact_model import (bottom_cover, mcu_cradle, mx_coupon, OLED_FRAME_BOTTOM,
                           OLED_BOTTOM, OLED_THICKNESS,
                           oled_centers, oled_cradle, reference_parts, top_shell)
from layout import (COVER, DEPTH, HEIGHT, WIDTH, OLED_HOLE_DIAMETER,
                    OLED_HOLE_PITCH, OLED_PIN_DIAMETER, OLED_SUPPORT_KEY_HEIGHT,
                    OLED_GLASS_HEIGHT, OLED_GLASS_RECESS, ENCODER_AXIS, OLED)


def common_volume(a, b):
    intersection = a & b
    return abs(intersection.volume) if intersection is not None else 0.0


def check_single(shape, name):
    if not shape.is_valid or len(shape.solids()) != 1 or shape.volume <= 0:
        raise ValueError(f'{name} is not one valid positive-volume solid')
    bb = shape.bounding_box()
    return {'label': shape.label, 'solids': len(shape.solids()),
            'volume_mm3': round(shape.volume, 3),
            'bbox_mm': [round(bb.size.X, 4), round(bb.size.Y, 4), round(bb.size.Z, 4)]}


def validate():
    top, base, coupon = top_shell(), bottom_cover(), mx_coupon()
    oled_frame, mcu_frame = oled_cradle(), mcu_cradle()
    refs = reference_parts()
    facts = {name: check_single(shape, name) for name, shape in
             [('shell', top), ('cover', base), ('coupon', coupon),
              ('oled_cradle', oled_frame), ('mcu_cradle', mcu_frame)]}
    expected = {'shell': [WIDTH, DEPTH, HEIGHT - COVER],
                'cover': [WIDTH, DEPTH, OLED_FRAME_BOTTOM + OLED_SUPPORT_KEY_HEIGHT],
                'coupon': [44, 25, 1.5]}
    for name, bbox in expected.items():
        if any(abs(a - b) > 1e-4 for a, b in zip(facts[name]['bbox_mm'], bbox)):
            raise ValueError(f'Unexpected dimensions for {name}: {facts[name]}')
    collisions = []
    comparisons = 0
    functional_parts = [('shell', top), ('cover', base),
                        ('oled_cradle', oled_frame), ('mcu_cradle', mcu_frame)]
    for name, body in functional_parts:
        for ref in refs:
            comparisons += 1
            volume = common_volume(body, ref)
            if volume > 1e-5:
                collisions.append({'part': name, 'reference': ref.label,
                                   'volume_mm3': round(volume, 6)})
    for i, (name, a) in enumerate(functional_parts):
        for other, b in functional_parts[i + 1:]:
            comparisons += 1
            volume = common_volume(a, b)
            if volume > 1e-5:
                collisions.append({'part': name + '/' + other,
                                   'volume_mm3': round(volume, 6)})
    report = {'revision': 'C2 concept', 'fusion_mcp_validated': False,
              'parts': facts, 'reference_count': len(refs),
              'intersection_checks': comparisons, 'collisions': collisions,
              'assumed_mx_solder_tip_to_cover_mm': HEIGHT - 11.5 - COVER,
              'nominal_shell_height_mm': HEIGHT,
              'flush_glass': {'top_z_mm': OLED_BOTTOM + OLED_THICKNESS + OLED_GLASS_HEIGHT,
                              'shell_top_z_mm': HEIGHT,
                              'recess_mm': OLED_GLASS_RECESS},
              'encoder_axis_xy_mm': ENCODER_AXIS,
              'display_center_xy_mm': [OLED.x + OLED.width / 2, OLED.y + OLED.depth / 2],
              'upper_mcu_clamp': False,
              'oled_mount': {'hole_pitch_mm': OLED_HOLE_PITCH,
                             'hole_diameter_mm': OLED_HOLE_DIAMETER,
                             'pin_diameter_mm': OLED_PIN_DIAMETER,
                             'diametral_clearance_mm': OLED_HOLE_DIAMETER - OLED_PIN_DIAMETER,
                             'centers_xy_mm': oled_centers(),
                             'centered_on_pcb_assumed': True},
              'limits': ['OLED pattern/glass centered on PCB assumed; nominal glass height 2.4 mm',
                         'OLED captured by roof and lid-supported frame; physical clearances untested',
                         'No upper MCU clamp per user request; lift retention not finalized',
                         'MCU outline, underside components, USB and antenna unmeasured',
                         'Encoder axis position and underside depth provisional',
                         'MX clips and wire bends require physical coupon/assembly',
                         'Reference solids are envelopes, not manufacturer models',
                         'No print-ready full enclosure released']}
    path = Path(__file__).with_name('validation.json')
    path.write_text(json.dumps(report, indent=2) + '\n')
    if collisions:
        raise ValueError(f'Envelope collisions: {collisions}')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    validate()
