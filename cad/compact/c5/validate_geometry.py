"""C5 mesh and bottom interface validation."""
import json
import struct
from collections import Counter
from pathlib import Path
from build123d import import_step
from compact_model import top_shell

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
    assert abs(min(p[2] for p in vertices) - expected['min_mm'][2]) < 1e-5
    return {'triangles': count, 'closed_manifold_edges': True,
            'consistent_winding': True, 'volume_mm3': volume, 'size_mm': dimensions,
            'max_bbox_deviation_mm': max(abs(a-b) for a,b in zip(dimensions, expected['size_mm']))}


if __name__ == '__main__':
    folder=Path(__file__).parent
    shell=top_shell()
    # Integral cover export is print-posed: use original C4 lower datum for mating.
    cover=import_step(folder.parent/'c4'/'bottom_cover.step')
    common=shell & cover
    overlap=abs(common.volume) if common else 0
    assert overlap<1e-6
    report={'part':facts(shell),'mesh':mesh_check(folder/'top_shell.stl',facts(shell)),
            'C4_lower_cover_overlap_mm3':overlap}
    (folder/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
