"""Orient V4 receiver and modified compact on the bed; validate exported meshes."""
import collections
import json
import math
import struct
from pathlib import Path
from prepare_switch_trial_meshes import orient, read_mesh

HERE=Path(__file__).parent


def compact_on_bed(source,destination):
    faces=read_mesh(source)
    angle=math.radians(-5)
    c,s=math.cos(angle),math.sin(angle)
    def rotate(v):
        x,y,z=v
        return x,c*y-s*z,s*y+c*z
    triangles=[[rotate(face[i:i+3]) for i in (3,6,9)] for face in faces]
    floor=[min(v[a] for tri in triangles for v in tri) for a in range(3)]
    triangles=[[tuple(v[a]-floor[a] for a in range(3)) for v in tri] for tri in triangles]
    edges=collections.Counter()
    volume=0
    for a,b,cpt in triangles:
        volume+=(a[0]*(b[1]*cpt[2]-b[2]*cpt[1])-a[1]*(b[0]*cpt[2]-b[2]*cpt[0])+a[2]*(b[0]*cpt[1]-b[1]*cpt[0]))/6
        pts=[tuple(round(v,4) for v in p) for p in (a,b,cpt)]
        for i in range(3):edges[tuple(sorted((pts[i],pts[(i+1)%3])))] += 1
    if volume<=0 or any(count!=2 for count in edges.values()):
        raise ValueError('Modified compact is not a closed positive-volume mesh')
    size=[max(v[a] for tri in triangles for v in tri) for a in range(3)]
    expected=(11.03147984,9.74910235,5.2)
    if any(abs(actual-target)>.02 for actual,target in zip(size,expected)):
        raise ValueError('Compact outer dimensions changed unexpectedly')
    output=bytearray(b'Compact V4; millimeters; one 1.2mm transverse mechanical pin bore'.ljust(80,b' '))
    output.extend(struct.pack('<I',len(faces)))
    for face,tri in zip(faces,triangles):
        output.extend(struct.pack('<12fH',*rotate(face[:3]),*(v for p in tri for v in p),face[-1]))
    destination.write_bytes(output)
    return {'file':destination.name,'size_mm':size,'volume_mm3':volume,'triangles':len(faces),'closed_edges':True,'bed_z_mm':0}


def main():
    exports=HERE/'exports';prints=HERE.parent/'print'
    result=[orient(exports/'switch_fit_coupon_compact_v4_native.stl',prints/'SwitchFitCoupon_Compact_V4.stl',math.radians(175)),
            compact_on_bed(exports/'hotswap_mx_compact_pin_v4_native.stl',prints/'Hotswap_MX_Compact_Pin_V4.stl')]
    (exports/'compact-v4-print-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
