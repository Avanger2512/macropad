"""Orient native Fusion trial STL exports on the bed and verify closed meshes."""
import collections
import json
import math
import struct
from pathlib import Path


def read_mesh(path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("STL header is incomplete")
    count = struct.unpack_from('<I', data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError("Expected a complete binary STL")
    return [struct.unpack_from('<12fH', data, 84 + i * 50) for i in range(count)]


def orient(source, destination, angle):
    faces = read_mesh(source)
    c, s = math.cos(angle), math.sin(angle)

    def rotate(v):
        x, y, z = v
        return x, c * y - s * z, s * y + c * z

    triangles = [[rotate(face[i:i + 3]) for i in (3, 6, 9)] for face in faces]
    floor = [min(v[i] for t in triangles for v in t) for i in range(3)]
    triangles = [[tuple(v[i] - floor[i] for i in range(3)) for v in t] for t in triangles]
    edges = collections.Counter()
    volume = 0.0
    for triangle in triangles:
        a, b, d = triangle
        volume += (a[0] * (b[1] * d[2] - b[2] * d[1])
                   - a[1] * (b[0] * d[2] - b[2] * d[0])
                   + a[2] * (b[0] * d[1] - b[1] * d[0])) / 6
        vertices = [tuple(round(x, 4) for x in v) for v in triangle]
        for i in range(3):
            edges[tuple(sorted((vertices[i], vertices[(i + 1) % 3])))] += 1
    if any(n != 2 for n in edges.values()) or volume <= 0:
        raise ValueError("Mesh edge counts or positive signed volume check failed")
    bounds = [max(v[i] for t in triangles for v in t) for i in range(3)]
    if any(abs(bounds[i] - 22) > 0.02 for i in (0, 1)):
        raise ValueError("Trial plate must remain 22 by 22 mm")
    data = bytearray(b'Macropad millimeter fit trial; flat plate on bed'.ljust(80, b' '))
    data.extend(struct.pack('<I', len(faces)))
    for face, triangle in zip(faces, triangles):
        normal = rotate(face[:3])
        data.extend(struct.pack('<12fH', *normal, *(x for v in triangle for x in v), face[-1]))
    destination.write_bytes(data)
    return {'file': destination.name, 'triangles': len(faces), 'size_mm': bounds,
            'volume_mm3': volume, 'closed_edges': True, 'bed_z_mm': 0,
            'rotation_about_x_deg': math.degrees(angle)}


def main():
    folder = Path(__file__).parent / 'exports'
    results = [orient(folder / 'switch_fit_coupon_native.stl',
                      folder / 'switch_fit_coupon.stl', math.radians(175)),
               orient(folder / 'lid_support_coupon_native.stl',
                      folder / 'lid_support_coupon.stl', 0)]
    (folder / 'switch-trial-mesh-validation.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
