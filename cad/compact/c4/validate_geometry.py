"""C4 B-rep checks against measured features and existing component envelopes."""
import json
from pathlib import Path
from build123d import Vector, Pos, import_step
from compact_model import (top_shell, bottom_cover, reference_parts, oled_centers,
                           mx_coupon, mcu_pin_row_centers, OLED_BOTTOM, OLED_THICKNESS)
from layout import (WIDTH, DEPTH, HEIGHT, COVER, OLED, OLED_GLASS_HEIGHT,
                    OLED_GLASS_DEPTH, OLED_WINDOW_DEPTH, OLED_GLASS_OFFSET_Y,
                    MCU_PIN_ROW_SPACING, MCU_PIN_ROW_LENGTH, MCU_SLOT_CENTER_Y,
                    MCU_SLOT_END_CLEARANCE, MCU_SLOT_WIDTH)


def common_volume(a, b):
    intersection = a & b
    return abs(intersection.volume) if intersection is not None else 0.0


def single(shape):
    assert shape.is_valid and len(shape.solids()) == 1 and shape.volume > 0
    bb = shape.bounding_box()
    return {'bbox_mm': [round(v, 5) for v in (bb.size.X, bb.size.Y, bb.size.Z)],
            'volume_mm3': round(shape.volume, 5), 'solids': len(shape.solids())}


def face_aperture(body, x, y, z, axis, span):
    """Find the actual inner parallel plane coordinates intersecting this section."""
    coords = []
    for face in body.faces():
        bb = face.bounding_box()
        lo, hi = ((bb.min.X, bb.max.X) if axis == 'x' else (bb.min.Y, bb.max.Y))
        cross_lo, cross_hi = ((bb.min.Y, bb.max.Y) if axis == 'x'
                              else (bb.min.X, bb.max.X))
        cross = y if axis == 'x' else x
        target = x if axis == 'x' else y
        if (abs(hi - lo) < 1e-5 and abs(lo - target) < span
                and cross_lo - 1e-6 <= cross <= cross_hi + 1e-6
                and bb.min.Z - 1e-6 <= z <= bb.max.Z + 1e-6):
            coords.append(round(lo, 6))
    below = [c for c in coords if c < (x if axis == 'x' else y)]
    above = [c for c in coords if c > (x if axis == 'x' else y)]
    assert below and above, (axis, coords)
    return [max(below), min(above)]


def validate():
    shell, cover, coupon = top_shell(), bottom_cover(), mx_coupon()
    refs = reference_parts()
    facts = {k: single(v) for k, v in [('shell', shell), ('cover', cover), ('coupon', coupon)]}
    assert facts['shell']['bbox_mm'] == [WIDTH, DEPTH, round(HEIGHT - COVER, 5)]
    assert facts['cover']['bbox_mm'] == [WIDTH, DEPTH, COVER]
    parts = [('shell', shell), ('cover', cover)]
    collisions, count = [], 0
    for i, (name, body) in enumerate(parts):
        for other_name, other in [(r.label, r) for r in refs] + parts[i + 1:]:
            count += 1
            volume = common_volume(body, other)
            if volume > 1e-5:
                collisions.append({'a': name, 'b': other_name, 'mm3': volume})
    assert not collisions, collisions
    # The OLED assembly must be able to slide upward from below onto roof pins.
    oled_refs = [r for r in refs if r.label.startswith(('REFERENCE OLED PCB', 'REFERENCE OLED glass'))]
    insertion_checks = 0
    for delta in (-0.1, -0.4, -1.0, -2.0, -4.0, -8.0):
        for ref in oled_refs:
            insertion_checks += 1
            assert common_volume(shell, Pos(0, 0, delta) * ref) < 1e-5
    slots = []
    for x in mcu_pin_row_centers():
        xs = face_aperture(shell, x, MCU_SLOT_CENTER_Y, HEIGHT - 1, 'x', 2)
        ys = face_aperture(shell, x, MCU_SLOT_CENTER_Y, HEIGHT - 1, 'y', 12)
        assert abs((xs[1] - xs[0]) - MCU_SLOT_WIDTH) < 1e-5
        assert abs((ys[1] - ys[0]) - (MCU_PIN_ROW_LENGTH + 2 * MCU_SLOT_END_CLEARANCE)) < 1e-5
        slots.append({'center_x_mm': sum(xs) / 2, 'x_bounds_mm': xs, 'y_bounds_mm': ys})
    assert abs(slots[1]['center_x_mm'] - slots[0]['center_x_mm'] - MCU_PIN_ROW_SPACING) < 1e-5
    wx = OLED.x + OLED.width / 2
    wy = OLED.y + OLED.depth / 2 + OLED_GLASS_OFFSET_Y
    window_y = face_aperture(shell, wx, wy, HEIGHT - 0.5, 'y', 15)
    window_x = face_aperture(shell, wx, wy, HEIGHT - 0.5, 'x', 20)
    assert abs(window_y[1] - window_y[0] - OLED_WINDOW_DEPTH) < 1e-5
    # Legacy lower cover is geometrically checked, not assumed compatible.
    old_lid = import_step(Path(__file__).parents[1] / 'c3' / 'bottom_cover.step')
    old_shell = import_step(Path(__file__).parents[1] / 'c3' / 'top_shell.step')
    glass = next(r for r in refs if r.label.startswith('REFERENCE OLED glass'))
    old_glass_interference = common_volume(old_shell, glass)
    assert old_glass_interference > 1.0
    legacy = {'old_cover_new_shell_overlap_mm3': common_volume(shell, old_lid),
              'old_cover_hardware_overlap_mm3': sum(common_volume(old_lid, r) for r in refs),
              'nominal_pin_tip_to_old_key_mm': round(OLED_BOTTOM - 0.4 - old_lid.bounding_box().max.Z, 5)}
    assert legacy['old_cover_new_shell_overlap_mm3'] < 1e-5
    assert legacy['old_cover_hardware_overlap_mm3'] < 1e-5
    report = {'revision': 'C4', 'parts': facts, 'reference_count': len(refs),
              'intersection_checks': count, 'collisions': collisions,
              'oled_insertion_checks': insertion_checks,
              'oled': {'glass_depth_measured_mm': OLED_GLASS_DEPTH,
                       'window_x_bounds_mm': window_x, 'window_y_bounds_mm': window_y,
                       'glass_offset_y_mm': OLED_GLASS_OFFSET_Y,
                       'glass_top_z_mm': OLED_BOTTOM + OLED_THICKNESS + OLED_GLASS_HEIGHT,
                       'nominal_flush_z_mm': HEIGHT, 'hole_centers_xy_mm': oled_centers(),
                       'mount': 'four roof-integral collars and downward pins; user adhesive'},
              'mcu': {'pin_row_spacing_mm': MCU_PIN_ROW_SPACING,
                      'pin_row_occupied_length_mm': MCU_PIN_ROW_LENGTH,
                      'end_clearance_per_end_mm': MCU_SLOT_END_CLEARANCE, 'slots': slots},
              'legacy_c3_lid': legacy,
              'diagnosis_old_window_actual_glass_overlap_mm3': old_glass_interference,
              'limits': ['Physical switch clipping requires fit sample',
                         'PCB, glass Z thickness and component projections provisional',
                         'Adhesive behavior not simulated']}
    Path(__file__).with_name('validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    validate()
