"""Binary STL checks: welded edge closure, winding, dimensions and volume."""
import json
import struct
from collections import Counter
from pathlib import Path


def check(path, expected_size, expected_volume):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + 50 * count
    edge_counts, directions, vertices = Counter(), Counter(), []
    signed_volume = 0.0
    for index in range(count):
        values = struct.unpack_from('<12fH', data, 84 + index * 50)
        points = [tuple(round(v, 5) for v in values[start:start + 3]) for start in (3, 6, 9)]
        assert len(set(points)) == 3
        vertices.extend(points)
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edge = tuple(sorted((points[i], points[j])))
            edge_counts[edge] += 1
            directions[edge] += 1 if points[i] < points[j] else -1
        a, b, c = points
        signed_volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
                          + a[1] * (b[2] * c[0] - b[0] * c[2])
                          + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    assert all(n == 2 for n in edge_counts.values())
    assert all(n == 0 for n in directions.values())
    lo = [min(p[i] for p in vertices) for i in range(3)]
    hi = [max(p[i] for p in vertices) for i in range(3)]
    dimensions = [round(b - a, 5) for a, b in zip(lo, hi)]
    assert all(abs(a - b) < 1e-4 for a, b in zip(dimensions, expected_size))
    assert signed_volume > 0 and abs(signed_volume - expected_volume) / expected_volume < 0.001
    return {'triangles': count, 'closed_edges': True, 'consistent_winding': True,
            'min_mm': lo, 'max_mm': hi, 'size_mm': dimensions,
            'mesh_volume_mm3': signed_volume}


def main():
    folder = Path(__file__).parent
    facts = json.loads((folder / 'validation.json').read_text())['parts']
    report = {}
    for stem, key in [('top_shell', 'shell'), ('bottom_cover', 'cover'), ('mx_coupon', 'coupon')]:
        report[stem] = check(folder / (stem + '.stl'), facts[key]['bbox_mm'], facts[key]['volume_mm3'])
    (folder / 'mesh-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
