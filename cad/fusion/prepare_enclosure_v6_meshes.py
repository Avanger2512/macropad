"""Prepare closed millimeter STL meshes for V6 shell and cover."""
import collections
import json
import math
import struct
from pathlib import Path

from prepare_switch_trial_meshes import read_mesh

HERE = Path(__file__).parent


def prepare(source, destination, angle_degrees, cad_volume):
    faces = read_mesh(source)
    angle = math.radians(angle_degrees)
    c, s = math.cos(angle), math.sin(angle)
    def rotate(p):
        x, y, z = p
        return x, c * y - s * z, s * y + c * z
    triangles = [[rotate(face[i:i + 3]) for i in (3, 6, 9)] for face in faces]
    minima = [min(p[a] for tri in triangles for p in tri) for a in range(3)]
    triangles = [[tuple(p[a] - minima[a] for a in range(3)) for p in tri] for tri in triangles]
    edges = collections.Counter()
    volume = 0
    for a, b, cpt in triangles:
        volume += (a[0] * (b[1] * cpt[2] - b[2] * cpt[1])
                   - a[1] * (b[0] * cpt[2] - b[2] * cpt[0])
                   + a[2] * (b[0] * cpt[1] - b[1] * cpt[0])) / 6
        points = [tuple(round(v, 4) for v in p) for p in (a, b, cpt)]
        for i in range(3):
            edges[tuple(sorted((points[i], points[(i + 1) % 3])))] += 1
    if volume <= 0 or any(count != 2 for count in edges.values()):
        raise ValueError('Mesh is not closed with positive signed volume: ' + str(source))
    if abs(volume - cad_volume) / cad_volume > .002:
        raise ValueError('STL/CAD volume mismatch: ' + str(source))
    size = [max(p[a] for tri in triangles for p in tri) for a in range(3)]
    output = bytearray(b'V6 enclosure; millimeters; print pose; BOOT RESET included'.ljust(80, b' '))
    output.extend(struct.pack('<I', len(faces)))
    for face, tri in zip(faces, triangles):
        output.extend(struct.pack('<12fH', *rotate(face[:3]), *(v for p in tri for v in p), face[-1]))
    destination.write_bytes(output)
    return {'file': str(destination.resolve()), 'size_mm': size, 'volume_mm3': volume,
            'cad_volume_mm3': cad_volume, 'triangles': len(faces), 'closed_edges': True,
            'rotation_about_x_deg': angle_degrees, 'bed_z_mm': 0}


def main():
    report = json.loads((HERE / 'exports/enclosure-v6-validation.json').read_text())
    parts = [('upper_shell_finish_v6', 'UpperShell_Finish_V6', 'UpperShell_Draft', 175),
             ('bottom_cover_finish_v6', 'BottomCover_Finish_V6', 'BottomCover_Draft', 0)]
    outputs = [prepare(HERE / 'exports' / (source + '_native.stl'),
                       HERE.parent / 'print' / (output + '.stl'), angle,
                       report['volumes_mm3'][body]) for source, output, body, angle in parts]
    (HERE / 'exports/enclosure-v6-print-validation.json').write_text(json.dumps(outputs, indent=2) + '\n')
    print(json.dumps(outputs))


if __name__ == '__main__':
    main()
