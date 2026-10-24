"""B-rep assembly, contact planes, head access and print mesh checks."""
import json
import struct
from collections import Counter
from math import sin
from pathlib import Path
from rear_foot import (assembled_parts, foot_case_local, print_foot, ANGLE,
                       POCKET_DIAMETER, POCKET_DEPTH, seat_z, FOOT_RADIUS)
from feet_set import gen_step as feet_set


def facts(shape):
    assert shape.is_valid and shape.volume > 0
    bb = shape.bounding_box()
    return {'solids': len(shape.solids()), 'volume_mm3': shape.volume,
            'size_mm': [bb.size.X, bb.size.Y, bb.size.Z],
            'min_mm': [bb.min.X, bb.min.Y, bb.min.Z],
            'max_mm': [bb.max.X, bb.max.Y, bb.max.Z]}


def mesh_check(path, expected):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + count * 50
    edges, winding, vertices = Counter(), Counter(), []
    volume = 0
    for i in range(count):
        numbers = struct.unpack_from('<12fH', data, 84 + i * 50)
        p = [tuple(round(v, 5) for v in numbers[j:j + 3]) for j in (3, 6, 9)]
        assert len(set(p)) == 3
        vertices.extend(p)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            key = tuple(sorted((p[a], p[b])))
            edges[key] += 1
            winding[key] += 1 if p[a] < p[b] else -1
        a, b, c = p
        volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
                   + a[1] * (b[2] * c[0] - b[0] * c[2])
                   + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    assert all(v == 2 for v in edges.values())
    assert all(v == 0 for v in winding.values())
    dimensions = [max(p[i] for p in vertices) - min(p[i] for p in vertices) for i in range(3)]
    assert all(abs(a - b) < 0.005 for a, b in zip(dimensions, expected['size_mm']))
    assert volume > 0 and abs(volume - expected['volume_mm3']) / volume < 0.003
    assert abs(min(p[2] for p in vertices)) < 1e-5
    return {'triangles': count, 'closed_manifold_edges': True,
            'consistent_winding': True, 'volume_mm3': volume, 'size_mm': dimensions,
            'max_bbox_deviation_mm': max(abs(a-b) for a,b in zip(dimensions, expected['size_mm']))}


def main():
    folder = Path(__file__).parent
    parts, report = assembled_parts(check=True)
    assert not report['collisions']
    assert len(parts) == 14
    assert all(p.is_valid and len(p.solids()) == 1 and p.volume > 0 for p in parts)
    assert all(p.bounding_box().min.Z > -1e-5 for p in parts)
    assert all(abs(z) < 1e-5 for z in report['support_min_z_mm'])
    report['parts'] = {'rear_foot': facts(print_foot()), 'front_foot': facts(print_foot(True)),
                       'feet_set': facts(feet_set())}
    assert report['parts']['rear_foot']['solids'] == 1
    assert report['parts']['front_foot']['solids'] == 1
    assert report['parts']['feet_set']['solids'] == 4
    assert report['screw_head_floor_min_clearance_mm'] > 0.4
    assert report['screw_head_min_clearance_mm'] > 0.4
    report['minimum_material_behind_front_pocket_mm'] = -seat_z(True) - sin(ANGLE) * POCKET_DIAMETER / 2
    assert report['minimum_material_behind_front_pocket_mm'] > 0.6
    report['pad_seat_diameter_mm'] = POCKET_DIAMETER
    report['pad_seat_normal_depth_mm'] = POCKET_DEPTH
    report['foot_body_diameter_mm'] = FOOT_RADIUS * 2
    report['meshes'] = {name: mesh_check(folder / (name + '.stl'), fact)
                        for name, fact in report['parts'].items()}
    report['limits'] = ['Pads measured by user; adhesive thickness excluded',
                        'Adhesive strength and rubber compression untested',
                        'Remove existing pads before attaching new feet']
    (folder / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
