"""Validate actual B-reps against concept datums and explicit reference solids."""

import json
from pathlib import Path

from compact_model import (bottom_cover, mcu_cradle, mcu_strap, mx_coupon,
                           oled_centers, oled_cradle, reference_parts, top_shell)
from layout import (COVER, DEPTH, HEIGHT, WIDTH, OLED_HOLE_DIAMETER,
                    OLED_HOLE_PITCH, OLED_PIN_DIAMETER)


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
    top, base, strap, coupon = top_shell(), bottom_cover(), mcu_strap(), mx_coupon()
    oled_frame, mcu_frame = oled_cradle(), mcu_cradle()
    refs = reference_parts()
    facts = {name: check_single(shape, name) for name, shape in
             [('shell', top), ('cover', base), ('mcu_strap', strap), ('coupon', coupon),
              ('oled_cradle', oled_frame), ('mcu_cradle', mcu_frame)]}
    expected = {'shell': [WIDTH, DEPTH, HEIGHT - COVER],
                'cover': [WIDTH, DEPTH, COVER], 'coupon': [44, 25, 1.5]}
    for name, bbox in expected.items():
        if any(abs(a - b) > 1e-4 for a, b in zip(facts[name]['bbox_mm'], bbox)):
            raise ValueError(f'Unexpected dimensions for {name}: {facts[name]}')
    collisions = []
    comparisons = 0
    functional_parts = [('shell', top), ('cover', base), ('strap', strap),
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
    report = {'revision': 'C1 concept', 'fusion_mcp_validated': False,
              'parts': facts, 'reference_count': len(refs),
              'intersection_checks': comparisons, 'collisions': collisions,
              'assumed_mx_solder_tip_to_cover_mm': HEIGHT - 11.5 - COVER,
              'nominal_shell_height_mm': HEIGHT,
              'oled_mount': {'hole_pitch_mm': OLED_HOLE_PITCH,
                             'hole_diameter_mm': OLED_HOLE_DIAMETER,
                             'pin_diameter_mm': OLED_PIN_DIAMETER,
                             'diametral_clearance_mm': OLED_HOLE_DIAMETER - OLED_PIN_DIAMETER,
                             'centers_xy_mm': oled_centers(),
                             'centered_on_pcb_assumed': True},
              'limits': ['OLED pattern centered on PCB assumed; edge retention not finalized',
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
