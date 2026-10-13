"""Place the middle carrier face-down on the print bed and validate STL."""
import collections
import json
import math
import struct
from pathlib import Path
from prepare_switch_trial_meshes import read_mesh

HERE=Path(__file__).parent


def main():
    source=HERE/'exports/middle_carrier_compact_v4_native.stl'
    destination=HERE.parent/'print/MiddleCarrier_Compact_V4.stl'
    faces=read_mesh(source);angle=math.radians(175);c,s=math.cos(angle),math.sin(angle)
    def rotate(p):
        x,y,z=p;return x,c*y-s*z,s*y+c*z
    triangles=[[rotate(face[i:i+3]) for i in (3,6,9)] for face in faces]
    minima=[min(v[a] for tri in triangles for v in tri) for a in range(3)]
    triangles=[[tuple(v[a]-minima[a] for a in range(3)) for v in tri] for tri in triangles]
    edges=collections.Counter();volume=0
    for a,b,cpt in triangles:
        volume+=(a[0]*(b[1]*cpt[2]-b[2]*cpt[1])-a[1]*(b[0]*cpt[2]-b[2]*cpt[0])+a[2]*(b[0]*cpt[1]-b[1]*cpt[0]))/6
        points=[tuple(round(v,4) for v in p) for p in (a,b,cpt)]
        for i in range(3):edges[tuple(sorted((points[i],points[(i+1)%3])))] += 1
    if volume<=0 or any(count!=2 for count in edges.values()):raise ValueError('Carrier mesh is not closed with positive volume')
    size=[max(v[a] for tri in triangles for v in tri) for a in range(3)]
    if not 70<size[0]<80 or not 100<size[1]<116 or not 8<size[2]<25:
        raise ValueError('Unexpected carrier dimensions '+str(size))
    report=json.loads((HERE/'exports/carrier-v4-validation.json').read_text())
    if abs(volume-report['volume_mm3'])/report['volume_mm3']>.002:raise ValueError('STL volume differs from CAD')
    output=bytearray(b'Middle carrier V4; millimeters; flat switch face on bed'.ljust(80,b' '))
    output.extend(struct.pack('<I',len(faces)))
    for face,tri in zip(faces,triangles):output.extend(struct.pack('<12fH',*rotate(face[:3]),*(v for p in tri for v in p),face[-1]))
    destination.write_bytes(output)
    result={'file':str(destination),'size_mm':size,'triangles':len(faces),'volume_mm3':volume,'closed_edges':True,'bed_z_mm':0,'rotation_about_x_deg':175}
    (HERE/'exports/carrier-v4-print-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
