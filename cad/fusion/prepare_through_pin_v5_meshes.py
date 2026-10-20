"""Orient V5 through-pin print parts and check scale, closure and CAD volume."""
import collections
import struct
import json
import math
from pathlib import Path
from prepare_switch_trial_meshes import read_mesh

HERE=Path(__file__).parent


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
    exports=HERE/'exports';prints=HERE.parent/'print'
    report=json.loads((exports/'through-pin-v5-validation.json').read_text())
    # The V5 holder includes a positive-Y reinforced land; the V4 helper's
    # exact original size assertion does not apply, but its transform does.
    source=exports/'hotswap_mx_through_pin_v5_native.stl'
    result=[]
    for stem,name,body in [('middle_carrier_through_pin_v5','MiddleCarrier_Through_Pin_V5','MiddleCarrier_Draft'),
                           ('switch_fit_coupon_through_pin_v5','SwitchFitCoupon_Through_Pin_V5','SwitchFitCoupon_Compact_V4')]:
        item=orient(exports/(stem+'_native.stl'),prints/(name+'.stl'),math.radians(175))
        result.append((item,body))
    # Generic mesh orientation performs the same rigid transform as the V4
    # holder helper, while allowing the explicitly enlarged V5 outer land.
    item=orient(source,prints/'Hotswap_MX_Through_Pin_V5.stl',math.radians(-5))
    result.append((item,'HotswapCompact_Pin_V4'))
    dimensions=[item['size_mm'] for item,body in result]
    if not (74<dimensions[0][0]<75 and 109<dimensions[0][1]<111 and 13<dimensions[0][2]<15):raise RuntimeError('Carrier scale changed')
    if any(abs(dimensions[1][i]-22)>.02 for i in (0,1)):raise RuntimeError('Coupon scale changed')
    if not (11<dimensions[2][0]<11.1 and 10<dimensions[2][1]<11 and 5.1<dimensions[2][2]<5.3):raise RuntimeError('Holder scale changed')
    for item,body in result:
        volume=item['volume_mm3']
        if abs(volume-report['volumes_mm3'][body])/report['volumes_mm3'][body]>.002:raise RuntimeError('CAD/STL volume mismatch '+body)
    (exports/'through-pin-v5-print-validation.json').write_text(json.dumps([item for item,body in result],indent=2)+'\n')
    print(json.dumps([item for item,body in result]))


if __name__=='__main__':main()
